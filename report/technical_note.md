# Cohort matched evaluation of seismic bump forecasting for mine warning decisions

Junjie Yang

Mining Engineering, Fuzhou University

Research code: https://github.com/junjie-yang11/seismic-bump-forecasting

## Abstract

Seismic warning evaluation must distinguish changes in the test population from changes in model behavior. We present an evaluation workflow that matches test records across validation protocols and connects discrimination, probability calibration and warning counts. On a 2,578-row mirror of the UCI Seismic Bumps dataset, evaluating both protocols on the same 2,063 records reduces the random-versus-record-order PR-AUC gap by 89.7 percent for logistic regression (LR) and 86.9 percent for bagged CART. The residual differences are 0.0114 and 0.0188, with paired moving-block bootstrap 95 percent intervals of [-0.0110, 0.0243] and [0.0064, 0.0323]. Training-fold prior correction reduces LR expected calibration error from 0.2904 to 0.0271 and Brier score from 0.1462 to 0.0439. A holdout evaluation then translates the fixed LR threshold into 8 alerts, 2 detected hazardous shifts and 24 missed hazardous shifts among 774 records. Together, these results establish test-cohort comparability as a prerequisite for interpreting validation gaps and show how calibration and threshold transfer require separate assessment. The gap reduction describes sensitivity to cohort composition; the intervals condition on fixed predictions. The workflow provides traceable evidence for evaluating mine-warning policies before prospective trials.

Keywords: mining engineering; seismic hazard; rare-event prediction; test-cohort shift; paired block bootstrap; probability calibration

## 1 Introduction

A mine-warning forecast has value when it supports a timely monitoring or inspection decision. For rare seismic hazards, evaluation must connect a model score to the hazardous shifts it detects and the workload its alerts create. The UCI Seismic Bumps target records an event above 10^4 J in the following shift [1]. This provides a concrete setting for studying early-warning evaluation: hazardous shifts comprise a small fraction of the records, and an always-negative predictor already achieves 93.41 percent accuracy.

Validation protocols are central to this assessment. Random splitting and validation along a record sequence admit different training histories [3,4], but they can also evaluate different test populations. A large PR-AUC gap may consequently reflect changes in which shifts are scored alongside changes in prediction behavior. Comparing the protocols on a common cohort makes this overlooked source of variation directly measurable.

We organize the analysis around this common test cohort and extend it to the decisions a warning model must support. The comparison measures how much of the apparent protocol gap changes when the test rows are matched; paired block resampling quantifies the residual difference. Training-fold prior correction then assesses the probability scale, while a fixed-threshold holdout expresses performance as detected events, missed events and alerts. The resulting contribution is an auditable evaluation workflow that links mine-monitoring records to warning consequences. Section 5.3 develops its transfer to UAV and mine-image validation.

## 2 Data provenance and engineering scope

### 2.1 Original dataset and mirror

The original UCI file has 2584 shifts from two Polish mine longwalls [1]. The CSV mirror documents removal of repeated rows [2]. A direct comparison of the downloaded ARFF and the local CSV confirms that keeping the first occurrence of each complete row reproduces all 2578 mirror rows in the same order. The six removed rows are exact duplicates and all have class 0; all 170 positive rows remain. Table 1 records the original one-based row IDs. File hashes, complete duplicate contents and the mirror-to-original row mapping are saved in source_audit.json, source_duplicates.csv and source_row_mapping.csv.

Table 1. Exact duplicate rows excluded by the mirror; row IDs refer to the original UCI data records, excluding the ARFF header.

| Removed row | Retained first row | Target class |
| --- | --- | --- |
| 90 | 88 | 0 |
| 91 | 89 | 0 |
| 973 | 971 | 0 |
| 974 | 972 | 0 |
| 1018 | 1016 | 0 |
| 1019 | 1017 | 0 |

The analysis uses this audited mirror throughout. Its version is reported explicitly so that comparisons can distinguish the 2,578-row cohort from published evaluations of the 2,584-row original. Row order serves as the temporal proxy; the file supplies no explicit timestamps or longwall identifiers.

### 2.2 Predictors and target

Each record summarizes one eight-hour shift. Predictor groups include mine hazard assessments, geophone energy and pulse measures, deviations from preceding-shift reference levels, bump counts by energy range, and total or maximum bump energy [1]. The target refers to the following shift. This measurement-to-target timing is essential when reconstructing a field prediction task. Ordinal categorical encoding and removal of total nbumps leave 17 input columns. Three retained bump-count columns are constant; constant-safe scaling and L2 regularization accommodate the resulting rank deficiency.

