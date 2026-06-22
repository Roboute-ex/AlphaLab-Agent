from alphalab_agent.config import ResearchConfig
from alphalab_agent.data.synthetic import generate_synthetic_ohlcv
from alphalab_agent.research.factors import FACTOR_COLUMNS, add_composite_score, calculate_factors
from alphalab_agent.research.panel import build_price_panel


def test_factor_columns_and_composite_score_are_created():
    config = ResearchConfig(seed=3, n_days=90, n_symbols=8, top_k=4)
    panel = build_price_panel(generate_synthetic_ohlcv(config))
    factors = calculate_factors(panel)
    scored = add_composite_score(factors, config.factor_weights)

    assert set(FACTOR_COLUMNS).issubset(scored.columns)
    assert "composite_score" in scored.columns
    assert scored["composite_score"].notna().sum() > 0


def test_factors_do_not_use_future_returns_or_label_columns():
    config = ResearchConfig(seed=23, n_days=90, n_symbols=4, top_k=2)
    panel = build_price_panel(generate_synthetic_ohlcv(config))
    baseline = calculate_factors(panel)

    mutated = panel.copy()
    cutoff = mutated["date"].drop_duplicates().sort_values().iloc[40]
    mutated.loc[mutated["date"] > cutoff, "close"] *= 10.0
    mutated["forward_return_5d"] = 999.0
    changed = calculate_factors(mutated)

    factor_cols = ["date", "symbol", *FACTOR_COLUMNS]
    before_cutoff = baseline["date"] <= cutoff
    assert baseline.loc[before_cutoff, factor_cols].equals(changed.loc[before_cutoff, factor_cols])
