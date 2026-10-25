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
| `overall.py` | Read saved CSVs and source references, construct the integrated argument and generate Markdown/Word plus the conceptual overview and record-block-specific decision tradeoff figure |
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

## Main argument and decision figure

The integrated paper asks how common test cohorts change interpretation of forecast gaps, and how historical warning rules transfer in loss, coverage and workload. Table 3a retains the common-cohort AP results; Table 3b computes gap attenuation from unrounded saved differences. Calibration and feature-use analyses support these questions. The ranking pilot remains a separately specified exploratory study.

Figure 4 reads the frozen XGBoost C results at `r=10` from the comparator CSVs. The generated [plot data](../reports/overall/decision_tradeoffs.csv) retain all four budgets, four record blocks and a supplementary pooled row, with the original policy-minus-no-alarm intervals. The figure does not run a new bootstrap. Grouped table budgets must have identical complete row-level decisions; capacity excess is still reported separately for each budget. Full combinations remain in the appendix.

The ranking report manifest records the hash of `overall.py`, which contains its shared Word writer. After changing that file, rebuild and verify the ranking report too, even when the pilot evidence and prose are unchanged. The original two stage reports and experimental result directories are not regenerated for presentation-only edits.

## Matched information-source study

The separately specified [information study](../phase2/information/README.md) provides a detailed short supplement whose core finding is included in Section 5.6 and Figure 5 of the integrated manuscript. The original stage-specific manuscripts remain unchanged. In the research environment, first run `python -B -m phase2.information.run` and `python -B -m phase2.information.verify --refit`. The reporting environment then reads the verified evidence:

```text
python -B -m reporting.information
pwsh -NoProfile -ExecutionPolicy Bypass -File reporting/export_overall.ps1 -ReportDirectory information -Stem monitoring_information_increment
python -B -m reporting.verify_information --pdf
```

The [short report](../reports/information/monitoring_information_increment.md) contains one record-block-specific table and one interval figure, with block length 32 as the main analysis and 16/64 retained as sensitivity settings. Saved scores, models, tuning predictions, inclusion probabilities and bootstrap evidence are under `results/phase2/information/`. Plain calculation/model loading and full candidate/final refitting are separately identified by the numerical verifier. Existing Quick Check covers the original study and discovers the new behavior tests; the two information-study verifiers above are separate additional checks. Export Word documents serially.

## Current manuscript revision and evidence scope

For presentation updates to retained evidence, first compute and independently check the complete three-model gap summary in the research environment:

```text
python -B -m phase1.gap_summary
python -B -m phase1.verify_results --reports
python -B -m phase2.information.verify --refit
```

The last command repeats all matched-information candidate and final fits and independently replays the saved decisions and resampling calculations; it does not reselect historical Stage 2 policies. The retained original run manifest is unchanged. Its bounded [historical context snapshot](../results/phase2/information/README.md) preserves the old presentation and derived-summary bytes, while computational inputs and evidence remain live hash checks.

In the reporting environment, generate/export/verify the integrated report, then repeat that sequence for the ranking and matched-information reports using their commands above. Export Word documents serially. All three report manifests bind the shared writer version. The main report includes editable native Word equations and matching Markdown math; its verifier checks fractions, subscripts, signs and floor delimiters through a separately specified mathematical structure. Figure 1 includes an SVG alternative with a PNG fallback. Figures 2/3 are redrawn from saved calibration bins/SHAP means, without changing those source tables. Figure 5 reads the saved length-32 matched-information intervals; all 20 record-block/pooled-budget settings are retained in [plot data](../reports/overall/monitoring_increment.csv). No new bootstrap is run by report generation.

The complete comparator appendix stays in [Markdown](../reports/overall/comparator_appendix.md), with locked technical reports and exploratory short reports as supporting materials. The main text retains the selection objectives, data isolation, canonical tie/threshold rules and conditional interval scope needed to understand its findings. Computational checks and page-by-page visual inspection are separate tasks.

The original `results/phase1/gap_attenuation.csv` remains the locked two-model summary. The standalone updater and the end of `phase1.run_research` write `results/phase1/gap_attenuation_all_models.csv`; Table 3b reads this separate three-model result. This keeps original Stage 2 input hashes intact. Both the Stage 1 verifier and the integrated-report verifier reconstruct the new summary from saved row predictions.

The matched-information short report is independently readable: it defines the source mirror, next-shift energy label, observed seismic grades and AP. Its native Word/PDF hyperlinks and Markdown links identify scientific source/evidence commit `de83319` and presentation tag `manuscript-2026-10-26`; `source_version`, `edition_tag` and `source_links` in the report manifest identify those fixed destinations. The current presentation is verified against the current generator rather than attributed to that older evidence edition.

## Printable complete supplement and fixed edition

The full frozen comparator tables also have a printable landscape supplement. In the reporting environment, after the main generator has created the Markdown appendix:

```text
python -B -m reporting.appendix
pwsh -NoProfile -ExecutionPolicy Bypass -File reporting/export_overall.ps1 -ReportDirectory overall -Stem decision_comparison_supplement
python -B -m reporting.verify_appendix --pdf
```

The [PDF](../reports/overall/decision_comparison_supplement.pdf), [Word](../reports/overall/decision_comparison_supplement.docx) and [Markdown](../reports/overall/decision_comparison_supplement.md) retain all 1,260 saved settings. The standalone verifier reconstructs every row from the saved CSVs. The original Markdown comparison appendix remains available for machine inspection.

Presentation links in the papers identify the immutable `manuscript-2026-10-26` edition; scientific source links in the short reports separately identify their earlier evidence commit. The tag is created only after generation and verification and must never be moved to a later revision. A later paper revision needs a new edition tag. README links continue to identify the latest materials. The measured Word quality flag alone retained about 200 PPI, so the actual quality improvement uses embedded SVG alternatives. The main report verifier inspects the exported PDF recursively and requires zero raster images for its five research figures.
