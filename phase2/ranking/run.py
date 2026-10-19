"""Execute equal-capacity ranking with analytical random allocation and reranking bootstrap."""
from __future__ import annotations
import hashlib
import json
import math
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from uncertainty import resample_indices


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def rank_queue(grades,scores,tie_keys,budgets):
    """Decisions and grade allocations have no outcome-label input."""
    g=np.asarray(grades,float);s=np.asarray(scores,float);keys=np.asarray(tie_keys,float)
    if g.ndim!=1 or not len(g) or s.shape!=g.shape or keys.shape!=g.shape:
        raise ValueError('Nonempty aligned grade, score and tie-key vectors required')
    if not np.isfinite(g).all() or not np.isfinite(s).all() or not np.isfinite(keys).all():
        raise ValueError('Finite grades, scores and tie keys required')
    if not np.isin(g,[0,1,2,3]).all():raise ValueError('Grades must use the specified ordinal codes')
    n=len(g);occurrence=np.arange(n)
    grade_order=np.lexsort((occurrence,keys,-s,-g));global_order=np.lexsort((occurrence,keys,-s))
    result=[]
    for budget in budgets:
        if not np.isfinite(budget) or not 0<=budget<=1:raise ValueError('Budget in [0,1] required')
        k=math.floor(budget*n);remaining=k;prob=np.zeros(n);quotas={}
        for level in sorted(set(g),reverse=True):
            mask=g==level;size=int(mask.sum());take=min(size,remaining);remaining-=take
            quotas[int(level)]=take;prob[mask]=take/size
        a=np.zeros(n,bool);a[grade_order[:k]]=True
        b=np.zeros(n,bool);b[global_order[:k]]=True
        result.append(dict(budget=budget,k=k,grade_ml=a,global_ml=b,random_probability=prob,quotas=quotas))
    return result


def allocation_pmf(grades,y,quotas):
    """Exact random-allocation distribution on this fixed labeled queue."""
    g=np.asarray(grades);y=np.asarray(y);distribution=np.array([1.])
    for level in sorted(set(g),reverse=True):
        group=y[g==level];n=len(group);p=int(group.sum());k=quotas[int(level)]
        part=np.zeros(p+1);denominator=math.comb(n,k)
        for tp in range(max(0,k-(n-p)),min(k,p)+1):
            part[tp]=math.comb(p,tp)*math.comb(n-p,k-tp)/denominator
        distribution=np.convolve(distribution,part)
    return distribution


def assess(y,grades,scores,keys,budgets,with_pmf=False):
    yy=np.asarray(y,float)
    if yy.ndim!=1 or len(yy)!=len(grades) or not np.isin(yy,[0,1]).all():
        raise ValueError('Aligned binary labels required for evaluation')
    policies=rank_queue(grades,scores,keys,budgets);rows=[];pmfs=[]
    for policy in policies:
        expected=float(np.dot(policy['random_probability'],yy))
        grade_tp=int(yy[policy['grade_ml']].sum());global_tp=int(yy[policy['global_ml']].sum())
        rows.append(dict(budget=policy['budget'],n=len(yy),positives=int(yy.sum()),k=policy['k'],
                         expected_random_tp=expected,grade_ml_tp=grade_tp,global_ml_tp=global_tp,
                         extra_grade_ml_tp=grade_tp-expected,extra_global_ml_tp=global_tp-expected))
        if with_pmf:pmfs.append(allocation_pmf(grades,yy,policy['quotas']))
    return rows,policies,pmfs


