"""Factor IC and quantile return analysis."""

from __future__ import annotations

import math

import pandas as pd


def calculate_factor_ic(
    research_frame: pd.DataFrame,
    label_col: str,
    factor_cols: list[str],
) -> pd.DataFrame:
    """Calculate mean IC, RankIC, and ICIR for each factor."""

    required = {"date", label_col, *factor_cols}
    missing = required.difference(research_frame.columns)
    if missing:
        raise ValueError(f"Missing columns for factor IC: {sorted(missing)}")

    rows: list[dict[str, float | int | str]] = []
    for factor in factor_cols:
        daily_rows: list[dict[str, float]] = []
        for _, cross_section in research_frame.groupby("date", sort=False):
            data = cross_section[[factor, label_col]].dropna()
            if len(data) < 3 or data[factor].nunique() < 2 or data[label_col].nunique() < 2:
                continue
            pearson = data[factor].corr(data[label_col], method="pearson")
            rank = data[factor].corr(data[label_col], method="spearman")
            if not pd.isna(pearson) and not pd.isna(rank):
                daily_rows.append({"ic": float(pearson), "rank_ic": float(rank)})

        daily = pd.DataFrame(daily_rows)
        if daily.empty:
            rows.append(
                {
                    "factor": factor,
                    "mean_ic": 0.0,
                    "mean_rank_ic": 0.0,
                    "ic_std": 0.0,
                    "icir": 0.0,
                    "observations": 0,
                }
            )
            continue

        ic_std = float(daily["ic"].std(ddof=0))
        icir = float(daily["ic"].mean() / ic_std * math.sqrt(len(daily))) if ic_std > 0 else 0.0
        rows.append(
            {
                "factor": factor,
                "mean_ic": float(daily["ic"].mean()),
                "mean_rank_ic": float(daily["rank_ic"].mean()),
                "ic_std": ic_std,
                "icir": icir,
                "observations": int(len(daily)),
            }
        )

    return pd.DataFrame(rows)


def calculate_quantile_returns(
    research_frame: pd.DataFrame,
    label_col: str,
    score_col: str = "composite_score",
    quantiles: int = 5,
) -> pd.DataFrame:
    """Calculate average forward return by score quantile."""

    if quantiles < 2:
        raise ValueError("quantiles must be at least 2.")
    required = {"date", score_col, label_col}
    missing = required.difference(research_frame.columns)
    if missing:
        raise ValueError(f"Missing columns for quantile returns: {sorted(missing)}")

    frame = research_frame[["date", score_col, label_col]].dropna().copy()
    if frame.empty:
        return pd.DataFrame(columns=["quantile", "mean_forward_return", "observations"])

    frame["quantile"] = frame.groupby("date", group_keys=False)[score_col].transform(
        lambda series: _date_quantiles(series, quantiles)
    )
    frame = frame.dropna(subset=["quantile"])
    if frame.empty:
        return pd.DataFrame(columns=["quantile", "mean_forward_return", "observations"])

    frame["quantile"] = frame["quantile"].astype(int)
    grouped = frame.groupby("quantile", sort=True)[label_col]
    result = grouped.agg(mean_forward_return="mean", observations="count").reset_index()
    return result


def _date_quantiles(series: pd.Series, quantiles: int) -> pd.Series:
    valid = series.dropna()
    if len(valid) < quantiles or valid.nunique() < quantiles:
        return pd.Series(pd.NA, index=series.index)
    ranks = series.rank(method="first")
    bucketed = pd.qcut(ranks, q=quantiles, labels=False, duplicates="drop")
    if bucketed.isna().all():
        return pd.Series(pd.NA, index=series.index)
    return bucketed + 1
