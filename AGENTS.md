# AGENTS.md

给后续 coding agent 的协作规则。AlphaLab Agent 当前采用 `v0.6` 合并式升级状态：`v0.1` 已单独提交和打 tag，`v0.2-v0.6` 作为一次升级完成并准备提交。

## 硬性边界

- 默认使用 synthetic data。
- 不接实盘交易。
- 不下单。
- 不保存、提交、打印或文档化真实 API key。
- 真实数据 adapter 必须 disabled-by-default。
- 默认不调用真实外部金融数据 API。
- LLM 必须 optional；当前项目不接 LLM。
- 核心研究结果必须 deterministic。
- 所有随机过程必须使用固定 seed。
- 新功能必须有 pytest。
- 不要只展示收益率，必须展示风险、成本、Reviewer、robustness。
- optional dependency 必须 graceful fallback，不能破坏默认 deterministic path。

## 当前 deterministic core

```text
synthetic market data
-> panel builder
-> factor calculation
-> forward return label
-> factor analysis
-> walk-forward validation
-> parameter sensitivity
-> top-k long-only backtest
-> risk metrics
-> reviewer checks
-> markdown/html report
```

## 版本状态

- `v0.1`: deterministic quant research core，已单独提交并打 tag。
- `v0.2`: JSON config、IC / RankIC、分层收益、charts、HTML report，本次合并式升级完成。
- `v0.3`: deterministic PlannerAgent、ResearchPlan parser、step logs、agent demo，本次合并式升级完成。
- `v0.4`: optional Streamlit demo 和 fallback，本次合并式升级完成。
- `v0.5`: disabled-by-default CSV / yfinance data adapters，本次合并式升级完成。
- `v0.6`: walk-forward validation、parameter sensitivity、robustness checks、Reviewer 增强，当前版本。
- `v0.7`: public demo polish，后续计划，尚未完成。

## 开发要求

- 修改核心计算时，必须补充或更新 pytest。
- 修改报告或 CLI 输出时，要同步 README 和 docs。
- 修改 optional dependency 时，必须证明未安装该依赖时仍能 graceful fallback。
- 修改真实数据 adapter 时，必须保持默认 synthetic path 不变。
- 修改 Reviewer 时，必须让结论由确定性代码产生，不能由 LLM 直接生成。
- 不要引入实盘交易、自动下单、broker API 或真实 API key 存储。
