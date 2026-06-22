# AlphaLab Agent

AlphaLab Agent 是一个面向量化策略实习和 Agent 项目展示的本地可复现低/中频股票多因子研究系统。

当前版本：`v0.7`。`v0.1` 已单独提交并打了 tag，`v0.2–v0.6` 作为一次合并式升级完成；本轮 `v0.7` 聚焦研究有效性验证和工程加固。

## 项目定位

AlphaLab Agent 不是金融问答机器人，也不是实盘交易系统。它把量化研究员的核心研究流程做成可本地复现的工作流：

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

核心计算全部由确定性 Python 代码完成，不依赖 LLM 生成收益、风险、Reviewer 结论或回测结果。

## 版本路线

### v0.1：确定性量化研究核心

- 固定随机种子的合成 OHLCV 数据
- panel builder、基础因子、forward return label
- top-k 纯多头基于标签的回测
- 风险指标、Reviewer、Markdown 报告、pytest

### v0.2–v0.6：合并式升级

- `v0.2`：JSON config、IC / RankIC、分层收益、图表、HTML 报告
- `v0.3`：确定性 PlannerAgent、ResearchPlan 解析、step logs、agent demo
- `v0.4`：可选 Streamlit demo 和 fallback
- `v0.5`：默认关闭的 CSV / yfinance 数据适配器
- `v0.6`：walk-forward 验证、参数敏感性、稳健性检查、Reviewer 增强

### v0.7：研究有效性与工程加固

- 基于执行信号的 signal-to-portfolio 回测
- benchmark / baseline 对比
- 因子诊断增强
- walk-forward 验证中仅用训练期做因子加权
- run_manifest.json
- GitHub Actions CI

后续的展示打磨、截图、GIF、视频脚本、简历 bullet 和 release notes 大改放到下一阶段，不属于本轮 v0.7。

## 快速开始

安装开发依赖：

```bash
python -m pip install -e ".[dev]"
```

跑测试：

```bash
py -m pytest -q
```

或者用 fallback runner：

```bash
py scripts\run_tests.py
```

## Demo 命令

默认 synthetic 研究 demo：

```bash
py -m alphalab_agent.cli --demo
```

确定性 agent 风格 demo：

```bash
py -m alphalab_agent.cli --agent-demo --goal "研究默认 synthetic 多因子策略"
```

示例脚本：

```bash
py examples\run_v0_research.py
```

可选 Streamlit demo：

```bash
python -m pip install -e ".[app]"
python -m streamlit run src/alphalab_agent/app/streamlit_app.py
```

没装 Streamlit 的话可以验证 fallback：

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

真实数据适配器默认关闭，需要显式指定才会启用：

```bash
py -m alphalab_agent.cli --demo --data-source csv --csv-path path/to/ohlcv.csv
python -m pip install -e ".[data]"
py -m alphalab_agent.cli --demo --data-source yfinance --ticker AAPL --start 2020-01-01 --end 2024-01-01
```

## 输出产物

默认输出目录：

```text
artifacts/
```

常见生成文件：

```text
artifacts/report.md
artifacts/report.html
artifacts/run_manifest.json
artifacts/research_plan.json
artifacts/step_logs.json
artifacts/equity_curve.png
```

这些自动生成的文件都加进了 `.gitignore`，不会把本地 demo 结果带进提交。`artifacts/.gitkeep` 用来保留目录结构，可以提交。

## 输出示例

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

- 本项目仅用于研究、教学等，不构成投资建议
- 不接实盘交易，不会自动下单
- 默认不调用任何真实行情 API
- yfinance / CSV 适配器是可选功能，默认关闭
- synthetic 数据不代表真实市场 alpha
- 回测结果不代表未来收益，也不代表在真实市场中可交易
- 不要在本项目中保存真实 API key
