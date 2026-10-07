# Contributions and AI Assistance

## Project direction

I defined the project's aims and scope and drove its iterative development. I selected the two-stage research structure: first evaluating forecast reliability and explainability, and then examining warning-threshold transfer under assumed costs and inspection capacity.

My role included setting research and review priorities, requesting reproducibility checks, and reviewing and directing revisions to the reports and repository presentation. These priorities included preserving negative results, keeping test outcomes separate from policy selection, and distinguishing forecast performance from warning decision value.

I was responsible for setting the research questions, refining and approving the analytical protocol, reviewing proposed implementations, results and verification records, and approving the research interpretation.

## Implementation and AI assistance

ChatGPT and Codex provided substantial assistance with code generation and revision, experiment execution, test development and execution, interpretation of outputs, reference checks, and manuscript drafting and editing.

The implementation uses established methods, including logistic regression, bagged CART, XGBoost, TreeSHAP and block resampling. The project contribution is their integration and empirical evaluation within a documented mining case, together with the two-stage evaluation and decision-analysis workflow.

AI-generated text and suggestions did not replace source data or recorded computational evidence. Research choices and final interpretations remained subject to my review and approval. The records describe an AI-assisted workflow, rather than independent authorship of every implementation or personal execution of every numerical check.

## Concrete project decisions and corresponding evidence

These examples connect research priorities to delivered work. File links identify implementations and outputs, rather than establish independent code authorship.

| Research priority | Corresponding implementation or evidence |
| --- | --- |
| Separate forecast evaluation from warning decision analysis | [Two-stage papers and scope](reports/README.md) |
| Separate fitting, threshold selection and testing; compare fixed and refitted models | [Locked Stage 2 protocol](phase2/locked_plan.json), [fold implementation](phase2/experiment.py) |
| Retain no-alarm comparisons and evaluate detections alongside workload and loss | [Decision accounting](phase2/supplement.py), [pooled results](results/phase2/decision_value_pooled.csv), [capacity and detection contrasts](results/phase2/capacity_tradeoffs.csv) |
| Require reproducibility checks and agreement between report formats | [Reproduction guide](docs/REPRODUCING.md), [version-specific review](docs/audits/CONTRIBUTION_REVIEW.md) |

## Evidence and verification

The repository retains the experimental code, locked Stage 2 protocol, row-level predictions, threshold-selection audits, computed results and version-specific verification records. Automated tests, model replay and saved-evidence checks are reported separately from the author's review and research decisions.

The project provides a documented retrospective evaluation of forecasting, threshold transfer, capacity constraints and decision value in a mining context. Its findings concern the specified dataset and workflows; operational validation requires further evidence.
