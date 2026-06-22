import pandas as pd

from alphalab_agent.research.panel import build_price_panel


def test_panel_sorts_deduplicates_and_adds_returns():
    raw = pd.DataFrame(
        {
            "date": ["2020-01-02", "2020-01-01", "2020-01-01"],
            "symbol": ["AAA", "AAA", "AAA"],
            "open": [11.0, 10.0, 10.0],
            "high": [12.0, 11.0, 11.0],
            "low": [10.5, 9.5, 9.5],
            "close": [12.0, 10.0, 10.0],
            "volume": [200, 100, 100],
        }
    )
    panel = build_price_panel(raw)
    assert len(panel) == 2
    assert not panel.duplicated(["date", "symbol"]).any()
    assert panel.loc[0, "date"] == pd.Timestamp("2020-01-01")
    assert round(panel.loc[1, "return_1d"], 6) == 0.2
    assert panel.loc[1, "dollar_volume"] == 2400.0