def run(root=ROOT):
    root=Path(root);out=root/'results/phase2/ranking';out.mkdir(parents=True,exist_ok=True)
    started=datetime.now(timezone.utc).isoformat();clock=time.perf_counter();record=out/'verification.json'
    record.write_text(json.dumps(dict(passed=False,status='running')),encoding='utf-8')
    manifest=out/'run_manifest.json'
    def state(status,**extra):manifest.write_text(json.dumps(dict(status=status,started_at_utc=started,**extra),indent=2),encoding='utf-8')
    state('running');inputs={}
    def js(name):
        inputs[name]=sha(root/name);return json.loads((root/name).read_text(encoding='utf-8'))
    def csv(name):
        inputs[name]=sha(root/name);return pd.read_csv(root/name,float_precision='round_trip')
    try:
        plan=js('phase2/ranking/protocol.json');original=js('phase2/locked_plan.json')['plan']
        assert plan['budgets']==original['budgets']
        for key in ('replicates','block_length','seed'):assert plan['bootstrap'][key]==original['bootstrap'][key]
        data=csv('data/seismic-bumps.csv');oldrun=js('results/phase2/run_manifest.json')
        assert inputs['data/seismic-bumps.csv']==oldrun['data_sha256']
        pred=csv('results/phase2/predictions.csv');pred=pred[(pred.model=='XGBoost')&(pred.scheme=='time')].sort_values('row')
        assert len(pred)==2063 and pred.row.is_unique and set(pred.fold)=={0,1,2,3}
        assert np.array_equal(pred.y,data.loc[pred.row,'class'])
        mapping={value:i for i,value in enumerate(plan['grade_order'])}
        all_rows=[];evaluations=[];allocations=[];pmfs={}
        for fold in range(4):
            p=pred[pred.fold==fold].sort_values('row');codes=data.loc[p.row,plan['primary_grade']]
            if not codes.isin(mapping).all():raise ValueError('Unknown grade in source data')
            g=codes.map(mapping).to_numpy(float);y=p.y.to_numpy();s=p.fixed_score.to_numpy()
            keys=np.random.default_rng(plan['tie_seed']+fold+1).random(len(p))
            result,policies,distributions=assess(y,g,s,keys,plan['budgets'],True)
            wide=dict(fold=fold,row=p.row.to_numpy(),y=y,grade_code=codes.to_numpy(),grade=g,score=s,tie_key=keys)
            for row,policy,pmf in zip(result,policies,distributions):
                evaluations.append(dict(fold=fold,**row));b=round(100*row['budget'])
                wide['grade_ml_b%02d'%b]=policy['grade_ml'];wide['global_ml_b%02d'%b]=policy['global_ml']
                wide['random_probability_b%02d'%b]=policy['random_probability'];pmfs[fold,b]=pmf
                for level,k in policy['quotas'].items():
                    mask=g==level;allocations.append(dict(fold=fold,budget=row['budget'],grade=level,n=int(mask.sum()),positives=int(y[mask].sum()),k=k))
            all_rows.append(pd.DataFrame(wide))
        wide=pd.concat(all_rows,ignore_index=True).sort_values('row')
        pooled=[]
        for budget in plan['budgets']:
            part=[r for r in evaluations if r['budget']==budget]
            pooled.append(dict(fold=-1,budget=budget,**{key:sum(r[key] for r in part) for key in
                ('n','positives','k','expected_random_tp','grade_ml_tp','global_ml_tp','extra_grade_ml_tp','extra_global_ml_tp')}))
            b=round(100*budget);pmfs[-1,b]=np.array([1.])
            for fold in range(4):pmfs[-1,b]=np.convolve(pmfs[-1,b],pmfs[fold,b])
        evaluations+=pooled;draws={};samples={};intervals=[];settings=plan['bootstrap']
        for fold in (0,1,2,3,-1):
            subset=wide if fold<0 else wide[wide.fold==fold];labels=subset.fold.to_numpy();n=len(subset)
            rng=np.random.default_rng(settings['seed']+fold+1)
            counts=np.array([np.bincount(resample_indices(rng,labels,settings['block_length']),minlength=n)
                             for _ in range(settings['replicates'])],dtype=np.int16)
            boot=np.zeros((settings['replicates'],len(plan['budgets']),2))
            y=subset.y.to_numpy();g=subset.grade.to_numpy();s=subset.score.to_numpy();keys=subset.tie_key.to_numpy()
            for j,multiplicity in enumerate(counts):
                for phase in sorted(set(labels)):
                    group=np.flatnonzero(labels==phase);expanded=np.repeat(group,multiplicity[group])
                    # Reapply ranking to the sampled multiset; old alert flags are never resampled.
                    rows,_,_=assess(y[expanded],g[expanded],s[expanded],keys[expanded],plan['budgets'])
                    boot[j]+=np.array([[r['extra_grade_ml_tp'],r['extra_global_ml_tp']] for r in rows])
            draws['fold_%d'%fold]=counts;samples['fold_%d'%fold]=boot
            lo,hi=np.quantile(boot,[.025,.975],axis=0)
            for bi,budget in enumerate(plan['budgets']):
                point=next(r for r in evaluations if r['fold']==fold and r['budget']==budget)
                for method,key in enumerate(('grade_ml','global_ml')):
                    intervals.append(dict(fold=fold,budget=budget,method=key,extra_tp=point['extra_'+key+'_tp'],
                                          ci_low=lo[bi,method],ci_high=hi[bi,method]))
            print('Ranking reranking-bootstrap cohort '+str(fold),flush=True)
        distributions=[]
        for (fold,b),pmf in pmfs.items():
            distributions += [dict(fold=fold,budget=b/100,tp=tp,probability=float(prob)) for tp,prob in enumerate(pmf)]
        for name,frame in [('rows',wide),('allocations',pd.DataFrame(allocations)),('evaluations',pd.DataFrame(evaluations)),
                           ('intervals',pd.DataFrame(intervals)),('random_allocation_distribution',pd.DataFrame(distributions))]:
            frame.to_csv(out/(name+'.csv'),index=False)
        np.savez_compressed(out/'bootstrap_counts.npz',**draws);np.savez_compressed(out/'bootstrap_replicates.npz',**samples)
        state('complete',inputs_sha256=inputs,code_sha256={name:sha(root/name) for name in ('phase2/ranking/run.py','src/uncertainty.py')},
              outputs_sha256={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.csv','.npz')},
              environment=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__),
              elapsed_seconds=time.perf_counter()-clock,scope='Frozen-score equal-capacity ranking; analytical random allocation; all bootstrap queues reranked within phases; no fitting')
        record.write_text(json.dumps(dict(passed=False,status='awaiting independent verification')),encoding='utf-8')
    except (Exception,KeyboardInterrupt) as error:
        state('failed',error_type=type(error).__name__,error=str(error))
        record.write_text(json.dumps(dict(passed=False,status='failed',error_type=type(error).__name__,error=str(error))),encoding='utf-8')
        raise


if __name__=='__main__':run()
