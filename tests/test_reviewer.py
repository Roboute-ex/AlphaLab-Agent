from alphalab_agent.config import ResearchConfig
from alphalab_agent.pipeline import run_v0_pipeline
from alphalab_agent.review.checks import run_reviewer_checks, summarize_review


def test_v0_pipeline_smoke_and_reviewer_are_deterministic():
    config = ResearchConfig(seed=13, n_days=180, n_symbols=12, top_k=4, output_dir="artifacts")
    first = run_v0_pipeline(config, write_report=False)
    second = run_v0_pipeline(config, write_report=False)

    assert first.metrics == second.metrics
    assert first.factor_ic.equals(second.factor_ic)
    assert first.quantile_returns.equals(second.quantile_returns)
    assert first.backtest.portfolio_returns.equals(second.backtest.portfolio_returns)
    assert first.report_path is None
    assert summarize_review(first.review_checks) in {"PASS", "WARN", "FAIL"}
    assert "not investment advice" in first.report_markdown
    for heading in [
        "## Research Hypothesis",
        "## Data Summary",
        "## Factor Summary",
        "## Backtest Config",
        "## Risk Metrics",
        "## Factor IC / RankIC Summary",
        "## Quantile Return Analysis",
        "## Walk-Forward Validation",
        "## Parameter Sensitivity",
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
        sensitivity_analysis=pd.DataFrame(
            [
                {"sharpe": -5.0, "max_drawdown": -0.90},
                {"sharpe": 5.0, "max_drawdown": -0.20},
            ]
        ),
    )
    statuses = {check.name: check.status for check in checks}
    assert statuses["backtest_periods"] == "FAIL"
    assert statuses["factor_score_coverage"] == "FAIL"
    assert statuses["drawdown_control"] == "FAIL"
    assert statuses["sharpe_sanity"] == "FAIL"
    assert statuses["turnover_sanity"] == "FAIL"
    assert statuses["cost_drag"] == "FAIL"
    assert statuses["walk_forward_coverage"] == "FAIL"
    assert statuses["walk_forward_oos_sharpe"] == "FAIL"
    assert statuses["walk_forward_drawdown"] == "FAIL"
    assert statuses["train_test_sharpe_gap"] == "FAIL"
    assert statuses["parameter_sensitivity"] == "FAIL"
    assert statuses["sensitivity_drawdown"] == "FAIL"
