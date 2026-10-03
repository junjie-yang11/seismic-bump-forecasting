# Computed evidence

This directory contains saved calculations underlying the two papers. Start with the [Stage 1 paper](../report/technical_note.md) or [Stage 2 paper](phase2/report/phase2_threshold_transfer_report.md), then use the groups below to trace the evidence.

## Stage 1

| Evidence | Main files or folders |
| --- | --- |
| Data provenance | `source_audit.json`, `source_duplicates.csv`, `source_row_mapping.csv` |
| Predictions and fold boundaries | `predictions.csv`, `random_predictions_by_seed.csv`, `fold_audit.csv` |
| Protocol and cohort comparison | `metrics_by_scheme.csv`, `shared_test_comparison.csv`, `shared_test_by_seed.csv`, `paired_uncertainty.csv`, `gap_attenuation.csv` |
| Probability calibration | `calibration.csv`, `calibration_bins.csv`, `probability_reference_comparison.csv` |
| Engineering feature comparisons | `feature_ablation*.csv`, `engineering_predictions.csv`, `engineering_references.csv`, `engineering_fold_audit.csv` |
| XGBoost and explanations | `xgboost_*.csv`, `shap_*.csv`, `research_models/` |
| Warning workload | `warning_budgets.csv`, `warning_budgets_by_fold.csv`, `operating_points.csv` |
| Figures and reproduction | `figures/`, `REPRODUCTION.md`, execution and verification logs |

## Stage 2

All second-stage evidence is under [phase2/](phase2/). The [module guide](../phase2/README.md#evidence-in-resultsphase2) describes each file, its units and conventions. Predictions, reference scores, candidate thresholds and selection audits preserve the chain from historical policy selection to later evaluation. `comparisons.csv` and `bootstrap_replicates.npz` retain paired uncertainty; `prevalence_scenarios.csv` stores the separate hypothetical expectations.

The independent paper and figures are under [phase2/report/](phase2/report/).

## Interpretation

Empty fields have documented meanings, such as undefined quantities or thresholds stored at a finer row level. Synthetic test fixtures are separate from these measured results. Preserve result filenames when reproducing the papers: report builders and verifiers use them to check provenance and consistency.
