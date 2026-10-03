# 论文定稿前事实及衔接核对

日期：2026-10-03。

## nbumps 表述

直接读取 `data/seismic-bumps.csv`，逐行比较 `nbumps` 与
`nbumps2, nbumps3, nbumps4, nbumps5, nbumps6, nbumps7, nbumps89` 的计数之和。
2,578 行中 2,576 行相等，2 行不同。

| 镜像数据行号（从 1 开始，不计表头） | nbumps | 分档计数之和 |
| --- | --- | --- |
| 435 | 2 | 1 |
| 436 | 1 | 0 |

因此第一阶段正文及附录统一采用：

> The total count nbumps is excluded from the retained 17-column design, which includes the energy-band counts.

这项修正描述实际保留的特征设计，不推断两条记录出错。模型输入仍为原来的
17 列，原始数据和第一阶段实验结果不变。逐行核算及输入文件校验值保存在
`results/phase2/final_factual_verification.json`。

## 两阶段衔接及呈现

第二阶段第 2 节增加简短衔接：第一阶段以外层重训练模型使用历史参考阈值，
第二阶段以固定模型和阈值为主、重训练为对照。另交代 XGBoost 参考模型参数
搜索与预算边界并列分数规则的差异。跨报告比较须注明模型、参数选择、流程
和阈值定义，数据及预算相同不意味着报警数量相同。

Figure 3 右图报警数量变化采用整数标注，损失差仍保留一位小数。
增加第一阶段技术报告引用及 Künsch（1989）的区块 bootstrap 方法引用。
文献元数据核对来源：作者出版物列表及 DOI 10.1214/aos/1176347265。

## 文件与最终核对

修改 `scripts/research_paper.py` 与 `phase2/report.py`，重新生成两阶段
Word、PDF、Markdown；更新本记录及第二阶段修改日志。
未增加模型、特征、策略或实验设置。为保持第二阶段执行记录中受保护的
第一阶段论文校验值与当前文档一致，按原锁定方案重新执行及回放第二阶段，
随后与修订前完整快照比较；该执行不是新增研究比较。

第一阶段报告一致性检查 8,169 项，第二阶段回放验证 63,863 项，补充计算验证
10,902 项，独立公式核对 8,220 项通过。18 个第二阶段 CSV、3,960,000 个
重采样值及两篇论文的全部表格内容与修订前相同。两篇共 27 页完成逐页渲染检查。
当前最终版本以 `final_factual_verification.json` 及
`results/phase2/report/report_verification.json` 的校验值为准；以前的审查记录
保留各自记录时的版本含义。
