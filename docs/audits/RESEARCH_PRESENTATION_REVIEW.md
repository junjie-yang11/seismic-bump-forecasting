# Research presentation release review

Baseline: `a54d4052e9155e270d00f6b6e994e3244012e0c8`. This edition updates research presentation, related-work positioning, report prose and the saved-evidence verification entry. Model families, features, folds, budgets, costs and the locked Stage 2 protocol remain unchanged.

The [fresh execution record](RESEARCH_PRESENTATION_EXECUTION.json) reports an isolated run from the official data without saved predictions, models or results supplied. It compares all 62 CSV files and 3,960,000 Stage 2 bootstrap values with the delivered evidence, including undefined-value masks and row/column coverage.

The [release validation record](RESEARCH_PRESENTATION_VALIDATION.json) records the formal checks for this edition. It is distinct from earlier audit records, which continue to describe their own versions. The [source-check record](RESEARCH_PRESENTATION_SOURCES.json) identifies primary materials reviewed and access limits for bibliographic-only checks.

## Presentation and reproducibility

The homepage presents the two questions, papers, three findings and an existing loss-contrast figure before the eight-step code map. The short overview links every quantitative finding to saved results. The related-work comparison separates method origins, the implemented evaluation framework and the empirical findings. It preserves the absence of pooled C loss advantage over no alarms at r=10 and distinguishes phase–budget from phase–budget–cost counts.

Both manuscripts are authored through their existing generators. Word, Markdown and PDF are regenerated together; results and tables retain their existing values. Full reproduction and quick saved-evidence inspection are separate entry points. The quick entry runs writing verifiers in a disposable copy and preserves published sources, results and reports.

## Reading the evidence

Monitoring records and labels come from the public source and audited mirror. Forecast scores, explanations, thresholds, decisions, intervals and evaluation statistics are computed outputs. Cost ratios, capacity budgets, temporal-proxy interpretation and frozen prevalence scenarios are declared assumptions. Empty quantities and infinite threshold sentinels keep their defined meanings; they are not substituted observations.

The new literature content does not add a model or change an experimental selection rule. Full fitting/threshold-selection uncertainty and independent working-face evaluation remain subsequent research questions.

## Checks for this edition

The complete fresh execution finished successfully: baseline fitting took 317.77 seconds, engineering feature comparisons 83.97 seconds, XGBoost research fitting 10.98 seconds, and Stage 2 fitting 19.98 seconds on the review machine. The largest CSV difference from the saved evidence was 4.03e-16; all 3,960,000 bootstrap values matched exactly. These timings describe this environment and exclude dependency installation and document export.

Current-source validation passed 54 behavioral tests, 8,169 Stage 1 consistency checks, 7,460 research replay checks, 63,854 Stage 2 checks with fixed/refitted model replay, 10,902 supplementary checks and 8,220 independent formula checks. Counts describe the corresponding checker scopes; they are not numbers of independent experimental observations.

The [document and presentation review](RESEARCH_PRESENTATION_DOCUMENTS.json) records 215 additional checks. All 62 result CSV files, the saved bootstrap archive, existing figures and locked protocol match the baseline bytes. All 11 Stage 1 and 17 Stage 2 Word tables match the baseline cell values. Word/Markdown agreement and PDF numerical content were checked; every final page was visually inspected (15 Stage 1 and 12 Stage 2 pages). The existing invisible Word export and Poppler rendering were used because LibreOffice was unavailable. The refreshed [Stage 2 document verification](../../reports/phase2/report_verification.json) contains 587 checks and the actual final document hashes.

The quick entry passed in 50.35 seconds with the existing local mirror, checking 133 file links and 239 Stage 2 Word items in addition to its existing verifier sequence. A second run exported the staged public files into a clean checkout with no data cache: the process passed in 52.19 seconds, including mirror download inside the disposable copy, and left the checkout without a cache. Both actual runs are recorded in the document review. Success records refer to this edition's checked inputs and do not certify future edits.
