# Integrated research report

The [overall paper](../reports/overall/integrated_research_report.pdf) connects forecast evidence to warning decisions. The two [stage reports](../reports/README.md) retain full technical detail. This package integrates saved evidence; it does not fit models or select features, parameters or policies.

Run from the repository root after both stages and their source checks are complete:

```text
python -B -m phase2.comparators.run
python -B -m phase2.comparators.verify
python -B -m reporting.overall
pwsh -NoProfile -ExecutionPolicy Bypass -File reporting/export_overall.ps1
python -B -m reporting.verify_overall --pdf
```

Use the existing reporting dependencies for authoring and PDF text checks. PDF export uses Microsoft Word on Windows. The standard-library check `python -B -m reporting.verify_overall` checks saved-source hashes, Word/Markdown agreement and independently reconstructed tables, without PDF text extraction or model fitting. It is included in the repository Quick Check, which runs in a disposable copy.

| File | Responsibility |
| --- | --- |
| `overall.py` | Read saved CSVs and source references, construct the integrated argument and generate Markdown/Word plus the conceptual overview |
| `export_overall.ps1` | Export the generated Word document to PDF |
| `verify_overall.py` | Reconstruct main decision counts/loss and scenarios from aligned row decisions; verify tables, citations, inputs and generated files |
| `ranking.py` | Build the separate short ranking report from verified pilot evidence, using the shared Word writer |
| `verify_ranking.py` | Independently reconstruct both pilot tables and check source/artifact hashes and Word/Markdown/PDF agreement |

Outputs are under `reports/overall/`. The manifest identifies the exact source files and generator, records source certificates available at build time and declares that no new experiment was performed. The independent verification record identifies its scope, whether PDF text was checked, the checked output hashes and verifier version. A failed build/check revokes its old success. Visual page inspection remains separate from computational checks.

Rebuilding also removes the previous PDF. Export the new Word document before verification; an older PDF must not accompany a rebuilt manuscript.

The main report's AP-minus-prevalence column is descriptive arithmetic for the stated cohort; its protocol-difference intervals do not become AP-gain intervals. The separately specified [frozen-policy supplement](../phase2/comparators/README.md) adds direct grade-warning rules and no-alarm/ML-minus-grade intervals. The generator reads its saved results, produces compact tables and a [complete combination appendix](../reports/overall/comparator_appendix.md), and does not perform the experiment itself. The original stage papers retain their locked-study scope.

## Separate ranking pilot

After executing and verifying the [ranking pilot](../phase2/ranking/README.md) in the research environment, use the reporting environment:

```text
python -B -m reporting.ranking
pwsh -NoProfile -ExecutionPolicy Bypass -File reporting/export_overall.ps1 -ReportDirectory ranking -Stem within_grade_ranking_pilot
python -B -m reporting.verify_ranking --pdf
```

Outputs are in `reports/ranking/`. The pilot has its own protocol, result directory, report manifest and verification record. The shared writer controls typography only; the pilot does not add a new result to the integrated paper or rewrite its research question. Export Word documents serially. Both builders remove their previous PDFs before generation, and their verifiers revoke stale success on failure.
