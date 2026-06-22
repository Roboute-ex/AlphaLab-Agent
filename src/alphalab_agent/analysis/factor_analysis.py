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


def calculate_factor_diagnostics(
    research_frame: pd.DataFrame,
    label_col: str,
    factor_cols: list[str],
    quantiles: int = 5,
) -> pd.DataFrame:
    """Calculate robust factor diagnostics used by the v0.7 report and Reviewer."""

    required = {"date", label_col, *factor_cols}
    missing = required.difference(research_frame.columns)
    if missing:
        raise ValueError(f"Missing columns for factor diagnostics: {sorted(missing)}")

    rows: list[dict[str, float | int | str]] = []
    for factor in factor_cols:
        daily = _daily_factor_correlations(research_frame, factor, label_col)
        quantile_stats = _factor_quantile_stats(research_frame, factor, label_col, quantiles)
        valid = research_frame[["date", factor]].copy()
        missing_rate = float(valid[factor].isna().mean()) if len(valid) else 1.0
        coverage_by_date = float(valid.groupby("date")[factor].apply(lambda series: series.notna().mean()).mean())
        ic_mean = float(daily["ic"].mean()) if not daily.empty else 0.0
        ic_std = float(daily["ic"].std(ddof=0)) if not daily.empty else 0.0
        rankic_mean = float(daily["rank_ic"].mean()) if not daily.empty else 0.0
        rankic_std = float(daily["rank_ic"].std(ddof=0)) if not daily.empty else 0.0
        rows.append(
            {
                "factor": factor,
                "ic_mean": ic_mean,
                "ic_std": ic_std,
                "icir": _safe_ratio(ic_mean, ic_std),
                "ic_positive_ratio": float((daily["ic"] > 0).mean()) if not daily.empty else 0.0,
                "ic_t_stat": _t_stat(daily["ic"]) if not daily.empty else 0.0,
                "rankic_mean": rankic_mean,
                "rankic_std": rankic_std,
                "rankicir": _safe_ratio(rankic_mean, rankic_std),
                "rankic_positive_ratio": float((daily["rank_ic"] > 0).mean()) if not daily.empty else 0.0,
                "rankic_t_stat": _t_stat(daily["rank_ic"]) if not daily.empty else 0.0,
                "top_quantile_return": quantile_stats["top_quantile_return"],
                "bottom_quantile_return": quantile_stats["bottom_quantile_return"],
                "top_bottom_spread": quantile_stats["top_bottom_spread"],
                "quantile_monotonicity_score": quantile_stats["quantile_monotonicity_score"],
                "factor_coverage_by_date": coverage_by_date if not pd.isna(coverage_by_date) else 0.0,
                "factor_missing_rate": missing_rate,
                "observations": int(len(daily)),
            }
        )
    return pd.DataFrame(rows)


def _date_quantiles(series: pd.Series, quantiles: int) -> pd.Series:
    valid = series.dropna()
    if len(valid) < quantiles or valid.nunique() < quantiles:
        return pd.Series(pd.NA, index=series.index)
    ranks = series.rank(method="first")
    bucketed = pd.qcut(ranks, q=quantiles, labels=False, duplicates="drop")
    if bucketed.isna().all():
        return pd.Series(pd.NA, index=series.index)
    return bucketed + 1


def _daily_factor_correlations(research_frame: pd.DataFrame, factor: str, label_col: str) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    for _, cross_section in research_frame.groupby("date", sort=False):
        data = cross_section[[factor, label_col]].dropna()
        if len(data) < 3 or data[factor].nunique() < 2 or data[label_col].nunique() < 2:
            continue
        ic = data[factor].corr(data[label_col], method="pearson")
        rank_ic = data[factor].corr(data[label_col], method="spearman")
        if not pd.isna(ic) and not pd.isna(rank_ic):
            rows.append({"ic": float(ic), "rank_ic": float(rank_ic)})
    return pd.DataFrame(rows)


def _factor_quantile_stats(
    research_frame: pd.DataFrame,
    factor: str,
    label_col: str,
    quantiles: int,
) -> dict[str, float]:
    quantile_returns = calculate_quantile_returns(
        research_frame,
        label_col=label_col,
        score_col=factor,
        quantiles=quantiles,
    )
    if quantile_returns.empty:
        return {
            "top_quantile_return": 0.0,
            "bottom_quantile_return": 0.0,
            "top_bottom_spread": 0.0,
            "quantile_monotonicity_score": 0.0,
        }

    ordered = quantile_returns.sort_values("quantile")
    bottom = float(ordered["mean_forward_return"].iloc[0])
    top = float(ordered["mean_forward_return"].iloc[-1])
    monotonicity = 0.0
    if len(ordered) >= 2 and ordered["mean_forward_return"].nunique() >= 2:
        corr = ordered["quantile"].corr(ordered["mean_forward_return"], method="spearman")
        monotonicity = float(corr) if not pd.isna(corr) else 0.0
    return {
        "top_quantile_return": top,
        "bottom_quantile_return": bottom,
        "top_bottom_spread": top - bottom,
        "quantile_monotonicity_score": monotonicity,
    }


def _safe_ratio(mean: float, std: float) -> float:
    return float(mean / std) if std > 0 else 0.0


def _t_stat(series: pd.Series) -> float:
    std = float(series.std(ddof=0))
    if std <= 0 or len(series) == 0:
        return 0.0
    return float(series.mean() / std * math.sqrt(len(series)))
