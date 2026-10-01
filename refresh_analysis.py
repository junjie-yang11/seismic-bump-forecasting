"""Add cohort-matched curves, paired uncertainty and engineering diagnostics.

Run after run_experiments.py. Bootstrap conditions on saved OOF scores rather
than refitting; all five random seeds are averaged as one paired statistic.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from data import load
from evaluation import cross_validate,stratified_random_folds
from metrics import average_precision,curve_points,summarise
from calibration import reliability_curve
from uncertainty import paired_ap_interval
from figures import save_curves_png,save_reliability_png,save_intervals_png
from run_experiments import MODELS

def refresh(rebuild=False):
    X,y,features,df=load()
    path=ROOT/'results/random_predictions_by_seed.csv'
    if rebuild or not path.exists():
        frames=[]
        for model,fac in MODELS.items():
            for seed in range(5):
                print('Saving paired predictions: %s, seed %d' % (model,seed),flush=True)
                p=cross_validate(fac,X,y,stratified_random_folds(y,10,seed))
                frames.append(pd.DataFrame(dict(model=model,seed=seed,row=np.arange(len(y)),y=y,score=p)))
        pd.concat(frames,ignore_index=True).to_csv(path,index=False)
    random=pd.read_csv(path)
    predictions=pd.read_csv(ROOT/'results/predictions.csv')
    shared=pd.read_csv(ROOT/'results/shared_test_comparison.csv')
    met=pd.read_csv(ROOT/'results/metrics_by_scheme.csv')
    intervals,replicates,attenuation,operating,bins=[],[],[],[],[]
    rocs,prs=[],[]
    for ci,model in enumerate(MODELS):
        short='LR' if 'logistic' in model else 'CART'
        time=predictions[(predictions.model==model)&(predictions.validation=='time')].sort_values('row')
        common=time.row.to_numpy()
        rnd=np.array([random[(random.model==model)&(random.seed==s)].set_index('row').loc[common].score.to_numpy() for s in range(5)])
        labels=time.y.to_numpy(); scores=time.score.to_numpy(); folds=time.fold.to_numpy()
        for length in (1,16,32,64):
            result,samples=paired_ap_interval(labels,rnd,scores,folds,block_length=length)
            result.update(model=short,n=len(common),positives=int(labels.sum()),random_seeds=5,
                          method='phase-stratified paired IID' if length==1 else 'phase-stratified paired moving blocks')
            intervals.append(result)
            replicates.append(pd.DataFrame(dict(model=short,block_length=length,replicate=np.arange(len(samples)),delta=samples)))
            print('%s L=%d: delta %.4f, CI [%.4f, %.4f]' % (short,length,result['delta'],result['ci_low'],result['ci_high']),flush=True)
        ref=met[met.model==model]
        full_gap=float(ref[ref.validation.str.startswith('random')].pr_auc.iloc[0]-ref[ref.validation.str.startswith('time')].pr_auc.iloc[0])
        common_gap=float(np.mean([average_precision(labels,p) for p in rnd])-average_precision(labels,scores))
        attenuation.append(dict(model=short,original_gap=full_gap,same_test_gap=common_gap,
                                gap_reduction_fraction=1-common_gap/full_gap))
        for tag,p,dashed in [('Random seed 0',rnd[0],False),('Record order',scores,True)]:
            roc,pr=curve_points(labels,p,2000)
            rocs.append((short+', '+tag,roc,ci,dashed)); prs.append((short+', '+tag,pr,ci,dashed))
        for scheme in ('time','holdout'):
            group=predictions[(predictions.model==model)&(predictions.validation==scheme)]
            for fold,part in group.groupby('fold'):
                s=summarise(part.y.to_numpy(),part.score.to_numpy(),threshold=part.threshold.to_numpy())
                operating.append(dict(model=short,validation=scheme,fold=int(fold),training_prior=float(part.training_prior.iloc[0]),**s))
        if short=='LR':
            panels=[]
            for variant,col in [('As fitted','score'),('Fold-prior corrected','calibrated')]:
                rc=reliability_curve(labels,time[col].to_numpy(),10)
                panels.append((variant,rc['mean_pred'],rc['obs_freq'],rc['count']))
                for b,(mp,of,n) in enumerate(zip(rc['mean_pred'],rc['obs_freq'],rc['count'])):
                    bins.append(dict(model=short,variant=variant,bin=b+1,count=int(n),mean_predicted=mp,observed_rate=of))
            save_reliability_png(str(ROOT/'results/figures/reliability_lr.png'),panels,'Logistic regression: calibration on 2,063 later records')
    pd.DataFrame(intervals).to_csv(ROOT/'results/paired_uncertainty.csv',index=False)
    pd.concat(replicates,ignore_index=True).to_csv(ROOT/'results/bootstrap_replicates.csv',index=False)
    pd.DataFrame(attenuation).to_csv(ROOT/'results/gap_attenuation.csv',index=False)
    pd.DataFrame(operating).to_csv(ROOT/'results/operating_points.csv',index=False)
    pd.DataFrame(bins).to_csv(ROOT/'results/calibration_bins.csv',index=False)
    fig=ROOT/'results/figures'
    save_curves_png(str(fig/'pr_same_test.png'),prs,'Precision-recall: identical 2,063 test records','recall','precision')
    save_curves_png(str(fig/'roc_same_test.png'),rocs,'ROC: identical 2,063 test records','false positive rate','true positive rate',diagonal=True)
    save_intervals_png(str(fig/'paired_ap_intervals.png'),[r for r in intervals if r['block_length']!=1])
    print('Refreshed paired intervals, same-test curves and operating diagnostics.',flush=True)

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--rebuild',action='store_true')
    refresh(**vars(ap.parse_args()))
