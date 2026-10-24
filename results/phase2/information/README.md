# Matched monitoring-information evidence

This directory contains actual outputs of the separately specified [protocol](../../../phase2/information/protocol.json). Original two-stage and ranking-pilot results remain in their existing directories. No result is supplied as a placeholder or an expected improvement.

| Evidence | Purpose |
| --- | --- |
| `run_manifest.json` | Input, protocol, source, protected-original and output hashes; actual runtime and environment |
| `fold_manifest.json` | Exact fitting, unused policy-reference, inner tuning and test row IDs; selected parameters for each design |
| `models/` | Eight fitted XGBoost models, one per design and test block |
| `tuning.csv`, `tuning_predictions.csv` | All 32 candidate objectives and row-level historical inner-validation scores |
| `rows.csv` | Test labels, grades, both model scores and label-free fractional inclusion probabilities at each budget |
| `allocations.csv` | Shared grade quotas, cohort sizes and hazardous-shift counts |
| `evaluations.csv` | All 16 phase-budget results and four supplementary pooled sums, including E(TP), E(FN), K and their contrast |
| `intervals.csv` | All 60 phase/pooled, budget and block-length comparisons; the point is unchanged across lengths |
| `bootstrap_counts.npz` | Every paired within-phase multiset, for all three lengths |
| `bootstrap_replicates.npz` | Both expected detection counts and their difference after reallocation and reranking on every draw |
| `verification.json` | Actual separate-path calculation/model-replay checks, and whether full refitting was requested and passed |

The main contrast is extended minus base E(TP), so positive favors the monitoring extension under the specified workflow. Expected detections integrate uniform random allocation at exact score ties; they may be fractional. They are not accidents avoided or executed inspections. Confidence intervals are conditional on frozen fitted models, not full training-process intervals. Record-block lengths are not verified physical time durations.

Run `python -B -m phase2.information.verify --refit` in an isolated copy for full model re-execution and saved-evidence verification. Follow the [execution guide](../../../phase2/information/README.md) and [reporting guide](../../../reporting/README.md) for authoring and exported-document checks. Failed runs/checks revoke earlier success instead of preserving it.
