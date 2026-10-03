# Seismic Hazard Forecasting and Warning Decisions

**A two-stage mining study: evaluate seismic hazard predictions, then examine how historical warning rules transfer under cost and inspection-capacity constraints.**

The project uses the UCI Seismic Bumps dataset: shift-level monitoring records from underground coal mining. It connects model evaluation to a practical decision question—how many hazardous shifts are detected, how many are missed, and how much inspection work a warning rule creates.

## Start with the papers

| Stage | Research question | Paper | Editable version | Manuscript |
| --- | --- | --- | --- | --- |
| **1 · Prediction evaluation** | How do validation cohorts, probability calibration and model explanations affect the interpretation of forecast performance? | [PDF](report/technical_report.pdf) | [Word](report/technical_report.docx) | [Read online](report/technical_note.md) |
| **2 · Warning decisions** | How do historically selected thresholds transfer when missed-event costs and inspection capacity differ? | [PDF](results/phase2/report/phase2_threshold_transfer_report.pdf) | [Word](results/phase2/report/phase2_threshold_transfer_report.docx) | [Read online](results/phase2/report/phase2_threshold_transfer_report.md) |

Read Stage 1 for the forecasting evidence and Stage 2 for the decision analysis. Each paper has its own methods, results and conclusions.

## What the studies show

**Stage 1 — evaluation changes the interpretation of apparent performance gaps.** Matching the test records reduces the apparent random-versus-record-order AP gap by 89.7% for LR and 86.9% for CART. On the shared cohort, the differences are 0.0114 and 0.0188, respectively. This quantifies sensitivity to cohort composition; it does not isolate a causal effect of leakage or drift. Fold-local LR prior correction improves calibration, while warning performance remains limited under the tested rules.

**Stage 2 — historical capacity feasibility does not fix subsequent workload.** For fixed XGBoost, budget thresholds exceed later-block capacity in 13 of 16 phase–budget settings. Cost-plus-capacity rules produce no alarms in 40 of 64 phase–budget–cost settings and exceed capacity in two. Their loss tradeoffs depend on the record stage and assumed missed-event cost. Refitting can change decisions even when the numerical threshold is held fixed.

Both studies use the audited 2,578-row mirror of the official 2,584-row dataset. Recorded row order is a temporal proxy; the second stage is retrospective, uses hypothetical relative costs, and evaluates warning decisions rather than demonstrated accident prevention.

## Repository map

```text
report/             Stage 1 paper in PDF, Word and Markdown
phase2/             Stage 2 protocol, experiment, decision rules and tests
results/            Saved predictions, metrics, figures and verification evidence
  phase2/           Stage 2 results and independent paper
scripts/            Stage 1 experiment, analysis, verification and report commands
src/                Shared data, model, metric and evaluation implementations
tests/              Shared and Stage 1 behavioral tests
requirements/       Separate baseline, research and reporting dependencies
data/               Data-source documentation and local download cache
docs/               Reproduction guide, project navigation and audit records
```

## Explore or reproduce

- **Understand the evidence:** [results guide](results/README.md).
- **Reproduce Stage 1:** [environment and execution sequence](docs/REPRODUCING.md).
- **Reproduce Stage 2:** [locked protocol and commands](phase2/README.md).
- **Find a script:** [command guide](scripts/README.md).
- **Inspect verification:** [Stage 1 review](docs/audits/PROJECT_REVIEW.md) and [Stage 2 review](results/phase2/PROJECT_REVIEW.md).

Run commands from the repository root. Stage 1 entry points use `python -m scripts.<command>`; Stage 2 uses `python -m phase2.<command>`. The reproduction guides specify the environment and prerequisites for each step. Earlier paper and audit records may use the script basenames; their current locations are under `scripts/`.

## Data and license

See [data provenance](data/README.md) and the paper references for source attribution. Source data are downloaded into the local cache and remain uncommitted. Code is released under the [MIT license](LICENSE).
