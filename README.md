# AlphaLab Agent

![CI](https://github.com/Roboute-ex/AlphaLab-Agent/actions/workflows/ci.yml/badge.svg)

AlphaLab Agent 是一个面向量化研究学习、Agent workflow 实践和本地可复现实验的低/中频股票多因子研究系统。

当前版本：`v0.10`。本轮重点是 **Agent Design Transparency and Project Maturity**：把 Agent 设计讲清楚，让研究流程更容易复现、审计和长期维护。

## 项目简介

AlphaLab Agent 不是金融问答机器人，也不是实盘交易系统。It is not a financial chatbot, and it is not a live trading system.

它的核心目标是把量化研究流程拆成可复现、可测试、可审计的工程模块：

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

所有收益、风险指标、Reviewer 结论和回测结果都由 deterministic Python code 生成，不由 LLM 编造。

## What is the Agent in AlphaLab Agent?

AlphaLab Agent 中的 Agent 不是让 LLM 直接生成投资建议、收益、风险指标或 Reviewer 结论。它是一个 **deterministic research workflow agent / research orchestration agent**。

Agent 的职责是把研究目标拆成可执行步骤，记录 step logs，调用 deterministic pipeline，并汇总 Reviewer 和 report。核心数值计算由明确的 Python 模块完成，而不是由 LLM 生成。

主要角色：

- `PlannerAgent`: 根据用户的研究目标生成结构化 `ResearchPlan`。
- `ResearchPlan`: 保存 universe size、top-k、forward horizon、cost 等研究配置。
- `Research pipeline`: 执行 synthetic / CSV data、panel、factors、labels、data quality、backtest、benchmark、walk-forward、ML OOS、sensitivity、Reviewer、report。
- `Reviewer`: 保守检查研究质量，包括 benchmark、drawdown、turnover、cost drag、IC stability、walk-forward、manifest、data quality 等。
- `Report / Manifest`: 输出 `report.md`、`report.html`、`run_manifest.json`，让结果可复现、可审计。

为什么采用 deterministic agent：

- 避免幻觉，尤其避免 LLM 编造收益和风险结论。
- 方便用 pytest 和 fallback runner 测试。
- 更适合量化研究中需要复验的流程。
- 方便长期维护和版本治理。
- 让研究流程透明，每一步都有明确输入、输出和 artifact。

它和金融聊天机器人的区别：

- 金融聊天机器人通常围绕自然语言问答；AlphaLab Agent 围绕 deterministic research workflow。
- AlphaLab Agent 不输出投资建议，不连接券商，不下单，不保存 API key。
- 它把研究步骤结构化，而不是把结论交给 LLM 生成。

它和普通 backtest script 的区别：

- 普通 backtest script 往往只跑一次策略收益；AlphaLab Agent 还包含 planning、data quality、factor diagnostics、benchmark、walk-forward validation、Reviewer、manifest 和 report。
- 结果不仅有收益，也有风险、成本、turnover、drawdown、样本外检查和可复现配置。

## Agent Workflow

```text
user research goal
-> PlannerAgent
-> ResearchPlan
-> deterministic pipeline
-> factor diagnostics
-> execution backtest
-> benchmark comparison
-> walk-forward validation
-> optional supervised model
-> Reviewer checks
-> run_manifest.json
-> markdown / html report
```

## Design Principles

- deterministic first: 所有核心结果由确定性代码生成。
- synthetic data by default: 默认不依赖真实行情或联网。
- offline-safe: 默认 demo、pytest、fallback runner 都不需要外部 API。
- explicit configuration: 研究参数写入 config 和 manifest。
- testable outputs: report、manifest、CLI、docs 都有测试保护。
- conservative reviewer: Reviewer 不只看收益，还检查风险、成本、benchmark 和稳健性。
- reproducible artifacts: `artifacts/report.md` 和 `artifacts/run_manifest.json` 记录运行结果。
- no hidden API dependency: yfinance / CSV 必须显式启用，缺少 optional dependency 时 graceful fallback。

## Safety Boundary

- synthetic data by default。
- no live trading。
- no auto order execution。
- no broker API。
- no saved API key。
- no default network access。
- yfinance / CSV optional and disabled-by-default。
- supervised model is research-only。
- backtest result is not investment advice。

## Version Roadmap

### v0.1: deterministic quant research core

- fixed-seed synthetic OHLCV data。
- panel builder、baseline factors、forward return label。
- top-k long-only label-based backtest。
- risk metrics、Reviewer、Markdown report、pytest。

### v0.6: consolidated research workflow

- JSON config、IC / RankIC、quantile analysis、charts、HTML report。
- deterministic PlannerAgent、ResearchPlan parser、step logs、agent demo。
- optional Streamlit demo 和 fallback。
- disabled-by-default CSV / yfinance adapters。
- walk-forward validation、parameter sensitivity、Reviewer robustness checks。

### v0.7: research validity and engineering hardening

- execution-based signal-to-portfolio backtest。
- benchmark / baseline comparison。
- factor diagnostics enhancement。
- train-only factor weighting for walk-forward validation。
- run_manifest.json。
- GitHub Actions CI。

### v0.8: real data quality and supervised factor model

- hardened CSV / yfinance real-data research entrypoints。
- market data quality checks。
- sample synthetic-style CSV workflow。
- train-only supervised factor model。
- out-of-sample ML evaluation。
- manifest and Reviewer integration。

### v0.9: maintenance, reproducibility and project governance

- CHANGELOG and maintenance docs。
- Release checklist。
- Version consistency tests。
- README command smoke tests。
- Manifest schema stability tests。
- CI hygiene improvements。
- Issue / PR templates。

### v0.10: agent design transparency and project maturity

- Expanded README explanation of deterministic Agent design。
- Added `docs/AGENT_DESIGN.md`。
- Added `docs/DEMO_WALKTHROUGH.md`。
- Added `docs/PROJECT_NOTES.md`。
- Added documentation tests for Agent design and project notes。

## Quickstart

安装开发依赖：

```bash
python -m pip install -e ".[dev]"
```

运行测试：

```powershell
py -m pytest -q
py scripts\run_tests.py
```

检查版本：

```powershell
py -m alphalab_agent.cli --version
```

默认 synthetic research demo：

```powershell
py -m alphalab_agent.cli --demo
```

deterministic agent-style demo：

```powershell
py -m alphalab_agent.cli --agent-demo --goal "研究默认 synthetic 多因子策略"
```

CSV sample demo：

```powershell
py -m alphalab_agent.cli --demo --data-source csv --csv-path examples/sample_ohlcv.csv
```

supervised model research demo：

```powershell
py -m alphalab_agent.cli --demo --enable-supervised-model
```

Streamlit fallback check：

```powershell
py -m alphalab_agent.app.streamlit_app
```

## Example Output

```text
AlphaLab Agent v0.10 demo complete
Steps: synthetic data -> panel -> factors -> labels -> factor analysis -> data quality -> execution backtest -> benchmarks -> walk-forward validation -> optional supervised model -> sensitivity -> reviewer -> report
Reviewer status: WARN
Periods: 483
Total return: ...
Sharpe: ...
Max drawdown: ...
Report: artifacts\report.md
HTML report: artifacts\report.html
Run manifest: artifacts\run_manifest.json
```

`WARN` 不代表 pipeline 失败。它通常表示研究质量仍有保守提示，例如 benchmark 表现、因子稳定性、turnover、成本或样本外表现需要继续观察。

## Project Structure

```text
AlphaLab Agent/
  .github/workflows/ci.yml
  .github/ISSUE_TEMPLATE/
  AGENTS.md
  CHANGELOG.md
  README.md
  pyproject.toml
  docs/
    AGENT_DESIGN.md
    DEMO_WALKTHROUGH.md
    MAINTENANCE.md
    MAINTENANCE_LOG.md
    PROJECT_NOTES.md
    PROJECT_PLAN.md
    RELEASE_CHECKLIST.md
  examples/
    sample_ohlcv.csv
    run_v0_research.py
  scripts/
    run_tests.py
  src/alphalab_agent/
    analysis/
    backtest/
    app/
    data/
    report/
    research/
    review/
    workflow/
  tests/
```

## Project Design Notes

- 这是 quant research workflow，不是金融聊天机器人。
- Agent 负责规划、编排、记录、审查，不负责编造收益。
- execution-based backtest 避免直接拿 forward_return label 当主收益来源。
- Reviewer 不只看收益，还看 benchmark、风险、成本、turnover、drawdown、样本外验证、参数敏感性和因子诊断。
- v0.10 重点是 Agent 透明性、项目成熟度、文档质量和持续维护意识。

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

这些自动生成物默认由 `.gitignore` 忽略，不应作为 demo 结果提交。`artifacts/.gitkeep` 用于保留目录。

## Disclaimer

本项目仅用于研究、教学和项目展示，不构成投资建议。回测结果、监督学习结果和 Reviewer 结论都不代表未来收益，也不代表真实市场可交易性。
