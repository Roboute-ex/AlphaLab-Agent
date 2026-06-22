"""v0 deterministic research pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from alphalab_agent.backtest.metrics import calculate_risk_metrics
from alphalab_agent.backtest.portfolio import PortfolioBacktestResult, run_topk_long_only_backtest
from alphalab_agent.config import ResearchConfig
from alphalab_agent.data.synthetic import generate_synthetic_ohlcv
from alphalab_agent.report.markdown import render_markdown_report, write_markdown_report
from alphalab_agent.research.factors import add_composite_score, calculate_factors
from alphalab_agent.research.labels import add_forward_returns
from alphalab_agent.research.panel import build_price_panel
from alphalab_agent.review.checks import ReviewCheck, run_reviewer_checks


@dataclass(frozen=True)
class ResearchArtifacts:
    """All material outputs from a v0 research run."""

    raw_data: pd.DataFrame
    panel: pd.DataFrame
    factors: pd.DataFrame
    labels: pd.DataFrame
    research_frame: pd.DataFrame
    backtest: PortfolioBacktestResult
    metrics: dict[str, float | int]
    review_checks: list[ReviewCheck]
    report_markdown: str
    report_path: Path | None


def run_v0_pipeline(config: ResearchConfig | None = None, write_report: bool = True) -> ResearchArtifacts:
    """Run the full v0 synthetic research workflow."""

    config = config or ResearchConfig()
    raw_data = generate_synthetic_ohlcv(config)
    panel = build_price_panel(raw_data)
    factors = calculate_factors(panel)
    scored_factors = add_composite_score(factors, weights=config.factor_weights)
    labels = add_forward_returns(panel, periods=config.forward_days)
    label_col = f"forward_return_{config.forward_days}d"

    research_frame = scored_factors.merge(labels, on=["date", "symbol"], how="inner")
    backtest = run_topk_long_only_backtest(
        research_frame=research_frame,
        label_col=label_col,
        score_col="composite_score",
        top_k=config.top_k,
        rebalance_every=config.rebalance_every,
        transaction_cost_bps=config.transaction_cost_bps,
    )
    periods_per_year = config.annualization / config.rebalance_every
    metrics = calculate_risk_metrics(backtest.portfolio_returns, periods_per_year=periods_per_year)
    review_checks = run_reviewer_checks(panel, scored_factors, backtest.portfolio_returns, metrics, config)
    report_markdown = render_markdown_report(
        config=config,
        metrics=metrics,
        checks=review_checks,
        portfolio_returns=backtest.portfolio_returns,
        positions=backtest.positions,
    )

    report_path = None
    if write_report:
        report_path = write_markdown_report(config.output_dir / config.report_name, report_markdown)

    return ResearchArtifacts(
        raw_data=raw_data,
        panel=panel,
        factors=scored_factors,
        labels=labels,
        research_frame=research_frame,
        backtest=backtest,
        metrics=metrics,
        review_checks=review_checks,
        report_markdown=report_markdown,
        report_path=report_path,
    )
