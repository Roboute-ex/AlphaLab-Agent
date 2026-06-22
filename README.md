# AlphaLab Agent

AlphaLab Agent is a deterministic local workflow for low- to mid-frequency
equity multi-factor research, built for quant strategy internship and agent
internship demos.

## What This Project Is

AlphaLab Agent v0.1 turns a quant research workflow into reproducible Python code:

```text
synthetic market data
-> panel builder
-> factor calculation
-> forward return label
-> top-k long-only backtest
-> risk metrics
-> reviewer checks
-> markdown report
```

## What This Project Is Not

- Not a financial chatbot.
- Not a live trading system.
- Not an order placement tool.
- Not investment advice.
- Not dependent on real market data APIs by default.
- Not dependent on LLMs by default.

## Quickstart

Install the package with dev dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run formal tests:

```bash
python -m pytest -q
```

If `pytest` is unavailable in a constrained demo environment, run the fallback
test runner:

```bash
python scripts/run_tests.py
```

Run the v0.1 demo:

```bash
python -m alphalab_agent.cli --demo
```

On Windows installations where `python` points to the Microsoft Store launcher,
use `py` instead:

```bash
py -m alphalab_agent.cli --demo
```

The demo writes the default report to:

```text
artifacts/report.md
```

## Example Output

```text
AlphaLab Agent v0.1 demo complete
Steps: synthetic data -> panel -> factors -> labels -> backtest -> metrics -> reviewer -> report
Reviewer status: WARN
Periods: 96
Total return: 9.94%
Annualized return: 5.10%
Sharpe: 0.36
Max drawdown: -18.04%
Average turnover: 73.75%
Average cost drag: 0.038%
Report: artifacts\report.md
```

Exact numbers are deterministic for the default seed and may change only when
the research configuration or implementation changes.

## Project Structure

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
  scripts/
    run_tests.py
  src/
    alphalab_agent/
      cli.py
      config.py
      pipeline.py
      data/synthetic.py
      research/panel.py
      research/factors.py
      research/labels.py
      backtest/portfolio.py
      backtest/metrics.py
      review/checks.py
      report/markdown.py
  tests/
```

This is a standard `src` layout. Install with `python -m pip install -e ".[dev]"`
before running module commands without setting `PYTHONPATH`.

## v0.1 Features

- Fixed-seed synthetic OHLCV data.
- Stable date-symbol panel builder.
- Baseline factors: momentum, reversal, low volatility, and volume trend.
- Cross-sectional z-score composite factor score.
- Forward return label with explicit future alignment.
- Top-k long-only equal-weight backtest.
- With-cost and without-cost equity curves.
- Risk metrics: total return, annualized return, volatility, Sharpe, max
  drawdown, win rate, turnover, and cost drag.
- Deterministic Reviewer checks.
- Markdown report generation to `artifacts/report.md`.
- Pytest-compatible test suite plus a fallback runner.

## Roadmap

### v0.1

Deterministic quant research core.

### v0.2

Research analysis upgrade, including config files, IC/RankIC, quantile analysis,
charts, and HTML report.

### v0.3

Agent-style workflow, including PlannerAgent, ResearchPlan parser, step logs, and
lightweight agent wrappers.

### v0.4

Streamlit demo.

### v0.5

Optional real data adapters.

### v0.6

Robustness and validation.

### v0.7

Public demo polish.

## Risk Disclaimer

This repository is for engineering demonstration, education, and interview
discussion. It does not provide investment advice. v0.1 uses synthetic data, does
not connect to brokers, does not place orders, and does not store real API keys.
Backtest results, especially on synthetic data, do not imply real-world
tradability or future performance.

## Interview Talking Points

- The project is a quant research workflow, not a financial Q&A bot.
- v0.1 proves the deterministic research core before adding any agent layer.
- The Reviewer makes research risks visible instead of only showing returns.
- The `src` layout, tests, CLI, and report artifact make the project easy to
  review on GitHub.
- v0.2-v0.7 optional dependencies must gracefully fall back and never break v0.1.

See `docs/PROJECT_PLAN.md` for the detailed architecture and staged plan.
