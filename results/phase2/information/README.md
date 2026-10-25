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
| `historical_context.zip` | Original bytes of the bounded older report outputs and derived-gap summary/entry points, with the unchanged original run manifest; each archived hash is checked against that manifest |

The main contrast is extended minus base E(TP), so positive favors the monitoring extension under the specified workflow. Expected detections integrate uniform random allocation at exact score ties; they may be fractional. They are not accidents avoided or executed inspections. Confidence intervals are conditional on frozen fitted models, not full training-process intervals. Record-block lengths are not verified physical time durations.

Run `python -B -m phase2.information.verify --refit` in an isolated copy for full model re-execution and saved-evidence verification. Follow the [execution guide](../../../phase2/information/README.md) and [reporting guide](../../../reporting/README.md) for authoring and exported-document checks. Failed runs/checks revoke earlier success instead of preserving it.

The original `run_manifest.json` records what remained unchanged **during the experiment**. Subsequent manuscript integration and gap-summary authoring/checking changes are separately generated revisions. Their original source/presentation bytes are retained in `historical_context.zip`; the verifier checks an explicitly bounded inventory, the archive's original manifest identity and every archived file against the original protected hash. It reports current differences in these historical context files rather than claiming that revised papers remain unchanged. All data, model implementation, locked protocols, original predictions and other protected computational evidence continue to require their current bytes to match. The original two-model gap CSV remains byte-for-byte unchanged and live-checked. The additional `results/phase1/gap_attenuation_all_models.csv` is independently recomputed from saved row-level scores; current reports receive their own document checks. A later experiment run with a different manifest is checked against its own live protected files; the older snapshot does not grant exemptions to that run.

The snapshot was produced from the retained pre-revision repository archive using `python -B -m phase2.information.provenance --baseline-tar <pre-revision-archive.tar>`. The command refuses an existing destination or any original bytes inconsistent with the recorded hashes. It does not generate a success certificate or replace the original manifest. The verification record includes the snapshot and helper-source fingerprints and distinguishes historical context from live computational checks.
