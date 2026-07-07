# AlphaLab Agent 维护说明

本项目是个人开源研究展示项目。维护目标是保持 deterministic core 可复验、文档命令不过期、安全边界不漂移。

## 本地复验

常规复验命令：

```powershell
py -m pytest -q
py scripts\run_tests.py
py -m alphalab_agent.cli --demo
py -m alphalab_agent.cli --demo --data-source csv --csv-path examples/sample_ohlcv.csv
py -m alphalab_agent.cli --demo --enable-supervised-model
```

如需检查版本：

```powershell
py -m alphalab_agent.cli --version
```

## Artifacts 处理

以下 demo 生成物默认由 `.gitignore` 忽略，不应提交：

- `artifacts/report.md`
- `artifacts/report.html`
- `artifacts/run_manifest.json`
- `artifacts/research_plan.json`
- `artifacts/step_logs.json`
- `artifacts/*.png`

`artifacts/.gitkeep` 可以保留目录。提交前请运行 `git status`，确认没有 demo 生成物进入 staged files。

## 真实数据处理

- 默认仍然使用 synthetic data。
- CSV / yfinance adapter 必须 disabled-by-default，只有显式命令才启用。
- 不保存 API key，不提交含敏感信息的数据。
- 不默认联网。yfinance 只在显式 `--data-source yfinance` 时尝试下载。

## 依赖处理

- 新增运行时依赖必须写入 `pyproject.toml` 的 core dependencies。
- optional dependency 必须 lazy import，并提供 graceful fallback。
- 依赖变更必须有测试或文档说明。
- 不引入 DuckDB、vector DB、Qlib、backtrader、vectorbt、FinRL、XGBoost、LightGBM、PyTorch、TensorFlow 等重依赖。

## GitHub Actions

- Green check 表示 Python 测试通过。
- Node.js deprecation warning 不等于 Python 测试失败。
- 不要为了消除 warning 盲目切换到不存在或不稳定的 action 版本。
- 当前 CI 只安装 core dev dependencies，不安装 yfinance / streamlit optional extras。

## v0.10 Maintenance Hygiene

- Generated artifacts must not be committed. Keep `artifacts/.gitkeep`, but do not stage `artifacts/report.md`, `artifacts/report.html`, `artifacts/run_manifest.json`, `artifacts/research_plan.json`, `artifacts/step_logs.json`, or chart PNGs.
- Always run `git status` before release preparation and before committing.
- Always run `py -m pytest -q` before release.
- Always run `py scripts\run_tests.py` before release.
- Optional dependencies should not move into core dependencies unless a core deterministic feature truly requires them.
- Dependabot is only an auxiliary signal for dependency updates. It does not replace local tests, manual review, or the safety boundary checks.
- README, docs, CLI output, package version, and report version must remain consistent.
