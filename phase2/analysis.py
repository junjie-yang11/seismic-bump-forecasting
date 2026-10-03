"""Prespecified paired loss contrasts and frozen-rule prevalence scenarios."""
import json
import time
import numpy as np
import pandas as pd
from .plan import OUT, PLAN
from .decisions import row_loss
from .run import declarations
from uncertainty import resample_indices

def pooled_evaluations(evaluations):
    rows=[]
    keys=['model','workflow','rule','mechanism','budget','cost']
    for key,part in evaluations[evaluations.scheme=='time'].groupby(keys,dropna=False,sort=False):
        row=dict(zip(keys,key)); row.update(scheme='time',fold=-1,threshold=np.nan)
        for column in ('n','positives','tp','fp','fn','tn','alerts','loss'): row[column]=part[column].sum()
        n=row['n']; tp=row['tp']; fp=row['fp']; fn=row['fn']; tn=row['tn']; alerts=row['alerts']
        row.update(loss100=100*row['loss']/n,loss_delta_no_alarm100=100*(row['loss']-row['cost']*row['positives'])/n,
                   recall=tp/(tp+fn),precision=tp/alerts if alerts else 0.,alert_rate=alerts/n,
                   fnr=fn/(tp+fn),fpr=fp/(fp+tn),
                   slots=part.slots.sum() if np.isfinite(row['budget']) else np.nan,
                   excess=part.excess.sum() if np.isfinite(row['budget']) else np.nan)
        rows.append(row)
    return pd.DataFrame(rows)

def comparison_specs():
    specs=[]
    for workflow in ('fixed','refitted'):
        for b in PLAN['budgets']:
            for r in PLAN['costs']:
                a='A_b%02d'%round(100*b); c='C_b%02d_r%02d'%(round(100*b),r); base='B_r%02d'%r
                for name,left,right in [('C-A',c,a),('C-B',c,base),('B-A',base,a)]:
                    specs.append(dict(comparison=name,workflow=workflow,budget=b,cost=r,
                                      left_rule=left,right_rule=right,left_workflow=workflow,right_workflow=workflow))
    for rule in declarations():
        if rule['mechanism'] not in ('A','B','C'): continue
        for r in ([rule['cost']] if rule['cost'] is not None else PLAN['costs']):
            specs.append(dict(comparison='Refitted-Fixed',workflow='paired',budget=rule['budget'],cost=r,
                left_rule=rule['rule'],right_rule=rule['rule'],left_workflow='refitted',right_workflow='fixed'))
    return specs

def analyse():
    start=time.perf_counter()
    evaluations=pd.read_csv(OUT/'evaluations.csv')
    pooled=pooled_evaluations(evaluations); pooled.to_csv(OUT/'pooled_evaluations.csv',index=False)
    scenario=[]
    for _,row in pd.concat([evaluations,pooled],ignore_index=True).iterrows():
        for pi in PLAN['scenarios']:
            scenario.append({**{k:row[k] for k in ('model','scheme','fold','workflow','rule','cost','budget')},
                'scenario_prevalence':pi,'expected_loss100':100*(row.cost*pi*row.fnr+(1-pi)*row.fpr),
                'expected_alert_rate':pi*(1-row.fnr)+(1-pi)*row.fpr,
                'empirical_fnr':row.fnr,'empirical_fpr':row.fpr})
    pd.DataFrame(scenario).to_csv(OUT/'prevalence_scenarios.csv',index=False)
    predictions=pd.read_csv(OUT/'predictions.csv'); decisions=pd.read_csv(OUT/'decisions.csv')
    meta=[]; differences=[]; left_decisions=[]; right_decisions=[]
    canonical=predictions[(predictions.scheme=='time')&(predictions.model=='XGBoost')].sort_values('row')
    folds=canonical.fold.to_numpy(); y=canonical.y.to_numpy()
    for model in PLAN['models']:
        wide={w:decisions[(decisions.scheme=='time')&(decisions.model==model)&(decisions.workflow==w)].sort_values('row') for w in ('fixed','refitted')}
        for spec in comparison_specs():
            left=wide[spec['left_workflow']][spec['left_rule']].to_numpy(dtype=bool)
            right=wide[spec['right_workflow']][spec['right_rule']].to_numpy(dtype=bool)
            meta.append(dict(model=model,**spec))
            differences.append(row_loss(y,left,spec['cost'])-row_loss(y,right,spec['cost']))
            left_decisions.append(left); right_decisions.append(right)
    dif=np.asarray(differences,float); lefts=np.asarray(left_decisions); rights=np.asarray(right_decisions)
    rows=[]; saved={}
    settings=PLAN['bootstrap']
    for fold in [0,1,2,3,-1]:
        idx=np.flatnonzero(folds==fold) if fold>=0 else np.arange(len(y))
        labels=folds[idx]; n=len(idx)
        rng=np.random.default_rng(settings['seed']+fold+1)
        counts=np.empty((settings['replicates'],n),np.int16)
        for j in range(len(counts)):
            counts[j]=np.bincount(resample_indices(rng,labels,settings['block_length']),minlength=n)
        samples=100*(counts @ dif[:,idx].T)/n
        saved['fold_%d'%fold]=samples
        ci=np.quantile(samples,[.025,.975],axis=0)
        for i,spec in enumerate(meta):
            b=spec['budget']; a=int(lefts[i,idx].sum()); z=int(rights[i,idx].sum())
            if b is not None:
                la=sum(max(0,int(lefts[i,idx[labels==f]].sum())-int(np.floor(b*np.sum(labels==f)))) for f in np.unique(labels))
                ra=sum(max(0,int(rights[i,idx[labels==f]].sum())-int(np.floor(b*np.sum(labels==f)))) for f in np.unique(labels))
            else: la=ra=np.nan
            rows.append(dict(**spec,scheme='time',fold=fold,comparison_id=i,n=n,
                loss_delta100=100*dif[i,idx].mean(),ci_low=ci[0,i],ci_high=ci[1,i],
                left_alerts=a,right_alerts=z,alert_delta=a-z,
                left_excess=la,right_excess=ra,excess_delta=la-ra))
        print('Paired loss intervals: phase %s'%('pooled' if fold<0 else fold+1),flush=True)
    pd.DataFrame(rows).to_csv(OUT/'comparisons.csv',index=False)
    np.savez_compressed(OUT/'bootstrap_replicates.npz',**saved)
    (OUT/'analysis_manifest.json').write_text(json.dumps(dict(bootstrap=settings,
        comparison_specs=meta,elapsed_seconds=time.perf_counter()-start,
        pooled_capacity='Sum phase-specific floor slots and phase-specific excess counts; no cross-phase cancellation'),indent=2),encoding='utf-8')

if __name__=='__main__': analyse()
