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
- Added `paper_content.py` and revised `generate_report.py` for a paper-style Word/PDF: title, conclusion-led abstract, keywords, numbered sections, table titles, figure captions, inline citations and numbered references. Times New Roman, black headings, fixed margins, justified body text and page numbers are set explicitly.
- Discussion connects shift-level predictions to inspection capacity, false-alarm workload, missed-event consequences and prospective validation.
- Added four paired-resampling regression tests and `verify_additions.py` checks for all seed metrics, interval percentiles, bin conservation, engineering counts and source mapping. Updated README and data documentation so the GitHub project exposes the evidence and the paper directly.

Final validation: the complete integrated experiment run succeeded; 21 regression tests passed and 719 consistency checks passed. Final Word and PDF contain the same text and numerical tables. All four-decimal report occurrences were verified in extracted PDF text. All eight final PDF pages were visually inspected, and embedded body/heading fonts are Times New Roman. No original ARFF data file is committed.

## Contribution-led paper polish (2026-10-02)

- Applied the anti-defensive-writing skill to the title, abstract, introduction, results, discussion and conclusions. The paper now leads with cohort comparability, training-prior calibration and the engineering consequences of a fixed warning threshold.
- Consolidated repeated qualifications into the relevant methods, interpretation and prospective-validation passages. Retained conditional bootstrap scope, both model intervals, negative Brier skill, missed-event counts and the record-order assumption.
- Updated `paper_content.py` and the README narrative, then regenerated `report/technical_note.md`, `report/technical_report.docx` and `report/technical_report.pdf`. Updated `generate_report.py` to keep the short warning-results introduction together across page breaks.
- No model, experiment, prediction or numerical result table was changed. All 719 report/result consistency checks passed; all four-decimal numerical occurrences were verified against PDF text. All eight final PDF pages were visually inspected, with embedded Times New Roman fonts.

## Extended paper experiments and explainability (2026-10-02)

- Three experimental stages support the paper: engineering feature comparisons, explanation stability and warning-budget evaluation.
- `src/engineering.py`, `run_engineering.py`: four exhaustive engineering groups, nine fixed feature sets, identical four record-order test phases, and 1/5/10/20 percent training-reference budgets. Saved inner-reference scores permit exact threshold and tie-cap checks. All future operating rates are measured, not forced to equal the training budget.
- `src/boosting.py`, `run_research.py`, `requirements-research.txt`: XGBoost 3.1.3 in a separate Python 3.12 environment. Four depth/round candidates are selected using only supplied training rows. Each outer fit and threshold-reference fit has its own inner selection. Full-training choices are held fixed across ablations. Five random-CV seeds use training-only selection and the same matched test cohort.
- `research_analysis.py`, `research_figures.py`: exact native TreeSHAP on raw log-odds, training leaf covers as reference, global/phase importances, value associations, rank correlations, top-five overlap and deterministic TP/FP/FN illustrations at the 10 percent budget. Saved models permit contribution replay. Cases and interpretations are descriptive, not causal.
- `research_paper.py`, `paper_content.py`, `generate_report.py`: rebuilt the paper around engineering information contribution, explanation stability and inspection workload. Preserved matched-validation findings, training-prior correction, conditional intervals, negative Brier skill and previously inspected holdout scope. Tables and figures are generated from saved evidence. Adjusted model-column widths and compact case panels for formal Word/PDF layout.
- `verify_research.py`, `verify_results.py`, three new test modules: coverage, data hashes, full feature partitions, training-only thresholds and parameter choices, every budget, every phase, ablation intervals, additive explanations, case rules and saved-model replay. Behavioral tests prove future-label invariance and corruption rejection.
- Main findings: full XGBoost AP 0.0862; its full-minus-ratings gain 0.0096 with conditional interval [-0.0148, 0.0413]. Importance-rank correlations 0.7122-0.9412 with top-five overlap 0.4286-0.6667. At 10/20 percent reference budgets, holdout XGBoost issues 30/81 alerts and detects 3/6 of 26 positive shifts. All nine feature sets and every budget are retained; no test-selected winning subset is claimed.
- Complete baseline-to-XGBoost extension rerun succeeded. All 33 regression tests passed. The extended verifier passed 7,149 checks including five full refits and native TreeSHAP replay; the integrated report verifier passes 7,858 consistency checks. Word and PDF use the same result-driven text. The final 12-page PDF is visually checked and its four-decimal numerical occurrences are verified against Markdown.

