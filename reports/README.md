# Research reports and supplements

For a quick introduction, read the [research overview](../docs/PROJECT_OVERVIEW.md). The integrated paper develops the full argument; the stage-specific technical reports and separately specified supplements provide the supporting detail. The [directory map](../docs/PROJECT_STRUCTURE.md) connects every study to its code and saved evidence.

## Main paper

| Material | PDF | Word | Online |
| --- | --- | --- | --- |
| Integrated research report | [PDF](overall/integrated_research_report.pdf) | [Word](overall/integrated_research_report.docx) | [Manuscript](overall/integrated_research_report.md) |
| Complete frozen-policy comparison supplement: all 1,260 settings | [PDF](overall/decision_comparison_supplement.pdf) | [Word](overall/decision_comparison_supplement.docx) | [Manuscript](overall/decision_comparison_supplement.md) |

The integrated paper connects forecast evidence, historical threshold transfer and decision value. It includes the direct-grade and no-alarm comparisons and the matched-information core finding. The [complete comparison appendix](overall/comparator_appendix.md) also retains every record-block/cost setting, including detections, missed shifts, false alerts, workload, excess and paired intervals.

## Original stage-specific technical reports

| Stage | PDF | Word | Online | Code and evidence |
| --- | --- | --- | --- | --- |
| Stage 1: forecast reliability and explainability | [PDF](phase1/technical_report.pdf) | [Word](phase1/technical_report.docx) | [Manuscript](phase1/technical_note.md) | [Workflow](../phase1/README.md) and [results](../results/phase1/README.md) |
| Stage 2: cost, capacity and threshold transfer | [PDF](phase2/phase2_threshold_transfer_report.pdf) | [Word](phase2/phase2_threshold_transfer_report.docx) | [Manuscript](phase2/phase2_threshold_transfer_report.md) | [Locked workflow](../phase2/README.md) and [results](../results/phase2/README.md) |

These are the retained technical editions. The Stage 2 PDF covers the original locked experiment; later direct-grade and no-alarm comparisons are in the integrated paper and supplement above. The stages use overlapping records and different fitting/threshold workflows, so cross-paper warning counts require matched definitions. They are not independent validation studies.

## Separately specified Stage 2 supplements

| Study | Question | Report | Protocol, code and evidence |
| --- | --- | --- | --- |
| Frozen-policy and direct-grade comparisons | How do frozen ML rules compare with no alarms and direct hazard grades? | [Integrated paper](overall/integrated_research_report.pdf) and [complete comparison supplement](overall/decision_comparison_supplement.pdf) | [Protocol and commands](../phase2/comparators/README.md); [saved comparisons](../results/phase2/comparators/README.md) |
| Exploratory within-grade ranking pilot | Can complete-model scores add detections at identical grade allocations and batch slots? | [PDF](ranking/within_grade_ranking_pilot.pdf), [Word](ranking/within_grade_ranking_pilot.docx), [online](ranking/within_grade_ranking_pilot.md) | [Protocol and commands](../phase2/ranking/README.md); [evidence](../results/phase2/ranking/README.md) |
| Exploratory matched-information analysis | Do monitoring variables add detections beyond hazard grades and shift type at identical allocations? | [PDF](information/monitoring_information_increment.pdf), [Word](information/monitoring_information_increment.docx), [online](information/monitoring_information_increment.md) | [Protocol and commands](../phase2/information/README.md); [evidence](../results/phase2/information/README.md) |

The ranking pilot reuses complete-model scores and does not isolate sensor-specific value. The matched-information analysis compares separately tuned four-input and 17-input designs. Its core result appears in Section 5.6 and Figure 5 of the integrated paper; the short report retains the full design, table and block-length sensitivity. Historical reference budgets and strict test-batch allocations are different constraints. These supplements reuse observed records and add no independent validation cohort.

## Generation, verification and fixed editions

Paper content is generated from saved computations. [Stage 1 generation](../phase1/generate_report.py) uses the [result-driven content module](../phase1/research_paper.py); [Stage 2 generation](../phase2/report.py) produces its technical report. The [reporting guide](../reporting/README.md) covers the integrated paper and short reports. Follow the [execution sequence](../docs/REPRODUCING.md) before rebuilding.

The [integrated manifest](overall/report_manifest.json) identifies inputs and generated tables; the [separate checker](../reporting/verify_overall.py) reconstructs them from saved evidence. Its [verification record](overall/verification.json) states the checked scope and output hashes. The ranking [manifest](ranking/report_manifest.json) and [verification](ranking/verification.json), and matched-information [manifest](information/report_manifest.json) and [verification](information/verification.json), identify their own report editions. Computational checks and visual inspection of exported pages are separate procedures.

The [Stage 2 report checker](../phase2/verify_report.py) checks manuscript/Word/PDF agreement and recorded inputs; its [record](phase2/report_verification.json) identifies that edition. The [homepage updater](../phase2/update_readme.py) refreshes its result table from saved computations.

Scientific code/evidence links in the matched-information short report identify source commit de83319; its integrated-paper link identifies presentation tag manuscript-2026-10-26. Current navigation links lead to the latest retained files. Report figures, plotting CSVs and generation/verification records keep their existing locations so the current generators and checkers continue to resolve them. Stage 1 figure sources remain under [its results directory](../results/phase1/README.md).
