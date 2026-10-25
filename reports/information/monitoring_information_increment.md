# Monitoring Information Beyond Hazard Grades and Shift Type

Junjie Yang

## Question and matched comparison

This study uses the audited UCI Seismic Bumps mirror containing 2,578 records. A hazardous-shift label indicates a seismic bump with energy above 10,000 J in the subsequent eight-hour shift. It identifies a hazardous shift, not an observed accident or an avoided accident. Recorded order is a temporal proxy because timestamps and working-face identifiers are unavailable.

The primary seismic assessment orders a (no hazard), b (low hazard), c (high hazard) and d (danger state). The mirror contains only a, b for this field; c and d are defined levels but are not observed here. Average precision (AP) is the sum of precision values weighted by recall increments, evaluating tied scores as a group. It selects historical model configurations and is distinct from the detection counts evaluated at fixed inspection slots.

Does monitoring information improve hazardous-shift detection beyond three existing hazard assessments and shift type, at identical inspection allocations? This separately specified exploratory supplement compares a four-input base design with the established 17-column design. Both use XGBoost and the same four historical fitting/test splits. Each design independently selects depth 2/3 and 80/160 rounds on the same inner historical split by AP, with negative Brier if that inner set has no positives. Policy-reference and test labels do not enter fitting or tuning; no holdout is added.

Within each test block, K=floor(B*N) slots go to higher seismic grades first; model scores rank records within each grade. Both models use uniform allocation within an exactly tied boundary score group: h slots among m records containing p hazards contribute E(TP)=h*p/m. Reported fractional counts integrate allocation randomness rather than describe fractional shifts. Pooled results sum block allocations; scores are never ranked across fitted blocks.

## Expected detections on the shared test records

The four blocks contain 516, 515, 516 and 516 records and 36, 10, 24 and 18 hazardous labels, respectively: 2,063 records and 88 labels in total. At the 20% budget, the pooled extended design detects 32.00 versus base 30.71 expected hazards with 412 alerts each; the difference is 1.29 [-5.48, 7.05]. All pooled intervals across the three specified block lengths include zero.

Table 1. Matched information designs at identical total and seismic-grade allocations. TP and FN are analytic expectations; K is the exact alert count. Positive differences favor the extended design. Brackets are conditional 95% intervals at block length 32.

| Block | Budget | K | Base E(TP) / E(FN) | Extended E(TP) / E(FN) | Delta E(TP) [95% CI] |
| --- | --- | --- | --- | --- | --- |
| 1 | 1% | 5 | 0.94 / 35.06 | 0.00 / 36.00 | -0.94 [-1.53, 0.17] |
| 1 | 5% | 25 | 4.69 / 31.31 | 5.00 / 31.00 | 0.31 [-4.46, 2.42] |
| 1 | 10% | 51 | 9.56 / 26.44 | 11.00 / 25.00 | 1.44 [-4.65, 3.25] |
| 1 | 20% | 103 | 16.47 / 19.53 | 17.00 / 19.00 | 0.53 [-1.41, 4.10] |
| 2 | 1% | 5 | 0.25 / 9.75 | 0.00 / 10.00 | -0.25 [-0.40, 0.00] |
| 2 | 5% | 25 | 1.23 / 8.77 | 0.00 / 10.00 | -1.23 [-1.88, 0.48] |
| 2 | 10% | 51 | 2.51 / 7.49 | 0.00 / 10.00 | -2.51 [-3.25, 1.13] |
| 2 | 20% | 103 | 5.17 / 4.83 | 5.00 / 5.00 | -0.17 [-3.95, 1.55] |
| 3 | 1% | 5 | 0.30 / 23.70 | 0.00 / 24.00 | -0.30 [-0.50, 0.82] |
| 3 | 5% | 25 | 1.48 / 22.52 | 3.00 / 21.00 | 1.52 [-1.23, 3.93] |
| 3 | 10% | 51 | 3.03 / 20.97 | 4.00 / 20.00 | 0.97 [-2.07, 5.09] |
| 3 | 20% | 103 | 6.11 / 17.89 | 6.00 / 18.00 | -0.11 [-4.00, 4.14] |
| 4 | 1% | 5 | 0.14 / 17.86 | 1.00 / 17.00 | 0.86 [-0.32, 1.79] |
| 4 | 5% | 25 | 0.72 / 17.28 | 1.00 / 17.00 | 0.28 [-0.91, 2.55] |
| 4 | 10% | 51 | 1.47 / 16.53 | 2.00 / 16.00 | 0.53 [-1.63, 3.81] |
| 4 | 20% | 103 | 2.96 / 15.04 | 4.00 / 14.00 | 1.04 [-1.49, 3.66] |
| Pooled | 1% | 20 | 1.62 / 86.38 | 1.00 / 87.00 | -0.62 [-2.20, 0.67] |
| Pooled | 5% | 100 | 8.12 / 79.88 | 9.00 / 79.00 | 0.88 [-4.95, 4.68] |
| Pooled | 10% | 204 | 16.56 / 71.44 | 17.00 / 71.00 | 0.44 [-5.40, 7.26] |
| Pooled | 20% | 412 | 30.71 / 57.29 | 32.00 / 56.00 | 1.29 [-5.48, 7.05] |

