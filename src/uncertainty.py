"""Paired resampling of fixed OOF scores; conditional intervals, no refitting."""
from __future__ import annotations
import numpy as np
from metrics import average_precision

def resample_indices(rng, fold, block_length):
    """Moving blocks within each test phase, preserving each phase's size.

    L=1 is an IID paired row bootstrap. L>1 keeps adjacent records together;
    blocks never cross phase boundaries and do not wrap the series ends.
    """
    fold=np.asarray(fold)
    if block_length < 1: raise ValueError('block length must be positive')
    parts=[]
    for f in np.unique(fold):
        rows=np.flatnonzero(fold==f); n=len(rows)
        length=min(int(block_length),n)
        if length==1: parts.append(rng.choice(rows,n,replace=True))
        else:
            starts=rng.integers(0,n-length+1,size=int(np.ceil(n/length)))
            parts.append(rows[(starts[:,None]+np.arange(length)).ravel()[:n]])
    return np.concatenate(parts)

def _ap_groups(y, score):
    order=np.argsort(-score,kind='mergesort')
    ends=np.r_[np.flatnonzero(np.diff(score[order]))+1,len(y)]
    return order,ends

def _weighted_ap(y, counts, groups):
    order,ends=groups
    w=counts[order]; positive=np.cumsum(w*y[order])[ends-1]
    total=np.cumsum(w)[ends-1]
    if positive[-1]==0: return np.nan
    precision=np.divide(positive,total,out=np.zeros_like(positive),where=total>0)
    return float(np.sum(np.diff(np.r_[0.,positive/positive[-1]])*precision))

def paired_ap_interval(y, random_scores, temporal_score, fold, block_length=32, n_boot=2000, seed=20261002):
    """Mean of five seed-specific AP differences on identical resampled rows.

    Does not treat seeds as independent observations or refit fitted models.
    A percentile interval is conditional on this cohort and these predictions.
    """
    y=np.asarray(y,dtype=float); rnd=np.asarray(random_scores,dtype=float)
    tim=np.asarray(temporal_score,dtype=float); fold=np.asarray(fold)
    if rnd.ndim==1: rnd=rnd[None,:]
    if y.ndim!=1 or rnd.shape[1]!=len(y) or tim.shape!=y.shape or fold.shape!=y.shape:
        raise ValueError('paired arrays must align')
    if not np.isin(y,[0,1]).all() or not np.isfinite(rnd).all() or not np.isfinite(tim).all():
        raise ValueError('finite paired predictions and binary labels required')
    if n_boot<2: raise ValueError('at least two bootstrap replicates required')
    groups=[_ap_groups(y,p) for p in rnd]
    tg=_ap_groups(y,tim)
    rng=np.random.default_rng(seed); samples=[]; skipped=0
    for _ in range(n_boot):
        ix=resample_indices(rng,fold,block_length)
        counts=np.bincount(ix,minlength=len(y)).astype(float)
        t=_weighted_ap(y,counts,tg)
        if not np.isfinite(t): skipped+=1; continue
        samples.append(np.mean([_weighted_ap(y,counts,g) for g in groups])-t)
    if len(samples)<.9*n_boot: raise ValueError('too many zero-positive bootstrap replicates')
    lower,upper=np.quantile(samples,[.025,.975])
    point=np.mean([average_precision(y,p) for p in rnd])-average_precision(y,tim)
    return dict(delta=float(point),ci_low=float(lower),ci_high=float(upper),
                block_length=block_length,n_boot=n_boot,valid_boot=len(samples),skipped=skipped,bootstrap_seed=seed),np.array(samples)
