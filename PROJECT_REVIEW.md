# Project review 2 October 2026

The current experiment outputs remain reproducible and internally consistent. This review found input-validation and reproduction-documentation defects, fixed them, and restored the paper's authorized byline and repository link. It did not identify renewed use of test labels for threshold selection, calibration priors or XGBoost parameter selection in the saved experiment workflow.

## Defects fixed

| Finding | Consequence before the fix | Change |
| --- | --- | --- |
| Metrics accepted mismatched shapes and invalid values | NumPy could silently broadcast predictions against labels. For example, labels `[0, 1]` and column predictions `[[0.2], [0.8]]` yielded Brier 0.34 instead of the intended paired 0.04. | Shared vector validation rejects mismatched shapes, empty arrays, nonbinary labels and nonfinite scores. Probability metrics also reject values outside 0 to 1. |
| Fold validation accepted negative, repeated or unordered indices | A negative training index can select the final record while passing the old maximum-index temporal check. An unordered training list also changes which observations enter the inner historical reference. Generated project folds did not use these malformed indices. | Training/test indices must be integer vectors within the data, unique and disjoint. Temporal indices must increase and all training records must precede testing. |
| Invalid labels could reach random-fold assignment | Labels other than 0 or 1 were never assigned a fold, leaving an uninitialised assignment value. | Reject invalid labels and impossible fold counts before assignment. Reject malformed feature matrices before validation or data loading returns them. |
| Extended-paper reproduction steps were absent from README | Running only the earlier workflow did not rebuild XGBoost, feature comparisons and explanations. Installation temporary directories were also visible as untracked files. | Document both environments and the ordered engineering/research workflow; ignore dependency-installation temporary directories. |

Changes are in `src/input_checks.py`, `src/metrics.py`, `src/calibration.py`, `src/evaluation.py`, `src/engineering.py`, `src/data.py`, `tests/test_input_validation.py`, `README.md` and `.gitignore`. Calibration and prevalence-drift comments now match the conditional interpretation already used by the paper.

## Evidence and remaining research scope

- All 39 regression tests passed in the research environment. The six new input-validation tests also passed in the original Python 3.7 environment.
- All 7,858 integrated result/report checks passed. The extended replay passed 7,149 checks, including five independent full XGBoost refits and exact native TreeSHAP reconstruction.
- Word and Markdown agree. All four-decimal numerical occurrences in the PDF match the source, and all 12 PDF pages were visually inspected. Experimental predictions, numerical tables and figures were not changed by the input guards.
- The dataset provides no explicit timestamps or longwall identifiers. Record-order validation remains an assumption, not a verified prospective field trial.
- Bootstrap intervals condition on saved predictions and empirical phases. They exclude the variability of a complete model-search/refitting procedure and are not adjusted for all feature comparisons.
- The holdout has already been inspected. It supplies supplementary warning evidence rather than an untouched confirmatory test. A new independent timed dataset is needed for confirmation.
- The XGBoost full-feature gain over hazard ratings has an interval spanning zero. Model explanations describe associations in fitted predictions; they do not establish causal failure mechanisms or guarantee operational safety.
- The baseline and extended experiments write combined result files in sequence. Both stages must finish before generating the extended paper; an interrupted refresh can leave a mixed result set that the verifiers reject.

The code review searched project sources for shell execution, dynamic code execution, unsafe pickle loading and archive extraction. The observed subprocess uses an argument list for `pip freeze`; the source audit reads a specified archive member without extracting arbitrary paths. This review is not a dependency CVE scan or a production-system penetration test.

## Paper identity fields

The paper again includes the authorized author name, university, discipline and GitHub repository URL. Word author/last-modifier metadata remains blank; personal local directory paths and unrelated background/contact material remain excluded. Both paper generators retain this distinction for future regeneration.
