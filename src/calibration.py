"""
Probability calibration for rare-event classifiers.

Balanced class weights give the logistic fit an effective positive rate of
50 percent. An analytical log-odds shift restores the outer training fold's
unweighted prior under a prior-shift interpretation. It is assessed empirically
and does not guarantee calibration after distribution shift or regularisation.

The shift is

    delta = log(pi / (1 - pi)) - log(pi_train / (1 - pi_train))

with ``pi`` the historical outer-training prevalence, never the test-label
prevalence, and ``pi_train`` the effective weighted prevalence (0.5 for balanced
weights). One monotone correction preserves rankings within a fold; different
fold-specific corrections can change pooled rankings. Reported discrimination
therefore uses raw scores. Unweighted CART and XGBoost are not corrected.

All functions are plain NumPy.
"""
from __future__ import annotations

import numpy as np
from input_checks import binary_vectors


def reliability_curve(y, p, n_bins: int = 10, strategy: str = "quantile"):
    """Bin predictions and compare mean predicted probability with observed rate.

    Returns mean predicted probability, observed frequency, and bin counts.
    Quantile bins are approximately equally populated when ties permit it;
    duplicate edges are collapsed and tied predictions stay together.
    """
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    if y.shape != p.shape or y.size == 0:
        raise ValueError("y and p must be non-empty arrays with the same shape")
    if y.ndim != 1 or not np.isin(y, [0, 1]).all() or np.any((p < 0) | (p > 1)):
        raise ValueError("labels must be binary vectors and probabilities in [0, 1]")
    if not np.all(np.isfinite(p)):
        raise ValueError("predicted probabilities must be finite")
    if (not isinstance(n_bins, (int, np.integer))
            or isinstance(n_bins, (bool, np.bool_)) or n_bins < 1):
        raise ValueError("n_bins must be a positive integer")
    if strategy == "quantile":
        edges = np.unique(np.quantile(p, np.linspace(0.0, 1.0, n_bins + 1)))
    elif strategy == "uniform":
        lo, hi = float(p.min()), float(p.max())
        edges = np.linspace(lo, hi, n_bins + 1) if hi > lo else np.array([lo, hi + 1.0])
    else:
        raise ValueError("strategy must be 'quantile' or 'uniform'")

    if len(edges) < 2:
        edges = np.array([float(p.min()), float(p.max()) + 1e-12])
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
    y, p = binary_vectors(y, p, probability=True)
    return float(np.mean((p - y) ** 2))


def brier_skill_score(y, p) -> float:
    """1 - Brier / Brier(reference), reference = always predict the base rate."""
    y, p = binary_vectors(y, p, probability=True)
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
    if not (0 < prevalence_true < 1 and 0 < prevalence_training < 1):
        raise ValueError('correction priors must be strictly between zero and one')
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
