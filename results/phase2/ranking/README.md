# Ranking pilot evidence

These files belong to the [separately specified within-grade ranking pilot](../../../phase2/ranking/README.md), not to the original threshold-selection experiment. The [protocol](../../../phase2/ranking/protocol.json) fixes the analysis. The [short report](../../../reports/ranking/within_grade_ranking_pilot.pdf) summarizes the saved calculations.

| File | Content |
| --- | --- |
| `rows.csv` | 2,063 aligned mirror rows, labels, seismic grades, fixed XGBoost scores, seeded tie keys, model alerts and analytic random inclusion probabilities |
| `allocations.csv` | Phase/budget/grade allocation sizes and positive counts |
| `evaluations.csv` | 20 phase/pooled budget evaluations; both ML detection counts, analytic random expectations and increments |
| `intervals.csv` | 40 conditional intervals, covering primary grade-first and auxiliary global rankings |
| `random_allocation_distribution.csv` | Exact detection probabilities under uniform within-grade random allocation on the original queues; pooled distributions convolve the four phase distributions |
| `bootstrap_counts.npz` | Every sampled multiplicity vector for the paired, phase-stratified block draws |
| `bootstrap_replicates.npz` | All 80,000 reranked detection increments: five cohorts, four budgets, two comparisons and 2,000 draws |
| `run_manifest.json` | Actual inputs, source/code/output hashes, environment, settings, execution status and duration |
| `verification.json` | Actual independent numerical replay status and verification scope |

`row` and `fold` use zero-based mirror indices; report phase equals `fold + 1`. `fold = -1` means a sum over the four phases, without cross-phase ranking or capacity transfer. K is the sum of the phase allocations when pooled. Analytic expected detections can be fractional; observed model detections are integers.

The random-allocation distribution describes choosing records on a fixed queue. The block interval instead varies the evaluation queue and reranks it, holding the fitted scores fixed. Neither includes fitting, tuning or information-source uncertainty. These are different uncertainty objects and should not be substituted for each other.

Run `python -B -m phase2.ranking.verify` to independently reconstruct sorting, allocations, distributions, block draws, all increments and interval quantiles. Run the [report verifier](../../../reporting/verify_ranking.py) for generated document agreement. All generated verification flags describe the hashes and scope recorded in that invocation.
