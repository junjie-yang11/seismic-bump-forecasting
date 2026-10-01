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

## Second review and completed repair (2026-10-02)

The earlier 33 checks established only approximate agreement with old ranking metrics. They did not detect the shared 70-percent calibration reference overlapping early temporal test folds, or the continued use of test-score quantiles for threshold selection. This entry supersedes the earlier claims about leakage prevention.

### Changed code

- `src/metrics.py`: `summarise` now requires an explicit fixed scalar or per-row threshold. `prior_threshold` is a training-reference selector; it excludes boundary ties so the reference alert count cannot exceed the integer budget. PR curves start at precision 1. The tied-score AP and ROC endpoint corrections are retained.
- `src/evaluation.py`: inner training validation selects a fixed threshold for each outer fold. Calibration priors come from that fold's training labels only. Zero-positive test blocks are retained. Splits reject overlapping train/test or repeated test rows. CART receives no prior correction.
- `src/calibration.py`: calibration inputs are validated; tied quantile edges retain all observations. Documentation distinguishes fold-local monotonic correction from pooled rankings.
- `src/data.py`: removed the incorrect full-rank claim for the retained design matrix.
- `run_experiments.py`: all random-CV operating metrics are averaged across five seeds. Added same-test comparisons, per-seed summaries, row-level predictions and fold audit records. Holdout and temporal metrics use fixed training-derived thresholds. Figures and all result files were regenerated.
- `verify_results.py`: replaced fixed old-value comparisons and the forced large-gap assertion with recomputation from stored predictions, complete coverage checks, training-prior/threshold provenance, seed aggregation and generated report checks. The verifier checks stored consistency; it is not an independent scientific validation or full model replay.
- `tests/test_evaluation.py`: 12 behavioral tests for future-label/feature invariance, ties, all-negative blocks, calibration and split validation.
- `tests/test_result_verifier.py`: five in-memory corruption tests for missing predictions and modified priors, thresholds, calibration metrics and random means.
- `generate_report.py`, `requirements-report.txt`, `export_report.ps1`: Markdown and Word now share one result-driven source; PDF is exported from Word on Windows. Word generation uses the bundled Python environment with python-docx 1.2.0, separate from the Python 3.7 analysis environment.
- `README.md`, `results/REPRODUCTION.md`, `results/summary.md`, `report/technical_note.md`, `report/technical_report.docx`, `report/technical_report.pdf`: updated methods, results and limitations. Removed unsupported causal interpretations and stale calibration values.

### Verified results

- Full experiment rerun completed on the project's Python 3.7.0 environment.
- 17 regression tests passed, including five tests proving the result verifier rejects corrupted inputs.
- `verify_results.py --reports`: all 496 consistency checks passed.
- Word paragraphs and table cells match the generated Markdown. PDF exported successfully, all four-decimal report values were checked against extracted PDF text, and all six rendered pages were visually inspected.
- Same-test LR mean PR-AUC: random 0.0953, record order 0.0838 (2,063 rows). Training histories still differ, so this is not a pure leakage estimate.
- Fold-local LR calibration: ECE 0.0271, mean prediction 0.0694, observed prevalence 0.0427. This replaces the over-optimistic earlier calibration numbers.

### Remaining limitations

The dataset lacks timestamps and wall IDs. No temporal confidence intervals or prospective evaluation are available. Transferring an inner-fit threshold to the fully refitted model can change its operating rate, as can distribution drift. Prior correction does not by itself prove deployment calibration. These are stated in the reports rather than presented as solved.

## Paper-format and evidence enhancement (2026-10-02)

- Reframed the report around three contributions: sensitivity of the apparent validation gap to test-cohort composition, calibration improvement, and fixed-threshold warning consequences. The descriptive gap reductions are 89.7% (LR) and 86.9% (CART), not causal shares attributable to drift or leakage.
- Added `src/uncertainty.py` and `refresh_analysis.py`: 2,000 phase-stratified paired moving-block bootstrap replicates for block lengths 16, 32 and 64, plus paired IID sensitivity. Each replicate uses the same sampled rows for labels and every prediction vector; its statistic averages AP differences across five random seeds. Intervals condition on fixed OOF predictions and exclude model-refit uncertainty.
- Saved all five seeds' predictions in `random_predictions_by_seed.csv`, bootstrap statistics in `bootstrap_replicates.csv`, and settings/intervals in `paired_uncertainty.csv`. Main experiments now invoke the supplementary analysis automatically.
- Primary 95% intervals: LR difference 0.0114, [-0.0110, 0.0243]; CART difference 0.0188, [0.0064, 0.0323]. The LR interval crosses zero; the CART intervals remain positive across examined block lengths. Neither finding identifies the causal mechanism.
- Added common-test PR/ROC curves and an interval figure. Random curves use seed 0 only for display; result tables average all five seeds. Updated LR calibration figure with sample/bin counts and marker sizes. Both LR panels contain 10 bins with 206-207 observations each.
- Added `audit_source.py`: a direct comparison confirms the 2,578-row mirror equals first-occurrence deduplication of the 2,584-row UCI ARFF without reordering. Removed original rows 90, 91, 973, 974, 1018 and 1019 are exact duplicate negatives. Complete duplicate rows, retained IDs, row mapping and SHA-256 hashes are committed in `results/source_*`. Identical measurements are not assumed to be invalid shifts.
- Added `operating_points.csv`, `gap_attenuation.csv` and `calibration_bins.csv`. The holdout LR threshold issues 8 alerts and detects 2 of 26 positives, missing 24. Lower prevalence alone is not asserted to explain this threshold-transfer result.
- Added `paper_content.py` and revised `generate_report.py` for a paper-style Word/PDF: title and affiliation, conclusion-led abstract, keywords, numbered sections, table titles, figure captions, inline citations and numbered references. Times New Roman, black headings, fixed margins, justified body text and page numbers are set explicitly.
- Discussion connects shift-level predictions to inspection capacity, false-alarm workload, missed-event consequences and prospective validation. UAV/image material is a proposed transfer of validation principles, not a claim that an image model or flight project was performed in this repository.
- Added four paired-resampling regression tests and `verify_additions.py` checks for all seed metrics, interval percentiles, bin conservation, engineering counts and source mapping. Updated README and data documentation so the GitHub project exposes the evidence and the paper directly.

Final validation: the complete integrated experiment run succeeded; 21 regression tests passed and 719 consistency checks passed. Final Word and PDF contain the same text and numerical tables. All four-decimal report occurrences were verified in extracted PDF text. All eight final PDF pages were visually inspected, and embedded body/heading fonts are Times New Roman. No original ARFF data file is committed.

## Contribution-led paper polish (2026-10-02)

- Applied the anti-defensive-writing skill to the title, abstract, introduction, results, discussion and conclusions. The paper now leads with cohort comparability, training-prior calibration and the engineering consequences of a fixed warning threshold.
- Consolidated repeated qualifications into the relevant methods, interpretation and prospective-validation passages. Retained conditional bootstrap scope, both model intervals, negative Brier skill, missed-event counts and the record-order assumption. UAV/image validation remains a proposed extension.
- Updated `paper_content.py` and the README narrative, then regenerated `report/technical_note.md`, `report/technical_report.docx` and `report/technical_report.pdf`. Updated `generate_report.py` to keep the short warning-results introduction together across page breaks.
- No model, experiment, prediction or numerical result table was changed. All 719 report/result consistency checks passed; all four-decimal numerical occurrences were verified against PDF text. All eight final PDF pages were visually inspected, with embedded Times New Roman fonts.
