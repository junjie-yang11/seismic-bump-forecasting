"""Check extended experiment coverage, training provenance and explanations."""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from data import load, CSV_PATH
from engineering import GROUPS, BUDGETS, feature_variants, warning_summary
from evaluation import time_ordered_folds, stratified_random_folds
from metrics import prior_threshold, summarise, average_precision, roc_auc
from calibration import calibration_summary, prior_correction


def verify_research(root, check, close, replay=False):
    def read(name): return pd.read_csv(root / 'results' / name)
    X, y, names, _ = load(); variants = feature_variants(names)
    config = json.loads((root / 'results/research_config.json').read_text(encoding='utf-8'))
    check(config['data_sha256'] == hashlib.sha256(Path(CSV_PATH).read_bytes()).hexdigest(), 'research source hash')
    check(config['budgets'] == list(BUDGETS), 'prespecified budgets')
    check(config['variants'] == {k: [names[i] for i in v] for k, v in variants.items()}, 'feature group definitions')
    p, ref, audit = read('engineering_predictions.csv'), read('engineering_references.csv'), read('engineering_fold_audit.csv')
    ab, per_fold, interval, reps = read('feature_ablation.csv'), read('feature_ablation_by_fold.csv'), read('feature_ablation_intervals.csv'), read('feature_ablation_replicates.csv')
    budget, phase = read('warning_budgets.csv'), read('warning_budgets_by_fold.csv')
    keys = ('n', 'positives', 'prevalence', 'roc_auc', 'pr_auc', 'tp', 'fp', 'fn', 'tn', 'precision', 'recall', 'alert_rate')
    models = ('LR', 'CART', 'XGBoost'); schemes = ('time', 'holdout')
    expected = {(m, v, 'time') for m in models for v in variants} | {(m, 'full', 'holdout') for m in models}
    check(set(zip(p.model, p.variant, p.validation)) == expected, 'complete engineering combinations')
    check(set(zip(ref.model, ref.variant, ref.validation)) == expected, 'complete reference combinations')
    check(set(zip(audit.model, audit.variant, audit.validation)) == expected, 'complete engineering audits')
    check(not p.duplicated(['model', 'variant', 'validation', 'row']).any(), 'unique engineering predictions')
    check(not ref.duplicated(['model', 'variant', 'validation', 'fold', 'row']).any(), 'unique reference predictions')
    check(not audit.duplicated(['model', 'variant', 'validation', 'fold', 'policy', 'budget']).any(), 'unique warning policies')
    for frame in (ab, interval):
        check(len(frame) == 27 and set(zip(frame.model, frame.variant)) == {(m, v) for m in models for v in variants}, 'complete ablation summaries')
    check(len(per_fold) == 108 and not per_fold.duplicated(['model', 'variant', 'fold']).any(), 'complete phase summaries')
    check(len(budget) == 24 and len(phase) == 60, 'complete warning summaries')
    cut = int(.7 * len(y)); old = read('predictions.csv')
    for (model, variant, scheme), part in p.groupby(['model', 'variant', 'validation']):
        part = part.sort_values('row')
        splits = time_ordered_folds(len(y), 5) if scheme == 'time' else [(np.arange(cut), np.arange(cut, len(y)))]
        rows = np.concatenate([te for tr, te in splits])
        check(np.array_equal(part.row, rows), 'engineering complete test coverage')
        close(part.y, y[rows], 'engineering labels')
        check(np.isfinite(part.score).all() and part.score.between(0, 1).all(), 'finite engineering scores')
        a = audit[(audit.model == model) & (audit.variant == variant) & (audit.validation == scheme)]
        r = ref[(ref.model == model) & (ref.variant == variant) & (ref.validation == scheme)]
        check(len(a) == 5 * len(splits), 'every budget and historical policy present')
        for f, (tr, te) in enumerate(splits):
            segment = part[part.fold == f]; reference = r[r.fold == f].sort_values('row')
            inner = tr[:int(.8 * len(tr))]; reference_rows = tr[int(.8 * len(tr)):]
            check(np.array_equal(reference.row, reference_rows), 'reference stays inside training')
            close(segment.training_prior, y[tr].mean(), 'engineering training prior')
            expected_cal = prior_correction(segment.score, float(y[tr].mean()), .5) if model == 'LR' else segment.score
            close(segment.calibrated, expected_cal, 'engineering correction scale')
            policies = a[a.fold == f]
            check(set(policies.policy) == {'budget', 'historical_prevalence'}, 'policy types')
            close(policies[policies.policy == 'budget'].sort_values('budget').budget, BUDGETS, 'every fixed budget')
            for _, policy in policies.iterrows():
                check(policy.train_end == tr.max() and policy.n_train == len(tr)
                    and policy.inner_fit_end == inner.max() and policy.inner_fit_n == len(inner)
                    and policy.reference_start == reference_rows.min() and policy.reference_end == reference_rows.max()
                    and policy.reference_n == len(reference_rows) and policy.test_start == te.min()
                    and policy.test_end == te.max() and policy.n_test == len(te), 'engineering training and test ranges')
                rate = float(y[inner].mean()) if policy.policy == 'historical_prevalence' else policy.budget
                close(policy.budget, rate, 'training historical prevalence')
                threshold = prior_threshold(reference.score.to_numpy(), rate)
                close(policy.threshold, threshold, 'reference-derived budget threshold')
                count = int(np.sum(reference.score >= threshold))
                check(policy.reference_alerts == count and count <= np.floor(len(reference) * rate), 'reference tie cap')
                if policy.policy == 'historical_prevalence':
                    close(segment.threshold, threshold, 'historical threshold mapped to rows')
            if scheme == 'time':
                stored = per_fold[(per_fold.model == model) & (per_fold.variant == variant) & (per_fold.fold == f)].iloc[0]
                summary = summarise(segment.y.to_numpy(), segment.score.to_numpy(), threshold=segment.threshold.to_numpy())
                for key in keys: close(stored[key], summary[key], 'phase ablation ' + key)
        if scheme == 'time':
            stored = ab[(ab.model == model) & (ab.variant == variant)].iloc[0]
            summary = summarise(part.y.to_numpy(), part.score.to_numpy(), threshold=part.threshold.to_numpy())
            for key in keys: close(stored[key], summary[key], 'ablation ' + key)
            check(stored.n_features == len(variants[variant]), 'ablation feature count')
            calibration = calibration_summary(part.y.to_numpy(), part.calibrated.to_numpy(), 'check')
            for key in ('brier', 'ece'): close(stored[key], calibration[key], 'ablation calibration ' + key)
            full = ab[(ab.model == model) & (ab.variant == 'full')].iloc[0]
            ci = interval[(interval.model == model) & (interval.variant == variant)].iloc[0]
            close(ci.delta, stored.pr_auc - full.pr_auc, 'ablation paired difference')
            sample = reps[(reps.model == model) & (reps.variant == variant)].sort_values('replicate')
            check(len(sample) == 2000 and np.array_equal(sample.replicate, np.arange(2000)), 'all ablation replicates')
            close([ci.ci_low, ci.ci_high], np.quantile(sample.delta, [.025, .975]), 'ablation paired interval')
        if variant == 'full':
            if model != 'XGBoost':
                original = old[(old.validation == scheme) & old.model.str.contains('logistic' if model == 'LR' else 'CART')].sort_values('row')
                for key in ('score', 'threshold', 'calibrated'):
                    close(part[key], original[key], 'unchanged baseline ' + key)
            for summary in warning_summary(part, a):
                stored = budget[(budget.model == model) & (budget.validation == scheme) & np.isclose(budget.budget, summary['budget'])].iloc[0]
                for key in keys + ('alerts', 'alerts_per_detection'): close(stored[key], summary[key], 'warning ' + key)
            for f, segment in part.groupby('fold'):
                for summary in warning_summary(segment, a[a.fold == f]):
                    stored = phase[(phase.model == model) & (phase.validation == scheme) & (phase.fold == f) & np.isclose(phase.budget, summary['budget'])].iloc[0]
                    for key in keys + ('alerts',): close(stored[key], summary[key], 'phase warning ' + key)
    _verify_explanations(root, check, close, X, y, names, p)
    _verify_tuning(root, check, close, X, y, names, replay)


