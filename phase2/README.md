# Phase two: cost and capacity sensitive threshold transfer

This independent module implements the locked retrospective decision study. It
does not overwrite the first-stage code, report or results. The main model is
XGBoost; weighted LR and unweighted 60-tree bagged CART retain the existing
baseline designs. No additional model, feature selection or SHAP analysis is
introduced.

## Reproduce the experiment

From the repository root, use Python 3.12 with `requirements/requirements-research.txt`:

```powershell
python -B -m unittest phase2.tests -v
python -B -m phase2.run
python -B -m phase2.verify --replay
python -B -m phase2.supplement
python -B -m phase2.verify_supplement
```

The experiment uses the existing cached source data. `run` checks the immutable
`phase2/locked_plan.json` against `plan.py` before fitting. A protocol change must
be explicitly versioned and documented rather than silently applied. The
successful run records the data hash, source and imported dependency hashes,
environment and elapsed time. Interrupted or failed reruns invalidate the
previous verification flag; a report requires a newly verified completed run.
Imported XGBoost settings are checked against the locked grid and parameters.
The verifier refits all fixed/refitted model pairs and checks preserved
first-stage output hashes.

The initial model uses the first 80% of each historical prefix. Its final 20%
selects the warning rule. XGBoost tuning occurs inside the initial fitting area.
The refitted workflow includes that reference area, deliberately, but retains
the selected parameters and exactly the same numerical threshold. Both use raw
model scores. Test labels cannot change either workflow's fitted models or
historically selected decisions.

## Decision rules and conventions

Current computation belongs to this stage directory: `run.py` fits the locked experiment, `supplement.py` accounts for its decision value, `verify.py` and `verify_supplement.py` independently check it, `report.py` builds the paper, `verify_report.py` checks the report, and `update_readme.py` presents the retained pooled counts on the homepage. Historical command aliases and execution records remain in `docs/audits/`.

- A maximizes reference alerts within `floor(budget * reference_n)`.
- B minimizes `cost * FN + FP`.
- C minimizes the same loss subject to the reference capacity.
- Tied scores remain whole groups; alarms use `score >= threshold`.
- Empty and full alert sets use `+inf` and `-inf`; other cutoffs are the minimum
  included reference score. Equal-loss decisions select fewer alerts.
- B/C with no positive reference labels select no alarms. Zero slots force A/C
  to no alarms. Insufficient fitting classes raise an explicit error.
- Retrospective batch Top-k uses complete test scores, never test labels, and
  may underfill capacity when a boundary tie cannot fit. It is a batch reference,
  not a real-time rule, oracle or performance upper bound.
- A's scalar reference loss, cost-specific capacity binding and loss gap are
  undefined. Candidate loss columns retain all four cost ratios. C's binding
  indicator means the unconstrained B decision exceeds reference capacity.
- The second-best gap uses the second distinct feasible decision; it is zero
  when optimal decisions tie. It is undefined if only one decision is feasible.
- Zero-alert precision is reported as 0; recall/FNR are undefined if there are
  no positives, and FPR is undefined if there are no negatives. Undefined CSV
  fields are empty; they are not placeholder measurements.
- Pooled capacity slots and excess sum phase-specific values. Spare capacity
  in one phase never offsets excess in another.

## Evidence in `results/phase2`

### Decision assumptions

An alert flags one dataset shift record; one flagged record represents one assumed inspection slot. TP is an alerted hazardous shift, FP an alerted non-hazardous shift and FN an unalerted hazardous shift. These counts describe label coverage. Actual inspection execution and accident prevention are not observed.

Loss `r * FN + FP` includes the assumed missed-shift and false-alert penalties only. It contains no separate true-positive inspection cost, delay penalty, accident-severity estimate or monetary valuation. Capacity slots are `floor(budget * n)` in each reference/test block. All alerts, including excess alerts, enter confusion counts and loss; the study records excess demand without simulating truncation, queuing, dispatch or an additional excess penalty. Pooled counts and excess sum the four blocks, with no cross-block capacity offset. [Report Table 2a](../reports/phase2/phase2_threshold_transfer_report.md) states these assumptions together.

