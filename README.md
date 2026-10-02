# Cohort matched evaluation of seismic bump forecasting for mine warning decisions

A mining-engineering evaluation workflow that matches test cohorts across protocols, assesses forecast probabilities using training-only information and translates fixed thresholds into event detection and inspection workload.

**Main finding:** matching the evaluation records reduces the apparent random-versus-record-order PR-AUC gap by 89.7% for logistic regression and 86.9% for CART. This is a descriptive cohort-sensitivity result; it is not a causal estimate of drift or leakage. In the common 2,063-row cohort:

| Model | Random mean AP | Record-order AP | Difference | Paired 95% interval |
| --- | --- | --- | --- | --- |
| LR | 0.0953 | 0.0838 | 0.0114 | [-0.0110, 0.0243] |
| CART | 0.0972 | 0.0784 | 0.0188 | [0.0064, 0.0323] |

Intervals use 2,000 phase-stratified paired moving-block replicates (length 32), averaging all five random seeds in each replicate. They condition on fixed predictions; they do not include model-refit uncertainty. Lengths 16 and 64 and paired IID resampling are sensitivity checks. LR crosses zero; CART retains a positive conditional difference.

**Calibration and warning consequences:** fold-local LR correction reduces ECE from 0.2904 to 0.0271 and Brier score from 0.1462 to 0.0439. Against a retrospective oracle constant reference, corrected Brier skill is -0.0751. In the final 774 shifts, a training-derived LR threshold produces 8 alerts, detects 2 hazardous shifts and misses 24. These results make probability assessment and threshold transfer explicit parts of the warning evaluation.

Read the [paper-style Word report](report/technical_report.docx), [PDF](report/technical_report.pdf), or [Markdown](report/technical_note.md). The discussion links shift-level forecasts to inspection workload and missed-event consequences. The experiments in this repository use tabular monitoring data.

## Data provenance

The original UCI ARFF has 2,584 records. The mirror removes six exact duplicate negative rows, retaining first occurrences and preserving the order of all remaining rows. A direct file comparison confirms this transformation; complete duplicate contents, row IDs, row mapping and hashes are in `results/source_*`. Identical readings need not represent invalid shifts, and row order alone does not confirm clock time or longwall grouping.

## Reproduce

```powershell
python -m pip install -r requirements.txt
python run_experiments.py
python audit_source.py
python -B -m unittest discover -s tests -v
python verify_results.py
```

`audit_source.py --source PATH_TO_ARFF` can audit a local original file without downloading. `--proxy URL` optionally supplies a proxy for the UCI download. Raw source data stay uncommitted. The supplied source audit describes the verified mirror version; changed sources should be audited again.

For an existing result set, `python refresh_analysis.py` regenerates the paired uncertainty and matched-cohort figures. `--rebuild` refits random predictions. A full experiment run saves all five seeds and invokes the paired analysis automatically.

```powershell
python -m pip install -r requirements-report.txt
python generate_report.py --docx
powershell -NoProfile -File export_report.ps1
python verify_results.py --reports
```

Word and Markdown share one result-driven source. PDF export requires Microsoft Word on Windows. The Word document uses a paper structure with title, abstract, keywords, numbered sections, table titles, figure captions and numbered references. All PDF pages are inspected after export.

### Extended paper experiments

The current paper also includes nine engineering feature sets, native XGBoost TreeSHAP, phase stability and four frozen warning budgets. Reproduce the original LR/CART evidence with the verified Python 3.7 environment recorded in `results/environment.txt`; create a separate Python 3.12 environment for the extension using `requirements-research.txt`. With existing verified baseline outputs:

```powershell
# Run in the baseline environment first.
python run_engineering.py
# Run in the Python 3.12 research environment next.
python run_research.py
python -B -m unittest discover -s tests -v
python verify_research.py --replay
python -m pip install -r requirements-report.txt
python generate_report.py --docx
powershell -NoProfile -File export_report.ps1
python verify_results.py --reports
```

Both experiment stages must finish before regenerating the extended paper. A baseline refresh replaces the combined feature/budget files; the research stage restores XGBoost rows and explanations. The README's original results above describe the earlier historical-prevalence policy; the paper's budget tables describe the separately evaluated 1/5/10/20 percent policies.

## Auditable outputs

| Output | Purpose |
| --- | --- |
| `metrics_by_scheme.csv`, `random_metrics_by_seed.csv` | Aggregate and seed-specific metrics |
| `predictions.csv`, `fold_audit.csv` | Training priors, frozen thresholds and fold provenance |
| `random_predictions_by_seed.csv` | All five random seeds' row-level OOF scores |
| `shared_test_by_seed.csv`, `shared_test_comparison.csv` | Identical-cohort comparisons |
| `paired_uncertainty.csv`, `bootstrap_replicates.csv` | Conditional intervals, settings and replicate statistics |
| `gap_attenuation.csv` | Descriptive gap reduction after matching test rows |
| `operating_points.csv` | Per-phase and holdout warning counts |
| `calibration.csv`, `calibration_bins.csv` | Calibration metrics and conserved bin counts |
| `source_audit.json`, `source_duplicates.csv`, `source_row_mapping.csv` | Original-to-mirror provenance |

All output names above refer to `results/`. The verifier recomputes every seed's ranking metrics, operating counts, bin summaries, interval percentiles and row coverage, and checks generated Word text against Markdown. Behavioral tests cover leakage invariance, tied scores, paired resampling and rejection of corrupted result files. This establishes reproducibility and consistency, not the truth of the ordering assumptions.

## Evaluation rules and limitations

Only LR uses balanced class weights; CART is unweighted and receives no balanced-prior correction. Scaling, thresholds and priors are estimated within training. Thresholds are fixed numerical cutoffs chosen using inner-reference scores; future alert rates can differ after refitting or drift. Calibration correction is monotone within a fold, while different fold corrections can change pooled rankings.

The dataset lacks timestamps and longwall IDs. The block length is a transparent sensitivity choice rather than an identified dependence horizon. Confidence intervals condition on observed scores. Matched-cohort comparisons still use different training histories and sizes. No prospective field trial is claimed.

See `MODIFICATION_LOG.md`, `results/REPRODUCTION.md` and the paper references for details. Code license: MIT; source-data terms follow the cited providers.
