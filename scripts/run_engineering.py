"""Run nine fixed feature sets and four prespecified warning budgets.

Uses the existing record-order folds and model settings. No model selection
on test outcomes; the previously inspected holdout is descriptive evaluation.
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from data import load, CSV_PATH
from evaluation import time_ordered_folds
from engineering import GROUPS, BUDGETS, feature_variants, evaluate_splits, warning_summary
from metrics import summarise
from calibration import calibration_summary
from uncertainty import paired_ap_interval
from scripts.run_experiments import MODELS


def run():
    X, y, names, _ = load()
    variants = feature_variants(names)
    splits = time_ordered_folds(len(y), 5)
    configuration = dict(groups=GROUPS, variants={k: [names[i] for i in v] for k, v in variants.items()},
        budgets=BUDGETS, inner_fraction=.8, bootstrap_length=32, bootstrap_replicates=2000,
        bootstrap_seed=20261002, data_sha256=hashlib.sha256(Path(CSV_PATH).read_bytes()).hexdigest(),
        models=list(MODELS), forest_seed=7, holdout_fraction=.7,
        interpretation='Fixed comparisons; no test-based feature or budget selection. Holdout previously inspected.')
    results = ROOT / 'results'
    (results / 'engineering_config.json').write_text(json.dumps(configuration, indent=2), encoding='utf-8')
    predictions, references, audits, metrics, folds, intervals, replicates, budgets, phases = [], [], [], [], [], [], [], [], []
    for model, factory in MODELS.items():
        short = 'LR' if 'logistic' in model else 'CART'
        baseline = None
        for variant, columns in variants.items():
            print('%s: %s (%d features)' % (short, variant, len(columns)), flush=True)
            p, ref, audit = evaluate_splits(factory, X[:, columns], y, splits)
            for frame in (p, ref, audit):
                frame['model'], frame['variant'], frame['validation'] = short, variant, 'time'
            predictions.append(p); references.append(ref); audits.append(audit)
            s = summarise(p.y.to_numpy(), p.score.to_numpy(), threshold=p.threshold.to_numpy())
            c = calibration_summary(p.y.to_numpy(), p.calibrated.to_numpy(), 'training-prior scale')
            metrics.append(dict(model=short, variant=variant, n_features=len(columns), **s,
                brier=c['brier'], ece=c['ece']))
            for fold, part in p.groupby('fold'):
                folds.append(dict(model=short, variant=variant, fold=fold,
                    **summarise(part.y.to_numpy(), part.score.to_numpy(), threshold=part.threshold.to_numpy())))
            if baseline is None:
                baseline = p
            delta, samples = paired_ap_interval(p.y.to_numpy(), p.score.to_numpy(),
                baseline.score.to_numpy(), p.fold.to_numpy())
            intervals.append(dict(model=short, variant=variant, comparison='variant minus full', **delta))
            replicates.append(pd.DataFrame(dict(model=short, variant=variant,
                replicate=np.arange(len(samples)), delta=samples)))
            if variant == 'full':
                budgets.extend(dict(model=short, validation='time', **s) for s in warning_summary(p, audit))
                for f, part in p.groupby('fold'):
                    phases.extend(dict(model=short, validation='time', fold=f, **s)
                        for s in warning_summary(part, audit[audit.fold == f]))
        cut = int(.7 * len(y))
        p, ref, audit = evaluate_splits(factory, X, y, [(np.arange(cut), np.arange(cut, len(y)))])
        for frame in (p, ref, audit):
            frame['model'], frame['variant'], frame['validation'] = short, 'full', 'holdout'
        predictions.append(p); references.append(ref); audits.append(audit)
        budgets.extend(dict(model=short, validation='holdout', **s) for s in warning_summary(p, audit))
        phases.extend(dict(model=short, validation='holdout', fold=0, **s) for s in warning_summary(p, audit))
    frames = {
        'engineering_predictions.csv': pd.concat(predictions, ignore_index=True),
        'engineering_references.csv': pd.concat(references, ignore_index=True),
        'engineering_fold_audit.csv': pd.concat(audits, ignore_index=True),
        'feature_ablation.csv': pd.DataFrame(metrics), 'feature_ablation_by_fold.csv': pd.DataFrame(folds),
        'feature_ablation_intervals.csv': pd.DataFrame(intervals),
        'feature_ablation_replicates.csv': pd.concat(replicates, ignore_index=True),
        'warning_budgets.csv': pd.DataFrame(budgets), 'warning_budgets_by_fold.csv': pd.DataFrame(phases),
    }
    for name, frame in frames.items():
        frame.to_csv(results / name, index=False)
    from scripts.engineering_figures import render
    render(ROOT)
    # A baseline refresh temporarily removes extended rows. The extended
    # paper is regenerated after run_research.py restores all three models.
    if not (results / 'research_config.json').exists():
        from scripts.generate_report import write_markdown_report
        write_markdown_report()
    print('Engineering experiments saved.', flush=True)


if __name__ == '__main__':
    run()
