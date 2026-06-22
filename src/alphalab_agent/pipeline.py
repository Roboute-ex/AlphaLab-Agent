"""Deterministic research pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from alphalab_agent.analysis.factor_analysis import calculate_factor_ic, calculate_quantile_returns
from alphalab_agent.analysis.robustness import calculate_parameter_sensitivity, calculate_walk_forward_validation
from alphalab_agent.backtest.metrics import calculate_risk_metrics
from alphalab_agent.backtest.portfolio import PortfolioBacktestResult, run_topk_long_only_backtest
from alphalab_agent.config import ResearchConfig
from alphalab_agent.data.synthetic import generate_synthetic_ohlcv
from alphalab_agent.report.charts import write_equity_chart
from alphalab_agent.report.html import render_html_report, write_html_report
from alphalab_agent.report.markdown import render_markdown_report, write_markdown_report
from alphalab_agent.research.factors import FACTOR_COLUMNS, add_composite_score, calculate_factors
from alphalab_agent.research.labels import add_forward_returns
from alphalab_agent.research.panel import build_price_panel
from alphalab_agent.review.checks import ReviewCheck, run_reviewer_checks


@dataclass(frozen=True)
class ResearchArtifacts:
    """All material outputs from a research run."""

    raw_data: pd.DataFrame
    panel: pd.DataFrame
    factors: pd.DataFrame
    labels: pd.DataFrame
    research_frame: pd.DataFrame
    backtest: PortfolioBacktestResult
    metrics: dict[str, float | int]
    factor_ic: pd.DataFrame
    quantile_returns: pd.DataFrame
    walk_forward_validation: pd.DataFrame
    sensitivity_analysis: pd.DataFrame
    review_checks: list[ReviewCheck]
    report_markdown: str
    report_path: Path | None
    report_html: str | None
    html_report_path: Path | None
    chart_paths: dict[str, Path]


def run_v0_pipeline(
    config: ResearchConfig | None = None,
    write_report: bool = True,
    raw_data: pd.DataFrame | None = None,
) -> ResearchArtifacts:
    """Run the full research workflow."""

    config = config or ResearchConfig()
    raw_data = raw_data.copy() if raw_data is not None else generate_synthetic_ohlcv(config)
    panel = build_price_panel(raw_data)
    factors = calculate_factors(panel)
    scored_factors = add_composite_score(factors, weights=config.factor_weights)
    labels = add_forward_returns(panel, periods=config.forward_days)
    label_col = f"forward_return_{config.forward_days}d"

    research_frame = scored_factors.merge(labels, on=["date", "symbol"], how="inner")
    analysis_factors = [*FACTOR_COLUMNS, "composite_score"]
    factor_ic = calculate_factor_ic(research_frame, label_col=label_col, factor_cols=analysis_factors)
    quantile_returns = calculate_quantile_returns(
        research_frame,
        label_col=label_col,
        score_col="composite_score",
        quantiles=config.quantiles,
    )
    walk_forward_validation = calculate_walk_forward_validation(
        research_frame,
        label_col=label_col,
        score_col="composite_score",
        config=config,
    )
    sensitivity_analysis = calculate_parameter_sensitivity(
        research_frame,
        label_col=label_col,
        score_col="composite_score",
        config=config,
    )
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
    review_checks = run_reviewer_checks(
        panel,
        scored_factors,
        backtest.portfolio_returns,
        metrics,
        config,
        walk_forward_validation=walk_forward_validation,
        sensitivity_analysis=sensitivity_analysis,
    )
    report_markdown = render_markdown_report(
        config=config,
        metrics=metrics,
        factor_ic=factor_ic,
        quantile_returns=quantile_returns,
        walk_forward_validation=walk_forward_validation,
        sensitivity_analysis=sensitivity_analysis,
        checks=review_checks,
        portfolio_returns=backtest.portfolio_returns,
        positions=backtest.positions,
    )

    report_path = None
    report_html = None
    html_report_path = None
    chart_paths: dict[str, Path] = {}
    if write_report:
        report_path = write_markdown_report(config.output_dir / config.report_name, report_markdown)
        if config.generate_html:
            report_html = render_html_report(report_markdown, title="AlphaLab Agent v0.6 Research Report")
            html_report_path = write_html_report(config.output_dir / config.html_report_name, report_html)
        if config.generate_charts:
            chart_path = write_equity_chart(config.output_dir, backtest.portfolio_returns)
            if chart_path is not None:
                chart_paths["equity_curve"] = chart_path

    return ResearchArtifacts(
        raw_data=raw_data,
        panel=panel,
        factors=scored_factors,
        labels=labels,
        research_frame=research_frame,
        backtest=backtest,
        metrics=metrics,
        factor_ic=factor_ic,
        quantile_returns=quantile_returns,
        walk_forward_validation=walk_forward_validation,
        sensitivity_analysis=sensitivity_analysis,
        review_checks=review_checks,
        report_markdown=report_markdown,
        report_path=report_path,
        report_html=report_html,
        html_report_path=html_report_path,
        chart_paths=chart_paths,
    )