## Block-length sensitivity

The saved scores, tuning choices and models are frozen. Each of 2,000 paired moving-block draws reconstructs a queue separately within each block, recomputes grade allocations and reranks both score sets, including analytic tie expectations. The same sampled records feed both designs and every budget. Zero-positive draws are retained. Length 32 is primary; lengths 16 and 64 are displayed without selecting one from the outcomes. These are record-order blocks, not verified physical time durations. Intervals exclude fitting, tuning and selection uncertainty.

## Discussion

The matched baseline changes the interpretation of the earlier complete-score-versus-grade-random pilot: the present increment is specifically relative to a fitted model already using all three assessments and shift type. Positive point differences occur in 3/4, 0/4, 2/4, 4/4 budgets in blocks 1-4, respectively; 16/16 main block-specific intervals include zero. The pooled intervals also include zero at every budget and block length, so these observations do not resolve a consistent monitoring-information increment under the specified workflow. This does not establish that monitoring information is generally uninformative: the comparison concerns these inputs, separately AP-selected configurations and previously examined records. At fixed P and K, E(L)=r*P+K-(r+1)*E(TP), so an additional cost grid would restate detection differences. Recorded order remains a temporal proxy, and the batch allocation is not an observed inspection process or accident-prevention effect. Independent timestamped working-face data with inspection outcomes would test transfer beyond this cohort.

## Protocol and computational evidence

The protocol, fitting and allocation code, numerical verifier and saved evidence are linked below. The verifier recomputes the calculations through a separate path and supports full refitting replay. Retained results include row-level scores and inclusion probabilities, all candidate tuning predictions, eight final models, grade allocations, every bootstrap multiplicity and replicate, and version-specific verification. The original stage-specific papers and ranking-pilot experimental results are retained. The integrated report includes the main matched-information finding; this supplement retains the complete design, table and block-length sensitivity.

Scientific code and saved-evidence links identify commit de83319. The integrated-manuscript link identifies the fixed presentation edition manuscript-2026-10-25. This revised report is generated by the current reporting code; its presentation is not claimed to be part of the earlier scientific source edition.

[UCI dataset and target definition](https://archive.ics.uci.edu/dataset/266/seismic+bumps) | [Audited source and row mapping](https://github.com/junjie-yang11/seismic-bump-forecasting/blob/de833195e2e7d025ca75c1efb57ac6d866127461/data/README.md)

[Matched-information protocol](https://github.com/junjie-yang11/seismic-bump-forecasting/blob/de833195e2e7d025ca75c1efb57ac6d866127461/phase2/information/protocol.json) | [Model fitting and within-grade allocation](https://github.com/junjie-yang11/seismic-bump-forecasting/blob/de833195e2e7d025ca75c1efb57ac6d866127461/phase2/information/run.py)

[Numerical verification and refit replay](https://github.com/junjie-yang11/seismic-bump-forecasting/blob/de833195e2e7d025ca75c1efb57ac6d866127461/phase2/information/verify.py) | [Saved results and verification guide](https://github.com/junjie-yang11/seismic-bump-forecasting/blob/de833195e2e7d025ca75c1efb57ac6d866127461/results/phase2/information/README.md)

[Integrated manuscript in this edition](https://github.com/junjie-yang11/seismic-bump-forecasting/blob/manuscript-2026-10-25/reports/overall/integrated_research_report.pdf) | [Author contributions and AI assistance](https://github.com/junjie-yang11/seismic-bump-forecasting/blob/de833195e2e7d025ca75c1efb57ac6d866127461/CONTRIBUTIONS.md)

## Increment and interval figure

![Figure 1. Extended minus base expected detections at identical allocations. Dots are the unchanged original-queue point differences. Lines show paired 95% intervals for lengths 16 (orange dashed), 32 (blue solid, main) and 64 (green dotted). Positive favors added monitoring. The shaded pooled panel is supplementary; block-specific evidence is primary.](../../reports/information/information_increment.png)
