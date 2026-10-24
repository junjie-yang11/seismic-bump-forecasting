# Monitoring information beyond hazard grades and shift type

This separately specified exploratory study asks whether adding monitoring variables increases expected hazardous-shift detections at the same inspection allocations. It preserves the original two-stage papers, experiments and ranking pilot.

The authoritative [protocol](protocol.json) was saved before these new fits and calculations, after the original test records had been inspected. It compares a four-column XGBoost design (`seismic`, `seismoacoustic`, `shift`, `ghazard`) with the existing ordered 17-column design. Both independently select parameters from the original four-configuration grid using the same temporal inner AP objective and fitting rows. The original policy-reference rows enter neither fitting nor tuning. No holdout, budget-specific tuning, new feature engineering or cost grid is added.

Within each of the four original test blocks, higher `seismic` grades receive priority and both models receive the same grade-specific quota and total `K=floor(B*N)`. At an exact score tie, the remaining slots are distributed uniformly. Evaluation integrates that allocation analytically for both designs: a tied group of size `m`, containing `p` hazardous records and receiving `h` slots, contributes `h*p/m` expected detections. Labels evaluate this rule; they never select records. Fractional E(TP) and E(FN) are expectations, while the allocated alert count K is an integer.

The contrast is **extended E(TP) minus base E(TP)**; positive favors the added monitoring design under this workflow. The main interval uses 2,000 paired moving-block draws of length 32. Lengths 16 and 64 are specified sensitivity checks. Every sampled multiset is reallocated and reranked, including recalculation of boundary-tie expectations. Zero-positive samples are retained. Pooled replicates sum corresponding phase replicates and never compare raw scores across separately fitted phase models. These unadjusted intervals condition on fitted scores and exclude full fitting, tuning and selection uncertainty.

Run from the repository root in the [research environment](../../docs/REPRODUCING.md):

```text
python -B -m unittest discover -s tests -p test_information.py -v
python -B -m phase2.information.run
python -B -m phase2.information.verify --refit
```

The last command independently reconstructs calculations and also reruns the model fits. Plain `python -B -m phase2.information.verify` loads and replays the saved models without retraining. Use a disposable copy for checks that write verification records; do not replace an existing full-refit certificate with a narrower check and describe it as full reproduction.

The [short report](../../reports/information/monitoring_information_increment.md) contains one phase-specific table, one increment/interval figure and a short interpretation. [Saved evidence](../../results/phase2/information/README.md) retains every planned comparison and its underlying scores, allocations and draws. The original [integrated manuscript](../../reports/overall/integrated_research_report.md) retains its previous scope. Recorded order remains a temporal proxy, and these hypothetical batches do not establish actual dispatch or intervention effects.
