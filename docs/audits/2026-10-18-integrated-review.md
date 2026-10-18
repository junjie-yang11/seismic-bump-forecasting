# Two-stage argument and integrated-report review

Baseline: `c18bd1019f250f8b9353f2ce5e281368d6634b43`, `main`, clean local worktree before work. Review and report preparation: 18–19 October 2026, Asia/Shanghai.

## Scope and method

This is an AI-assisted content, workflow and evidence review, not independent journal peer review. ARS-Codex supplies architecture/evidence-mapping and drafting guidance; Supervisor-Skills supplies the problem–challenge–method–contribution checks. Their guidance is adapted to an applied mining evaluation, without claiming a new algorithm, new benchmark or established priority. No additional reviewer/model panel or external-model review was run.

Inspected materials include both active stage manuscripts and their generators, the research overview, contribution statement, stage execution guides, decision and paired-analysis implementations, source audit and retained result schemas. The new overall-report verifier reconstructs the displayed main decision counts and loss, capacity excess and prevalence scenarios from aligned row decisions, in addition to checking source hashes, retained table values and document agreement. Its [actual execution record](../../reports/overall/verification.json) identifies scope, verifier and checked outputs. The [existing stage evidence](../../results/README.md) retains the separate model-replay provenance. This task does not repeat model fitting or estimate new uncertainty intervals.

## Findings and disposition

| Priority | Finding | Evidence and implication | Implemented response |
| --- | --- | --- | --- |
| High, presentation and inference | Two stage papers leave the common research question dispersed | Stage 1 concerns forecast comparisons; Stage 2 concerns historical rules. Reading both in full is needed to reconstruct their relation. | Add one overall paper with a common question, shared provenance, protocol comparison and integrated Discussion; retain technical reports for detail. |
| High, inference boundary | Shared and holdout records can be mistaken for independent validation | The 774-row holdout falls entirely within the 2,063 common test rows; the stages also share the same underlying records. | State overlap explicitly in the overall report and Stage 1 guide; do not sum cohort sizes. |
| High, comparator interpretation | Ratings-only can be mistaken for a direct expert/grade rule | Existing ablations refit a learner on the three rating fields jointly. They do not directly threshold each field. | Clarify the meaning in the overall report and stage guide. Keep direct-grade rules as unperformed proposed work. |
| High, uncertainty interpretation | Different paired intervals can be mistaken for uncertainty in the no-alarm comparison | Saved comparisons cover C-A, C-B, B-A and refitted-fixed; there is no ML-minus-no-alarm interval in those outputs. | Label the no-alarm result as a point comparison; identify the actual contrast of each displayed interval. |
| High, cross-stage interpretation | An integrated flow could imply identical scores or a calibration-to-policy pipeline | Stage 1 applies a reference cutoff after outer refitting; Stage 2 uses a fixed-model primary workflow with a separate refit control. Both alert workflows use raw scores. | Add the workflow table and a two-branch conceptual diagram. Explain that corrected LR probabilities do not feed Stage 2 rules. |
| Medium, metric interpretation | AP needs its cohort-specific prevalence reference | Common test prevalence is 88/2,063; the full-mirror prevalence is a different denominator. Existing paired protocol intervals are not AP-minus-prevalence intervals. | Compute a descriptive AP-minus-prevalence column in the new overall report; keep its interval label attached to the protocol difference. No new test or normalized gain is introduced. |
| Medium, economy and navigation | Repeated context, methods and conclusions increase reading effort | Both technical reports introduce the same dataset and related research. | Use the overall paper as the first README entry and deduplicate the integrated bibliography. Keep detailed reports as supporting routes. |
| Medium, report lifecycle | A rebuilt Word manuscript could coexist with an earlier PDF | Export is a separate command, so artifact existence alone does not establish a current export. | Revoke the prior success and remove the old integrated PDF when rebuilding; regression-test interrupted builds and failed verification. |
| Retained evidence limits | Explanation, calibration and quiet rules do not establish deployment benefit | SHAP/ablation contrasts, reference-dependent Brier skill, invariant infinite thresholds and hypothetical costs concern distinct evidence. | Preserve unfavorable and uncertain results. Keep measured detections/workload together and operational outcomes outside the claims. |

