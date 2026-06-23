"""Robustness and validation analysis for deterministic research runs."""

from __future__ import annotations

from itertools import product

import pandas as pd

from alphalab_agent.backtest.metrics import calculate_risk_metrics
from alphalab_agent.backtest.execution import run_signal_execution_backtest
from alphalab_agent.backtest.portfolio import run_topk_long_only_backtest
from alphalab_agent.config import ResearchConfig
from alphalab_agent.research.factors import add_composite_score
from alphalab_agent.analysis.ml_model import (
    evaluate_supervised_factor_model,
    predict_supervised_factor_model,
    train_supervised_factor_model,
)
from alphalab_agent.analysis.weighting import learn_factor_weights, weights_to_frame


VALIDATION_COLUMNS = [
    "fold",
    "segment",
    "start_date",
    "end_date",
    "rows",
    "dates",
    "symbols",
    "periods",
    "total_return",
    "annualized_return",
    "annualized_volatility",
    "sharpe",
    "max_drawdown",
    "average_turnover",
    "average_cost_drag",
]

SENSITIVITY_COLUMNS = [
    "top_k",
    "transaction_cost_bps",
    "periods",
    "total_return",
    "annualized_return",
    "annualized_volatility",
    "sharpe",
    "max_drawdown",
    "average_turnover",
    "average_cost_drag",
]

ML_WALK_FORWARD_COLUMNS = [
    "fold",
    "train_start",
    "train_end",
    "test_start",
    "test_end",
    "model_type",
    "coefficients",
    "prediction_ic",
    "prediction_rankic",
    "mse",
    "mae",
    "hit_rate",
    "top_quantile_forward_return",
    "bottom_quantile_forward_return",
    "top_bottom_spread",
    "test_total_return",
    "test_sharpe",
    "test_max_drawdown",
    "n_train",
    "n_test",
    "status",
    "warnings",
]


