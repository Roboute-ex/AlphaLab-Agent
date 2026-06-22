# AlphaLab Agent

AlphaLab Agent 是一个面向量化策略实习与 Agent 项目展示的本地可复现低/中频股票多因子研究系统。

当前版本：`v0.7`。`v0.1` 已单独提交和打 tag，`v0.2-v0.6` 已作为一次合并式升级完成；本轮 `v0.7` 聚焦 Research Validity & Engineering Hardening。

## 项目定位

AlphaLab Agent 不是金融问答机器人，也不是实盘交易系统。它把量化研究员的核心研究流程做成可复现的本地工作流：

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
-> markdown / html report
```

核心计算由确定性 Python 代码完成，不依赖 LLM 直接生成收益、风险、Reviewer 结论或回测结果。

## 版本路线

### v0.1: deterministic quant research core

- fixed-seed synthetic OHLCV data。
- panel builder、baseline factors、forward return label。
- top-k long-only label-based backtest。
- risk metrics、Reviewer、Markdown report、pytest。

### v0.2-v0.6: 合并式升级

- `v0.2`: JSON config、IC / RankIC、分层收益、图表、HTML report。
- `v0.3`: deterministic PlannerAgent、ResearchPlan parser、step logs、agent demo。
- `v0.4`: optional Streamlit demo 和 fallback。
- `v0.5`: disabled-by-default CSV / yfinance data adapters。
- `v0.6`: walk-forward validation、parameter sensitivity、robustness checks、Reviewer 增强。

### v0.7: research validity and engineering hardening

- execution-based signal-to-portfolio backtest。
- benchmark / baseline comparison。
- factor diagnostics enhancement。
- train-only factor weighting for walk-forward validation。
- run_manifest.json。
- GitHub Actions CI。

后续展示打磨、截图、GIF、视频脚本、简历 bullet 和 release notes 大改放到后续阶段，不属于本轮 v0.7。

## Quickstart

安装开发依赖：

```bash
python -m pip install -e ".[dev]"
```

运行正式 pytest：

```bash
py -m pytest -q
```

运行 fallback runner：

```bash
py scripts\run_tests.py
```

## Demo 命令

默认 synthetic research demo：

```bash
py -m alphalab_agent.cli --demo
```

deterministic agent-style demo：

```bash
py -m alphalab_agent.cli --agent-demo --goal "研究默认 synthetic 多因子策略"
```

示例脚本：

```bash
py examples\run_v0_research.py
```

optional Streamlit demo：

```bash
python -m pip install -e ".[app]"
python -m streamlit run src/alphalab_agent/app/streamlit_app.py
```

未安装 Streamlit 时可验证 fallback：

```bash
py -m alphalab_agent.app.streamlit_app
```

## CLI 参数

常用参数：

```text
--demo
--agent-demo
--config path/to/config.json
--output-dir artifacts
--backtest-mode execution|label_based
--weighting-mode equal_weight|config_weight|ic_weight_train_only|rankic_weight_train_only
--benchmark-seed 42
--no-manifest
```

真实数据 adapter 仍然 disabled-by-default，只有显式指定才启用：

```bash
py -m alphalab_agent.cli --demo --data-source csv --csv-path path/to/ohlcv.csv
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
artifacts/run_manifest.json
artifacts/research_plan.json
artifacts/step_logs.json
artifacts/equity_curve.png
```

这些自动生成物会被 `.gitignore` 忽略，避免本地 demo 结果进入提交。`artifacts/.gitkeep` 用于保留目录，可以提交。

## Example Output

```text
AlphaLab Agent v0.7 demo complete
Steps: synthetic data -> panel -> factors -> labels -> factor analysis -> execution backtest -> benchmarks -> walk-forward validation -> sensitivity -> reviewer -> report
Reviewer status: WARN
Periods: 481
Total return: ...
Sharpe: ...
Max drawdown: ...
Report: artifacts\report.md
HTML report: artifacts\report.html
Run manifest: artifacts\run_manifest.json
```

## 项目结构

```text
AlphaLab Agent/
  .github/workflows/ci.yml
  AGENTS.md
  README.md
  pyproject.toml
  docs/PROJECT_PLAN.md
  examples/
  scripts/
  src/alphalab_agent/
    analysis/
      factor_analysis.py
      robustness.py
      weighting.py
    backtest/
      benchmark.py
      execution.py
      metrics.py
      portfolio.py
    app/streamlit_app.py
    data/
    report/
      charts.py
      html.py
      manifest.py
      markdown.py
    research/
    review/
    workflow/
  tests/
```

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
- `v0.7` 从“能跑通研究闭环”升级到“更像真实研究验证流程”：execution backtest、benchmark、factor diagnostics、train-only weighting、manifest、CI。
- 默认回测不再直接用 forward_return label 作为主收益来源，而是用 signal date 后的 realized return。
- Reviewer 不只展示收益率，还展示 benchmark、风险、成本、turnover、drawdown、样本外验证、参数敏感性和因子诊断。
- Reviewer severity 中，FAIL 保留给数据无效、无收益、无持仓或流程断裂；弱信号、跑输 benchmark、高成本和高换手属于 WARN。
- Agent 部分仍是 deterministic PlannerAgent，不接 LLM，不让 LLM 生成核心数值结论。
