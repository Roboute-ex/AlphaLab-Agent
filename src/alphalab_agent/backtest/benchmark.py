"""Benchmark and baseline comparison utilities."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from alphalab_agent.backtest.execution import run_custom_execution_backtest, run_signal_execution_backtest
from alphalab_agent.backtest.metrics import calculate_risk_metrics
from alphalab_agent.config import ResearchConfig


@dataclass(frozen=True)
class BenchmarkComparison:
    """Benchmark return series and comparison summaries."""

    benchmark_returns: dict[str, pd.DataFrame]
    benchmark_metrics: pd.DataFrame
    comparison_summary: pd.DataFrame


def calculate_benchmark_comparison(
    research_frame: pd.DataFrame,
    strategy_returns: pd.DataFrame,
    config: ResearchConfig,
    score_col: str = "composite_score",
    return_col: str = "return_1d",
    factor_col: str = "momentum_20",
) -> BenchmarkComparison:
    """Compare the strategy against deterministic baseline portfolios."""

    required = {"date", "symbol", return_col}
    missing = required.difference(research_frame.columns)
    if missing:
        raise ValueError(f"Missing research frame columns for benchmarks: {sorted(missing)}")

    frame = research_frame.copy()
    n_symbols = int(frame["symbol"].nunique())
    periods_per_year = config.annualization / config.rebalance_every

    equal_weight = run_signal_execution_backtest(
        frame.assign(_equal_weight_score=0.0),
        score_col="_equal_weight_score",
        return_col=return_col,
        top_k=n_symbols,
        rebalance_every=config.rebalance_every,
        transaction_cost_bps=config.transaction_cost_bps,
    ).portfolio_returns

    random_frame = _with_random_scores(frame, seed=config.benchmark_seed)
    random_topk = run_signal_execution_backtest(
        random_frame,
        score_col="_random_score",
        return_col=return_col,
        top_k=min(config.top_k, n_symbols),
        rebalance_every=config.rebalance_every,
        transaction_cost_bps=config.transaction_cost_bps,
    ).portfolio_returns

    if factor_col not in frame.columns:
        factor_frame = frame.assign(_single_factor_score=frame.get(score_col, 0.0))
        factor_score_col = "_single_factor_score"
    else:
        factor_frame = frame
        factor_score_col = factor_col
    single_factor = run_signal_execution_backtest(
        factor_frame,
        score_col=factor_score_col,
        return_col=return_col,
        top_k=min(config.top_k, n_symbols),
        rebalance_every=config.rebalance_every,
        transaction_cost_bps=config.transaction_cost_bps,
    ).portfolio_returns

    benchmark_returns = {
        "equal_weight_universe": equal_weight,
        "random_topk": random_topk,
        f"{factor_col}_only": single_factor,
    }
    strategy_metrics = calculate_risk_metrics(strategy_returns, periods_per_year=periods_per_year)

    metrics_rows: list[dict[str, float | int | str]] = []
    comparison_rows: list[dict[str, float | int | str]] = []
    for name, returns in benchmark_returns.items():
        metrics = calculate_risk_metrics(returns, periods_per_year=periods_per_year)
        metrics_rows.append({"benchmark": name, **metrics})
        comparison_rows.append(_comparison_row(name, strategy_returns, returns, strategy_metrics, metrics))

    return BenchmarkComparison(
        benchmark_returns=benchmark_returns,
        benchmark_metrics=pd.DataFrame(metrics_rows),
        comparison_summary=pd.DataFrame(comparison_rows),
    )


def _with_random_scores(frame: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    scored = frame.sort_values(["date", "symbol"], kind="mergesort").copy()
    scores = np.empty(len(scored), dtype=float)
    for _, index in scored.groupby("date", sort=False).groups.items():
        positions = list(index)
        scores[positions] = rng.random(len(positions))
    scored["_random_score"] = scores
    return scored


def _comparison_row(
    benchmark_name: str,
    strategy_returns: pd.DataFrame,
    benchmark_returns: pd.DataFrame,
    strategy_metrics: dict[str, float | int],
    benchmark_metrics: dict[str, float | int],
) -> dict[str, float | int | str]:
    hit_rate = 0.0
    if not strategy_returns.empty and not benchmark_returns.empty:
        merged = strategy_returns[["date", "net_return"]].merge(
            benchmark_returns[["date", "net_return"]],
            on="date",
            how="inner",
            suffixes=("_strategy", "_benchmark"),
        )
        if not merged.empty:
            hit_rate = float((merged["net_return_strategy"] > merged["net_return_benchmark"]).mean())

    return {
        "benchmark": benchmark_name,
        "strategy_total_return": float(strategy_metrics["total_return"]),
        "benchmark_total_return": float(benchmark_metrics["total_return"]),
        "strategy_sharpe": float(strategy_metrics["sharpe"]),
        "benchmark_sharpe": float(benchmark_metrics["sharpe"]),
        "excess_total_return": float(strategy_metrics["total_return"]) - float(benchmark_metrics["total_return"]),
        "excess_sharpe": float(strategy_metrics["sharpe"]) - float(benchmark_metrics["sharpe"]),
        "strategy_max_drawdown": float(strategy_metrics["max_drawdown"]),
        "benchmark_max_drawdown": float(benchmark_metrics["max_drawdown"]),
        "hit_rate_vs_benchmark": hit_rate,
    }
