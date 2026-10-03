"""Targeted review supplements computed from existing predictions and SHAP."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from data import load
from calibration import brier_score


def stability_sensitivity(importance, feature_sets):
    rows = []
    phases = importance[(importance.validation == 'time') & (importance.fold >= 0)]
    for scope, names in feature_sets.items():
        for a in range(4):
            for b in range(a + 1, 4):
                left = phases[phases.fold == a].set_index('feature').loc[names]
                right = phases[phases.fold == b].set_index('feature').loc[names]
                # Recompute average ranks on the same fixed feature universe.
                ranks_a = left.mean_abs.rank(ascending=False, method='average')
                ranks_b = right.mean_abs.rank(ascending=False, method='average')
                top_a = set(left.sort_values(['mean_abs', 'feature'], ascending=[False, True]).head(5).index)
                top_b = set(right.sort_values(['mean_abs', 'feature'], ascending=[False, True]).head(5).index)
                rows.append(dict(scope=scope, n_features=len(names), fold_a=a, fold_b=b,
                    rank_spearman=ranks_a.corr(ranks_b),
                    top5_jaccard=len(top_a & top_b) / len(top_a | top_b)))
    return pd.DataFrame(rows)


def reference_comparison(predictions):
    rows = []
    full = predictions[predictions.variant == 'full']
    for (model, scheme), part in full.groupby(['model', 'validation']):
        for fold, segment in [(-1, part)] + list(part.groupby('fold')):
            y = segment.y.to_numpy()
            historical = brier_score(y, segment.training_prior.to_numpy())
            oracle = brier_score(y, np.full(len(y), y.mean()))
            fitted = brier_score(y, segment.calibrated.to_numpy())
            rows.append(dict(model=model, validation=scheme, fold=fold, n=len(y),
                model_brier=fitted, raw_brier=brier_score(y, segment.score.to_numpy()),
                historical_brier=historical, oracle_brier=oracle,
                historical_skill=1 - fitted / historical if historical else np.nan,
                oracle_skill=1 - fitted / oracle if oracle else np.nan,
                mean_training_prior=segment.training_prior.mean(), observed_rate=y.mean()))
    return pd.DataFrame(rows)


def phase_contrasts(per_fold):
    rows = []
    for (model, fold), part in per_fold.groupby(['model', 'fold']):
        part = part.set_index('variant')
        full, ratings, removed = [float(part.loc[v, 'pr_auc'])
                                  for v in ('full', 'ratings_only', 'without_seismic_activity')]
        rows.append(dict(model=model, fold=fold, full_ap=full, ratings_ap=ratings,
            without_seismic_ap=removed, full_minus_ratings=full-ratings,
            without_seismic_minus_full=removed-full))
    return pd.DataFrame(rows)


def analyse(root=ROOT):
    X, _, names, _ = load()
    results = root / 'results'
    constant = [name for i, name in enumerate(names) if np.ptp(X[:, i]) == 0]
    feature_sets = {'all_features': names,
                    'nonconstant_features': [n for n in names if n not in constant]}
    # Whole-cohort constants define a descriptive sensitivity set, not a fit.
    configuration = dict(feature_sets=feature_sets, constant_features=constant,
        scope='Descriptive reanalysis of saved predictions; no model or budget selection',
        historical_reference='Per-row outer-training unweighted prevalence; frozen before each test phase',
        oracle_reference='Evaluation-cohort prevalence; retrospective metric reference only')
    (results / 'review_analysis_config.json').write_text(json.dumps(configuration, indent=2), encoding='utf-8')
    stability_sensitivity(pd.read_csv(results / 'shap_importance.csv'), feature_sets).to_csv(
        results / 'shap_stability_sensitivity.csv', index=False)
    reference_comparison(pd.read_csv(results / 'engineering_predictions.csv')).to_csv(
        results / 'probability_reference_comparison.csv', index=False)
    phase_contrasts(pd.read_csv(results / 'feature_ablation_by_fold.csv')).to_csv(
        results / 'feature_ablation_phase_contrasts.csv', index=False)
    print('Review supplements saved without refitting or changing predictions.')


if __name__ == '__main__':
    analyse()
