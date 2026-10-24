"""Fit matched designs and evaluate equal-allocation expected detections."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import xgboost

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from data import load, CSV_PATH
from boosting import BoostedModel, select_parameters, CANDIDATES, PARAMETERS
from uncertainty import resample_indices
from input_checks import supervised_arrays, split_indices


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inclusion_probabilities(grades,scores,budget):
    """Label-free exact-score tie allocation; probabilities sum to floor(B*N)."""
    g=np.asarray(grades,float);s=np.asarray(scores,float)
    if g.ndim!=1 or not len(g) or s.shape!=g.shape or not np.isfinite(s).all() or not np.isin(g,[0,1,2,3]).all():
        raise ValueError('Aligned nonempty finite scores and ordinal grades required')
    if not np.isfinite(budget) or not 0<=budget<=1:raise ValueError('Budget must lie in [0,1]')
    order=np.lexsort((-s,-g));starts=np.r_[0,np.flatnonzero((np.diff(g[order])!=0)|(np.diff(s[order])!=0))+1]
    sizes=np.diff(np.r_[starts,len(g)]);before=np.cumsum(sizes)-sizes
    taken=np.minimum(sizes,np.maximum(0,math.floor(budget*len(g))-before))
    probabilities=np.empty(len(g));probabilities[order]=np.repeat(taken/sizes,sizes)
    return probabilities


def expected_detections(y,grades,scores,counts,budgets):
    """Analytically rerank sampled multisets, rather than resampling old alerts."""
    y=np.asarray(y,float);g=np.asarray(grades,float);s=np.asarray(scores,float);w=np.asarray(counts)
    if y.ndim!=1 or not len(y) or g.shape!=y.shape or s.shape!=y.shape or not np.isin(y,[0,1]).all():
        raise ValueError('Aligned binary labels, grades and scores required')
    if not np.isfinite(s).all() or not np.isin(g,[0,1,2,3]).all():raise ValueError('Invalid score or grade')
    if w.ndim!=2 or w.shape[1]!=len(y) or not np.isfinite(w).all() or np.any(w<0) or np.any(w!=np.floor(w)) or np.any(w.sum(axis=1)==0):
        raise ValueError('Nonnegative integer multiplicities and nonempty draws required')
    if any(not np.isfinite(b) or not 0<=b<=1 for b in budgets):raise ValueError('Invalid budget')
    order=np.lexsort((-s,-g));starts=np.r_[0,np.flatnonzero((np.diff(g[order])!=0)|(np.diff(s[order])!=0))+1]
    group_n=np.add.reduceat(w[:,order],starts,axis=1)
    group_p=np.add.reduceat(w[:,order]*y[order],starts,axis=1)
    before=np.cumsum(group_n,axis=1)-group_n
    rate=np.divide(group_p,group_n,out=np.zeros_like(group_p,dtype=float),where=group_n>0)
    return np.column_stack([np.sum(np.minimum(group_n,np.maximum(0,np.floor(b*w.sum(axis=1))[:,None]-before))*rate,axis=1) for b in budgets])


def fit_design(X,y,fit_rows,test_rows,names):
    """Only model-fitting labels reach tuning and model fitting."""
    X,y=supervised_arrays(X,y)
    fit_rows,test_rows=split_indices(fit_rows,test_rows,len(y),temporal=True)
    choice,audit,inner_fit,inner_ref,tuning_scores=select_parameters(X[fit_rows],y[fit_rows],names,True)
    model=BoostedModel(*choice,names=names).fit(X[fit_rows],y[fit_rows])
    return model,model.predict_proba(X[test_rows]),audit,fit_rows[inner_fit],fit_rows[inner_ref],tuning_scores


def run(root=ROOT):
    root=Path(root);out=root/'results/phase2/information';out.mkdir(parents=True,exist_ok=True)
    record=out/'verification.json';manifest=out/'run_manifest.json';clock=time.perf_counter()
    started=datetime.now(timezone.utc).isoformat()
    record.write_text(json.dumps(dict(passed=False,status='running')),encoding='utf-8')
    manifest.write_text(json.dumps(dict(status='running',started_at_utc=started)),encoding='utf-8')
    try:
        protocol=root/'phase2/information/protocol.json';plan=json.loads(protocol.read_text(encoding='utf-8'))
        old_folds=root/'results/phase2/fold_manifest.json'
        if sha(old_folds)!=plan['fold_source_sha256']:raise ValueError('Original fold definitions changed')
        setting=plan['model_settings']
        if setting['candidates']!=[list(p) for p in CANDIDATES]:raise ValueError('Parameter grid differs from protocol')
        for key in ('eta','min_child_weight','reg_lambda','nthread','seed','subsample','colsample_bytree','scale_pos_weight'):
            if PARAMETERS[key]!=setting[key]:raise ValueError('Model parameter changed: '+key)
        protected={p.relative_to(root).as_posix():sha(p) for folder in ('src','phase1','phase2','results','reports')
                   for p in (root/folder).rglob('*') if p.is_file() and 'information' not in p.relative_to(root).parts and '__pycache__' not in p.parts and p.suffix!='.pyc'}
        X,y,names,data=load()
        if sha(CSV_PATH)!=json.loads((root/'results/phase2/run_manifest.json').read_text())['data_sha256']:raise ValueError('Data source differs')
        if X.shape[1]!=17:raise ValueError('Expected original 17-column design')
        folds=[r for r in json.loads(old_folds.read_text()) if r['model']=='XGBoost' and r['scheme']=='time']
        folds.sort(key=lambda r:r['fold'])
        if [r['fold'] for r in folds]!=list(range(4)):raise ValueError('Four original time folds required')
        (out/'models').mkdir(exist_ok=True)
        rows=[];tuning=[];tuning_predictions=[];audits=[];allocations=[];evaluations=[];intervals=[];draws={};replicates={};phase_arrays={}
        for original in folds:
            fold=original['fold'];fitting=np.array(original['fit_rows']);test=np.array(original['test_rows'])
            reference=np.array(original['reference_rows']);history=np.array(original['outer_train_rows'])
            if not np.array_equal(np.r_[fitting,reference],history) or len(fitting)!=int(.8*len(history)):
                raise ValueError('Fitting and reference boundaries differ')
            g=data.loc[test,plan['primary_grade']].map({v:i for i,v in enumerate(plan['grade_order'])}).to_numpy(float)
            columns=dict(fold=fold,row=test,y=y[test],grade=g);scores={}
            for design,features in [('base',plan['base_features']),('extended',names)]:
                indices=[names.index(name) for name in features];design_X=X[:,indices]
                model,score,audit,inner_fit,inner_ref,inner_scores=fit_design(design_X,y,fitting,test,features)
                if not np.array_equal(inner_fit,original['tuning_fit_rows']) or not np.array_equal(inner_ref,original['tuning_reference_rows']):
                    raise ValueError('Inner boundaries differ from original fixed workflow')
                model.booster.save_model(str(out/f'models/{design}_fold{fold}.json'))
                scores[design]=score;columns[design+'_score']=score
                audits.append(dict(fold=fold,design=design,features=features,fit_rows=fitting.tolist(),reference_rows=reference.tolist(),test_rows=test.tolist(),
                    tuning_fit_rows=inner_fit.tolist(),tuning_reference_rows=inner_ref.tolist(),selected_depth=model.depth,selected_rounds=model.rounds))
                tuning.extend(dict(fold=fold,design=design,**r) for r in audit)
                for a,ss in zip(audit,inner_scores):
                    tuning_predictions.append(pd.DataFrame(dict(fold=fold,design=design,candidate=a['candidate'],row=inner_ref,y=y[inner_ref],score=ss)))
            for budget in plan['budgets']:
                b=round(100*budget);k=math.floor(budget*len(test));remaining=k
                for level in sorted(set(g),reverse=True):
                    mask=g==level;take=min(int(mask.sum()),remaining);remaining-=take
                    allocations.append(dict(fold=fold,budget=budget,grade=int(level),n=int(mask.sum()),positives=int(y[test][mask].sum()),k=take))
                stats={}
                for design in ('base','extended'):
                    probability=inclusion_probabilities(g,scores[design],budget);columns[f'{design}_prob_b{b:02d}']=probability
                    stats[design]=float(probability@y[test])
                evaluations.append(dict(fold=fold,budget=budget,n=len(test),positives=int(y[test].sum()),k=k,
                    base_etp=stats['base'],extended_etp=stats['extended'],delta_etp=stats['extended']-stats['base'],
                    base_efn=float(y[test].sum())-stats['base'],extended_efn=float(y[test].sum())-stats['extended']))
            rows.append(pd.DataFrame(columns));phase_arrays[fold]=(g,y[test],scores)
            print(f'Information fold {fold+1}: both designs independently tuned and fitted',flush=True)
        for budget in plan['budgets']:
            part=[r for r in evaluations if r['budget']==budget]
            evaluations.append(dict(fold=-1,budget=budget,**{key:sum(r[key] for r in part) for key in
                ('n','positives','k','base_etp','extended_etp','delta_etp','base_efn','extended_efn')}))
        settings=plan['bootstrap']
        for length in settings['block_lengths']:
            pooled=np.zeros((settings['replicates'],len(plan['budgets']),3))
            for fold in range(4):
                g,yy,scores=phase_arrays[fold];n=len(yy);rng=np.random.default_rng(settings['seed']+1000*length+fold)
                counts=np.array([np.bincount(resample_indices(rng,np.zeros(n,int),length),minlength=n) for _ in range(settings['replicates'])],dtype=np.int16)
                a=expected_detections(yy,g,scores['base'],counts,plan['budgets']);b=expected_detections(yy,g,scores['extended'],counts,plan['budgets'])
                saved=np.stack([a,b,b-a],axis=2);key=f'length{length}_fold{fold}'
                draws[key]=counts;replicates[key]=saved;pooled+=saved
            replicates[f'length{length}_pooled']=pooled
            for fold in (0,1,2,3,-1):
                saved=pooled if fold<0 else replicates[f'length{length}_fold{fold}'];lo,hi=np.quantile(saved[:,:,2],[.025,.975],axis=0)
                for bi,budget in enumerate(plan['budgets']):
                    point=next(r for r in evaluations if r['fold']==fold and r['budget']==budget)
                    intervals.append(dict(fold=fold,budget=budget,block_length=length,replicates=settings['replicates'],delta_etp=point['delta_etp'],ci_low=lo[bi],ci_high=hi[bi]))
            print(f'Information block length {length}: all 2,000 paired draws evaluated',flush=True)
        for name,frame in [('rows',pd.concat(rows,ignore_index=True)),('allocations',pd.DataFrame(allocations)),('evaluations',pd.DataFrame(evaluations)),
                           ('intervals',pd.DataFrame(intervals)),('tuning',pd.DataFrame(tuning)),('tuning_predictions',pd.concat(tuning_predictions,ignore_index=True))]:
            frame.to_csv(out/(name+'.csv'),index=False)
        (out/'fold_manifest.json').write_text(json.dumps(audits,indent=2),encoding='utf-8')
        np.savez_compressed(out/'bootstrap_counts.npz',**draws);np.savez_compressed(out/'bootstrap_replicates.npz',**replicates)
        if any(sha(root/name)!=value for name,value in protected.items()):raise ValueError('Original evidence changed')
        code=['phase2/information/run.py','src/boosting.py','src/data.py','src/metrics.py','src/uncertainty.py']
        manifest.write_text(json.dumps(dict(status='complete',started_at_utc=started,completed_at_utc=datetime.now(timezone.utc).isoformat(),
            elapsed_seconds=time.perf_counter()-clock,protocol_sha256=sha(protocol),
            inputs_sha256={name:sha(root/name) for name in ('data/seismic-bumps.csv','results/phase2/fold_manifest.json','phase2/locked_plan.json')},
            code_sha256={name:sha(root/name) for name in code},protected_sha256=protected,
            outputs_sha256={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file() and p.name not in ('verification.json','run_manifest.json','README.md')},
            environment=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,xgboost=xgboost.__version__),
            scope='Eight final models and 32 inner candidate fits; analytic tie expectations and frozen-model within-phase reranking. No original policy, feature design or evidence overwritten.'),indent=2),encoding='utf-8')
        record.write_text(json.dumps(dict(passed=False,status='awaiting separate verification')),encoding='utf-8')
    except (Exception,KeyboardInterrupt) as error:
        failure=dict(passed=False,status='failed',error_type=type(error).__name__,error=str(error),started_at_utc=started)
        manifest.write_text(json.dumps(failure,indent=2),encoding='utf-8');record.write_text(json.dumps(failure,indent=2),encoding='utf-8');raise


if __name__=='__main__':run()
