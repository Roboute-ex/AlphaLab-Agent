# AlphaLab Agent Project Plan

This document records the execution plan derived from the provided Chinese
roadmap and PDF design report, while preserving the v0.1 constraints requested for
this repository: synthetic data first, no LLM by default, no external financial
API by default, and no live trading.

## 1. Overall Architecture

AlphaLab Agent is a low- to mid-frequency stock multi-factor research workflow.
The deterministic research core is intentionally separated from optional agent
or UI layers:

```text
synthetic market data
-> panel builder
-> factor calculation
-> forward return label
-> top-k long-only backtest
-> risk metrics
-> reviewer checks
-> markdown/html report
-> optional Streamlit demo
-> optional agent workflow
```

The v0.1 code path is a fixed workflow, not a dynamic LLM agent. Later versions can
add LangGraph or Streamlit around the same tested core.

## 2. Version Roadmap

### v0.1: deterministic quant research core

- Generate reproducible synthetic OHLCV data with fixed random seeds.
- Build a date-symbol research panel.
- Calculate baseline factors: momentum, reversal, low volatility, and volume
  trend.
- Create forward return labels with explicit future alignment.
- Run an equal-weight top-k long-only backtest with transaction costs.
- Calculate risk metrics and deterministic reviewer checks.
- Generate a Markdown report and pytest-compatible tests.

### v0.2: research analysis upgrade

- Add file-based configs, experiment directories, and richer result artifacts.
- Add IC/RankIC analysis, quantile analysis, charts, and HTML reports.
- Keep external APIs and heavier storage optional.

### v0.3: agent-style workflow

- Add PlannerAgent, ResearchPlan parser, step logs, and lightweight agent
  wrappers.
- Keep LLM usage outside the numerical truth path.

### v0.4: Streamlit demo

- Add a lightweight Streamlit demo around the tested deterministic core.

### v0.5: optional real data adapters

- Add disabled-by-default adapters for real data sources.

### v0.6: robustness and validation

- Add stronger validation checks, sensitivity analysis, and research robustness
  tooling.

### v0.7: public demo polish

- Polish public demo materials, screenshots, and interview walkthroughs.

## 3. Recommended File Tree

```text
AlphaLab Agent/
  README.md
  pyproject.toml
  docs/PROJECT_PLAN.md
  scripts/run_tests.py
  examples/run_v0_research.py
  src/alphalab_agent/
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
  artifacts/
```

## 4. Module Responsibilities

- `config.py`: dataclass-based run configuration and validation.
- `data/synthetic.py`: deterministic synthetic OHLCV generator.
- `research/panel.py`: panel normalization, validation, sorting, and return
  columns.
- `research/factors.py`: baseline factor calculation, z-scoring, and composite
  score.
- `research/labels.py`: forward return label construction.
- `backtest/portfolio.py`: top-k long-only equal-weight portfolio simulation.
- `backtest/metrics.py`: risk and performance metrics.
- `review/checks.py`: deterministic reviewer checks and final status.
- `report/markdown.py`: Markdown report rendering.
- `pipeline.py`: v0.1 orchestration from data generation to report output.

## 5. Dependencies

### Minimal v0.1 dependencies

- Python 3.10+
- pandas
- numpy
- pytest for the standard test command

### Optional dependencies

- matplotlib for charts
- duckdb for local analytical storage
- streamlit for demos
- langgraph for optional workflow orchestration
- vectorbt, backtrader, or Qlib only as later optional adapters

## 6. Test Strategy

The tests focus on deterministic behavior and alignment bugs:

- Fixed-seed synthetic data reproducibility.
- OHLCV constraints.
- Panel sorting, deduplication, and return calculation.
- Factor and composite score creation.
- Forward return label alignment.
- Top-k selection, cost deduction, and portfolio output.
- Risk metric calculations on hand-checkable series.
- Pipeline smoke test and deterministic reviewer output.

## 7. README Display Structure

The README is structured for GitHub and interview use:

- Project positioning and non-goals.
- Research workflow.
- Quickstart commands.
- v0.1 features.
- v0.1-v0.7 roadmap.
- Project structure.
- Determinism and safety notes.
- Interview talking points.

## 8. Files Created For v0.1

- `README.md`
- `pyproject.toml`
- `.gitignore`
- `docs/PROJECT_PLAN.md`
- `scripts/run_tests.py`
- `examples/run_v0_research.py`
- `src/alphalab_agent/**`
- `tests/test_*.py`
- `artifacts/.gitkeep`

The generated report `artifacts/report.md` is intentionally ignored by git so
each run can regenerate it locally. The old `reports/` path may exist only as a
legacy local artifact and is not the default v0.1 output.

## 9. Open Confirmation Questions For Future Iterations

- Should v0.2 add matplotlib charts by default or keep them optional?
- Should v0.2 use JSON, YAML, or Python dataclasses for experiment configs?
- Should v0.2 prioritize factor IC analysis, HTML reporting, or charts first?
- Should v0.3 use lightweight wrappers only, or also expose a natural-language
  planner?
- If real data is added in v0.5, should the first adapter target yfinance,
  AKShare, or Qlib sample data?
