"""Run the locked phase-two study; never write first-stage outputs."""
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import xgboost
from .plan import ROOT, OUT, PLAN, lock_plan
from .experiment import fit_fold
from .decisions import candidates, select, batch_topk, evaluate
from data import load, CSV_PATH
from evaluation import time_ordered_folds

def protected_hashes():
    files = list((ROOT/'reports/phase1').rglob('*')) + [p for p in (ROOT/'results').rglob('*') if OUT not in p.parents]
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}

def declarations():
    rows = [dict(rule='none',mechanism='none',budget=None,cost=None)]
    rows += [dict(rule='A_b%02d'%round(100*b),mechanism='A',budget=b,cost=None) for b in PLAN['budgets']]
    rows += [dict(rule='B_r%02d'%r,mechanism='B',budget=None,cost=r) for r in PLAN['costs']]
    rows += [dict(rule='C_b%02d_r%02d'%(round(100*b),r),mechanism='C',budget=b,cost=r)
             for b in PLAN['budgets'] for r in PLAN['costs']]
    rows += [dict(rule='TopK_b%02d'%round(100*b),mechanism='TopK',budget=b,cost=None) for b in PLAN['budgets']]
    return rows

def _run():
    locked=lock_plan(); start=time.perf_counter(); started_at=datetime.now(timezone.utc).isoformat()
    OUT.mkdir(parents=True,exist_ok=True)
    # A failed or interrupted rerun cannot inherit a previous success flag.
    (OUT/'verification.json').write_text(json.dumps(dict(passed=False,replay=False,status='running',
        started_at_utc=started_at)),encoding='utf-8')
    (OUT/'run_manifest.json').write_text(json.dumps(dict(status='running',started_at_utc=started_at,
        plan_sha256=locked['plan_sha256'])),encoding='utf-8')
    protected=protected_hashes()
    X,y,names,_=load(); cut=int(PLAN['holdout_fraction']*len(y))
    splits=[('time',f,tr,te) for f,(tr,te) in enumerate(time_ordered_folds(len(y),5))]
    splits += [('holdout',0,np.arange(cut),np.arange(cut,len(y)))]
    manifest=[]; prediction=[]; refs=[]; cand=[]; audits=[]; evals=[]; decisions=[]; tuning=[]; tuning_predictions=[]
    for model in PLAN['models']:
        for scheme,fold,tr,te in splits:
            print('%s %s phase %d: fit, choose historical rules, transfer, refit'%(model,scheme,fold+1),flush=True)
            result=fit_fold(model,X,y,tr,te,names)
            meta=dict(model=model,scheme=scheme,fold=fold)
            m=result['manifest']; m.update(meta); manifest.append(m)
            reference=np.array(m['reference_rows'])
            prediction.append(pd.DataFrame(dict(**meta,row=te,y=y[te],fixed_score=result['fixed_score'],refitted_score=result['refitted_score'])))
            refs.append(pd.DataFrame(dict(**meta,row=reference,y=y[reference],score=result['reference_score'])))
            frame=candidates(result['reference_score'],y[reference])
            for r in PLAN['costs']: frame['loss_r%d'%r]=r*frame.fn+frame.fp
            cand.append(frame.assign(**meta))
            if model=='XGBoost':
                for candidate,score in zip(result['tuning'],result['tuning_scores']):
                    tuning.append(dict(**meta,**candidate))
                    tuning_predictions.append(pd.DataFrame(dict(**meta,candidate=candidate['candidate'],
                        row=m['tuning_reference_rows'],y=y[m['tuning_reference_rows']],score=score)))
            rules=[]
            for declaration in declarations():
                rule=declaration.copy()
                if rule['mechanism'] in ('A','B','C'):
                    audit=select(frame,rule['mechanism'],rule['budget'],rule['cost'])
                    rule['threshold']=audit['threshold']
                    audits.append(dict(**meta,**declaration,**audit))
                elif rule['mechanism']=='none': rule['threshold']=np.inf
                rules.append(rule)
            for workflow in ('fixed','refitted'):
                score=result[workflow+'_score']
                wide=pd.DataFrame(dict(**meta,row=te,workflow=workflow))
                for rule in rules:
                    if rule['mechanism']=='TopK': alert,threshold=batch_topk(score,rule['budget'])
                    else:
                        threshold=rule['threshold']; alert=score>=threshold
                    wide[rule['rule']]=alert
                    for r in ([rule['cost']] if rule['cost'] is not None else PLAN['costs']):
                        evals.append(dict(**meta,workflow=workflow,rule=rule['rule'],mechanism=rule['mechanism'],
                            budget=rule['budget'],cost=r,threshold=threshold,
                            **evaluate(y[te],alert,r,rule['budget'])))
                decisions.append(wide)
    for name,frames in [('predictions',prediction),('references',refs),('candidates',cand),('decisions',decisions),('tuning_predictions',tuning_predictions)]:
        pd.concat(frames,ignore_index=True).to_csv(OUT/(name+'.csv'),index=False)
    for name,rows in [('audits',audits),('evaluations',evals),('tuning',tuning)]:
        pd.DataFrame(rows).to_csv(OUT/(name+'.csv'),index=False)
    (OUT/'fold_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    assert protected_hashes()==protected, 'First-stage evidence changed'
    run_record=dict(started_at_utc=started_at,elapsed_seconds=time.perf_counter()-start,
        plan_sha256=locked['plan_sha256'],data_sha256=hashlib.sha256(Path(CSV_PATH).read_bytes()).hexdigest(),
        environment=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,xgboost=xgboost.__version__),
        source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'phase2').glob('*.py')},
        dependency_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src').glob('*.py')},
        first_stage_unchanged=True, first_stage_hashes=protected)
    (OUT/'run_manifest.json').write_text(json.dumps(run_record,indent=2),encoding='utf-8')
    from .analysis import analyse
    analyse()
    run_record['status']='complete'
    run_record['total_elapsed_seconds']=time.perf_counter()-start
    (OUT/'run_manifest.json').write_text(json.dumps(run_record,indent=2),encoding='utf-8')
    print('Phase-two evidence saved independently.',flush=True)

def run():
    try:
        _run()
    except Exception as error:
        # Keep actual failure evidence, never a stale completed manifest.
        if OUT.exists():
            path=OUT/'run_manifest.json'
            record=json.loads(path.read_text()) if path.exists() else {}
            record.update(status='failed',error_type=type(error).__name__)
            path.write_text(json.dumps(record,indent=2),encoding='utf-8')
            (OUT/'verification.json').write_text(json.dumps(dict(passed=False,replay=False,status='failed')),
                                                 encoding='utf-8')
        raise

if __name__=='__main__': run()
