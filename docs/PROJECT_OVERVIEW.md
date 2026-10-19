# Research overview

This overview introduces the research questions, main findings, contribution and study boundaries. The [integrated report](../reports/overall/integrated_research_report.pdf) develops the complete argument; the stage-specific reports below provide supporting technical detail. The two stages share evaluated records; their sample sizes do not represent independent validation cohorts.

## The engineering question

What evidence supports using mine-monitoring forecasts to select later shifts for inspection? This project connects two retrospective studies. Stage 1 separates ranking performance, probability accuracy and fitted-model feature use on comparable test records. Stage 2 links historical threshold choices to later loss, hazardous-shift coverage and inspection demand under stated costs and capacity. The engineering objective is to make these decisions auditable: each claim has a defined comparator, a saved calculation and a stated scope of application.

| Study | Question | Main evidence | Paper |
| --- | --- | --- | --- |
| Stage 1 | How do a common test cohort, probability assessment and feature comparisons change the interpretation of seismic forecasts? | Paired protocol contrasts, calibration references, engineering ablations and TreeSHAP | [PDF](../reports/phase1/technical_report.pdf) · [Word](../reports/phase1/technical_report.docx) |
| Stage 2 | What happens when historical thresholds transfer under assumed costs and inspection capacity? | Loss relative to no alarms, historical selection reasons, future capacity excess and fixed/refitted contrasts | [PDF](../reports/phase2/phase2_threshold_transfer_report.pdf) · [Word](../reports/phase2/phase2_threshold_transfer_report.docx) |

## Data and study design

The audited UCI Seismic Bumps mirror contains **2,578 shift records and 170 hazardous-shift labels**. The official source has 2,584 rows; the mirror removes six exact duplicate occurrences and preserves first-occurrence order. A positive target means a high-energy seismic bump in the next shift. The label does not establish an accident or the effectiveness of an intervention. [Source audit and row mapping](../data/README.md).

The retained design has 17 monitoring and shift columns. LR, unweighted bagged CART and training-tuned XGBoost supply three forecast models. Four successive record-order test blocks cover **2,063 rows and 88 positives**. Recorded order is a time proxy because timestamps and working-face identifiers are absent. The already viewed holdout remains supplementary.

Stage 1 compares random and record-order predictions on the same test rows, evaluates probability correction and compares fitted-model explanations with refitted feature ablations. Stage 2 retains the full feature design, separates historical fitting and policy-reference areas, then transfers fixed cutoffs. It compares budget rule A, cost rule B and cost-plus-capacity rule C under four hypothetical cost ratios and four historical budgets. A refitted model uses the same selected parameters and numerical cutoff. Test outcomes evaluate the rules; they do not select them.

## Findings and their evidence

**Comparable test records change the apparent validation gap.** Matching rows reduces the original AP gap by 89.7% for LR and 86.9% for CART. Residual random-minus-record-order AP differences are 0.0114 and 0.0188. This is a cohort-sensitive recalculation, not a causal decomposition of leakage or drift. Training-local LR correction improves ECE from 0.2904 to 0.0271; its Brier skill depends on the stated probability reference. [Matched-cohort results](../results/phase1/shared_test_comparison.csv) · [Gap calculation](../results/phase1/gap_attenuation.csv) · [Probability references](../results/phase1/probability_reference_comparison.csv).

**Historical cost optimization does not establish later decision value.** At `r=10`, pooled fixed XGBoost C has point loss differences of **0.00 to +0.82 units per 100 shifts relative to no alarms**. The point estimates show no improvement, while the nonzero pooled conditional intervals still include improvement and increase. Phase 1 C at 5% and 10% has no detections and entirely positive loss-difference intervals; pooling does not describe every phase. The 40 historical no-alarm C selections comprise 28 unconstrained cost choices and 12 capacity-induced changes. [Point comparisons](../results/phase2/decision_value_pooled.csv) · [Intervals](../results/phase2/comparators/intervals.csv) · [Historical reasons](../results/phase2/threshold_explanations.csv).

