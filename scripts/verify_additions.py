"""Checks for paired analysis, source mapping and engineering count tables."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

def verify_additions(root,check,close,y):
    from metrics import roc_auc,average_precision,summarise
    from calibration import reliability_curve
    def read(name): return pd.read_csv(root/'results'/name)
    rnd,pred=read('random_predictions_by_seed.csv'),read('predictions.csv')
    met,seeds,shared=read('metrics_by_scheme.csv'),read('random_metrics_by_seed.csv'),read('shared_test_by_seed.csv')
    intervals,reps=read('paired_uncertainty.csv'),read('bootstrap_replicates.csv')
    gaps,operating,bins=read('gap_attenuation.csv'),read('operating_points.csv'),read('calibration_bins.csv')
    models=seeds.model.unique()
    check(len(rnd)==len(y)*10 and not rnd.duplicated(['model','seed','row']).any(),'all-seed prediction count')
    check(set(zip(rnd.model,rnd.seed))=={(m,s) for m in models for s in range(5)},'all-seed prediction combinations')
    check(set(zip(intervals.model,intervals.block_length))=={(m,l) for m in ('LR','CART') for l in (1,16,32,64)} and len(intervals)==8,'bootstrap sensitivity combinations')
    check(len(gaps)==2 and len(operating)==10,'diagnostic table sizes')
    for model in models:
        short='LR' if 'logistic' in model else 'CART'
        time=pred[(pred.model==model)&(pred.validation=='time')].sort_values('row')
        shared_ap=[]
        for seed in range(5):
            p=rnd[(rnd.model==model)&(rnd.seed==seed)].sort_values('row')
            check(np.array_equal(p.row,np.arange(len(y))),'seed row coverage')
            close(p.y,y,'seed prediction labels')
            check(p.score.between(0,1).all() and np.isfinite(p.score).all(),'seed finite scores')
            s=seeds[(seeds.model==model)&(seeds.seed==seed)].iloc[0]
            close(s.pr_auc,average_precision(y,p.score.to_numpy()),'recompute every seed AP')
            close(s.roc_auc,roc_auc(y,p.score.to_numpy()),'recompute every seed ROC')
            common=p.set_index('row').loc[time.row]
            s=shared[(shared.model==model)&(shared.seed==seed)].iloc[0]
            ap=average_precision(time.y.to_numpy(),common.score.to_numpy()); shared_ap.append(ap)
            close(s.random_pr_auc,ap,'recompute every shared seed AP')
        delta=np.mean(shared_ap)-average_precision(time.y.to_numpy(),time.score.to_numpy())
        for _,r in intervals[intervals.model==short].iterrows():
            values=reps[(reps.model==short)&(reps.block_length==r.block_length)]
            check(len(values)==r.valid_boot and r.valid_boot+r.skipped==r.n_boot,'bootstrap replicate counts')
            check(not values.replicate.duplicated().any() and np.isfinite(values.delta).all(),'finite distinct replicates')
            close(r.delta,delta,'bootstrap point estimate')
            close([r.ci_low,r.ci_high],np.quantile(values.delta,[.025,.975]),'bootstrap percentile interval')
            check(r.n==len(time) and r.positives==time.y.sum() and r.random_seeds==5 and r.bootstrap_seed==20261002,'bootstrap metadata')
        r=gaps[gaps.model==short].iloc[0]
        m=met[met.model==model]
        gap=m[m.validation.str.startswith('random')].pr_auc.iloc[0]-m[m.validation.str.startswith('time')].pr_auc.iloc[0]
        close(r.original_gap,gap,'original gap')
        close(r.same_test_gap,delta,'matched gap')
        close(r.gap_reduction_fraction,1-delta/gap,'descriptive attenuation')
        for _,r in operating[operating.model==short].iterrows():
            p=pred[(pred.model==model)&(pred.validation==r.validation)&(pred.fold==r.fold)]
            s=summarise(p.y.to_numpy(),p.score.to_numpy(),threshold=p.threshold.to_numpy())
            for key in ('n','positives','tp','fp','fn','tn','recall','precision','alert_rate','pr_auc'):
                close(r[key],s[key],'engineering outcomes '+key)
        if short=='LR':
            for variant,col in [('As fitted','score'),('Fold-prior corrected','calibrated')]:
                b=bins[bins.variant==variant].sort_values('bin')
                rc=reliability_curve(time.y.to_numpy(),time[col].to_numpy(),10)
                close(b['count'],rc['count'],'bin counts')
                close(b.mean_predicted,rc['mean_pred'],'bin forecast means')
                close(b.observed_rate,rc['obs_freq'],'bin observed rates')
                check(b['count'].sum()==len(time),'bin sample conservation')
    src=json.loads((root/'results/source_audit.json').read_text(encoding='utf-8'))
    check(src['mirror_sha256']==hashlib.sha256((root/'data/seismic-bumps.csv').read_bytes()).hexdigest(),'source mirror hash')
    check(src['original_rows']==2584 and src['mirror_rows']==2578 and src['removed_rows']==6 and src['removed_positives']==0 and src['order_preserving_dedup_matches'],'source audit facts')
    mapping,duplicates=read('source_row_mapping.csv'),read('source_duplicates.csv')
    check(np.array_equal(mapping.mirror_row_0based,np.arange(len(y))),'source mapping coverage')
    missing=duplicates.removed_uci_row_1based.to_numpy()
    check(np.array_equal(mapping.uci_row_1based,np.setdiff1d(np.arange(1,2585),missing)),'source order-preserving row map')
    check(len(duplicates)==6 and duplicates['class'].sum()==0,'duplicate rows are negative')
