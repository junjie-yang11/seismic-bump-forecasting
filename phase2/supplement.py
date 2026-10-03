"""Descriptive decision audits derived from frozen phase-two evidence.

No fitting, tuning, threshold selection or bootstrap resampling occurs here.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .plan import OUT

OUTPUTS = ('decision_value','decision_value_pooled','threshold_audit_enriched',
           'threshold_explanations','refit_transfer','capacity_tradeoffs','prevalence_decision_value')

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def no_alarm_reason(positives, unconstrained_alerts, constrained_alerts):
    if constrained_alerts != 0: return 'alarm_selected'
    if positives == 0: return 'no_reference_positives'
    if unconstrained_alerts == 0: return 'cost_selects_no_alarm'
    return 'capacity_changes_to_no_alarm'

def threshold_kind(threshold):
    if np.isposinf(threshold): return 'no_alarm'
    if np.isneginf(threshold): return 'all_alarm'
    if np.isfinite(threshold): return 'finite'
    raise ValueError('A historical threshold must be finite or an infinity sentinel')

def build():
    verification=json.loads((OUT/'verification.json').read_text())
    if not verification['passed'] or not verification['replay']:
        raise RuntimeError('Verified fixed predictions are required')
    # Restrict dependencies to the original experiment evidence, even if a later
    # core verifier also records hashes of these supplementary outputs.
    inputs=['evaluations.csv','pooled_evaluations.csv','audits.csv','candidates.csv',
            'references.csv','predictions.csv','decisions.csv','prevalence_scenarios.csv',
            'run_manifest.json','fold_manifest.json','analysis_manifest.json','bootstrap_replicates.npz']
    verified={**verification['evidence_sha256'],**verification['provenance_sha256']}
    for name in inputs:
        if digest(OUT/name)!=verified[name]: raise RuntimeError('Evidence changed: '+name)
    read=lambda name:pd.read_csv(OUT/(name+'.csv'))
    e=read('evaluations'); pooled=read('pooled_evaluations'); a=read('audits'); cand=read('candidates')
    frames={}
    for name,frame in [('decision_value',e),('decision_value_pooled',pooled)]:
        q=frame.copy()
        q['loss_no_alarm_100']=100*q.cost*q.positives/q.n
        q['delta_loss_vs_no_alarm_100']=100*(q.fp-q.cost*q.tp)/q.n
        frames[name]=q
    enriched=[]
    for _,row in a.iterrows():
        part=cand[(cand.model==row.model)&(cand.scheme==row.scheme)&(cand.fold==row.fold)]
        result=row.to_dict()
        result.update(reference_prevalence=row.reference_positives/row.reference_n,
            threshold_kind=threshold_kind(row.threshold),
            loss_gap_100=100*row.loss_gap/row.reference_n,
            reference_capacity_zero=bool(row.slots==0) if np.isfinite(row.slots) else np.nan,
            reference_capacity_utilization=row.reference_alerts/row.slots if row.slots>0 else np.nan,
            unconstrained_cost_optimum_exceeds_reference_capacity=row.capacity_binding,
            no_alarm_reason=np.nan,no_alarm_tied_with_other_optimum=np.nan)
        if row.mechanism=='C':
            baseline=a[(a.model==row.model)&(a.scheme==row.scheme)&(a.fold==row.fold)&
                       (a.mechanism=='B')&(a.cost==row.cost)].iloc[0]
            result['no_alarm_reason']=no_alarm_reason(row.reference_positives,baseline.reference_alerts,row.reference_alerts)
            feasible=part[part.alerts<=row.slots]
            losses=row.cost*feasible.fn+feasible.fp
            best=losses.min()
            result['no_alarm_tied_with_other_optimum']=bool(
                row.cost*row.reference_positives==best and ((losses==best)&(feasible.alerts>0)).any())
            result['unconstrained_reference_alerts']=int(baseline.reference_alerts)
        enriched.append(result)
    frames['threshold_audit_enriched']=pd.DataFrame(enriched)
    frames['threshold_explanations']=frames['threshold_audit_enriched'].query("mechanism=='C'").copy()
    fixed=e[(e.workflow=='fixed')&e.mechanism.isin(['A','B','C'])]
    refitted=e[(e.workflow=='refitted')&e.mechanism.isin(['A','B','C'])]
    keys=['model','scheme','fold','rule','mechanism','cost']
    transfer=fixed.merge(refitted,on=keys,suffixes=('_fixed','_refitted'),validate='one_to_one')
    transfer['threshold_kind']=transfer.threshold_fixed.map(threshold_kind)
    for field in ['loss100','alerts','tp','fp','fn','excess']:
        transfer[field+'_delta']=transfer[field+'_refitted']-transfer[field+'_fixed']
    frames['refit_transfer']=transfer
    capacity=[]
    for frame in [e.assign(cohort='phase_or_holdout'),pooled.assign(cohort='pooled')]:
        for _,left in frame[frame.mechanism=='C'].iterrows():
            right=frame[(frame.model==left.model)&(frame.scheme==left.scheme)&(frame.fold==left.fold)&
                (frame.workflow==left.workflow)&(frame.mechanism=='A')&(frame.cost==left.cost)&
                (frame.budget==left.budget)].iloc[0]
            row={k:left[k] for k in ('model','scheme','fold','workflow','budget','cost','cohort','n')}
            for field in ('alerts','tp','fp','fn','excess','loss100'):
                row['C_'+field]=left[field];row['A_'+field]=right[field]
                row[field+'_delta']=left[field]-right[field]
            capacity.append(row)
    frames['capacity_tradeoffs']=pd.DataFrame(capacity)
    scenarios=read('prevalence_scenarios').copy()
    scenarios['loss_no_alarm_100']=100*scenarios.cost*scenarios.scenario_prevalence
    scenarios['delta_loss_vs_no_alarm_100']=scenarios.expected_loss100-scenarios.loss_no_alarm_100
    frames['prevalence_decision_value']=scenarios
    for name,frame in frames.items(): frame.to_csv(OUT/(name+'.csv'),index=False)
    record=dict(nature='Post hoc descriptive accounting; frozen models and historically selected policies',
        inputs={name:digest(OUT/name) for name in inputs},
        outputs={name+'.csv':digest(OUT/(name+'.csv')) for name in OUTPUTS},
        source_sha256=digest(Path(__file__)),rows={name:len(frame) for name,frame in frames.items()},
        rule='Negative delta_loss_vs_no_alarm_100 is lower loss under the specified hypothetical cost')
    (OUT/'supplement_manifest.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    (OUT/'supplement_verification.json').write_text(json.dumps(dict(passed=False,status='awaiting independent verification')),encoding='utf-8')
    print('Supplementary decision accounting saved without refitting or selecting rules.')

if __name__=='__main__': build()
