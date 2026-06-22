# AlphaLab Agent 项目计划

AlphaLab Agent 是一个面向量化策略实习与 Agent 项目展示的本地可复现低/中频股票多因子研究系统。项目边界保持不变：默认 synthetic data，不接 LLM，不接实盘，不下单，不保存 API key。

## 1. 当前版本状态

- `v0.1` 已单独 tag。
- `v0.2-v0.6` 已合并式升级完成。
- 当前 `v0.7` 是 Research Validity & Engineering Hardening。
- 后续 `v0.8` 或最终展示阶段再做 Public Demo Polish；不要把截图、视频脚本、简历 bullet、release notes 大改写成当前已完成。

## 2. v0.7 目标

把项目从 `v0.6` 的完整可运行研究 workflow，升级为更接近真实量化研究验证流程的版本：

```text
synthetic market data
-> panel builder
-> factor calculation
-> forward return label for diagnostics
-> factor diagnostics
-> execution-based signal-to-portfolio backtest
-> benchmark / baseline comparison
-> walk-forward validation with train-only factor weighting
-> parameter sensitivity
-> Reviewer robustness checks
-> run_manifest.json
-> markdown/html report
```

## 3. 已完成版本能力

### v0.1

- deterministic quant research core。
- synthetic OHLCV、panel、factors、labels、label-based top-k backtest。
- risk metrics、Reviewer、Markdown report、pytest。

### v0.2-v0.6

- JSON config、IC / RankIC、quantile analysis、charts、HTML report。
- deterministic PlannerAgent、ResearchPlan parser、step logs、agent demo。
- optional Streamlit demo 和 fallback。
- disabled-by-default CSV / yfinance adapters。
- walk-forward validation、parameter sensitivity、Reviewer robustness checks。

### v0.7

- execution-based backtest。
- benchmark comparison。
- factor diagnostics enhancement。
- train-only factor weighting。
- run_manifest.json。
- GitHub Actions CI。

## 4. 模块职责

- `backtest/execution.py`: signal date 到 realized return 的 execution-style backtest。
- `backtest/benchmark.py`: equal-weight、random top-k、single-factor baselines 和 comparison summary。
- `analysis/factor_analysis.py`: IC / RankIC、quantile analysis、factor diagnostics。
- `analysis/weighting.py`: equal/config/IC/RankIC train-only factor weighting。
- `analysis/robustness.py`: walk-forward validation、walk-forward factor weights、parameter sensitivity。
- `report/manifest.py`: `run_manifest.json` 实验元信息。
- `review/checks.py`: benchmark、diagnostics、robustness、cost、risk 的 deterministic Reviewer。
- `pipeline.py`: v0.7 end-to-end orchestration。
- `.github/workflows/ci.yml`: core deterministic path CI。

## 5. 依赖策略

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

不引入数据库、DuckDB、vector DB、Qlib、backtrader、vectorbt 等重依赖。任何 optional dependency 都必须 lazy import / graceful fallback。

## 6. 测试策略

测试覆盖：

- execution backtest 不使用 forward_return label 作为主收益。
- benchmark comparison。
- factor diagnostics。
- train-only weighting。
- manifest generation。
- pipeline integration。
- CLI backwards compatibility。
- Reviewer 新检查。
- Reviewer severity 区分结构性 FAIL 与研究质量 WARN。
- `.gitignore` 对 `artifacts/run_manifest.json` 的忽略规则。
- CI 文件存在且命令合理。

## 7. Artifacts 策略

`artifacts/.gitkeep` 可以提交。

自动生成物默认不提交：

- `artifacts/report.md`
- `artifacts/report.html`
- `artifacts/run_manifest.json`
- `artifacts/research_plan.json`
- `artifacts/step_logs.json`
- `artifacts/*.png`

## 8. 安全边界

- 不接 OpenAI API。
- 不接 LLM。
- 不接实盘交易。
- 不自动下单。
- 不保存 API key。
- 默认仍然使用 synthetic data。
- yfinance / CSV adapter 必须 disabled-by-default。
- 新增研究功能必须展示 benchmark、risk、cost、Reviewer、robustness。
