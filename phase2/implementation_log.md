# Implementation record

The protocol was locked before phase-two model fitting. No protocol amendments have been made.

3 October 2026: the first full execution completed model fitting and CSV generation, then failed while writing the run manifest because pathlib.Path was not imported. Added the missing import and reran the complete workflow. This is an implementation correction, not a change to the locked selection rules or numerical model settings. Completion and verification are recorded by the successful run manifest and verifier output.

Independent checks additionally reconstruct paired moving-block replicates, pooled error rates and phase-specific capacity contrasts. A's cost-specific capacity-binding field was made undefined, since A has no unconstrained cost-specific B decision; no thresholds or alarm decisions changed. The complete workflow and independent model replay were repeated after that audit-field correction. The plan has not changed.

The independent academic report is generated from verified result tables, and refuses to run if their hashes no longer match the verification record. It preserves all tested costs and budgets, records zero-alarm outcomes, and separates actual observations from frozen prevalence scenarios. Full combinations are retained as the electronic appendix, alongside the Word/PDF short report.

Full project review on 3 October 2026: added failed/interrupted-run invalidation,
completed-run checks, imported model-setting checks and imported dependency
hashes. Independent verification now reconstructs every one of the 2,000 paired
block samples in each phase, rather than checking eight samples plus all
quantiles. Report generation also checks manifests, replicate arrays and core
experimental source hashes. Two regression tests cover silent setting changes
and stale verification after a failed rerun. These changes strengthen execution
and evidence provenance; locked thresholds, models, parameters and cost rules
were not amended.

An additional run using the research NumPy version for first-stage baseline
and engineering calculations found small floating-point sensitivity near LR
ties: one historical reference count and two ROC-AUC cells differed, while
reported loss/warning results were unchanged. Permutation importance values
matched by feature, with tied-row ordering differences. The alternative results
passed independent consistency checks and are documented separately. Exact
published-result reproduction uses each stage's recorded environment.

Editorial revision on 3 October 2026: revised the independent paper's abstract,
motivation, result interpretation and conclusions around historical selection,
subsequent inspection workload and same-cutoff transfer. Consolidated repeated
qualifications into their relevant methods and evidence descriptions. Retained
the full policy grid, unfavorable results, conditional uncertainty and
retrospective scope. No experimental settings, thresholds, predictions or result
data were changed. Regenerated the academic Word, PDF and manuscript from the
verified evidence and reviewed all nine rendered pages.

Decision-accounting revision on 3 October 2026: added a separate descriptive
module and independent verifier for explicit no-alarm value, historical
no-alarm reasons, normalized selection margins, all A/B/C refitting contrasts,
matched capacity/detection tradeoffs and frozen prior-shift relative loss.
Original models, predictions, selected policies, bootstrap arrays and locked
settings remain unchanged. Supplementary files retain every original setting.
The core verifier now hashes its explicitly checked evidence, while the
supplementary verifier owns derived outputs; stale derived files cannot be
certified as part of a new core verification. Revised the independent paper
around decision value, capacity transfer and finite-cutoff refitting.

Validation of that revision: 52 existing tests, 8,169 first-stage checks,
63,862 original second-stage checks with every model pair replayed, 10,902
independent supplementary checks and 531 document/result checks passed.
All eleven final PDF page images were reviewed; sixteen tables and three
figures are complete, with both references on the final page.

Final contextual revision on 3 October 2026: added reference/test prevalence
to Table 1 and contextual discussion, count definitions to Table 8, two saved
paired intervals in Section 8, and budget-specific paired prior-shift values
at r=10 in Table A5. Retained Table 9 exactly and clarified the marginal ranges
in Table 11. Bounded the C-B transfer interpretation and finite-rule workload
comparison; clarified reference positives in the abstract. No fitting, tuning,
threshold selection or new experiment was performed. Source hashes, saved
evidence and independently reconstructed new table values were checked.
The updated Word/manuscript/PDF passed 583 checks; all twelve rendered pages
were inspected, with seventeen complete tables and three figures. Earlier
eleven-page and nine-page review entries describe their respective prior editions.

Complete current-project review on 3 October 2026: a clean isolated run without
saved experiment evidence reproduced all 62 CSVs (44 stage-one, 18 stage-two)
and all 3,960,000 paired bootstrap values. The primary UCI ARFF was fetched again
and its deduplication matched the input mirror. Added independent formula
reconstruction in scripts/verify_formulae.py (8,220 checks). Corrected obsolete
stage-one paper reproduction commands after repository reorganization.
Regenerated stage-one Word/PDF and re-executed stage two to capture the current
protected paper hashes through actual execution. All 18 stage-two CSVs and
bootstrap arrays matched the pre-edit snapshot. Current stage-two verification
passed 63,863 checks; supplementary verification passed 10,902. Final papers
contain 15 and 12 pages, inspected across all 27 rendered pages. Stage-two
document checks now total 584. See docs/audits/FINAL_PROJECT_REVIEW.md and the
current_* / formula_verification / post_document_rerun_comparison JSON records.

Editorial revision on 3 October 2026: revised the two papers' abstracts,
introductions, interpretation and closing paragraphs around comparable forecast
evidence and transferred decision value. Retained the locked design, formulas,
all table cells, unfavorable outcomes and conditional uncertainty scope.
Regenerated stage-one artifacts and executed the unchanged stage-two protocol
to record their current protected hashes. Replay, supplementary and independent
formula verification passed. The editorial comparison preserves all 18 CSVs
and 3,960,000 bootstrap values, with all 27 final pages visually reviewed.
See docs/audits/PAPER_EDITORIAL_REVIEW.md and editorial_verification.json for
this edition; prior review records retain their historical edition meanings.

Final factual correction on 3 October 2026: stage-one nbumps wording now
describes the retained energy-band design without asserting exact equality.
The mirror has 2,576 equal totals and two differing rows (one-based 435 and 436);
this observation does not establish a source-record error. Added a short
cross-stage workflow link, explicit parameter/threshold comparison conditions,
two references and integer alert-change labels. The unchanged second-stage
protocol was executed and replayed to capture current protected paper hashes;
all 18 CSVs, bootstrap values and paper tables match the pre-correction snapshot.
No model, feature, strategy or experimental setting was added. Current edition
checks and artifact hashes are in final_factual_verification.json.