def _verify_explanations(root, check, close, X, y, names, predictions):
    read = lambda name: pd.read_csv(root / 'results' / name)
    shap = read('shap_predictions.csv'); importance = read('shap_importance.csv')
    check(len(shap) == 2837 and not shap.duplicated(['validation', 'row']).any(), 'complete SHAP coverage')
    columns = ['shap__' + n for n in names]
    check(np.isfinite(shap[columns].to_numpy()).all(), 'finite SHAP contributions')
    check(np.allclose(shap[columns].sum(axis=1) + shap.bias, shap.margin, atol=1e-5), 'SHAP additivity')
    check(np.allclose(1 / (1 + np.exp(-shap.margin)), shap.score, atol=1e-7), 'SHAP probability reconstruction')
    check((shap.train_end < shap.row).all(), 'SHAP training precedes explained row')
    check(len(importance) == 119 and not importance.duplicated(['validation', 'fold', 'feature']).any(), 'complete importance summaries')
    for scheme, part in shap.groupby('validation'):
        original = predictions[(predictions.model == 'XGBoost') & (predictions.variant == 'full') & (predictions.validation == scheme)].sort_values('row')
        part = part.sort_values('row'); close(part.score, original.score, 'SHAP saved prediction agreement')
        close(part.y, y[part.row.to_numpy(dtype=int)], 'SHAP labels')
        for fold, segment in [(-1, part)] + list(part.groupby('fold')):
            stored = importance[(importance.validation == scheme) & (importance.fold == fold)].set_index('feature').loc[names]
            mean_abs = segment[columns].abs().mean().to_numpy()
            close(stored.mean_abs, mean_abs, 'mean absolute SHAP')
            close(stored.mean_signed, segment[columns].mean().to_numpy(), 'mean signed SHAP')
            close(stored['rank'], pd.Series(mean_abs).rank(ascending=False, method='average'), 'SHAP ranks')
            for i, name in enumerate(names):
                raw = pd.Series(X[segment.row.to_numpy(dtype=int), i])
                contribution = segment[columns[i]].reset_index(drop=True)
                correlation = raw.rank().corr(contribution.rank()) if raw.nunique() > 1 and contribution.nunique() > 1 else np.nan
                close(stored.loc[name, 'value_contribution_spearman'], correlation, 'SHAP value association')
            groups = read('shap_groups.csv')
            groups = groups[(groups.validation == scheme) & (groups.fold == fold)].set_index('group')
            for group, members in GROUPS.items():
                joint = segment[['shap__' + n for n in members]].sum(axis=1)
                close(groups.loc[group, 'mean_abs_joint'], joint.abs().mean(), 'joint group SHAP')
    stability = read('shap_stability.csv')
    check(len(stability) == 6, 'all phase pairs')
    for _, pair in stability.iterrows():
        a = importance[(importance.validation == 'time') & (importance.fold == pair.fold_a)].set_index('feature').loc[names]
        b = importance[(importance.validation == 'time') & (importance.fold == pair.fold_b)].set_index('feature').loc[names]
        close(pair.rank_spearman, a['rank'].corr(b['rank']), 'phase importance correlation')
        left = set(a.sort_values(['mean_abs', 'feature'], ascending=[False, True]).head(5).index)
        right = set(b.sort_values(['mean_abs', 'feature'], ascending=[False, True]).head(5).index)
        close(pair.top5_jaccard, len(left & right) / len(left | right), 'phase top-five overlap')
    cases = read('shap_cases.csv'); values = read('shap_case_contributions.csv')
    check(len(cases) == 6, 'all predetermined case categories')
    for _, case in cases.iterrows():
        p = predictions[(predictions.model == 'XGBoost') & (predictions.variant == 'full') & (predictions.validation == case.validation)].sort_values('row')
        audit = read('engineering_fold_audit.csv')
        a = audit[(audit.model == 'XGBoost') & (audit.variant == 'full') & (audit.validation == case.validation) & (audit.policy == 'budget') & np.isclose(audit.budget, .1)]
        thresholds = p.fold.map(a.set_index('fold').threshold); alert = p.score >= thresholds
        mask = alert & (p.y == 1) if case.category == 'TP' else alert & (p.y == 0) if case.category == 'FP' else ~alert & (p.y == 1)
        eligible = p[mask]
        check(bool(case.available) == bool(len(eligible)), 'case availability')
        if not len(eligible): continue
        check(case.row == eligible.row.iloc[0], 'first chronological illustrative case')
        contribution = values[(values.validation == case.validation) & (values.category == case.category)].set_index('feature').loc[names]
        s = shap[(shap.validation == case.validation) & (shap.row == case.row)].iloc[0]
        close(contribution.contribution, s[columns].to_numpy(dtype=float), 'case contribution agreement')
        close(contribution.value, X[int(case.row)], 'case feature values')
        close(case.threshold, thresholds.loc[eligible.index[0]], 'case frozen cutoff')


