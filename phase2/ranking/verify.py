"""Independently reconstruct ranking allocations and every reranked bootstrap result."""
from __future__ import annotations
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import hypergeom

ROOT=Path(__file__).resolve().parents[2]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def weighted_detection(y,counts,order,k):
    weights=counts[order];before=np.cumsum(weights)-weights
    selected=np.minimum(weights,np.maximum(0,k-before))
    return int(np.dot(selected,y[order]))


def verify_checks(root):
    out=root/'results/phase2/ranking';count=0
    def check(condition,message):
        nonlocal count
        count+=1
        if not condition:raise AssertionError(message)
    def close(a,b,message):check(np.allclose(a,b,rtol=0,atol=1e-12),message)
    read=lambda name:pd.read_csv(root/name,float_precision='round_trip')
    manifest=json.loads((out/'run_manifest.json').read_text(encoding='utf-8'))
    check(manifest['status']=='complete','completed ranking run')
    for group in ('inputs_sha256','code_sha256'):
        for name,value in manifest[group].items():check(sha(root/name)==value,'source/code '+name)
    for name,value in manifest['outputs_sha256'].items():check(sha(out/name)==value,'output '+name)
    plan=json.loads((root/'phase2/ranking/protocol.json').read_text(encoding='utf-8'))
    d=read('results/phase2/ranking/rows.csv');ev=read('results/phase2/ranking/evaluations.csv')
    intervals=read('results/phase2/ranking/intervals.csv');alloc=read('results/phase2/ranking/allocations.csv')
    pmf=read('results/phase2/ranking/random_allocation_distribution.csv')
    data=read('data/seismic-bumps.csv');p=read('results/phase2/predictions.csv')
    p=p[(p.model=='XGBoost')&(p.scheme=='time')].sort_values('row')
    check(d.row.is_unique and len(d)==2063,'unique original test rows')
    check(np.array_equal(d.row,p.row) and np.array_equal(d.fold,p.fold),'original phase and row identity')
    check(np.array_equal(d.score,p.fixed_score) and np.array_equal(d.y,p.y),'frozen scores and labels')
    check(np.array_equal(d.y,data.loc[d.row,'class']),'mirror label identity')
    check(np.array_equal(d.grade_code,data.loc[d.row,plan['primary_grade']]),'primary grade source')
    mapping={value:i for i,value in enumerate(plan['grade_order'])}
    check(np.array_equal(d.grade,d.grade_code.map(mapping)),'grade encoding')
    check(len(ev)==20 and not ev.duplicated(['fold','budget']).any(),'all phase/budget evaluations')
    check(len(intervals)==40 and not intervals.duplicated(['fold','budget','method']).any(),'all primary and auxiliary intervals')
    check(not alloc.duplicated(['fold','budget','grade']).any(),'unique historical-free grade allocations')
    points={};distributions={};vectors={}
    for fold in range(4):
        q=d[d.fold==fold];y=q.y.to_numpy();g=q.grade.to_numpy();score=q.score.to_numpy();keys=q.tie_key.to_numpy();n=len(q)
        check(np.array_equal(keys,np.random.default_rng(plan['tie_seed']+fold+1).random(n)),'label-independent tie keys')
        grade_order=np.array(sorted(range(n),key=lambda i:(-g[i],-score[i],keys[i],i)))
        global_order=np.array(sorted(range(n),key=lambda i:(-score[i],keys[i],i)))
        vectors[fold]=(q,y,g,grade_order,global_order)
        for budget in plan['budgets']:
            k=math.floor(budget*n);b=round(100*budget);remaining=k;expected=0.;distribution=np.array([1.])
            for level in sorted(set(g),reverse=True):
                mask=g==level;ng=int(mask.sum());pg=int(y[mask].sum());kg=min(ng,remaining);remaining-=kg
                a=alloc[(alloc.fold==fold)&(alloc.budget==budget)&(alloc.grade==level)]
                check(len(a)==1,'one grade allocation');a=a.iloc[0]
                check((a.n,a.positives,a.k)==(ng,pg,kg),'independent grade quota')
                check(int(q.loc[mask,'grade_ml_b%02d'%b].sum())==kg,'same exact within-grade allocations')
                close(q.loc[mask,'random_probability_b%02d'%b].to_numpy(),kg/ng,'uniform random inclusion')
                expected+=kg*pg/ng
                distribution=np.convolve(distribution,hypergeom.pmf(np.arange(pg+1),ng,pg,kg))
            for name,order in (('grade_ml',grade_order),('global_ml',global_order)):
                chosen=np.zeros(n,bool);chosen[order[:k]]=True
                check(np.array_equal(chosen,q[name+'_b%02d'%b]),'independent exact K '+name)
            primary=int(y[grade_order[:k]].sum());aux=int(y[global_order[:k]].sum())
            r=ev[(ev.fold==fold)&(ev.budget==budget)].iloc[0]
            close([r.n,r.positives,r.k,r.expected_random_tp,r.grade_ml_tp,r.global_ml_tp,r.extra_grade_ml_tp,r.extra_global_ml_tp],
                  [n,y.sum(),k,expected,primary,aux,primary-expected,aux-expected],'original queue evaluation')
            points[fold,budget]=(n,int(y.sum()),k,expected,primary,aux)
            distributions[fold,budget]=distribution
    for budget in plan['budgets']:
        total=np.array([points[f,budget] for f in range(4)]).sum(axis=0)
        r=ev[(ev.fold==-1)&(ev.budget==budget)].iloc[0]
        close([r.n,r.positives,r.k,r.expected_random_tp,r.grade_ml_tp,r.global_ml_tp],total,'pooled sums, never global reranking')
        close([r.extra_grade_ml_tp,r.extra_global_ml_tp],[total[4]-total[3],total[5]-total[3]],'pooled extra detections')
        distributions[-1,budget]=np.array([1.])
        for f in range(4):distributions[-1,budget]=np.convolve(distributions[-1,budget],distributions[f,budget])
    for (fold,budget),distribution in distributions.items():
        part=pmf[(pmf.fold==fold)&(pmf.budget==budget)].sort_values('tp')
        check(part.tp.tolist()==list(range(len(distribution))),'complete random allocation support')
        close(part.probability,distribution,'independent SciPy hypergeometric distribution')
        close(distribution.sum(),1.,'probabilities sum to one')
        r=ev[(ev.fold==fold)&(ev.budget==budget)].iloc[0]
        close(np.dot(np.arange(len(distribution)),distribution),r.expected_random_tp,'analytic random expectation')
    counts_file=np.load(out/'bootstrap_counts.npz');samples_file=np.load(out/'bootstrap_replicates.npz')
    settings=plan['bootstrap']
    for fold in (0,1,2,3,-1):
        subset=d if fold<0 else d[d.fold==fold];labels=subset.fold.to_numpy();n=len(subset)
        counts=counts_file['fold_%d'%fold];saved=samples_file['fold_%d'%fold]
        check(counts.shape==(settings['replicates'],n) and np.all(counts>=0) and np.all(counts.sum(axis=1)==n),'bootstrap count shape and sizes')
        rng=np.random.default_rng(settings['seed']+fold+1);computed=np.zeros_like(saved)
        for j,multiplicity in enumerate(counts):
            expected_counts=np.zeros(n,dtype=int)
            for phase in sorted(set(labels)):
                indices=np.flatnonzero(labels==phase);size=len(indices);length=min(size,settings['block_length'])
                starts=rng.integers(0,size-length+1,size=math.ceil(size/length))
                draws=np.concatenate([indices[s:s+length] for s in starts])[:size]
                expected_counts+=np.bincount(draws,minlength=n)
                _,y,g,grade_order,global_order=vectors[int(phase)];weights=multiplicity[indices]
                check(weights.sum()==size,'phase size preserved in pooled bootstrap')
                for bi,budget in enumerate(plan['budgets']):
                    k=math.floor(budget*size);remaining=k;baseline=0.
                    for level in sorted(set(g),reverse=True):
                        mask=g==level;ng=int(weights[mask].sum());pg=float(np.dot(weights[mask],y[mask]))
                        kg=min(ng,remaining);remaining-=kg
                        if ng:baseline+=kg*pg/ng
                    # Weighted ranking prefixes equal re-sorting duplicated queues, not resampling old flags.
                    computed[j,bi]=computed[j,bi]+[weighted_detection(y,weights,grade_order,k)-baseline,
                                                   weighted_detection(y,weights,global_order,k)-baseline]
            check(np.array_equal(multiplicity,expected_counts),'independent moving-block draw replay')
        close(computed,saved,'all reranked bootstrap contrasts')
        lo,hi=np.quantile(computed,[.025,.975],axis=0)
        for bi,budget in enumerate(plan['budgets']):
            r=ev[(ev.fold==fold)&(ev.budget==budget)].iloc[0]
            for method,name in enumerate(('grade_ml','global_ml')):
                q=intervals[(intervals.fold==fold)&(intervals.budget==budget)&(intervals.method==name)].iloc[0]
                close([q.extra_tp,q.ci_low,q.ci_high],[r['extra_'+name+'_tp'],lo[bi,method],hi[bi,method]],'point and percentile interval')
    return dict(checks=count,rows=len(d),evaluations=len(ev),intervals=len(intervals),
                reranked_bootstrap_contrasts=sum(samples_file[key].size for key in samples_file.files),
                manifest_sha256=sha(out/'run_manifest.json'),protocol_sha256=sha(root/'phase2/ranking/protocol.json'),
                scope='Frozen source scores, exact grade quotas and K, independent ranking, analytical random allocation via SciPy, every block draw and weighted reranking replay; no fitting or real dispatch validation')


def verify(root=ROOT):
    root=Path(root);out=root/'results/phase2/ranking';out.mkdir(parents=True,exist_ok=True)
    path=out/'verification.json';started=datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(dict(passed=False,status='running',started_at_utc=started)),encoding='utf-8')
    try:
        record=verify_checks(root);record.update(passed=True,status='passed',started_at_utc=started,
            completed_at_utc=datetime.now(timezone.utc).isoformat(),verifier_sha256=sha(Path(__file__)))
        path.write_text(json.dumps(record,indent=2),encoding='utf-8')
        print('RANKING PILOT PASSED: %d checks; %d reranked contrasts.'%(record['checks'],record['reranked_bootstrap_contrasts']))
        return record
    except (Exception,KeyboardInterrupt) as error:
        path.write_text(json.dumps(dict(passed=False,status='failed',started_at_utc=started,error_type=type(error).__name__,error=str(error)),indent=2),encoding='utf-8')
        raise


if __name__=='__main__':verify()
