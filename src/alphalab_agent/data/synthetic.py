"""Synthetic market data generation for v0."""

from __future__ import annotations

import numpy as np
import pandas as pd

from alphalab_agent.config import ResearchConfig


def generate_synthetic_ohlcv(config: ResearchConfig | None = None) -> pd.DataFrame:
    """Generate deterministic synthetic OHLCV data.

    The generator creates a market component, symbol-specific drift, and
    idiosyncratic noise. It is intentionally simple: the goal is a reproducible
    research fixture, not a realistic market simulator.
    """

    config = config or ResearchConfig()
    rng = np.random.default_rng(config.seed)
    dates = pd.bdate_range(config.start_date, periods=config.n_days)
    symbols = [f"STK{i:03d}" for i in range(config.n_symbols)]

    market_noise = rng.normal(loc=0.00015, scale=0.0075, size=config.n_days)
    slow_regime = np.sin(np.linspace(0, 6 * np.pi, config.n_days)) * 0.0015
    market_returns = market_noise + slow_regime

    records: list[pd.DataFrame] = []
    for symbol in symbols:
        beta = rng.uniform(0.65, 1.35)
        volatility = rng.uniform(0.009, 0.026)
        drift = rng.normal(0.00005, 0.00025)
        ar_coef = rng.uniform(-0.15, 0.20)
        idio = rng.normal(0.0, volatility, size=config.n_days)

        log_returns = np.empty(config.n_days)
        previous = 0.0
        for idx in range(config.n_days):
            current = drift + beta * market_returns[idx] + idio[idx] + ar_coef * previous
            log_returns[idx] = current
            previous = current

        initial_price = rng.uniform(20.0, 180.0)
        close = initial_price * np.exp(np.cumsum(log_returns))
        overnight_gap = rng.normal(0.0, 0.0025, size=config.n_days)
        open_ = np.r_[close[0], close[:-1]] * np.exp(overnight_gap)
        intraday_spread = np.abs(rng.normal(0.006, 0.004, size=config.n_days))
        high = np.maximum(open_, close) * (1.0 + intraday_spread)
        low = np.minimum(open_, close) * np.maximum(0.01, 1.0 - intraday_spread)

        base_volume = rng.integers(300_000, 4_000_000)
        volume_noise = rng.lognormal(mean=0.0, sigma=0.35, size=config.n_days)
        volume = np.maximum(1, (base_volume * volume_noise).astype(int))

        records.append(
            pd.DataFrame(
                {
                    "date": dates,
                    "symbol": symbol,
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                }
            )
        )

    df = pd.concat(records, ignore_index=True)
    return df.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)
