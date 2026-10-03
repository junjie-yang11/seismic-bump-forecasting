# Seismic Hazard Forecasting and Warning Decisions

**A retrospective mining study of how forecast evidence translates into warning loss, detections and inspection workload.**

The project uses the audited UCI Seismic Bumps mirror: 2,578 shift records and 170 hazardous-shift labels. It follows the evidence from monitoring inputs to predictions, calibration, historical threshold selection and later inspection workload.

## Start here

| Study | Question | Final paper | Editable paper | Code and steps |
| --- | --- | --- | --- | --- |
| **Stage 1 · Forecast evaluation** | How do comparable test cohorts, probability calibration and model explanations change the interpretation of performance? | [PDF](reports/phase1/technical_report.pdf) | [Word](reports/phase1/technical_report.docx) | [Stage 1 guide](phase1/README.md) |
| **Stage 2 · Warning decisions** | How do historical thresholds transfer under assumed missed-event costs and inspection capacity? | [PDF](reports/phase2/phase2_threshold_transfer_report.pdf) | [Word](reports/phase2/phase2_threshold_transfer_report.docx) | [Stage 2 guide](phase2/README.md) |

Read Stage 1 for predictive evidence and Stage 2 for decision value, capacity excess and refitting effects. [All final reports](reports/README.md) include online manuscripts. The [research overview](docs/PROJECT_OVERVIEW.md) connects the questions, findings and next studies in a short read.

## Three findings

1. **Who is tested changes the apparent validation gap.** On common test records, the original random-versus-record-order AP gap shrinks by 89.7% for LR and 86.9% for CART; residual differences are 0.0114 and 0.0188. This recalculation shows cohort sensitivity, not a causal decomposition of leakage or drift. [Matched results](results/phase1/shared_test_comparison.csv) · [Gap calculation](results/phase1/gap_attenuation.csv).
2. **A historical optimum can have no later loss advantage over no alarms.** At `r=10`, pooled fixed XGBoost cost-plus-capacity rule C has differences of **0.00 to +0.82 relative loss units per 100 shifts** versus no alarms across four budgets. Negative differences would mean improvement. The result applies to the assumed cost and observed cohort. [No-alarm comparison](results/phase2/decision_value_pooled.csv).
3. **Historical capacity feasibility does not guarantee future feasibility.** Budget rule A exceeds later capacity in **13/16 phase–budget settings**; C does so in **2/64 phase–budget–cost settings**. These are different, dependent setting counts, not directly comparable independent violation rates. Refitting can also change alerts at the same finite numerical cutoff. [Capacity and detection](results/phase2/capacity_tradeoffs.csv) · [Refitting](results/phase2/refit_transfer.csv).

## Read the decision tradeoff

![Fixed XGBoost C-minus-A and C-minus-B loss differences by phase, historical budget and assumed missed-event cost](reports/phase2/loss_contrasts.png)

The existing Stage 2 figure compares **C minus A** and **C minus B** on the same later records. Every cell is relative loss per 100 shifts at its labelled cost ratio `r` and historical budget; false-alert cost is 1. **Negative values favor C; positive values favor the comparator.** Panels have separate color scales, so compare the numbers rather than color intensity between panels. This figure compares warning rules; the [no-alarm table](results/phase2/decision_value_pooled.csv) supplies the separate decision-value baseline at `r=10`.

## Contribution and study scope

