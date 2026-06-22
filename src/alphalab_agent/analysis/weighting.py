"""Train-only factor weighting utilities."""

from __future__ import annotations

import pandas as pd

from alphalab_agent.analysis.factor_analysis import calculate_factor_ic


def learn_factor_weights(
    train_frame: pd.DataFrame,
    label_col: str,
    factor_cols: list[str],
    mode: str = "equal_weight",
    config_weights: dict[str, float] | None = None,
    min_observations: int = 5,
) -> dict[str, float]:
    """Learn normalized factor weights using only a train window."""

    if mode == "equal_weight":
        return _equal_weights(factor_cols)
    if mode == "config_weight":
        return _normalize_weights(config_weights or _equal_weights(factor_cols), factor_cols)
    if mode not in {"ic_weight_train_only", "rankic_weight_train_only"}:
        raise ValueError(
            "weighting mode must be one of: equal_weight, config_weight, "
            "ic_weight_train_only, rankic_weight_train_only."
        )

    if train_frame.empty or len(train_frame.dropna(subset=[label_col])) < min_observations:
        return _equal_weights(factor_cols)

    stats = calculate_factor_ic(train_frame, label_col=label_col, factor_cols=factor_cols)
    if stats.empty:
        return _equal_weights(factor_cols)

    metric = "mean_ic" if mode == "ic_weight_train_only" else "mean_rank_ic"
    raw = {row["factor"]: float(row[metric]) for _, row in stats.iterrows()}
    normalized = _normalize_weights(raw, factor_cols)
    if all(value == 0.0 for value in normalized.values()):
        return _equal_weights(factor_cols)
    return normalized


def weights_to_frame(weights_by_fold: dict[int, dict[str, float]], mode: str) -> pd.DataFrame:
    """Convert fold weights to a stable DataFrame."""

    rows: list[dict[str, float | int | str]] = []
    for fold in sorted(weights_by_fold):
        for factor, weight in sorted(weights_by_fold[fold].items()):
            rows.append({"fold": fold, "weighting_mode": mode, "factor": factor, "weight": float(weight)})
    return pd.DataFrame(rows, columns=["fold", "weighting_mode", "factor", "weight"])


def _equal_weights(factor_cols: list[str]) -> dict[str, float]:
    if not factor_cols:
        return {}
    weight = 1.0 / len(factor_cols)
    return {factor: weight for factor in factor_cols}


def _normalize_weights(weights: dict[str, float], factor_cols: list[str]) -> dict[str, float]:
    values = {factor: float(weights.get(factor, 0.0)) for factor in factor_cols}
    total = sum(abs(value) for value in values.values())
    if total == 0:
        return _equal_weights(factor_cols)
    return {factor: value / total for factor, value in values.items()}
