"""
Validation schemes.

The whole point of the study is the difference between:

* `stratified_random_folds` — what most published results on this dataset use.
  Shuffles rows, so a model may be trained on shifts that occur *after* the ones
  it is tested on.

* `time_ordered_folds` — expanding-window validation. Fold i trains on the first
  i blocks and is tested on block i+1, which mirrors the real forecasting task
  ("given everything so far, what happens next shift?").

* `chronological_holdout` — a single train/early -> test/late split.

The schemes evaluate different test populations and training histories. Pooled
ROC-AUC and PR-AUC differences cannot be attributed solely to temporal leakage.
"""
from __future__ import annotations

import numpy as np
from calibration import prior_correction
from metrics import prior_threshold
from input_checks import supervised_arrays, split_indices


def stratified_random_folds(y: np.ndarray, k: int = 10, seed: int = 0) -> np.ndarray:
    y = np.asarray(y)
    if y.ndim != 1 or not len(y) or not np.isin(y, (0, 1)).all():
        raise ValueError('nonempty binary label vector required')
    if not isinstance(k, (int, np.integer)) or isinstance(k, (bool, np.bool_)) or not 2 <= k <= len(y):
        raise ValueError('fold count must be an integer between two and sample size')
    rng = np.random.default_rng(seed)
    fold = np.empty(len(y), dtype=int)
    for cls in (0, 1):
        idx = np.where(y == cls)[0]
        rng.shuffle(idx)
        for f, part in enumerate(np.array_split(idx, k)):
            fold[part] = f
    return fold


def time_ordered_folds(n: int, k: int = 5) -> list[tuple[np.ndarray, np.ndarray]]:
    """Expanding window: train on blocks [0..i], test on block i+1."""
    if (not isinstance(n, (int, np.integer)) or not isinstance(k, (int, np.integer))
            or isinstance(n, (bool, np.bool_)) or isinstance(k, (bool, np.bool_)) or not 2 <= k <= n):
        raise ValueError('integer sample and fold counts with 2 <= k <= n required')
    bounds = np.linspace(0, n, k + 1).astype(int)
    return [(np.arange(0, bounds[i + 1]), np.arange(bounds[i + 1], bounds[i + 2]))
            for i in range(k - 1)]


def cross_validate(make_model, X, y, fold, return_details=False):
    """Out-of-fold predictions under an explicit fold assignment."""
    splits = [(np.flatnonzero(fold != f), np.flatnonzero(fold == f)) for f in np.unique(fold)]
    return cross_validate_splits(make_model, X, y, splits, return_details, temporal=False)


def cross_validate_splits(make_model, X, y, splits, return_details=False, temporal=True):
    """Out-of-fold predictions from an explicit list of (train, test) index pairs."""
    X, y = supervised_arrays(X, y)
    preds = np.full(len(y), np.nan)
    thresholds = np.full(len(y), np.nan)
    calibrated = np.full(len(y), np.nan)
    priors = np.full(len(y), np.nan)
    folds = np.full(len(y), -1, dtype=int)
    records = []
    for f, (train, test) in enumerate(splits):
        train, test = split_indices(train, test, len(y), temporal)
        if np.any(folds[test] >= 0):
            raise ValueError('test indices overlap between folds')
        if len(np.unique(y[train])) < 2:
            raise ValueError('training fold must contain both classes')
        model = make_model().fit(X[train], y[train])
        preds[test] = model.predict_proba(X[test])
        folds[test] = f
        if return_details:
            threshold, info = select_training_threshold(make_model, X[train], y[train], temporal)
            prior = float(y[train].mean())
            thresholds[test], priors[test] = threshold, prior
            weighted = bool(getattr(model, 'class_weight', False))
            calibrated[test] = prior_correction(preds[test], prior, .5) if weighted else preds[test]
            records.append(dict(fold=f, n_train=len(train), n_test=len(test),
                                train_end=int(train.max()), test_start=int(test.min()),
                                test_end=int(test.max()), training_prior=prior,
                                threshold=threshold, class_weighted=weighted, **info))
    if return_details:
        return dict(score=preds, threshold=thresholds, calibrated=calibrated,
                    training_prior=priors, fold=folds, records=records)
    return preds


def select_training_threshold(make_model, X, y, temporal=True):
    """Inner validation uses only outer training rows, never future test data.

    Reserve the last 20% of training history for temporal validation, or 20%
    of each class (seed 7) for random validation. Fit the inner model on the
    remainder, use its training prevalence as alert budget, and freeze the
    threshold selected on the held-out training scores for outer evaluation.
    """
    n = len(y)
    if temporal:
        cut = max(1, int(.8 * n))
        fit_idx, ref_idx = np.arange(cut), np.arange(cut, n)
    else:
        rng = np.random.default_rng(7)
        fit_parts, ref_parts = [], []
        for cls in (0, 1):
            idx = np.where(y == cls)[0]
            rng.shuffle(idx)
            cut = max(1, int(.8 * len(idx)))
            fit_parts.append(idx[:cut])
            ref_parts.append(idx[cut:])
        fit_idx, ref_idx = np.concatenate(fit_parts), np.concatenate(ref_parts)
    if len(ref_idx) == 0 or len(np.unique(y[fit_idx])) < 2:
        raise ValueError('insufficient training history for inner threshold selection')
    inner = make_model().fit(X[fit_idx], y[fit_idx])
    rate = float(y[fit_idx].mean())
    threshold = prior_threshold(inner.predict_proba(X[ref_idx]), rate)
    return threshold, dict(threshold_fit_n=len(fit_idx), threshold_reference_n=len(ref_idx),
                           threshold_target_rate=rate)


def chronological_holdout(X, y, frac: float = 0.7):
    X, y = supervised_arrays(X, y)
    if not 0 < frac < 1 or not 0 < int(frac * len(y)) < len(y):
        raise ValueError('holdout fraction must produce nonempty training and test sets')
    cut = int(frac * len(y))
    return (X[:cut], y[:cut]), (X[cut:], y[cut:])
