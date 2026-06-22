import pandas as pd

from alphalab_agent.analysis.factor_analysis import calculate_factor_diagnostics


def test_factor_diagnostics_outputs_stable_columns():
    frame = pd.DataFrame(
        {
            "date": [pd.Timestamp("2020-01-01")] * 6 + [pd.Timestamp("2020-01-02")] * 6,
            "factor": [1, 2, 3, 4, 5, 6, 6, 5, 4, 3, 2, 1],
            "constant": [1] * 12,
            "forward_return_1d": [1, 2, 3, 4, 5, 6, 6, 5, 4, 3, 2, 1],
        }
    )

    result = calculate_factor_diagnostics(
        frame,
        label_col="forward_return_1d",
        factor_cols=["factor", "constant"],
        quantiles=3,
    )

    assert set(result["factor"]) == {"factor", "constant"}
    for column in [
        "ic_positive_ratio",
        "ic_t_stat",
        "rankic_positive_ratio",
        "top_bottom_spread",
        "quantile_monotonicity_score",
        "factor_missing_rate",
    ]:
        assert column in result.columns
    constant = result[result["factor"] == "constant"].iloc[0]
    assert constant["observations"] == 0
    assert constant["icir"] == 0.0
