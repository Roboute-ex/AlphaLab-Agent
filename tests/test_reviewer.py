from alphalab_agent.config import ResearchConfig
from alphalab_agent.pipeline import run_v0_pipeline
from alphalab_agent.review.checks import run_reviewer_checks, summarize_review


def test_v0_pipeline_smoke_and_reviewer_are_deterministic():
    config = ResearchConfig(seed=13, n_days=180, n_symbols=12, top_k=4, output_dir="artifacts")
    first = run_v0_pipeline(config, write_report=False)
    second = run_v0_pipeline(config, write_report=False)

    assert first.metrics == second.metrics
    assert first.factor_ic.equals(second.factor_ic)
    assert first.factor_diagnostics.equals(second.factor_diagnostics)
    assert first.quantile_returns.equals(second.quantile_returns)
    assert first.benchmark_comparison.comparison_summary.equals(second.benchmark_comparison.comparison_summary)
    assert first.backtest.portfolio_returns.equals(second.backtest.portfolio_returns)
    assert first.data_quality.status == second.data_quality.status
    assert first.supervised_model == {"enabled": False}
    assert first.ml_oos_evaluation.empty
    assert first.report_path is None
    assert summarize_review(first.review_checks) in {"PASS", "WARN"}
    assert "not investment advice" in first.report_markdown
    for heading in [
        "## Research Hypothesis",
        "## Data Summary",
        "## Data Quality",
        "## Factor Summary",
        "## Backtest Config",
        "## Backtest Assumptions",
        "## Risk Metrics",
        "## Factor IC / RankIC Summary",
        "## Factor Diagnostics",
        "## Quantile Return Analysis",
        "## Benchmark Comparison",
        "## Walk-Forward Validation",
        "## Walk-forward Factor Weights",
        "## Supervised Factor Model",
        "## Out-of-sample ML Evaluation",
        "## Parameter Sensitivity",
        "## Run Manifest",
        "## Reviewer Findings",
        "## Limitations",
        "## Disclaimer",
    ]:
        assert heading in first.report_markdown


def test_pipeline_writes_report_when_enabled():
    import shutil
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    output_dir = root / "artifacts" / "test_pipeline"
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    config = ResearchConfig(seed=17, n_days=180, n_symbols=12, top_k=4, output_dir=Path(output_dir))
    artifacts = run_v0_pipeline(config, write_report=True)
    assert artifacts.report_path is not None
    assert artifacts.report_path.exists()
    assert artifacts.report_path.name == "report.md"
    assert artifacts.html_report_path is not None
    assert artifacts.html_report_path.exists()
    assert artifacts.html_report_path.name == "report.html"
    assert artifacts.manifest_path is not None
    assert artifacts.manifest_path.exists()
    assert artifacts.manifest_path.name == "run_manifest.json"
    shutil.rmtree(output_dir, ignore_errors=True)


def test_reviewer_detects_abnormal_results():
    import pandas as pd

    config = ResearchConfig(seed=19, n_days=80, n_symbols=6, top_k=3)
    artifacts = run_v0_pipeline(config, write_report=False)
    bad_metrics = dict(artifacts.metrics)
    bad_metrics.update({"periods": 2, "max_drawdown": -0.95, "sharpe": -2.0, "average_turnover": 1.5})
    checks = run_reviewer_checks(
        artifacts.panel,
        artifacts.factors.assign(composite_score=float("nan")),
        artifacts.backtest.portfolio_returns.assign(transaction_cost=0.01),
        bad_metrics,
        config,
        walk_forward_validation=pd.DataFrame(
            [
                {"fold": 1, "segment": "train", "periods": 10, "sharpe": 3.0, "max_drawdown": -0.10},
                {"fold": 1, "segment": "test", "periods": 1, "sharpe": -3.0, "max_drawdown": -0.90},
            ]
        ),
        walk_forward_weights=pd.DataFrame(
            [
                {"fold": 1, "weighting_mode": "equal_weight", "factor": "momentum_20", "weight": 0.5},
                {"fold": 1, "weighting_mode": "equal_weight", "factor": "reversal_5", "weight": 0.5},
            ]
        ),
        sensitivity_analysis=pd.DataFrame(
            [
                {"sharpe": -5.0, "max_drawdown": -0.90},
                {"sharpe": 5.0, "max_drawdown": -0.20},
            ]
        ),
        benchmark_comparison=pd.DataFrame(
            [
                {
                    "benchmark": "equal_weight_universe",
                    "excess_total_return": -0.5,
                    "excess_sharpe": -1.0,
                },
                {
                    "benchmark": "random_topk",
                    "excess_total_return": -0.2,
                    "excess_sharpe": -0.5,
                },
            ]
        ),
        factor_diagnostics=pd.DataFrame(
            [
                {
                    "factor": "bad",
                    "observations": 1,
                    "ic_positive_ratio": 0.1,
                    "top_bottom_spread": -0.1,
                    "quantile_monotonicity_score": -1.0,
                    "factor_missing_rate": 0.8,
                }
            ]
        ),
    )
    statuses = {check.name: check.status for check in checks}
    assert statuses["supervised_model"] == "PASS"
    assert statuses["backtest_periods"] == "WARN"
    assert statuses["factor_score_coverage"] == "FAIL"
    assert statuses["drawdown_control"] == "WARN"
    assert statuses["sharpe_sanity"] == "WARN"
    assert statuses["turnover_sanity"] == "WARN"
    assert statuses["cost_drag"] == "WARN"
    assert statuses["walk_forward_coverage"] == "WARN"
    assert statuses["walk_forward_oos_sharpe"] == "WARN"
    assert statuses["walk_forward_drawdown"] == "WARN"
    assert statuses["train_test_sharpe_gap"] == "WARN"
    assert statuses["walk_forward_factor_weights"] == "PASS"
    assert statuses["parameter_sensitivity"] == "WARN"
    assert statuses["sensitivity_drawdown"] == "WARN"
    assert statuses["equal_weight_excess_return"] == "WARN"
    assert statuses["random_baseline_excess_return"] == "WARN"
    assert statuses["factor_ic_observations"] == "WARN"
    assert statuses["factor_ic_positive_ratio"] == "WARN"
    assert statuses["factor_top_bottom_spread"] == "WARN"
    assert statuses["factor_quantile_monotonicity"] == "WARN"
    assert statuses["factor_missing_rate"] == "WARN"
    assert summarize_review(checks) == "FAIL"