The project contributes an audited data transformation, comparable-cohort evaluation, training-local probability and threshold handling, and joint accounting of transferred loss, detection, capacity and refitting. Established model and decision methods support these empirical findings. [Contribution and method origins](docs/RELATED_WORK.md) · [Study boundaries and next questions](docs/PROJECT_OVERVIEW.md#study-boundaries-and-next-questions).

Recorded order is a temporal proxy, costs are hypothetical, and the labels describe hazardous shifts. These studies do not demonstrate prevented accidents or an operationally optimal warning system.

## Quick verification

With Python 3.12 and the [research dependencies](requirements/requirements-research.txt), run from the repository root:

```text
python -B -m phase1.quick_check
```

This checks saved evidence and formulas in a disposable copy, preserves published verification records and ends with `QUICK CHECK PASSED` if all checks succeed. It downloads the mirror only when the local cache is absent. [Setup, scope and measured runtime](docs/QUICK_CHECK.md) · [Full model reproduction](docs/REPRODUCING.md).

## Follow the research workflow

| Step | What it does | Code | Evidence |
| --- | --- | --- | --- |
| 1 | Audit the official dataset and the mirror transformation | [Source audit](phase1/audit_source.py), [data loading](src/data.py) | `results/phase1/source_*` |
| 2 | Fit LR/CART under random and expanding record-order validation | [Baseline experiment](phase1/run_experiments.py), [shared validation](src/evaluation.py) | `results/phase1/predictions.csv`, `fold_audit.csv` |
| 3 | Compare the same test rows and assess probabilities | [Paired analysis](phase1/refresh_analysis.py), [metrics](src/metrics.py), [calibration](src/calibration.py) | `shared_test_*`, `paired_uncertainty.csv`, `calibration*` |
| 4 | Evaluate engineering feature groups and XGBoost explanations | [Feature study](phase1/run_engineering.py), [XGBoost study](phase1/run_research.py), [explanation analysis](phase1/research_analysis.py) | `results/phase1/feature_ablation*`, `shap_*`, `warning_budgets*` |
| 5 | Lock Stage 2 settings and separate fitting/reference/test areas | [Locked protocol](phase2/locked_plan.json), [fold fitting](phase2/experiment.py) | `results/phase2/fold_manifest.json`, `references.csv`, `tuning*` |
| 6 | Select budget, cost and cost-plus-capacity rules; transfer fixed cutoffs | [Decision rules](phase2/decisions.py), [experiment](phase2/run.py) | `candidates.csv`, `audits.csv`, `decisions.csv`, `evaluations.csv` |
| 7 | Compare loss, inspection demand and refitting; evaluate frozen prevalence scenarios | [Paired analysis](phase2/analysis.py), [decision accounting](phase2/supplement.py) | `comparisons.csv`, `capacity_tradeoffs.csv`, `refit_transfer.csv`, `prevalence_decision_value.csv` |
| 8 | Verify saved evidence and generate the papers | [Stage 1 checks](phase1/verify_results.py), [Stage 2 replay](phase2/verify.py), [equation checks](phase1/verify_formulae.py), [paper generators](reports/README.md) | [Final reports](reports/README.md), [verification guide](docs/REPRODUCING.md) |

The filenames in Steps 3–4 belong to `results/phase1/`; those in Steps 5–7 belong to `results/phase2/`. [Result-file guides](results/README.md) explain their roles.

## Repository structure

```text
phase1/              Stage 1 experiments, analysis, verification and paper generator
phase2/              Stage 2 locked protocol, decisions, transfer study and paper generator
reports/
  phase1/            Final Stage 1 Word, PDF and manuscript
  phase2/            Final Stage 2 Word, PDF, manuscript and report figures
results/
  phase1/            Stage 1 predictions, metrics, explanations and diagnostic figures
  phase2/            Stage 2 references, thresholds, decisions and verification evidence
src/                 Shared data, models, metrics, calibration and validation
tests/               Shared and Stage 1 behavioral tests; Stage 2 tests live in phase2/
data/                Data-source guide and ignored local download cache
requirements/        Separate baseline, research and reporting environments
docs/                Reproduction guide and dated audit history
```

## Reproduce or inspect

- [Complete execution sequence and environment requirements](docs/REPRODUCING.md)
- [Research overview](docs/PROJECT_OVERVIEW.md) · [Related work and contribution](docs/RELATED_WORK.md)
- [Quick verification of saved evidence](docs/QUICK_CHECK.md)
- [Stage 1 commands](phase1/README.md) · [Stage 2 protocol and commands](phase2/README.md)
- [Saved evidence](results/README.md) · [Final reports](reports/README.md)
- [Code and structure cleanup record](docs/audits/STRUCTURE_CLEANUP.json)
- [Current structure and verification review](docs/audits/STRUCTURE_REVIEW.md)
- [Research presentation release review](docs/audits/RESEARCH_PRESENTATION_REVIEW.md)

Run commands from the repository root. Stage 1 uses `python -m phase1.<command>`; Stage 2 uses `python -m phase2.<command>`. Older dated audit records retain the paths used in their original editions.

## Data and license

[Data provenance](data/README.md) identifies the official source and mirror. Raw data are downloaded to the ignored local cache. Code uses the [MIT license](LICENSE).
