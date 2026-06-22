"""Panel construction and validation."""

from __future__ import annotations

import pandas as pd


REQUIRED_OHLCV_COLUMNS = {"date", "symbol", "open", "high", "low", "close", "volume"}


def build_price_panel(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalize OHLCV data into a sorted date-symbol panel."""

    missing = REQUIRED_OHLCV_COLUMNS.difference(raw.columns)
    if missing:
        raise ValueError(f"Missing required OHLCV columns: {sorted(missing)}")

    panel = raw.copy()
    panel["date"] = pd.to_datetime(panel["date"])
    panel = panel.drop_duplicates(["date", "symbol"], keep="last")
    panel = panel.sort_values(["symbol", "date"], kind="mergesort").reset_index(drop=True)

    price_cols = ["open", "high", "low", "close"]
    if (panel[price_cols] <= 0).any().any():
        raise ValueError("OHLC prices must be positive.")
    if (panel["volume"] < 0).any():
        raise ValueError("Volume must be non-negative.")
    if (panel["high"] < panel[["open", "close"]].max(axis=1)).any():
        raise ValueError("High must be at least max(open, close).")
    if (panel["low"] > panel[["open", "close"]].min(axis=1)).any():
        raise ValueError("Low must be at most min(open, close).")

    panel["return_1d"] = panel.groupby("symbol", sort=False)["close"].pct_change()
    panel["dollar_volume"] = panel["close"] * panel["volume"]
    return panel.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)