## Publication privacy review (2026-10-02)

- Removed identifying bylines and affiliations from both paper sources and regenerated Markdown, Word and PDF. Removed account-identifying repository links and material outside the tabular seismic-monitoring study.
- Replaced the project's named copyright attribution with Project contributors; the MIT license terms remain intact. Environment records now retain only the executable filename, and future environment generation omits absolute personal directory paths.
- Word generation clears author, last-modifier and descriptive property fields, removes unused custom XML stores and revision identifiers, and enables removal of personal information. PDF export excludes document properties. Final packages were checked for hidden content, attachments, comments, metadata and identifying text.
- Updated README and historical change-log descriptions to match the project-only report. Necessary dataset and method references are preserved. All final delivery aliases are replaced with the reviewed versions.
- All 7,858 result/report consistency checks passed after regeneration. Experimental data, predictions, figures and numerical results are unchanged. The final PDF's numerical occurrences match the source, and all 12 pages were visually inspected using Word export and Poppler.
- Review scope is the current project and final delivery files. Git commit history, remote account identity, installed environments and dependency download caches are outside this publication-material review.

## Code reliability review and authorized byline restoration (2026-10-02)

- Added src/input_checks.py and six behavioral regression tests. Metrics reject malformed vectors, nonfinite scores and nonbinary labels before broadcasting. Probability errors reject values outside 0 to 1. Validation rejects negative, out-of-range, repeated and unordered temporal indices before a model fit; random-fold assignment rejects invalid labels and fold counts.
- Integrated guards into data loading, evaluation and engineering experiments. Corrected calibration/prior interpretation comments without changing formulas. Added extended-paper reproduction instructions to README and ignored dependency-installation temporary directories.
- Restored the authorized paper byline, affiliation and repository URL in research_paper.py and paper_content.py. The Word generator centers only the actual byline block, keeping the abstract justified. Personal document metadata and machine paths remain excluded.
- Added PROJECT_REVIEW.md with concrete defect examples, affected files, verification evidence and remaining scientific limitations. No experimental predictions, result tables or figures changed.
- Validation: 39 tests passed in the research environment; the six new tests also passed on Python 3.7. Integrated report verification passed 7,858 checks; extended verification passed 7,149 checks with five independent XGBoost refits and TreeSHAP replay. All final PDF numerical occurrences match the source, and all 12 pages were visually inspected.

## Engineering contribution paper polish (2026-10-02)

- Applied the anti-defensive-writing skill to the extended paper source research_paper.py. Rewrote the abstract and introduction around the connection from monitoring information to explainable warning decisions and inspection workload.
- Promoted matched-cohort sensitivity and training-prior calibration to explicit abstract results. Connected feature ablations, phase explanations and warning policies to the same engineering question; replaced repeated defensive statements with direct descriptions of what each result establishes.
- Rewrote the discussion and conclusions to state the project's engineering contribution. Retained zero-crossing feature intervals, negative Brier skill, the record-order proxy, training-only selection, fixed-prediction and multiple-comparison scope, correlated-feature interpretation and the previously inspected holdout.
- Kept all seven tables byte-for-byte identical at the Markdown row level. No experiment, prediction, model setting or figure was changed. Authorized byline, affiliation and repository URL remain on the first page. README was not edited in this polish.
- Regenerated report/technical_note.md, report/technical_report.docx and report/technical_report.pdf. All 7,858 consistency checks passed; every four-decimal numerical occurrence in the final PDF matches the source. All 12 pages were visually inspected after Word export and Poppler rendering.

## Evidence-aligned review response (2026-10-03)

