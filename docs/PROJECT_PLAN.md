# AlphaLab Agent 项目计划

本文档记录 AlphaLab Agent 的版本路线、当前实现状态和后续边界。项目定位保持不变：这是一个面向量化策略实习与 Agent 项目展示的本地可复现低/中频股票多因子研究系统，不是金融问答机器人，也不是实盘交易系统。

## 1. 当前提交策略

- 远程 GitHub 已有 `v0.1`，并且 `v0.1` 已单独提交和打 tag。
- 本地工作区已完成 `v0.2-v0.6` 的能力。
- 本次采用合并式升级策略：不回退、不拆分多个 commit，不再分别提交 `v0.2`、`v0.3`、`v0.4`、`v0.5`。
- 当前版本定为 `v0.6`。
- 后续 `v0.7` 是 public demo polish，尚未完成，不应写成当前已完成。

## 2. 总体架构

默认研究流程：

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
-> optional Streamlit demo
-> optional deterministic agent-style workflow
-> optional disabled-by-default data adapters
```

设计原则：

- 默认使用 synthetic data。
- 默认不调用真实外部金融数据 API。
- 默认不使用 LLM。
- 不接实盘交易。
- 不下单。
- 核心研究结果由 deterministic code 产生。
- 所有随机过程必须固定 seed。

## 3. 版本路线

### v0.1: deterministic quant research core

已单独提交并打 tag。

- fixed-seed synthetic OHLCV data。
- panel builder。
- baseline factors。
- forward return label。
- top-k long-only backtest。
- risk metrics。
- deterministic Reviewer。
- Markdown report。
- pytest tests。

### v0.2: research analysis upgrade

本次合并式升级中完成。

- JSON config。
- IC / RankIC。
- 分层收益分析。
- optional charts。
- HTML report。

### v0.3: agent-style workflow

本次合并式升级中完成。

- deterministic PlannerAgent。
- ResearchPlan parser。
- step logs。
- `--agent-demo`。
- `research_plan.json`。
- `step_logs.json`。

### v0.4: optional Streamlit demo

本次合并式升级中完成。

- optional Streamlit app。
- Streamlit 未安装时 graceful fallback。
- UI entrypoint。
- 参数展示、报告展示、Factor Analysis、Validation、Positions、Workflow Logs。

### v0.5: optional real data adapters

本次合并式升级中完成。

- CSV adapter。
- yfinance adapter。
- disabled-by-default。
- `data_source` 标注。
- Report / Reviewer 区分 synthetic、csv、yfinance。

### v0.6: robustness and validation

本次合并式升级中完成，当前版本。

- walk-forward validation。
- parameter sensitivity。
- robustness checks。
- Reviewer 增强。

### v0.7: public demo polish

后续计划，尚未完成。

- README 展示 polish。
- demo 截图或 GIF。
- 面试 walkthrough。
- 更清晰的 release notes。

## 4. 文件结构

```text
AlphaLab Agent/
  README.md
  AGENTS.md
  pyproject.toml
  docs/PROJECT_PLAN.md
  scripts/run_tests.py
  examples/run_v0_research.py
  examples/v0_2_config.json
  examples/v0_3_goal.txt
  src/alphalab_agent/
    app/streamlit_app.py
    analysis/factor_analysis.py
    analysis/robustness.py
    config.py
    pipeline.py
    data/adapters.py
    data/synthetic.py
    research/panel.py
    research/factors.py
    research/labels.py
    backtest/portfolio.py
    backtest/metrics.py
    review/checks.py
    workflow/planner.py
    workflow/agent.py
    workflow/steps.py
    report/markdown.py
    report/html.py
    report/charts.py
  tests/
  artifacts/
```

## 5. 模块职责

- `config.py`: deterministic run config、JSON config、参数校验。
- `data/synthetic.py`: fixed-seed synthetic OHLCV generator。
- `data/adapters.py`: disabled-by-default CSV / yfinance adapters。
- `research/`: panel、factor、label。
- `analysis/factor_analysis.py`: IC / RankIC 与分层收益。
- `analysis/robustness.py`: walk-forward validation 与 parameter sensitivity。
- `backtest/`: top-k long-only backtest 与 risk metrics。
- `review/checks.py`: deterministic Reviewer checks。
- `workflow/`: PlannerAgent、ResearchPlan、step logs、agent-style workflow。
- `app/streamlit_app.py`: optional Streamlit demo。
- `report/`: Markdown、HTML、optional chart。
- `pipeline.py`: v0.6 end-to-end deterministic research orchestration。
- `cli.py`: `--demo`、`--agent-demo`、optional data adapter CLI。

## 6. 依赖策略

Minimal dependencies:

- Python 3.10+
- pandas
- numpy

Dev dependency:

- pytest

Optional dependencies:

- matplotlib: optional charts。
- streamlit: optional demo。
- yfinance: explicit real data adapter。
- duckdb、langgraph、vectorbt、backtrader、Qlib: 后续 optional，不默认启用。

任何 optional dependency 都必须 graceful fallback，不能破坏默认 synthetic deterministic path。

## 7. 测试策略

测试应覆盖：

- synthetic data shape、OHLCV 合法性、fixed seed reproducibility。
- panel 无重复 symbol-date。
- factor columns、forward label shift、no look-ahead。
- top-k backtest、with-cost / without-cost equity。
- risk metrics: Sharpe、max drawdown、turnover、cost drag。
- IC / RankIC、分层收益。
- walk-forward validation。
- parameter sensitivity。
- Reviewer 能发现异常配置或异常结果。
- pipeline smoke test。
- CLI demo。
- agent-demo artifacts。
- CSV adapter 与 yfinance missing-dependency fallback。
- Streamlit import fallback。

## 8. Artifacts 策略

`artifacts/.gitkeep` 可以提交，用于保留目录。

自动生成的 demo 产物默认不提交：

- `artifacts/report.md`
- `artifacts/report.html`
- `artifacts/*.png`
- `artifacts/research_plan.json`
- `artifacts/step_logs.json`
- `artifacts/test*/`
- `artifacts/tmp*/`

本地运行 demo 时可以重新生成这些文件。

## 9. 当前边界

- 不接实盘。
- 不下单。
- 不保存 API key。
- 默认不调用真实行情 API。
- CSV / yfinance adapter 必须显式启用。
- 当前不接 LLM。
- synthetic data 不代表真实市场 alpha。
- 本项目仅用于研究、教学与求职展示，不构成投资建议。
