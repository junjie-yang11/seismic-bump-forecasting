# Related work and contribution

This comparison positions the two studies as applied research and a reproducible evaluation framework. It separates established methods, the implementation in this repository and the empirical findings. It does not claim algorithmic priority or a validated operational optimum.

## 1 Mining hazard forecasts and evaluation cohorts

| Verified source | Task and data | Evaluation or decision method | Relation to this project | Evidence this project still needs |
| --- | --- | --- | --- | --- |
| [Sikora and Wrobel, UCI Seismic Bumps dataset](https://archive.ics.uci.edu/dataset/266/seismic+bumps), cited year 2010, DOI `10.24432/C5W902` | Public shift summaries; next-shift seismic bump above 10⁴ J; 2,584 source rows | Official label and variable definitions; no public timestamps or working-face identifiers | Defines our target; the audited 2,578-row mirror retains first-occurrence order | Dated shifts, working-face identity and inspection outcomes for operational validation |
| [Sikora and Wrobel, 2010, Archives of Mining Sciences 55(1):91–114](https://www.researchgate.net/publication/281395657_Application_of_rule_induction_algorithms_for_analysis_of_data_collected_by_seismic_hazard_monitoring_systems_in_coal_mines) | Hestia longwall monitoring; shift/hour horizons and an energy-based hazardous-state definition | Rule induction/filtering; shift experiments use five-fold CV and transfer between longwalls | Establishes earlier mining prediction and site-transfer work; its labels and cohorts differ from UCI | Working-face identifiers needed to reproduce a cross-face test; published accuracy cannot be ranked against our AP |

The mining paper's full text is linked from the [authors' project bibliography](https://github.com/ruleminer/ruleminer#publications); its bibliographic details are also recorded by [Silesian University of Technology](https://omega.polsl.pl/info/article/PSLa52fdf78c23940d99f66a621ab498fc8/). Sections 4.1 and Table 3 support the validation description. No DOI was verified for that paper, so none is supplied. The dataset's DOI identifies the dataset, not this article. UCI displays a 2013 donation date and a 2010 citation year; these describe different metadata fields.

The first-stage contribution is the common-row protocol comparison together with probability references and the distinction between fitted-model feature use and incremental predictive value. It is not a direct replication of the original mining paper or a cross-study performance ranking.

## 2 Error costs and inspection capacity

| Verified source | Task and data | Evaluation or decision method | Relation to this project | Evidence this project still needs |
| --- | --- | --- | --- | --- |
| [Elkan, 2001, The Foundations of Cost-Sensitive Learning](https://cseweb.ucsd.edu/~elkan/rescale.pdf), IJCAI:973–978 | Binary decisions with unequal error costs; general decision theory | Derives cost-based decisions and discusses empirical threshold adjustment | Motivates `r FN + FP`; A/B/C search observed whole-score alert sets, with C adding a reference-capacity constraint | Measured intervention costs and inspection effectiveness; assumed `r` does not supply either |

Under a calibrated posterior and zero cost for correct classifications, expected costs are `1-p` for an alert and `r*p` for no alert. Thus an alert can be optimal when `p >= 1/(r+1)`; equality permits either decision. The repository does not assume raw scores satisfy that calibration: B/C minimize empirical reference loss over canonical cutoffs and favor fewer alerts on equal loss. C adds a historical capacity constraint. The contribution here is the joint account of selection rationale, transferred loss and inspection demand. Historical feasibility does not guarantee future feasibility.

## 3 Threshold transfer and distribution changes

| Verified source | Task and data | Evaluation or decision method | Relation to this project | Evidence this project still needs |
| --- | --- | --- | --- | --- |
| [Roberts et al., 2017, Ecography 40:913–929](https://doi.org/10.1111/ecog.02881), DOI `10.1111/ecog.02881` | Structured ecological observations and simulated/case-study validation | Discusses blocked validation, dependence and interpolation versus extrapolation | Supports matching evaluation design to the prediction setting; our common test rows control cohort membership, not all training differences | Independent temporal/site validation rather than treating row blocks as confirmed operational time |
| [Lipton, Wang and Smola, 2018, ICML, PMLR 80:3122–3130](https://proceedings.mlr.press/v80/lipton18a.html) | Label shift, with changing class prevalence and fixed class-conditional distributions | Black Box Shift Estimation and correction; full method in the [paper](https://proceedings.mlr.press/v80/lipton18a/lipton18a.pdf) | Defines the assumption behind our frozen prevalence scenarios; we do not implement BBSE or estimate actual shift | Evidence that class-conditional behavior remains stable; observed prevalence differences alone do not establish it |
| [Künsch, 1989, The Annals of Statistics 17(3):1217–1241](https://doi.org/10.1214/aos/1176347265), DOI `10.1214/aos/1176347265` | Dependent stationary observations | Block resampling for dependent data | Method origin for paired block uncertainty; this repository resamples within record stages and conditions on fitted rules | Full fitting/selection uncertainty and evidence supporting the relevant dependence assumptions |

Fixed-model transfer and refitted-model transfer are separate workflows. A retained numerical cutoff may acquire a different workload when the model is refitted. Neither contrast identifies a causal refitting effect. Likewise, the prevalence-only scenarios calculate expected loss and workload under a stated assumption; they do not diagnose the observed transfer mechanism or estimate capacity-excess probability.

## What is adopted and what is contributed

| Layer | Established component | Repository contribution |
| --- | --- | --- |
| Forecasting | LR, bagged CART, [XGBoost](https://doi.org/10.1145/2939672.2939785) | Training-local implementation, common-row evidence and transparent asymmetric configurations |
| Explanation | [TreeSHAP](https://doi.org/10.1038/s42256-019-0138-9) | Paired interpretation of model feature use and refitted engineering-group ablations |
| Decisions | Error-cost loss, empirical cutoffs, capacity limits | Reference/test separation, canonical tie rules, no-alarm accounting and matched fixed/refitted comparisons |
| Uncertainty | Block resampling | Conditional paired intervals and saved replicates for independent reconstruction |

Sources were checked against official documentation, full papers or author publication records for this release. The comparison is focused rather than an exhaustive systematic review; the [source-check record](audits/RESEARCH_PRESENTATION_SOURCES.json) identifies bibliographic-only checks and full-text access limits. No published performance number is used to infer a predictability ceiling for the public dataset.

[Research overview](PROJECT_OVERVIEW.md) · [Stage 1 paper](../reports/phase1/technical_report.pdf) · [Stage 2 paper](../reports/phase2/phase2_threshold_transfer_report.pdf)
