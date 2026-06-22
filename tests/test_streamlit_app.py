from pathlib import Path

from alphalab_agent.app import build_demo_config


def test_streamlit_app_config_builder_is_importable_without_streamlit():
    config = build_demo_config(
        seed=123,
        n_days=150,
        n_symbols=20,
        top_k=4,
        forward_days=7,
        rebalance_every=7,
        transaction_cost_bps=3.0,
        output_dir="artifacts",
    )

    assert config.seed == 123
    assert config.n_days == 150
    assert config.n_symbols == 20
    assert config.top_k == 4
    assert config.forward_days == 7
    assert config.rebalance_every == 7
    assert config.transaction_cost_bps == 3.0
    assert config.output_dir == Path("artifacts")
