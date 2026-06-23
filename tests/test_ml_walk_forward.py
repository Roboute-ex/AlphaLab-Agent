from alphalab_agent.analysis.robustness import calculate_ml_walk_forward_evaluation
from alphalab_agent.config import ResearchConfig
from alphalab_agent.data.synthetic import generate_synthetic_ohlcv
from alphalab_agent.pipeline import run_v0_pipeline
from alphalab_agent.research.factors import FACTOR_COLUMNS
from alphalab_agent.research.labels import add_forward_returns
from alphalab_agent.research.panel import build_price_panel
from alphalab_agent.research.factors import calculate_factors, add_composite_score


def test_ml_walk_forward_outputs_oos_metrics():
    config = ResearchConfig(seed=31, n_days=140, n_symbols=12, top_k=4, enable_supervised_model=True)
    panel = build_price_panel(generate_synthetic_ohlcv(config))
    factors = add_composite_score(calculate_factors(panel), weights=config.factor_weights)
    labels = add_forward_returns(panel, periods=config.forward_days)
    frame = factors.merge(labels, on=["date", "symbol"], how="inner")
    frame = frame.merge(panel[["date", "symbol", "return_1d"]], on=["date", "symbol"], how="left")

    result = calculate_ml_walk_forward_evaluation(
        frame,
        label_col="forward_return_5d",
        config=config,
        factor_cols=FACTOR_COLUMNS,
    )

    assert not result.empty
    assert {"fold", "prediction_ic", "test_total_return", "n_train", "n_test", "status"}.issubset(result.columns)
    assert (result["n_train"] > 0).all()
    assert (result["n_test"] > 0).all()


def test_pipeline_runs_with_supervised_model_enabled():
    config = ResearchConfig(
        seed=32,
        n_days=140,
        n_symbols=12,
        top_k=4,
        enable_supervised_model=True,
        output_dir="artifacts",
    )

    artifacts = run_v0_pipeline(config, write_report=False)

    assert artifacts.supervised_model["enabled"] is True
    assert artifacts.supervised_model["model_type"] == "ridge"
    assert not artifacts.ml_oos_evaluation.empty
    assert "## Supervised Factor Model" in artifacts.report_markdown
    assert "## Out-of-sample ML Evaluation" in artifacts.report_markdown
