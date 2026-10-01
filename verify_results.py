"""Recompute metrics and verify coverage, training provenance and current reports."""
from __future__ import annotations
import argparse
import sys
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from data import load, integrity_report
from evaluation import stratified_random_folds, time_ordered_folds
from metrics import summarise, roc_auc, average_precision
from calibration import prior_correction, calibration_summary
from generate_report import report_markdown

def verify(reports=False):
    count = 0
    def check(condition, label):
        nonlocal count
        if not condition: raise AssertionError(label)
        count += 1
    def close(a,b,label):
        check(np.allclose(a,b,rtol=1e-9,atol=1e-10,equal_nan=True),label)
    def read(name): return pd.read_csv(ROOT/'results'/name)
    X,y,features,df=load()
    check(len(y)==2578 and y.sum()==170,'dataset size / labels')
    stored=json.loads((ROOT/'results/integrity.json').read_text(encoding='utf-8'))
    check(stored==json.loads(json.dumps(integrity_report(df))),'raw data vs integrity.json')
    pred,audit=read('predictions.csv'),read('fold_audit.csv')
    met,hold,seeds=read('metrics_by_scheme.csv'),read('holdout.csv'),read('random_metrics_by_seed.csv')
    shared,means,cal=read('shared_test_by_seed.csv'),read('shared_test_comparison.csv'),read('calibration.csv')
    models=['logistic regression (L2, class-weighted)','bagged CART (60 trees, depth 6)']
    check(set(zip(pred.model,pred.validation))=={(m,v) for m in models for v in ('random','time','holdout')},'prediction combinations')
    check(not pred.duplicated(['model','validation','row']).any(),'unique predictions')
    check(not audit.duplicated(['model','validation','fold']).any(),'unique audit records')
    check(set(zip(audit.model,audit.validation))==set(zip(pred.model,pred.validation)) and len(audit)==30,'complete audit combinations')
    check(len(met)==4 and len(hold)==2 and len(cal)==3 and len(means)==2,'complete summary tables')
    for table in (seeds,shared):
        check(set(zip(table.model,table.seed))=={(m,s) for m in models for s in range(5)} and len(table)==10,'five seeds per model')
    cut=int(.7*len(y))
    temporal=time_ordered_folds(len(y),5)
    keys=['roc_auc','pr_auc','accuracy','balanced_accuracy','recall','precision','f1','alert_rate']
    for model in models:
        groups={}
        for scheme in ('random','time','holdout'):
            p=pred[(pred.model==model)&(pred.validation==scheme)].sort_values('row')
            groups[scheme]=p
            folds=stratified_random_folds(y,10,0)
            splits=[(np.flatnonzero(folds!=f),np.flatnonzero(folds==f)) for f in range(10)] if scheme=='random' else temporal if scheme=='time' else [(np.arange(cut),np.arange(cut,len(y)))]
            expected_rows=np.sort(np.concatenate([te for tr,te in splits]))
            check(np.array_equal(p.row.to_numpy(),expected_rows),model+'/'+scheme+' complete test coverage')
            close(p.y,y[expected_rows],'prediction labels')
            check(np.isfinite(p.score).all() and p.score.between(0,1).all(),'valid scores')
            check(not p.threshold.isna().any(),'fixed thresholds present')
            a=audit[(audit.model==model)&(audit.validation==scheme)]
            check(len(a)==len(splits),'audit fold count')
            for f,(tr,te) in enumerate(splits):
                row=a[a.fold==f]
                check(len(row)==1,'audit fold exists')
                row=row.iloc[0]; pf=p[p.fold==f]
                check(np.array_equal(np.sort(pf.row),np.sort(te)),'fold coverage includes negatives')
                check(row.n_train==len(tr) and row.n_test==len(te) and row.train_end==tr.max() and row.test_start==te.min() and row.test_end==te.max(),'fold ranges')
                prior=float(y[tr].mean())
                close(row.training_prior,prior,'audit training prior')
                close(pf.training_prior,prior,'per-row training prior')
                close(pf.threshold,row.threshold,'per-row fixed threshold')
                if scheme!='random':
                    check(tr.max()<te.min(),'training precedes test')
                    inner=tr[:int(.8*len(tr))]
                else:
                    rng=np.random.default_rng(7); parts=[]
                    for cls in (0,1):
                        ix=np.flatnonzero(y[tr]==cls); rng.shuffle(ix)
                        parts.extend(ix[:max(1,int(.8*len(ix)))])
                    inner=tr[np.array(parts,dtype=int)]
                check(row.threshold_fit_n==len(inner) and row.threshold_reference_n==len(tr)-len(inner),'inner training-only sizes')
                close(row.threshold_target_rate,y[inner].mean(),'inner training-only budget')
                weighted='logistic' in model
                check(bool(row.class_weighted)==weighted,'actual class weights')
                corrected=prior_correction(pf.score,prior,.5) if weighted else pf.score
                close(pf.calibrated,corrected,'fold-local probability correction')
            summary=summarise(p.y.to_numpy(),p.score.to_numpy(),threshold=p.threshold.to_numpy())
            r=seeds[(seeds.model==model)&(seeds.seed==0)].iloc[0] if scheme=='random' else met[(met.model==model)&met.validation.str.startswith('time')].iloc[0] if scheme=='time' else hold[hold.model==model].iloc[0]
            for key in keys: close(r[key],summary[key],'recomputed '+scheme+'/'+key)
        sr=seeds[seeds.model==model]
        r=met[(met.model==model)&met.validation.str.startswith('random')].iloc[0]
        for key in keys: close(r[key],sr[key].mean(),'five-seed mean '+key)
        for key in ('roc_auc','pr_auc'): close(r[key+'_sd'],sr[key].std(ddof=0),'five-seed spread')
        common=groups['time'].row.to_numpy()
        random=groups['random'].set_index('row').loc[common]; time=groups['time']
        ss=shared[(shared.model==model)&(shared.seed==0)].iloc[0]
        close(ss.random_roc_auc,roc_auc(time.y,random.score),'shared random ROC')
        close(ss.random_pr_auc,average_precision(time.y,random.score),'shared random AP')
        for _,s in shared[shared.model==model].iterrows():
            check(s.n==len(common),'shared sample size')
            close(s.prevalence,time.y.mean(),'shared prevalence')
            close(s.time_roc_auc,roc_auc(time.y,time.score),'shared temporal ROC')
            close(s.time_pr_auc,average_precision(time.y,time.score),'shared temporal AP')
        mean=shared[shared.model==model].drop(columns=['model','seed']).mean()
        r=means[means.model==model].iloc[0]
        for key in mean.index: close(r[key],mean[key],'shared seed mean')
        c=cal[cal.model==('LR' if 'logistic' in model else 'CART')]
        check(len(c)==(2 if 'logistic' in model else 1),'calibration variants')
        for _,r in c.iterrows():
            scores=time.calibrated if r.variant.startswith('after') else time.score
            summary=calibration_summary(time.y,scores,'check')
            for key in ('brier','brier_skill','ece','mce','mean_predicted','observed_rate'):
                close(r[key],summary[key],'recomputed calibration '+key)
    from verify_additions import verify_additions
    verify_additions(ROOT,check,close,y)
    source=report_markdown()
    check((ROOT/'report/technical_note.md').read_text(encoding='utf-8')==source,'Markdown matches current results')
    if reports:
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        with zipfile.ZipFile(ROOT/'report/technical_report.docx') as z:
            body=ET.fromstring(z.read('word/document.xml')).find('w:body',ns)
        actual=[''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in body.findall('.//w:p',ns)]
        wanted=[]
        for line in source.splitlines():
            if not line or re.fullmatch(r'\|[\s|:-]+',line): continue
            if line.startswith('|'): wanted.extend(v.strip() for v in line.strip('|').split('|'))
            elif line.startswith('!['): wanted.append(re.match(r'!\[(.*?)\]',line).group(1))
            else: wanted.append(line.lstrip('# '))
        check([s for s in actual if s]==wanted,'Word paragraphs and tables match current Markdown')
        check((ROOT/'report/technical_report.pdf').stat().st_size>10000,'PDF export exists')
    print('RESULT: all %d consistency checks passed.' % count)
    return count

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--reports',action='store_true')
    try: verify(**vars(ap.parse_args()))
    except (AssertionError,ValueError,KeyError,IndexError,OSError) as error:
        print('FAIL: %s' % error); sys.exit(1)
