import pandas as pd

from alphalab_agent.backtest.portfolio import run_topk_long_only_backtest


def test_topk_backtest_selects_top_scores_and_applies_costs():
    frame = pd.DataFrame(
        {
            "date": [pd.Timestamp("2020-01-01")] * 3 + [pd.Timestamp("2020-01-02")] * 3,
            "symbol": ["A", "B", "C", "A", "B", "C"],
            "composite_score": [0.1, 0.9, 0.2, 0.8, 0.1, 0.7],
            "forward_return_1d": [0.01, 0.03, 0.02, -0.01, 0.02, 0.04],
        }
    )
    result = run_topk_long_only_backtest(
        frame,
        label_col="forward_return_1d",
        top_k=2,
        rebalance_every=1,
        transaction_cost_bps=10,
    )

    first_positions = result.positions[result.positions["date"] == pd.Timestamp("2020-01-01")]
    assert set(first_positions["symbol"]) == {"B", "C"}
    assert round(result.portfolio_returns.loc[0, "gross_return"], 6) == 0.025
    assert round(result.portfolio_returns.loc[0, "transaction_cost"], 6) == 0.001
    assert round(result.portfolio_returns.loc[0, "net_return"], 6) == 0.024
    assert "equity_without_cost" in result.portfolio_returns.columns
    assert "equity_with_cost" in result.portfolio_returns.columns
    assert result.portfolio_returns.loc[0, "equity_without_cost"] > result.portfolio_returns.loc[0, "equity_with_cost"]
