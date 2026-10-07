# Final research reports

| Stage | PDF | Word | Online manuscript |
| --- | --- | --- | --- |
| 1 · Reliability and explainability | [PDF](phase1/technical_report.pdf) | [Word](phase1/technical_report.docx) | [Manuscript](phase1/technical_note.md) |
| 2 · Cost, capacity and threshold transfer | [PDF](phase2/phase2_threshold_transfer_report.pdf) | [Word](phase2/phase2_threshold_transfer_report.docx) | [Manuscript](phase2/phase2_threshold_transfer_report.md) |

Stage 1 assesses predictions and monitoring signals. Stage 2 measures how historically selected rules translate into later loss, detections and inspection demand. Their fixed/refitted workflows and cutoff definitions differ; cross-paper warning counts require matched workflows.

Both papers are generated from verified saved evidence. Their authoring code is [Stage 1](../phase1/generate_report.py), with [result-driven paper content](../phase1/research_paper.py), and [Stage 2](../phase2/report.py). Stage 2 report figures and its report manifest accompany the manuscript; Stage 1 figure sources remain under `results/phase1/figures/`.

The [Stage 2 report checker](../phase2/verify_report.py) compares the manuscript, Word tables, PDF numbers and input/generator hashes. Its record describes those computational checks; page rendering and visual inspection are recorded separately in the release review. Use [the homepage table updater](../phase2/update_readme.py) after rebuilding the second paper's presentation.

See the [execution sequence](../docs/REPRODUCING.md) before rebuilding. The current structure places all final papers here; older review editions record their original paths.
