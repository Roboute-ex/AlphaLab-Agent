"""Robustness and validation analysis for deterministic research runs."""

from __future__ import annotations

from itertools import product

import pandas as pd

from alphalab_agent.backtest.metrics import calculate_risk_metrics
from alphalab_agent.backtest.portfolio import run_topk_long_only_backtest
from alphalab_agent.config import ResearchConfig


VALIDATION_COLUMNS = [
    "fold",
    "segment",
    "start_date",
    "end_date",
    "rows",
    "dates",
    "symbols",
    "periods",
    "total_return",
    "annualized_return",
    "annualized_volatility",
    "sharpe",
    "max_drawdown",
    "average_turnover",
    "average_cost_drag",
]

SENSITIVITY_COLUMNS = [
    "top_k",
    "transaction_cost_bps",
    "periods",
    "total_return",
    "annualized_return",
    "annualized_volatility",
    "sharpe",
    "max_drawdown",
    "average_turnover",
    "average_cost_drag",
]


def calculate_walk_forward_validation(
    research_frame: pd.DataFrame,
    label_col: str,
    config: ResearchConfig,
    score_col: str = "composite_score",
) -> pd.DataFrame:
    """Run deterministic expanding-window train/test validation.

    Each fold uses all dates before the test window as the train segment, skips
    an embargo window, and evaluates the next chronological test window. The
    function reuses the same top-k research backtest, so it is a validation view
    of the existing research logic rather than a separate strategy engine.
    """

    _validate_research_frame(research_frame, label_col, score_col)
    if config.validation_splits <= 0:
        return pd.DataFrame(columns=VALIDATION_COLUMNS)

    frame = research_frame.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    dates = frame["date"].drop_duplicates().sort_values().to_list()
    if len(dates) < 10:
        return pd.DataFrame(columns=VALIDATION_COLUMNS)

    embargo = config.validation_embargo_periods
    if embargo is None:
        embargo = max(config.forward_days, config.rebalance_every)
    embargo = max(0, int(embargo))

    initial_train_size = max(1, int(len(dates) * config.validation_train_fraction))
    remaining = len(dates) - initial_train_size - embargo
    if remaining <= 0:
        return pd.DataFrame(columns=VALIDATION_COLUMNS)
    test_window = max(1, remaining // config.validation_splits)

    rows: list[dict[str, object]] = []
    for fold in range(1, config.validation_splits + 1):
        train_end = initial_train_size + (fold - 1) * test_window
        test_start = train_end + embargo
        test_end = min(test_start + test_window, len(dates))
        if test_start >= len(dates):
            break

        train_dates = dates[:train_end]
        test_dates = dates[test_start:test_end]
        rows.append(
            _segment_metrics(
                frame=frame.loc[frame["date"].isin(train_dates)],
                fold=fold,
                segment="train",
                label_col=label_col,
                score_col=score_col,
                config=config,
            )
        )
        rows.append(
            _segment_metrics(
                frame=frame.loc[frame["date"].isin(test_dates)],
                fold=fold,
                segment="test",
                label_col=label_col,
                score_col=score_col,
                config=config,
            )
        )

    return pd.DataFrame(rows, columns=VALIDATION_COLUMNS)


def calculate_parameter_sensitivity(
    research_frame: pd.DataFrame,
    label_col: str,
    config: ResearchConfig,
    score_col: str = "composite_score",
) -> pd.DataFrame:
    """Run a small deterministic top-k and transaction-cost sensitivity grid."""

    _validate_research_frame(research_frame, label_col, score_col)
    frame = research_frame.copy()
    n_symbols = int(frame["symbol"].nunique())
    top_k_values = _top_k_candidates(config.top_k, n_symbols, config.sensitivity_top_k_step)
    cost_values = _cost_candidates(config.transaction_cost_bps)
    periods_per_year = config.annualization / config.rebalance_every

    rows: list[dict[str, float | int]] = []
    for top_k, cost_bps in product(top_k_values, cost_values):
        backtest = run_topk_long_only_backtest(
            research_frame=frame,
            label_col=label_col,
            score_col=score_col,
            top_k=top_k,
            rebalance_every=config.rebalance_every,
            transaction_cost_bps=cost_bps,
        )
        metrics = calculate_risk_metrics(backtest.portfolio_returns, periods_per_year=periods_per_year)
        rows.append(
            {
                "top_k": int(top_k),
                "transaction_cost_bps": float(cost_bps),
                "periods": int(metrics["periods"]),
                "total_return": float(metrics["total_return"]),
                "annualized_return": float(metrics["annualized_return"]),
                "annualized_volatility": float(metrics["annualized_volatility"]),
                "sharpe": float(metrics["sharpe"]),
                "max_drawdown": float(metrics["max_drawdown"]),
                "average_turnover": float(metrics["average_turnover"]),
                "average_cost_drag": float(metrics["average_cost_drag"]),
            }
        )

    return pd.DataFrame(rows, columns=SENSITIVITY_COLUMNS)


def _segment_metrics(
    frame: pd.DataFrame,
    fold: int,
    segment: str,
    label_col: str,
    score_col: str,
    config: ResearchConfig,
) -> dict[str, object]:
    periods_per_year = config.annualization / config.rebalance_every
    if frame.empty:
        metrics = calculate_risk_metrics(pd.DataFrame(columns=["net_return"]), periods_per_year=periods_per_year)
        return _validation_row(frame, fold, segment, metrics)

    backtest = run_topk_long_only_backtest(
        research_frame=frame,
        label_col=label_col,
        score_col=score_col,
        top_k=min(config.top_k, int(frame["symbol"].nunique())),
        rebalance_every=config.rebalance_every,
        transaction_cost_bps=config.transaction_cost_bps,
    )
    metrics = calculate_risk_metrics(backtest.portfolio_returns, periods_per_year=periods_per_year)
    return _validation_row(frame, fold, segment, metrics)


def _validation_row(
    frame: pd.DataFrame,
    fold: int,
    segment: str,
    metrics: dict[str, float | int],
) -> dict[str, object]:
    if frame.empty:
        start_date = ""
        end_date = ""
    else:
        start_date = str(frame["date"].min().date())
        end_date = str(frame["date"].max().date())
    return {
        "fold": fold,
        "segment": segment,
        "start_date": start_date,
        "end_date": end_date,
        "rows": int(len(frame)),
        "dates": int(frame["date"].nunique()) if "date" in frame else 0,
        "symbols": int(frame["symbol"].nunique()) if "symbol" in frame else 0,
        "periods": int(metrics["periods"]),
        "total_return": float(metrics["total_return"]),
        "annualized_return": float(metrics["annualized_return"]),
        "annualized_volatility": float(metrics["annualized_volatility"]),
        "sharpe": float(metrics["sharpe"]),
        "max_drawdown": float(metrics["max_drawdown"]),
        "average_turnover": float(metrics["average_turnover"]),
        "average_cost_drag": float(metrics["average_cost_drag"]),
    }


def _top_k_candidates(top_k: int, n_symbols: int, step: int) -> list[int]:
    step = max(1, int(step))
    candidates = {max(1, top_k - step), top_k, min(n_symbols, top_k + step)}
    return sorted(value for value in candidates if 1 <= value <= n_symbols)


def _cost_candidates(transaction_cost_bps: float) -> list[float]:
    if transaction_cost_bps > 0:
        candidates = {0.0, float(transaction_cost_bps), float(transaction_cost_bps * 2.0)}
    else:
        candidates = {0.0, 5.0, 10.0}
    return sorted(candidates)


def _validate_research_frame(research_frame: pd.DataFrame, label_col: str, score_col: str) -> None:
    required = {"date", "symbol", label_col, score_col}
    missing = required.difference(research_frame.columns)
    if missing:
        raise ValueError(f"Missing research frame columns for robustness analysis: {sorted(missing)}")
