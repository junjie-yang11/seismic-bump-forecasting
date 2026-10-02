"""Small audited XGBoost search and native exact TreeSHAP contributions."""
from __future__ import annotations
import numpy as np
import xgboost as xgb
from metrics import average_precision

CANDIDATES = [(2, 80), (2, 160), (3, 80), (3, 160)]
PARAMETERS = dict(objective='binary:logistic', tree_method='hist', eta=.05,
    min_child_weight=10, reg_lambda=5, subsample=1, colsample_bytree=1,
    seed=7, nthread=2, verbosity=0, scale_pos_weight=1)


class BoostedModel:
    class_weight = False

    def __init__(self, depth=2, rounds=80, names=None):
        self.depth, self.rounds, self.names = depth, rounds, names

    def matrix(self, X, y=None):
        return xgb.DMatrix(X, label=y, feature_names=self.names, nthread=2)

    def fit(self, X, y):
        self.booster = xgb.train(dict(PARAMETERS, max_depth=self.depth), self.matrix(X, y), self.rounds)
        return self

    def predict_proba(self, X):
        return self.booster.predict(self.matrix(X)).astype(float)

    def contributions(self, X):
        """Features then bias; sum equals raw log-odds, not probability."""
        return self.booster.predict(self.matrix(X), pred_contribs=True, approx_contribs=False).astype(float)

    def margin(self, X):
        return self.booster.predict(self.matrix(X), output_margin=True).astype(float)


def inner_indices(y, temporal=True):
    if temporal:
        cut = max(1, int(.8 * len(y)))
        fit, reference = np.arange(cut), np.arange(cut, len(y))
    else:
        rng = np.random.default_rng(7); fit_parts, ref_parts = [], []
        for cls in (0, 1):
            ix = np.flatnonzero(y == cls); rng.shuffle(ix)
            cut = max(1, int(.8 * len(ix)))
            fit_parts.append(ix[:cut]); ref_parts.append(ix[cut:])
        fit, reference = np.concatenate(fit_parts), np.concatenate(ref_parts)
    if len(reference) == 0 or len(np.unique(y[fit])) != 2:
        raise ValueError('insufficient inner training classes/reference')
    return fit, reference


def select_parameters(X, y, names, temporal=True):
    """Only the supplied training rows enter candidate fits or selection.

    Fixed lexicographic grid; AP selection, with negative Brier fallback if
    the inner reference has no positives. First grid entry wins exact ties.
    """
    fit, reference = inner_indices(y, temporal)
    metric = 'AP' if y[reference].sum() else 'negative Brier'
    candidates, predictions = [], []
    for candidate, (depth, rounds) in enumerate(CANDIDATES):
        model = BoostedModel(depth, rounds, names).fit(X[fit], y[fit])
        score = model.predict_proba(X[reference])
        value = average_precision(y[reference], score) if metric == 'AP' else -float(np.mean((score - y[reference]) ** 2))
        candidates.append(dict(candidate=candidate, depth=depth, rounds=rounds, selection_metric=metric, value=value))
        predictions.append(score)
    chosen = int(np.argmax([r['value'] for r in candidates]))
    for row in candidates:
        row['selected'] = row['candidate'] == chosen
    return CANDIDATES[chosen], candidates, fit, reference, predictions
