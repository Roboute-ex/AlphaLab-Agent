# Runbook

## Purpose

This runbook keeps AlphaLab Agent v0.10 reproducible and release-safe. It is for local validation, artifact hygiene, and lightweight release preparation. It does not change the research logic, portfolio construction, benchmark calculation, Reviewer severity, factor formulas, or synthetic data generation.

## Local Environment Checklist

- Use Python 3.10 or 3.11.
- Work from the repository root.
- Prefer a virtual environment for local development.
- Install core development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

- Optional extras stay optional:
  - `.[viz]` for matplotlib charts.
  - `.[app]` for Streamlit.
  - `.[data]` for yfinance.
- Do not add optional dependencies to the core path unless they become required by deterministic tests.
- Do not save API keys in config files, docs, examples, tests, or logs.

## Standard Validation Commands

Run these commands before preparing a release or asking for review:

```powershell
py -m pytest -q
py scripts\run_tests.py
py -m alphalab_agent.cli --version
py -m alphalab_agent.cli --demo
py -m alphalab_agent.cli --agent-demo --goal "研究默认 synthetic 多因子策略"
py -m alphalab_agent.cli --demo --data-source csv --csv-path examples/sample_ohlcv.csv
py -m alphalab_agent.cli --demo --enable-supervised-model
py -m alphalab_agent.app.streamlit_app
py examples\run_v0_research.py
```

## Expected Outputs

Generated outputs are written under `artifacts/` by default:

- `artifacts/report.md`
- `artifacts/report.html`
- `artifacts/run_manifest.json`
- `artifacts/research_plan.json`
- `artifacts/step_logs.json`
- `artifacts/equity_curve.png`

These are generated artifacts and should not be committed. Keep `artifacts/.gitkeep` so the directory exists in a clean checkout.

## Release Routine

1. Confirm the version is consistent across `pyproject.toml`, package version files, README, docs, CLI output, and report title.
2. Run `py -m pytest -q`.
3. Run `py scripts\run_tests.py`.
4. Run the standard CLI smoke commands listed above.
5. Run `git status` and confirm generated artifacts are not staged.
6. Review `git diff --stat` and inspect any source-code diff carefully.
7. Update `CHANGELOG.md` only for the release being prepared.
8. Merge with `--ff-only` when practical.
9. Push the release branch or `main`.
10. Wait for GitHub Actions to pass.
11. Create the tag only after CI is green.
12. Create the GitHub Release after the tag is correct.

## When Not To Release

Do not release when any of these are true:

- `pytest` failed.
- `scripts/run_tests.py` failed.
- CLI `--version` does not match the documented version.
- README claims do not match CLI behavior.
- Generated artifacts are staged.
- A real API key, secret, token, password, broker credential, or private data appears in the diff.
- The diff changes core research logic without dedicated tests and explicit review.
- The default demo starts using real external market data or network access.
- Reviewer status changed because severity rules were weakened rather than because logic was intentionally reviewed.
