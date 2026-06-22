"""Baseline factor calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd


FACTOR_COLUMNS = ["momentum_20", "reversal_5", "low_volatility_20", "volume_trend_20"]


def calculate_factors(panel: pd.DataFrame) -> pd.DataFrame:
    """Calculate deterministic baseline factors from the price panel."""

    required = {"date", "symbol", "close", "volume", "return_1d"}
    missing = required.difference(panel.columns)
    if missing:
        raise ValueError(f"Missing panel columns for factors: {sorted(missing)}")

    frame = panel.sort_values(["symbol", "date"], kind="mergesort").copy()
    grouped = frame.groupby("symbol", sort=False)

    frame["momentum_20"] = grouped["close"].pct_change(20)
    frame["reversal_5"] = -grouped["close"].pct_change(5)
    rolling_vol = grouped["return_1d"].rolling(20, min_periods=20).std()
    frame["low_volatility_20"] = -rolling_vol.reset_index(level=0, drop=True)
    frame["volume_trend_20"] = grouped["volume"].pct_change(20)

    columns = ["date", "symbol", *FACTOR_COLUMNS]
    return frame[columns].sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)


def add_composite_score(
    factors: pd.DataFrame,
    weights: dict[str, float] | None = None,
    score_col: str = "composite_score",
) -> pd.DataFrame:
    """Add date-wise z-scored factors and a weighted composite score."""

    weights = weights or {name: 1.0 for name in FACTOR_COLUMNS}
    missing = set(weights).difference(factors.columns)
    if missing:
        raise ValueError(f"Missing factors for composite score: {sorted(missing)}")

    scored = factors.copy()
    z_cols: list[str] = []
    for factor_name in weights:
        z_col = f"{factor_name}_z"
        values = scored.groupby("date", sort=False)[factor_name].transform(_safe_zscore)
        scored[z_col] = values
        z_cols.append(z_col)

    total_weight = sum(abs(weight) for weight in weights.values())
    if total_weight == 0:
        raise ValueError("At least one factor weight must be non-zero.")

    composite = np.zeros(len(scored), dtype=float)
    for factor_name, weight in weights.items():
        composite += scored[f"{factor_name}_z"].fillna(0.0).to_numpy() * weight

    valid = scored[z_cols].notna().all(axis=1)
    scored[score_col] = np.where(valid, composite / total_weight, np.nan)
    return scored


def _safe_zscore(series: pd.Series) -> pd.Series:
    mean = series.mean(skipna=True)
    std = series.std(skipna=True, ddof=0)
    if pd.isna(std) or std == 0:
        return pd.Series(np.nan, index=series.index)
    return (series - mean) / std
