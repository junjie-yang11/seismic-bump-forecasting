# Frozen policy comparisons and manuscript revision

Baseline: `f15ab579e283324cbddffab56746e580027501fc`, `main`, clean worktree. Remote: `https://github.com/junjie-yang11/seismic-bump-forecasting.git`. Work branch: `supplement/hazard-grade-20261019`. Work was carried out in an isolated candidate before copying reviewed files to the original checkout.

## Research boundary

The [separate protocol](../../phase2/comparators/protocol.json) was saved before executing these supplementary comparisons, after the original results were already known. This is an exploratory addition, not a retrospective claim of preregistration. The original locked plan, model configurations, fits, feature design, cost/budget grid, reference/test boundaries and ML decisions remain unchanged. No training or ML threshold reselection is performed.

Three direct fields are retained separately: seismic, seismoacoustic and ghazard. The official UCI metadata and ARFF coding were inspected. Seismic has explicit severity descriptions; the shared ordering for the other two assessments is an adopted ordinal interpretation, clearly disclosed. The observed mirror contains a/b in seismic and a/b/c in the other fields. The experiment does not invent d observations or claim these simple rules are documented mine operating procedures.

Candidate sets and selected thresholds use only historical reference rows. Whole grades move together. Candidate sets with identical reference decisions are collapsed using the original canonical convention, including infinite thresholds. The test rows supply grades for frozen decisions and labels only for evaluation. All costs and budgets are retained; no field or workflow is selected from test performance.

## Implemented revisions

1. Correct AP prose to precision weighted by recall increments; the AP implementation and original AP values are unchanged.
2. Add policy-minus-no-alarm and fixed-XGBoost-minus-each-grade paired intervals, separately by phase and pooled with phase boundaries preserved.
3. Save historical scores, grade coding, candidates, 384 audits, 8,252 method/test-row decisions, 720 evaluations, 1,260 intervals and every bootstrap multiplicity/replicate.
4. Put original C-A intervals with policy comparisons. Add a specifically identified finite-cutoff refitted/fixed example to the model-updating subsection using retained evidence.
5. Add matched-cohort attenuation and the 557-to-34 alerts / 25-to-2 detections tradeoff to the abstract and conclusion. Retain comparator-dependent B and C findings.
6. Reduce forced pagination, keep new comparison tables together, set readable column widths and use heading page-break properties to avoid an empty page before references. Generate all-cost combinations in a separate online appendix.

## Findings and interpretation

At r=10, nonzero pooled XGBoost C-minus-no-alarm intervals contain zero. The seismic and seismoacoustic C rules select no alarms; the ghazard C rule gives four detections, 22 false alerts and a pooled loss difference of -0.87 per 100 records, with interval [-3.97, 1.36]. Its negative point estimate does not resolve loss direction. All displayed pooled C-minus-grade intervals also contain zero; exact zero intervals follow identical decisions and do not prove stable transfer or equivalence.

Selection mechanism matters. Cost-only B has pooled ML-minus-grade loss -4.41 [-7.03, -0.97] for each field, while B-minus-no-alarm is +1.41 [-9.26, 11.05]. The three grade contrasts are dependent, not independent replications. These unadjusted conditional intervals are presented alongside all remaining A/B/C settings; they are not used to choose a new preferred strategy.

## Skills and verification scope

ARS-Codex supplied the evidence/revision and statistical interpretation checks; Supervisor-Skills supplied the challenge-method-contribution consistency checks; anti-defensive-writing supplied narrative editing. The document/PDF skills supplied render-and-inspect guidance. These are AI-assisted workflows, not an independent journal review panel. Source-code inspection, actual execution and independent arithmetic/replay supply the computational evidence.

The independent [supplement verifier](../../phase2/comparators/verify.py) does not call the production grade selector or bootstrap index function. It enumerates historical decisions, checks exact frozen ML scores/alerts/thresholds, reconstructs losses and phase-specific capacity, regenerates every random draw and replays all 2,520,000 paired differences. Numeric arithmetic allows a 1e-12 rounding bound; decisions and numerical threshold comparisons are exact. The [execution manifest](../../results/phase2/comparators/run_manifest.json) and [verification record](../../results/phase2/comparators/verification.json) identify actual input, code, output and verifier hashes.

The [integrated report verifier](../../reporting/verify_overall.py) checks generated artifacts and the complete appendix. Its [record](../../reports/overall/verification.json) describes its own scope. Quick Check executes both independently in a disposable snapshot, preserving full-replay records. This task does not refit the original models, estimate full selection uncertainty, perform independent-site validation or repeat the entire literature review. Original stage report editions are retained; the overall paper presents the addition.

## Actual execution

Environment: Windows; Python 3.12.14, NumPy 2.3.5 and pandas 3.0.1 for computation. Authoring used the bundled Python runtime and reporting dependencies; Microsoft Word supplied the PDF export and Poppler supplied page renders.

| Command or inspection | Result |
| --- | --- |
| `python -B -m phase2.comparators.run` | Exit 0; 1.99 seconds for the final implementation. No model fitting. The executed manifest records its precise environment, input/code hashes and outputs |
| `python -B -m phase2.comparators.verify` | Exit 0; 26,911 independent checks; all 720 evaluations, 1,260 intervals and 2,520,000 paired replicates replayed |
| `python -B -m reporting.overall` | Exit 0; generated 13 tables, 3 figures and the complete online comparison appendix |
| `pwsh -NoProfile -ExecutionPolicy Bypass -File reporting/export_overall.ps1` | Exit 0; final export 42.91 seconds |
| `python -B -m reporting.verify_overall --pdf` | Exit 0; 2,225 checks including main tables, appendix, source hashes, Word/Markdown agreement and PDF text |
| `python -B -m phase1.quick_check` | Exit 0; 54.97 seconds; 73 shared/report tests plus 12 decision tests. Stage 1: 8,169 checks; Stage 2: 63,809; original supplement: 13,036; formulas: 10,342; comparator supplement: 26,911; integrated paper: 1,830 standard-library checks; 211 local links and 274 Stage 2 Word items |
| Visual page inspection | All 14 final pages inspected. The final width/text edit changed only pages 8 and 10; these were inspected again and the other pages matched the reviewed render pixel-for-pixel. No blank page, clipped table or split Budget header remains |
| Baseline comparison | All 63 original CSVs, original stage report files, original result records and shared model/metric/validation code unchanged. All 68 Python files parsed successfully |

An initial report-verifier attempt mistook the literal zero interval `[0,0]` for a bibliography index; restricting citation indices to positive integers fixed the parser. The run did not change numeric results. Earlier layout exports exposed a blank break page and an awkward header wrap; both were corrected through the generator and re-exported, followed by the final checks above. All earlier run logs remain outside the published research tree; no failed result was replaced with invented values or a manually edited success/hash record.

During publication, the existing CSV ignore rule excluded the new nested evidence directory. A scoped exception for `results/phase2/comparators/*.csv` retains those six computed files while leaving the raw data cache ignored. Staged file bytes were compared with the tested candidate before commit.
