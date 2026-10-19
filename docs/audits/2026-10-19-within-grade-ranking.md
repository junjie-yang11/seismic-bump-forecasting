# Editorial closure and separately specified ranking pilot

## Baseline and scope

Work began from `39accad5a32660f351b3dc27838a15c21bf56c37` on `main`, with a clean working tree, at `2026-10-19T06:22:45.429119+00:00`. Remote: <https://github.com/junjie-yang11/seismic-bump-forecasting>. Work branch: `study/within-grade-ranking-20261019`. All calculations and document generation ran in a separate byte-preserving copy before deployment to the original checkout.

The original models, features, splits, costs, budgets, threshold rules and locked protocol remain unchanged. All 69 original CSV files, original saved-result files, shared model sources and both stage-specific report directories compare byte-for-byte with the baseline. The integrated paper receives explanation changes only. The ranking pilot is a different retrospective batch question with its own saved protocol, evidence and short report.

## Clarifications to the existing evidence

- At `r=10`, the three direct-grade B rules have identical row decisions: all 516 phase-1 records are flagged; none are flagged in phases 2–4. Their common TP/FP/alerts are 36/480/516; fixed XGBoost B has 35/379/414. Its lower assumed loss against that common rule reflects 101 fewer false alerts and one fewer detection, not three distinct replications.
- The integrated paper, homepage and overview distinguish pooled C-minus-no-alarm point differences from conditional intervals. At 5% and 10%, phase 1 has no detections and entirely positive loss-difference intervals; the nonzero pooled intervals span zero.
- Navigation identifies the original Stage 2 PDF as the locked-experiment technical edition, and the integrated report plus comparison appendix as the latest complete threshold-decision analysis. Supplementary protocol, runner, independent verifier and evidence are linked explicitly.

## Ranking specification and results

The [protocol](../../phase2/ranking/protocol.json) was saved before the new calculations, after earlier study results had been inspected. This is an exploratory specification, not a preregistration. It fixes `seismic`, the four original test phases, four budgets, saved fixed XGBoost scores, analytic random selection, label-independent score-tie keys and 2,000 paired length-32 block draws.

Primary grade-first ML and grade-random selection have exactly the same total and grade-specific allocations. Every bootstrap queue is reallocated and reranked; saved alert flags are not simply resampled. The random reference is an analytic expectation, with its separate exact hypergeometric allocation distribution retained. The independent verifier uses Python sorting, weighted-prefix ranking and SciPy probabilities rather than calling the production ranking implementation.

Pooled primary extra detections are −0.47, +1.67, +2.04 and +3.92 at 1%, 5%, 10% and 20%. All pooled conditional intervals contain zero. At 20%, the model detects 32 records with 412 alerts, compared with random expected detections 28.08; the increment is 3.92 [−2.05, 9.86]. Phase 2 at 1% instead has −0.23 [−0.40, −0.07]. Every phase and budget is retained. No preferred setting is selected.

The full score uses other grades and shift type as well as monitoring inputs. This pilot does not isolate a sensor effect. A matched information-source model comparison was not run. These records are not verified simultaneous inspection candidates; the task is retrospective batch ranking, not operational dispatch.

## Actual execution

Windows x64, Python 3.12.14. Research dependencies: NumPy 2.3.5, pandas 3.0.1, SciPy 1.18.1 and XGBoost 3.1.3. Reporting used a separate document dependency directory. Native PDF export used Microsoft Word through PowerShell 7; all pages were rendered with Poppler for visual inspection. Commands below ran from the isolated repository root. Durations are measured wall times, including interpreter startup.

| Command | Actual result | Seconds |
| --- | --- | --- |
| `python -B -m unittest tests.test_ranking_pilot -v` | 11 passed, including label isolation, exact capacity, ties, reranking and revocation of stale success | 2.36 |
| `python -B -m phase2.ranking.run` | Completed all phase/pooled allocations and 80,000 resampled contrasts | 5.94 |
| `python -B -m phase2.ranking.verify` | 26,342 checks passed; every saved draw and contrast independently replayed | 6.10 |
| `python -B -m reporting.overall` | Generated integrated Markdown/Word, 13 tables | 2.87 |
| `pwsh -NoProfile -ExecutionPolicy Bypass -File reporting/export_overall.ps1` | Integrated PDF exported | 43.00 |
| `python -B -m reporting.verify_overall --pdf` | 2,232 checks passed, including PDF text | 1.25 |
| `python -B -m reporting.ranking` | Final separate Markdown/Word generated, two tables | 0.43 |
| `pwsh -NoProfile -ExecutionPolicy Bypass -File reporting/export_overall.ps1 -ReportDirectory ranking -Stem within_grade_ranking_pilot` | Final short PDF exported | 33.41 |
| `python -B -m reporting.verify_ranking --pdf` | 188 checks passed, including PDF text | 0.24 |
| `python -B -m phase1.quick_check` | Complete saved-evidence entry passed in a disposable copy, published bytes preserved | 65.69 |

The complete Quick Check ran 84 shared/report tests and 12 decision tests. Saved-evidence checks passed: Stage 1 8,169; Stage 2 63,809; decision accounting 13,036; formula reconstruction 10,342; direct-grade supplement 26,911; ranking pilot 26,342. Standard-library document checks passed with 1,837 integrated and 94 short-report checks; these counts exclude the separately completed PDF-text checks. The invocation checked 228 local links and 274 Stage 2 Word items. Both artifact exporters and all final experiment/check commands above exited zero.

All 74 Python files parsed successfully. No files were deleted or moved. New code, evidence and the short report are confined to their ranking directories, with one behavior-test file; shared authoring/export and Quick Check were extended. Integrated Markdown, Word and PDF were rebuilt together. Visual review covered all 14 integrated and three pilot pages, with the new pilot tables and main comparator tables also inspected individually; no obvious clipping or table overflow was observed.

The [numerical verification](../../results/phase2/ranking/verification.json), [pilot report verification](../../reports/ranking/verification.json) and [integrated report verification](../../reports/overall/verification.json) identify actual checked hashes and scope. The run manifest records real execution and saved output hashes. These are computational checks, not an audit of the original mine measurements.

## Skills and limits

Academic Research Skills' evidence-mapping workflow and Supervisor-Skills' consistency checks guided the question/evidence review. They were applied in this session without a separate agent panel. `anti-defensive-writing` guided concise findings-led prose; document/PDF skills guided synchronized generation and rendered-page review. None substitutes for the executed tests or numerical replay.

This round did not refit the original research models, repeat their full model replay, redownload the official ARFF, verify original field measurements, re-review every cited paper, or certify another operating system. Original model-replay records are preserved and retain their recorded scope. The new ranking computation and every ranking resampling result were actually executed and independently replayed. No new model, information-source attribution experiment, shrinkage threshold study or predictive-multiplicity study was added.
