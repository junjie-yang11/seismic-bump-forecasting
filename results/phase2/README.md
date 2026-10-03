# Stage 2 evidence

| Step | Evidence |
| --- | --- |
| Recorded run and row boundaries | `run_manifest.json`, `fold_manifest.json`, `tuning.csv`, `tuning_predictions.csv` |
| Historical rule selection | `references.csv`, `candidates.csv`, `audits.csv` |
| Fixed/refitted transfer | `predictions.csv`, `decisions.csv`, `evaluations.csv`, `pooled_evaluations.csv` |
| Paired uncertainty | `comparisons.csv`, `bootstrap_replicates.npz`, `analysis_manifest.json` |
| No-alarm value | `decision_value.csv`, `decision_value_pooled.csv` |
| Selection reasons and margins | `threshold_explanations.csv`, `threshold_audit_enriched.csv` |
| Workload/detection comparison | `capacity_tradeoffs.csv`, `refit_transfer.csv` |
| Frozen prevalence scenarios | `prevalence_scenarios.csv`, `prevalence_decision_value.csv` |
| Independent checks | `verification.json`, `supplement_manifest.json`, `supplement_verification.json`, `formula_verification.json` |

[Protocol and execution](../../phase2/README.md) · [Final paper](../../reports/phase2/phase2_threshold_transfer_report.pdf) · [Historical review editions](../../docs/audits/phase2/history/).

Manifests record the actual run, implementation and evidence hashes. Git preserves audited file bytes so downloads retain those hashes. Observed loss uses the actual labels and alert decisions; scenario loss uses explicitly frozen class-conditional rates and hypothetical prevalence. Neither is measured economic loss or a count of prevented accidents.
