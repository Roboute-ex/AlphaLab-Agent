import pandas as pd

from alphalab_agent.backtest.execution import run_signal_execution_backtest


def _execution_frame():
    dates = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-06"])
    return pd.DataFrame(
        {
            "date": [dates[0], dates[0], dates[1], dates[1], dates[2], dates[2], dates[3], dates[3]],
            "symbol": ["A", "B"] * 4,
            "composite_score": [1.0, 0.0, 0.0, 1.0, 0.2, 0.9, 0.0, 1.0],
            "return_1d": [0.0, 0.0, 0.01, 0.50, 0.02, -0.10, 0.03, 0.04],
            "forward_return_1d": [10.0, 99.0, 10.0, 99.0, 10.0, 99.0, 10.0, 99.0],
        }
    )


def test_execution_backtest_uses_realized_returns_not_forward_labels():
    result = run_signal_execution_backtest(
        _execution_frame(),
        top_k=1,
        rebalance_every=2,
        transaction_cost_bps=0,
    )

    assert round(result.portfolio_returns.loc[0, "gross_return"], 6) == 0.01
    assert result.portfolio_returns.loc[0, "gross_return"] != 10.0
    assert result.positions.loc[0, "symbol"] == "A"
    assert "forward_return" not in result.positions.columns


def test_execution_backtest_selection_depends_on_signal_date_score_only():
    result = run_signal_execution_backtest(
        _execution_frame(),
        top_k=1,
        rebalance_every=2,
        transaction_cost_bps=0,
    )

    first_signal = result.positions[result.positions["signal_date"] == pd.Timestamp("2020-01-01")]
    assert set(first_signal["symbol"]) == {"A"}


def test_execution_backtest_costs_reduce_equity():
    low_cost = run_signal_execution_backtest(_execution_frame(), top_k=1, rebalance_every=2, transaction_cost_bps=0)
    high_cost = run_signal_execution_backtest(_execution_frame(), top_k=1, rebalance_every=2, transaction_cost_bps=100)

    assert high_cost.portfolio_returns["net_return"].sum() <= low_cost.portfolio_returns["net_return"].sum()
    assert high_cost.portfolio_returns["equity_with_cost"].iloc[-1] <= low_cost.portfolio_returns[
        "equity_with_cost"
    ].iloc[-1]


def test_execution_backtest_validates_parameters_and_is_deterministic():
    frame = _execution_frame()
    first = run_signal_execution_backtest(frame, top_k=1, rebalance_every=2, transaction_cost_bps=5)
    second = run_signal_execution_backtest(frame, top_k=1, rebalance_every=2, transaction_cost_bps=5)
    assert first.portfolio_returns.equals(second.portfolio_returns)
    assert first.positions.equals(second.positions)

    for kwargs in [{"top_k": 0}, {"rebalance_every": 0}, {"transaction_cost_bps": -1}]:
        try:
            run_signal_execution_backtest(frame, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected ValueError for {kwargs}")
