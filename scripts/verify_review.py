"""Independently recompute the targeted review supplement statistics."""
import json
import numpy as np
import pandas as pd


def verify_review(root, check, close, X, y, names):
    read = lambda name: pd.read_csv(root / 'results' / name)
    configuration = json.loads((root / 'results/review_analysis_config.json').read_text(encoding='utf-8'))
    constants = [n for i, n in enumerate(names) if np.unique(X[:, i]).size == 1]
    check(configuration['constant_features'] == constants, 'review constant feature definitions')
    feature_sets = {'all_features': names, 'nonconstant_features': [n for n in names if n not in constants]}
    check(configuration['feature_sets'] == feature_sets, 'fixed sensitivity feature universes')
    importance, stability = read('shap_importance.csv'), read('shap_stability_sensitivity.csv')
    expected_pairs = {(scope, a, b) for scope in feature_sets for a in range(4) for b in range(a+1, 4)}
    check(len(stability) == 12 and set(zip(stability.scope, stability.fold_a, stability.fold_b)) == expected_pairs,
          'review stability phase coverage')
    for _, row in stability.iterrows():
        selected = feature_sets[row.scope]
        a, b = [importance[(importance.validation == 'time') & (importance.fold == f)]
                .set_index('feature').loc[selected] for f in (row.fold_a, row.fold_b)]
        check(row.n_features == len(selected), 'sensitivity feature count')
        close(row.rank_spearman, a.mean_abs.rank().corr(b.mean_abs.rank()), 'recomputed sensitivity Spearman')
        left, right = [set(part.sort_values(['mean_abs', 'feature'], ascending=[False, True]).head(5).index)
                       for part in (a, b)]
        close(row.top5_jaccard, len(left & right) / len(left | right), 'recomputed sensitivity Jaccard')
    predictions, references = read('engineering_predictions.csv'), read('probability_reference_comparison.csv')
    expected_keys = {(m, s, f) for m in ('LR', 'CART', 'XGBoost')
                     for s, folds in [('time', [-1, 0, 1, 2, 3]), ('holdout', [-1, 0])] for f in folds}
    check(len(references) == 21 and set(zip(references.model, references.validation, references.fold)) == expected_keys,
          'reference comparison coverage')
    for _, row in references.iterrows():
        part = predictions[(predictions.model == row.model) & (predictions.validation == row.validation)
                           & (predictions.variant == 'full')]
        if row.fold >= 0: part = part[part.fold == row.fold]
        labels = y[part.row.to_numpy(dtype=int)]
        close(part.y, labels, 'review labels aligned')
        check(row.n == len(part), 'reference cohort count')
        historical = float(np.mean((part.training_prior.to_numpy() - labels) ** 2))
        oracle = float(np.mean((labels.mean() - labels) ** 2))
        fitted = float(np.mean((part.calibrated.to_numpy() - labels) ** 2))
        for key, value in dict(model_brier=fitted, raw_brier=np.mean((part.score.to_numpy()-labels)**2),
            historical_brier=historical, oracle_brier=oracle, historical_skill=1-fitted/historical,
            oracle_skill=1-fitted/oracle, mean_training_prior=part.training_prior.mean(),
            observed_rate=labels.mean()).items():
            close(row[key], value, 'review reference ' + key)
    contrasts, phases = read('feature_ablation_phase_contrasts.csv'), read('feature_ablation_by_fold.csv')
    check(len(contrasts) == 12 and set(zip(contrasts.model, contrasts.fold)) ==
          {(m, f) for m in ('LR', 'CART', 'XGBoost') for f in range(4)}, 'phase contrast coverage')
    for _, row in contrasts.iterrows():
        part = phases[(phases.model == row.model) & (phases.fold == row.fold)].set_index('variant')
        values = {key: part.loc[variant, 'pr_auc'] for key, variant in
                  [('full_ap', 'full'), ('ratings_ap', 'ratings_only'), ('without_seismic_ap', 'without_seismic_activity')]}
        values.update(full_minus_ratings=values['full_ap']-values['ratings_ap'],
                      without_seismic_minus_full=values['without_seismic_ap']-values['full_ap'])
        for key, value in values.items(): close(row[key], value, 'review phase ablation ' + key)
