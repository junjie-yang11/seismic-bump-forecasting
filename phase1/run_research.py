"""Extended paper experiments; no README changes or test-based selection.

Run run_engineering.py first for the unchanged LR/CART baselines. This script
adds tuned XGBoost, the same nine ablations, matched random predictions,
native exact TreeSHAP, phase stability and predetermined case illustrations.
"""
from __future__ import annotations
import json
import platform
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
import xgboost
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from data import load
from evaluation import time_ordered_folds, stratified_random_folds
from engineering import feature_variants, evaluate_splits, warning_summary
from boosting import BoostedModel, select_parameters, PARAMETERS, CANDIDATES
from metrics import summarise, average_precision, roc_auc
from calibration import calibration_summary
from uncertainty import paired_ap_interval


def run():
    X, y, names, _ = load()
    results = ROOT / 'results/phase1'; models = results / 'research_models'; models.mkdir(exist_ok=True)
    config = json.loads((results / 'engineering_config.json').read_text(encoding='utf-8'))
    config.update(xgboost_parameters=PARAMETERS, candidates=CANDIDATES,
        selection='Inner AP; negative Brier for zero-positive reference; first candidate on exact ties',
        explanation='Native exact tree-path-dependent TreeSHAP; raw log-odds; training leaf covers',
        case_policy='First row per TP, FP, FN category at the predeclared 10% reference budget',
        environment=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                         xgboost=xgboost.__version__, scipy=scipy.__version__))
    (results / 'research_config.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    tuning, tuning_scores, manifests, shap_frames = [], [], [], []

    def tune(rows, scheme, fold, purpose, seed=-1):
        choice, candidates, fit, ref, scores = select_parameters(X[rows], y[rows], names, scheme != 'random')
        key = '%s_%d_%d_%s' % (scheme, seed, fold, purpose)
        manifests.append(dict(key=key, validation=scheme, fold=int(fold), seed=int(seed), purpose=purpose,
            available_rows=rows.tolist(), fit_rows=rows[fit].tolist(), reference_rows=rows[ref].tolist(),
            depth=choice[0], rounds=choice[1]))
        for candidate, score in zip(candidates, scores):
            tuning.append(dict(key=key, **candidate))
            tuning_scores.append(pd.DataFrame(dict(key=key, candidate=candidate['candidate'],
                row=rows[ref], y=y[rows[ref]], score=score)))
        return choice

    p_frames, r_frames, a_frames, metrics, fold_metrics, intervals, reps, budgets, phases = [], [], [], [], [], [], [], [], []
    for scheme in ('time', 'holdout'):
        cut = int(.7 * len(y))
        splits = time_ordered_folds(len(y), 5) if scheme == 'time' else [(np.arange(cut), np.arange(cut, len(y)))]
        choices = {}
        for f, (tr, _) in enumerate(splits):
            inner = tr[:max(1, int(.8 * len(tr)))]
            choices[f] = (tune(inner, scheme, f, 'threshold_inner'), tune(tr, scheme, f, 'outer'))
        full = None
        for variant, columns in feature_variants(names).items():
            if scheme == 'holdout' and variant != 'full':
                continue
            print('XGBoost %s: %s' % (scheme, variant), flush=True)

            def factory(fold, train, inner):
                inside, outside = choices[fold]
                feature_names = [names[i] for i in columns]
                return (lambda: BoostedModel(*inside, names=feature_names),
                        lambda: BoostedModel(*outside, names=feature_names))

            def explain(fold, model, train, test):
                if variant != 'full':
                    return
                contribution = model.contributions(X[test])
                margin = model.margin(X[test]); score = model.predict_proba(X[test])
                if not np.allclose(contribution.sum(axis=1), margin, atol=1e-5):
                    raise AssertionError('TreeSHAP additivity failed')
                frame = pd.DataFrame(contribution[:, :-1], columns=['shap__' + n for n in names])
                frame['row'], frame['fold'], frame['validation'] = test, fold, scheme
                frame['y'], frame['score'], frame['margin'], frame['bias'] = y[test], score, margin, contribution[:, -1]
                frame['train_end'] = int(train.max()); shap_frames.append(frame)
                model.booster.save_model(models / ('xgboost_%s_fold%d.json' % (scheme, fold)))

            p, ref, audit = evaluate_splits(None, X[:, columns], y, splits, fold_factory=factory, on_model=explain)
            for frame in (p, ref, audit):
                frame['model'], frame['variant'], frame['validation'] = 'XGBoost', variant, scheme
            p_frames.append(p); r_frames.append(ref); a_frames.append(audit)
            if variant == 'full':
                full = p
                budgets.extend(dict(model='XGBoost', validation=scheme, **s) for s in warning_summary(p, audit))
                for f, part in p.groupby('fold'):
                    phases.extend(dict(model='XGBoost', validation=scheme, fold=f, **s)
                        for s in warning_summary(part, audit[audit.fold == f]))
            if scheme != 'time':
                continue
            s = summarise(p.y.to_numpy(), p.score.to_numpy(), threshold=p.threshold.to_numpy())
            c = calibration_summary(p.y.to_numpy(), p.calibrated.to_numpy(), 'raw')
            metrics.append(dict(model='XGBoost', variant=variant, n_features=len(columns), **s, brier=c['brier'], ece=c['ece']))
            for f, part in p.groupby('fold'):
                fold_metrics.append(dict(model='XGBoost', variant=variant, fold=f,
                    **summarise(part.y.to_numpy(), part.score.to_numpy(), threshold=part.threshold.to_numpy())))
            result, samples = paired_ap_interval(p.y.to_numpy(), p.score.to_numpy(), full.score.to_numpy(), p.fold.to_numpy())
            intervals.append(dict(model='XGBoost', variant=variant, comparison='variant minus full', **result))
            reps.append(pd.DataFrame(dict(model='XGBoost', variant=variant, replicate=np.arange(len(samples)), delta=samples)))

    def append(name, frames):
        old = pd.read_csv(results / name)
        old = old[old.model != 'XGBoost']
        pd.concat([old] + frames, ignore_index=True).to_csv(results / name, index=False)

    for name, frames in [('engineering_predictions.csv', p_frames), ('engineering_references.csv', r_frames),
        ('engineering_fold_audit.csv', a_frames), ('feature_ablation.csv', [pd.DataFrame(metrics)]),
        ('feature_ablation_by_fold.csv', [pd.DataFrame(fold_metrics)]),
        ('feature_ablation_intervals.csv', [pd.DataFrame(intervals)]), ('feature_ablation_replicates.csv', reps),
        ('warning_budgets.csv', [pd.DataFrame(budgets)]), ('warning_budgets_by_fold.csv', [pd.DataFrame(phases)])]:
        append(name, frames)
    explanation = pd.concat(shap_frames, ignore_index=True)
    explanation.to_csv(results / 'shap_predictions.csv', index=False)

    random = []
    for seed in range(5):
        print('XGBoost random seed %d' % seed, flush=True)
        assignment = stratified_random_folds(y, 10, seed)
        for f in range(10):
            tr, te = np.flatnonzero(assignment != f), np.flatnonzero(assignment == f)
            choice = tune(tr, 'random', f, 'outer', seed)
            model = BoostedModel(*choice, names=names).fit(X[tr], y[tr])
            random.append(pd.DataFrame(dict(seed=seed, fold=f, row=te, y=y[te], score=model.predict_proba(X[te]))))
    random = pd.concat(random, ignore_index=True)
    random.to_csv(results / 'xgboost_random_predictions.csv', index=False)
    temporal = pd.concat(p_frames).query('validation == "time" and variant == "full"').sort_values('row')
    random_scores = np.array([random[random.seed == s].set_index('row').loc[temporal.row].score.to_numpy() for s in range(5)])
    result, samples = paired_ap_interval(temporal.y.to_numpy(), random_scores, temporal.score.to_numpy(), temporal.fold.to_numpy())
    pd.DataFrame([dict(model='XGBoost', **result)]).to_csv(results / 'xgboost_protocol_interval.csv', index=False)
    pd.DataFrame(dict(replicate=np.arange(len(samples)), delta=samples)).to_csv(results / 'xgboost_protocol_replicates.csv', index=False)
    pd.DataFrame([dict(seed=s, n=len(temporal), random_ap=average_precision(temporal.y.to_numpy(), scores),
        random_roc=roc_auc(temporal.y.to_numpy(), scores), time_ap=average_precision(temporal.y.to_numpy(), temporal.score.to_numpy()))
        for s, scores in enumerate(random_scores)]).to_csv(results / 'xgboost_shared_by_seed.csv', index=False)
    pd.DataFrame(tuning).to_csv(results / 'xgboost_tuning.csv', index=False)
    pd.concat(tuning_scores, ignore_index=True).to_csv(results / 'xgboost_tuning_predictions.csv', index=False)
    (results / 'xgboost_tuning_manifest.json').write_text(json.dumps(manifests, indent=2), encoding='utf-8')
    from phase1.research_analysis import analyse
    analyse(ROOT)
    from phase1.review_analysis import analyse as analyse_review
    analyse_review(ROOT)
    from phase1.generate_report import write_markdown_report
    write_markdown_report()
    print('Extended experiments and explanations saved.', flush=True)


if __name__ == '__main__':
    run()
