"""Canonical whole-tie thresholds and prespecified policy objectives."""
import numpy as np
import pandas as pd

def vectors(score, y):
    score, y = np.asarray(score, float), np.asarray(y, float)
    if score.ndim != 1 or not score.size or y.shape != score.shape:
        raise ValueError('Nonempty aligned reference vectors required')
    if not np.isfinite(score).all() or not np.isin(y, [0,1]).all():
        raise ValueError('Finite scores and binary labels required')
    return score, y

def candidates(score, y):
    score, y = vectors(score, y)
    order = np.argsort(-score, kind='mergesort')
    s, labels = score[order], y[order]
    ends = np.r_[np.flatnonzero(np.diff(s)) + 1, len(s)]
    alerts = np.r_[0, ends]
    tp = np.r_[0, np.cumsum(labels)[ends-1]].astype(int)
    thresholds = np.r_[np.inf, s[ends[:-1]-1], -np.inf]
    return pd.DataFrame(dict(candidate=np.arange(len(alerts)), threshold=thresholds,
        alerts=alerts, tp=tp, fp=alerts-tp, fn=int(y.sum())-tp,
        tn=len(y)-int(y.sum())-(alerts-tp)))

def select(frame, mechanism, budget=None, cost=None):
    n = int(frame.iloc[-1].alerts)
    if mechanism not in ('A','B','C'): raise ValueError('Unknown mechanism')
    if mechanism in ('A','C') and (budget is None or not 0 <= budget <= 1):
        raise ValueError('Budget in [0,1] required')
    if mechanism in ('B','C') and (cost is None or not np.isfinite(cost) or cost <= 0):
        raise ValueError('Positive finite cost required')
    slots = int(np.floor(budget*n)) if budget is not None else None
    feasible = frame if mechanism == 'B' else frame[frame.alerts <= slots]
    if mechanism == 'A':
        chosen = feasible.loc[feasible.alerts.idxmax()]
        # A has no cost-specific unconstrained B counterpart. The binding
        # indicator is therefore undefined, rather than a different definition.
        tied, gap, binding = 1, np.nan, np.nan
    else:
        loss = feasible.fn*cost + feasible.fp
        best = loss.min(); optimal = feasible[loss == best]
        chosen = optimal.loc[optimal.alerts.idxmin()]
        tied = len(optimal)
        gap = float(np.sort(loss.to_numpy())[1]-best) if len(loss)>1 else np.nan
        global_loss = frame.fn*cost + frame.fp
        unconstrained = frame[global_loss == global_loss.min()]
        unconstrained = unconstrained.loc[unconstrained.alerts.idxmin()]
        binding = bool(mechanism == 'C' and unconstrained.alerts > slots)
    return dict(candidate=int(chosen.candidate), threshold=float(chosen.threshold),
        reference_n=n, reference_positives=int(chosen.tp+chosen.fn),
        reference_alerts=int(chosen.alerts), reference_tp=int(chosen.tp),
        reference_fp=int(chosen.fp), reference_fn=int(chosen.fn),
        reference_loss=float(cost*chosen.fn+chosen.fp) if cost is not None else np.nan,
        candidate_count=len(frame), feasible_count=len(feasible), optimal_decisions=tied,
        loss_gap=gap, slots=slots, capacity_binding=binding,
        feasible_on_reference=bool(slots is None or chosen.alerts <= slots))

def batch_topk(score, budget):
    # Labels are absent from this retrospective ranking reference.
    frame = candidates(score, np.zeros(len(score)))
    threshold = select(frame, 'A', budget)['threshold']
    return np.asarray(score) >= threshold, threshold

def evaluate(y, alert, cost, budget=None):
    y, alert = np.asarray(y), np.asarray(alert)
    if y.ndim != 1 or not y.size or alert.shape != y.shape or not np.isin(y,[0,1]).all() or not np.isin(alert,[0,1]).all():
        raise ValueError('Aligned binary outcomes and decisions required')
    if not np.isfinite(cost) or cost <= 0: raise ValueError('Positive finite cost required')
    if budget is not None and (not np.isfinite(budget) or not 0 <= budget <= 1):
        raise ValueError('Budget in [0,1] required')
    alert = alert.astype(bool)
    tp, fp = int(np.sum((y==1)&alert)), int(np.sum((y==0)&alert))
    fn, tn = int(y.sum())-tp, int(np.sum(y==0))-fp
    alerts, n = tp+fp, len(y)
    loss = cost*fn+fp
    slots = int(np.floor(budget*n)) if budget is not None else None
    return dict(n=n, positives=int(y.sum()), tp=tp, fp=fp, fn=fn, tn=tn,
        alerts=alerts, recall=tp/(tp+fn) if tp+fn else np.nan,
        precision=tp/alerts if alerts else 0., alert_rate=alerts/n,
        loss=loss, loss100=100*loss/n, loss_delta_no_alarm100=100*(loss-cost*y.sum())/n,
        slots=slots, excess=max(0,alerts-slots) if slots is not None else np.nan,
        fnr=fn/(tp+fn) if tp+fn else np.nan,
        fpr=fp/(fp+tn) if fp+tn else np.nan)

def row_loss(y, alert, cost):
    y, alert = np.asarray(y), np.asarray(alert,dtype=bool)
    return cost*((y==1)&(~alert)) + ((y==0)&alert)
