"""Training-only feature ablations and fixed-budget warning evaluation."""
from __future__ import annotations
import numpy as np
import pandas as pd
from calibration import prior_correction
from metrics import prior_threshold, summarise
from input_checks import supervised_arrays, split_indices

GROUPS = {
    'ratings': ('seismic', 'seismoacoustic', 'ghazard'),
    'geophone': ('genergy', 'gpuls', 'gdenergy', 'gdpuls'),
    'seismic_activity': ('nbumps2', 'nbumps3', 'nbumps4', 'nbumps5',
                         'nbumps6', 'nbumps7', 'nbumps89', 'energy', 'maxenergy'),
    'operation': ('shift',),
}
BUDGETS = (.01, .05, .10, .20)


def feature_variants(names):
    """Partition the existing design, without new transformations or tuning."""
    flat = [name for group in GROUPS.values() for name in group]
    if len(set(flat)) != len(flat) or set(flat) != set(names):
        raise ValueError('engineering groups must partition the design columns')
    variants = {'full': list(names)}
    for group, columns in GROUPS.items():
        variants[group + '_only'] = [n for n in names if n in columns]
        variants['without_' + group] = [n for n in names if n not in columns]
    return {key: [names.index(n) for n in columns] for key, columns in variants.items()}


def evaluate_splits(make_model, X, y, splits, budgets=BUDGETS, fold_factory=None, on_model=None):
    """One inner fit per fold provides reference scores for every budget.

    Refitting on the complete outer training fold may change the score scale.
    Test scores never select thresholds. Inner labels determine only the
    historical prevalence policy; explicit budget policies use fixed rates.
    """
    X, y = supervised_arrays(X, y)
    predictions, references, audits = [], [], []
    seen = set()
    rates = tuple(float(b) for b in budgets)
    if not rates or len(set(rates)) != len(rates) or any(not 0 < b < 1 for b in rates):
        raise ValueError('budgets must be distinct rates strictly between zero and one')
    for fold, (train, test) in enumerate(splits):
        train, test = split_indices(train, test, len(y), temporal=True)
        if seen.intersection(test):
            raise ValueError('ordered disjoint nonempty folds required')
        seen.update(test)
        cut = max(1, int(.8 * len(train)))
        fit, reference = train[:cut], train[cut:]
        if not len(reference) or len(np.unique(y[fit])) != 2:
            raise ValueError('inner training needs both classes and reference rows')
        inner_factory, outer_factory = (make_model, make_model) if fold_factory is None else fold_factory(fold, train, fit)
        inner = inner_factory().fit(X[fit], y[fit])
        reference_scores = inner.predict_proba(X[reference])
        outer = outer_factory().fit(X[train], y[train])
        scores = outer.predict_proba(X[test])
        if on_model is not None:
            on_model(fold, outer, train, test)
        prior = float(y[train].mean())
        corrected = prior_correction(scores, prior, .5) if getattr(outer, 'class_weight', False) else scores
        prevalence_rate = float(y[fit].mean())
        threshold = prior_threshold(reference_scores, prevalence_rate)
        predictions.append(pd.DataFrame(dict(row=test, fold=fold, y=y[test], score=scores,
            calibrated=corrected, training_prior=prior, threshold=threshold)))
        references.append(pd.DataFrame(dict(row=reference, fold=fold, score=reference_scores)))
        for policy, rate in [('historical_prevalence', prevalence_rate)] + [('budget', b) for b in rates]:
            thr = prior_threshold(reference_scores, rate)
            audits.append(dict(fold=fold, policy=policy, budget=rate, threshold=thr,
                train_start=int(train.min()), train_end=int(train.max()), n_train=len(train),
                inner_fit_start=int(fit.min()), inner_fit_end=int(fit.max()), inner_fit_n=len(fit),
                reference_start=int(reference.min()), reference_end=int(reference.max()),
                reference_n=len(reference), reference_alerts=int(np.sum(reference_scores >= thr)),
                test_start=int(test.min()), test_end=int(test.max()), n_test=len(test),
                training_prior=prior))
    return (pd.concat(predictions, ignore_index=True),
            pd.concat(references, ignore_index=True), pd.DataFrame(audits))


def warning_summary(predictions, audits):
    """Aggregate warning consequences with per-fold frozen cutoffs."""
    rows = []
    for budget, group in audits[audits.policy == 'budget'].groupby('budget'):
        threshold = predictions.fold.map(group.set_index('fold').threshold).to_numpy()
        if np.isnan(threshold).any():
            raise ValueError('every prediction fold needs a frozen threshold')
        summary = summarise(predictions.y.to_numpy(), predictions.score.to_numpy(), threshold=threshold)
        alerts = summary['tp'] + summary['fp']
        summary.update(budget=budget, alerts=alerts,
            alerts_per_detection=alerts / summary['tp'] if summary['tp'] else np.nan)
        rows.append(summary)
    return rows
