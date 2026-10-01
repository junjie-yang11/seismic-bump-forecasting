"""
Classification metrics implemented from scratch.

Everything here is written in plain NumPy so that each number in the report can
be traced back to a formula, with no library behaving as a black box.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def confusion(y: np.ndarray, pred: np.ndarray) -> dict:
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def threshold_metrics(y: np.ndarray, score: np.ndarray, thr: float) -> dict:
    c = confusion(y, (score >= thr).astype(float))
    tp, fp, fn, tn = c["tp"], c["fp"], c["fn"], c["tn"]
    n = len(y)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    spec = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    out = dict(c)
    out.update(
        accuracy=(tp + tn) / n,
        precision=prec,
        recall=rec,
        specificity=spec,
        f1=f1,
        balanced_accuracy=0.5 * (rec + spec),
    )
    return out


def roc_auc(y: np.ndarray, score: np.ndarray) -> float:
    """Rank (Mann-Whitney) formulation; ties receive average ranks."""
    npos = int((y == 1).sum())
    nneg = int((y == 0).sum())
    if npos == 0 or nneg == 0:
        return float("nan")
    ranks = pd.Series(score).rank().to_numpy()
    return float((ranks[y == 1].sum() - npos * (npos + 1) / 2) / (npos * nneg))


def average_precision(y: np.ndarray, score: np.ndarray) -> float:
    """Area under the precision-recall curve (step-wise / trapezoid-free)."""
    order = np.argsort(-score, kind="mergesort")
    yy = y[order]
    tp = np.cumsum(yy)
    if tp[-1] == 0:
        return float("nan")
    precision = tp / np.arange(1, len(yy) + 1)
    recall = tp / tp[-1]
    return float(np.sum(np.diff(np.r_[0.0, recall]) * precision))


def prior_threshold(score: np.ndarray, prevalence: float) -> float:
    """Flag the riskiest `prevalence` fraction of shifts (operationally useful)."""
    return float(np.quantile(score, 1.0 - prevalence))


def summarise(y: np.ndarray, score: np.ndarray, prevalence: float | None = None) -> dict:
    if prevalence is None:
        prevalence = float(y.mean())
    thr = prior_threshold(score, prevalence)
    out = dict(n=int(len(y)), positives=int((y == 1).sum()), prevalence=float(y.mean()),
               roc_auc=roc_auc(y, score), pr_auc=average_precision(y, score),
               threshold=thr)
    out.update(threshold_metrics(y, score, thr))
    return out


def curve_points(y: np.ndarray, score: np.ndarray, n_points: int = 200):
    """ROC and PR coordinates for plotting."""
    thresholds = np.quantile(score, np.linspace(1.0, 0.0, n_points))
    thresholds = np.unique(thresholds)
    roc, pr = [], []
    for t in thresholds:
        m = threshold_metrics(y, score, t)
        roc.append((m["specificity"] and 1 - m["specificity"], m["recall"]))
        pr.append((m["recall"], m["precision"]))
    return np.array(roc), np.array(pr)
