# Troubleshooting

## pytest cannot import alphalab_agent

Common causes:

- The command is not running from the repository root.
- The editable install was not completed.
- The active virtual environment is not the one used for installation.

Suggested fix:

```powershell
python -m pip install -e ".[dev]"
py -m pytest -q
```

You can also set `PYTHONPATH=src` for a temporary local check, but the editable install is the preferred project workflow.

## Streamlit command fails

Streamlit is an optional dependency. The fallback command should still run without Streamlit:

```powershell
py -m alphalab_agent.app.streamlit_app
```

To run the interactive app locally, install the optional app extra:

```powershell
python -m pip install -e ".[app]"
python -m streamlit run src/alphalab_agent/app/streamlit_app.py
```

Do not add Streamlit to the core dependency set only to make the optional app available.

## yfinance unavailable

`yfinance` is optional and disabled by default. The default demo and CI should not require it and should not download real market data.

Only use it explicitly:

```powershell
python -m pip install -e ".[data]"
py -m alphalab_agent.cli --demo --data-source yfinance --tickers AAPL,MSFT --start-date 2020-01-01 --end-date 2020-12-31
```

If `yfinance` is not installed, the adapter should fail gracefully with a clear message.

## Reviewer WARN is not a failure

`WARN` usually means the research result needs caution, not that the pipeline broke. Examples include weak factor monotonicity, unstable IC, underperformance versus benchmark, high turnover, or high cost drag.

`FAIL` is reserved for structural issues such as invalid data, leakage risk, no positions, no returns, or a broken pipeline.

## GitHub Actions failed but local passed

Check these first:

- CI uses a clean environment, so a missing core dependency must be declared in `pyproject.toml`.
- CI should install only core dev dependencies, not optional yfinance or Streamlit extras.
- Python version differences can reveal import or typing issues.
- Path assumptions can differ between Windows and Linux.
- A Node.js deprecation warning is not the same as a Python test failure.

Do not change stable GitHub Actions versions just to suppress warnings.

## Version mismatch

Version references must remain aligned across:

- `pyproject.toml`
- `src/alphalab_agent/_version.py`
- `src/alphalab_agent/__init__.py`
- README current version
- `docs/PROJECT_PLAN.md`
- CLI `--version`
- report title

Run:

```powershell
py -m alphalab_agent.cli --version
py -m pytest -q tests/test_version_consistency.py
```

## Generated artifacts accidentally staged

Generated artifacts should not be committed:

- `artifacts/report.md`
- `artifacts/report.html`
- `artifacts/run_manifest.json`
- `artifacts/research_plan.json`
- `artifacts/step_logs.json`
- `artifacts/*.png`

Keep `artifacts/.gitkeep`, but unstage generated outputs before committing.
