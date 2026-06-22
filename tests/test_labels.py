import pandas as pd

from alphalab_agent.research.labels import add_forward_returns


def test_forward_return_label_alignment():
    panel = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=4),
            "symbol": ["AAA"] * 4,
            "close": [100.0, 110.0, 121.0, 133.1],
        }
    )
    labels = add_forward_returns(panel, periods=2)
    assert round(labels.loc[0, "forward_return_2d"], 6) == 0.21
    assert round(labels.loc[1, "forward_return_2d"], 6) == 0.21
    assert labels.loc[2, "forward_return_2d"] != labels.loc[2, "forward_return_2d"]
