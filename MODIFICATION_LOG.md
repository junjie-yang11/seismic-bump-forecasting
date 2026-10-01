# Modification log

Date: 2026-10-02

## Evaluation and leakage fixes

- `src/metrics.py`: average precision now aggregates equal score values before integrating; ROC plotting points include `(0, 0)` and `(1, 1)`; calibration/alert thresholds validate their prevalence; `summarise()` requires a prevalence supplied from training data instead of deriving it from evaluation labels.
- `src/calibration.py`: reliability bins validate inputs, handle repeated quantile edges and constant predictions, and keep every observation assigned to a bin.
- `run_experiments.py`: thresholds and prior corrections use the first 70% historical prevalence; chronological holdout uses the training prevalence; prior correction is applied only to the class-weighted logistic model. CART is explicitly reported as unweighted and evaluated as fitted.

## Verification

- Metric smoke tests: passed (tied-score PR-AUC, ROC endpoints, constant calibration bins, and threshold leakage guard).
- `python run_experiments.py`: completed successfully and regenerated `results/`.
- `python verify_results.py`: all 33 repository consistency checks passed.
