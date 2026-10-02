# Complete execution and evidence audit — 3 October 2026

The current experimental evidence and paper were checked against a new complete execution in an isolated project copy with an initially empty results directory. No published predictions, metrics, fitted models or bootstrap replicates were supplied to that copy. The complete regenerated Markdown paper matches the current paper exactly. No fabricated measurements, substitute predictions or placeholder numerical results were found in the checked evidence.

## Input provenance

The UCI ZIP archive and CSV mirror were downloaded again. Their contents match the cached original ARFF and the input CSV byte-for-byte. A new source audit confirms 2,584 original rows, 2,578 mirror rows and 170 retained positive targets. The six removed rows are exact duplicate negative records; retaining first occurrences preserves mirror order.

- Original ARFF SHA-256: `aabe512fab65b36d1dfb462650b75cfd8d99d8cc2723e8ecb4e6f5e1caccd5a7`
- Model-input CSV SHA-256: `e41de6a3c2039ce5a50d081143bd573581f2b4c053a49e665145f5c16c1d1d7a`
- Primary source: https://archive.ics.uci.edu/dataset/266/seismic+bumps
- Mirror: https://raw.githubusercontent.com/datasets/seismic-bumps/main/data/seismic-bumps.csv

## Actual execution

The isolated run executed `run_experiments.py`, `audit_source.py --source data/original-seismic-bumps.arff`, `run_engineering.py`, `run_research.py` and `verify_results.py`, in that order. Baseline and engineering calculations used the verified Python 3.7.0 environment; research calculations used Python 3.12.14 with the pinned research dependencies. All stages completed successfully.

Engineering execution took 86.6091008 seconds and research execution 11.5567641 seconds in this run. Baseline execution completed but was not separately timed. Tree training is computation-heavy; it is distinct from a hung process. Hardware and library versions affect duration.

## Independent comparisons

- All 44 published result CSVs were compared, including row-level predictions, training-reference scores, tuning decisions, warning counts, bootstrap replicates, SHAP contributions and the review supplements.
- Shapes, column names, categorical values and missing-value locations agree. Numeric comparisons use relative tolerance 1e-9 and absolute tolerance 1e-10. Maximum observed absolute difference: 4.0245584642661925e-16.
- All 17 saved figures were checked. Fourteen files are identical. Three baseline PNGs differ in text rasterization between Pillow environments; the colored curve and marker pixels match exactly.
- The complete paper generated from fresh calculations matches `report/technical_note.md` exactly. Its matched-cohort results, model-configuration notes, calibration references, ablations, phase evidence, cases and warning policies therefore reproduce from actual calculations.
- All five Word-embedded figures match the verified source figure files. Word text and tables match Markdown, and every four-decimal numerical occurrence in the final 15-page PDF matches the paper source. The existing report layout was already inspected page by page and was unchanged in this audit.

Machine-readable file comparisons and hashes are in `results/execution_audit_comparison.json`. Actual stage output is retained in `results/engineering_execution_audit_log.txt` and `results/research_execution_audit_log.txt`. The isolated results remain available locally in the ignored `.audit-work` folder.

## Verification

- All 34 Python source files parse successfully.
- All 42 behavioral/regression tests pass.
- All 8,169 integrated result/report checks pass.
- All 7,460 extended checks pass with five independent full-feature XGBoost refits and native TreeSHAP replay.
- Fresh result-only verification passes 8,167 checks; the additional two integrated checks validate the existing Word document.

Random numbers in the experiment code implement declared fold assignment, bootstrap aggregation, permutation analysis and uncertainty resampling. They do not replace monitoring measurements or targets. Synthetic arrays and mocks in tests are isolated test fixtures and do not supply experiment or paper results.

## Empty cells and numerical conventions

There are 307 empty numeric cells in the published CSV evidence. They were inspected and reproduced:

- 239 aggregate `threshold` cells: the summary was evaluated with a vector of frozen cutoffs. Actual cutoffs are retained in predictions and fold-audit records, rather than represented by one aggregate scalar.
- 46 feature-value/contribution correlations: one variable is constant, so Spearman correlation is undefined.
- 22 alerts-per-detection ratios: no positive shift was detected, so division by zero is undefined.

These are declared storage or mathematical conventions, not estimated or invented values. Infinite thresholds can also encode a zero-alert reference budget; they are deliberate policies rather than non-finite model predictions. Saved model probabilities were independently checked as finite values in [0,1].

## Corrections made during this audit

- `run_experiments.py`: defer paper generation when source provenance has not yet been audited, and retain the extended paper until its engineering/research stages have been rebuilt. Enable immediate stage/seed progress output. Replace the inaccurate accuracy-baseline and index-probe console claims with statements consistent with the paper.
- `audit_source.py`: create needed output directories so a clean project can perform source auditing.
- `generate_report.py`: create the report directory when generating Markdown.
- `src/evaluation.py`: state the record-order assumption consistently with the paper; no validation algorithm changes.
- `README.md`: distinguish historical-prevalence and fixed-budget warning policies, specify the research environment for complete validation, align both PDF-export commands, and explain undefined cells.
- `.gitignore`: exclude the local isolated audit copy. `results/REPRODUCTION.md` identifies current evidence separately from earlier historical records.

No numerical model algorithm, fitted prediction, selected parameter, warning cutoff or paper result was changed by these corrections.

The subsequent prose polish on 3 October 2026 revised the abstract, introduction, discussion and conclusions. All 115 Markdown table rows and all experimental evidence remain unchanged. The revised paper was also regenerated from the isolated run's results, with exact Markdown agreement, and its 15 Word/PDF pages were inspected again. The comparisons above therefore remain applicable to the final polished paper.

## Scientific scope

The evidence is internally consistent and executable under the documented environments. It does not establish real timestamps or longwall grouping absent from the dataset. Paired intervals condition on fixed predictions; they exclude full learning/selection uncertainty. SHAP explains fitted associations, while ablation refits a different model. The previously inspected holdout is supplementary evidence. Current model scores do not establish a dataset predictability ceiling or validate a deployed mine-warning system.
