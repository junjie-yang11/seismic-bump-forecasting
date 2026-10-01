"""
Probability calibration for rare-event classifiers.

Why this matters here
---------------------
The classifiers in this study are trained with class weights, so that the
positive class carries weight ``n / (2 * n_pos)`` instead of 1. That weighting
is what makes the model usable on a 6.6 %-positive dataset: it stops the fit
from collapsing onto the majority class. But it has a side effect that is easy
to miss -- **the output probabilities are no longer on the true prevalence
scale.** The model is effectively trained as if the base rate were 50 %, so its
predicted probabilities are far too high.

Discrimination metrics such as ROC-AUC and PR-AUC are unaffected by this,
because they depend only on the *ranking* of scores. Any statement of the form
"this shift has a 30 % chance of being hazardous", however, is wrong by a large
factor. For an early-warning system that is the difference between a usable
threshold rule and a useless one.

The correction is a shift of the log-odds by

    delta = log(pi / (1 - pi)) - log(pi_train / (1 - pi_train))

with ``pi`` the true prevalence and ``pi_train`` the effective prevalence seen
by the weighted fit (0.5 for balanced weights). This is the standard prior
correction for case-control style sampling.

All functions are plain NumPy.
"""
from __future__ import annotations

import numpy as np


def reliability_curve(y, p, n_bins: int = 10, strategy: str = "quantile"):
    """Bin predictions and compare mean predicted probability with observed rate.

    Returns a dict with bin centres, mean predicted probability, observed
    frequency, and bin counts. ``strategy='quantile'`` gives equally populated
    bins, which is essential when almost all scores are near zero.
    """
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    if strategy == "quantile":
        edges = np.unique(np.quantile(p, np.linspace(0.0, 1.0, n_bins + 1)))
    elif strategy == "uniform":
        edges = np.linspace(p.min(), p.max(), n_bins + 1)
    else:
        raise ValueError("strategy must be 'quantile' or 'uniform'")

    idx = np.clip(np.digitize(p, edges[1:-1], right=False), 0, len(edges) - 2)
    rows = []
    for b in range(len(edges) - 1):
        m = idx == b
        if m.sum() == 0:
            continue
        rows.append((float(p[m].mean()), float(y[m].mean()), int(m.sum())))
    if not rows:
        return dict(mean_pred=np.array([]), obs_freq=np.array([]), count=np.array([]))
    return dict(mean_pred=np.array([r[0] for r in rows]),
                obs_freq=np.array([r[1] for r in rows]),
                count=np.array([r[2] for r in rows]))


def brier_score(y, p) -> float:
    """Mean squared error of the predicted probabilities. Lower is better."""
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    return float(np.mean((p - y) ** 2))


def brier_skill_score(y, p) -> float:
    """1 - Brier / Brier(reference), reference = always predict the base rate."""
    y = np.asarray(y, dtype=float)
    base = float(y.mean())
    ref = brier_score(y, np.full_like(y, base))
    if ref == 0:
        return float("nan")
    return float(1.0 - brier_score(y, p) / ref)


def expected_calibration_error(y, p, n_bins: int = 10, strategy: str = "quantile") -> float:
    """Weighted average gap between confidence and accuracy."""
    y = np.asarray(y, dtype=float)
    rc = reliability_curve(y, p, n_bins, strategy)
    n = len(y)
    return float(np.sum(rc["count"] / n * np.abs(rc["obs_freq"] - rc["mean_pred"])))


def maximum_calibration_error(y, p, n_bins: int = 10, strategy: str = "quantile") -> float:
    rc = reliability_curve(y, p, n_bins, strategy)
    if len(rc["count"]) == 0:
        return float("nan")
    return float(np.max(np.abs(rc["obs_freq"] - rc["mean_pred"])))


def logit(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-12, 1 - 1e-12)
    return np.log(p / (1.0 - p))


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -40, 40)))


def prior_correction(p, prevalence_true: float, prevalence_training: float = 0.5):
    """Shift log-odds to undo the effect of balanced class weights.

    ``prevalence_training`` is the effective positive rate the model was fitted
    against. With weights n/(2*n_pos) and n/(2*n_neg) this is 0.5.
    """
    delta = (np.log(prevalence_true / (1.0 - prevalence_true))
             - np.log(prevalence_training / (1.0 - prevalence_training)))
    return sigmoid(logit(p) + delta)


def calibration_summary(y, p, label: str, n_bins: int = 10) -> dict:
    return dict(label=label,
                brier=brier_score(y, p),
                brier_skill=brier_skill_score(y, p),
                ece=expected_calibration_error(y, p, n_bins),
                mce=maximum_calibration_error(y, p, n_bins),
                mean_predicted=float(np.mean(p)),
                observed_rate=float(np.mean(y)))
