"""Deterministic research pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from alphalab_agent.analysis.factor_analysis import (
    calculate_factor_diagnostics,
    calculate_factor_ic,
    calculate_quantile_returns,
)
from alphalab_agent.analysis.robustness import (
    calculate_parameter_sensitivity,
    calculate_walk_forward_factor_weights,
    calculate_walk_forward_validation,
)
from alphalab_agent.backtest.benchmark import BenchmarkComparison, calculate_benchmark_comparison
from alphalab_agent.backtest.execution import run_signal_execution_backtest
from alphalab_agent.backtest.metrics import calculate_risk_metrics
from alphalab_agent.backtest.portfolio import PortfolioBacktestResult, run_topk_long_only_backtest
from alphalab_agent.config import ResearchConfig
from alphalab_agent.data.synthetic import generate_synthetic_ohlcv
from alphalab_agent.report.charts import write_equity_chart
from alphalab_agent.report.html import render_html_report, write_html_report
from alphalab_agent.report.manifest import build_run_manifest, write_run_manifest
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
    factor_diagnostics: pd.DataFrame
    quantile_returns: pd.DataFrame
    benchmark_comparison: BenchmarkComparison
    walk_forward_validation: pd.DataFrame
    walk_forward_weights: pd.DataFrame
    sensitivity_analysis: pd.DataFrame
    review_checks: list[ReviewCheck]
    report_markdown: str
    report_path: Path | None
    report_html: str | None
    html_report_path: Path | None
    chart_paths: dict[str, Path]
    manifest_path: Path | None


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

    realized_returns = panel[["date", "symbol", "return_1d"]]
    research_frame = scored_factors.merge(labels, on=["date", "symbol"], how="inner")
    research_frame = research_frame.merge(realized_returns, on=["date", "symbol"], how="left")
    analysis_factors = [*FACTOR_COLUMNS, "composite_score"]
    factor_ic = calculate_factor_ic(research_frame, label_col=label_col, factor_cols=analysis_factors)
    factor_diagnostics = calculate_factor_diagnostics(
        research_frame,
        label_col=label_col,
        factor_cols=analysis_factors,
        quantiles=config.quantiles,
    )
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
        factor_cols=FACTOR_COLUMNS,
    )
    walk_forward_weights = calculate_walk_forward_factor_weights(
        research_frame,
        label_col=label_col,
        config=config,
        factor_cols=FACTOR_COLUMNS,
    )
    sensitivity_analysis = calculate_parameter_sensitivity(
        research_frame,
        label_col=label_col,
        score_col="composite_score",
        config=config,
    )
    if config.backtest_mode == "execution":
        backtest = run_signal_execution_backtest(
            research_frame=research_frame,
            score_col="composite_score",
            top_k=config.top_k,
            rebalance_every=config.rebalance_every,
            transaction_cost_bps=config.transaction_cost_bps,
        )
    else:
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
    benchmark_comparison = calculate_benchmark_comparison(
        research_frame=research_frame,
        strategy_returns=backtest.portfolio_returns,
        config=config,
        score_col="composite_score",
    )
    review_checks = run_reviewer_checks(
        panel,
        scored_factors,
        backtest.portfolio_returns,
        metrics,
        config,
        walk_forward_validation=walk_forward_validation,
        walk_forward_weights=walk_forward_weights,
        sensitivity_analysis=sensitivity_analysis,
        benchmark_comparison=benchmark_comparison.comparison_summary,
        factor_diagnostics=factor_diagnostics,
    )
    report_markdown = render_markdown_report(
        config=config,
        metrics=metrics,
        factor_ic=factor_ic,
        factor_diagnostics=factor_diagnostics,
        quantile_returns=quantile_returns,
        benchmark_comparison=benchmark_comparison.comparison_summary,
        benchmark_metrics=benchmark_comparison.benchmark_metrics,
        walk_forward_validation=walk_forward_validation,
        walk_forward_weights=walk_forward_weights,
        sensitivity_analysis=sensitivity_analysis,
        manifest_path=config.output_dir / "run_manifest.json" if config.generate_manifest else None,
        checks=review_checks,
        portfolio_returns=backtest.portfolio_returns,
        positions=backtest.positions,
    )

    report_path = None
    report_html = None
    html_report_path = None
    chart_paths: dict[str, Path] = {}
    manifest_path = None
    if write_report:
        report_path = write_markdown_report(config.output_dir / config.report_name, report_markdown)
        if config.generate_html:
            report_html = render_html_report(report_markdown, title="AlphaLab Agent v0.7 Research Report")
            html_report_path = write_html_report(config.output_dir / config.html_report_name, report_html)
        if config.generate_charts:
            chart_path = write_equity_chart(config.output_dir, backtest.portfolio_returns)
            if chart_path is not None:
                chart_paths["equity_curve"] = chart_path
        if config.generate_manifest:
            manifest = build_run_manifest(
                config=config,
                metrics=metrics,
                checks=review_checks,
                report_path=report_path,
                html_report_path=html_report_path,
                chart_paths=chart_paths,
                benchmark_summary=benchmark_comparison.comparison_summary,
            )
            manifest_path = write_run_manifest(config.output_dir / "run_manifest.json", manifest)

    return ResearchArtifacts(
        raw_data=raw_data,
        panel=panel,
        factors=scored_factors,
        labels=labels,
        research_frame=research_frame,
        backtest=backtest,
        metrics=metrics,
        factor_ic=factor_ic,
        factor_diagnostics=factor_diagnostics,
        quantile_returns=quantile_returns,
        benchmark_comparison=benchmark_comparison,
        walk_forward_validation=walk_forward_validation,
        walk_forward_weights=walk_forward_weights,
        sensitivity_analysis=sensitivity_analysis,
        review_checks=review_checks,
        report_markdown=report_markdown,
        report_path=report_path,
        report_html=report_html,
        html_report_path=html_report_path,
        chart_paths=chart_paths,
        manifest_path=manifest_path,
    )
