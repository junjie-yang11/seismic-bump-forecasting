# Complete code, workflow and reproduction review

The review started from `main` at `8aa4230e3c8b491b9bcc3e38742e11bb8cce258b` in [junjie-yang11/seismic-bump-forecasting](https://github.com/junjie-yang11/seismic-bump-forecasting). The user checkout was clean. Changes belong to the independent branch `audit/full-review-20261007`; the original checkout and all 235 initially tracked files remain unchanged. [Initial state](initial_state.json) and [preservation check](preservation.json) retain the evidence.

## Scope and design

All 48 original Python sources were inventoried; the final 50 core and test sources were parsed and reviewed with their entry commands, dependencies, two PowerShell exporters, requirements, report generators and current file guides. Two additional independent release/report tools are retained here. The review covers source-to-mirror mapping, model inputs and indices, training/reference/test boundaries, calibration, tied-score ranking, thresholds, extreme rules, paired blocks, saved model replay, result-driven reports and current links. [Current source inventory](current-source-inventory.json) identifies the inspected source versions.

The existing questions, feature sets, splits, model settings, seeds, costs, budgets and locked Stage 2 plan were retained. Stage 1 random validation deliberately differs from the record-order protocol; it is not treated as prospective training. Stage 1 uses reference cutoffs on refitted models. Stage 2 separates fixed-model transfer from the same-cutoff refitted comparison. Their threshold boundary conventions also differ as documented. No test outcome was used to replace a model, parameter, feature set or policy.

## Findings and fixes

| Priority | Finding | Fix and evidence |
| --- | --- | --- |
| P1 | A failed main or supplementary verification could leave a previous successful certificate on disk. | Both verifiers now invalidate the prior certificate before checking and record an actual exception as failure. The two regression tests failed before repair and pass after repair: [before](logs/lifecycle-before-fix.log), [after](logs/lifecycle-after-fix.log). |
| P1 | The Stage 2 report checked evidence hashes but did not require the current main verifier identity. | Added the verifier SHA-256 gate. An actual report invocation rejected the old certificate with `Main verifier changed`; [execution](additional-execution.json), [log](logs/stale-certificate-refusal.log). New full replay and report generation passed. |
| P2 | Malformed random fold assignments could reach fitting or silently cover fewer rows. | `cross_validate` now rejects wrong shape, noninteger or negative IDs and fewer than two folds before invoking a model. [Before](logs/folds-before-fix.log), [after](logs/folds-after-fix.log). Valid published folds reproduce their results. |
| P3 | Three intermediate baseline prose rates were literals rather than values read from their computed counts. The literals were correct for their own policy. | Bind that sentence to the measured operating points; add an independent count-based text check. This is a synchronization fix, not a correction of published values. The baseline policy and the extended 10% policy remain distinct. |
| P3 | One obsolete source-mapping path, stale test-module count and ignore-file comments reduced navigation clarity. An unused CSV read and two local bindings remained. | Corrected guides/comments and removed only those unused operations. [Cleanup decisions](cleanup-candidates.json) explain retained public APIs, baseline generators, historical evidence and independent checks. No file or function was deleted or moved. |
| P3 | The environment recorder duplicated Windows line endings, named an obsolete experiment command, and did not distinguish nonzero `pip freeze` exit from an empty successful result. | Normalize package lines and output line endings, report the current module entry and retain an explicit failed-freeze message. Regenerate the actual environment and rerun Stage 2 so its snapshot records the new environment without manual hash changes. |

The Stage 2 future-label and reference-label behavior checks now cover LR, CART and XGBoost. Changing test labels leaves tuning, scores, historical thresholds and fixed/refitted alert decisions unchanged. Changing policy-reference labels leaves fixed fitting, tuning and fixed/reference scores unchanged; the refitted model deliberately may use those historical labels.

## Actual execution

The fresh reproduction started without saved numeric results, models, bootstrap arrays or report files. It used an independent ignored directory and genuine cached raw inputs. A separate fresh download from both UCI and the mirror returned HTTP 200 and exactly matched the audited input hashes: [download record](fresh-source-download.json). The actual ARFF audit reconstructed the 2,584-to-2,578 order-preserving first-occurrence mapping. The `nbumps` audit confirms 2,576 equal band sums and two different rows, 435 and 436; the paper does not claim exact equality. [Data consistency](data-consistency.json) distinguishes settings, undefined values and test fixtures from observed results.

| Executed step | Exit/status | Evidence |
| --- | --- | --- |
| Baseline environment record and original-to-mirror source audit | 0 | [Fresh Stage 1 execution](full-execution.json) |
| Stage 1 LR/CART fit, feature study and XGBoost extension | 0; 329.43, 83.85 and 13.66 seconds | Same execution record and logs |
| Stage 1 XGBoost and native contribution replay | 0; 7,460 checks | Same execution record |
| Final shared tests and decision tests | 0; 46 + 12 tests, no skipped tests | [Final execution](final-execution.json) |
| Final Stage 2 fitting and complete fixed/refitted replay | 0; 15 model pairs, 63,854 checks; actual durations in the linked record | Same final record |
| Supplement generation and independent checking | 0; 10,902 checks | Same final record |
| Independent cross-stage formulas | 0; 8,220 checks | Same final record |
| Stage 1 results and Word agreement | 0; 8,169 checks | Same final record |
| Both Markdown/Word papers and both actual Word PDF exports | Completed; 15 and 13 PDF pages | [Stage 1 retry completion](word-export-retry.json), [report comparison](numerical-comparison.json), [rendering](rendering.json), [visual review](additional-execution.json) |
| Stage 2 independent report tables | 0; 591 checks | [Generated report certificate](../../../reports/phase2/report_verification.json) and `check_report_tables.py` |
| Final fresh-directory quick check | 0; 58 tests, 137 links, 242 Word items; actual duration in the linked record | Same final execution; final branch navigation is additionally checked in the release snapshot |

The final Stage 2 rerun occurred after Stage 1 PDF export and environment-record repair, so its 77-entry Stage 1 snapshot contains the finished PDF and new environment. The earlier 76-entry snapshot is documented in [continuation](continuation-execution.json); the subsequent successful edition is retained in [the pre-environment-fix record](pre-env-fix-execution.json). Both were superseded by real complete reruns, not by editing hash lists. Saved-evidence-only checks, full model replay, formula reconstruction, document arithmetic and human page inspection are separate scopes. Logs are retained under `logs/`; local user paths are redacted, while exit codes, durations, hashes and outcomes are preserved.

## Reproduction differences and conclusions

All 62 result CSVs agree within `rtol=1e-9, atol=1e-10`; 60 are byte-identical. In two Stage 1 derived tables, parsing/serialization and recomputation produced differences of at most `4.0245584642661925e-16`. Row identifiers and decision counts are checked exactly. Every array in the five-array Stage 2 bootstrap archive is exactly equal. Both manuscript texts and all Word tables are unchanged. [Per-file comparison](numerical-comparison.json) records the values and comparison standard.

Fresh environment/run timestamps, source/verifier/report hashes, Office package metadata and three redrawn baseline diagnostic PNGs differ from the earlier edition. The final paper figures and table content retain their computed findings. No older numerical outputs were copied back to hide a difference. Forecast, no-alarm value, capacity and refitting conclusions are unchanged. This review found no fabricated observations, substitute predictions or placeholder experimental measurements in the checked evidence.

## Failures, retries and boundaries

The first two C-drive execution attempts could not access the isolated output directories through the installed D-drive virtual environments; their real failed statuses remain in [attempt 1](platform-attempt-execution.json) and [attempt 2](platform-attempt-2-execution.json). Execution was moved to a separate ignored D-drive directory. Windows PowerShell Word export stalled for 483.53 seconds and was terminated; its nonzero exit remains in `full-execution.json`. The documented PowerShell 7 route exported successfully. The bundled `render_docx.py` could not find LibreOffice: [renderer log](logs/packaged-renderer.log). Actual Word-exported PDFs were instead rendered with Poppler, and all 28 pages were visually inspected; this does not claim LibreOffice compatibility.

The before-fix tests intentionally expose failures. An initial test-module invocation had a working-directory import error. The added three-model test initially assumed XGBoost-only tuning fields for LR/CART and was corrected. The independent comparison helper initially tried to subtract booleans and failed; [that failed record](numerical-attempt-1.json) is retained. These development/setup failures did not write experimental results or replace failing research outputs.

The review does not establish real chronology, new-site generalization, measured mine inspection costs or field warning effectiveness. The existing holdout remains supplementary, and block intervals remain conditional on fitted predictions/rules. No comprehensive rereading of every cited paper, installation on a new machine, Linux/macOS PDF export, or broader parameter search was performed. Limited source-access retries are recorded in the skill account. Follow-up research should use independent dated working-face records and measured inspection outcomes rather than selecting a policy from this test cohort.

## Skills and repeatable review tools

[Skills actually read and used](skills.json) distinguish research review, writing integrity, limited citation checks and document QA. `paper-review` and `academic-writing-skills` support reasoning and cross-document review; they do not certify statistics. Word/PDF skills were used for regeneration and inspection. `anti-defensive-writing` was read for wording review; no extra final-paper prose rewrite was needed. `literature-review-skills`, `sciwrite` and `ml-paper-writing` were not installed and were not claimed as used.

The normal research sequence remains in [REPRODUCING.md](../../REPRODUCING.md). For an independent saved-versus-fresh comparison, keep a checkout of the base commit and a freshly reproduced checkout. In a reporting environment with `pypdf` additionally available, run from the repository root:

```text
python docs/audits/2026-10-07-full-review/check_release.py --root PATH_TO_FRESH --baseline PATH_TO_BASE --output comparison.json
python docs/audits/2026-10-07-full-review/check_report_tables.py --root PATH_TO_FRESH --baseline PATH_TO_BASE --output report-check.json
```

These tools inspect evidence and produce their own records; they do not fit models or certify visual inspection. [Changed-file inventory](changed-files.json) records all additions and modifications. No pre-existing files or directories were deleted or moved, and historical review records retain their original-version meanings. [Packaging cleanup](packaging-cleanup.json) records ten uncommitted duplicate log copies removed only after confirming their identical retained copies. Published logs redact local paths and normalize terminal trailing whitespace without changing execution outcomes; private originals remain intact.

The final branch snapshot completed its quick check in 49.60 seconds, covering 58 tests, 140 navigation links and 242 Stage 2 Word items. Its independent report check reconstructed 591 items. [Final delivery execution](release-execution.json) records each command's exit status and measured duration. The repeated rendering confirmed that all 28 final page images are identical to the pages already inspected.
