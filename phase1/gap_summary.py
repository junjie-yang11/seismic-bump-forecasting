"""Recompute cohort-sensitive AP gaps from saved predictions, without fitting.

Run after the complete Stage 1 workflow with ``python -m phase1.gap_summary``.
The original two-model gap table is retained as locked evidence. This module
writes a separate three-model table after run_research has saved XGBoost scores.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from metrics import average_precision

BASE_MODELS = {
    'LR': 'logistic regression (L2, class-weighted)',
    'CART': 'bagged CART (60 trees, depth 6)',
}


def design_gap(random, ordered, labels, model):
    """Mean the five seed-specific APs; never pool seed predictions."""
    labels = np.asarray(labels, dtype=float)
    if labels.ndim != 1 or not len(labels) or not np.isin(labels, (0, 1)).all():
        raise ValueError('Nonempty binary source labels required')
    required = {'row', 'y', 'score'}
    if not required.issubset(ordered) or not required.union({'seed'}).issubset(random):
        raise ValueError('Saved prediction columns missing')
    if set(random.seed.unique()) != set(range(5)):
        raise ValueError('Exactly seeds 0 through 4 required')
    def validate(frame, full):
        values = frame[['row', 'y', 'score']].to_numpy(float)
        row = values[:, 0]
        if (not len(frame) or not np.isfinite(values).all()
                or np.any(row != np.floor(row)) or np.any(row < 0)
                or np.any(row >= len(labels)) or frame.row.duplicated().any()):
            raise ValueError('Invalid, duplicate or missing prediction rows')
        if full and set(row) != set(range(len(labels))):
            raise ValueError('Each random seed must cover every source row')
        if not np.array_equal(values[:, 1], labels[row.astype(int)]):
            raise ValueError('Prediction labels differ from source rows')
        if np.any(values[:, 2] < 0) or np.any(values[:, 2] > 1):
            raise ValueError('Prediction probabilities must lie in [0,1]')
    ordered = ordered.sort_values('row')
    validate(ordered, False)
    if not ordered.y.sum():
        raise ValueError('AP requires positive labels in the evaluation cohort')
    full_ap, common_ap = [], []
    for seed in range(5):
        frame = random[random.seed == seed].sort_values('row')
        validate(frame, True)
        common = frame.set_index('row').loc[ordered.row]
        full_ap.append(average_precision(frame.y.to_numpy(), frame.score.to_numpy()))
        common_ap.append(average_precision(common.y.to_numpy(), common.score.to_numpy()))
    ordered_ap = average_precision(ordered.y.to_numpy(), ordered.score.to_numpy())
    original = float(np.mean(full_ap) - ordered_ap)
    matched = float(np.mean(common_ap) - ordered_ap)
    if original == 0:
        raise ValueError('Attenuation is undefined for a zero original gap')
    return dict(model=model, original_gap=original, same_test_gap=matched,
                gap_reduction_fraction=1 - matched / original)


def compute_gap_rows(root=ROOT, *, allow_missing_xgboost=False):
    root = Path(root)
    folder = root / 'results/phase1'
    labels = pd.read_csv(root / 'data/seismic-bumps.csv')['class'].to_numpy(float)
    random = pd.read_csv(folder / 'random_predictions_by_seed.csv')
    ordered = pd.read_csv(folder / 'predictions.csv')
    if set(random.model.unique()) != set(BASE_MODELS.values()):
        raise ValueError('Unexpected baseline prediction models')
    result = []
    common_rows = None
    for short, name in BASE_MODELS.items():
        time = ordered[(ordered.model == name) & (ordered.validation == 'time')]
        rows = np.sort(time.row.to_numpy())
        if common_rows is not None and not np.array_equal(rows, common_rows):
            raise ValueError('Baseline common cohorts differ')
        common_rows = rows
        result.append(design_gap(random[random.model == name], time, labels, short))
    xgb_path = folder / 'xgboost_random_predictions.csv'
    if not xgb_path.exists():
        if not allow_missing_xgboost:
            raise FileNotFoundError('Run Stage 1 XGBoost experiments before the complete gap summary')
        return result
    extended = pd.read_csv(folder / 'engineering_predictions.csv')
    time = extended[(extended.model == 'XGBoost') & (extended.variant == 'full')
                    & (extended.validation == 'time')]
    if not np.array_equal(np.sort(time.row.to_numpy()), common_rows):
        raise ValueError('XGBoost common cohort differs from baseline cohorts')
    result.append(design_gap(pd.read_csv(xgb_path), time, labels, 'XGBoost'))
    return result


def write_gap_summary(root=ROOT, *, allow_missing_xgboost=False):
    rows = compute_gap_rows(root, allow_missing_xgboost=allow_missing_xgboost)
    path = Path(root) / 'results/phase1/gap_attenuation_all_models.csv'
    pd.DataFrame(rows).to_csv(path, index=False)
    print('Recomputed AP gap summary from saved predictions: ' + ', '.join(r['model'] for r in rows), flush=True)
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--allow-missing-xgboost', action='store_true',
                        help='Explicit baseline-only intermediate output before the research stage')
    write_gap_summary(**vars(parser.parse_args()))
