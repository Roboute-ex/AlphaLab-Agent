from pathlib import Path

from alphalab_agent.config import ResearchConfig, load_config, write_config


def test_config_json_roundtrip():
    output_path = Path("artifacts") / "test_config.json"
    try:
        config = ResearchConfig(seed=99, n_days=120, n_symbols=8, top_k=3)
        write_config(output_path, config)
        loaded = load_config(output_path)

        assert loaded.seed == 99
        assert loaded.n_days == 120
        assert loaded.n_symbols == 8
        assert loaded.top_k == 3
        assert loaded.output_dir == Path("artifacts")
    finally:
        output_path.unlink(missing_ok=True)


def test_config_validates_v0_6_robustness_settings():
    for kwargs in [
        {"validation_splits": -1},
        {"validation_train_fraction": 0.0},
        {"validation_train_fraction": 1.0},
        {"validation_embargo_periods": -1},
        {"sensitivity_top_k_step": 0},
    ]:
        try:
            ResearchConfig(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected ValueError for {kwargs}")