- Retitled the paper around evaluating reliability and explainability. Moved the record-order assumption into the abstract and reported both historical-reference and retrospective-reference Brier skill. Shortened the discussion and conclusions around the measured contributions.
- Added review_analysis.py and saved supplementary evidence for 12 fixed-universe stability comparisons, 21 pooled/phase probability-reference comparisons and 12 phase ablation contrasts. No model predictions, fitted parameters, warning cutoffs or figures were changed. run_research.py now refreshes these supplements automatically.
- Corrected LR Brier skill on the common cohort is 0.0342 against fold-specific historical training prevalence and -0.0751 against retrospective test prevalence. Nonconstant-feature rank stability spans 0.6570-0.9342; the original 17-feature range is 0.7122-0.9412.
- Compared full-model SHAP with refitted ablation, including the zero-crossing seismic-group-removal interval and all four phase contrasts. Added feature definitions, all 27 feature-set/model phase rows and all six stability pairs to the appendix.
- Clarified raw-score threshold transfer versus corrected probability assessment, asymmetric model configurations, outcome-dependent case categories and one-based duplicate provenance. Retained all 12 budget rows and added Precision.
- Added verify_review.py with independent recomputation and three corruption-rejection tests. All 42 tests and 8,169 report consistency checks passed. Independent feature-subset retuning and a frozen-inner-model comparison remain future experiments; this revision does not claim to have performed them.
- Changed files: research_paper.py, generate_report.py, review_analysis.py, verify_review.py, run_research.py, verify_research.py, tests/test_research_verifier.py, README.md, this log, the four review supplementary result files, and the regenerated Markdown/Word/PDF paper.
- Updated export_report.ps1 to export to a fresh system-temporary PDF before replacing the existing output and to close Word without save prompts. Verified export through PowerShell 7 and updated the reproduction command. Final PDF numeric occurrences match the generated source; all 15 pages were visually inspected. Authorized author, affiliation and GitHub URL remain on the first page.

## Complete execution and consistency audit (2026-10-03)

- Re-downloaded the UCI ARFF and CSV mirror; both match the audited input hashes byte-for-byte. Recomputed the first-occurrence duplicate mapping from the original source.
- Executed all three experiment stages in an isolated copy with initially empty results, followed by fresh verification. Compared all 44 result CSVs, all 17 figures and the complete regenerated paper with current evidence. Maximum absolute numeric difference was 4.0245584642661925e-16. Fourteen figures match byte-for-byte; three baseline PNGs have text-rasterization differences with identical colored curve and marker pixels. All five Word-embedded figures match their verified source files.
- Fixed clean-run/report-generation ordering in run_experiments.py, created missing directories in audit_source.py and generate_report.py, and added immediate stage/seed progress output. Aligned console accuracy/index claims and src/evaluation.py documentation with the paper. Numerical algorithms and paper results were unchanged.
- Clarified different historical-prevalence and fixed-budget policies, the research-environment requirement for full validation, PowerShell 7 export commands, and legitimate undefined CSV fields. The 307 empty numeric cells reproduce and have explicit storage/mathematical explanations; no substitute data were inserted.
- All 42 tests, 8,169 integrated checks and 7,460 extended checks with independent full XGBoost refits/native TreeSHAP replay passed. All 34 Python files parse. Fresh result-only verification passed 8,167 checks. Final PDF numbers continue to match the source; the unchanged report remains 15 pages.
- Added EXECUTION_AUDIT.md, results/execution_audit_comparison.json and the actual engineering/research execution logs. Updated PROJECT_REVIEW.md and results/REPRODUCTION.md to separate current verification from historical records. Added .audit-work/ to .gitignore. The isolated audit outputs remain locally available and are not publication inputs.

## Final paper narrative polish (2026-10-03)

- Applied the anti-defensive-writing skill to the abstract, introduction, discussion and conclusions in research_paper.py. Led with the effect of matching evaluation cohorts and connected probability references, monitoring-signal interpretation and warning workload to that result.
- Replaced generic framework descriptions with explicit relationships between the measured findings. Retained negative retrospective Brier skill, zero-crossing feature intervals, the record-order assumption, fixed-prediction uncertainty and the previously inspected holdout. Author, affiliation and repository link remain on the first page.
- All 115 Markdown table rows, experimental predictions, model settings, warning policies and figures remain unchanged. Regenerated the revised paper from independently recomputed results and confirmed exact Markdown agreement; all 44 CSV comparisons remain valid.
- Regenerated Word and PDF, checked all 15 rendered pages, and confirmed all four-decimal PDF numbers against the source. All 42 tests and 8,169 integrated checks passed.
