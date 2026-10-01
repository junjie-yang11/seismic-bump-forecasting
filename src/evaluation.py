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

All three return out-of-fold predictions on the same 0..1 scale so that the
pooled ROC-AUC and PR-AUC are directly comparable.
"""
from __future__ import annotations

import numpy as np


def stratified_random_folds(y: np.ndarray, k: int = 10, seed: int = 0) -> np.ndarray:
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
    bounds = np.linspace(0, n, k + 1).astype(int)
    return [(np.arange(0, bounds[i + 1]), np.arange(bounds[i + 1], bounds[i + 2]))
            for i in range(k - 1)]


def cross_validate(make_model, X, y, fold) -> np.ndarray:
    """Out-of-fold predictions under an explicit fold assignment."""
    preds = np.full(len(y), np.nan)
    for f in np.unique(fold):
        test = fold == f
        train = ~test
        if y[train].sum() < 5 or y[test].sum() < 1:
            continue
        model = make_model().fit(X[train], y[train])
        preds[test] = model.predict_proba(X[test])
    return preds


def cross_validate_splits(make_model, X, y, splits) -> np.ndarray:
    """Out-of-fold predictions from an explicit list of (train, test) index pairs."""
    preds = np.full(len(y), np.nan)
    for train, test in splits:
        if y[train].sum() < 5 or y[test].sum() < 1:
            continue
        model = make_model().fit(X[train], y[train])
        preds[test] = model.predict_proba(X[test])
    return preds


def chronological_holdout(X, y, frac: float = 0.7):
    cut = int(frac * len(y))
    return (X[:cut], y[:cut]), (X[cut:], y[cut:])
