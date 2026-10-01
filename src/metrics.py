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
    """Area under the precision-recall curve, grouping tied scores."""
    y = np.asarray(y, dtype=float)
    score = np.asarray(score, dtype=float)
    order = np.argsort(-score, kind="mergesort")
    yy, ss = y[order], score[order]
    total_pos = float(yy.sum())
    if total_pos == 0:
        return float("nan")
    end = np.r_[np.flatnonzero(np.diff(ss)) + 1, len(ss)]
    tp = np.cumsum(yy)[end - 1]
    fp = end - tp
    precision = tp / (tp + fp)
    recall = tp / total_pos
    return float(np.sum(np.diff(np.r_[0.0, recall]) * precision))


def prior_threshold(score: np.ndarray, prevalence: float) -> float:
    """Select on TRAINING validation scores; exclude boundary ties together.

    At most floor(n * prevalence) reference samples are flagged. The future
    alert rate can differ from this training-only budget.
    """
    score = np.asarray(score, dtype=float)
    if score.ndim != 1 or score.size == 0 or not np.isfinite(score).all():
        raise ValueError("reference scores must be a non-empty finite vector")
    if not 0.0 <= prevalence <= 1.0:
        raise ValueError("prevalence must be in [0, 1]")
    budget = int(np.floor(len(score) * prevalence))
    if budget == 0:
        return float("inf")
    if budget == len(score):
        return float("-inf")
    boundary = np.sort(score)[::-1][budget]
    return float(np.nextafter(boundary, np.inf))


def summarise(y: np.ndarray, score: np.ndarray, *, threshold=None) -> dict:
    """Evaluate with a fixed scalar or per-row training-derived threshold."""
    if threshold is None:
        raise ValueError("a threshold selected on training validation data is required")
    thr = np.asarray(threshold, dtype=float)
    if thr.ndim > 1 or (thr.ndim == 1 and thr.shape != np.asarray(score).shape) or np.isnan(thr).any():
        raise ValueError("threshold must be scalar or match score shape and contain no NaN")
    out = dict(n=int(len(y)), positives=int((y == 1).sum()), prevalence=float(y.mean()),
               roc_auc=roc_auc(y, score), pr_auc=average_precision(y, score),
               threshold=float(thr) if thr.ndim == 0 else None)
    out.update(threshold_metrics(y, score, thr))
    out['alert_rate'] = float(np.mean(score >= thr))
    return out


def curve_points(y: np.ndarray, score: np.ndarray, n_points: int = 200):
    """ROC and PR coordinates for plotting."""
    thresholds = np.unique(np.asarray(score, dtype=float))
    if len(thresholds) > n_points:
        thresholds = np.quantile(thresholds, np.linspace(1.0, 0.0, n_points))
        thresholds = np.unique(thresholds)
    thresholds = np.r_[np.inf, thresholds[::-1], -np.inf]
    roc, pr = [], []
    for t in thresholds:
        m = threshold_metrics(y, score, t)
        roc.append((1.0 - m["specificity"], m["recall"]))
        pr.append((m["recall"], 1.0 if t == np.inf else m["precision"]))
    return np.array(roc), np.array(pr)
