"""Top-k long-only portfolio simulation."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PortfolioBacktestResult:
    """Portfolio return series and position-level records."""

    portfolio_returns: pd.DataFrame
    positions: pd.DataFrame
    label_col: str
    score_col: str


def run_topk_long_only_backtest(
    research_frame: pd.DataFrame,
    label_col: str,
    score_col: str = "composite_score",
    top_k: int = 5,
    rebalance_every: int = 5,
    transaction_cost_bps: float = 5.0,
) -> PortfolioBacktestResult:
    """Run an equal-weight top-k long-only backtest.

    Each rebalance date selects the top-k symbols by `score_col` and applies the
    precomputed forward return label. The method is deliberately simple and fully
    deterministic for v0.
    """

    if top_k <= 0:
        raise ValueError("top_k must be positive.")
    if rebalance_every <= 0:
        raise ValueError("rebalance_every must be positive.")
    if transaction_cost_bps < 0:
        raise ValueError("transaction_cost_bps cannot be negative.")

    required = {"date", "symbol", score_col, label_col}
    missing = required.difference(research_frame.columns)
    if missing:
        raise ValueError(f"Missing research frame columns: {sorted(missing)}")

    frame = research_frame.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.sort_values(["date", "symbol"], kind="mergesort")
    all_dates = frame["date"].drop_duplicates().sort_values().to_list()
    rebalance_dates = all_dates[::rebalance_every]

    return_rows: list[dict[str, object]] = []
    position_rows: list[dict[str, object]] = []
    previous_weights: dict[str, float] = {}
    gross_equity = 1.0
    net_equity = 1.0
    cost_rate = transaction_cost_bps / 10_000.0

    for date in rebalance_dates:
        cross_section = frame.loc[frame["date"] == date, ["date", "symbol", score_col, label_col]]
        cross_section = cross_section.dropna(subset=[score_col, label_col])
        if cross_section.empty:
            continue

        selected = cross_section.sort_values(score_col, ascending=False, kind="mergesort").head(top_k)
        if selected.empty:
            continue

        weight = 1.0 / len(selected)
        current_weights = {symbol: weight for symbol in selected["symbol"]}
        turnover = _calculate_turnover(previous_weights, current_weights)
        gross_return = float((selected[label_col] * weight).sum())
        cost = turnover * cost_rate
        net_return = gross_return - cost
        gross_equity *= 1.0 + gross_return
        net_equity *= 1.0 + net_return

        return_rows.append(
            {
                "date": date,
                "gross_return": gross_return,
                "transaction_cost": cost,
                "net_return": net_return,
                "turnover": turnover,
                "n_positions": len(selected),
                "equity_without_cost": gross_equity,
                "equity_with_cost": net_equity,
                "equity_curve": net_equity,
            }
        )
        for _, row in selected.iterrows():
            position_rows.append(
                {
                    "date": date,
                    "symbol": row["symbol"],
                    "weight": weight,
                    "score": float(row[score_col]),
                    "forward_return": float(row[label_col]),
                }
            )
        previous_weights = current_weights

    portfolio_returns = pd.DataFrame(return_rows)
    positions = pd.DataFrame(position_rows)
    if not portfolio_returns.empty:
        portfolio_returns = portfolio_returns.sort_values("date", kind="mergesort").reset_index(drop=True)
    if not positions.empty:
        positions = positions.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)

    return PortfolioBacktestResult(
        portfolio_returns=portfolio_returns,
        positions=positions,
        label_col=label_col,
        score_col=score_col,
    )


def run_label_based_topk_backtest(
    research_frame: pd.DataFrame,
    label_col: str,
    score_col: str = "composite_score",
    top_k: int = 5,
    rebalance_every: int = 5,
    transaction_cost_bps: float = 5.0,
) -> PortfolioBacktestResult:
    """Backward-compatible label-based top-k backtest."""

    return run_topk_long_only_backtest(
        research_frame=research_frame,
        label_col=label_col,
        score_col=score_col,
        top_k=top_k,
        rebalance_every=rebalance_every,
        transaction_cost_bps=transaction_cost_bps,
    )


def _calculate_turnover(previous: dict[str, float], current: dict[str, float]) -> float:
    if not previous:
        return sum(current.values())
    symbols = set(previous) | set(current)
    if not symbols:
        return 0.0
    return 0.5 * sum(abs(current.get(symbol, 0.0) - previous.get(symbol, 0.0)) for symbol in symbols)
