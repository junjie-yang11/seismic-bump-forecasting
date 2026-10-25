"""Separate-path reconstruction, model replay and optional full refitting.

This module does not import the information experiment's fitting, ranking,
tie-allocation or bootstrap calculations. Numerical tolerances apply only to
floating arithmetic in expected counts; scores and score ties remain exact.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
import numpy as np
import pandas as pd
import xgboost as xgb
from phase2.information.provenance import verify_protected

ROOT=Path(__file__).resolve().parents[2]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tie_probabilities(grades,scores,budget):
    """Independent dictionary grouping; labels are not an argument."""
    groups={}
    for i,(grade,score) in enumerate(zip(grades,scores)):
        groups.setdefault((float(grade),float(score)),[]).append(i)
    left=math.floor(budget*len(grades));probability=np.zeros(len(grades))
    for key in sorted(groups,reverse=True):
        indices=groups[key];take=min(left,len(indices));left-=take
        probability[indices]=take/len(indices)
    return probability


def weighted_expectations(y,grades,scores,multiplicity,budgets):
    """Sequential weighted group allocation on every sampled multiset."""
    groups={}
    for i,(grade,score) in enumerate(zip(grades,scores)):
        groups.setdefault((float(grade),float(score)),[]).append(i)
    ordered=[groups[key] for key in sorted(groups,reverse=True)]
    sizes=[multiplicity[:,indices].sum(axis=1) for indices in ordered]
    positive=[multiplicity[:,indices]@y[indices] for indices in ordered]
    totals=multiplicity.sum(axis=1);result=np.zeros((len(multiplicity),len(budgets)))
    for bi,budget in enumerate(budgets):
        remaining=np.floor(budget*totals).astype(int)
        for size,hits in zip(sizes,positive):
            take=np.minimum(size,remaining);remaining-=take
            result[:,bi]+=take*np.divide(hits,size,out=np.zeros_like(hits,dtype=float),where=size>0)
    return result


def grouped_ap(y,scores):
    """Precision weighted by positive increments, grouping equal scores."""
    total_positive=float(np.sum(y))
    if not total_positive:return float('nan')
    positive=0.;total=0;value=0.
    for score in sorted(set(scores),reverse=True):
        group=scores==score;gain=float(y[group].sum());positive+=gain;total+=int(group.sum())
        value+=gain/total_positive*(positive/total)
    return value


def checks(root,refit=False):
    root=Path(root);out=root/'results/phase2/information';counter=0
    def check(condition,message):
        nonlocal counter
        counter+=1
        if not condition:raise AssertionError(message)
    def close(actual,expected,message):
        check(np.allclose(actual,expected,rtol=0,atol=1e-10),message)
    def read(name):return pd.read_csv(root/name,float_precision='round_trip')
    def pick(frame,**conditions):
        selected=frame
        for name,value in conditions.items():selected=selected[selected[name]==value]
        check(len(selected)==1,'unique source selection '+str(conditions))
        return selected.iloc[0]
    manifest=json.loads((out/'run_manifest.json').read_text(encoding='utf-8'))
    plan=json.loads((root/'phase2/information/protocol.json').read_text(encoding='utf-8'))
    check(manifest['status']=='complete','complete experiment')
    check(sha(root/'phase2/information/protocol.json')==manifest['protocol_sha256'],'current protocol hash')
    for field in ('inputs_sha256','code_sha256'):
        for name,value in manifest[field].items():check(sha(root/name)==value,'unchanged '+field+' '+name)
    provenance=verify_protected(root,manifest,check)
    for name,value in manifest['outputs_sha256'].items():check(sha(out/name)==value,'saved output '+name)
    check(sha(root/'results/phase2/fold_manifest.json')==plan['fold_source_sha256'],'original fold identity')
    original_lock=json.loads((root/'phase2/locked_plan.json').read_text(encoding='utf-8'))
    check(original_lock['plan_sha256']==plan['locked_plan_sha256'],'original locked protocol identity')
    check(plan['model_settings']==original_lock['plan']['model_settings']['XGBoost'],'matched original model settings')
    check(plan['budgets']==[.01,.05,.1,.2] and plan['bootstrap']['block_lengths']==[16,32,64],
          'all specified budgets and record-block lengths')
    check(plan['bootstrap']['main_block_length']==32 and plan['bootstrap']['replicates']==2000,'fixed main interval settings')
    check(plan['base_features']==['seismic','seismoacoustic','shift','ghazard'],'four declared base inputs')
    data=read('data/seismic-bumps.csv');names=[name for name in data.columns if name not in ('class','nbumps')]
    check(len(data)==2578 and int(data['class'].sum())==170,'audited mirror size and positives')
    check(len(names)==17,'retained full design')
    # Reconstruct encodings directly from raw data rather than calling load().
    mapping={'seismic':'abcd','seismoacoustic':'abcd','ghazard':'abcd','shift':'NW'}
    encoded=data[names].copy()
    for name,values in mapping.items():
        check(set(data[name]).issubset(set(values)),'known source categories '+name)
        encoded[name]=data[name].map({value:i for i,value in enumerate(values)})
    X=encoded.to_numpy(float);labels=data['class'].to_numpy(float)
    check(np.isfinite(X).all() and np.isin(labels,[0,1]).all(),'finite features and binary source labels')
    old_folds=json.loads((root/'results/phase2/fold_manifest.json').read_text(encoding='utf-8'))
    original={r['fold']:r for r in old_folds if r['model']=='XGBoost' and r['scheme']=='time'}
    check(set(original)==set(range(4)),'four original time folds')
    folds=json.loads((out/'fold_manifest.json').read_text(encoding='utf-8'))
    check(len(folds)==8 and len({(r['fold'],r['design']) for r in folds})==8,'eight unique fitted designs')
    rows=read('results/phase2/information/rows.csv');evaluations=read('results/phase2/information/evaluations.csv')
    intervals=read('results/phase2/information/intervals.csv');allocations=read('results/phase2/information/allocations.csv')
    tuning=read('results/phase2/information/tuning.csv');tune_predictions=read('results/phase2/information/tuning_predictions.csv')
    check(len(rows)==2063 and rows.row.is_unique and set(rows.fold)==set(range(4)),'unique original test cohort')
    check(int(rows.y.sum())==88 and np.array_equal(rows.y,labels[rows.row.to_numpy(int)]),'source test labels')
    grade_map={value:i for i,value in enumerate(plan['grade_order'])}
    check(np.array_equal(rows.grade,data.loc[rows.row,plan['primary_grade']].map(grade_map)),'source primary grade identity')
    check(len(evaluations)==20 and not evaluations.duplicated(['fold','budget']).any(),'all phase and pooled evaluation settings')
    check(len(intervals)==60 and not intervals.duplicated(['fold','budget','block_length']).any(),'all interval settings')
    check(len(tuning)==32 and not tuning.duplicated(['fold','design','candidate']).any(),'four candidates for each design and phase')
    check(not tune_predictions.duplicated(['fold','design','candidate','row']).any(),'unique tuning predictions')
    check(not allocations.duplicated(['fold','budget','grade']).any(),'unique grade allocations')
    setting=plan['model_settings'];grid=setting['candidates'];candidate_refits=0;final_refits=0
    parameters={key:value for key,value in setting.items() if key!='candidates'}
    parameters.update(objective='binary:logistic',tree_method='hist',verbosity=0)
    for fold in range(4):
        old=original[fold];q=rows[rows.fold==fold].sort_values('row');test=q.row.to_numpy(int)
        check(np.array_equal(test,old['test_rows']),'exact original test rows '+str(fold))
        fitting=np.asarray(old['fit_rows'],int);reference=np.asarray(old['reference_rows'],int)
        history=np.asarray(old['outer_train_rows'],int);cut=int(.8*len(history))
        check(np.array_equal(fitting,history[:cut]) and np.array_equal(reference,history[cut:]),'historical fitting/reference boundary')
        check(np.intersect1d(fitting,reference).size==0 and history.max()<test.min(),'history and test isolation')
        for design,features in (('base',plan['base_features']),('extended',names)):
            matches=[r for r in folds if r['fold']==fold and r['design']==design]
            check(len(matches)==1,'one design manifest');m=matches[0]
            check(m['features']==features,'matched feature columns '+design)
            for key in ('fit_rows','reference_rows','test_rows','tuning_fit_rows','tuning_reference_rows'):
                check(m[key]==old[key],'same original boundaries '+design+' '+key)
            inner_fit=np.asarray(m['tuning_fit_rows'],int);inner_ref=np.asarray(m['tuning_reference_rows'],int)
            inner_cut=max(1,int(.8*len(fitting)))
            check(np.array_equal(inner_fit,fitting[:inner_cut]) and np.array_equal(inner_ref,fitting[inner_cut:]),'inner tuning stays inside fitting area')
            check(len(np.unique(labels[inner_fit]))==2,'inner fitting class support')
            a=tuning[(tuning.fold==fold)&(tuning.design==design)].sort_values('candidate')
            check(a.candidate.tolist()==list(range(4)),'candidate order')
            check(a[['depth','rounds']].to_numpy(int).tolist()==grid,'matched candidate grid')
            metric='AP' if labels[inner_ref].sum() else 'negative Brier'
            check(set(a.selection_metric)=={metric},'historical metric/fallback')
            features_X=X[:,[names.index(name) for name in features]]
            for candidate,(depth,rounds) in enumerate(grid):
                p=tune_predictions[(tune_predictions.fold==fold)&(tune_predictions.design==design)&(tune_predictions.candidate==candidate)].sort_values('row')
                check(np.array_equal(p.row,inner_ref) and np.array_equal(p.y,labels[inner_ref]),'candidate labels and historical rows')
                score=p.score.to_numpy();check(np.isfinite(score).all(),'finite tuning scores')
                value=grouped_ap(p.y.to_numpy(),score) if metric=='AP' else -float(np.mean((score-p.y.to_numpy())**2))
                close(a.iloc[candidate]['value'],value,'independent candidate selection metric')
                if refit:
                    fitted=xgb.train(dict(parameters,max_depth=depth),xgb.DMatrix(features_X[inner_fit],label=labels[inner_fit],feature_names=features,nthread=2),rounds)
                    replay=fitted.predict(xgb.DMatrix(features_X[inner_ref],feature_names=features,nthread=2)).astype(float)
                    check(np.array_equal(replay,score),'exact repeated inner candidate scores');candidate_refits+=1
            winner=int(np.argmax(a['value'].to_numpy()))
            check(a['selected'].astype(bool).tolist()==[i==winner for i in range(4)],'first exact maximum selects candidate')
            check([m['selected_depth'],m['selected_rounds']]==grid[winner],'manifest training-selected parameters')
            model=xgb.Booster(params={'nthread':2});model.load_model(str(out/f'models/{design}_fold{fold}.json'))
            check(model.feature_names==features,'saved model feature identity')
            replay=model.predict(xgb.DMatrix(features_X[test],feature_names=features,nthread=2)).astype(float)
            check(np.array_equal(replay,q[design+'_score'].to_numpy()),'exact saved-model score replay '+design)
            if refit:
                depth,rounds=grid[winner]
                fitted=xgb.train(dict(parameters,max_depth=depth),xgb.DMatrix(features_X[fitting],label=labels[fitting],feature_names=features,nthread=2),rounds)
                score=fitted.predict(xgb.DMatrix(features_X[test],feature_names=features,nthread=2)).astype(float)
                check(np.array_equal(score,replay),'exact final refitting score replay '+design);final_refits+=1
    points={};phase_vectors={}
    for fold in range(4):
        q=rows[rows.fold==fold].sort_values('row');y=q.y.to_numpy();g=q.grade.to_numpy();n=len(q)
        scores={name:q[name+'_score'].to_numpy() for name in ('base','extended')};phase_vectors[fold]=(y,g,scores)
        for budget in plan['budgets']:
            k=math.floor(budget*n);remaining=k;quotas={}
            for grade in sorted(set(g),reverse=True):
                mask=g==grade;quota=min(int(mask.sum()),remaining);remaining-=quota;quotas[grade]=quota
                r=pick(allocations,fold=fold,budget=budget,grade=grade)
                check((int(r.n),int(r.positives),int(r.k))==(int(mask.sum()),int(y[mask].sum()),quota),'exact grade census and quota')
            detections={}
            for design in ('base','extended'):
                p=tie_probabilities(g,scores[design],budget);saved=q[f'{design}_prob_b{round(100*budget):02d}'].to_numpy()
                check(np.isfinite(saved).all() and np.all((saved>=0)&(saved<=1)),'valid saved inclusion probabilities')
                close(saved,p,'independent label-free score-tie allocation '+design)
                close(p.sum(),k,'same total K '+design)
                for grade,quota in quotas.items():close(p[g==grade].sum(),quota,'same grade-specific quotas '+design)
                detections[design]=float(p@y)
            r=pick(evaluations,fold=fold,budget=budget)
            expected=[n,int(y.sum()),k,detections['base'],detections['extended'],detections['extended']-detections['base'],
                      y.sum()-detections['base'],y.sum()-detections['extended']]
            fields=['n','positives','k','base_etp','extended_etp','delta_etp','base_efn','extended_efn']
            close(r[fields].to_numpy(float),expected,'all expected detections/misses and point contrasts')
            points[fold,budget]=np.asarray(expected)
    for budget in plan['budgets']:
        expected=sum(points[fold,budget] for fold in range(4));r=pick(evaluations,fold=-1,budget=budget)
        close(r[fields].to_numpy(float),expected,'pooled sums of phase allocations and counts')
        points[-1,budget]=expected
    counts_file=np.load(out/'bootstrap_counts.npz');replicates=np.load(out/'bootstrap_replicates.npz')
    settings=plan['bootstrap'];zero_positive={};contrasts=0
    expected_count_keys={f'length{length}_fold{fold}' for length in settings['block_lengths'] for fold in range(4)}
    expected_sample_keys=expected_count_keys|{f'length{length}_pooled' for length in settings['block_lengths']}
    check(set(counts_file.files)==expected_count_keys and set(replicates.files)==expected_sample_keys,'complete saved draw and replicate arrays')
    for length in settings['block_lengths']:
        pooled=np.zeros((settings['replicates'],len(plan['budgets']),3))
        for fold in range(4):
            y,g,scores=phase_vectors[fold];n=len(y);key=f'length{length}_fold{fold}'
            multiplicity=counts_file[key];saved=replicates[key]
            check(multiplicity.shape==(settings['replicates'],n) and np.issubdtype(multiplicity.dtype,np.integer), 'integer draw shape')
            check(np.all(multiplicity>=0) and np.all(multiplicity.sum(axis=1)==n),'all draws preserve the phase size')
            rng=np.random.default_rng(settings['seed']+1000*length+fold);ell=min(length,n)
            for weights in multiplicity:
                starts=rng.integers(0,n-ell+1,size=math.ceil(n/ell))
                ix=np.concatenate([np.arange(start,start+ell) for start in starts])[:n]
                check(np.array_equal(weights,np.bincount(ix,minlength=n)),'every nonwrapping moving-block draw replayed')
            a=weighted_expectations(y,g,scores['base'],multiplicity,plan['budgets'])
            b=weighted_expectations(y,g,scores['extended'],multiplicity,plan['budgets'])
            computed=np.stack([a,b,b-a],axis=2)
            check(saved.shape==computed.shape,'complete analytic bootstrap array shape')
            close(saved,computed,'all multiset reranking/tie expectations')
            zero=multiplicity@y==0;zero_positive[key]=int(zero.sum())
            check(np.all(saved[zero]==0),'zero-positive draws retained as zero expectations')
            # Check the weighted implementation against explicit duplicated queues.
            for draw in (0,settings['replicates']//2,settings['replicates']-1):
                ix=np.repeat(np.arange(n),multiplicity[draw])
                for design,column in (('base',0),('extended',1)):
                    for bi,budget in enumerate(plan['budgets']):
                        direct=float(tie_probabilities(g[ix],scores[design][ix],budget)@y[ix])
                        close(saved[draw,bi,column],direct,'explicit duplicated queue equivalence')
            pooled+=computed
        close(replicates[f'length{length}_pooled'],pooled,'paired pooled draws sum phases, never cross phase boundaries')
        for fold in (0,1,2,3,-1):
            saved=pooled if fold<0 else replicates[f'length{length}_fold{fold}']
            low,high=np.quantile(saved[:,:,2],[.025,.975],axis=0)
            for bi,budget in enumerate(plan['budgets']):
                r=pick(intervals,fold=fold,budget=budget,block_length=length)
                close([r.delta_etp,r.ci_low,r.ci_high],[points[fold,budget][5],low[bi],high[bi]],'unchanged point and independently reconstructed percentile interval')
                check(int(r.replicates)==settings['replicates'],'all replicates retained')
                contrasts+=settings['replicates']
    return dict(checks=counter,refit=refit,model_replay=True,final_models=8,
                provenance=provenance,
                candidate_fits_repeated=candidate_refits,final_fits_repeated=final_refits,
                rows=len(rows),evaluations=len(evaluations),intervals=len(intervals),bootstrap_contrasts=contrasts,
                zero_positive_draws=zero_positive,protocol_sha256=manifest['protocol_sha256'],
                manifest_sha256=sha(out/'run_manifest.json'),
                scope='Live model-input/code/output and protected computational-evidence hashes; bounded historical presentation/derived-summary snapshots checked separately (not a claim that current papers are unchanged). Raw-data encodings and historical split isolation; separate-path tuning metrics, analytic score-tie inclusion, quota/count/interval reconstruction; exact saved-model replay; all moving-block draws and 120000 reranked contrasts. '+
                      ('All32 inner candidates and8 final models refitted with exact score replay.' if refit else 'No model refitting; saved models replayed only.'))


def verify(root=ROOT,refit=False):
    root=Path(root);out=root/'results/phase2/information';out.mkdir(parents=True,exist_ok=True)
    path=out/'verification.json';started=datetime.now(timezone.utc).isoformat();clock=time.perf_counter()
    path.write_text(json.dumps(dict(passed=False,status='running',started_at_utc=started)),encoding='utf-8')
    try:
        result=checks(root,refit)
        result.update(passed=True,status='passed',started_at_utc=started,completed_at_utc=datetime.now(timezone.utc).isoformat(),
                      elapsed_seconds=time.perf_counter()-clock,verifier_sha256=sha(Path(__file__)))
        path.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(f'INFORMATION SUPPLEMENT PASSED: {result["checks"]} checks; {result["bootstrap_contrasts"]} reranked contrasts; refit={refit}.')
        return result
    except (Exception,KeyboardInterrupt) as error:
        path.write_text(json.dumps(dict(passed=False,status='failed',started_at_utc=started,
            error_type=type(error).__name__,error=str(error)),indent=2),encoding='utf-8');raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--refit',action='store_true');arguments=parser.parse_args()
    verify(arguments.root,arguments.refit)