def test_reviewer_fails_when_data_quality_fails():
    import pandas as pd

    config = ResearchConfig(seed=23, n_days=120, n_symbols=6, top_k=3)
    artifacts = run_v0_pipeline(config, write_report=False)

    class BadQuality:
        status = "FAIL"
        summary = {"rows": 10, "issues": 2}

    checks = run_reviewer_checks(
        artifacts.panel,
        artifacts.factors,
        artifacts.backtest.portfolio_returns,
        artifacts.metrics,
        config,
        data_quality=BadQuality(),
        ml_oos_evaluation=pd.DataFrame(),
    )
    statuses = {check.name: check.status for check in checks}

    assert statuses["data_quality"] == "FAIL"
    assert statuses["supervised_model"] == "PASS"
    assert summarize_review(checks) == "FAIL"


def test_reviewer_summarizes_quality_risks_as_warn_without_structural_failures():
    import pandas as pd

    config = ResearchConfig(seed=23, n_days=120, n_symbols=6, top_k=3)
    panel = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=120, freq="B").repeat(6),
            "symbol": [f"S{i}" for _ in range(120) for i in range(6)],
        }
    )
    scored = panel.assign(composite_score=1.0)
    returns = pd.DataFrame({"transaction_cost": [0.01, 0.02]})
    metrics = {
        "periods": 2,
        "max_drawdown": -0.95,
        "sharpe": -3.0,
        "average_turnover": 1.5,
        "total_cost_drag": 0.25,
    }
    checks = run_reviewer_checks(
        panel,
        scored,
        returns,
        metrics,
        config,
        walk_forward_validation=pd.DataFrame(
            [
                {"fold": 1, "segment": "train", "periods": 10, "sharpe": 3.0, "max_drawdown": -0.10},
                {"fold": 1, "segment": "test", "periods": 1, "sharpe": -3.0, "max_drawdown": -0.90},
            ]
        ),
        walk_forward_weights=pd.DataFrame(
            [
                {"fold": 1, "weighting_mode": "equal_weight", "factor": "momentum_20", "weight": 0.5},
                {"fold": 1, "weighting_mode": "equal_weight", "factor": "reversal_5", "weight": 0.5},
            ]
        ),
        sensitivity_analysis=pd.DataFrame(
            [
                {"sharpe": -5.0, "max_drawdown": -0.90},
                {"sharpe": 5.0, "max_drawdown": -0.20},
            ]
        ),
        benchmark_comparison=pd.DataFrame(
            [
                {"benchmark": "equal_weight_universe", "excess_total_return": -0.5, "excess_sharpe": -1.0},
                {"benchmark": "random_topk", "excess_total_return": -0.2, "excess_sharpe": -0.5},
            ]
        ),
        factor_diagnostics=pd.DataFrame(
            [
                {
                    "factor": "weak",
                    "observations": 1,
                    "ic_positive_ratio": 0.1,
                    "top_bottom_spread": -0.1,
                    "quantile_monotonicity_score": -1.0,
                    "factor_missing_rate": 0.8,
                }
            ]
        ),
    )

    assert summarize_review(checks) == "WARN"
