"""Reject malformed inputs before NumPy broadcasting or indexing can hide them."""
import numpy as np


def binary_vectors(y, score, probability=False):
    y, score = np.asarray(y, dtype=float), np.asarray(score, dtype=float)
    if y.ndim != 1 or not y.size or score.shape != y.shape:
        raise ValueError('labels and scores must be nonempty aligned vectors')
    if not np.isin(y, (0, 1)).all() or not np.isfinite(score).all():
        raise ValueError('binary labels and finite scores required')
    if probability and np.any((score < 0) | (score > 1)):
        raise ValueError('probabilities must be in [0, 1]')
    return y, score


def supervised_arrays(X, y):
    X, y = np.asarray(X, dtype=float), np.asarray(y, dtype=float)
    if X.ndim != 2 or not X.shape[1] or y.ndim != 1 or not y.size or len(X) != len(y):
        raise ValueError('nonempty feature matrix and aligned label vector required')
    if not np.isfinite(X).all() or not np.isin(y, (0, 1)).all():
        raise ValueError('finite features and binary labels required')
    return X, y


def split_indices(train, test, n, temporal=False):
    indices = []
    for rows in (train, test):
        rows = np.asarray(rows)
        if (rows.ndim != 1 or not rows.size or rows.dtype.kind not in 'iu'
                or np.any(rows < 0) or np.any(rows >= n)
                or np.unique(rows).size != rows.size):
            raise ValueError('fold indices must be unique nonempty integer vectors within the data')
        indices.append(rows)
    train, test = indices
    if np.intersect1d(train, test).size:
        raise ValueError('training and test indices must be disjoint')
    if temporal and (np.any(np.diff(train) <= 0) or np.any(np.diff(test) <= 0)
                     or train[-1] >= test[0]):
        raise ValueError('temporal indices must be increasing and training must precede testing')
    return train, test
