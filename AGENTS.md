# AGENTS.md

Guidance for coding agents working on AlphaLab Agent.

## Hard Safety Rules

- Do not connect this project to live trading.
- Do not place orders.
- Do not write, store, commit, print, or document real API keys.
- Do not use real external financial data APIs by default.
- Do not use an LLM by default in v0.1.
- Core research results must be deterministic.
- Every random process must use an explicit fixed seed.
- New features must include tests.
- Do not only show attractive returns. Always show risk metrics and Reviewer
  conclusions.
- Any v0.2-v0.7 optional dependency must have graceful fallback behavior and must
  not break the v0.1 deterministic path.

## v0.1 Boundaries

v0.1 is a local synthetic-data research workflow:

```text
synthetic market data
-> panel builder
-> factor calculation
-> forward return label
-> top-k long-only backtest
-> risk metrics
-> reviewer checks
-> report
```

## Version Roadmap

- `v0.1`: deterministic quant research core
- `v0.2`: research analysis upgrade, including config files, IC/RankIC,
  quantile analysis, charts, HTML report
- `v0.3`: agent-style workflow, including PlannerAgent, ResearchPlan parser,
  step logs, lightweight agent wrappers
- `v0.4`: Streamlit demo
- `v0.5`: optional real data adapters
- `v0.6`: robustness and validation
- `v0.7`: public demo polish

Keep v0.1 small, reproducible, and suitable for GitHub and interview demos.
