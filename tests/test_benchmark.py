from alphalab_agent.backtest.benchmark import calculate_benchmark_comparison
from alphalab_agent.config import ResearchConfig
from alphalab_agent.pipeline import run_v0_pipeline


def test_benchmark_comparison_outputs_required_baselines_and_is_deterministic():
    config = ResearchConfig(seed=41, n_days=140, n_symbols=10, top_k=3, benchmark_seed=123)
    artifacts = run_v0_pipeline(config, write_report=False)

    first = calculate_benchmark_comparison(artifacts.research_frame, artifacts.backtest.portfolio_returns, config)
    second = calculate_benchmark_comparison(artifacts.research_frame, artifacts.backtest.portfolio_returns, config)

    assert set(first.benchmark_returns) == {"equal_weight_universe", "random_topk", "momentum_20_only"}
    assert set(first.comparison_summary["benchmark"]) == set(first.benchmark_returns)
    assert first.comparison_summary.equals(second.comparison_summary)
    for column in [
        "strategy_total_return",
        "benchmark_total_return",
        "excess_total_return",
        "hit_rate_vs_benchmark",
    ]:
        assert column in first.comparison_summary.columns
