import pandas as pd

from alphalab_agent.analysis.factor_analysis import calculate_factor_ic, calculate_quantile_returns


def test_factor_ic_and_rank_ic_are_calculated():
    frame = pd.DataFrame(
        {
            "date": [pd.Timestamp("2020-01-01")] * 5 + [pd.Timestamp("2020-01-02")] * 5,
            "factor": [1, 2, 3, 4, 5, 5, 4, 3, 2, 1],
            "forward_return_1d": [1, 2, 3, 4, 5, 5, 4, 3, 2, 1],
        }
    )
    result = calculate_factor_ic(frame, label_col="forward_return_1d", factor_cols=["factor"])

    assert result.loc[0, "factor"] == "factor"
    assert result.loc[0, "observations"] == 2
    assert round(result.loc[0, "mean_ic"], 6) == 1.0
    assert round(result.loc[0, "mean_rank_ic"], 6) == 1.0


def test_quantile_returns_rank_by_score():
    frame = pd.DataFrame(
        {
            "date": [pd.Timestamp("2020-01-01")] * 6,
            "composite_score": [1, 2, 3, 4, 5, 6],
            "forward_return_1d": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06],
        }
    )
    result = calculate_quantile_returns(
        frame,
        label_col="forward_return_1d",
        score_col="composite_score",
        quantiles=3,
    )

    assert list(result["quantile"]) == [1, 2, 3]
    assert result.loc[result["quantile"] == 3, "mean_forward_return"].iloc[0] > result.loc[
        result["quantile"] == 1, "mean_forward_return"
    ].iloc[0]
