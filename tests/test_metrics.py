import pandas as pd

from alphalab_agent.backtest.metrics import calculate_risk_metrics


def test_risk_metrics_for_simple_series():
    returns = pd.DataFrame(
        {
            "net_return": [0.10, -0.05],
            "gross_return": [0.11, -0.04],
            "turnover": [1.0, 0.5],
            "transaction_cost": [0.01, 0.01],
            "equity_without_cost": [1.11, 1.0656],
            "equity_with_cost": [1.10, 1.045],
        }
    )
    metrics = calculate_risk_metrics(returns, periods_per_year=2)
    assert metrics["periods"] == 2
    assert round(metrics["total_return"], 6) == 0.045
    assert round(metrics["max_drawdown"], 6) == -0.05
    assert "sharpe" in metrics
    assert metrics["win_rate"] == 0.5
    assert metrics["average_turnover"] == 0.75
    assert metrics["average_cost_drag"] == 0.01
    assert round(metrics["total_cost_drag"], 6) == 0.0206