def _verify_tuning(root, check, close, X, y, names, replay):
    read = lambda name: pd.read_csv(root / 'results' / name)
    manifests = json.loads((root / 'results/xgboost_tuning_manifest.json').read_text(encoding='utf-8'))
    tuning, scores = read('xgboost_tuning.csv'), read('xgboost_tuning_predictions.csv')
    check(len(manifests) == 60 and len(tuning) == 240, 'all nested searches')
    for manifest in manifests:
        rows, fit, reference = [np.array(manifest[k], dtype=int) for k in ('available_rows', 'fit_rows', 'reference_rows')]
        check(not np.intersect1d(fit, reference).size and np.array_equal(np.sort(np.r_[fit, reference]), np.sort(rows)), 'tuning partition')
        if manifest['validation'] != 'random':
            split = time_ordered_folds(len(y), 5)[manifest['fold']][0] if manifest['validation'] == 'time' else np.arange(int(.7 * len(y)))
            expected = split[:int(.8 * len(split))] if manifest['purpose'] == 'threshold_inner' else split
            check(np.array_equal(rows, expected) and fit.max() < reference.min(), 'nested tuning excludes future test rows')
        else:
            folds = stratified_random_folds(y, 10, manifest['seed'])
            check(np.array_equal(rows, np.flatnonzero(folds != manifest['fold'])), 'random tuning excludes outer test rows')
        candidates = tuning[tuning.key == manifest['key']].sort_values('candidate')
        check(len(candidates) == 4 and candidates.selected.sum() == 1, 'complete candidate search')
        for _, candidate in candidates.iterrows():
            p = scores[(scores.key == manifest['key']) & (scores.candidate == candidate.candidate)].sort_values('row')
            check(np.array_equal(p.row, np.sort(reference)), 'tuning reference coverage')
            close(p.y, y[p.row.to_numpy(dtype=int)], 'tuning reference labels')
            value = average_precision(p.y.to_numpy(), p.score.to_numpy()) if p.y.sum() else -np.mean((p.score - p.y) ** 2)
            close(candidate.value, value, 'training-only selection value')
        chosen = candidates.iloc[int(np.argmax(candidates.value.to_numpy()))]
        check(bool(chosen.selected) and manifest['depth'] == chosen.depth and manifest['rounds'] == chosen.rounds, 'training-only selected candidate')
    random = read('xgboost_random_predictions.csv'); shared = read('xgboost_shared_by_seed.csv')
    predictions = read('engineering_predictions.csv')
    temporal = predictions[(predictions.model == 'XGBoost') & (predictions.variant == 'full') & (predictions.validation == 'time')].sort_values('row')
    check(len(random) == 12890 and not random.duplicated(['seed', 'row']).any(), 'five XGBoost OOF seeds')
    for seed, part in random.groupby('seed'):
        check(np.array_equal(np.sort(part.row), np.arange(len(y))), 'XGBoost random coverage')
        assignment = stratified_random_folds(y, 10, int(seed))
        close(part.fold, assignment[part.row.to_numpy(dtype=int)], 'random fold assignment')
        matched = part.set_index('row').loc[temporal.row]
        stored = shared[shared.seed == seed].iloc[0]
        close(stored.random_ap, average_precision(temporal.y.to_numpy(), matched.score.to_numpy()), 'XGBoost matched random AP')
        close(stored.random_roc, roc_auc(temporal.y.to_numpy(), matched.score.to_numpy()), 'XGBoost matched random ROC')
    ci = read('xgboost_protocol_interval.csv').iloc[0]; reps = read('xgboost_protocol_replicates.csv')
    close(ci.delta, shared.random_ap.mean() - average_precision(temporal.y.to_numpy(), temporal.score.to_numpy()), 'XGBoost protocol difference')
    close([ci.ci_low, ci.ci_high], np.quantile(reps.delta, [.025, .975]), 'XGBoost protocol interval')
    for _, ci in read('research_model_intervals.csv').iterrows():
        other = ci.comparison.split(' minus ')[1]
        baseline = predictions[(predictions.model == other) & (predictions.variant == 'full') & (predictions.validation == 'time')].sort_values('row')
        close(ci.delta, average_precision(temporal.y.to_numpy(), temporal.score.to_numpy()) - average_precision(baseline.y.to_numpy(), baseline.score.to_numpy()), 'paired model difference')
        reps = read('research_model_replicates.csv').query('comparison == @ci.comparison')
        close([ci.ci_low, ci.ci_high], np.quantile(reps.delta, [.025, .975]), 'paired model interval')
    if replay:
        from boosting import BoostedModel
        import xgboost as xgb
        for manifest in manifests:
            if manifest['validation'] == 'random' or manifest['purpose'] != 'outer': continue
            tr = np.array(manifest['available_rows'], dtype=int)
            scheme, fold = manifest['validation'], manifest['fold']
            part = predictions[(predictions.model == 'XGBoost') & (predictions.variant == 'full') & (predictions.validation == scheme) & (predictions.fold == fold)].sort_values('row')
            fitted = BoostedModel(manifest['depth'], manifest['rounds'], names).fit(X[tr], y[tr])
            check(np.allclose(fitted.predict_proba(X[part.row.to_numpy(dtype=int)]), part.score, atol=1e-7), 'independent XGBoost full refit')
            saved = xgb.Booster(); saved.load_model(root / 'results/research_models' / ('xgboost_%s_fold%d.json' % (scheme, fold)))
            matrix = xgb.DMatrix(X[part.row.to_numpy(dtype=int)], feature_names=names)
            shap = read('shap_predictions.csv')
            shap = shap[(shap.validation == scheme) & (shap.fold == fold)].sort_values('row')
            stored = np.column_stack([shap[['shap__' + n for n in names]].to_numpy(), shap.bias])
            check(np.allclose(saved.predict(matrix, pred_contribs=True), stored, atol=1e-7), 'native TreeSHAP replay')


def main(replay=False):
    count = [0]
    def check(value, label):
        if not value: raise AssertionError(label)
        count[0] += 1
    def close(a, b, label): check(np.allclose(a, b, rtol=1e-9, atol=1e-10, equal_nan=True), label)
    verify_research(ROOT, check, close, replay)
    print('RESULT: %d extended consistency checks passed%s.' % (count[0], '; full XGBoost refits and native TreeSHAP replay passed' if replay else ''))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--replay', action='store_true')
    main(**vars(parser.parse_args()))
