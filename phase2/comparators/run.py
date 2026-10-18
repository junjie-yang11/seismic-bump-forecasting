"""Select historical grade rules and assess frozen decisions against comparators."""
from __future__ import annotations
import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from phase2.decisions import candidates, select, evaluate, row_loss

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from uncertainty import resample_indices

METHODS=('XGBoost','seismic','seismoacoustic','ghazard')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def encode(grades,order=('a','b','c','d')):
    mapping={name:i for i,name in enumerate(order)}
    values=list(grades)
    if not values or any(value not in mapping for value in values):
        raise ValueError('Nonempty known grade codes required')
    return np.array([mapping[value] for value in values],dtype=float)


def rules(plan):
    rows=[dict(rule='A_b%02d'%round(100*b),mechanism='A',budget=b,cost=None) for b in plan['budgets']]
    rows += [dict(rule='B_r%02d'%r,mechanism='B',budget=None,cost=r) for r in plan['costs']]
    rows += [dict(rule='C_b%02d_r%02d'%(round(100*b),r),mechanism='C',budget=b,cost=r)
             for b in plan['budgets'] for r in plan['costs']]
    return rows


def choose(reference_grades,reference_labels,test_grades,plan):
    """Test outcomes are deliberately absent from the selection interface."""
    ref=encode(reference_grades,plan['grade_order']);test=encode(test_grades,plan['grade_order'])
    frame=candidates(ref,reference_labels);audits=[];alerts={'none':np.zeros(len(test),bool)}
    for rule in rules(plan):
        audit={**rule,**select(frame,rule['mechanism'],rule['budget'],rule['cost'])}
        alerts[rule['rule']]=test>=audit['threshold'];audits.append(audit)
    return ref,test,frame,audits,alerts


def policy_specs(plan):
    return [{**rule,'cost':cost} for rule in rules(plan)
            for cost in ([rule['cost']] if rule['cost'] is not None else plan['costs'])]


def comparison_specs(plan):
    specs=[]
    for spec in policy_specs(plan):
        for method in METHODS:
            specs.append(dict(**spec,comparison='policy-none',left_method=method,right_method='none'))
        for field in plan['fields']:
            specs.append(dict(**spec,comparison='ML-grade',left_method='XGBoost',right_method=field))
    return specs