The first record-order block has a much larger positive proportion than later blocks (Figure 1). Random validation covers all 2,578 rows with prevalence 0.0659; the common later test cohort contains 88 positives among 2,063 rows, prevalence 0.0427. These are different evaluation populations, even when the underlying model family is unchanged.

![Figure 1. Hazard prevalence in five consecutive record blocks; row order is a proxy rather than verified clock time.](../results/figures/prevalence_drift.png)

## 3 Methods

### 3.1 Models and validation protocols

LR uses IRLS, L2 penalty 1.0, an unpenalized intercept and balanced class weights. Scaling is fitted on training rows only. The tree baseline uses 60 ordinary bootstrap CART trees, depth 6 and at least 20 observations per leaf, with unweighted Gini impurity and unweighted leaf probabilities. Hyperparameters are fixed across protocols, providing a controlled comparison of evaluation behavior for linear and nonlinear predictors.

Random stratified validation has ten folds and five seeds, 0 to 4. Every aggregate random metric is the mean of the five seed-specific metrics. Record-order validation divides the mirror into five consecutive blocks; four expanding windows train on earlier blocks and test the next one. The first block is training only. The final holdout trains on the first 70 percent and tests the last 774 rows. All test rows, including all-negative blocks, are retained. ROC-AUC is undefined for a single-class cohort; PR-AUC here means non-interpolated average precision, with ties grouped before integration.

### 3.2 Common test cohort and paired uncertainty

Random predictions for each seed are restricted to the exact 2,063 rows covered by record-order validation. The reported difference is the mean random average precision across five seeds minus the temporal average precision. The aggregation averages seed-specific metrics. Seeds describe sensitivity to fold assignment rather than independent sampling of mine populations.

The primary interval uses 2,000 paired moving-block bootstrap replicates, block length 32 records and fixed random generator seed 20261002. For every replicate, contiguous blocks are sampled with replacement separately within each of the four temporal test phases, preserving each phase size; the final block is truncated. The identical sampled row indices are applied to labels, all five random prediction vectors and the temporal vector. The statistic is recomputed on each resampled cohort, and its 2.5th and 97.5th percentiles form a conditional interval. Block lengths 16 and 64, plus phase-stratified paired IID resampling, are sensitivity checks. Resampling contiguous records preserves local dependence within blocks [5]. Models remain fixed during resampling, so the intervals describe test-cohort uncertainty conditional on the saved predictions. Section 5.2 sets out the scope of this analysis.

### 3.3 Warning thresholds and probability correction

Each outer training fold has an inner split: temporal folds reserve the latest 20 percent of training rows, while random folds reserve 20 percent within each class. An inner model scores these reference rows; its own training prevalence sets a reference alert budget. The boundary score and all its ties are excluded together so the reference count cannot exceed the integer budget. The outer model is refitted on its full training fold and evaluated using that fixed numerical threshold. Threshold selection is completed within training; the realized test alert rate is then measured as an outcome. The prevalence-based budget defines a reference operating point for studying threshold transfer.

For balanced-weight LR, a log-odds offset converts the effective training prior of 0.5 to each outer training fold's unweighted positive proportion. The transformation is applied fold by fold before pooling calibration predictions. CART is unweighted and receives no such correction. A correction with one fixed prior is monotone and preserves rankings within that fold; different corrections across folds can change the pooled ordering. The discrimination tables retain raw scores, separating the assessment of probability scale from the assessment of ranking.

Calibration uses Brier score, expected calibration error (ECE), maximum calibration error and reliability diagrams. Ten quantile bins are requested; repeated edges are merged and tied scores remain together. Reliability diagrams and Brier error complement the bin-dependent ECE. Brier skill uses an evaluation-prevalence constant predictor as a retrospective oracle reference.

## 4 Results

### 4.1 Test cohort matching reduces the apparent validation gap

Matching the test records reduces the absolute PR-AUC gap by 89.7 percent for LR and 86.9 percent for CART (Table 2). The random-model fits and predictions remain unchanged; their evaluation is restricted to the rows covered by record-order validation. The large reduction therefore demonstrates how strongly the apparent protocol gap depends on test composition, including prevalence and record difficulty.

Table 2. Absolute random-minus-record-order PR-AUC gaps before and after matching test rows; reduction is descriptive.

