# AlphaLab Agent

![CI](https://github.com/Roboute-ex/AlphaLab-Agent/actions/workflows/ci.yml/badge.svg)

AlphaLab Agent 是一个面向量化策略实习与 Agent 项目展示的本地可复现低/中频股票多因子研究系统。

当前版本：`v0.9`。`v0.1` 已单独提交和打 tag，`v0.6` 是合并式升级，`v0.7` 是 Research Validity & Engineering Hardening，`v0.8` 是 Real Data Research Adapter + Data Quality + Supervised Factor Model；本轮 `v0.9` 聚焦 Maintenance, Reproducibility and Project Governance。

## 项目定位

AlphaLab Agent 不是金融问答机器人，也不是实盘交易系统。它把量化研究员的核心研究流程做成可复现的本地工作流：

```text
synthetic market data
-> panel builder
-> factor calculation
-> forward return label
-> data quality
-> factor diagnostics
-> execution-based backtest
-> benchmark comparison
-> walk-forward validation
-> optional supervised factor model
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

### v0.8: Real Data Research Adapter + Data Quality + Supervised Factor Model

- hardened CSV / yfinance real-data research entrypoints。
- market data quality checks。
- sample synthetic-style CSV workflow。
- train-only supervised factor model。
- out-of-sample ML evaluation。
- manifest and Reviewer integration。

### v0.9: Maintenance, Reproducibility and Project Governance

- CHANGELOG and maintenance docs。
- Release checklist。
- Version consistency tests。
- README command smoke tests。
- Manifest schema stability tests。
- CI hygiene improvements。
- Issue / PR templates。

本项目将通过 CHANGELOG、release checklist、CI 和 smoke tests 保持持续维护。

后续展示打磨、截图、GIF、视频脚本、简历 bullet 和 release notes 大改放到后续阶段，不属于本轮 v0.9。

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

检查版本：

```bash
py -m alphalab_agent.cli --version
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
--version
--config path/to/config.json
--output-dir artifacts
--backtest-mode execution|label_based
--weighting-mode equal_weight|config_weight|ic_weight_train_only|rankic_weight_train_only
--benchmark-seed 42
--enable-supervised-model
--model-type ridge|linear
--no-manifest
```

真实数据 adapter 仍然 disabled-by-default，只有显式指定才启用：

```bash
py -m alphalab_agent.cli --demo --data-source csv --csv-path examples/sample_ohlcv.csv
py -m alphalab_agent.cli --demo --data-source csv --csv-path path/to/ohlcv.csv
python -m pip install -e ".[data]"
py -m alphalab_agent.cli --demo --data-source yfinance --tickers AAPL,MSFT --start-date 2020-01-01 --end-date 2024-01-01
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
AlphaLab Agent v0.9 demo complete
Steps: synthetic data -> panel -> factors -> labels -> factor analysis -> data quality -> execution backtest -> benchmarks -> walk-forward validation -> optional supervised model -> sensitivity -> reviewer -> report
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
  .github/ISSUE_TEMPLATE/
  AGENTS.md
  CHANGELOG.md
  README.md
  pyproject.toml
  docs/
    MAINTENANCE.md
    MAINTENANCE_LOG.md
    PROJECT_PLAN.md
    RELEASE_CHECKLIST.md
  examples/
  scripts/
  src/alphalab_agent/
    analysis/
      factor_analysis.py
      ml_model.py
      robustness.py
      weighting.py
    backtest/
      benchmark.py
      execution.py
      metrics.py
      portfolio.py
    app/streamlit_app.py
    data/
      quality.py
      schema.py
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
- supervised model 仅用于研究验证，不代表可实盘预测能力。
- 回测结果不代表未来收益，也不代表真实市场可交易性。
- 不应在本项目中保存真实 API key。

## 面试讲法

- 这是一个 quant research workflow，不是金融聊天机器人。
- `v0.9` 在 v0.8 基础上增加 CHANGELOG、维护文档、release checklist、版本一致性测试、README 命令 smoke tests、manifest schema 稳定性测试、CI hygiene 和 issue / PR templates。
- 默认回测不再直接用 forward_return label 作为主收益来源，而是用 signal date 后的 realized return。
- Reviewer 不只展示收益率，还展示 benchmark、风险、成本、turnover、drawdown、样本外验证、参数敏感性和因子诊断。
- Reviewer severity 中，FAIL 保留给数据无效、无收益、无持仓或流程断裂；弱信号、跑输 benchmark、高成本和高换手属于 WARN。
- 监督学习模型严格 train-only，不能随机切分时间序列，也不能把 test label 用于训练。
- Agent 部分仍是 deterministic PlannerAgent，不接 LLM，不让 LLM 生成核心数值结论。