def calculate_walk_forward_validation(
    research_frame: pd.DataFrame,
    label_col: str,
    config: ResearchConfig,
    score_col: str = "composite_score",
    factor_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Run deterministic expanding-window train/test validation.

    Each fold uses all dates before the test window as the train segment, skips
    an embargo window, and evaluates the next chronological test window. The
    function reuses the same top-k research backtest, so it is a validation view
    of the existing research logic rather than a separate strategy engine.
    """

    _validate_research_frame(research_frame, label_col, score_col)
    if config.validation_splits <= 0:
        return pd.DataFrame(columns=VALIDATION_COLUMNS)

    frame = research_frame.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    dates = frame["date"].drop_duplicates().sort_values().to_list()
    if len(dates) < 10:
        return pd.DataFrame(columns=VALIDATION_COLUMNS)

    embargo = config.validation_embargo_periods
    if embargo is None:
        embargo = max(config.forward_days, config.rebalance_every)
    embargo = max(0, int(embargo))

    initial_train_size = max(1, int(len(dates) * config.validation_train_fraction))
    remaining = len(dates) - initial_train_size - embargo
    if remaining <= 0:
        return pd.DataFrame(columns=VALIDATION_COLUMNS)
    test_window = max(1, remaining // config.validation_splits)

    rows: list[dict[str, object]] = []
    for fold in range(1, config.validation_splits + 1):
        train_end = initial_train_size + (fold - 1) * test_window
        test_start = train_end + embargo
        test_end = min(test_start + test_window, len(dates))
        if test_start >= len(dates):
            break

        train_dates = dates[:train_end]
        test_dates = dates[test_start:test_end]
        fold_score_col = score_col
        fold_frame = frame
        if factor_cols:
            train_raw = frame.loc[frame["date"].isin(train_dates)]
            weights = learn_factor_weights(
                train_raw,
                label_col=label_col,
                factor_cols=factor_cols,
                mode=config.weighting_mode,
                config_weights=config.factor_weights,
            )
            fold_score_col = "_walk_forward_score"
            fold_frame = add_composite_score(frame, weights=weights, score_col=fold_score_col)
        rows.append(
            _segment_metrics(
                frame=fold_frame.loc[fold_frame["date"].isin(train_dates)],
                fold=fold,
                segment="train",
                label_col=label_col,
                score_col=fold_score_col,
                config=config,
            )
        )
        rows.append(
            _segment_metrics(
                frame=fold_frame.loc[fold_frame["date"].isin(test_dates)],
                fold=fold,
                segment="test",
                label_col=label_col,
                score_col=fold_score_col,
                config=config,
            )
        )

    return pd.DataFrame(rows, columns=VALIDATION_COLUMNS)


def calculate_walk_forward_factor_weights(
    research_frame: pd.DataFrame,
    label_col: str,
    config: ResearchConfig,
    factor_cols: list[str],
) -> pd.DataFrame:
    """Return train-only learned factor weights for each walk-forward fold."""

    missing = {"date", "symbol", label_col, *factor_cols}.difference(research_frame.columns)
    if missing:
        raise ValueError(f"Missing research frame columns for walk-forward weights: {sorted(missing)}")
    frame = research_frame.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    dates = frame["date"].drop_duplicates().sort_values().to_list()
    if config.validation_splits <= 0 or len(dates) < 10:
        return pd.DataFrame(columns=["fold", "weighting_mode", "factor", "weight"])

    embargo = config.validation_embargo_periods
    if embargo is None:
        embargo = max(config.forward_days, config.rebalance_every)
    initial_train_size = max(1, int(len(dates) * config.validation_train_fraction))
    remaining = len(dates) - initial_train_size - max(0, int(embargo))
    if remaining <= 0:
        return pd.DataFrame(columns=["fold", "weighting_mode", "factor", "weight"])
    test_window = max(1, remaining // config.validation_splits)

    weights_by_fold: dict[int, dict[str, float]] = {}
    for fold in range(1, config.validation_splits + 1):
        train_end = initial_train_size + (fold - 1) * test_window
        if train_end >= len(dates):
            break
        train_dates = dates[:train_end]
        train_frame = frame.loc[frame["date"].isin(train_dates)]
        weights_by_fold[fold] = learn_factor_weights(
            train_frame,
            label_col=label_col,
            factor_cols=factor_cols,
            mode=config.weighting_mode,
            config_weights=config.factor_weights,
        )
    return weights_to_frame(weights_by_fold, config.weighting_mode)


def calculate_parameter_sensitivity(
    research_frame: pd.DataFrame,
    label_col: str,
    config: ResearchConfig,
    score_col: str = "composite_score",
) -> pd.DataFrame:
    """Run a small deterministic top-k and transaction-cost sensitivity grid."""

    _validate_research_frame(research_frame, label_col, score_col)
    frame = research_frame.copy()
    n_symbols = int(frame["symbol"].nunique())
    top_k_values = _top_k_candidates(config.top_k, n_symbols, config.sensitivity_top_k_step)
    cost_values = _cost_candidates(config.transaction_cost_bps)
    periods_per_year = config.annualization / config.rebalance_every

    rows: list[dict[str, float | int]] = []
    for top_k, cost_bps in product(top_k_values, cost_values):
        if config.backtest_mode == "execution" and "return_1d" in frame.columns:
            backtest = run_signal_execution_backtest(
                research_frame=frame,
                score_col=score_col,
                top_k=top_k,
                rebalance_every=config.rebalance_every,
                transaction_cost_bps=cost_bps,
            )
        else:
            backtest = run_topk_long_only_backtest(
                research_frame=frame,
                label_col=label_col,
                score_col=score_col,
                top_k=top_k,
                rebalance_every=config.rebalance_every,
                transaction_cost_bps=cost_bps,
            )
        metrics = calculate_risk_metrics(_returns_for_metrics(backtest.portfolio_returns), periods_per_year=periods_per_year)
        rows.append(
            {
                "top_k": int(top_k),
                "transaction_cost_bps": float(cost_bps),
                "periods": int(metrics["periods"]),
                "total_return": float(metrics["total_return"]),
                "annualized_return": float(metrics["annualized_return"]),
                "annualized_volatility": float(metrics["annualized_volatility"]),
                "sharpe": float(metrics["sharpe"]),
                "max_drawdown": float(metrics["max_drawdown"]),
                "average_turnover": float(metrics["average_turnover"]),
                "average_cost_drag": float(metrics["average_cost_drag"]),
            }
        )

    return pd.DataFrame(rows, columns=SENSITIVITY_COLUMNS)


def calculate_ml_walk_forward_evaluation(
    research_frame: pd.DataFrame,
    label_col: str,
    config: ResearchConfig,
    factor_cols: list[str],
) -> pd.DataFrame:
    """Train a supervised factor model on each train window and evaluate on test windows."""

    missing = {"date", "symbol", label_col, *factor_cols}.difference(research_frame.columns)
    if missing:
        raise ValueError(f"Missing research frame columns for ML walk-forward evaluation: {sorted(missing)}")
    if config.validation_splits <= 0:
        return pd.DataFrame(columns=ML_WALK_FORWARD_COLUMNS)

    frame = research_frame.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    dates = frame["date"].drop_duplicates().sort_values().to_list()
    if len(dates) < 10:
        return pd.DataFrame(columns=ML_WALK_FORWARD_COLUMNS)

    embargo = config.validation_embargo_periods
    if embargo is None:
        embargo = max(config.forward_days, config.rebalance_every)
    embargo = max(0, int(embargo))
    initial_train_size = max(1, int(len(dates) * config.validation_train_fraction))
    remaining = len(dates) - initial_train_size - embargo
    if remaining <= 0:
        return pd.DataFrame(columns=ML_WALK_FORWARD_COLUMNS)
    test_window = max(1, remaining // config.validation_splits)

    rows: list[dict[str, object]] = []
    periods_per_year = config.annualization / config.rebalance_every
    for fold in range(1, config.validation_splits + 1):
        train_end_idx = initial_train_size + (fold - 1) * test_window
        test_start_idx = train_end_idx + embargo
        test_end_idx = min(test_start_idx + test_window, len(dates))
        if test_start_idx >= len(dates):
            break

        train_dates = dates[:train_end_idx]
        test_dates = dates[test_start_idx:test_end_idx]
        train_frame = frame.loc[frame["date"].isin(train_dates)].copy()
        test_frame = frame.loc[frame["date"].isin(test_dates)].copy()
        warnings: list[str] = []
        status = "PASS"
        if train_frame.empty or test_frame.empty:
            status = "WARN"
            warnings.append("Train or test window is empty.")

        model = train_supervised_factor_model(
            train_frame,
            factor_cols=factor_cols,
            label_col=label_col,
            model_type=config.model_type,
        )
        warnings.extend(model.warnings)
        if model.status != "PASS":
            status = "WARN"

        if test_frame.empty:
            metrics = _empty_ml_metrics()
            risk_metrics = calculate_risk_metrics(pd.DataFrame(columns=["net_return"]), periods_per_year=periods_per_year)
        else:
            test_frame = test_frame.copy()
            test_frame["prediction_score"] = predict_supervised_factor_model(model, test_frame)
            metrics = evaluate_supervised_factor_model(
                test_frame,
                prediction_col="prediction_score",
                label_col=label_col,
                quantiles=config.quantiles,
            )
            if int(metrics["n_test"]) < max(10, config.top_k):
                status = "WARN"
                warnings.append("Test sample is small for supervised evaluation.")
            top_k = min(config.top_k, int(test_frame["symbol"].nunique()))
            if top_k <= 0:
                risk_metrics = calculate_risk_metrics(pd.DataFrame(columns=["net_return"]), periods_per_year=periods_per_year)
                status = "WARN"
                warnings.append("No symbols available for ML OOS backtest.")
            elif config.backtest_mode == "execution" and "return_1d" in test_frame.columns:
                backtest = run_signal_execution_backtest(
                    research_frame=test_frame,
                    score_col="prediction_score",
                    top_k=top_k,
                    rebalance_every=config.rebalance_every,
                    transaction_cost_bps=config.transaction_cost_bps,
                )
                risk_metrics = calculate_risk_metrics(
                    _returns_for_metrics(backtest.portfolio_returns),
                    periods_per_year=periods_per_year,
                )
            else:
                backtest = run_topk_long_only_backtest(
                    research_frame=test_frame,
                    label_col=label_col,
                    score_col="prediction_score",
                    top_k=top_k,
                    rebalance_every=config.rebalance_every,
                    transaction_cost_bps=config.transaction_cost_bps,
                )
                risk_metrics = calculate_risk_metrics(
                    _returns_for_metrics(backtest.portfolio_returns),
                    periods_per_year=periods_per_year,
                )

        rows.append(
            {
                "fold": fold,
                "train_start": str(train_frame["date"].min().date()) if not train_frame.empty else "",
                "train_end": str(train_frame["date"].max().date()) if not train_frame.empty else "",
                "test_start": str(test_frame["date"].min().date()) if not test_frame.empty else "",
                "test_end": str(test_frame["date"].max().date()) if not test_frame.empty else "",
                "model_type": config.model_type,
                "coefficients": model.coefficients,
                "prediction_ic": float(metrics["prediction_ic"]),
                "prediction_rankic": float(metrics["prediction_rankic"]),
                "mse": float(metrics["mse"]),
                "mae": float(metrics["mae"]),
                "hit_rate": float(metrics["hit_rate"]),
                "top_quantile_forward_return": float(metrics["top_quantile_forward_return"]),
                "bottom_quantile_forward_return": float(metrics["bottom_quantile_forward_return"]),
                "top_bottom_spread": float(metrics["top_bottom_spread"]),
                "test_total_return": float(risk_metrics["total_return"]),
                "test_sharpe": float(risk_metrics["sharpe"]),
                "test_max_drawdown": float(risk_metrics["max_drawdown"]),
                "n_train": int(model.n_train),
                "n_test": int(metrics["n_test"]),
                "status": status,
                "warnings": "; ".join(warnings),
            }
        )
    return pd.DataFrame(rows, columns=ML_WALK_FORWARD_COLUMNS)


def _segment_metrics(
    frame: pd.DataFrame,
    fold: int,
    segment: str,
    label_col: str,
    score_col: str,
    config: ResearchConfig,
) -> dict[str, object]:
    periods_per_year = config.annualization / config.rebalance_every
    if frame.empty:
        metrics = calculate_risk_metrics(pd.DataFrame(columns=["net_return"]), periods_per_year=periods_per_year)
        return _validation_row(frame, fold, segment, metrics)

    if config.backtest_mode == "execution" and "return_1d" in frame.columns:
        backtest = run_signal_execution_backtest(
            research_frame=frame,
            score_col=score_col,
            top_k=min(config.top_k, int(frame["symbol"].nunique())),
            rebalance_every=config.rebalance_every,
            transaction_cost_bps=config.transaction_cost_bps,
        )
    else:
        backtest = run_topk_long_only_backtest(
            research_frame=frame,
            label_col=label_col,
            score_col=score_col,
            top_k=min(config.top_k, int(frame["symbol"].nunique())),
            rebalance_every=config.rebalance_every,
            transaction_cost_bps=config.transaction_cost_bps,
        )
    metrics = calculate_risk_metrics(_returns_for_metrics(backtest.portfolio_returns), periods_per_year=periods_per_year)
    return _validation_row(frame, fold, segment, metrics)


def _validation_row(
    frame: pd.DataFrame,
    fold: int,
    segment: str,
    metrics: dict[str, float | int],
) -> dict[str, object]:
    if frame.empty:
        start_date = ""
        end_date = ""
    else:
        start_date = str(frame["date"].min().date())
        end_date = str(frame["date"].max().date())
    return {
        "fold": fold,
        "segment": segment,
        "start_date": start_date,
        "end_date": end_date,
        "rows": int(len(frame)),
        "dates": int(frame["date"].nunique()) if "date" in frame else 0,
        "symbols": int(frame["symbol"].nunique()) if "symbol" in frame else 0,
        "periods": int(metrics["periods"]),
        "total_return": float(metrics["total_return"]),
        "annualized_return": float(metrics["annualized_return"]),
        "annualized_volatility": float(metrics["annualized_volatility"]),
        "sharpe": float(metrics["sharpe"]),
        "max_drawdown": float(metrics["max_drawdown"]),
        "average_turnover": float(metrics["average_turnover"]),
        "average_cost_drag": float(metrics["average_cost_drag"]),
    }


def _empty_ml_metrics() -> dict[str, float | int]:
    return {
        "prediction_ic": 0.0,
        "prediction_rankic": 0.0,
        "mse": 0.0,
        "mae": 0.0,
        "hit_rate": 0.0,
        "top_quantile_forward_return": 0.0,
        "bottom_quantile_forward_return": 0.0,
        "top_bottom_spread": 0.0,
        "n_test": 0,
    }


def _returns_for_metrics(portfolio_returns: pd.DataFrame) -> pd.DataFrame:
    if "net_return" in portfolio_returns.columns:
        return portfolio_returns
    return pd.DataFrame(columns=["net_return"])


def _top_k_candidates(top_k: int, n_symbols: int, step: int) -> list[int]:
    step = max(1, int(step))
    candidates = {max(1, top_k - step), top_k, min(n_symbols, top_k + step)}
    return sorted(value for value in candidates if 1 <= value <= n_symbols)


def _cost_candidates(transaction_cost_bps: float) -> list[float]:
    if transaction_cost_bps > 0:
        candidates = {0.0, float(transaction_cost_bps), float(transaction_cost_bps * 2.0)}
    else:
        candidates = {0.0, 5.0, 10.0}
    return sorted(candidates)


def _validate_research_frame(research_frame: pd.DataFrame, label_col: str, score_col: str) -> None:
    required = {"date", "symbol", label_col, score_col}
    missing = required.difference(research_frame.columns)
    if missing:
        raise ValueError(f"Missing research frame columns for robustness analysis: {sorted(missing)}")
