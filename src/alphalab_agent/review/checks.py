"""Deterministic reviewer checks for v0 research artifacts."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from alphalab_agent.config import ResearchConfig


@dataclass(frozen=True)
class ReviewCheck:
    """A single deterministic reviewer result."""

    name: str
    status: str
    severity: str
    message: str


def run_reviewer_checks(
    panel: pd.DataFrame,
    scored_factors: pd.DataFrame,
    portfolio_returns: pd.DataFrame,
    metrics: dict[str, float | int],
    config: ResearchConfig,
) -> list[ReviewCheck]:
    """Run rule-based checks over the research output."""

    checks: list[ReviewCheck] = []
    unique_dates = panel["date"].nunique() if "date" in panel else 0
    unique_symbols = panel["symbol"].nunique() if "symbol" in panel else 0

    checks.append(
        _check(
            name="sample_size",
            passed=unique_dates >= 120 and unique_symbols >= config.top_k,
            warn=unique_dates >= 60 and unique_symbols >= config.top_k,
            message=(
                f"Panel has {unique_dates} dates and {unique_symbols} symbols; "
                "v0 expects enough history for rolling factors."
            ),
        )
    )

    score_missing_rate = 1.0
    if "composite_score" in scored_factors and len(scored_factors) > 0:
        score_missing_rate = float(scored_factors["composite_score"].isna().mean())
    checks.append(
        _check(
            name="factor_score_coverage",
            passed=score_missing_rate <= 0.35,
            warn=score_missing_rate <= 0.55,
            message=f"Composite score missing rate is {score_missing_rate:.1%}.",
        )
    )

    checks.append(
        _check(
            name="backtest_periods",
            passed=int(metrics.get("periods", 0)) >= 40,
            warn=int(metrics.get("periods", 0)) >= 15,
            message=f"Backtest produced {int(metrics.get('periods', 0))} rebalance periods.",
        )
    )

    max_drawdown = float(metrics.get("max_drawdown", 0.0))
    checks.append(
        _check(
            name="drawdown_control",
            passed=max_drawdown >= -0.35,
            warn=max_drawdown >= -0.60,
            message=f"Max drawdown is {max_drawdown:.2%}.",
        )
    )

    sharpe = float(metrics.get("sharpe", 0.0))
    checks.append(
        _check(
            name="sharpe_sanity",
            passed=sharpe >= 0.0,
            warn=sharpe >= -0.5,
            message=f"Sharpe is {sharpe:.2f}; synthetic data can still produce weak signals.",
        )
    )

    average_turnover = float(metrics.get("average_turnover", 0.0))
    checks.append(
        _check(
            name="turnover_sanity",
            passed=average_turnover <= 0.65,
            warn=average_turnover <= 0.90,
            message=f"Average one-way turnover is {average_turnover:.2%}.",
        )
    )

    cost_drag = 0.0
    if not portfolio_returns.empty and "transaction_cost" in portfolio_returns:
        cost_drag = float(portfolio_returns["transaction_cost"].mean())
    checks.append(
        _check(
            name="cost_drag",
            passed=cost_drag <= 0.001,
            warn=cost_drag <= 0.003,
            message=f"Average period transaction cost drag is {cost_drag:.3%}.",
        )
    )

    checks.append(
        ReviewCheck(
            name="v0_scope",
            status="PASS",
            severity="info",
            message="v0 uses synthetic data, no LLM, no external market API, and no live trading.",
        )
    )
    return checks


def summarize_review(checks: list[ReviewCheck]) -> str:
    """Return PASS/WARN/FAIL for a list of reviewer checks."""

    statuses = {check.status for check in checks}
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"


def _check(name: str, passed: bool, warn: bool, message: str) -> ReviewCheck:
    if passed:
        return ReviewCheck(name=name, status="PASS", severity="info", message=message)
    if warn:
        return ReviewCheck(name=name, status="WARN", severity="warning", message=message)
    return ReviewCheck(name=name, status="FAIL", severity="error", message=message)