The [release replay audit](../docs/audits/2026-10-07-stable-release/check_threshold_replay.py) separates numeric score comparisons from exact frozen-threshold decisions. [Environment support](../docs/REPRODUCING.md#environments) identifies the tested Windows setup and the unverified Linux/macOS scope.

| File | Meaning |
| --- | --- |
| `predictions.csv` | Label and fixed/refitted score for every test row |
| `references.csv` | Historical policy-reference scores and labels |
| `fold_manifest.json` | Exact fitting, policy, tuning and test row IDs |
| `tuning.csv`, `tuning_predictions.csv` | Training-only candidate objectives and internal predictions |
| `candidates.csv` | Every whole-tie reference decision, cutoff, counts and all four costs |
| `audits.csv` | Chosen rules, reference counts, ties, gap, feasibility and binding |
| `decisions.csv` | Wide per-row warning decisions for both workflows |
| `evaluations.csv` | All 1,680 phase/holdout evaluations, including no-alarm and Top-k |
| `pooled_evaluations.csv` | 336 supplementary four-phase pooled evaluations |
| `comparisons.csv` | 1,980 paired phase/pooled contrasts with loss, workload, excess and intervals |
| `bootstrap_replicates.npz` | Five arrays of 2,000 × 396 paired loss samples, indexed by comparison ID |
| `analysis_manifest.json` | Comparison ordering and bootstrap settings |
| `prevalence_scenarios.csv` | 8,064 frozen-rule expectations, separate from observed losses |
| `run_manifest.json`, `verification.json` | Execution provenance and independent checks |
| `../../reports/phase2/` | Independent manuscript, Word, PDF, figures and report provenance |
| `decision_value.csv`, `decision_value_pooled.csv` | Complete evaluations with explicit no-alarm loss and relative-loss fields |
| `threshold_explanations.csv`, `threshold_audit_enriched.csv` | Reference-only no-alarm causes, capacity flags, threshold types and normalized next-decision margins |
| `refit_transfer.csv`, `capacity_tradeoffs.csv` | All A/B/C fixed/refitted contrasts and matched C-A loss, detection and workload contrasts |
| `prevalence_decision_value.csv` | Frozen prior-shift relative loss and expected workload, separate from observed results |
| `supplement_manifest.json`, `supplement_verification.json` | Original-input hashes and independent descriptive-accounting checks |

`fold` and `row` are zero-based **mirror** indices. Displayed report phases are
`fold + 1`; pooled supplementary rows have `fold = -1`. The 774-row previously
viewed holdout is descriptive and overlaps the primary test cohort; it is not
additional independent evidence. First-stage `results/phase1/source_row_mapping.csv`
maps mirror rows to the official source.

## Conditional intervals and scenarios

The prespecified 2,000 paired moving-block resamples use length 32 within each
phase. They preserve phase sizes, never wrap or cross boundaries, and hold
models and policies fixed. Intervals do not include fitting, tuning or threshold
selection uncertainty. The verifier independently reconstructs all 2,000 samples
in every phase and validates every saved replicate and interval quantile.

Prevalence scenarios (2%, 5%, 10%, 15%) retain empirical FNR/FPR and frozen
rules. Only class proportions change. Expected loss and expected workload are
not actual test outcomes or estimated probabilities of future capacity excess.
Costs are relative hypothetical penalties, not money or avoided accidents.

## Regenerate the independent academic report

Use a document environment with `requirements/requirements-report.txt` **separate from
the experimental environment**:

```powershell
python -B -m phase2.report
pwsh -NoProfile -ExecutionPolicy Bypass -File phase2/export_report.ps1
```

Reporting requires completed `verify --replay` evidence; the builder validates
verified CSVs, manifests, bootstrap arrays and experimental source hashes,
and reads saved data only. PDF export uses installed
Microsoft Word invisibly on Windows through PowerShell 7. Inspect the rendered document after any
layout change. The full combination tables are the electronic appendix above;
the report displays all cost/budget cells for the main comparisons and keeps
pooled and previously viewed holdout results supplementary.

## Descriptive decision accounting

The supplementary module derives its outputs from verified, frozen evidence;
it neither fits a model nor reselects a threshold. Negative
`delta_loss_vs_no_alarm_100 = 100 * (FP - cost * TP) / N` means lower loss than
no alarms under the specified hypothetical cost. Original evaluations already
contain the equivalent `loss_delta_no_alarm100`; both fields are cross-checked.

No-alarm reasons use historical reference outcomes: no reference positives,
unconstrained cost choice, or a capacity-induced change from an alarming B rule.
They describe selected rules, not zero test alarms from a finite cutoff.
Threshold groups are determined before testing. A +infinity rule stays empty,
and a -infinity rule stays full, under refitting. Finite groups retain every
historically finite rule, including settings with zero observed change.

The normalized next-decision margin uses a second distinct feasible alert set;
it is undefined if none exists. The capacity flag states whether the
unconstrained cost optimum exceeds reference capacity, independently of C's
capacity utilization. The prior-shift file retains absolute expected loss,
relative expected loss and expected alert rate; none is a probability of future
capacity excess. These are post hoc descriptive extensions, not changes to the
locked protocol or a selection of a preferred strategy from test outcomes.

## Project navigation

[Final paper](../reports/phase2/phase2_threshold_transfer_report.pdf) · [Word](../reports/phase2/phase2_threshold_transfer_report.docx) · [Result-file guide](../results/phase2/README.md) · [Complete execution sequence](../docs/REPRODUCING.md) · [Stage 1](../phase1/README.md).
