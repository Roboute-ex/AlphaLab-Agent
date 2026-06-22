from alphalab_agent.config import ResearchConfig
from alphalab_agent.data.synthetic import generate_synthetic_ohlcv


def test_synthetic_data_is_reproducible_with_fixed_seed():
    config = ResearchConfig(seed=7, n_days=80, n_symbols=6, top_k=3)
    first = generate_synthetic_ohlcv(config)
    second = generate_synthetic_ohlcv(config)
    assert first.equals(second)


def test_synthetic_ohlcv_constraints_hold():
    config = ResearchConfig(seed=11, n_days=80, n_symbols=6, top_k=3)
    df = generate_synthetic_ohlcv(config)
    assert set(["date", "symbol", "open", "high", "low", "close", "volume"]).issubset(df.columns)
    assert (df[["open", "high", "low", "close"]] > 0).all().all()
    assert (df["volume"] > 0).all()
    assert (df["high"] >= df[["open", "close"]].max(axis=1)).all()
    assert (df["low"] <= df[["open", "close"]].min(axis=1)).all()
