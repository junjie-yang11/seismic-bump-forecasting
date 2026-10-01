"""
Two classifiers, implemented from scratch:

1. `LogisticRegressionIRLS` — L2-regularised logistic regression fitted by
   iteratively reweighted least squares, with class weights to counter the
   ~1:14 imbalance.
2. `BaggedForest` — bagged CART trees (Gini impurity), as a non-linear model so
   that any conclusion is not an artefact of one model family.

Feature standardisation is performed *inside* `fit`, using training statistics
only, and reused at prediction time. Fitting the scaler on the full dataset
before cross-validation would be another, subtler form of leakage.
"""
from __future__ import annotations

import numpy as np


class Standardiser:
    def fit(self, X):
        self.mu = X.mean(axis=0)
        sd = X.std(axis=0)
        self.sd = np.where(sd < 1e-12, 1.0, sd)
        return self

    def transform(self, X):
        return (X - self.mu) / self.sd


class LogisticRegressionIRLS:
    def __init__(self, lam: float = 1.0, max_iter: int = 60, tol: float = 1e-9,
                 class_weight: bool = True):
        self.lam = lam
        self.max_iter = max_iter
        self.tol = tol
        self.class_weight = class_weight

    def fit(self, X, y):
        n, d = X.shape
        self.scaler = Standardiser().fit(X)
        Z = self.scaler.transform(X)
        Xb = np.hstack([np.ones((n, 1)), Z])

        if self.class_weight:
            npos = max((y == 1).sum(), 1)
            nneg = max((y == 0).sum(), 1)
            w = np.where(y == 1, n / (2 * npos), n / (2 * nneg))
        else:
            w = np.ones(n)

        beta = np.zeros(d + 1)
        penalty = self.lam * np.diag(np.r_[0.0, np.ones(d)])  # intercept unpenalised
        for _ in range(self.max_iter):
            eta = np.clip(Xb @ beta, -30, 30)
            p = 1.0 / (1.0 + np.exp(-eta))
            W = w * p * (1.0 - p)
            grad = Xb.T @ (w * (p - y)) + self.lam * np.r_[0.0, beta[1:]]
            hess = Xb.T @ (Xb * W[:, None]) + penalty
            try:
                step = np.linalg.solve(hess, grad)
            except np.linalg.LinAlgError:
                step = np.linalg.lstsq(hess, grad, rcond=None)[0]
            beta = beta - step
            if np.max(np.abs(step)) < self.tol:
                break
        self.beta = beta
        self.n_iter = _
        return self

    def decision_function(self, X):
        Z = self.scaler.transform(X)
        return np.hstack([np.ones((len(Z), 1)), Z]) @ self.beta

    def predict_proba(self, X):
        return 1.0 / (1.0 + np.exp(-np.clip(self.decision_function(X), -30, 30)))

    def predict(self, X, threshold: float = 0.5):
        return (self.predict_proba(X) >= threshold).astype(float)


class _Node:
    __slots__ = ("p", "feature", "threshold", "left", "right")

    def __init__(self, p):
        self.p = p


class DecisionTree:
    """Depth-limited CART for binary classification (Gini impurity)."""

    def __init__(self, max_depth: int = 6, min_samples_leaf: int = 20,
                 n_features=None, rng=None, n_thresholds: int = 12):
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.n_features = n_features
        self.rng = rng
        self.n_thresholds = n_thresholds

    @staticmethod
    def _gini(y):
        if len(y) == 0:
            return 0.0
        p = y.mean()
        return 2.0 * p * (1.0 - p)

    def _best_split(self, X, y, features):
        parent = self._gini(y)
        n = len(y)
        best = None
        for j in features:
            col = X[:, j]
            for t in np.unique(np.quantile(col, np.linspace(0.05, 0.95, self.n_thresholds))):
                mask = col <= t
                nl = int(mask.sum())
                if nl < self.min_samples_leaf or n - nl < self.min_samples_leaf:
                    continue
                gain = parent - (nl * self._gini(y[mask]) +
                                 (n - nl) * self._gini(y[~mask])) / n
                if best is None or gain > best[0]:
                    best = (gain, j, t, mask)
        return best

    def fit(self, X, y, depth: int = 0):
        self.root = self._build(X, y, depth)
        return self

    def _build(self, X, y, depth):
        node = _Node(float(y.mean()) if len(y) else 0.0)
        if depth >= self.max_depth or len(y) < 2 * self.min_samples_leaf:
            return node
        if len(np.unique(y)) == 1:
            return node
        features = np.arange(X.shape[1])
        if self.n_features and self.n_features < X.shape[1]:
            features = self.rng.choice(X.shape[1], self.n_features, replace=False)
        split = self._best_split(X, y, features)
        if split is None or split[0] <= 1e-12:
            return node
        _, node.feature, node.threshold, mask = split
        node.left = self._build(X[mask], y[mask], depth + 1)
        node.right = self._build(X[~mask], y[~mask], depth + 1)
        return node

    def predict_proba(self, X):
        out = np.empty(len(X))
        stack = [(self.root, np.arange(len(X)))]
        while stack:
            node, idx = stack.pop()
            if idx.size == 0:
                continue
            if not hasattr(node, "feature"):
                out[idx] = node.p
                continue
            go_left = X[idx, node.feature] <= node.threshold
            stack.append((node.left, idx[go_left]))
            stack.append((node.right, idx[~go_left]))
        return out


class BaggedForest:
    """Bootstrap-aggregated decision trees. No feature subsampling by default."""

    def __init__(self, n_trees: int = 60, max_depth: int = 6,
                 min_samples_leaf: int = 20, n_features=None, seed: int = 0):
        self.n_trees = n_trees
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.n_features = n_features
        self.seed = seed

    def fit(self, X, y):
        rng = np.random.default_rng(self.seed)
        n = len(y)
        self.trees = []
        for _ in range(self.n_trees):
            idx = rng.integers(0, n, n)
            if y[idx].sum() < 2:            # need both classes to grow a split
                continue
            tree = DecisionTree(self.max_depth, self.min_samples_leaf,
                                self.n_features, rng)
            self.trees.append(tree.fit(X[idx], y[idx]))
        if not self.trees:
            raise RuntimeError("no tree could be grown")
        return self

    def predict_proba(self, X):
        return np.mean([t.predict_proba(X) for t in self.trees], axis=0)


def permutation_importance(model, X, y, metric, n_repeats: int = 10,
                           seed: int = 0):
    """Drop in ROC-AUC when a column is shuffled. Handles collinearity better
    than raw coefficients, which are unstable when features are correlated."""
    rng = np.random.default_rng(seed)
    base = metric(y, model.predict_proba(X))
    out = np.zeros((n_repeats, X.shape[1]))
    for r in range(n_repeats):
        for j in range(X.shape[1]):
            Xp = X.copy()
            rng.shuffle(Xp[:, j])
            out[r, j] = base - metric(y, model.predict_proba(Xp))
    return base, out.mean(axis=0), out.std(axis=0)
