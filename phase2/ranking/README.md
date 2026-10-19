# Within-grade ranking at equal capacity

This separately specified exploratory pilot asks whether saved complete-model scores improve ranking **within the same seismic grade**, at identical total and grade-specific inspection allocations. It does not refit models or change the locked Stage 2 threshold experiment. Read the [protocol](protocol.json) before the [short report](../../reports/ranking/within_grade_ranking_pilot.pdf).

The protocol was saved before these calculations, after earlier project results had been inspected. It is a retrospective analysis specification, not a preregistration. It fixes `seismic`, the four original test phases, fixed XGBoost scores and budgets 1%, 5%, 10% and 20%. The observed grades are a and b; their priority follows the source's increasing hazard order.

Each phase receives `K = floor(budget * N)` alerts. Grade-first ML and the grade-random comparator receive exactly the same number from each grade. Random selection is represented by its analytic expected detections, `sum(k_g * P_g / N_g)`, and its complete hypergeometric allocation distribution. No single random realization is used as the baseline. Global score ranking is an auxiliary comparison that can change grade allocations. Label-independent seeded keys break model-score ties.

The 2,000 paired length-32 block draws preserve phase boundaries. Every sampled queue is reallocated and reranked; resampling old alert flags would not preserve the capacity constraint. The random expectation is also recomputed in each draw. The block intervals condition on the saved fitted models and existing cohort. Random allocation variability on a fixed queue is saved separately and is not the bootstrap interval.

## Execute and check

From the repository root, use the existing research environment:

```text
python -B -m unittest tests.test_ranking_pilot -v
python -B -m phase2.ranking.run
python -B -m phase2.ranking.verify
```

The runner writes only `results/phase2/ranking/`. It checks the source mirror against the original model-run hash and aligns every saved score, label and grade by mirror row. The verifier independently sorts records, reconstructs allocations and uses weighted-prefix ranking to replay every block draw and contrast. Its second implementation of random-allocation probabilities uses [SciPy's hypergeometric distribution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.hypergeom.html). Failed runs/checks revoke old success records.

Use the separate reporting environment for document generation and PDF text checks:

```text
python -B -m reporting.ranking
pwsh -NoProfile -ExecutionPolicy Bypass -File reporting/export_overall.ps1 -ReportDirectory ranking -Stem within_grade_ranking_pilot
python -B -m reporting.verify_ranking --pdf
```

Word export requires Microsoft Word on Windows. Inspect rendered PDF pages as well as the computational checks. [Quick Check](../../docs/QUICK_CHECK.md) runs the numerical and document verifiers in a disposable copy.

## Interpretation

Pooled counts sum phase-specific allocations and detections; scores from different phase models are never ranked together. At fixed positive count P and alert count K, `L = r*P + K - (r+1)*TP`, so detection and assumed-cost changes are algebraically linked.

The complete score uses other hazard grades, monitoring variables and shift type. This pilot cannot attribute an increment specifically to sensors. A matched information-source comparison is future work. The records are not established simultaneous inspection candidates: this is retrospective batch ranking, not an operational dispatch evaluation. All settings are retained, including negative increments and intervals spanning zero.

[Evidence guide](../../results/phase2/ranking/README.md) · [Integrated study](../../reports/overall/integrated_research_report.pdf) · [Locked threshold study](../README.md)
