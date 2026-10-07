# Stable release review

This edition completes the report-check failure lifecycle, clarifies decision assumptions and presents pooled decision value on the homepage. The locked models, features, splits, costs, budgets and rules are unchanged. Numerical results and research conclusions are unchanged relative to the reviewed audit branch `3253818`.

## Repository and scope

The original checkout was clean on `main` at `8aa4230`; the review started from `3253818` on `release/stable-20261007`. [Initial state](initial-state.json) records the repository and branch. Work ran in an independent saved-evidence copy. The [earlier full review](../2026-10-07-full-review/REVIEW.md) records complete fresh Stage 1/2 experiments for its edition.

This round reran behavior tests, XGBoost/TreeSHAP refits, all Stage 2 model-pair replay, decision accounting and formulas. It did not repeat every baseline LR/CART seed or engineering-feature fit: their implementation and saved numerical evidence were retained. The final Stage 1 manuscript is unchanged and still agrees with its current generator and Word document.

## Findings and repairs

1. **Report-check failure could retain an older success.** The current checker now writes a running non-success before reading inputs and persists the actual exception on failure. A malformed current manifest after a real prior success produced a [failed certificate](failed-report-check.json) with `passed:false`, `status:failed` and `JSONDecodeError`. The unit regression also exercises this case. No failed check was converted into a success.
2. **Current checking code belonged to a dated audit folder.** Its implementation is now [phase2/verify_report.py](../../../phase2/verify_report.py). The dated command remains a thin compatibility adapter. The two-stage directory layout and old audit records remain intact.
3. **Decision counts needed an explicit operational definition.** Report Table 2a defines alert objects, hypothetical slots, confusion counts, included loss terms and excess demand. Every alert remains in evaluation; dispatch, queues and accident prevention are not evaluated. Figure 3 now describes inspection demand rather than completed inspections.
4. **The homepage needed a compact traceable comparison.** [The updater](../../../phase2/update_readme.py) reads saved pooled fixed-XGBoost C counts at r=10 and checks `100(FP − 10TP)/N`. It generates all four budgets, including **5% = +0.68**, alongside TP, FN and alerts. Negative values favor the policy over no alarms.
5. **Cleanup candidates needed actual use checks.** [CLEANUP.json](CLEANUP.json) lists removed bindings, an unused import and duplicate reads, the verifier reclassification and retained candidates. Historical logs with equal stdout represent distinct recorded runs. No experimental resource, published result, model, standalone check or working CLI was deleted.

## Executed checks

| Check | Actual result | Evidence |
| --- | --- | --- |
| Behavioral tests | 48 shared/repository + 12 Stage 2 tests; no skips | [Execution](execution.json) and logs |
| Stage 1 XGBoost/TreeSHAP replay | 7,460 checks | [Replay log](logs/02-phase1.verify_research.log) |
| Stage 2 model and bootstrap replay | 63,854 checks; 15 fixed/refitted model pairs | [Replay log](logs/03-phase2.verify.log) |
| Supplementary accounting | 10,902 checks | [Accounting log](logs/04-phase2.verify_supplement.log) |
| Formula reconstruction | 8,220 checks | [Formula log](logs/05-phase1.verify_formulae.log) |
| Separate scores and frozen decisions | 45 score arrays passed; 720 exact Boolean comparisons; 0 changed alerts | [Replay and complete build/dependencies](threshold-replay.json) |
| Saved numeric evidence | All 62 CSVs byte-identical to the review base | [Evidence](EVIDENCE.json) |
| Final Stage 2 paper | 605 checks; 18 tables, 3 figures, 14 pages | [Report certificate](../../../reports/phase2/report_verification.json) |
| First final-pipeline Quick Check | 147 links and 253 Word items; all component checks passed | [Quick log](logs/11-phase1.quick_check.log) |
| Final-artifact Quick Check | 151 links and 253 Word items; all component checks passed | [Final Quick log](final-logs/final-quick-check.log) |
| Final archive/navigation checks | 151 active links, 19 release links and 27 recorded log references passed | [Delivery check](FINAL_CHECK.json) |
| Final presentation regeneration | Word, Markdown and PDF regenerated; table checks and rendering passed | [Final execution](final-execution.json) |
| Visual review | All 14 pages inspected; revised pages 3/8 inspected again | [Visual record](VISUAL_REVIEW.json) |

The largest observed numeric score difference was 1.11e-16. Scores used the existing `rtol=1e-9, atol=1e-10` criterion; transferred alerts required exact equality. No tolerance or threshold was changed. The homepage numbers come from stored counts, not hand-entered estimates. Empty metric values remain defined missing quantities; infinity remains a decision sentinel. Synthetic regression fixtures are not research observations.

## Environment, failures and remaining scope

The exercised research setup was Windows x64, Python 3.12.14, NumPy 2.3.5, pandas 3.0.1, SciPy 1.18.1 and XGBoost 3.1.3. The replay record includes full installed packages, numerical backends, XGBoost build information and locked settings. The XGBoost package includes CUDA support; the locked experiment uses histogram trees with two CPU threads.

The Linux feedback originated from a separate AI inspection environment; its logs and build details are not in this checkout. This local WSL query failed because WSL is not installed. Linux/macOS replay is therefore unverified here and is not a release certification. Future cross-environment diagnosis should retain that environment's actual failed/successful record and compare inputs, builds, scores and exact frozen alerts, without selecting replacement cutoffs.

The [first execution attempt](attempts/first/execution.json) stopped when the installed research interpreter could not write a diagnostic output across to the C workspace. Its logs were retained; routing that diagnostic output to the isolated execution directory allowed the actual rerun to finish. The bundled LibreOffice document renderer was unavailable. Actual PowerShell 7/Microsoft Word export and Poppler rendering succeeded; [additional attempts](additional-execution.json) retain both the renderer failure and expected corrupt-input failure. A preliminary test outside the execution copy also encountered sandbox temporary-directory access restrictions; tests in the declared execution directory passed without skips.

The final-artifact Quick Check passed before audit-directory shortening. A subsequent [navigation check](FAILED_NAVIGATION_CHECK.json) detected a 262-character archived-log path in the deep Windows review workspace. The archive was shortened and navigation/log references were actually checked again. Two permission-review deadlines prevented another redundant Quick Check invocation after this archive-only change; the delivery record references the actual successful check and separately verifies source and report identity. The failed navigation record was retained rather than rewritten as a success.

`CONTRIBUTIONS.md` and the 2017/2023 comparison in `docs/RELATED_WORK.md` are byte-preserved. This edition used paper-review and academic-writing-skills for evidence/assumption alignment, anti-defensive-writing for focused prose, and documents/pdf skills for generation and visual checking. Writing skills did not replace computational checks. No new literature search, model, strategy selection, field validation or stability experiment was added.