| Model | Different-cohort gap | Same-cohort gap | Gap reduction |
| --- | --- | --- | --- |
| LR | 0.1114 | 0.0114 | 89.7% |
| CART | 0.1433 | 0.0188 | 86.9% |

Table 3. Common-cohort average precision and primary paired 95 percent moving-block intervals (2,063 rows, 88 positives; block length 32). Differences use unrounded metrics.

| Model | Random mean AP | Record-order AP | Difference | 95% interval |
| --- | --- | --- | --- | --- |
| LR | 0.0953 | 0.0838 | 0.0114 | [-0.0110, 0.0243] |
| CART | 0.0972 | 0.0784 | 0.0188 | [0.0064, 0.0323] |

Across the five random fold assignments, the common-cohort AP difference ranges from 0.0088 to 0.0128 for LR and from 0.0169 to 0.0223 for CART. These ranges summarize split sensitivity alongside the paired test-cohort intervals.

The paired analysis distinguishes the residual behavior of the two model families (Figure 2). The LR interval spans zero, while the CART interval stays positive across the examined block lengths. The common cohort thus reveals a smaller and model-dependent protocol difference that the original pooled comparison obscured. An interval spanning zero leaves a range of residual differences compatible with the resampling analysis; it is not an equivalence test. The gap reduction measures cohort sensitivity, while remaining differences in training history and size preclude a causal leakage decomposition.

![Figure 2. Paired PR-AUC differences and 95 percent conditional intervals, with block lengths 16, 32 and 64; five random seeds are averaged in each replicate.](../results/figures/paired_ap_intervals.png)

![Figure 3. Precision-recall curves on the identical 2,063 test rows. The random curves use seed 0 for display; Tables 2 and 3 use five-seed mean metrics.](../results/figures/pr_same_test.png)

Figure 3 visualizes the common-cohort comparison at random seed 0. The shared positive proportion of 0.0427 supplies a consistent prevalence reference for interpreting both precision-recall curves; Table 3 and Figure 2 provide the aggregate estimates and their uncertainty.

### 4.2 Training priors improve probability calibration

Fold-local LR prior correction reduces ECE from 0.2904 to 0.0271 and Brier score from 0.1462 to 0.0439 (Table 4). Mean predicted probability falls from 0.3331 to 0.0694 against observed prevalence 0.0427. The correction brings the probability scale substantially closer to the observed event frequency using historical labels available to each training fold. Against the retrospective constant reference, corrected LR Brier skill is -0.0751 and unweighted CART Brier skill is -0.0607. These benchmark values quantify the remaining probability error alongside the improvement from the weighted LR output.

Table 4. Probability assessment on record-order test rows. Correction uses training priors, and only LR has a corrected variant.

| Model / variant | Brier | ECE | Mean forecast | Observed |
| --- | --- | --- | --- | --- |
| LR / raw | 0.1462 | 0.2904 | 0.3331 | 0.0427 |
| LR / fold prior | 0.0439 | 0.0271 | 0.0694 | 0.0427 |
| CART / raw | 0.0433 | 0.0374 | 0.0662 | 0.0427 |

![Figure 4. LR reliability diagrams on 2,063 rows. Both panels contain 10 quantile bins of 206-207 observations; marker size reflects count. Panel axes differ. Tied scores remain together and repeated edges are merged.](../results/figures/reliability_lr.png)

The reliability diagrams show how the training-prior correction redistributes forecasts toward the low-risk range (Figure 4). Each panel contains all 2,063 observations, with closely spaced low-probability bins appearing near the origin. Brier skill and the forecast-to-observation mean comparison retain a complementary assessment of the remaining probability error.

### 4.3 Warning counts expose threshold transfer behavior

Table 5 reports fixed-threshold holdout performance. For LR, 8 of 774 shifts are flagged, including 2 true positives and 6 false positives; 24 of 26 hazardous shifts are missed. Recall is 0.0769 and the alert rate is 0.0103. These counts translate the selected operating point into event detection and review workload, which overall accuracy does not resolve.

Table 5. Record-order holdout warning outcomes, using frozen numerical thresholds selected inside training.

| Model | Hazardous shifts | Alerts | Detected | Missed | Recall |
| --- | --- | --- | --- | --- | --- |
| LR | 26 | 8 | 2 | 24 | 0.0769 |
| CART | 26 | 6 | 1 | 25 | 0.0385 |

