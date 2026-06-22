# AGENTS.md

给后续 coding agent 的协作规则。AlphaLab Agent 当前是 `v0.7` Research Validity & Engineering Hardening。

## 硬性边界

- 默认使用 synthetic data。
- 不接 OpenAI API。
- 不接 LLM；如果未来接入，必须 optional，且不能参与核心数值真值生成。
- 不接实盘交易。
- 不下单。
- 不保存、提交、打印或文档化真实 API key。
- 真实数据 adapter 必须 disabled-by-default。
- 默认不调用真实外部金融数据 API。
- 不引入数据库、DuckDB、vector DB、Qlib、backtrader、vectorbt 等重依赖。
- optional dependency 必须 lazy import / graceful fallback。
- 核心研究结果必须 deterministic。
- 所有随机过程必须使用固定 seed。
- 新功能必须有 pytest。
- 不要只展示收益率，必须展示 benchmark、风险、成本、Reviewer、robustness。

## v0.7 规则

- 回测默认不能直接依赖 forward_return label 作为主收益。
- forward_return label 只能用于 IC / RankIC、quantile analysis、factor diagnostics 等分析。
- 新增研究功能必须有 benchmark / risk / cost / reviewer。
- 任何 train/test 或 walk-forward 逻辑必须避免 test leakage。
- train-only weighting 只能在 train window 学权重，在 test window 冻结使用。
- CI 必须覆盖 core deterministic path。
- 自动生成的 artifacts 不应进入 staged files。

## 当前 deterministic core

```text
synthetic market data
-> panel builder
-> factor calculation
-> forward return label
-> factor diagnostics
-> execution-based backtest
-> benchmark comparison
-> walk-forward validation
-> parameter sensitivity
-> risk metrics
-> reviewer checks
-> run_manifest.json
-> report
```

## 版本状态

- `v0.1`: deterministic quant research core，已单独提交并打 tag。
- `v0.2-v0.6`: 合并式升级已完成。
- `v0.7`: execution backtest、benchmark、factor diagnostics、train-only weighting、manifest、CI，当前版本。
- 后续展示打磨另行处理。
