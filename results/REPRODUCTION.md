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

## Supplementary paired analysis and paper edition

The supplementary analysis saves all five random seeds' OOF scores. The primary paired moving-block percentile intervals use length 32, 2,000 replicates and RNG seed 20261002; phase sizes are preserved. Lengths 16 and 64 and phase-stratified IID resampling are sensitivity analyses. No model is refitted in the bootstrap, so the intervals condition on observed predictions rather than estimating all sources of learning uncertainty.

LR common-test gap: 0.0114, 95% interval [-0.0110, 0.0243]. CART: 0.0188, [0.0064, 0.0323]. Descriptive reductions from the original different-cohort gap are 89.7% and 86.9%. These percentages are not drift or leakage attribution estimates.

The original UCI ARFF was independently downloaded and compared. First-occurrence deduplication matches the mirror exactly in order and contents. Six removed rows are negatives; hashes, full duplicate contents and original/mirror row mappings are saved. The audit establishes the mirror transformation, not the validity of deduplication for distinct shifts or the chronological interpretation of row order.

The main experiment now writes `random_predictions_by_seed.csv` and invokes `refresh_analysis.py`. To refresh the additions alone, run `python refresh_analysis.py`. To refit its random predictions, add `--rebuild`. The Word/PDF paper is generated after analysis, then checked with `verify_results.py --reports` and visual PDF inspection.

Final edition verification: 21 regression tests passed and 719 consistency checks passed, including every seed's AP/ROC, bootstrap percentile reproduction, sample/bin conservation, operating counts, source hashes/mapping, and Word-to-Markdown agreement.

The final paper edition has eight PDF pages. All eight were inspected after the last layout change. Numeric occurrences and paired interval bounds were checked against extracted PDF text; embedded text fonts are Times New Roman.
