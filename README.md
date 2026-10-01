# Seismic-bump forecasting: validation and calibration

A reproducible comparison of logistic regression and bagged CART on the 2,578-row Seismic Bumps mirror. The task is prediction of hazardous events in the next shift. Record order is a temporal proxy; timestamps and longwall identifiers are unavailable.

Random and record-order validation produce different results, but their original test populations also differ. A large PR-AUC gap cannot be interpreted as a causal estimate of temporal leakage. `results/shared_test_comparison.csv` compares the protocols on identical test rows, while retaining differences in training history and size.

## Evaluation rules

- Logistic regression uses balanced class weights. CART uses ordinary bootstrap sampling, unweighted Gini and unweighted leaf proportions.
- Scaling is fitted inside each training fold.
- Alert thresholds use an inner validation subset of each outer training fold. The inner training prevalence sets the reference alert budget. The numerical threshold is then frozen for the outer test fold; neither future labels nor future scores select it.
- Boundary ties are excluded together. The reference alert budget is an upper bound, and the future alert rate can differ under drift or after refitting.
- Logistic prior correction uses each outer training fold's prevalence. CART is evaluated as fitted.
- All test rows are retained, including all-negative test blocks. Single-class ROC-AUC is undefined.
- Random validation tables average every metric across seeds 0 to 4; curve plots show seed 0.

## Run and verify

```powershell
python -m pip install -r requirements.txt
python -B -m unittest discover -s tests -v
python -B run_experiments.py
python -B verify_results.py
```

The analysis uses NumPy, pandas and Pillow, without scikit-learn or a GPU. It has been rerun locally on Python 3.7.0, NumPy 1.21.6, pandas 1.1.5 and Pillow 9.5.0. The additional inner fits increase runtime.

`verify_results.py` recomputes metrics from saved row-level predictions, checks test coverage and fold provenance, verifies seed aggregation and compares Markdown with current result files. It verifies consistency, not a scientific conclusion. Behavioral tests separately check invariance to changes in future labels and features.

## Reports

Markdown is generated automatically by the experiments. To regenerate Word and PDF:

```powershell
python -m pip install -r requirements-report.txt
python -B generate_report.py --docx
powershell -NoProfile -File export_report.ps1
python -B verify_results.py --reports
```

PDF export requires installed Microsoft Word on Windows. `--reports` checks all Word paragraphs and table cells against the generated Markdown and confirms a PDF exists; PDF layout and text also need inspection after export.

## Output files

| File | Purpose |
| --- | --- |
| `results/metrics_by_scheme.csv` | Main metrics, including actual alert rates |
| `results/random_metrics_by_seed.csv` | Five random-validation runs |
| `results/shared_test_by_seed.csv` | Comparisons on the same test rows |
| `results/shared_test_comparison.csv` | Same-test seed means |
| `results/predictions.csv` | Row-level predictions, thresholds, priors and fold IDs; random seed 0, temporal and holdout |
| `results/fold_audit.csv` | Training/test ranges, inner sizes, fixed thresholds and training priors |
| `results/calibration.csv` | Fold-local LR correction and unweighted CART |
| `results/holdout.csv` | Final 30-percent test period |
| `results/summary.md` | Generated tables and methodological notes |
| `report/technical_note.md` | Full generated report |
| `report/technical_report.docx` | Word version of the same content |
| `report/technical_report.pdf` | PDF exported from Word |

See `MODIFICATION_LOG.md` for repair history and `results/REPRODUCTION.md` for verification details. Permutation importance is descriptive and measured in-sample. Prior correction assumes a prior shift and does not certify operational calibration. The Brier skill reference uses evaluation prevalence retrospectively as an oracle baseline.

## Limitations

The same-test comparison controls the evaluation rows but not training size or time period. No confidence intervals or prospective deployment evaluation are supplied. The chronological interpretation depends on the dataset order. Thresholds may need separate prospective validation because inner and refitted model score scales can differ. These results do not establish suitability for mine safety decisions.

## References and license

The report lists the source dataset and methodological references. MIT license: see `LICENSE`.
