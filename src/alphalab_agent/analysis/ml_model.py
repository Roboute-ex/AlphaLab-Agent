"""Train-only supervised factor model utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from alphalab_agent.analysis.factor_analysis import calculate_quantile_returns


@dataclass(frozen=True)
class SupervisedModelBundle:
    """A deterministic linear factor model fitted on one train window."""

    model_type: str
    factor_cols: list[str]
    label_col: str
    coefficients: dict[str, float]
    intercept: float
    feature_means: dict[str, float]
    train_start: str
    train_end: str
    n_train: int
    status: str = "PASS"
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_type": self.model_type,
            "factor_cols": self.factor_cols,
            "label_col": self.label_col,
            "coefficients": self.coefficients,
            "intercept": self.intercept,
            "feature_means": self.feature_means,
            "train_start": self.train_start,
            "train_end": self.train_end,
            "n_train": self.n_train,
            "status": self.status,
            "warnings": self.warnings,
        }


def train_supervised_factor_model(
    train_df: pd.DataFrame,
    factor_cols: list[str],
    label_col: str,
    model_type: str = "ridge",
    ridge_alpha: float = 1.0,
) -> SupervisedModelBundle:
    """Fit a deterministic train-only linear factor model."""

    if model_type not in {"ridge", "linear"}:
        raise ValueError("model_type must be one of: ridge, linear.")
    missing = set([*factor_cols, label_col]).difference(train_df.columns)
    if missing:
        raise ValueError(f"Missing columns for supervised model training: {sorted(missing)}")

    frame = train_df.copy()
    if "date" in frame:
        frame["date"] = pd.to_datetime(frame["date"])
    for column in [*factor_cols, label_col]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    valid = frame.dropna(subset=[*factor_cols, label_col]).copy()
    warnings: list[str] = []
    train_start = str(valid["date"].min().date()) if "date" in valid and not valid.empty else ""
    train_end = str(valid["date"].max().date()) if "date" in valid and not valid.empty else ""
    feature_means = {column: float(valid[column].mean()) if not valid.empty else 0.0 for column in factor_cols}
    intercept = float(valid[label_col].mean()) if not valid.empty else 0.0

    min_rows = max(5, len(factor_cols) + 2)
    if len(valid) < min_rows:
        warnings.append(f"Insufficient train rows: {len(valid)} < {min_rows}.")
        return SupervisedModelBundle(
            model_type=model_type,
            factor_cols=factor_cols,
            label_col=label_col,
            coefficients={column: 0.0 for column in factor_cols},
            intercept=intercept,
            feature_means=feature_means,
            train_start=train_start,
            train_end=train_end,
            n_train=int(len(valid)),
            status="WARN",
            warnings=warnings,
        )

    x = valid[factor_cols].to_numpy(dtype=float)
    y = valid[label_col].to_numpy(dtype=float)
    x_mean = x.mean(axis=0)
    y_mean = float(y.mean())
    x_centered = x - x_mean
    y_centered = y - y_mean
    alpha = 0.0 if model_type == "linear" else float(ridge_alpha)
    penalty = np.eye(len(factor_cols)) * alpha
    try:
        coefficients_array = np.linalg.solve(x_centered.T @ x_centered + penalty, x_centered.T @ y_centered)
    except np.linalg.LinAlgError:
        coefficients_array = np.linalg.lstsq(x_centered.T @ x_centered + penalty, x_centered.T @ y_centered, rcond=None)[0]
        warnings.append("Linear solve was singular; used deterministic least-squares fallback.")
    coefficients = {column: float(value) for column, value in zip(factor_cols, coefficients_array)}
    intercept = float(y_mean - np.dot(x_mean, coefficients_array))
    return SupervisedModelBundle(
        model_type=model_type,
        factor_cols=factor_cols,
        label_col=label_col,
        coefficients=coefficients,
        intercept=intercept,
        feature_means={column: float(value) for column, value in zip(factor_cols, x_mean)},
        train_start=train_start,
        train_end=train_end,
        n_train=int(len(valid)),
        status="WARN" if warnings else "PASS",
        warnings=warnings,
    )


def predict_supervised_factor_model(model_bundle: SupervisedModelBundle, test_df: pd.DataFrame) -> pd.Series:
    """Generate deterministic predictions for a test window."""

    missing = set(model_bundle.factor_cols).difference(test_df.columns)
    if missing:
        raise ValueError(f"Missing columns for supervised model prediction: {sorted(missing)}")
    features = test_df[model_bundle.factor_cols].copy()
    for column in model_bundle.factor_cols:
        features[column] = pd.to_numeric(features[column], errors="coerce").fillna(model_bundle.feature_means[column])
    prediction = np.full(len(features), model_bundle.intercept, dtype=float)
    for column in model_bundle.factor_cols:
        prediction += features[column].to_numpy(dtype=float) * model_bundle.coefficients[column]
    return pd.Series(prediction, index=test_df.index, name="prediction_score")


def evaluate_supervised_factor_model(
    test_df: pd.DataFrame,
    prediction_col: str,
    label_col: str,
    quantiles: int = 5,
) -> dict[str, float | int]:
    """Evaluate predictions against forward-return labels."""

    required = {prediction_col, label_col}
    missing = required.difference(test_df.columns)
    if missing:
        raise ValueError(f"Missing columns for supervised model evaluation: {sorted(missing)}")
    columns = [prediction_col, label_col]
    if "date" in test_df.columns:
        columns.append("date")
    data = test_df[columns].copy()
    data[prediction_col] = pd.to_numeric(data[prediction_col], errors="coerce")
    data[label_col] = pd.to_numeric(data[label_col], errors="coerce")
    valid = data.dropna(subset=[prediction_col, label_col])
    if valid.empty or valid[prediction_col].nunique() < 2 or valid[label_col].nunique() < 2:
        return _empty_metrics(len(valid))

    errors = valid[prediction_col] - valid[label_col]
    prediction_ic = valid[prediction_col].corr(valid[label_col], method="pearson")
    prediction_rankic = valid[prediction_col].corr(valid[label_col], method="spearman")
    quantile_frame = valid.copy()
    if "date" not in quantile_frame:
        quantile_frame["date"] = 0
    quantiles_df = calculate_quantile_returns(
        quantile_frame,
        label_col=label_col,
        score_col=prediction_col,
        quantiles=quantiles,
    )
    if quantiles_df.empty:
        top_return = 0.0
        bottom_return = 0.0
    else:
        ordered = quantiles_df.sort_values("quantile")
        bottom_return = float(ordered["mean_forward_return"].iloc[0])
        top_return = float(ordered["mean_forward_return"].iloc[-1])
    return {
        "prediction_ic": float(prediction_ic) if not pd.isna(prediction_ic) else 0.0,
        "prediction_rankic": float(prediction_rankic) if not pd.isna(prediction_rankic) else 0.0,
        "mse": float((errors**2).mean()),
        "mae": float(errors.abs().mean()),
        "hit_rate": float((np.sign(valid[prediction_col]) == np.sign(valid[label_col])).mean()),
        "top_quantile_forward_return": top_return,
        "bottom_quantile_forward_return": bottom_return,
        "top_bottom_spread": top_return - bottom_return,
        "n_test": int(len(valid)),
    }


def _empty_metrics(n_test: int) -> dict[str, float | int]:
    return {
        "prediction_ic": 0.0,
        "prediction_rankic": 0.0,
        "mse": 0.0,
        "mae": 0.0,
        "hit_rate": 0.0,
        "top_quantile_forward_return": 0.0,
        "bottom_quantile_forward_return": 0.0,
        "top_bottom_spread": 0.0,
        "n_test": int(n_test),
    }
