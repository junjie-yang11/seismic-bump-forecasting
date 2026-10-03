# 项目导航

## 阅读论文

| 阶段 | 内容 | Word | PDF | 文本版本 |
| --- | --- | --- | --- | --- |
| 第一阶段 | 预测评估、校准、可解释性与预警工作量 | [Word](../report/technical_report.docx) | [PDF](../report/technical_report.pdf) | [Markdown](../report/technical_note.md) |
| 第二阶段 | 成本与容量约束下的预警阈值转移 | [Word](../results/phase2/report/phase2_threshold_transfer_report.docx) | [PDF](../results/phase2/report/phase2_threshold_transfer_report.pdf) | [Markdown](../results/phase2/report/phase2_threshold_transfer_report.md) |

在本机可直接打开根目录的 `00_论文入口`，双击对应快捷方式。入口指向上述原始文件，重新生成后会打开更新后的版本。

## 目录用途

| 位置 | 用途 |
| --- | --- |
| `report/` | 第一阶段最终论文 |
| `results/` | 第一阶段计算结果、预测、图像、模型与验证记录 |
| `results/phase2/` | 第二阶段逐行预测、阈值候选、选择审计、评价与不确定性结果 |
| `results/phase2/report/` | 第二阶段论文、插图及文档来源记录 |
| `src/` | 共用的数据处理、模型、指标、校准与评估实现 |
| `tests/` | 第一阶段及共用功能的测试 |
| `phase2/` | 第二阶段独立模块、锁定方案、测试和执行说明 |
| `data/` | 数据缓存和来源说明 |
| `docs/` | 项目导航和目录整理记录 |
| `docs/audits/` | 第一阶段审核和修改记录 |
| `scripts/` | 第一阶段实验、分析、核验及文档生成入口 |
| `requirements/` | 基线、研究与文档生成环境的依赖清单 |
| `.venv/` | 第一阶段基线复现环境 |
| `.venv-research/` | XGBoost 扩展及第二阶段运行环境 |
| `99_本地归档/` | 完整复算工作副本与安装临时文件，仅在本机保留 |

`results/phase2/report/` 内的论文与其他结果文件分开保存。图像、CSV、JSON 和重采样数组是论文的计算依据，不应当作重复文件清理。

## 运行脚本

第一阶段脚本已集中到 `scripts/`。从仓库根目录执行 `python -m scripts.<模块名>`，例如 `python -m scripts.run_experiments`。第二阶段继续使用 `python -m phase2.<模块名>`。结果与论文仍保留原始路径。

| 工作 | 主要文件 |
| --- | --- |
| 基线实验与数据来源核查 | `run_experiments.py`、`audit_source.py`、`record_environment.py` |
| 矿业特征、校准与预警扩展 | `run_engineering.py`、`engineering_figures.py` |
| XGBoost 与解释分析 | `run_research.py`、`research_analysis.py`、`research_figures.py` |
| 配对分析和审阅补充 | `refresh_analysis.py`、`review_analysis.py` |
| 第一阶段论文内容与生成 | `paper_content.py`、`research_paper.py`、`generate_report.py`、`export_report.ps1` |
| 结果核验 | `verify_results.py`、`verify_additions.py`、`verify_research.py`、`verify_review.py` |
| 环境依赖 | `requirements.txt`、`requirements-research.txt`、`requirements-report.txt` |

表中 Python 和 PowerShell 文件均位于 `scripts/`，三个依赖清单位于 `requirements/`。完整执行顺序见[复现说明](REPRODUCING.md)，第二阶段命令见[独立模块说明](../phase2/README.md)。两个 Python 环境服务于不同阶段的记录环境，不是重复安装目录。

## 审核和修改记录

- [第一阶段项目审查](audits/PROJECT_REVIEW.md)
- [第一阶段执行审计](audits/EXECUTION_AUDIT.md)
- [第一阶段修改记录](audits/MODIFICATION_LOG.md)
- [第二阶段完整审查](../results/phase2/PROJECT_REVIEW.md)
- [第二阶段变更记录](../phase2/CHANGELOG.md)
- [第二阶段执行与润色记录](../phase2/implementation_log.md)
- [本次目录整理记录](ORGANIZATION_LOG.md)

## 本地归档

原根目录 `.audit-work/` 的独立复算副本，以及八个 `pip-*` 安装临时目录，已移入 `99_本地归档/2026-10-03_整理/`。没有删除文件。逐文件校验与原路径记录保存在归档中的 `organization_manifest.json`；需要恢复时，先确认根目录没有同名目录，再将相应子目录移回。

`00_论文入口/` 与 `99_本地归档/` 不同步到 GitHub。论文、计算结果、代码和此导航仍使用仓库内的相对链接。
