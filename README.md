# Seismic Hazard Forecasting and Warning Decisions

**A retrospective mining study of how forecast evidence translates into warning loss, detections and inspection workload.**

The audited UCI Seismic Bumps mirror contains 2,578 shift records and 170 hazardous-shift labels. Stage 1 evaluates forecasts; Stage 2 examines how historical warning thresholds transfer under assumed costs and inspection capacity.

## Start here

| Reading level | Entry | What it provides |
| --- | --- | --- |
| Quick introduction | [Research overview](docs/PROJECT_OVERVIEW.md) | Questions, findings, contribution and study boundaries |
| Complete argument | [Integrated paper: PDF](reports/overall/integrated_research_report.pdf) · [Word](reports/overall/integrated_research_report.docx) · [Online](reports/overall/integrated_research_report.md) | Forecast evaluation, threshold transfer and the matched-information core finding |
| Methods, code and evidence | [Project directory map](docs/PROJECT_STRUCTURE.md) · [Report catalogue](reports/README.md) | Stage-specific technical reports, separate supplements and the code behind each step |

The integrated paper contains the latest combined argument and added grade/no-alarm comparisons. The catalogue retains the original stage reports, the separate ranking pilot and the matched-information supplement. These studies use overlapping records and do not add independent validation cohorts.

## Three findings

1. **Who is tested changes the apparent validation gap.** On common test records, the original random-versus-record-order AP gap shrinks by 89.7% for LR, 86.9% for CART and 89.4% for XGBoost; residual AP differences are 0.0114, 0.0188 and 0.0133. This recalculation shows cohort sensitivity, not a causal decomposition of leakage or drift. [Matched results](results/phase1/shared_test_comparison.csv) · [Gap calculation](results/phase1/gap_attenuation_all_models.csv).
2. **Pooled loss point estimates and interval evidence answer different questions.** At `r=10`, pooled fixed XGBoost cost-plus-capacity rule C has point differences of **0.00 to +0.82 relative loss units per 100 shifts** versus no alarms. The nonzero pooled conditional intervals still include loss improvement and increase. C in record block 1 at 5% and 10% has no detections and entirely positive loss-difference intervals. These findings apply to the assumed cost and observed records. [Point comparisons](results/phase2/decision_value_pooled.csv) · [Phase and pooled intervals](results/phase2/comparators/intervals.csv).
3. **Historical capacity feasibility does not guarantee future feasibility.** Budget rule A exceeds later capacity in **13/16 record-block–budget settings**; C does so in **2/64 record-block–budget–cost settings**. These are different, dependent setting counts, not directly comparable independent violation rates. Refitting can also change alerts at the same finite numerical cutoff. [Capacity and detection](results/phase2/capacity_tradeoffs.csv) · [Refitting](results/phase2/refit_transfer.csv).

## Read the decision tradeoff

<!-- BEGIN GENERATED DECISION TABLE -->
**Fixed XGBoost · rule C · r=10 · four later blocks pooled (2,063 shifts; 88 hazardous labels).**

| Historical budget | Δ loss / 100 vs no alarms | TP | FN | Alerts |
| --- | --- | --- | --- | --- |
| 1% | 0.00 | 0 | 88 | 0 |
| 5% | +0.68 | 1 | 87 | 25 |
| 10% | +0.82 | 1 | 87 | 28 |
| 20% | +0.58 | 2 | 86 | 34 |

**Negative differences mean lower assumed loss; positive differences mean higher loss.** False-alert cost is 1 and missed hazardous-shift cost is 10. Budgets constrain historical selection, not later workload. TP counts hazardous shifts flagged, not inspections completed or accidents prevented.

Generated from [saved pooled results](results/phase2/decision_value_pooled.csv) by [the table updater](phase2/update_readme.py); Δ loss is independently reconstructed as `100(FP − 10TP)/N`.
<!-- END GENERATED DECISION TABLE -->

[Detailed decision comparisons](reports/comparators/comparator_appendix.md) retain all specified costs, budgets and record blocks. The [research overview](docs/PROJECT_OVERVIEW.md#findings-and-their-evidence) explains the grade-rule, refitting and frozen-scenario results.

## Contribution and study scope

The project links audited data transformation, comparable-cohort evaluation, historical threshold selection and joint loss/detection/workload accounting. [Author contributions and AI assistance](CONTRIBUTIONS.md) · [Related work and method origins](docs/RELATED_WORK.md).

Recorded order is a temporal proxy, costs are hypothetical, and the labels describe hazardous shifts. The results do not demonstrate prevented accidents or an operationally optimal warning system. [Study boundaries and next questions](docs/PROJECT_OVERVIEW.md#study-boundaries-and-next-questions).

## Quick verification

With Python 3.12 and the [research dependencies](requirements/requirements-research.txt), run from the repository root:

```text
python -B -m phase1.quick_check
```

Quick Check recalculates saved evidence in a disposable copy and preserves published records. It is separate from full model refitting and external third-party replication. [Scope and setup](docs/QUICK_CHECK.md) · [Complete reproduction](docs/REPRODUCING.md).

## Follow the research workflow

The [step-by-step directory map](docs/PROJECT_STRUCTURE.md#research-workflow) connects each calculation to its code and saved outputs. Start with the [Stage 1 guide](phase1/README.md) for forecast evaluation or the [Stage 2 guide](phase2/README.md) for the locked decision experiment and separately specified supplements.

## Data and license

[Data provenance](data/README.md) identifies the official source and mirror. Raw data are downloaded to the ignored local cache. Code uses the [MIT license](LICENSE).
