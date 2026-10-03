# Stage 1 command guide

Run these commands from the repository root. Use the recorded baseline environment for baseline and engineering experiments and the research environment for XGBoost and complete verification. See [the full reproduction sequence](../docs/REPRODUCING.md) before refreshing results.

| Task | Command |
| --- | --- |
| Baseline experiments | `python -m scripts.run_experiments` |
| Audit source data | `python -m scripts.audit_source` |
| Engineering extensions | `python -m scripts.run_engineering` |
| XGBoost and explanation extensions | `python -m scripts.run_research` |
| Refresh paired analysis | `python -m scripts.refresh_analysis` |
| Refresh review supplements | `python -m scripts.review_analysis` |
| Verify saved results and paper | `python -m scripts.verify_results --reports` |
| Replay research models | `python -m scripts.verify_research --replay` |
| Independently reconstruct metric and decision formulae | `python -B -m scripts.verify_formulae` |
| Generate Word and Markdown | `python -m scripts.generate_report --docx` |
| Export Word to PDF on Windows | `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/export_report.ps1` |
| Record an execution environment | `python -m scripts.record_environment` |

The remaining modules support those commands: `paper_content` and `research_paper` assemble the manuscript; `engineering_figures` and `research_figures` render figures; `research_analysis`, `verify_additions` and `verify_review` implement supplementary analysis and checks.

The second stage has an independent [module and command guide](../phase2/README.md).
