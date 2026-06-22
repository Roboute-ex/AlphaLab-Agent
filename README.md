# AlphaLab Agent

AlphaLab Agent 是一个面向量化策略实习与 Agent 项目展示的本地可复现低/中频股票多因子研究系统。

当前版本：`v0.6`。远程仓库已有 `v0.1`，本次不再拆分 `v0.2-v0.6`，而是作为一次合并式升级完成并准备提交。

## 项目定位

AlphaLab Agent 不是金融问答机器人，也不是实盘交易系统。它把量化研究员的核心研究流程做成可复现的本地工作流：

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
-> optional deterministic agent-style workflow logs
-> optional Streamlit demo
-> optional explicit real data adapters
-> markdown / html report
```

核心计算由确定性 Python 代码完成，不依赖 LLM 直接生成收益、风险、Reviewer 结论或回测结果。

## 当前版本说明

- `v0.1`: deterministic quant research core，已单独提交并打 tag。
- `v0.2-v0.6`: 在本次合并式升级中一起完成，当前版本定为 `v0.6`。
- 后续 `v0.7`: public demo polish，尚未完成。

## 功能分层

### v0.1: deterministic quant research core

- 固定随机种子的 synthetic OHLCV 数据。
- date-symbol panel builder。
- baseline factors: momentum、reversal、low volatility、volume trend。
- forward return label。
- top-k long-only equal-weight backtest。
- risk metrics 与 deterministic Reviewer。
- Markdown report 与 pytest 测试。

### v0.2: research analysis upgrade

- JSON config。
- Factor IC / RankIC。
- 分层收益分析。
- optional chart generation。
- HTML report。

### v0.3: agent-style workflow

- deterministic `PlannerAgent`，不依赖 LLM。
- `ResearchPlan` parser。
- deterministic step logs。
- `--agent-demo` CLI。
- `artifacts/research_plan.json`。
- `artifacts/step_logs.json`。

### v0.4: optional Streamlit demo

- optional Streamlit app。
- Streamlit 未安装时 graceful fallback。
- UI entrypoint: `python -m streamlit run src/alphalab_agent/app/streamlit_app.py`。
- 参数展示、报告展示、Factor Analysis、Validation、Positions、Workflow Logs 页面。

### v0.5: optional real data adapters

- disabled-by-default CSV OHLCV adapter。
- disabled-by-default yfinance adapter。
- 默认仍然使用 synthetic data。
- `data_source` 标注。
- Report / Reviewer 能区分 synthetic、csv、yfinance。

### v0.6: robustness and validation

- walk-forward validation。
- parameter sensitivity。
- robustness checks。
- Reviewer 增强：样本外覆盖、样本外 Sharpe、train/test Sharpe gap、参数敏感性、成本和风险提示。

## Quickstart

安装开发依赖：

```bash
python -m pip install -e ".[dev]"
```

如果 Windows 上 `python` 指向 Microsoft Store launcher，可以改用：

```bash
py -m pip install -e ".[dev]"
```

运行正式 pytest：

```bash
py -m pytest -q
```

在受限环境中，如果不能使用 pytest，可以运行 fallback runner：

```bash
py scripts\run_tests.py
```

## Demo 命令

运行默认 synthetic research demo：

```bash
py -m alphalab_agent.cli --demo
```

运行 deterministic agent-style demo：

```bash
py -m alphalab_agent.cli --agent-demo --goal "研究默认 synthetic 多因子策略"
```

运行示例脚本：

```bash
py examples\run_v0_research.py
```

运行 optional Streamlit demo：

```bash
python -m pip install -e ".[app]"
python -m streamlit run src/alphalab_agent/app/streamlit_app.py
```

如果未安装 Streamlit，以下命令会输出安装提示并正常退出：

```bash
py -m alphalab_agent.app.streamlit_app
```

## Optional Data Adapters

默认路径不调用真实行情 API。只有显式指定 `--data-source csv` 或 `--data-source yfinance` 时，才会进入对应 adapter。

本地 CSV 示例：

```bash
py -m alphalab_agent.cli --demo --data-source csv --csv-path path/to/ohlcv.csv
```

yfinance 示例：

```bash
python -m pip install -e ".[data]"
py -m alphalab_agent.cli --demo --data-source yfinance --ticker AAPL --start 2020-01-01 --end 2024-01-01
```

## Artifacts

默认输出目录：

```text
artifacts/
```

常见生成物：

```text
artifacts/report.md
artifacts/report.html
artifacts/research_plan.json
artifacts/step_logs.json
artifacts/equity_curve.png
```

这些 demo 产物会被 `.gitignore` 忽略，避免把本地运行结果混入提交。`artifacts/.gitkeep` 用于保留目录，可以提交。

## Example Output

```text
AlphaLab Agent v0.6 demo complete
Steps: synthetic data -> panel -> factors -> labels -> factor analysis -> walk-forward validation -> sensitivity -> backtest -> metrics -> reviewer -> report
Reviewer status: WARN
Periods: 96
Total return: 9.94%
Annualized return: 5.10%
Sharpe: 0.36
Max drawdown: -18.04%
Average turnover: 73.75%
Average cost drag: 0.037%
Report: artifacts\report.md
HTML report: artifacts\report.html
```

## 项目结构

```text
AlphaLab Agent/
  AGENTS.md
  README.md
  pyproject.toml
  .gitignore
  artifacts/
    .gitkeep
  docs/
    PROJECT_PLAN.md
  examples/
    run_v0_research.py
    v0_2_config.json
    v0_3_goal.txt
  scripts/
    run_tests.py
  src/
    alphalab_agent/
      app/streamlit_app.py
      analysis/factor_analysis.py
      analysis/robustness.py
      cli.py
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
```

这是标准 `src` layout。建议先安装 `python -m pip install -e ".[dev]"`，再运行模块命令。

## 风险提示

- 本项目仅用于研究、教学与求职展示。
- 本项目不构成投资建议。
- 本项目不接实盘交易。
- 本项目不自动下单。
- 本项目默认不调用真实行情 API。
- yfinance / CSV adapter 是 optional 且 disabled-by-default。
- synthetic data 不代表真实市场 alpha。
- 回测结果不代表未来收益，也不代表真实市场可交易性。
- 不应在本项目中保存真实 API key。

## 面试讲法

- 这是一个 quant research workflow，不是金融聊天机器人。
- `v0.1` 先证明了 deterministic research core：数据、panel、因子、标签、回测、风险指标、Reviewer、报告。
- 本次合并式升级把 `v0.2-v0.6` 一起补齐：分析、Agent-style workflow、Streamlit、optional data adapters、robustness validation。
- Agent 部分是 deterministic PlannerAgent，展示任务拆解、结构化 ResearchPlan、step logs 和工具编排，不让 LLM 直接生成核心数值结论。
- Reviewer 不只展示好看的收益率，还展示风险、成本、turnover、drawdown、样本外验证和参数敏感性。
- optional dependencies 都要 graceful fallback，不能破坏默认 synthetic deterministic path。