def run(root=ROOT,out=None):
    root=Path(root);out=Path(out) if out else root/'results/phase2/comparators'
    out.mkdir(parents=True,exist_ok=True);start=time.perf_counter();started=datetime.now(timezone.utc).isoformat()
    certificate=out/'verification.json';manifest_path=out/'run_manifest.json'
    def state(status,**extra):
        manifest_path.write_text(json.dumps(dict(status=status,started_at_utc=started,**extra),indent=2),encoding='utf-8')
    certificate.write_text(json.dumps(dict(passed=False,status='running')),encoding='utf-8');state('running')
    inputs={}
    def read(name):
        inputs[name]=sha(root/name)
        return pd.read_csv(root/name,float_precision='round_trip')
    def read_json(name):
        inputs[name]=sha(root/name)
        return json.loads((root/name).read_text(encoding='utf-8'))
    try:
        plan=read_json('phase2/comparators/protocol.json')
        original=read_json('phase2/locked_plan.json')['plan']
        for key in ('budgets','costs'):assert plan[key]==original[key],key
        assert {k:plan['bootstrap'][k] for k in ('replicates','block_length','seed')}=={k:original['bootstrap'][k] for k in ('replicates','block_length','seed')}
        data=read('data/seismic-bumps.csv')
        record=read_json('results/phase2/run_manifest.json')
        assert inputs['data/seismic-bumps.csv']==record['data_sha256'],'Data mirror differs from fitted evidence'
        pred=read('results/phase2/predictions.csv');pred=pred[(pred.model=='XGBoost')&(pred.scheme=='time')].sort_values('row')
        refs=read('results/phase2/references.csv');refs=refs[(refs.model=='XGBoost')&(refs.scheme=='time')]
        frozen=read('results/phase2/decisions.csv');frozen=frozen[(frozen.model=='XGBoost')&(frozen.scheme=='time')&(frozen.workflow=='fixed')]
        old_audits=read('results/phase2/audits.csv');old_audits=old_audits[(old_audits.model=='XGBoost')&(old_audits.scheme=='time')]
        old_candidates=read('results/phase2/candidates.csv');old_candidates=old_candidates[(old_candidates.model=='XGBoost')&(old_candidates.scheme=='time')]
        folds=read_json('results/phase2/fold_manifest.json')
        folds=sorted([f for f in folds if f['model']=='XGBoost' and f['scheme']=='time'],key=lambda f:f['fold'])
        assert len(folds)==4 and pred.row.is_unique and len(pred)==2063
        assert np.array_equal(data.loc[pred.row,'class'].to_numpy(),pred.y.to_numpy())
        decisions=[];references=[];frames=[];audit_rows=[];evaluations=[]
        for f in folds:
            fold=f['fold'];te=np.array(f['test_rows']);ref=np.array(f['reference_rows'])
            assert max(f['fit_rows'])<min(ref) and max(ref)<min(te)
            p=pred[pred.fold==fold].sort_values('row');h=refs[refs.fold==fold].sort_values('row')
            saved=frozen[frozen.fold==fold].sort_values('row')
            assert np.array_equal(p.row,te) and np.array_equal(saved.row,te) and np.array_equal(h.row,ref)
            assert np.array_equal(h.y,data.loc[ref,'class'])
            for method in METHODS:
                if method=='XGBoost':
                    score=p.fixed_score.to_numpy();refscore=h.score.to_numpy()
                    frame=old_candidates[old_candidates.fold==fold].drop(columns=['model','scheme','fold'])
                    selected=old_audits[old_audits.fold==fold].drop(columns=['model','scheme','fold']).to_dict('records')
                    alerts={name:saved[name].to_numpy(dtype=bool) for name in ['none']+[r['rule'] for r in rules(plan)]}
                    for audit in selected:assert np.array_equal(score>=audit['threshold'],alerts[audit['rule']])
                else:
                    refscore,score,frame,selected,alerts=choose(data.loc[ref,method],h.y,data.loc[te,method],plan)
                decisions.append(pd.DataFrame(dict(method=method,fold=fold,row=te,y=p.y.to_numpy(),score=score,**alerts)))
                references.append(pd.DataFrame(dict(method=method,fold=fold,row=ref,y=h.y.to_numpy(),score=refscore)))
                frames.append(frame.assign(method=method,fold=fold))
                audit_rows.extend(dict(method=method,fold=fold,**a) for a in selected)
                for spec in policy_specs(plan):
                    evaluations.append(dict(method=method,fold=fold,**spec,**evaluate(p.y.to_numpy(),alerts[spec['rule']],spec['cost'],spec['budget'])))
            print('Supplement phase %d: frozen ML and three historical grade fields'%(fold+1),flush=True)
        wide=pd.concat(decisions,ignore_index=True).sort_values(['method','row'])
        ev=pd.DataFrame(evaluations)
        pooled=[]
        for (method,rule,cost),part in ev.groupby(['method','rule','cost'],sort=False):
            spec=next(s for s in policy_specs(plan) if s['rule']==rule and s['cost']==cost)
            rows=wide[wide.method==method]
            result=evaluate(rows.y.to_numpy(),rows[rule].to_numpy(),cost,spec['budget'])
            if spec['budget'] is not None:result.update(slots=int(part.slots.sum()),excess=int(part.excess.sum()))
            pooled.append(dict(method=method,fold=-1,**spec,**result))
        ev=pd.concat([ev,pd.DataFrame(pooled)],ignore_index=True)
        specs=comparison_specs(plan);aligned={m:wide[wide.method==m].sort_values('row') for m in METHODS}
        y=aligned['XGBoost'].y.to_numpy();phase=aligned['XGBoost'].fold.to_numpy()
        for method in METHODS:
            assert np.array_equal(aligned[method].row,aligned['XGBoost'].row) and np.array_equal(aligned[method].y,y)
        differences=[]
        for spec in specs:
            left=aligned[spec['left_method']][spec['rule']].to_numpy(bool)
            right=np.zeros(len(y),bool) if spec['right_method']=='none' else aligned[spec['right_method']][spec['rule']].to_numpy(bool)
            differences.append(row_loss(y,left,spec['cost'])-row_loss(y,right,spec['cost']))
        dif=np.asarray(differences,dtype=float);draws={};samples={};intervals=[]
        settings=plan['bootstrap']
        for fold in (0,1,2,3,-1):
            idx=np.flatnonzero(phase==fold) if fold>=0 else np.arange(len(y));labels=phase[idx];n=len(idx)
            rng=np.random.default_rng(settings['seed']+fold+1)
            counts=np.array([np.bincount(resample_indices(rng,labels,settings['block_length']),minlength=n)
                             for _ in range(settings['replicates'])],dtype=np.int16)
            boot=100*(counts.astype(float) @ dif[:,idx].T)/n
            ci=np.quantile(boot,[.025,.975],axis=0)
            draws['fold_%d'%fold]=counts;samples['fold_%d'%fold]=boot
            for i,spec in enumerate(specs):
                intervals.append(dict(comparison_id=i,fold=fold,n=n,**spec,loss_delta100=100*dif[i,idx].sum()/n,
                                      ci_low=ci[0,i],ci_high=ci[1,i],replicates=settings['replicates'],block_length=settings['block_length']))
            print('Supplement paired intervals: '+str(fold),flush=True)
        for name,frame in [('decisions',wide),('references',pd.concat(references,ignore_index=True)),
                           ('candidates',pd.concat(frames,ignore_index=True)),('audits',pd.DataFrame(audit_rows)),
                           ('evaluations',ev),('intervals',pd.DataFrame(intervals))]:frame.to_csv(out/(name+'.csv'),index=False)
        np.savez_compressed(out/'bootstrap_counts.npz',**draws)
        np.savez_compressed(out/'bootstrap_replicates.npz',**samples)
        metadata=dict(order=plan['grade_order'],interpretation=plan['grade_interpretation'],source_url=plan['source_url'],
                      observed_counts={field:{g:int(v) for g,v in data[field].value_counts().sort_index().items()} for field in plan['fields']})
        (out/'grade_metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
        state('complete',inputs_sha256=inputs,
              code_sha256={name:sha(root/name) for name in ('phase2/comparators/run.py','phase2/decisions.py','src/uncertainty.py')},
              outputs_sha256={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.csv','.npz') or p.name=='grade_metadata.json'},
              comparison_specs=specs,environment=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__),
              elapsed_seconds=time.perf_counter()-start,scope='Frozen saved XGBoost and new reference-only grade policies; no refitting; conditional paired block intervals')
        certificate.write_text(json.dumps(dict(passed=False,status='awaiting independent verification')),encoding='utf-8')
    except (Exception,KeyboardInterrupt) as error:
        state('failed',error_type=type(error).__name__,error=str(error))
        certificate.write_text(json.dumps(dict(passed=False,status='failed',error=str(error))),encoding='utf-8')
        raise


if __name__=='__main__':run()