The historical reference budget becomes a fixed score cutoff, whose later alert rate depends on the score distribution. The holdout produces an LR alert rate of 0.0103, whereas pooled record-order testing produces 0.1832 at prevalence 0.0427. This variation establishes threshold transfer as an evaluation target in its own right. Lower event prevalence, feature shifts and refitting are candidate contributors to the change; the warning-count analysis measures the operating outcome without assigning it to a single mechanism.

## 5 Discussion

### 5.1 Implications for mine monitoring

The common-cohort analysis makes a large evaluation-population effect visible before interpreting protocol differences. The calibration experiment then identifies a practical adjustment to weighted LR probabilities, and the warning counts show what a frozen threshold means for a later set of shifts. Each result points to a distinct engineering decision: select a comparable evaluation cohort, assess the probability scale, and validate the alert policy at its intended operating point.

For mine monitoring, the decision unit and prediction lead time should be tied to a defined inspection or escalation action. Missed hazardous shifts, false alarms and inspection capacity provide the operational quantities for choosing a threshold using training or prospective validation data. Site records of face advance, work activity, sensor changes and monitoring coverage would help investigate score-distribution changes in a subsequent field study. This connects predictive evaluation to how monitoring teams allocate attention and investigate elevated seismic activity.

### 5.2 Scope and prospective validation

The results characterize the audited mirror under a record-order forecasting assumption. Timestamps and longwall identifiers would enable direct temporal and site-specific validation, while retaining the original 2,584 records would assess the effect of repeated measurements that may represent distinct shifts. The paired intervals quantify uncertainty conditional on fixed predictions and empirical test phases; they exclude model-refit uncertainty. Block lengths 16, 32 and 64 provide sensitivity checks around a chosen dependence scale, with coverage under nonstationary conditions requiring further assessment.

The next validation stage should combine matched training sizes with phase-level calibration and a prospectively frozen warning policy. The record-index probe and in-sample permutation importance, available in the supplementary result files, offer descriptive diagnostics for choosing which record structure and correlated monitoring features to investigate. This sequence extends the present evaluation to field conditions with defined data timing and warning actions.

### 5.3 Transferable lessons for UAV and mine-image data

For UAV and mine-image analysis, the same evaluation logic begins with an inspection target, such as locating a visible surface defect or mapping a feature for follow-up. Nearby frames, overlapping image tiles and repeated views of the same area should be grouped by flight, site and acquisition period for validation, since a random image split may put nearly identical views on both sides. Common test sites and periods would make protocol comparisons interpretable. Spatial resolution, image quality and annotation consistency would be audited as measurement conditions, while missed targets and review workload would be reported separately from recognition accuracy. These design principles define a subsequent image-data study with grouped validation and explicit inspection outcomes.

## 6 Conclusions

Cohort matching changes the interpretation of validation performance in this seismic forecasting study. Holding the test rows fixed removes most of the apparent random-versus-record-order PR-AUC gap and reveals a smaller, model-dependent residual difference. Training-fold prior correction substantially improves the LR probability scale, while fixed-threshold warning counts connect predictions to detected events and inspection workload. The contribution is an auditable workflow that makes test comparability, calibration and warning-policy transfer explicit before a prospective mine trial. It provides a concrete basis for designing mine-monitoring evaluations around the decisions their predictions must support.

## Data and code availability

Source data are available from UCI [1] and the CSV mirror [2]. The repository contains analysis code, row-level OOF predictions for all five random seeds, paired-bootstrap replicates, provenance hashes, fold audits and generated reports. Reproduction commands and the report-generation workflow are documented in the repository README. The analysis uses NumPy, pandas and Pillow, with all reported comparisons linked to saved predictions and result tables.

## References

[1] Sikora M, Wrobel L. Seismic Bumps [Dataset]. UCI Machine Learning Repository, 2010. DOI: 10.24432/C5W902. https://archive.ics.uci.edu/dataset/266/seismic+bumps

[2] datasets/seismic-bumps. CSV mirror and preparation description: repeated-row removal. https://github.com/datasets/seismic-bumps

[3] Bergmeir C, Benitez JM. On the use of cross-validation for time series predictor evaluation. Information Sciences, 2012, 191:192-213.

[4] Roberts DR et al. Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. Ecography, 2017, 40:913-929.

[5] Shalizi CR. Simulation for Inference I: The Bootstrap. Carnegie Mellon University course notes, 2018. https://stat.cmu.edu/~cshalizi/dst/18/lectures/18/lecture-18.html
