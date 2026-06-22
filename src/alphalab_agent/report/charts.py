"""Optional chart generation with graceful fallback."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_equity_chart(output_dir: Path, portfolio_returns: pd.DataFrame) -> Path | None:
    """Write an equity curve chart if matplotlib is installed."""

    if portfolio_returns.empty:
        return None
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    chart_path = output_dir / "equity_curve.png"

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(portfolio_returns["date"], portfolio_returns["equity_without_cost"], label="without cost")
    ax.plot(portfolio_returns["date"], portfolio_returns["equity_with_cost"], label="with cost")
    ax.set_title("AlphaLab Agent Equity Curve")
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(chart_path, dpi=140)
    plt.close(fig)
    return chart_path
