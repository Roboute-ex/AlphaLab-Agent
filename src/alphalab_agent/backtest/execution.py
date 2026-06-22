"""Execution-style signal-to-portfolio backtests."""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from alphalab_agent.backtest.portfolio import PortfolioBacktestResult, _calculate_turnover


Selector = Callable[[pd.DataFrame], pd.DataFrame]


def run_signal_execution_backtest(
    research_frame: pd.DataFrame,
    score_col: str = "composite_score",
    return_col: str = "return_1d",
    top_k: int = 5,
    rebalance_every: int = 5,
    transaction_cost_bps: float = 5.0,
) -> PortfolioBacktestResult:
    """Run a top-k execution-style backtest using realized next-period returns."""

    if top_k <= 0:
        raise ValueError("top_k must be positive.")

    def select_top_k(cross_section: pd.DataFrame) -> pd.DataFrame:
        return cross_section.dropna(subset=[score_col]).sort_values(
            score_col,
            ascending=False,
            kind="mergesort",
        ).head(top_k)

    return run_custom_execution_backtest(
        research_frame=research_frame,
        selector=select_top_k,
        score_col=score_col,
        return_col=return_col,
        rebalance_every=rebalance_every,
        transaction_cost_bps=transaction_cost_bps,
        result_label_col=return_col,
    )


def run_custom_execution_backtest(
    research_frame: pd.DataFrame,
    selector: Selector,
    score_col: str = "score",
    return_col: str = "return_1d",
    rebalance_every: int = 5,
    transaction_cost_bps: float = 5.0,
    result_label_col: str = "return_1d",
) -> PortfolioBacktestResult:
    """Run an execution backtest with a deterministic selector."""

    if rebalance_every <= 0:
        raise ValueError("rebalance_every must be positive.")
    if transaction_cost_bps < 0:
        raise ValueError("transaction_cost_bps cannot be negative.")

    required = {"date", "symbol", return_col}
    missing = required.difference(research_frame.columns)
    if missing:
        raise ValueError(f"Missing research frame columns for execution backtest: {sorted(missing)}")

    frame = research_frame.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame["symbol"] = frame["symbol"].astype(str)
    frame = frame.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)
    all_dates = frame["date"].drop_duplicates().sort_values().to_list()
    if len(all_dates) < 2:
        return PortfolioBacktestResult(
            portfolio_returns=pd.DataFrame(),
            positions=pd.DataFrame(),
            label_col=result_label_col,
            score_col=score_col,
        )

    signal_dates = all_dates[:-1:rebalance_every]
    return_rows: list[dict[str, object]] = []
    position_rows: list[dict[str, object]] = []
    previous_weights: dict[str, float] = {}
    gross_equity = 1.0
    net_equity = 1.0
    cost_rate = transaction_cost_bps / 10_000.0
    date_index = {date: idx for idx, date in enumerate(all_dates)}

    for signal_date in signal_dates:
        signal_idx = date_index[signal_date]
        next_signal_idx = min(signal_idx + rebalance_every, len(all_dates) - 1)
        holding_dates = all_dates[signal_idx + 1 : next_signal_idx + 1]
        if not holding_dates:
            continue

        cross_section = frame.loc[frame["date"] == signal_date].copy()
        selected = selector(cross_section)
        if selected.empty:
            continue

        selected = selected.drop_duplicates("symbol", keep="first")
        weight = 1.0 / len(selected)
        current_weights = {str(symbol): weight for symbol in selected["symbol"]}
        turnover = _calculate_turnover(previous_weights, current_weights)
        cost = turnover * cost_rate
        selected_scores: dict[str, float] = {}
        if score_col in selected:
            selected_scores = dict(zip(selected["symbol"].astype(str), selected[score_col].astype(float)))

        for offset, holding_date in enumerate(holding_dates):
            realized = frame.loc[
                frame["date"].eq(holding_date) & frame["symbol"].isin(current_weights),
                ["symbol", return_col],
            ].dropna(subset=[return_col])
            if realized.empty:
                continue

            realized["weight"] = realized["symbol"].map(current_weights)
            gross_return = float((realized[return_col].astype(float) * realized["weight"]).sum())
            transaction_cost = cost if offset == 0 else 0.0
            net_return = gross_return - transaction_cost
            gross_equity *= 1.0 + gross_return
            net_equity *= 1.0 + net_return

            return_rows.append(
                {
                    "date": holding_date,
                    "signal_date": signal_date,
                    "gross_return": gross_return,
                    "transaction_cost": transaction_cost,
                    "net_return": net_return,
                    "turnover": turnover if offset == 0 else 0.0,
                    "n_positions": len(current_weights),
                    "equity_without_cost": gross_equity,
                    "equity_with_cost": net_equity,
                    "equity_curve": net_equity,
                }
            )
            for _, row in realized.iterrows():
                symbol = str(row["symbol"])
                position_rows.append(
                    {
                        "signal_date": signal_date,
                        "holding_date": holding_date,
                        "date": holding_date,
                        "symbol": symbol,
                        "weight": float(row["weight"]),
                        "score": float(selected_scores.get(symbol, 0.0)),
                        "realized_return": float(row[return_col]),
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
        label_col=result_label_col,
        score_col=score_col,
    )
