# Final research reports

For a quick introduction, read the [research overview](../docs/PROJECT_OVERVIEW.md). For the complete argument, read the **integrated research report**: [PDF](overall/integrated_research_report.pdf) · [Word](overall/integrated_research_report.docx) · [Online manuscript](overall/integrated_research_report.md). It gives one argument, shared data description and integrated discussion, including the matched-information core finding, while preserving the different stage protocols.

The two supporting technical reports retain complete stage-specific methods, combinations and supplementary evidence:

| Stage | PDF | Word | Online manuscript |
| --- | --- | --- | --- |
| 1 · Reliability and explainability | [PDF](phase1/technical_report.pdf) | [Word](phase1/technical_report.docx) | [Manuscript](phase1/technical_note.md) |
| 2 · Cost, capacity and threshold transfer | [PDF](phase2/phase2_threshold_transfer_report.pdf) | [Word](phase2/phase2_threshold_transfer_report.docx) | [Manuscript](phase2/phase2_threshold_transfer_report.md) |

Stage 1 assesses predictions and monitoring signals. Stage 2 measures how historically selected rules translate into later loss, detections and inspection demand. Their fixed/refitted workflows and cutoff definitions differ; cross-paper warning counts require matched workflows.

Both papers are generated from verified saved evidence. Their authoring code is [Stage 1](../phase1/generate_report.py), with [result-driven paper content](../phase1/research_paper.py), and [Stage 2](../phase2/report.py). Stage 2 report figures and its report manifest accompany the manuscript; Stage 1 figure sources remain under `results/phase1/figures/`.

The [integrated generator and commands](../reporting/README.md) use existing evidence without fitting models. Its [manifest](overall/report_manifest.json) records input hashes and computed table content. Its [independent check](../reporting/verify_overall.py) reconstructs the main decision and scenario tables from aligned saved row decisions; the [verification record](overall/verification.json) states the exact scope and checked output hashes. Visual inspection of exported pages is an additional step.

The integrated report includes the separately specified [frozen-policy and direct-grade supplement](../phase2/comparators/README.md). Its [complete record-block/cost appendix](overall/comparator_appendix.md) retains every A/B/C combination, with detections, missed shifts, false alerts, workload, excess and paired intervals. The original stage papers remain the locked-study technical edition.

For the latest complete threshold-decision analysis, use the integrated report and its appendix above. The Stage 2 PDF is the original locked-experiment technical report; it does not include the later direct-grade supplement.

The **separate exploratory ranking pilot** asks whether complete-model scores add detections within the same seismic grade at identical inspection allocations: [PDF](ranking/within_grade_ranking_pilot.pdf) · [Word](ranking/within_grade_ranking_pilot.docx) · [Online report](ranking/within_grade_ranking_pilot.md). Its [protocol and commands](../phase2/ranking/README.md), [evidence](../results/phase2/ranking/README.md), [report manifest](ranking/report_manifest.json) and [verification](ranking/verification.json) are separate from the locked threshold study. It reuses saved scores and does not establish sensor-specific value.

The [Stage 2 report checker](../phase2/verify_report.py) compares the manuscript, Word tables, PDF numbers and input/generator hashes. Its [verification record](phase2/report_verification.json) identifies the checked report hashes and verifier version. Inspect the rendered pages as well as these computational checks. Use [the homepage table updater](../phase2/update_readme.py) after rebuilding the second paper's presentation.

See the [execution sequence](../docs/REPRODUCING.md) before rebuilding. The current structure places all final papers here; older review editions record their original paths.

The matched-information main result appears in Section 5.6 and Figure 5 of the integrated manuscript. The [full supplement](information/monitoring_information_increment.pdf) retains all record-block-specific expectations, the three block lengths and the reproduction detail. Historical reference budgets and strict test-batch allocations are distinct; the latter does not add an independent validation cohort.

The information supplement introduces the audited dataset, target label, seismic severity order and AP before describing the matched design. Its code and evidence links are pinned to scientific source edition `de83319`, while its integrated-manuscript link points to presentation tag `manuscript-2026-10-25`; the report manifest distinguishes both versions.

The complete frozen-policy comparison supplement is available as [PDF](overall/decision_comparison_supplement.pdf), [Word](overall/decision_comparison_supplement.docx) and [Markdown](overall/decision_comparison_supplement.md). It contains all 1,260 settings without selecting favorable results.
