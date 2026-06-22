"""Forward return label generation."""

from __future__ import annotations

import pandas as pd


def add_forward_returns(panel: pd.DataFrame, periods: int = 5) -> pd.DataFrame:
    """Create future return labels aligned to the current date.

    The label at date t is close[t + periods] / close[t] - 1 for the same symbol.
    It is intended for evaluation and backtesting, not for factor construction.
    """

    if periods <= 0:
        raise ValueError("periods must be positive.")
    required = {"date", "symbol", "close"}
    missing = required.difference(panel.columns)
    if missing:
        raise ValueError(f"Missing panel columns for labels: {sorted(missing)}")

    label_col = f"forward_return_{periods}d"
    frame = panel.sort_values(["symbol", "date"], kind="mergesort").copy()
    future_close = frame.groupby("symbol", sort=False)["close"].shift(-periods)
    frame[label_col] = future_close / frame["close"] - 1.0
    return frame[["date", "symbol", label_col]].sort_values(
        ["date", "symbol"], kind="mergesort"
    ).reset_index(drop=True)
