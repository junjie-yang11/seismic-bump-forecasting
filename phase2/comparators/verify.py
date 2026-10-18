"""Independent enumeration and complete paired-draw replay for the supplement."""
from __future__ import annotations
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def checks(root):
    out=root/'results/phase2/comparators';count=0
    def check(condition,message):
        nonlocal count
        count+=1
        if not condition:raise AssertionError(message)
    def read(path):return pd.read_csv(root/path,float_precision='round_trip')
    record=json.loads((out/'run_manifest.json').read_text(encoding='utf-8'))
    check(record['status']=='complete','completed supplement run required')
    for path,value in record['inputs_sha256'].items():check(sha(root/path)==value,'source '+path)
    for path,value in record['code_sha256'].items():check(sha(root/path)==value,'code '+path)
    for path,value in record['outputs_sha256'].items():check(sha(out/path)==value,'output '+path)
    plan=json.loads((root/'phase2/comparators/protocol.json').read_text(encoding='utf-8'))
    original=json.loads((root/'phase2/locked_plan.json').read_text(encoding='utf-8'))['plan']
    check(plan['budgets']==original['budgets'] and plan['costs']==original['costs'],'original settings retained')
    for name in ('replicates','block_length','seed'):check(plan['bootstrap'][name]==original['bootstrap'][name],'original bootstrap '+name)
    data=read('data/seismic-bumps.csv');pred=read('results/phase2/predictions.csv')
    pred=pred[(pred.model=='XGBoost')&(pred.scheme=='time')].sort_values('row')
    old=read('results/phase2/decisions.csv');old=old[(old.model=='XGBoost')&(old.scheme=='time')&(old.workflow=='fixed')].sort_values('row')
    oldrefs=read('results/phase2/references.csv');oldrefs=oldrefs[(oldrefs.model=='XGBoost')&(oldrefs.scheme=='time')]
    oldaudits=read('results/phase2/audits.csv');oldaudits=oldaudits[(oldaudits.model=='XGBoost')&(oldaudits.scheme=='time')]
    d=read('results/phase2/comparators/decisions.csv');ref=read('results/phase2/comparators/references.csv')
    c=read('results/phase2/comparators/candidates.csv');a=read('results/phase2/comparators/audits.csv')
    ev=read('results/phase2/comparators/evaluations.csv');ci=read('results/phase2/comparators/intervals.csv')
    check(not d.duplicated(['method','row']).any() and len(d)==4*2063,'unique four-method decisions')
    check(not a.duplicated(['method','fold','rule']).any() and len(a)==4*4*24,'one audit per distinct historical selection')
    check(not ev.duplicated(['method','fold','rule','cost']).any() and len(ev)==720,'all cost/cohort evaluations')
    check(not ci.duplicated(['comparison_id','fold']).any() and len(ci)==1260,'all requested paired contrasts')
    aligned={m:d[d.method==m].sort_values('row') for m in ('XGBoost',*plan['fields'])}
    rule_names=['A_b%02d'%round(100*b) for b in plan['budgets']]+['B_r%02d'%r for r in plan['costs']]
    rule_names+=['C_b%02d_r%02d'%(round(100*b),r) for b in plan['budgets'] for r in plan['costs']]
    for method,rows in aligned.items():
        check(np.array_equal(rows.row,pred.row) and np.array_equal(rows.fold,pred.fold),'aligned phase and row '+method)
        check(np.array_equal(rows.y,pred.y) and np.array_equal(rows.y,data.loc[rows.row,'class']),'aligned actual labels '+method)
        check(not rows['none'].any(),'no-alarm comparator '+method)
        for name in rule_names:
            check(rows[name].isin([True,False]).all(),'binary alert decisions')
            if method=='XGBoost':check(np.array_equal(rows[name],old[name]),'original frozen ML decisions '+name)
    folds=json.loads((root/'results/phase2/fold_manifest.json').read_text(encoding='utf-8'))
    folds=[f for f in folds if f['model']=='XGBoost' and f['scheme']=='time']
    for f in folds:
        fold=f['fold'];indices=f['reference_rows'];test=f['test_rows']
        check(max(f['fit_rows'])<min(indices) and max(indices)<min(test),'fit/reference/test boundaries')
        for method in aligned:
            h=ref[(ref.method==method)&(ref.fold==fold)].sort_values('row')
            t=aligned[method][aligned[method].fold==fold]
            check(h.row.tolist()==indices and t.row.tolist()==test,'exact reference/test identity')
            check(np.array_equal(h.y,data.loc[indices,'class']),'reference labels')
            selected=a[(a.method==method)&(a.fold==fold)]
            if method=='XGBoost':
                source=oldrefs[oldrefs.fold==fold].sort_values('row')
                check(np.array_equal(h.score,source.score),'ML reference scores unchanged')
                check(np.array_equal(t.score,pred[pred.fold==fold].fixed_score),'ML test scores unchanged')
            else:
                mapping={g:i for i,g in enumerate(plan['grade_order'])}
                check(np.array_equal(h.score,data.loc[indices,method].map(mapping)),'reference grade encoding')
                check(np.array_equal(t.score,data.loc[test,method].map(mapping)),'future grade encoding')
                levels=sorted(set(h.score),reverse=True)
                thresholds=[math.inf]+levels[:-1]+[-math.inf]
                # Direct enumeration is independent of the production candidate/selector functions.
                possibilities=[]
                for threshold in thresholds:
                    alert=h.score.to_numpy()>=threshold;yy=h.y.to_numpy()
                    tp=int(np.sum(alert&(yy==1)));fp=int(np.sum(alert&(yy==0)))
                    possibilities.append(dict(threshold=threshold,alerts=int(alert.sum()),tp=tp,fp=fp,fn=int(yy.sum())-tp))
                candidates=c[(c.method==method)&(c.fold==fold)].sort_values('candidate')
                check(len(candidates)==len(possibilities),'distinct candidate alert sets')
                for actual,expected in zip(candidates.to_dict('records'),possibilities):
                    for key,value in expected.items():check(actual[key]==value,'independent reference candidate '+key)
            for audit in selected.to_dict('records'):
                threshold=audit['threshold'];alert=t.score.to_numpy()>=threshold
                check(np.array_equal(alert,t[audit['rule']]),'frozen numeric threshold application')
                if method=='XGBoost':
                    orig=oldaudits[(oldaudits.fold==fold)&(oldaudits.rule==audit['rule'])].iloc[0]
                    check(threshold==orig.threshold,'original ML threshold retained')
                    continue
                slots=math.floor(audit['budget']*len(h)) if audit['mechanism']!='B' else None
                feasible=[p for p in possibilities if slots is None or p['alerts']<=slots]
                if audit['mechanism']=='A':best=max(feasible,key=lambda p:p['alerts'])
                else:best=min(feasible,key=lambda p:(audit['cost']*p['fn']+p['fp'],p['alerts']))
                check(threshold==best['threshold'],'reference-only independently selected grade threshold')
                for key in ('alerts','tp','fp','fn'):check(audit['reference_'+key]==best[key],'historical audit '+key)
                check(audit['reference_n']==len(h) and audit['reference_positives']==int(h.y.sum()),'reference census')
                check(slots is None or audit['reference_alerts']<=slots,'reference capacity feasibility')
                if audit['mechanism']=='C':
                    b=selected[(selected.mechanism=='B')&(selected.cost==audit['cost'])].iloc[0]
                    check(audit['reference_loss']>=b.reference_loss,'constrained optimum cannot beat unconstrained reference loss')
    # Reconstruct each evaluation using direct binary counts and phase floors.
    for e in ev.to_dict('records'):
        rows=aligned[e['method']]
        if e['fold']>=0:rows=rows[rows.fold==e['fold']]
        yy=rows.y.to_numpy();alert=rows[e['rule']].to_numpy(bool)
        tp=int(np.sum(alert&(yy==1)));fp=int(np.sum(alert&(yy==0)));fn=int(np.sum((~alert)&(yy==1)))
        n=len(yy);loss=e['cost']*fn+fp
        expected=dict(n=n,positives=int(yy.sum()),tp=tp,fp=fp,fn=fn,tn=n-tp-fp-fn,alerts=tp+fp,loss=loss,
                      loss100=100*loss/n,loss_delta_no_alarm100=100*(fp-e['cost']*tp)/n,
                      recall=tp/(tp+fn),precision=tp/(tp+fp) if tp+fp else 0.,alert_rate=(tp+fp)/n)
        for key,value in expected.items():check(abs(e[key]-value)<=1e-12,'independent evaluation '+key)
        if not math.isnan(e['budget']):
            slots=sum(math.floor(e['budget']*len(part)) for _,part in rows.groupby('fold'))
            excess=sum(max(0,int(part[e['rule']].sum())-math.floor(e['budget']*len(part))) for _,part in rows.groupby('fold'))
            check(e['slots']==slots and e['excess']==excess,'capacity uses phase-specific floors without cancellation')
    specs=record['comparison_specs'];diffs=[];y=pred.y.to_numpy();phase=pred.fold.to_numpy()
    check(len(specs)==252,'all cost/method contrasts without test selection')
    for spec in specs:
        left=aligned[spec['left_method']][spec['rule']].to_numpy(bool)
        right=np.zeros(len(y),bool) if spec['right_method']=='none' else aligned[spec['right_method']][spec['rule']].to_numpy(bool)
        diffs.append((left.astype(int)-right.astype(int))*np.where(y==1,-spec['cost'],1))
    diffs=np.asarray(diffs,dtype=float)
    settings=plan['bootstrap'];draws=np.load(out/'bootstrap_counts.npz');replicas=np.load(out/'bootstrap_replicates.npz')
    for fold in (0,1,2,3,-1):
        idx=np.flatnonzero(phase==fold) if fold>=0 else np.arange(len(y));labels=phase[idx];n=len(idx)
        counts=draws['fold_%d'%fold]
        check(counts.shape==(2000,n) and np.all(counts>=0) and np.all(counts.sum(axis=1)==n),'valid bootstrap multiplicities')
        rng=np.random.default_rng(settings['seed']+fold+1)
        for j in range(settings['replicates']):
            expected=np.zeros(n,dtype=np.int64)
            for f in sorted(set(labels)):
                rows=np.flatnonzero(labels==f);length=min(settings['block_length'],len(rows))
                starts=rng.integers(0,len(rows)-length+1,size=math.ceil(len(rows)/length))
                sampled=np.concatenate([rows[s:s+length] for s in starts])[:len(rows)]
                expected+=np.bincount(sampled,minlength=n)
            check(np.array_equal(counts[j],expected),'independent within-phase draw replay')
        computed=100*(counts.astype(float) @ diffs[:,idx].T)/n
        check(np.array_equal(computed,replicas['fold_%d'%fold]),'all paired replicates replay exactly')
        low,high=np.quantile(computed,[.025,.975],axis=0)
        for i,spec in enumerate(specs):
            r=ci[(ci.fold==fold)&(ci.comparison_id==i)]
            check(len(r)==1,'one interval per contrast and cohort');r=r.iloc[0]
            check(abs(r.loss_delta100-100*diffs[i,idx].sum()/n)<=1e-12,'paired point difference')
            check(abs(r.ci_low-low[i])<=1e-12 and abs(r.ci_high-high[i])<=1e-12,'paired percentile interval')
    check(len(ref)==4132,'all retained reference scores and grade codes')
    metadata=json.loads((out/'grade_metadata.json').read_text(encoding='utf-8'))
    for field in plan['fields']:
        check(metadata['observed_counts'][field]=={g:int(v) for g,v in data[field].value_counts().sort_index().items()},'observed grade counts')
    return dict(checks=count,evaluations=len(ev),intervals=len(ci),decisions=len(d),replicates_replayed=2000*252*5,
                run_manifest_sha256=sha(out/'run_manifest.json'),protocol_sha256=sha(root/'phase2/comparators/protocol.json'),
                scope='Exact frozen ML decisions, independent grade selection enumeration, all policy arithmetic and all within-phase draws/paired replicates; no model refitting or field validation')


def verify(root=ROOT):
    root=Path(root);out=root/'results/phase2/comparators';out.mkdir(parents=True,exist_ok=True)
    path=out/'verification.json';started=datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(dict(passed=False,status='running',started_at_utc=started)),encoding='utf-8')
    try:
        record=checks(root)
        record.update(passed=True,status='passed',started_at_utc=started,completed_at_utc=datetime.now(timezone.utc).isoformat(),verifier_sha256=sha(Path(__file__)))
        path.write_text(json.dumps(record,indent=2),encoding='utf-8')
        print('COMPARATOR SUPPLEMENT PASSED: %d checks; %d evaluations; %d intervals.'%(record['checks'],record['evaluations'],record['intervals']))
        return record
    except (Exception,KeyboardInterrupt) as error:
        path.write_text(json.dumps(dict(passed=False,status='failed',started_at_utc=started,error_type=type(error).__name__,error=str(error)),indent=2),encoding='utf-8')
        raise


if __name__=='__main__':verify()
