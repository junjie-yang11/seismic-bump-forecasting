# Ranking Within Hazard Grades at Fixed Inspection Capacity: A Retrospective Pilot

Junjie Yang

## Research question and result

Can complete-model scores identify additional hazardous records within the same seismic grade and inspection allocation? This exploratory pilot uses saved fixed XGBoost scores on the existing four test blocks. It compares grade-priority ranking by model score with uniform random selection at exactly the same total and grade-specific allocations. Global model ranking is a separate auxiliary comparison.

At the 20% budget, grade-first ML detects 32 hazardous records with 412 alerts, versus an analytic random expectation of 28.08 detections. The increment is 3.92 [-2.05, 9.86] records. The pooled intervals at all four budgets contain zero. Positive point increments at 5%, 10% and 20% do not resolve the direction of within-grade benefit under this conditional analysis. No grade, budget, model or seed is selected from these results.

## Data and fixed analysis protocol

The audited UCI mirror supplies seismic grades for 2,063 existing test records and 88 hazardous-shift labels. The observed primary field has a and b only. Higher grade receives priority. Within each grade, the full XGBoost score supplies the model ranking; seeded label-independent keys break score ties. The same keys are used for global model ranking. The full scores also use two other hazard grades, monitoring variables and shift type, so any increment is not an isolated sensor effect.

The separate protocol was saved before these calculations, after previous results had been inspected. It fixes seismic, the four original phases, budgets 1%, 5%, 10% and 20%, and the saved fixed-model scores. No model is trained, retuned or selected. The earlier Stage 2 whole-tie threshold rules remain unchanged; this pilot instead permits a grade group to be split to fill a hypothetical batch allocation.

For each phase, K=floor(B*N). Grade-random and grade-first ML receive identical k_g allocations, with E[TP_random]=sum_g k_g*P_g/N_g. Each expectation is calculated analytically rather than from one random draw. The saved hypergeometric allocation distribution describes random choice on this fixed queue; its spread is distinct from the block-bootstrap uncertainty interval.

The block analysis uses 2,000 paired moving-block draws of length 32 within phases. Every sampled queue is reallocated and reranked using frozen scores and the original label-independent tie keys, including duplicate copies. The random expectation is recomputed for each queue. Zero-positive draws are retained. Pooled results sum phase-specific allocations and detections; they never rank scores across separately fitted phase models. Intervals are unadjusted and exclude model-fitting and selection uncertainty.

## Phase results and pooled comparison

Table 1. Extra detections from grade-first ML relative to analytic grade-random expectation. Brackets are conditional 95% block intervals.

| Phase | Budget | K | Random E(TP) | Grade+ML TP | Extra TP [95%] |
| --- | --- | --- | --- | --- | --- |
| 1 | 1% | 5 | 0.87 | 0 | -0.87 [-1.39, 0.34] |
| 1 | 5% | 25 | 4.36 | 5 | 0.64 [-3.71, 2.99] |
| 1 | 10% | 51 | 8.90 | 11 | 2.10 [-3.87, 4.43] |
| 1 | 20% | 103 | 15.83 | 17 | 1.17 [-0.70, 5.68] |
| 2 | 1% | 5 | 0.23 | 0 | -0.23 [-0.40, -0.07] |
| 2 | 5% | 25 | 1.15 | 0 | -1.15 [-1.90, 0.43] |
| 2 | 10% | 51 | 2.35 | 0 | -2.35 [-3.26, 1.13] |
| 2 | 20% | 103 | 4.75 | 5 | 0.25 [-3.11, 1.63] |
| 3 | 1% | 5 | 0.22 | 0 | -0.22 [-0.35, 0.84] |
| 3 | 5% | 25 | 1.12 | 3 | 1.88 [-0.96, 4.31] |
| 3 | 10% | 51 | 2.28 | 4 | 1.72 [-0.99, 5.57] |
| 3 | 20% | 103 | 4.61 | 6 | 1.39 [-1.99, 4.58] |
| 4 | 1% | 5 | 0.14 | 1 | 0.86 [-0.24, 1.85] |
| 4 | 5% | 25 | 0.70 | 1 | 0.30 [-0.90, 3.01] |
| 4 | 10% | 51 | 1.43 | 2 | 0.57 [-1.64, 4.54] |
| 4 | 20% | 103 | 2.88 | 4 | 1.12 [-1.51, 4.86] |
| Pooled | 1% | 20 | 1.47 | 1 | -0.47 [-1.94, 1.09] |
| Pooled | 5% | 100 | 7.33 | 9 | 1.67 [-4.35, 5.43] |
| Pooled | 10% | 204 | 14.96 | 17 | 2.04 [-3.81, 9.31] |
| Pooled | 20% | 412 | 28.08 | 32 | 3.92 [-2.05, 9.86] |

Phase-specific intervals and counts are the primary evidence. The pooled point increment is negative at 1% and positive at the three larger budgets, while all pooled intervals include both improvement and decrease. Phase 2 at 1% instead has an increment of -0.23 [-0.40, -0.07], entirely below zero. Pooling does not erase that result. An interval spanning zero does not establish equivalence or exclude useful increments on another queue.

## Auxiliary ranking and interpretation

Table 2. Global model ranking on each phase, pooled afterwards. Extra TP is measured against the grade-random expectation, not against Grade+ML. This can change allocations between grades and does not isolate within-grade information.

| Budget | K | Grade+ML TP | Global ML TP | Global TP - grade-random E(TP) [95% CI] |
| --- | --- | --- | --- | --- |
| 1% | 20 | 1 | 0 | -1.47 [-2.01, 0.56] |
| 5% | 100 | 9 | 7 | -0.33 [-6.26, 4.53] |
| 10% | 204 | 17 | 14 | -0.96 [-6.80, 7.55] |
| 20% | 412 | 32 | 31 | 2.92 [-9.31, 13.11] |

The primary comparison holds grade-specific allocations fixed. The global comparison holds only total K fixed and therefore answers a different allocation question. Under the original hypothetical cost, L=r*P+K-(r+1)*TP. At fixed P and K, loss change is determined entirely by detection change; a second cost grid would not supply independent evidence.

These records are not verified simultaneously waiting inspection candidates. The pilot is retrospective batch ranking, not validation of real-time dispatch or accident prevention. Record order remains a temporal proxy. The present evidence does not establish a within-grade ranking increment or prove monitoring information useless. A source-attribution study would require matched grade-only and grade-plus-monitoring models, with shift type handled identically and equal fitting/tuning opportunities. That study has not been performed here.

## Code and evidence

The protocol and execution code are in phase2/ranking/. Results under results/phase2/ranking/ retain row-level decisions and random inclusion probabilities, allocations, evaluations, analytic allocation distributions and every block draw and reranked contrast. The verifier uses independent sorting, weighted-prefix reranking and SciPy hypergeometric probabilities. Author review and AI assistance follow the repository CONTRIBUTIONS.md statement; computational evidence comes from saved data and actual execution.
