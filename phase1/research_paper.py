"""Extended scientific paper, generated from saved experiment evidence."""
import csv
import json


def build_paper(root):
    def read(name):
        with (root / 'results/phase1' / name).open(encoding='utf-8', newline='') as f:
            return list(csv.DictReader(f))
    def number(x): return '%.4f' % float(x)
    def integer(x): return str(int(float(x)))
    def interval(lo, hi): return '[%s, %s]' % (number(lo), number(hi))
    def table(headers, rows):
        return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
                         + ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])
    models = ('LR', 'CART', 'XGBoost')
    ab = read('feature_ablation.csv'); ci = read('feature_ablation_intervals.csv')
    budget = read('warning_budgets.csv'); stability = read('shap_stability.csv')
    importance = read('shap_importance.csv'); cases = read('shap_cases.csv')
    phase = read('feature_ablation_by_fold.csv'); cal = read('calibration.csv')
    config = json.loads((root / 'results/phase1/research_config.json').read_text(encoding='utf-8'))
    integrity = json.loads((root / 'results/phase1/integrity.json').read_text(encoding='utf-8'))
    gaps = read('gap_attenuation.csv'); shared = read('shared_test_comparison.csv')
    old_ci = read('paired_uncertainty.csv'); new_ci = read('xgboost_protocol_interval.csv')[0]
    new_random = read('xgboost_shared_by_seed.csv')
    full = {m: next(r for r in ab if r['model'] == m and r['variant'] == 'full') for m in models}
    rating = {m: next(r for r in ab if r['model'] == m and r['variant'] == 'ratings_only') for m in models}
    rating_ci = {m: next(r for r in ci if r['model'] == m and r['variant'] == 'ratings_only') for m in models}
    global_shap = sorted([r for r in importance if r['validation'] == 'time' and int(r['fold']) == -1], key=lambda r: -float(r['mean_abs']))
    correlations = [float(r['rank_spearman']) for r in stability]
    overlaps = [float(r['top5_jaccard']) for r in stability]
    selected_budget = lambda m, b, v='holdout': next(r for r in budget if r['model'] == m and r['validation'] == v and abs(float(r['budget']) - b) < 1e-8)
    ten, twenty = selected_budget('XGBoost', .1), selected_budget('XGBoost', .2)
    raw = next(r for r in cal if r['model'] == 'LR' and r['variant'].startswith('as'))
    corrected = next(r for r in cal if r['model'] == 'LR' and r['variant'].startswith('after'))
    differences = read('research_model_intervals.csv')
    sensitivity = read('shap_stability_sensitivity.csv')
    nonconstant = [float(r['rank_spearman']) for r in sensitivity if r['scope'] == 'nonconstant_features']
    reference = read('probability_reference_comparison.csv')
    historical = {m: next(r for r in reference if r['model'] == m and r['validation'] == 'time' and int(r['fold']) == -1) for m in models}
    phase_contrast = read('feature_ablation_phase_contrasts.csv')
    xgb_phase = sorted([r for r in phase_contrast if r['model'] == 'XGBoost'], key=lambda r: int(r['fold']))
    seismic_removed = next(r for r in ab if r['model'] == 'XGBoost' and r['variant'] == 'without_seismic_activity')
    seismic_interval = next(r for r in ci if r['model'] == 'XGBoost' and r['variant'] == 'without_seismic_activity')
    labels = {'full': 'All features', 'ratings_only': 'Hazard ratings only', 'without_ratings': 'Without hazard ratings',
        'geophone_only': 'Geophone only', 'without_geophone': 'Without geophone',
        'seismic_activity_only': 'Seismic activity only', 'without_seismic_activity': 'Without seismic activity',
        'operation_only': 'Shift type only', 'without_operation': 'Without shift type'}
    protocol_rows = []
    for m in models:
        if m == 'XGBoost':
            random_ap = sum(float(r['random_ap']) for r in new_random) / 5
            result = new_ci
        else:
            r = next(r for r in shared if ('logistic' in r['model']) == (m == 'LR'))
            random_ap = float(r['random_pr_auc'])
            result = next(r for r in old_ci if r['model'] == m and int(r['block_length']) == 32)
        protocol_rows.append([m, number(random_ap), number(full[m]['pr_auc']), number(result['delta']), interval(result['ci_low'], result['ci_high'])])
    out = [
        '# Evaluating reliability and explainability in seismic hazard forecasting for underground mine monitoring',
        'Junjie Yang',
        'Mining Engineering, Fuzhou University',
        'Research code: https://github.com/junjie-yang11/seismic-bump-forecasting',
        '## Abstract',
        'Test-cohort composition materially changes the apparent validation gap in seismic hazard forecasting. '
        'We evaluate logistic regression (LR), bagged CART and training-tuned XGBoost on 2,063 common test rows from the 2,578-row UCI Seismic Bumps mirror. Record order serves as a temporal proxy because timestamps and longwall identifiers are absent. '
        'Matching test rows reduces the apparent random-versus-record-order average-precision gap by %.1f percent for LR and %.1f percent for CART. Residual differences are %s (95 percent interval %s) and %s (%s), respectively. These changes quantify sensitivity to evaluation-cohort composition. '
        'Training-prior correction improves LR expected calibration error from %s to %s and Brier score from %s to %s. '
        'Corrected LR Brier skill is %s against the historical training-prior reference and %s against the retrospective test-prevalence reference. '
        'Nine prespecified feature combinations assess the predictive information in hazard ratings, geophone signals, seismic activity and shift type. '
        'Exact TreeSHAP identifies total seismic energy, low-energy event counts and pulse activity as recurring contributors to XGBoost predictions; '
        'comparison with refitted feature ablations distinguishes model reliance from incremental predictive value. '
        'At training reference budgets of 10 and 20 percent, supplementary holdout XGBoost produces %s and %s alerts and detects %s and %s of 26 hazardous shifts. '
        'The results distinguish three properties needed for engineering interpretation: performance on comparable shifts, the probability scale of the forecasts and the detection workload of a warning rule. Paired intervals describe uncertainty conditional on fixed predictions.'
        % (100 * float(gaps[0]['gap_reduction_fraction']), 100 * float(gaps[1]['gap_reduction_fraction']),
           protocol_rows[0][3], protocol_rows[0][4], protocol_rows[1][3], protocol_rows[1][4],
           number(raw['ece']), number(corrected['ece']), number(raw['brier']), number(corrected['brier']),
           number(historical['LR']['historical_skill']), number(historical['LR']['oracle_skill']),
           integer(ten['alerts']), integer(twenty['alerts']), integer(ten['tp']), integer(twenty['tp'])),
        'Keywords: mining engineering; seismic hazard forecasting; engineering feature ablation; TreeSHAP; explanation stability; warning budget',
        '## 1 Introduction',
        'Underground mine monitoring records rock-mass activity to support the assessment of hazardous conditions. '
        'Interpreting a forecast for engineering review requires evidence about its performance on later shifts, the monitoring signals it uses and the inspections its warnings would trigger. '
        'These questions connect model evaluation to detected hazards, missed hazardous shifts and false-alert workload.',
        'The UCI Seismic Bumps data provide a defined next-shift forecasting task: each record summarizes an eight-hour shift, '
        'and the target indicates whether the following shift contains a seismic event above 10,000 J [1]. Existing seismic and seismoacoustic hazard ratings '
        'appear alongside energy, pulse and event-count measurements. Their coexistence makes the additional predictive information in measured signals testable against the recorded assessments. '
        'The target is next-shift high-energy seismic occurrence; confirmed rockburst accidents are outside its label definition.',
        'Rule-based mining-hazard prediction predates this study. Sikora and Wrobel [9] evaluated shift and hourly forecasts using longwall-specific monitoring data and also transferred rules between working faces. '
        'Their hazard definition and cohorts differ from the public UCI task, so their classification results provide engineering context rather than a numerical benchmark for our average precision.',
        'Validation protocols can change both the training history and the test population [3,4]. Comparing their scores on different shifts can therefore obscure the source of an apparent performance gap. '
        'A common test cohort makes that comparison interpretable, while probability assessment determines what the score scale conveys. '
        'Feature ablation, model explanations and frozen thresholds then connect the monitoring inputs to predictive contribution and warning workload.',
        'The contribution is an applied evaluation framework connecting comparable test records, probability assessment and engineering interpretation. '
        'Common test rows reveal how cohort composition changes the apparent protocol gap. Training-local correction and explicit probability references separate calibration improvement from baseline-relative skill. '
        'TreeSHAP and nine prespecified, refitted feature combinations distinguish the inputs used by a fitted model from their incremental predictive value. '
        'Frozen reference budgets then express the forecasts as detections, missed hazardous shifts and inspection workload. These empirical findings use established learning and explanation methods [6,7], saved row-level evidence and training-only selection.',
        '## 2 Data and engineering feature hypotheses',
        '### 2.1 Dataset and provenance',
        'The original UCI dataset contains 2,584 records from two longwalls of a Polish coal mine, with 170 positive target records [1]. '
        'The positive count refers to labelled shift records, rather than a catalogue of 170 independently identified seismic events. '
        'The CSV mirror retains 2,578 records [2]. A direct ARFF-to-CSV audit confirms first-occurrence deduplication without reordering: '
        'six excluded original rows, 90, 91, 973, 974, 1018 and 1019, are exact duplicate negatives. All positive records remain. '
        'The content-identical first-occurrence records retained for these rows have original IDs 88, 89, 971, 972, 1016 and 1017, respectively. '
        'These IDs are one-based data-row numbers excluding the ARFF header.',
        'Row order is used as the temporal proxy because explicit timestamps and longwall identifiers are absent. '
        'The initial training block contains %.2f percent positive records, compared with %s percent in the four subsequent test phases. '
        'Exact phase counts and prevalence are provided in Table 7. The full dataset prevalence is 6.59 percent, whereas the common test cohort has 88 positives '
        'among 2,063 records, or 4.27 percent. These differences motivate both matched evaluation and phase-specific analysis.'
        % (100 * (integrity['n_positive'] - int(full['LR']['positives'])) / (integrity['n_rows'] - int(full['LR']['n'])),
           ', '.join('%.2f' % (100 * float(next(r for r in phase if r['model'] == 'LR' and r['variant'] == 'full' and int(r['fold']) == f)['prevalence'])) for f in range(4))),
        '### 2.2 Engineering feature groups',
        'Table 1 partitions the existing 17-column design into four engineering groups. The three hazard-rating variables encode recorded assessments, '
        'while the geophone and seismic-activity groups contain monitoring measurements. Shift type describes preparation or coal-getting activity. '
        'These groups define comparisons between existing hazard assessments and the measured signals available to a forecasting model.',
        'Table 1. Engineering feature groups and the predictive hypotheses examined.',
        table(['Group', 'Variables', 'Question'], [
            ['Hazard ratings', 'seismic, seismoacoustic, ghazard', 'How much information is already represented by recorded assessments?'],
            ['Geophone', 'genergy, gpuls, gdenergy, gdpuls', 'Do energy, pulse activity and deviations add information beyond ratings?'],
            ['Seismic activity', 'nbumps2 to nbumps89, energy, maxenergy', 'Do event counts by energy band and released-energy measures add information?'],
            ['Operation', 'shift', 'Does shift type provide predictive context?']]),
        'Categorical fields retain the existing ordinal encoding. The total count nbumps is excluded from the retained 17-column design, which includes the energy-band counts. '
        'Constant energy-band columns remain in the audited design. LR uses constant-safe training standardization and L2 regularization. '
        'The design uses the supplied shift summaries; constructing cross-shift lag features would require known longwall continuity.',
        '## 3 Methods',
        '### 3.1 Common test cohort and model comparison',
        'Record-order evaluation divides the mirror into five consecutive blocks. Four expanding-window fits train on earlier blocks and predict the next block; '
        'the first block supplies training only. Every model and feature combination therefore evaluates the same 2,063 rows. '
        'A supplementary holdout trains on the first 70 percent and evaluates the last 774 records, containing 26 positive targets. '
        'This holdout was inspected in the earlier project, so it is reported as descriptive supplementary evidence and is not used to select a feature set, model or budget.',
        'LR retains L2 penalty 1.0, an unpenalized intercept and balanced class weights. Bagged CART retains 60 ordinary bootstrap trees, maximum depth 6, '
        'minimum leaf size 20, unweighted Gini and forest seed 7. XGBoost uses unweighted binary logistic loss and histogram trees, learning rate 0.05, '
        'minimum child weight 10 and L2 penalty 5.0, with full row and column sampling, seed 7 and two CPU threads [6]. '
        'Its fixed candidate grid combines depth 2 or 3 with 80 or 160 boosting rounds.',
        'Each XGBoost search uses only its supplied training rows: the final 20 percent forms an inner reference, '
        'and candidates are fitted on the preceding 80 percent. Selection maximizes tied-score average precision (AP), '
        'with negative Brier score as the predefined fallback for a zero-positive reference; the first grid entry wins exact ties. '
        'The selected model is refitted on the entire supplied training set. Threshold-reference models conduct their own search within the earlier inner-fit prefix. '
        'For feature ablations, full-feature training selects parameters once per fold and the same choices are used for all nine feature combinations.',
        'The random protocol uses ten stratified folds and five seeds, 0 to 4. XGBoost selects parameters through a stratified inner split within each outer training fold. '
        'Random predictions are restricted to the record-order test cohort before calculating comparative metrics. '
        'Reported random AP is the mean of five seed-specific AP values, rather than AP after averaging scores. '
        'LR and CART retain fixed settings; XGBoost is training-tuned. Comparisons characterize these stated workflows rather than equally extensive searches for every model.',
        '### 3.2 Feature comparisons and conditional uncertainty',
        'The prespecified feature sets are the full design, each group alone and the design with each group removed. '
        'They are all reported, without choosing a final feature set from test outcomes. '
        'The full-versus-ratings-only contrast addresses the additional predictive information in monitoring measurements and shift type. '
        'Group-removal contrasts assess predictive dependence on information groups in the presence of correlated alternatives.',
        'AP is the main ranking measure and groups tied scores before integration. ROC-AUC, Brier score and ten-quantile-bin expected calibration error (ECE) '
        'provide complementary discrimination and probability assessments. LR probability assessment uses each outer training fold\'s unweighted prior to correct its balanced-weight output; '
        'CART and XGBoost are assessed as fitted. No test-label prior is used in forecasting or calibration.',
        'Paired moving-block intervals use 2,000 replicates, block length 32 and RNG seed 20261002. '
        'Contiguous blocks are sampled separately within each test phase, preserving phase sizes and applying identical sampled rows to every compared score vector. '
        'Intervals are the 2.5th and 97.5th percentiles of paired AP differences and condition on fixed predictions. '
        'Random-protocol differences average the five seed-specific AP values within each replicate. The earlier LR/CART protocol analysis also checks lengths 16 and 64. '
        'The intervals are descriptive, unadjusted for multiple feature contrasts, and exclude model-refit and parameter-selection uncertainty [5].',
        '### 3.3 Explanations and phase stability',
        'Full-feature XGBoost models explain their own outer-test predictions through native exact TreeSHAP, using the training-derived leaf covers '
        'as the tree-path-dependent reference [7,8]. Each row has 17 feature contributions and a bias term. '
        'Their sum reconstructs the raw log-odds margin; applying the logistic function reconstructs the predicted probability. '
        'Contributions are additive on the model\'s log-odds scale and describe fitted predictive associations.',
        'Global importance is mean absolute contribution on the common test cohort. Each phase also has its own importance ranks. '
        'Pairwise Spearman correlations compare the ranks of all 17 features, with average ranks for ties; top-five Jaccard overlap measures agreement in leading features. '
        'A fixed feature-name order resolves ties at the top-five boundary. Value-contribution Spearman associations and scatter plots describe how observed values relate to contributions. '
        'Together, the rank and overlap measures characterize recurring feature use and changes among leading inputs.',
        'Illustrative cases use the earliest record in each true-positive, false-positive and false-negative category under the predeclared 10 percent training reference budget. '
        'Case selection is a post-evaluation explanation step, independent of model and threshold selection.',
        '### 3.4 Training reference budgets and warning outcomes',
        'The reference budgets are fixed at 1, 5, 10 and 20 percent. For each outer fold, an inner model predicts the last 20 percent of the training history. '
        'The threshold excludes the boundary score and all tied scores together, so at most floor(reference size times budget) reference records are flagged. '
        'After outer refitting, the numerical threshold is frozen and evaluated on future test records. All budgets use the same model scores; no test labels enter threshold selection.',
        'For LR, both threshold selection and alert classification use raw weighted-model scores. Prior-corrected probabilities are used separately for probability assessment. '
        'The inner and outer models are distinct fits, so refitting can alter raw-score distributions and the transferred alert rate even though the probability scales are not mixed. '
        'A frozen-inner-model comparison would isolate this refitting contribution from temporal distribution changes.',
        'Reference budgets are experimental workload scenarios, not established operating limits for a mine. '
        'The future actual alert rate is measured separately because refitting and changing score distributions can alter it. '
        'Warning outcomes include true detections, false alerts, missed hazardous shifts, precision and recall. '
        'The target and available labels measure shift-level detections, not event counts, spatial warning coverage or avoided accidents.',
        '## 4 Predictive contribution of monitoring information',
        '### 4.1 Cohort sensitivity and matched model comparison',
        'Table 2 compares validation protocols on identical test records. Full-feature XGBoost record-order AP is %s, compared with %s for LR and %s for CART. '
        'The XGBoost-minus-LR paired difference is %s with interval %s, and the XGBoost-minus-CART difference is %s with interval %s. '
        'These paired comparisons establish the model context for the monitoring-information and warning-policy analyses below.'
        % (number(full['XGBoost']['pr_auc']), number(full['LR']['pr_auc']), number(full['CART']['pr_auc']),
           number(differences[0]['delta']), interval(differences[0]['ci_low'], differences[0]['ci_high']),
           number(differences[1]['delta']), interval(differences[1]['ci_low'], differences[1]['ci_high'])),
        'Table 2. AP on identical 2,063 test rows and paired random-minus-record-order intervals; random values average five seeds.',
        table(['Model', 'Random AP', 'Record-order AP', 'Difference', '95% interval'], protocol_rows),
        'Table 2 note. LR uses balanced class weights, bagged CART is unweighted, and XGBoost is unweighted with an additional training-only parameter search. '
        'This is a comparison of stated workflows with asymmetric weighting and tuning. The CART and XGBoost protocol intervals exclude zero; the LR interval includes zero.',
        'Matching test rows reduces the original different-cohort AP gap by %.1f percent for LR and %.1f percent for CART. '
        'The size of this change establishes test-cohort composition as a material part of protocol comparison. '
        'It measures evaluation-population sensitivity; the remaining differences combine training history, training size and, for XGBoost, training-selected configurations, '
        'so the reduction is not a causal decomposition of leakage or drift.'
        % (100 * float(gaps[0]['gap_reduction_fraction']), 100 * float(gaps[1]['gap_reduction_fraction'])),
        '### 4.2 Engineering feature comparisons',
        'Table 3 reports every prespecified feature set. Hazard ratings alone yield AP %s, %s and %s for LR, CART and XGBoost. '
        'The full-feature gains are %s, %s and %s, respectively (Table 4). '
        'Paired intervals in Table 4 include zero for all three gains. The comparisons quantify the observed contribution of measured signals and its conditional uncertainty.'
        % (number(rating['LR']['pr_auc']), number(rating['CART']['pr_auc']), number(rating['XGBoost']['pr_auc']),
           number(-float(rating_ci['LR']['delta'])), number(-float(rating_ci['CART']['delta'])), number(-float(rating_ci['XGBoost']['delta']))),
        'Table 3. Engineering feature ablations on the common record-order cohort; entries are AP. All three models use the same columns per row.',
        table(['Feature set', 'Columns', 'LR', 'CART', 'XGBoost'],
              [[labels[v], len(config['variants'][v])] + [number(next(r for r in ab if r['model'] == m and r['variant'] == v)['pr_auc']) for m in models] for v in labels]),
        'Table 4. Full-feature AP minus hazard-ratings-only AP with conditional paired 95 percent intervals.',
        table(['Model', 'Incremental AP', '95% interval'], [[m, number(-float(rating_ci[m]['delta'])),
            interval(-float(rating_ci[m]['ci_high']), -float(rating_ci[m]['ci_low']))] for m in models]),
        'The geophone-only XGBoost achieves AP %s, while removal of the seismic-activity group gives %s. '
        'The latter differs from the full model by %s with interval %s. '
        'Together with the LR and CART contrasts, these results show that predictive use of a monitoring group depends on the other available inputs and fitted model. '
        'The comparisons hold XGBoost settings fixed within each fold, assessing the sensitivity of that design to information sources. '
        'Redundancy, estimation variability and changing phase distributions are candidate explanations for the observed patterns; they are not separately identified here.'
        % (number(next(r for r in ab if r['model'] == 'XGBoost' and r['variant'] == 'geophone_only')['pr_auc']),
           number(next(r for r in ab if r['model'] == 'XGBoost' and r['variant'] == 'without_seismic_activity')['pr_auc']),
           number(next(r for r in ci if r['model'] == 'XGBoost' and r['variant'] == 'without_seismic_activity')['delta']),
           interval(next(r for r in ci if r['model'] == 'XGBoost' and r['variant'] == 'without_seismic_activity')['ci_low'],
                    next(r for r in ci if r['model'] == 'XGBoost' and r['variant'] == 'without_seismic_activity')['ci_high'])),
        '### 4.3 Calibration improvement and reference choice',
        'Training-prior correction improves LR ECE from %s to %s and Brier score from %s to %s, providing a direct adjustment to the probability scale using historical labels. '
        'Corrected LR, raw CART and raw XGBoost Brier scores are %s, %s and %s. '
        'Corrected LR Brier skill against a retrospective evaluation-prevalence constant is %s. '
        'The constant is an oracle reference used for assessment, with no role in generating forecasts. '
        'Table 5 also compares each model with a deployable historical reference: every test row receives the unweighted prevalence of its outer training fold. '
        'Corrected LR has Brier skill %s against this historical reference. ECE improvement compares LR before and after correction, while skill compares its squared error with a stated reference; the two assessments therefore answer different questions.'
        % (number(raw['ece']), number(corrected['ece']), number(raw['brier']), number(corrected['brier']),
           number(full['LR']['brier']), number(full['CART']['brier']), number(full['XGBoost']['brier']), number(corrected['brier_skill']),
           number(historical['LR']['historical_skill'])),
        'Table 5. Probability assessment on the common test cohort. LR uses corrected probabilities; CART and XGBoost use raw probabilities. Historical references are frozen within training; oracle references use the evaluation prevalence for retrospective assessment.',
        table(['Model', 'Model Brier', 'Historical Brier', 'Historical skill', 'Oracle Brier', 'Oracle skill'],
              [[m] + [number(historical[m][k]) for k in ('model_brier', 'historical_brier', 'historical_skill', 'oracle_brier', 'oracle_skill')] for m in models]),
        '![Figure 1. LR calibration on the common test cohort. Each panel contains 10 quantile bins of 206 or 207 observations; ties stay together, marker sizes encode counts, and panel axes differ.](../../results/phase1/figures/reliability_lr.png)',
        '## 5 Model explanations and phase stability',
        '### 5.1 Global and stage-specific feature use',
        'Total seismic energy, low-energy event count nbumps2 and pulse count gpuls have the largest mean absolute XGBoost contributions. '
        'These are observable indicators of seismic and geophone activity; their importance describes how the fitted models use monitoring information. '
        'Table 6 reports the leading contributions and value associations. Read alongside the ablations, these explanations distinguish a model\'s reliance on a signal from the incremental value of its monitoring group.',
        'Table 6. Leading full-feature XGBoost contributions on 2,063 test rows. Magnitudes are in raw log-odds units; correlations are descriptive value-contribution associations.',
        table(['Feature', 'Mean absolute contribution', 'Value association'], [[r['feature'], number(r['mean_abs']), number(r['value_contribution_spearman'])] for r in global_shap[:5]]),
        'The two largest contributions, energy and nbumps2, belong to the seismic-activity group. Removing that group and refitting gives pooled XGBoost AP %s versus %s for the full design, '
        'a difference of %s with paired interval %s. The interval includes zero. '
        'SHAP attributes the predictions of the full fitted model; ablation evaluates a newly fitted model with different inputs. '
        'Model reliance and incremental predictive value are distinct: influential signals need not improve the performance of a refitted model under the tested configuration. The interval leaves the direction of the group-removal gain unresolved. '
        'Correlated inputs, fitted interactions and sampling variability are plausible contributors. Appendix Table A2 reports all feature sets by phase; '
        'for XGBoost, without-seismic-minus-full AP differences are %s across phases 1 to 4. These phase patterns accompany the pooled comparison rather than identify its cause.'
        % (number(seismic_removed['pr_auc']), number(full['XGBoost']['pr_auc']),
           number(float(seismic_removed['pr_auc']) - float(full['XGBoost']['pr_auc'])),
           interval(seismic_interval['ci_low'], seismic_interval['ci_high']),
           ', '.join(number(r['without_seismic_minus_full']) for r in xgb_phase)),
        '![Figure 2. Global importance and phase shares for the eight globally leading features. Each cell is that feature\'s mean absolute contribution divided by the sum over all 17 features in the phase.](../../results/phase1/figures/shap_phase_stability.png)',
        'Across the six phase pairs, importance-rank correlations range from %s to %s and top-five Jaccard overlap ranges from %s to %s. '
        'This combination shows recurring feature use alongside changing membership of the most influential group. '
        'Excluding the globally constant nbumps6, nbumps7 and nbumps89 leaves one fixed 14-feature universe for every phase and gives correlations from %s to %s. '
        'Ranks are recomputed using average ranks on each fixed universe; alphabetical ordering resolves only top-five membership ties. '
        'Top-five overlap is unchanged by excluding these constants. Appendix Table A3 reports every phase pair under both universes.'
        % (number(min(correlations)), number(max(correlations)), number(min(overlaps)), number(max(overlaps)),
           number(min(nonconstant)), number(max(nonconstant))),
        '![Figure 3. Values and TreeSHAP contributions for the three globally leading features. Colours identify test phases; horizontal values use signed log1p for display, and vertical values are raw log-odds contributions.](../../results/phase1/figures/shap_dependence.png)',
        'The scatter distributions expose phase-dependent and nonlinear feature use. A high global importance can coexist with a weak global monotonic association: '
        'genergy, for example, has a descriptive value-contribution correlation of %s. '
        'The phase-coloured patterns show how a measurement\'s contribution varies with the other inputs and the fitted model. '
        'For engineering review, the contribution describes the signal in its prediction context.'
        % number(next(r for r in global_shap if r['feature'] == 'genergy')['value_contribution_spearman']),
        '### 5.2 Phase outcomes and illustrative warning cases',
        'Table 7 connects explanation changes to the phase outcomes. Positive prevalence and full-model AP vary across the record sequence. '
        'Computing AP within each block separates its observed discrimination from the cross-model score-scale differences that can affect pooled AP. '
        'Together, Tables 6 and 7 show why monitoring review benefits from examining feature use and phase outcomes side by side.',
        'Table 7. Four common test phases with positive counts, prevalence and within-phase full-feature AP.',
        table(['Phase', 'Rows', 'Positives', 'Prevalence', 'LR AP', 'CART AP', 'XGBoost AP'],
            [[f + 1, integer(next(r for r in phase if r['model'] == 'LR' and r['variant'] == 'full' and int(r['fold']) == f)['n']),
              integer(next(r for r in phase if r['model'] == 'LR' and r['variant'] == 'full' and int(r['fold']) == f)['positives']),
              number(next(r for r in phase if r['model'] == 'LR' and r['variant'] == 'full' and int(r['fold']) == f)['prevalence'])]
             + [number(next(r for r in phase if r['model'] == m and r['variant'] == 'full' and int(r['fold']) == f)['pr_auc']) for m in models] for f in range(4)]),
        'The predetermined holdout cases are shown in Figure 4. Each case decomposes the bias and all feature contributions to reconstruct the model margin. '
        'The five largest absolute contributions are displayed individually, with remaining contributions combined as Other features. '
        'The three outcomes show how combinations of measured signals place different records above or below the same frozen cutoff. '
        'Signed contributions locate each model adjustment relative to its baseline.',
        'The TP, FP and FN categories depend on predicted alerts and observed labels. The first row in each category supplies a deterministic illustration with limited discretionary case selection.',
        '![Figure 4. Earliest holdout true-positive, false-positive and false-negative cases under the 10 percent reference budget. IDs are one-based mirror rows; raw log-odds contributions, including Other features, sum with the bias to the margin.](../../results/phase1/figures/shap_warning_cases.png)',
        '## 6 Warning budgets and inspection workload',
        'Changing the reference budget changes the frozen threshold while leaving fitted scores unchanged. '
        'In the common record-order cohort, LR, CART and XGBoost actual alert rates at the 10 percent reference budget are %s, %s and %s. '
        'This provides a direct comparison between intended historical workload and its transferred operating outcome.'
        % tuple(number(selected_budget(m, .1, 'time')['alert_rate']) for m in models),
        '![Figure 5. Recall versus actual test alert fraction under the four fixed training reference budgets. Colours identify models and increasing circle sizes identify 1, 5, 10 and 20 percent budgets.](../../results/phase1/figures/research_warning_tradeoff.png)',
        'Table 8 reports the supplementary holdout outcomes for every model and budget. '
        'For XGBoost, increasing the reference budget from 10 to 20 percent increases alerts from %s to %s and detections from %s to %s, '
        'while missed hazardous shifts change from %s to %s. The corresponding actual alert rates are %s and %s. '
        'Reporting both detection counts and actual alert rates makes the workload change measurable when a historical threshold is transferred to later records.'
        % (integer(ten['alerts']), integer(twenty['alerts']), integer(ten['tp']), integer(twenty['tp']), integer(ten['fn']), integer(twenty['fn']), number(ten['alert_rate']), number(twenty['alert_rate'])),
        'Table 8. All holdout warning policies on 774 records with 26 positive targets. Budget is the training reference fraction; alert rate is measured on holdout rows. Precision is reported as zero when no alerts are issued.',
        table(['Model', 'Budget', 'Alerts', 'Detected', 'False alerts', 'Missed', 'Alert rate', 'Recall', 'Precision'],
            [[m, '%.0f%%' % (100 * b)] + [integer(selected_budget(m, b)[k]) for k in ('alerts', 'tp', 'fp', 'fn')]
             + [number(selected_budget(m, b)[k]) for k in ('alert_rate', 'recall', 'precision')] for m in models for b in (.01, .05, .10, .20)]),
        'At the 1 percent reference budget, holdout LR issues one alert and detects one hazardous shift, while CART and XGBoost issue no alerts. '
        'Detection and missed-shift counts make these sparse outcomes interpretable alongside precision. '
        'Higher budgets increase detections together with additional false-alert workload. '
        'The policy curves describe the observed detection–workload tradeoff. Choosing an operating budget would also require defined inspection capacity and consequences of missed hazards.',
        '## 7 Discussion',
        '### 7.1 Connecting monitoring evidence to warning decisions',
        'Matching test rows sharply reduces the LR and CART validation gaps, showing that the evaluation cohort materially affects their apparent size. The residual gaps compare workflows that still differ in training history and size; they do not isolate a leakage effect. '
        'Probability assessment adds a second distinction. Training-prior correction improves LR calibration, but corrected probabilities have positive Brier skill against the historical reference and negative skill against the retrospective test-prevalence reference. Improvement over the raw model and advantage over a reference are separate findings.',
        'The SHAP-ablation comparison provides an engineering reading of the monitoring signals. Energy and low-energy event counts strongly influence the fitted XGBoost predictions, '
        'while refitting without their group yields a positive pooled AP difference whose interval includes zero. Their influence describes the fitted prediction mechanism; the ablation tests the performance of a different fitted model. Reading these results together prevents global importance from becoming a claim of incremental value. '
        'The warning-budget results extend this interpretation to decisions: additional detections come with additional false alerts, and a historical reference budget can produce a different alert rate on later records.',
        '### 7.2 Scope and prospective validation',
        'Changing a probability scale and changing a decision rule address different engineering questions. Cost-sensitive decision theory [11] links probabilities to error costs; here historical reference scores supply empirical cutoffs. '
        'Prior-only distribution change [10] is a specific assumption rather than a diagnosis of the observed protocol gap. The companion decision study evaluates loss, capacity and refitting at frozen thresholds; '
        'it builds on this forecast evidence without treating calibration gains as evidence of operational warning value.',
        'These results concern the audited mirror under a record-order forecasting assumption. '
        'Timestamps, longwall identifiers and event locations are needed for direct temporal, site-specific and spatial validation. '
        'Repeated measurements can correspond to distinct shifts; the provenance audit establishes the mirror transformation rather than the operational validity of deduplication. '
        'Native TreeSHAP uses training leaf covers, and correlated inputs affect the allocation of contributions. '
        'Its signed values explain fitted associations rather than the causal effect of changing a monitoring variable. '
        'Phase stability is conditional on the fitted models and observed test distributions.',
        'The feature comparisons are prespecified descriptive contrasts with unadjusted fixed-prediction intervals. '
        'A maximum AP among these feature sets is not treated as a validated model-selection result. '
        'The already inspected holdout supplies additional warning evidence but does not constitute an untouched confirmatory test. '
        'A subsequent study should preregister its feature and alert-policy choices, then test them on independent timestamped working-face data with defined inspection actions.',
        '## 8 Conclusions',
        'Recalculating performance on common test rows substantially reduces the apparent random-versus-record-order gap. The paired residual differences and their intervals measure the remaining protocol contrast; they do not identify a causal share of leakage or drift. '
        'Training-prior correction improves LR probability assessment, while its reference-dependent Brier skill shows why calibration gains need an explicit comparator. '
        'TreeSHAP and refitted ablations distinguish the signals used by a model from their observed incremental predictive value. Frozen-budget outcomes quantify the detections, missed shifts and false alerts associated with those forecasts. '
        'The engineering contribution is an auditable connection from monitoring signals to forecasts and inspection demand: matched shifts define the performance comparison, explicit probability references define calibration value, and detected, missed and falsely alerted shifts define warning workload.',
        '## Data and computational reproducibility',
        'Source data are available from UCI [1] and the CSV mirror [2]. Saved evidence includes all feature-set predictions, inner-reference scores, '
        'fold audits, candidate-selection predictions and row-index manifests, bootstrap replicates, five random seeds, native XGBoost models, '
        'row-level TreeSHAP contributions and the predetermined case records. '
        'Result tables are generated from saved evidence. Source hashes and duplicate row mappings preserve the data version. '
        'Appendix Table A1 maps feature names to UCI definitions and the implemented engineering groups.',
        'The extended analysis uses Python %s, NumPy %s, pandas %s, XGBoost %s and SciPy %s. '
        'The legacy LR/CART baselines use the original verified Python 3.7 environment and retain their saved full-model predictions. '
        'Run commands from the repository root. Use the recorded baseline environment for python -m phase1.run_experiments and python -m phase1.run_engineering. '
        'For the extension, install requirements/requirements-research.txt in a separate Python 3.12 environment, then run python -m phase1.run_research, '
        'python -m phase1.review_analysis and python -m phase1.verify_research --replay. '
        'In a separate document environment, python -m phase1.generate_report --docx generates the paper; '
        'pwsh -NoProfile -ExecutionPolicy Bypass -File phase1/export_report.ps1 exports PDF. '
        'Use python -m phase1.verify_results --reports to check results and report agreement.'
        % tuple(config['environment'][k] for k in ('python', 'numpy', 'pandas', 'xgboost', 'scipy')),
        '## References',
        '[1] Sikora M, Wrobel L. Seismic Bumps [Dataset]. UCI Machine Learning Repository, 2010. DOI: 10.24432/C5W902. https://archive.ics.uci.edu/dataset/266/seismic+bumps',
        '[2] datasets/seismic-bumps. CSV mirror and preparation description. https://github.com/datasets/seismic-bumps',
        '[3] Bergmeir C, Benitez JM. On the use of cross-validation for time series predictor evaluation. Information Sciences, 2012, 191:192-213. DOI: 10.1016/j.ins.2011.12.028.',
        '[4] Roberts DR et al. Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. Ecography, 2017, 40:913-929. DOI: 10.1111/ecog.02881.',
        '[5] Shalizi CR. Simulation for Inference I: The Bootstrap. Carnegie Mellon University course notes, 2018. https://stat.cmu.edu/~cshalizi/dst/18/lectures/18/lecture-18.html',
        '[6] Chen T, Guestrin C. XGBoost: A Scalable Tree Boosting System. Proceedings of KDD, 2016, 785-794. DOI: 10.1145/2939672.2939785.',
        '[7] Lundberg SM et al. From local explanations to global understanding with explainable AI for trees. Nature Machine Intelligence, 2020, 2:56-67. DOI: 10.1038/s42256-019-0138-9.',
        '[8] XGBoost documentation. Booster.predict and exact feature contributions. https://xgboost.readthedocs.io/en/stable/python/python_api.html',
        '[9] Sikora M, Wrobel L. Application of rule induction algorithms for analysis of data collected by seismic hazard monitoring systems in coal mines. Archives of Mining Sciences, 2010, 55(1):91-114. Author-linked full text: https://www.researchgate.net/publication/281395657',
        '[10] Lipton ZC, Wang YX, Smola AJ. Detecting and Correcting for Label Shift with Black Box Predictors. Proceedings of ICML, PMLR 80, 2018:3122-3130. https://proceedings.mlr.press/v80/lipton18a.html',
        '[11] Elkan C. The Foundations of Cost-Sensitive Learning. Proceedings of IJCAI, 2001:973-978. Author manuscript: https://cseweb.ucsd.edu/~elkan/rescale.pdf',
    ]
    definitions = {
        'seismic': ('Hazard ratings', 'Seismic-method shift hazard rating', 'Ordinal a-d'),
        'seismoacoustic': ('Hazard ratings', 'Seismoacoustic shift hazard rating', 'Ordinal a-d'),
        'ghazard': ('Hazard ratings', 'GMax geophone hazard rating', 'Ordinal a-d'),
        'genergy': ('Geophone', 'Previous-shift energy at GMax', 'Numeric'),
        'gpuls': ('Geophone', 'Previous-shift pulse count at GMax', 'Numeric'),
        'gdenergy': ('Geophone', 'Energy deviation from previous eight-shift mean', 'Numeric'),
        'gdpuls': ('Geophone', 'Pulse-count deviation from previous eight-shift mean', 'Numeric'),
        'shift': ('Operation', 'Coal-getting W or preparation N', 'Binary'),
        'energy': ('Seismic activity', 'Previous-shift total bump energy', 'Numeric'),
        'maxenergy': ('Seismic activity', 'Previous-shift maximum bump energy', 'Numeric'),
    }
    for feature, bounds in [('nbumps2', '[10^2, 10^3)'), ('nbumps3', '[10^3, 10^4)'),
                            ('nbumps4', '[10^4, 10^5)'), ('nbumps5', '[10^5, 10^6)'),
                            ('nbumps6', '[10^6, 10^7)'), ('nbumps7', '[10^7, 10^8)'),
                            ('nbumps89', '[10^8, 10^10)')]:
        definitions[feature] = ('Seismic activity', 'Previous-shift bump count in ' + bounds + ' J',
                                'Constant' if feature in ('nbumps6', 'nbumps7', 'nbumps89') else 'Numeric')
    out.extend([
        '## Appendix A Feature definitions and phase evidence',
        'Table A1. Implemented feature groups and concise UCI variable definitions [1]. GMax is the most active geophone. Constant marks a numeric column with one value in the audited mirror.',
        table(['Feature', 'Group', 'Definition', 'Encoding'], [[name] + list(values) for name, values in definitions.items()]),
        'The total count nbumps is excluded from the retained 17-column design, which includes the energy-band counts. Ordinal ratings and the binary shift type use the fixed mappings documented in the preprocessing code; scaling is fitted within training.',
        'Table A2. Within-phase AP for every prespecified feature set. Phases use the same test rows across models and subsets. XGBoost subsets reuse the configuration selected on full-feature training data.',
        table(['Model', 'Feature set', 'Phase 1', 'Phase 2', 'Phase 3', 'Phase 4'],
              [[model, label] + [number(next(r for r in phase if r['model'] == model and r['variant'] == variant and int(r['fold']) == f)['pr_auc']) for f in range(4)]
               for model in models for variant, label in labels.items()]),
        'Table A3. Phase-pair stability with a fixed universe of 17 columns and after excluding the three constant columns. Average ranks are used for Spearman; top-five overlap uses the stated alphabetical boundary rule.',
        table(['Phase pair', 'Spearman 17', 'Spearman 14', 'Top-5 Jaccard 17', 'Top-5 Jaccard 14'],
              [['%d-%d' % (a+1, b+1)] + [number(next(r for r in sensitivity if r['scope'] == scope and int(r['fold_a']) == a and int(r['fold_b']) == b)[metric])
               for metric in ('rank_spearman', 'top5_jaccard') for scope in ('all_features', 'nonconstant_features')]
               for a in range(4) for b in range(a+1, 4)]),
    ])
    return '\n\n'.join(out) + '\n'
