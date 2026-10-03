# Stage 1 evidence

| Evidence | Files |
| --- | --- |
| Source transformation | `source_audit.json`, `source_duplicates.csv`, `source_row_mapping.csv`, `integrity.json` |
| Baseline fits | `predictions.csv`, `fold_audit.csv`, `random_predictions_by_seed.csv`, `random_metrics_by_seed.csv` |
| Comparable cohorts | `shared_test_*`, `gap_attenuation.csv`, `paired_uncertainty.csv`, `bootstrap_replicates.csv` |
| Probabilities | `calibration.csv`, `calibration_bins.csv`, `probability_reference_comparison.csv` |
| Feature groups | `engineering_*`, `feature_ablation*`, `research_model_*` |
| XGBoost provenance | `research_config.json`, `research_models/`, `xgboost_tuning*`, `xgboost_protocol*`, `xgboost_random_predictions.csv` |
| Explanations | `shap_*` |
| Warning decisions | `warning_budgets.csv`, `warning_budgets_by_fold.csv`, `operating_points.csv`, `holdout.csv` |
| Additional diagnostics | `importance.csv`, `leakage_probe.csv`, `figures/`, `summary.md` |

These outputs support both headline and descriptive diagnostic comparisons; they are not alternate final reports. Numeric CSV evidence is retained for independent reconstruction. [Execution guide](../../phase1/README.md) · [Final paper](../../reports/phase1/technical_report.pdf).
