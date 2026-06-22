"""Risk metrics for portfolio return series."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def calculate_risk_metrics(
    portfolio_returns: pd.DataFrame,
    return_col: str = "net_return",
    periods_per_year: float = 252 / 5,
) -> dict[str, float | int]:
    """Calculate deterministic risk metrics from a return series."""

    if return_col not in portfolio_returns.columns:
        raise ValueError(f"Missing return column: {return_col}")
    returns = portfolio_returns[return_col].dropna().astype(float)
    if returns.empty:
        return {
            "periods": 0,
            "total_return": 0.0,
            "annualized_return": 0.0,
            "annualized_volatility": 0.0,
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "average_return": 0.0,
            "average_turnover": 0.0,
            "average_cost_drag": 0.0,
            "total_cost_drag": 0.0,
        }

    equity = (1.0 + returns).cumprod()
    total_return = float(equity.iloc[-1] - 1.0)
    if len(returns) > 0 and equity.iloc[-1] > 0:
        annualized_return = float(equity.iloc[-1] ** (periods_per_year / len(returns)) - 1.0)
    else:
        annualized_return = 0.0

    volatility = float(returns.std(ddof=0) * math.sqrt(periods_per_year))
    sharpe = 0.0
    if volatility > 0:
        sharpe = float(returns.mean() / returns.std(ddof=0) * math.sqrt(periods_per_year))

    drawdown = equity / equity.cummax() - 1.0
    average_turnover = 0.0
    if "turnover" in portfolio_returns.columns:
        average_turnover = float(portfolio_returns["turnover"].dropna().mean())
    average_cost_drag = 0.0
    if "transaction_cost" in portfolio_returns.columns:
        average_cost_drag = float(portfolio_returns["transaction_cost"].dropna().mean())

    total_cost_drag = 0.0
    if {"equity_without_cost", "equity_with_cost"}.issubset(portfolio_returns.columns):
        total_cost_drag = float(
            portfolio_returns["equity_without_cost"].iloc[-1]
            - portfolio_returns["equity_with_cost"].iloc[-1]
        )

    return {
        "periods": int(len(returns)),
        "total_return": total_return,
        "annualized_return": annualized_return,
        "annualized_volatility": volatility,
        "sharpe": sharpe,
        "max_drawdown": float(drawdown.min()),
        "win_rate": float((returns > 0).mean()),
        "average_return": float(returns.mean()),
        "average_turnover": average_turnover if not np.isnan(average_turnover) else 0.0,
        "average_cost_drag": average_cost_drag if not np.isnan(average_cost_drag) else 0.0,
        "total_cost_drag": total_cost_drag if not np.isnan(total_cost_drag) else 0.0,
    }