**Capacity and the meaning of a cutoff can change after transfer.** All historical A choices satisfy capacity, yet later capacity is exceeded in 13/16 phase–budget settings. C exceeds it in 2/64 phase–budget–cost settings; these denominators differ and are not independent, directly comparable violation rates. Refitting can change alerts at a finite numerical cutoff. A no-alarm cutoff remains empty by definition. Loss, detections and workload must be read together. [Matched capacity and detection results](../results/phase2/capacity_tradeoffs.csv) · [Refitting results](../results/phase2/refit_transfer.csv).

The descriptive extension separates historical selection cost from evaluation cost. [Frozen-policy cost boundaries](../results/phase2/frozen_policy_cost_boundaries.csv) report the FP/TP equality point for every retained A/B/C rule, with explicit no-detection cases. [Prevalence scenarios](../results/phase2/prevalence_decision_value.csv) pair expected precision with loss and workload while retaining the historical rules. These calculations explain conditions for decision value without selecting another strategy from test outcomes.

## Project contribution

The [separately specified frozen-policy supplement](../phase2/comparators/README.md) adds direct hazard-grade rules and paired policy-minus-no-alarm/ML-minus-grade loss intervals. At r=10, nonzero pooled C intervals span zero. The three grade B rules produce exactly the same decisions, all alarms in phase 1 and none later. XGBoost B has 101 fewer false alerts and one fewer detection than that common rule; its no-alarm interval still crosses zero. Full phase/cost combinations remain in the [appendix](../reports/overall/comparator_appendix.md).

The [separate ranking pilot](../phase2/ranking/README.md) tests full-score ranking within seismic grades at identical inspection allocations. It is an exploratory batch task using saved scores, not a new fitted model or real dispatch study. Its results remain in a [short report](../reports/ranking/within_grade_ranking_pilot.pdf); they do not change the two-stage study's main question.

The work contributed in this repository is the data-source audit, the implementation of comparable-cohort evaluation, training-local probability and threshold handling, the engineering feature comparisons, and the reproducible accounting of loss, capacity and refitting. Saved scores, candidate decisions and verification through separate calculation paths connect reported results to their underlying computations. This supplies a reproducible evaluation workflow for examining which forecast properties and historical decision rules carry into later records. Calibration gains, uncertain feature-removal contrasts and transferred decision tradeoffs each inform that assessment. The [verification guide](QUICK_CHECK.md#verification-scope) distinguishes source/file checks, separate-path recalculation and model refitting/replay; these project-run checks do not constitute external third-party replication.

LR, CART, XGBoost, TreeSHAP, cost-sensitive loss and block resampling are established methods. The contribution is their implementation and joint empirical evaluation in this mining case. [Related-work comparison](RELATED_WORK.md) separates method origins from the project's findings.

The author set the research scope and review priorities and coordinated protocol refinement, reproducibility checks and report revisions. ChatGPT and Codex provided substantial implementation, execution and writing support. [Author contributions and AI assistance](../CONTRIBUTIONS.md) separates these roles and links concrete project decisions to their evidence.

## Study boundaries and next questions

The results apply to the audited public cohort and the specified retrospective workflows. Relative costs and inspection slots are assumptions, not measured economic loss or avoided accidents. Current intervals condition on saved predictions or fitted rules. Frozen prevalence scenarios hold class-conditional rates constant and do not identify the cause of observed changes.

Two follow-up questions require further evidence: how much uncertainty arises from the complete fitting and threshold-selection process, and whether a preregistered rule transfers to an independent, timestamped working face with recorded inspection outcomes. These are future studies; this release adds no model or policy selection based on test results.

## Inspect or reproduce

[Quick verification](QUICK_CHECK.md) checks published evidence in a disposable copy. [Complete reproduction](REPRODUCING.md) fits the models and recreates the analyses. The [workflow and supplements](../README.md#follow-the-research-workflow) map each question and calculation to code and saved outputs. The Stage 2 PDF is the locked-study technical edition; the integrated report and comparison appendix contain the latest complete decision analysis.