These are interpretation and presentation improvements. No model, feature set, fit/reference/test split, cost, budget or historical threshold is changed to produce the integrated report. Source experiment CSVs and the two technical report editions are retained.

## Four consistency checks

1. **Evaluation gaps to goal:** common-cohort interpretation, distinct predictive evidence and historical-rule transfer all support the common engineering question. Missing timestamps and actual intervention outcomes remain boundaries, not gaps claimed solved.
2. **Goal to challenges:** population comparability, evidence-layer interpretation and rule transfer follow directly from the question.
3. **Challenges to methods:** existing matched-cohort analysis, probability/ablation comparisons and frozen-rule evaluation supply the corresponding methods. The overall paper adds reporting and descriptive arithmetic, not another experiment.
4. **Methods to contributions:** each proposed contribution maps to an existing stage result and an integrated section. Direct-grade comparisons, new paired contrasts and lag-feature work are not claimed as delivered contributions.

The outline is structurally coherent under these boundaries. This does not certify novelty, journal acceptance, full model-selection uncertainty or field effectiveness.

## Verification and remaining work

Use the [reporting guide](../../reporting/README.md) for the generator, native Word export and independent check. Repository Quick Check includes the integrated-report table check in a disposable copy. PDF text checks and visual page inspection remain separate steps; the verification record explicitly says which computational scope was executed.

Final execution used Windows, Python 3.12.14, NumPy 2.3.5, pandas 3.0.1, SciPy 1.18.1 and XGBoost 3.1.3. All commands below ran against the isolated candidate; original experiment evidence was not overwritten.

| Command or inspection | Actual result and scope |
| --- | --- |
| `python -B -m reporting.overall` | Generated the integrated Word/Markdown, overview and input manifest; no fitting or threshold selection |
| `pwsh -NoProfile -ExecutionPolicy Bypass -File reporting/export_overall.ps1` | Fresh native Word PDF export, exit 0, 37.54 seconds |
| `python -B -m reporting.verify_overall --pdf` | 460 checks passed, including table agreement and contiguous GitHub Markdown, aligned row-level reconstruction, source/artifact hashes and PDF text; exit 0 |
| `python -B -m phase1.quick_check` | Exit 0, 54.06 seconds: 64 shared/report tests and 12 decision tests; Stage 1 8,169 checks, Stage 2 63,809, supplement 13,036, formulas 10,342, integrated report 353 standard-library checks; 190 local links and 274 Stage 2 Word items |
| PDF rendering and visual inspection | Final 14-page report; 10 tables, 3 figures. All pages reviewed, with unchanged pages compared to the previous inspected render. No clipped tables, overlapping text or orphan final page found |
| Baseline byte comparison | All 63 retained CSVs, original stage report files, shared model code and existing result records unchanged; all 64 Python files parsed successfully |

An earlier Quick Check attempt failed because the disposable copy omitted `CONTRIBUTIONS.md`, an integrated-report input. Copying and protecting that input resolved the failure. The bundled LibreOffice-based Word renderer was unavailable because its executable was missing; native Microsoft Word export followed by Poppler page rendering supplied the completed document checks. No Linux rerun, fresh official-source download, full model fitting/replay or new uncertainty experiment was performed for this reporting-only change. Existing full-replay certificates describe their retained source editions; they are not relabeled as new model runs.

The useful next empirical comparison remains historically selected direct rules for each hazard-grade field, accompanied by ML-minus-grade and ML-minus-no-alarm paired loss intervals. These require a separate recorded supplementary plan. Cross-row lag/rolling features need continuity evidence or a clearly labeled record-order sensitivity design. They are not silently appended to the locked Stage 2 study.
