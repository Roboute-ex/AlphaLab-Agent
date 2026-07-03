# Project Notes

## One-liner

AlphaLab Agent 是一个 deterministic local quant research workflow，用 Agent-style orchestration 把数据、因子、回测、诊断、Reviewer 和 report 串成可复现实验。

## Motivation

做这个项目的动机：

- 学习量化研究流程。
- 练习 agent workflow。
- 练习可复现工程。
- 练习测试、CI、文档和项目治理。

## Technical highlights

- synthetic data。
- panel builder。
- factor calculation。
- forward return label。
- execution-based backtest。
- benchmark comparison。
- walk-forward validation。
- data quality checks。
- supervised factor model。
- Reviewer。
- manifest。
- markdown/html report。
- CI/tests。

## Agent highlights

- `PlannerAgent`。
- `ResearchPlan`。
- deterministic pipeline。
- step logs。
- Reviewer Agent。
- report / manifest。

## Engineering highlights

- pytest。
- fallback runner。
- version consistency tests。
- README command smoke tests。
- manifest schema tests。
- CI。
- CHANGELOG。
- maintenance docs。
- release checklist。

## Difference from a chatbot

AlphaLab Agent 不是金融聊天机器人。它不通过自然语言生成投资建议，也不让 LLM 生成收益、风险或 Reviewer 结论。它把研究流程结构化，并由 deterministic Python modules 产生可复验结果。

## Difference from a simple backtest script

它不仅是单个回测脚本，而是带 planning、diagnostics、benchmark、walk-forward、Reviewer、manifest 和 report 的完整 workflow。普通 backtest script 可能只关心收益曲线；AlphaLab Agent 还关心数据质量、风险、成本、稳定性和可复现 artifacts。

## Future improvement ideas

- architecture diagram。
- sample report snapshot。
- clearer config examples。
- more data quality diagnostics。
- more benchmark variants。
- better documentation around limitations。
