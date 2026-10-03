"""Independent reconstruction of the phase-two saved evidence."""
import argparse
import hashlib
import json
import sys
import numpy as np
import pandas as pd
from .plan import ROOT, OUT, PLAN, canonical
sys.path.insert(0,str(ROOT/'src'))
from data import load, CSV_PATH
from metrics import average_precision
from evaluation import time_ordered_folds

def verify(replay=False):
    count=0
    def check(value,label):
        nonlocal count
        if not value: raise AssertionError(label)
        count+=1
    def close(a,b,label): check(np.allclose(a,b,rtol=1e-9,atol=1e-10,equal_nan=True),label)
    read=lambda name:pd.read_csv(OUT/(name+'.csv'))
    locked=json.loads((ROOT/'phase2/locked_plan.json').read_text())
    check(locked['plan']==PLAN,'locked protocol')
    check(locked['plan_sha256']==hashlib.sha256(canonical(PLAN)).hexdigest(),'plan checksum')
    X,y,names,_=load(); manifest=json.loads((OUT/'fold_manifest.json').read_text())
    run=json.loads((OUT/'run_manifest.json').read_text())
    check(run['status']=='complete','full experiment completed')
    from pathlib import Path
    check(run['data_sha256']==hashlib.sha256(Path(CSV_PATH).read_bytes()).hexdigest(),'source checksum')
    for name in ('analysis.py','decisions.py','experiment.py','plan.py','run.py'):
        check(hashlib.sha256((ROOT/'phase2'/name).read_bytes()).hexdigest()==run['source_hashes'][name],
              'experimental implementation unchanged '+name)
    for name,digest in run['dependency_hashes'].items():
        check(hashlib.sha256((ROOT/'src'/name).read_bytes()).hexdigest()==digest,'imported first-stage dependency unchanged '+name)
    for name,digest in run['first_stage_hashes'].items():
        check(hashlib.sha256((ROOT/name.replace('\\', '/')).read_bytes()).hexdigest()==digest,'first-stage evidence retained '+name)
    p,ref,c,a,d,e,tuning,tune_scores=[read(n) for n in ('predictions','references','candidates','audits','decisions','evaluations','tuning','tuning_predictions')]
    check(len(manifest)==15,'complete models/folds')
    check(len(p)==8511 and not p.duplicated(['model','scheme','row']).any(),'prediction coverage')
    check(len(a)==360 and not a.duplicated(['model','scheme','fold','rule']).any(),'threshold policy coverage')
    check(len(e)==1680 and not e.duplicated(['model','scheme','fold','workflow','rule','cost']).any(),'evaluation coverage')
    for m in manifest:
        model,scheme,fold=m['model'],m['scheme'],m['fold']
        tr,fit,rr,te=[np.array(m[k],dtype=int) for k in ('outer_train_rows','fit_rows','reference_rows','test_rows')]
        expected=time_ordered_folds(len(y),5)[fold] if scheme=='time' else (np.arange(int(.7*len(y))),np.arange(int(.7*len(y)),len(y)))
        check(np.array_equal(tr,expected[0]) and np.array_equal(te,expected[1]),'declared outer rows')
        cut=int(.8*len(tr)); check(np.array_equal(fit,tr[:cut]) and np.array_equal(rr,tr[cut:]),'fit/reference boundary')
        check(fit[-1]<rr[0]<=rr[-1]<te[0],'ordered disjoint model/policy/test areas')
        pick=lambda df:df[(df.model==model)&(df.scheme==scheme)&(df.fold==fold)]
        part=pick(p).sort_values('row'); reference=pick(ref).sort_values('row'); candidate=pick(c).sort_values('candidate')
        close(part.row,te,'test row IDs'); close(part.y,y[te],'test targets'); close(reference.row,rr,'policy reference IDs'); close(reference.y,y[rr],'reference targets')
        check(np.isfinite(part[['fixed_score','refitted_score']]).all().all(),'finite model predictions')
        check(part[['fixed_score','refitted_score']].ge(0).all().all() and part[['fixed_score','refitted_score']].le(1).all().all(),'probability range')
        scores=reference.score.to_numpy(); labels=reference.y.to_numpy()
        unique=np.unique(scores)[::-1]; thresholds=np.r_[np.inf,unique[:-1],-np.inf]
        close(candidate.threshold,thresholds,'canonical distinct decision thresholds')
        for _,row in candidate.iterrows():
            alert=scores>=row.threshold; tp=int(np.sum(alert&(labels==1))); fp=int(np.sum(alert&(labels==0))); fn=int(labels.sum())-tp
            close([row.alerts,row.tp,row.fp,row.fn,row.tn],[alert.sum(),tp,fp,fn,len(labels)-labels.sum()-fp],'candidate confusion counts')
            for r in PLAN['costs']: close(row['loss_r%d'%r],r*fn+fp,'candidate loss')
        for _,row in pick(a).iterrows():
            close([row.reference_n,row.reference_positives],[len(rr),y[rr].sum()],'reference audit sample counts')
            budget=row.budget; slots=int(np.floor(budget*len(rr))) if np.isfinite(budget) else None
            feasible=candidate if row.mechanism=='B' else candidate[candidate.alerts<=slots]
            if row.mechanism=='A': selected=feasible.loc[feasible.alerts.idxmax()]
            else:
                loss=feasible.fn*row.cost+feasible.fp; optimum=feasible[loss==loss.min()]
                selected=optimum.loc[optimum.alerts.idxmin()]
                close(row.optimal_decisions,len(optimum),'optimal decision tie count')
                gap=np.sort(loss)[1]-loss.min() if len(loss)>1 else np.nan
                close(row.loss_gap,gap,'second distinct decision gap')
                close(row.reference_loss,row.cost*selected.fn+selected.fp,'selected historical loss')
                unconstrained_loss=candidate.fn*row.cost+candidate.fp
                best=candidate[unconstrained_loss==unconstrained_loss.min()]; best=best.loc[best.alerts.idxmin()]
                check(bool(row.capacity_binding)==bool(row.mechanism=='C' and best.alerts>slots),'capacity binds selection')
                if row.mechanism=='C': check(row.reference_loss>=unconstrained_loss.min(),'C historical loss >= B historical loss')
            close(row.candidate,selected.candidate,'selected candidate'); close(row.threshold,selected.threshold,'selected cutoff')
            check(row.feasible_count==len(feasible) and row.candidate_count==len(candidate),'decision audit coverage')
            close([row.reference_alerts,row.reference_tp,row.reference_fp,row.reference_fn],[selected.alerts,selected.tp,selected.fp,selected.fn],'selected audit counts')
            if row.mechanism!='B': check(row.reference_alerts<=slots,'historical capacity feasibility')
            check(bool(row.feasible_on_reference),'saved reference feasibility')
            if row.mechanism=='A': check(np.isnan(row.capacity_binding),'A cost-specific binding is undefined')
        for workflow in ('fixed','refitted'):
            wide=pick(d); wide=wide[wide.workflow==workflow].sort_values('row')
            close(wide.row,te,'fixed/refitted same rows')
            score=part[workflow+'_score'].to_numpy()
            for _,row in pick(e)[pick(e).workflow==workflow].iterrows():
                alert=wide[row.rule].to_numpy(dtype=bool)
                if row.mechanism in ('A','B','C'):
                    selected=pick(a).set_index('rule').loc[row.rule]
                    close(row.threshold,selected.threshold,'same numeric threshold across workflows')
                elif row.mechanism=='none': check(np.isposinf(row.threshold),'no-alarm cutoff')
                else:
                    distinct=np.unique(score)[::-1]; possibilities=np.r_[np.inf,distinct[:-1],-np.inf]
                    counts=np.array([(score>=v).sum() for v in possibilities]); feasible=np.flatnonzero(counts<=int(np.floor(row.budget*len(te))))
                    close(row.threshold,possibilities[feasible[-1]],'whole-tie batch Top-k')
                check(np.array_equal(alert,score>=row.threshold),'saved alert decisions')
                tp=int(np.sum(alert&(part.y.to_numpy()==1))); fp=int(np.sum(alert&(part.y.to_numpy()==0))); fn=int(part.y.sum())-tp; tn=len(te)-int(part.y.sum())-fp
                close([row.tp,row.fp,row.fn,row.tn,row.alerts],[tp,fp,fn,tn,tp+fp],'test confusion counts')
                close(row.loss100,100*(row.cost*fn+fp)/len(te),'test relative loss per 100')
                close(row.loss_delta_no_alarm100,100*(fp-row.cost*tp)/len(te),'no-alarm loss difference')
                close([row.recall,row.precision,row.alert_rate],[tp/(tp+fn),tp/(tp+fp) if tp+fp else 0,(tp+fp)/len(te)],'warning metrics')
                if np.isfinite(row.budget): close([row.slots,row.excess],[int(np.floor(row.budget*len(te))),max(0,tp+fp-int(np.floor(row.budget*len(te))))],'future capacity excess')
        if model=='XGBoost':
            tf,tv=[np.array(m[k]) for k in ('tuning_fit_rows','tuning_reference_rows')]
            check(np.array_equal(tf,fit[:int(.8*len(fit))]) and np.array_equal(tv,fit[int(.8*len(fit)):]),'tuning contained inside fitting area')
            check(set(np.r_[tf,tv]).isdisjoint(rr),'policy reference excluded from tuning')
            candidates_tune=pick(tuning).sort_values('candidate')
            check(len(candidates_tune)==4,'four parameter candidates')
            for _,choice in candidates_tune.iterrows():
                values=pick(tune_scores); values=values[values.candidate==choice.candidate].sort_values('row')
                close(values.row,tv,'tuning reference rows'); close(values.y,y[tv],'tuning labels')
                metric=average_precision(y[tv],values.score.to_numpy()) if y[tv].sum() else -np.mean((values.score-y[tv])**2)
                close(choice.value,metric,'training-only tuning objective')
            winner=candidates_tune.iloc[int(np.argmax(candidates_tune.value))]
            check(winner.depth==m['depth'] and winner['rounds']==m['rounds'],'chosen parameters fixed for refit')
        if replay:
            from models import LogisticRegressionIRLS,BaggedForest
            from boosting import BoostedModel
            factory=(lambda:BoostedModel(m['depth'],m['rounds'],names)) if model=='XGBoost' else ((lambda:LogisticRegressionIRLS(lam=1.)) if model=='LR' else (lambda:BaggedForest(60,6,20,None,seed=7)))
            fixed=factory().fit(X[fit],y[fit]); refitted=factory().fit(X[tr],y[tr])
            close(reference.score,fixed.predict_proba(X[rr]),'independent policy-reference replay')
            close(part.fixed_score,fixed.predict_proba(X[te]),'independent fixed-model replay')
            close(part.refitted_score,refitted.predict_proba(X[te]),'independent refitted-model replay')
            print('Replayed %s %s phase %d'%(model,scheme,fold+1),flush=True)
    pooled=read('pooled_evaluations')
    check(len(pooled)==336,'pooled supplementary coverage')
    for _,row in pooled.iterrows():
        part=e[(e.scheme=='time')&(e.model==row.model)&(e.workflow==row.workflow)&(e.rule==row.rule)&(e.cost==row.cost)]
        for column in ('n','positives','tp','fp','fn','tn','alerts','loss'): close(row[column],part[column].sum(),'pooled count '+column)
        close(row.loss100,100*part.loss.sum()/part.n.sum(),'pooled weighted loss')
        close([row.fnr,row.fpr,row.recall,row.precision,row.alert_rate],
              [row.fn/(row.tp+row.fn),row.fp/(row.fp+row.tn),row.tp/(row.tp+row.fn),
               row.tp/row.alerts if row.alerts else 0.,row.alerts/row.n],'pooled rates from counts')
        if np.isfinite(row.budget): close([row.slots,row.excess],[part.slots.sum(),part.excess.sum()],'pooled phase-specific capacity accounting')
    all_e=pd.concat([e,pooled],ignore_index=True); scenarios=read('prevalence_scenarios')
    check(len(scenarios)==8064,'frozen scenario coverage')
    lookup=all_e.set_index(['model','scheme','fold','workflow','rule','cost'])
    for _,row in scenarios.iterrows():
        empirical=lookup.loc[(row.model,row.scheme,row.fold,row.workflow,row.rule,row.cost)]
        close(row.expected_loss100,100*(row.cost*row.scenario_prevalence*empirical.fnr+(1-row.scenario_prevalence)*empirical.fpr),'frozen prevalence expected loss')
        close(row.expected_alert_rate,row.scenario_prevalence*(1-empirical.fnr)+(1-row.scenario_prevalence)*empirical.fpr,'frozen scenario workload')
    comparison=read('comparisons'); boot=np.load(OUT/'bootstrap_replicates.npz')
    check(len(comparison)==1980,'paired comparison coverage')
    # Independently reconstruct the first eight paired moving-block replicates
    # in every phase, including the stratified pooled cohort.
    sampled={}; block_counts={}; full_differences={}
    canonical_rows=p[(p.scheme=='time')&(p.model=='XGBoost')].sort_values('row')
    for fold in [0,1,2,3,-1]:
        phases=canonical_rows.fold.to_numpy()
        phases=phases[phases==fold] if fold>=0 else phases
        rng=np.random.default_rng(PLAN['bootstrap']['seed']+fold+1)
        generated=[]
        counts=np.empty((PLAN['bootstrap']['replicates'],len(phases)),dtype=np.int16)
        for replicate in range(PLAN['bootstrap']['replicates']):
            pieces=[]
            for phase in np.unique(phases):
                rows=np.flatnonzero(phases==phase); n=len(rows)
                length=min(PLAN['bootstrap']['block_length'],n)
                starts=rng.integers(0,n-length+1,size=int(np.ceil(n/length)))
                pieces.append(rows[(starts[:,None]+np.arange(length)).ravel()[:n]])
            indices=np.concatenate(pieces)
            counts[replicate]=np.bincount(indices,minlength=len(phases))
            if replicate<8: generated.append(indices)
        sampled[fold]=generated
        block_counts[fold]=counts
        phase_rows=comparison[comparison.fold==fold]
        check(np.array_equal(np.sort(phase_rows.comparison_id),np.arange(396)),'complete comparison IDs per phase')
        full_differences[fold]=np.empty((396,len(phases)))
    for _,row in comparison.iterrows():
        subset=d[(d.scheme=='time')&(d.model==row.model)]
        if row.fold>=0: subset=subset[subset.fold==row.fold]
        left=subset[subset.workflow==row.left_workflow].sort_values('row'); right=subset[subset.workflow==row.right_workflow].sort_values('row')
        truth=p[(p.scheme=='time')&(p.model==row.model)]
        if row.fold>=0: truth=truth[truth.fold==row.fold]
        truth=truth.sort_values('row').y.to_numpy()
        la=left[row.left_rule].to_numpy(dtype=bool); ra=right[row.right_rule].to_numpy(dtype=bool)
        loss_left=row.cost*((truth==1)&(~la))+((truth==0)&la); loss_right=row.cost*((truth==1)&(~ra))+((truth==0)&ra)
        close(row.loss_delta100,100*np.mean(loss_left-loss_right),'paired loss contrast point')
        full_differences[int(row.fold)][int(row.comparison_id)]=loss_left-loss_right
        samples=boot['fold_%d'%row.fold][:,int(row.comparison_id)]
        close([row.ci_low,row.ci_high],np.quantile(samples,[.025,.975]),'paired percentile interval')
        close(samples[:8],[100*np.mean((loss_left-loss_right)[ix]) for ix in sampled[int(row.fold)]],
              'independently replayed paired block replicates')
        close([row.left_alerts,row.right_alerts,row.alert_delta],[la.sum(),ra.sum(),la.sum()-ra.sum()],'paired workload contrast')
        if np.isfinite(row.budget):
            phases=left.fold.to_numpy()
            excess=lambda alert:sum(max(0,int(alert[phases==f].sum())-int(np.floor(row.budget*np.sum(phases==f)))) for f in np.unique(phases))
            le,re=excess(la),excess(ra)
            close([row.left_excess,row.right_excess,row.excess_delta],[le,re,le-re],'paired phase-specific capacity contrast')
    for fold in [0,1,2,3,-1]:
        regenerated=100*(block_counts[fold] @ full_differences[fold].T)/block_counts[fold].shape[1]
        close(boot['fold_%d'%fold],regenerated,'all 2000 independently regenerated paired block replicates')
    # Supplementary descriptive outputs have a separate independent verifier.
    # Do not certify stale supplementary files left by an earlier experiment.
    evidence_names=('predictions','references','candidates','audits','decisions','evaluations',
                    'tuning','tuning_predictions','pooled_evaluations','comparisons','prevalence_scenarios')
    evidence_hashes={name+'.csv':hashlib.sha256((OUT/(name+'.csv')).read_bytes()).hexdigest() for name in evidence_names}
    provenance_hashes={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest()
        for name in ('run_manifest.json','fold_manifest.json','analysis_manifest.json','bootstrap_replicates.npz')}
    record=dict(checks=count,replay=replay,passed=True,evidence_sha256=evidence_hashes,
                provenance_sha256=provenance_hashes,
                verifier_sha256=hashlib.sha256((ROOT/'phase2/verify.py').read_bytes()).hexdigest())
    (OUT/'verification.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print('RESULT: %d phase-two checks passed%s.'%(count,' with all fixed/refitted models replayed' if replay else ''))
    return count

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--replay',action='store_true')
    verify(parser.parse_args().replay)
