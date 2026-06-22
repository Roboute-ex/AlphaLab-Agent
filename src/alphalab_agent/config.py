"""Configuration objects for deterministic research runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResearchConfig:
    """Parameters for the v0 synthetic multi-factor research workflow."""

    seed: int = 42
    start_date: str = "2020-01-01"
    n_days: int = 504
    n_symbols: int = 50
    forward_days: int = 5
    rebalance_every: int = 5
    top_k: int = 5
    transaction_cost_bps: float = 5.0
    annualization: int = 252
    output_dir: Path = Path("artifacts")
    report_name: str = "report.md"
    factor_weights: dict[str, float] = field(
        default_factory=lambda: {
            "momentum_20": 0.35,
            "reversal_5": 0.25,
            "low_volatility_20": 0.25,
            "volume_trend_20": 0.15,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "output_dir", Path(self.output_dir))
        if self.n_days <= 40:
            raise ValueError("n_days must be greater than 40 for rolling factors.")
        if self.n_symbols <= 1:
            raise ValueError("n_symbols must be greater than 1.")
        if self.forward_days <= 0:
            raise ValueError("forward_days must be positive.")
        if self.rebalance_every <= 0:
            raise ValueError("rebalance_every must be positive.")
        if self.top_k <= 0:
            raise ValueError("top_k must be positive.")
        if self.top_k > self.n_symbols:
            raise ValueError("top_k cannot exceed n_symbols.")
        if self.transaction_cost_bps < 0:
            raise ValueError("transaction_cost_bps cannot be negative.")
        if not self.factor_weights:
            raise ValueError("factor_weights cannot be empty.")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly config dictionary."""

        data = asdict(self)
        data["output_dir"] = str(self.output_dir)
        return data
