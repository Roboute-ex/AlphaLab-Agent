"""Deterministic reviewer checks for v0 research artifacts."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from alphalab_agent.config import ResearchConfig


@dataclass(frozen=True)
class ReviewCheck:
    """A single deterministic reviewer result."""

    name: str
    status: str
    severity: str
    message: str


def run_reviewer_checks(
    panel: pd.DataFrame,
    scored_factors: pd.DataFrame,
    portfolio_returns: pd.DataFrame,
    metrics: dict[str, float | int],
    config: ResearchConfig,
    walk_forward_validation: pd.DataFrame | None = None,
    walk_forward_weights: pd.DataFrame | None = None,
    sensitivity_analysis: pd.DataFrame | None = None,
    benchmark_comparison: pd.DataFrame | None = None,
    factor_diagnostics: pd.DataFrame | None = None,
    data_quality: object | None = None,
    ml_oos_evaluation: pd.DataFrame | None = None,
) -> list[ReviewCheck]:
    """Run rule-based checks over the research output."""

    checks: list[ReviewCheck] = []
    if data_quality is not None:
        checks.append(_data_quality_check(data_quality))

    unique_dates = panel["date"].nunique() if "date" in panel else 0
    unique_symbols = panel["symbol"].nunique() if "symbol" in panel else 0

    sample_message = (
        f"Panel has {unique_dates} dates and {unique_symbols} symbols; "
        "v0 expects enough history for rolling factors."
    )
    if unique_dates <= 0 or unique_symbols < config.top_k:
        checks.append(ReviewCheck(name="sample_size", status="FAIL", severity="error", message=sample_message))
    else:
        checks.append(_quality_check("sample_size", unique_dates >= 120, sample_message))

    score_missing_rate = 1.0
    if "composite_score" in scored_factors and len(scored_factors) > 0:
        score_missing_rate = float(scored_factors["composite_score"].isna().mean())
    score_message = f"Composite score missing rate is {score_missing_rate:.1%}."
    if score_missing_rate >= 1.0:
        checks.append(ReviewCheck(name="factor_score_coverage", status="FAIL", severity="error", message=score_message))
    else:
        checks.append(_quality_check("factor_score_coverage", score_missing_rate <= 0.35, score_message))

    periods = int(metrics.get("periods", 0))
    periods_message = f"Backtest produced {periods} rebalance periods."
    if periods <= 0:
        checks.append(ReviewCheck(name="backtest_periods", status="FAIL", severity="error", message=periods_message))
    else:
        checks.append(_quality_check("backtest_periods", periods >= 40, periods_message))

    max_drawdown = float(metrics.get("max_drawdown", 0.0))
    checks.append(
        _quality_check(
            name="drawdown_control",
            passed=max_drawdown >= -0.35,
            message=f"Max drawdown is {max_drawdown:.2%}.",
        )
    )

    sharpe = float(metrics.get("sharpe", 0.0))
    checks.append(
        _quality_check(
            name="sharpe_sanity",
            passed=sharpe >= 0.0,
            message=f"Sharpe is {sharpe:.2f}; synthetic data can still produce weak signals.",
        )
    )

    average_turnover = float(metrics.get("average_turnover", 0.0))
    checks.append(
        _quality_check(
            name="turnover_sanity",
            passed=average_turnover <= 0.65,
            message=f"Average one-way turnover is {average_turnover:.2%}.",
        )
    )

    cost_drag = 0.0
    if not portfolio_returns.empty and "transaction_cost" in portfolio_returns:
        cost_drag = float(portfolio_returns["transaction_cost"].mean())
    checks.append(
        _quality_check(
            name="cost_drag",
            passed=cost_drag <= 0.001,
            message=f"Average period transaction cost drag is {cost_drag:.3%}.",
        )
    )

    if walk_forward_validation is not None:
        checks.extend(_walk_forward_checks(walk_forward_validation))

    if walk_forward_weights is not None:
        checks.extend(_walk_forward_weight_checks(walk_forward_weights))

    if sensitivity_analysis is not None:
        checks.extend(_sensitivity_checks(sensitivity_analysis))

    if benchmark_comparison is not None:
        checks.extend(_benchmark_checks(benchmark_comparison, metrics))

    if factor_diagnostics is not None:
        checks.extend(_factor_diagnostic_checks(factor_diagnostics))

    checks.extend(_ml_oos_checks(config, ml_oos_evaluation))

    checks.append(
        ReviewCheck(
            name="v0_scope",
            status="PASS",
            severity="info",
            message=_scope_message(config),
        )
    )
    return checks


def summarize_review(checks: list[ReviewCheck]) -> str:
    """Return PASS/WARN/FAIL for a list of reviewer checks."""

    statuses = {check.status for check in checks}
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"


def _check(name: str, passed: bool, warn: bool, message: str) -> ReviewCheck:
    if passed:
        return ReviewCheck(name=name, status="PASS", severity="info", message=message)
    if warn:
        return ReviewCheck(name=name, status="WARN", severity="warning", message=message)
    return ReviewCheck(name=name, status="FAIL", severity="error", message=message)


def _quality_check(name: str, passed: bool, message: str) -> ReviewCheck:
    """Return WARN, not FAIL, for weak but still valid research diagnostics."""

    if passed:
        return ReviewCheck(name=name, status="PASS", severity="info", message=message)
    return ReviewCheck(name=name, status="WARN", severity="warning", message=message)


def _scope_message(config: ResearchConfig) -> str:
    if config.data_source == "synthetic":
        return "v0.8 uses synthetic data by default, no LLM, no external market API, and no live trading."
    return (
        f"v0.8 data source '{config.data_source}' was explicitly selected; "
        "no LLM, no broker connection, and no live trading."
    )


def _data_quality_check(data_quality: object) -> ReviewCheck:
    status = getattr(data_quality, "status", "WARN")
    summary = getattr(data_quality, "summary", {})
    if isinstance(summary, dict):
        message = (
            f"Data quality status is {status}; rows={summary.get('rows', 0)}, "
            f"issues={summary.get('issues', 0)}."
        )
    else:
        message = f"Data quality status is {status}."
    if status == "FAIL":
        return ReviewCheck(name="data_quality", status="FAIL", severity="error", message=message)
    if status == "WARN":
        return ReviewCheck(name="data_quality", status="WARN", severity="warning", message=message)
    return ReviewCheck(name="data_quality", status="PASS", severity="info", message=message)


def _walk_forward_checks(validation: pd.DataFrame) -> list[ReviewCheck]:
    if validation.empty or "segment" not in validation:
        return [
            ReviewCheck(
                name="walk_forward_coverage",
                status="FAIL",
                severity="error",
                message="Walk-forward validation produced no folds.",
            )
        ]

    test_rows = validation.loc[validation["segment"] == "test"].copy()
    if test_rows.empty:
        return [
            ReviewCheck(
                name="walk_forward_coverage",
                status="FAIL",
                severity="error",
                message="Walk-forward validation produced no out-of-sample test segments.",
            )
        ]

    min_periods = int(test_rows["periods"].min())
    mean_oos_sharpe = float(test_rows["sharpe"].mean())
    worst_oos_drawdown = float(test_rows["max_drawdown"].min())
    checks = [
        _check(
            name="walk_forward_coverage",
            passed=min_periods >= 10,
            warn=min_periods > 0,
            message=f"Minimum out-of-sample rebalance periods per fold is {min_periods}.",
        ),
        _quality_check(
            name="walk_forward_oos_sharpe",
            passed=mean_oos_sharpe >= -0.5,
            message=f"Mean out-of-sample Sharpe across folds is {mean_oos_sharpe:.2f}.",
        ),
        _quality_check(
            name="walk_forward_drawdown",
            passed=worst_oos_drawdown >= -0.40,
            message=f"Worst out-of-sample drawdown across folds is {worst_oos_drawdown:.2%}.",
        ),
    ]

    train_rows = validation.loc[validation["segment"] == "train", ["fold", "sharpe"]]
    paired = train_rows.merge(test_rows[["fold", "sharpe"]], on="fold", suffixes=("_train", "_test"))
    if not paired.empty:
        mean_gap = float((paired["sharpe_train"] - paired["sharpe_test"]).abs().mean())
        checks.append(
            _quality_check(
                name="train_test_sharpe_gap",
                passed=mean_gap <= 2.5,
                message=f"Mean absolute train/test Sharpe gap is {mean_gap:.2f}.",
            )
        )
    return checks


def _sensitivity_checks(sensitivity: pd.DataFrame) -> list[ReviewCheck]:
    if sensitivity.empty:
        return [
            ReviewCheck(
                name="parameter_sensitivity",
                status="FAIL",
                severity="error",
                message="Parameter sensitivity analysis produced no rows.",
            )
        ]

    sharpe_range = float(sensitivity["sharpe"].max() - sensitivity["sharpe"].min())
    worst_drawdown = float(sensitivity["max_drawdown"].min())
    return [
        _quality_check(
            name="parameter_sensitivity",
            passed=sharpe_range <= 4.0,
            message=f"Sharpe range across the sensitivity grid is {sharpe_range:.2f}.",
        ),
        _quality_check(
            name="sensitivity_drawdown",
            passed=worst_drawdown >= -0.50,
            message=f"Worst drawdown across the sensitivity grid is {worst_drawdown:.2%}.",
        ),
    ]


def _walk_forward_weight_checks(weights: pd.DataFrame) -> list[ReviewCheck]:
    if weights.empty:
        return [
            ReviewCheck(
                name="walk_forward_factor_weights",
                status="FAIL",
                severity="error",
                message="Walk-forward factor weighting produced no learned weights.",
            )
        ]
    max_abs_sum = weights.groupby("fold")["weight"].apply(lambda series: float(series.abs().sum())).max()
    if pd.isna(max_abs_sum) or max_abs_sum <= 0.0:
        return [
            ReviewCheck(
                name="walk_forward_factor_weights",
                status="FAIL",
                severity="error",
                message="Walk-forward factor weighting produced invalid learned weights.",
            )
        ]
    return [
        _check(
            name="walk_forward_factor_weights",
            passed=0.99 <= max_abs_sum <= 1.01,
            warn=0.95 <= max_abs_sum <= 1.05,
            message=f"Maximum absolute factor-weight sum by fold is {max_abs_sum:.2f}.",
        )
    ]


def _benchmark_checks(
    comparison: pd.DataFrame,
    metrics: dict[str, float | int],
) -> list[ReviewCheck]:
    if comparison.empty:
        return [
            ReviewCheck(
                name="benchmark_comparison",
                status="FAIL",
                severity="error",
                message="Benchmark comparison produced no rows.",
            )
        ]

    checks: list[ReviewCheck] = []
    equal_weight = comparison.loc[comparison["benchmark"] == "equal_weight_universe"]
    if not equal_weight.empty:
        excess = float(equal_weight["excess_total_return"].iloc[0])
        checks.append(
            _quality_check(
                name="equal_weight_excess_return",
                passed=excess >= -0.05,
                message=f"Strategy excess total return vs equal-weight benchmark is {excess:.2%}.",
            )
        )

    random_topk = comparison.loc[comparison["benchmark"] == "random_topk"]
    if not random_topk.empty:
        random_excess = float(random_topk["excess_total_return"].iloc[0])
        checks.append(
            _quality_check(
                name="random_baseline_excess_return",
                passed=random_excess >= 0.0,
                message=f"Strategy excess total return vs random top-k baseline is {random_excess:.2%}.",
            )
        )

    total_cost_drag = float(metrics.get("total_cost_drag", 0.0))
    best_excess = float(comparison["excess_total_return"].max())
    checks.append(
        _quality_check(
            name="excess_return_cost_context",
            passed=not (best_excess > 0.30 and total_cost_drag > 0.10),
            message=f"Best benchmark excess return is {best_excess:.2%}; total cost drag is {total_cost_drag:.2%}.",
        )
    )
    return checks


def _factor_diagnostic_checks(diagnostics: pd.DataFrame) -> list[ReviewCheck]:
    if diagnostics.empty:
        return [
            ReviewCheck(
                name="factor_diagnostics",
                status="FAIL",
                severity="error",
                message="Factor diagnostics produced no rows.",
            )
        ]

    required_columns = {
        "observations",
        "ic_positive_ratio",
        "top_bottom_spread",
        "quantile_monotonicity_score",
        "factor_missing_rate",
    }
    missing_columns = sorted(required_columns.difference(diagnostics.columns))
    if missing_columns:
        return [
            ReviewCheck(
                name="factor_diagnostics",
                status="FAIL",
                severity="error",
                message=f"Factor diagnostics are missing required columns: {', '.join(missing_columns)}.",
            )
        ]

    min_observations = int(diagnostics["observations"].min())
    min_positive_ratio = float(diagnostics["ic_positive_ratio"].min())
    worst_spread = float(diagnostics["top_bottom_spread"].min())
    min_monotonicity = float(diagnostics["quantile_monotonicity_score"].min())
    max_missing = float(diagnostics["factor_missing_rate"].max())
    checks: list[ReviewCheck] = []
    observations_message = f"Minimum factor IC observation count is {min_observations}."
    if min_observations <= 0:
        checks.append(
            ReviewCheck(
                name="factor_ic_observations",
                status="FAIL",
                severity="error",
                message=observations_message,
            )
        )
    else:
        checks.append(_quality_check("factor_ic_observations", min_observations >= 40, observations_message))

    checks.extend(
        [
            _quality_check(
                name="factor_ic_positive_ratio",
                passed=min_positive_ratio >= 0.40,
                message=f"Lowest factor IC positive ratio is {min_positive_ratio:.2%}.",
            ),
            _quality_check(
                name="factor_top_bottom_spread",
                passed=worst_spread >= -0.02,
                message=f"Worst top-bottom quantile spread is {worst_spread:.2%}.",
            ),
            _quality_check(
                name="factor_quantile_monotonicity",
                passed=min_monotonicity >= -0.25,
                message=f"Lowest factor quantile monotonicity score is {min_monotonicity:.2f}.",
            ),
        ]
    )

    missing_message = f"Maximum factor missing rate is {max_missing:.2%}."
    if max_missing >= 1.0:
        checks.append(ReviewCheck(name="factor_missing_rate", status="FAIL", severity="error", message=missing_message))
    else:
        checks.append(_quality_check("factor_missing_rate", max_missing <= 0.35, missing_message))
    return checks


def _ml_oos_checks(config: ResearchConfig, ml_oos_evaluation: pd.DataFrame | None) -> list[ReviewCheck]:
    if not config.enable_supervised_model:
        return [
            ReviewCheck(
                name="supervised_model",
                status="PASS",
                severity="info",
                message="Supervised factor model is not enabled.",
            )
        ]
    if ml_oos_evaluation is None or ml_oos_evaluation.empty:
        return [
            ReviewCheck(
                name="ml_oos_evaluation",
                status="WARN",
                severity="warning",
                message="Supervised factor model is enabled but produced no OOS evaluation rows.",
            )
        ]

    failed_ratio = float((ml_oos_evaluation["status"] != "PASS").mean()) if "status" in ml_oos_evaluation else 1.0
    mean_ic = float(ml_oos_evaluation["prediction_ic"].mean()) if "prediction_ic" in ml_oos_evaluation else 0.0
    min_n_test = int(ml_oos_evaluation["n_test"].min()) if "n_test" in ml_oos_evaluation else 0
    mean_spread = float(ml_oos_evaluation["top_bottom_spread"].mean()) if "top_bottom_spread" in ml_oos_evaluation else 0.0
    checks = [
        _check(
            name="ml_fold_success",
            passed=failed_ratio <= 0.34,
            warn=failed_ratio < 1.0,
            message=f"ML OOS warning/failure fold ratio is {failed_ratio:.2%}.",
        ),
        _quality_check(
            name="ml_prediction_ic",
            passed=mean_ic > 0.0,
            message=f"Mean OOS prediction IC is {mean_ic:.4f}.",
        ),
        _quality_check(
            name="ml_prediction_sample",
            passed=min_n_test >= 30,
            message=f"Minimum ML OOS test sample size is {min_n_test}.",
        ),
        _quality_check(
            name="ml_top_bottom_spread",
            passed=mean_spread >= 0.0,
            message=f"Mean ML top-bottom spread is {mean_spread:.4%}.",
        ),
    ]
    return checks
