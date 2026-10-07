"""Summarize saved test explanations and predetermined warning cases."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from data import load
from engineering import GROUPS
from uncertainty import paired_ap_interval


def explanation_summary(part, X, names):
    rows = []
    for i, feature in enumerate(names):
        values = part['shap__' + feature]
        raw = pd.Series(X[part.row.to_numpy(dtype=int), i], index=part.index)
        direction = raw.corr(values, method='spearman') if raw.nunique() > 1 and values.nunique() > 1 else np.nan
        rows.append(dict(feature=feature, n=len(part), mean_abs=float(values.abs().mean()),
            mean_signed=float(values.mean()), value_contribution_spearman=direction))
    out = pd.DataFrame(rows)
    out['rank'] = out.mean_abs.rank(ascending=False, method='average')
    return out


def analyse(root):
    results = root / 'results/phase1'; X, _, names, _ = load()
    shap = pd.read_csv(results / 'shap_predictions.csv')
    summary, group_summary = [], []
    for scheme, part in shap.groupby('validation'):
        for fold, segment in [(-1, part)] + list(part.groupby('fold')):
            summary.append(explanation_summary(segment, X, names).assign(validation=scheme, fold=fold))
            for group, features in GROUPS.items():
                joint = segment[['shap__' + n for n in features]].sum(axis=1)
                group_summary.append(dict(validation=scheme, fold=fold, group=group, n=len(segment),
                    mean_abs_joint=float(joint.abs().mean()), mean_signed_joint=float(joint.mean())))
    summary = pd.concat(summary, ignore_index=True)
    summary.to_csv(results / 'shap_importance.csv', index=False)
    pd.DataFrame(group_summary).to_csv(results / 'shap_groups.csv', index=False)
    phases = summary[(summary.validation == 'time') & (summary.fold >= 0)]
    stability = []
    for a in range(4):
        for b in range(a + 1, 4):
            left = phases[phases.fold == a].set_index('feature').loc[names]
            right = phases[phases.fold == b].set_index('feature').loc[names]
            top_a = set(left.sort_values(['mean_abs', 'feature'], ascending=[False, True]).head(5).index)
            top_b = set(right.sort_values(['mean_abs', 'feature'], ascending=[False, True]).head(5).index)
            stability.append(dict(fold_a=a, fold_b=b,
                rank_spearman=left['rank'].corr(right['rank']),
                top5_jaccard=len(top_a & top_b) / len(top_a | top_b)))
    pd.DataFrame(stability).to_csv(results / 'shap_stability.csv', index=False)

    predictions = pd.read_csv(results / 'engineering_predictions.csv')
    audit = pd.read_csv(results / 'engineering_fold_audit.csv')
    cases, contributions = [], []
    for scheme in ('time', 'holdout'):
        p = predictions[(predictions.model == 'XGBoost') & (predictions.variant == 'full') & (predictions.validation == scheme)].sort_values('row')
        a = audit[(audit.model == 'XGBoost') & (audit.variant == 'full') & (audit.validation == scheme)
                  & (audit.policy == 'budget') & np.isclose(audit.budget, .1)]
        thresholds = p.fold.map(a.set_index('fold').threshold)
        alert = p.score >= thresholds
        for category, mask in [('TP', alert & (p.y == 1)), ('FP', alert & (p.y == 0)), ('FN', ~alert & (p.y == 1))]:
            selected = p[mask]
            if not len(selected):
                cases.append(dict(validation=scheme, category=category, available=False))
                continue
            row = selected.iloc[0]; threshold = float(thresholds.loc[row.name])
            s = shap[(shap.validation == scheme) & (shap.row == row.row)].iloc[0]
            cases.append(dict(validation=scheme, category=category, available=True, row=int(row.row),
                fold=int(row.fold), y=int(row.y), score=row.score, threshold=threshold, budget=.1,
                margin=s.margin, bias=s.bias))
            for i, feature in enumerate(names):
                contributions.append(dict(validation=scheme, category=category, row=int(row.row),
                    feature=feature, value=X[int(row.row), i], contribution=s['shap__' + feature]))
    pd.DataFrame(cases).to_csv(results / 'shap_cases.csv', index=False)
    pd.DataFrame(contributions).to_csv(results / 'shap_case_contributions.csv', index=False)

    full = predictions[(predictions.validation == 'time') & (predictions.variant == 'full')]
    xgb = full[full.model == 'XGBoost'].sort_values('row')
    comparisons, reps = [], []
    for baseline in ('LR', 'CART'):
        other = full[full.model == baseline].sort_values('row')
        result, sample = paired_ap_interval(xgb.y.to_numpy(), xgb.score.to_numpy(), other.score.to_numpy(), xgb.fold.to_numpy())
        comparisons.append(dict(comparison='XGBoost minus ' + baseline, **result))
        reps.append(pd.DataFrame(dict(comparison='XGBoost minus ' + baseline,
            replicate=np.arange(len(sample)), delta=sample)))
    pd.DataFrame(comparisons).to_csv(results / 'research_model_intervals.csv', index=False)
    pd.concat(reps, ignore_index=True).to_csv(results / 'research_model_replicates.csv', index=False)
    from phase1.research_figures import render
    render(root)


if __name__ == '__main__':
    analyse(Path(__file__).resolve().parents[1])
