# Reproduction record: corrected pipeline, 2 October 2026

The complete experiment was rerun locally using Python 3.7.0, NumPy 1.21.6, pandas 1.1.5 and Pillow 9.5.0. Raw output is in `run_log.txt`.

```
python -B run_experiments.py
python -B -m unittest discover -s tests -v
python -B verify_results.py --reports
```

Results: full run completed; 17 regression tests passed; 496 consistency checks passed. Five verifier tests deliberately corrupt outputs in memory and confirm rejection. No input or result files are modified by those tests.

The verifier reconstructs test coverage from the declared protocols, recomputes metrics from saved predictions and checks each fold's historical prevalence, threshold metadata, calibration transformation and seed means. Random row-level predictions cover seed 0; the remaining seeds have separate metric summaries. This does not constitute replaying every model fit or proving the scientific ordering assumption.

Reports use one result-driven source. Word was generated with bundled Python 3.12.14 and python-docx 1.2.0. PDF was exported by Microsoft Word. Word text and all table cells match current Markdown; all four-decimal report values occur in the extracted PDF, and all six PDF pages were visually checked.

## Changes in interpretation

On the common 2,063 test rows, LR random mean PR-AUC is 0.0953 versus 0.0838 for record order. CART has 0.0972 versus 0.0784. Training size and periods still differ. These gaps cannot be assigned wholly to leakage.

Fold-local LR prior correction has ECE 0.0271 and mean prediction 0.0694, with observed prevalence 0.0427. The earlier global or shared-history prior was inappropriate for some temporal folds. CART is unweighted and is not prior-corrected.

Thresholds are numerical cutoffs frozen from training-only inner validation. The temporal LR alert rate is 0.1832 and recall 0.1932; holdout alert rate is 0.0103 and recall 0.0769. This variation demonstrates why a training alert budget is not a guarantee of the future operating rate.

## Audit artifacts

`fold_audit.csv` stores training/test ranges, training priors, inner fit/reference sizes and fixed thresholds. `predictions.csv` stores row IDs, labels, raw and corrected probabilities, thresholds and fold IDs for random seed 0, record-order validation and holdout. `random_metrics_by_seed.csv` and `shared_test_by_seed.csv` retain all five seeds' summaries.
