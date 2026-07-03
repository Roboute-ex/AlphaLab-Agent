# CHANGELOG

AlphaLab Agent 的变更记录。项目坚持默认 synthetic data、不接 LLM、不接实盘、不下单、不保存 API key。

## v0.10 - Agent Design Transparency and Project Maturity

### Added

- Added detailed README explanation of the deterministic research workflow agent.
- Added `docs/AGENT_DESIGN.md`.
- Added `docs/DEMO_WALKTHROUGH.md`.
- Added `docs/PROJECT_NOTES.md`.
- Added tests for agent documentation and README agent sections.

### Changed

- Updated version references from v0.9 to v0.10.
- Expanded README project positioning, Agent workflow, design principles, safety boundary, and project notes.

### Safety Boundary

- No live trading.
- No broker API.
- No default network access.
- No API key storage.
- No LLM-generated returns, risks, Reviewer conclusions, or backtest results.

### Validation

- `py -m pytest -q` passed.
- `py scripts\run_tests.py` passed.
- CLI version, default demo, agent demo, CSV sample demo, supervised model demo, Streamlit fallback, and example runner passed.

## v0.9

### Added

- 新增维护文档：`docs/MAINTENANCE.md`、`docs/MAINTENANCE_LOG.md`、`docs/RELEASE_CHECKLIST.md`。
- 新增版本一致性测试（Version consistency tests）、README 命令 smoke test、manifest schema 稳定性测试。
- 新增 GitHub issue / PR templates。

### Changed

- CI 增加 pip cache 和 CLI version check。
- README 增加 CI badge 和维护说明。

### Fixed

- 补强维护流程，降低版本号、README 命令和 manifest schema 漂移风险。

### Safety Boundary

- 不接 OpenAI API，不接 LLM，不接实盘交易，不自动下单。
- 默认 synthetic data，不默认联网，不保存 API key。

### Validation

- `py -m pytest -q`
- `py scripts\run_tests.py`
- CLI demo / CSV demo / supervised model demo smoke checks。

## v0.8

### Added

- Hardened CSV / yfinance real-data research entrypoints。
- Market data quality checks。
- Sample synthetic-style CSV workflow。
- NumPy train-only supervised factor model。
- Out-of-sample ML evaluation。

### Changed

- Report、Reviewer、manifest 接入 data quality 和 supervised model 结果。

### Fixed

- 真实数据入口增加 schema normalization 和 graceful fallback。

### Safety Boundary

- CSV / yfinance 必须显式启用。
- yfinance 仍为 optional dependency 且 lazy import。
- supervised model 仅用于研究验证，不代表可实盘预测能力。

### Validation

- 新增 data quality、sample CSV pipeline、ML model、ML walk-forward tests。

## v0.7

### Added

- Execution-based signal-to-portfolio backtest。
- Benchmark comparison。
- Factor diagnostics enhancement。
- Train-only factor weighting。
- `run_manifest.json`。
- GitHub Actions CI。

### Changed

- 默认回测不再直接用 forward return label 作为主收益来源。

### Fixed

- Reviewer severity 调整：研究质量风险为 WARN，结构性问题为 FAIL。
- `scipy` 作为 Spearman / RankIC 核心依赖进入 runtime dependencies。

### Safety Boundary

- 默认 synthetic data。
- 不接 LLM、不接实盘、不下单。

### Validation

- pytest、fallback runner、default demo、agent demo、example runner。

## v0.6

### Added

- JSON config、IC / RankIC、quantile analysis、charts、HTML report。
- Deterministic PlannerAgent、ResearchPlan parser、step logs、agent demo。
- Optional Streamlit demo 和 fallback。
- Disabled-by-default CSV / yfinance adapters。
- Walk-forward validation、parameter sensitivity、Reviewer robustness checks。

### Changed

- 从 v0.1 core 扩展为更完整的本地研究 workflow。

### Fixed

- 补齐多阶段研究分析和报告输出能力。

### Safety Boundary

- 真实数据 adapter disabled-by-default。
- optional dependency 必须 graceful fallback。

### Validation

- pytest 和 fallback runner 覆盖 core workflow。

## v0.1

### Added

- Fixed-seed synthetic OHLCV data。
- Panel builder、baseline factors、forward return label。
- Top-k long-only label-based backtest。
- Risk metrics、Reviewer、Markdown report、pytest。

### Changed

- 初始 deterministic quant research core。

### Fixed

- 无历史修复记录。

### Safety Boundary

- 不接真实行情 API。
- 不接实盘交易。
- 不构成投资建议。

### Validation

- Synthetic full pipeline smoke test。
