from alphalab_agent.analysis.robustness import (
    calculate_parameter_sensitivity,
    calculate_walk_forward_validation,
)
from alphalab_agent.config import ResearchConfig
from alphalab_agent.pipeline import run_v0_pipeline


def test_walk_forward_validation_outputs_train_test_folds_and_is_deterministic():
    config = ResearchConfig(seed=31, n_days=180, n_symbols=12, top_k=4, validation_splits=2)
    artifacts = run_v0_pipeline(config, write_report=False)
    label_col = f"forward_return_{config.forward_days}d"

    first = calculate_walk_forward_validation(artifacts.research_frame, label_col, config)
    second = calculate_walk_forward_validation(artifacts.research_frame, label_col, config)

    assert first.equals(second)
    assert set(first["segment"]) == {"train", "test"}
    assert set(first["fold"]) == {1, 2}
    assert (first["periods"] >= 0).all()
    assert {"sharpe", "max_drawdown", "average_turnover"}.issubset(first.columns)


def test_parameter_sensitivity_outputs_deterministic_grid():
    config = ResearchConfig(seed=37, n_days=180, n_symbols=12, top_k=4)
    artifacts = run_v0_pipeline(config, write_report=False)
    label_col = f"forward_return_{config.forward_days}d"

    first = calculate_parameter_sensitivity(artifacts.research_frame, label_col, config)
    second = calculate_parameter_sensitivity(artifacts.research_frame, label_col, config)

    assert first.equals(second)
    assert sorted(first["top_k"].unique().tolist()) == [2, 4, 6]
    assert sorted(first["transaction_cost_bps"].unique().tolist()) == [0.0, 5.0, 10.0]
    assert len(first) == 9
    assert {"sharpe", "max_drawdown", "average_cost_drag"}.issubset(first.columns)
