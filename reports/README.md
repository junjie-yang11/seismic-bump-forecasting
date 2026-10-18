# Final research reports

Start with the **integrated research report**: [PDF](overall/integrated_research_report.pdf) · [Word](overall/integrated_research_report.docx) · [Online manuscript](overall/integrated_research_report.md). It gives one argument, shared data description and integrated discussion, while preserving the different stage protocols.

The two supporting technical reports retain complete stage-specific methods, combinations and supplementary evidence:

| Stage | PDF | Word | Online manuscript |
| --- | --- | --- | --- |
| 1 · Reliability and explainability | [PDF](phase1/technical_report.pdf) | [Word](phase1/technical_report.docx) | [Manuscript](phase1/technical_note.md) |
| 2 · Cost, capacity and threshold transfer | [PDF](phase2/phase2_threshold_transfer_report.pdf) | [Word](phase2/phase2_threshold_transfer_report.docx) | [Manuscript](phase2/phase2_threshold_transfer_report.md) |

Stage 1 assesses predictions and monitoring signals. Stage 2 measures how historically selected rules translate into later loss, detections and inspection demand. Their fixed/refitted workflows and cutoff definitions differ; cross-paper warning counts require matched workflows.

Both papers are generated from verified saved evidence. Their authoring code is [Stage 1](../phase1/generate_report.py), with [result-driven paper content](../phase1/research_paper.py), and [Stage 2](../phase2/report.py). Stage 2 report figures and its report manifest accompany the manuscript; Stage 1 figure sources remain under `results/phase1/figures/`.

The [integrated generator and commands](../reporting/README.md) use existing evidence without fitting models. Its [manifest](overall/report_manifest.json) records input hashes and computed table content. Its [independent check](../reporting/verify_overall.py) reconstructs the main decision and scenario tables from aligned saved row decisions; the [verification record](overall/verification.json) states the exact scope and checked output hashes. Visual inspection of exported pages is an additional step.

The integrated report includes the separately specified [frozen-policy and direct-grade supplement](../phase2/comparators/README.md). Its [complete phase/cost appendix](overall/comparator_appendix.md) retains every A/B/C combination, with detections, missed shifts, false alerts, workload, excess and paired intervals. The original stage papers remain the locked-study technical edition.

The [Stage 2 report checker](../phase2/verify_report.py) compares the manuscript, Word tables, PDF numbers and input/generator hashes. Its [verification record](phase2/report_verification.json) identifies the checked report hashes and verifier version. Inspect the rendered pages as well as these computational checks. Use [the homepage table updater](../phase2/update_readme.py) after rebuilding the second paper's presentation.

See the [execution sequence](../docs/REPRODUCING.md) before rebuilding. The current structure places all final papers here; older review editions record their original paths.
