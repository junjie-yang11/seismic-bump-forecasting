"""Independent checks of descriptive extensions against original saved rows."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from .plan import ROOT, OUT

def _verify():
    count=0
    def check(value,label):
        nonlocal count
        if not value: raise AssertionError(label)
        count+=1
    def close(left,right,label): check(np.allclose(left,right,rtol=1e-10,atol=1e-10,equal_nan=True),label)
    digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    read=lambda name:pd.read_csv(OUT/(name+'.csv'))
    manifest=json.loads((OUT/'supplement_manifest.json').read_text())
    for name,value in {**manifest['inputs'],**manifest['outputs']}.items():
        check(digest(OUT/name)==value,'saved provenance '+name)
    check(digest(ROOT/'phase2/supplement.py')==manifest['source_sha256'],'supplementary generator unchanged')
    for name,original in [('decision_value','evaluations'),('decision_value_pooled','pooled_evaluations')]:
        q=read(name); base=read(original)
        pd.testing.assert_frame_equal(q[base.columns],base)
        check(len(q)==len(base),'complete evaluation coverage')
        close(q.loss_no_alarm_100,100*q.cost*(q.tp+q.fn)/q.n,'no-alarm loss')
        close(q.delta_loss_vs_no_alarm_100,q.loss100-q.loss_no_alarm_100,'loss improvement sign')
        close(q.delta_loss_vs_no_alarm_100,q.loss_delta_no_alarm100,'existing loss-delta consistency')
    a=read('audits'); candidates=read('candidates'); ref=read('references'); q=read('threshold_audit_enriched')
    pd.testing.assert_frame_equal(q[a.columns],a)
    check(len(q)==360,'every historical audit retained')
    close(q.reference_prevalence,q.reference_positives/q.reference_n,'historical prevalence')
    for _,row in q.iterrows():
        part=candidates[(candidates.model==row.model)&(candidates.scheme==row.scheme)&(candidates.fold==row.fold)]
        reference=ref[(ref.model==row.model)&(ref.scheme==row.scheme)&(ref.fold==row.fold)]
        close([row.reference_n,row.reference_positives],[len(reference),reference.y.sum()],'reference targets')
        kind='no_alarm' if row.threshold==np.inf else 'all_alarm' if row.threshold==-np.inf else 'finite'
        check(row.threshold_kind==kind,'historical threshold group')
        if row.mechanism=='A':
            check(pd.isna(row.loss_gap_100),'no cost objective for A');continue
        feasible=part if row.mechanism=='B' else part[part.alerts<=row.slots]
        check(not feasible.alerts.duplicated().any(),'second candidate is a distinct feasible alert set')
        loss=feasible.fn*row.cost+feasible.fp
        ordered=sorted(loss.tolist())
        gap=100*(ordered[1]-ordered[0])/len(reference) if len(ordered)>1 else np.nan
        close(row.loss_gap_100,gap,'normalized second-decision gap')
        if row.mechanism=='C':
            all_loss=part.fn*row.cost+part.fp
            best_alerts=part[all_loss==all_loss.min()].alerts.min()
            reason='alarm_selected'
            if row.reference_alerts==0:
                reason='no_reference_positives' if reference.y.sum()==0 else 'cost_selects_no_alarm' if best_alerts==0 else 'capacity_changes_to_no_alarm'
            check(row.no_alarm_reason==reason,'reference-only explanation')
            check(bool(row.reference_capacity_zero)==(row.slots==0),'zero capacity flag')
            tied=(loss==loss.min())&(feasible.alerts>0)
            empty_optimal=row.cost*reference.y.sum()==loss.min()
            check(bool(row.no_alarm_tied_with_other_optimum)==bool(empty_optimal and tied.any()),'no-alarm optimal tie')
            check(bool(row.unconstrained_cost_optimum_exceeds_reference_capacity)==(best_alerts>row.slots),'capacity term')
    reasons=read('threshold_explanations')
    pd.testing.assert_frame_equal(reasons.reset_index(drop=True),q[q.mechanism=='C'].reset_index(drop=True),check_dtype=False)
    check(len(reasons)==240,'all models and C policies explained')
    x=reasons[(reasons.model=='XGBoost')&(reasons.scheme=='time')]
    check((x.reference_alerts==0).sum()==40,'40 historical no-alarm settings')
    noalarm=x[x.reference_alerts==0]
    check(noalarm.no_alarm_reason.isin(['no_reference_positives','cost_selects_no_alarm','capacity_changes_to_no_alarm']).all(),'exhaustive no-alarm classification')
    e=read('evaluations'); transfer=read('refit_transfer')
    check(len(transfer)==540,'all A/B/C refitting settings including holdout')
    for _,row in transfer.iterrows():
        part=e[(e.model==row.model)&(e.scheme==row.scheme)&(e.fold==row.fold)&(e.rule==row.rule)&(e.cost==row.cost)]
        fixed=part[part.workflow=='fixed'].iloc[0]; refitted=part[part.workflow=='refitted'].iloc[0]
        close(row.threshold_fixed,fixed.threshold,'fixed cutoff');close(row.threshold_refitted,fixed.threshold,'same numerical cutoff')
        for field in ('loss100','alerts','tp','fp','fn','excess'):
            close(row[field+'_delta'],refitted[field]-fixed[field],'refit contrast '+field)
        if np.isinf(row.threshold_fixed):
            close([row.loss100_delta,row.alerts_delta,row.tp_delta,row.fn_delta],[0,0,0,0],'extreme rule invariance')
    trade=read('capacity_tradeoffs'); pooled=read('pooled_evaluations')
    check(len(trade)==576,'every phase/holdout/pooled matched-capacity C-A contrast')
    for _,row in trade.iterrows():
        frame=pooled if row.cohort=='pooled' else e
        part=frame[(frame.model==row.model)&(frame.scheme==row.scheme)&(frame.fold==row.fold)&(frame.workflow==row.workflow)&(frame.cost==row.cost)&(frame.budget==row.budget)]
        left=part[part.mechanism=='C'].iloc[0];right=part[part.mechanism=='A'].iloc[0]
        for field in ('alerts','tp','fp','fn','excess','loss100'):
            close([row['C_'+field],row['A_'+field],row[field+'_delta']],[left[field],right[field],left[field]-right[field]],'detection-capacity tradeoff '+field)
        close(row.fn_delta,-row.tp_delta,'matched rows imply complementary TP/FN changes')
    scen=read('prevalence_decision_value');original=read('prevalence_scenarios')
    pd.testing.assert_frame_equal(scen[original.columns],original)
    check(len(scen)==8064,'all frozen prevalence scenarios retained')
    pi=scen.scenario_prevalence
    expected=100*(scen.cost*pi*scen.empirical_fnr+(1-pi)*scen.empirical_fpr)
    close(scen.delta_loss_vs_no_alarm_100,expected-100*scen.cost*pi,'scenario relative loss')
    close(scen.expected_alert_rate,pi*(1-scen.empirical_fnr)+(1-pi)*scen.empirical_fpr,'scenario expected workload')
    true_mass=pi*(1-scen.empirical_fnr)
    alert_mass=true_mass+(1-pi)*scen.empirical_fpr
    expected_precision=np.full(len(scen),np.nan)
    positive_mass=alert_mass.to_numpy()>0
    expected_precision[positive_mass]=(true_mass/alert_mass).to_numpy()[positive_mass]
    close(scen.expected_precision,expected_precision,'scenario precision by expected true/total alert mass')
    check(scen.loc[~positive_mass,'expected_precision'].isna().all(),'undefined precision for zero expected alerts')
    boundaries=read('frozen_policy_cost_boundaries')
    keys=['cohort','model','scheme','fold','workflow','rule']
    originals=pd.concat([e.assign(cohort='phase_or_holdout'),pooled.assign(cohort='pooled')],ignore_index=True)
    frozen=originals[originals.mechanism.isin(['A','B','C'])].drop_duplicates(keys)
    check(len(boundaries)==len(frozen)==864,'all distinct frozen policies, without replicated A cost rows')
    check(not boundaries.duplicated(keys).any(),'one cost boundary per frozen policy')
    merged=boundaries.merge(frozen,on=keys,suffixes=('_boundary','_original'),validate='one_to_one')
    for field in ('n','positives','tp','fp','fn','tn','alerts'):
        close(merged[field+'_boundary'],merged[field+'_original'],'cost-boundary source count '+field)
    selection=np.where(merged.mechanism_original.isin(['B','C']),merged.cost,np.nan)
    close(merged.selection_cost,selection,'historical selection cost distinct from evaluation cost')
    for _,row in boundaries.iterrows():
        if row.tp>0:
            close(row.break_even_cost,row.fp/row.tp,'fixed-decision cost equality')
            close(100*(row.fp-row.break_even_cost*row.tp)/row.n,0,'zero loss difference at equality')
            check(row.boundary_status=='finite','finite boundary classification')
        else:
            check(pd.isna(row.break_even_cost),'no fabricated equality with zero detections')
            check(row.boundary_status==('no_alarm_equivalent' if row.fp==0 else 'never_improves'),
                'empty-rule equivalence distinguished from false alerts without detections')
    record=dict(passed=True,checks=count,manifest_sha256=digest(OUT/'supplement_manifest.json'),
                verifier_sha256=digest(Path(__file__)),outputs_sha256=manifest['outputs'])
    (OUT/'supplement_verification.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print('RESULT: %d independent supplementary checks passed.'%count)
    return count

def verify():
    """Invalidate a previous certificate before checking current evidence."""
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / 'supplement_verification.json'
    started = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(dict(passed=False, status='running',
        started_at_utc=started)), encoding='utf-8')
    try:
        return _verify()
    except (Exception, KeyboardInterrupt) as error:
        path.write_text(json.dumps(dict(passed=False, status='failed',
            started_at_utc=started, failed_at_utc=datetime.now(timezone.utc).isoformat(),
            error_type=type(error).__name__, error=str(error)), indent=2), encoding='utf-8')
        raise

if __name__=='__main__': verify()
