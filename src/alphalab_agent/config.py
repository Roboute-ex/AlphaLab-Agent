"""Configuration objects for deterministic research runs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResearchConfig:
    """Parameters for the synthetic multi-factor research workflow."""

    seed: int = 42
    data_source: str = "synthetic"
    start_date: str = "2020-01-01"
    n_days: int = 504
    n_symbols: int = 50
    forward_days: int = 5
    rebalance_every: int = 5
    top_k: int = 5
    transaction_cost_bps: float = 5.0
    annualization: int = 252
    backtest_mode: str = "execution"
    weighting_mode: str = "equal_weight"
    benchmark_seed: int = 42
    enable_supervised_model: bool = False
    model_type: str = "ridge"
    model_label_col: str = "forward_return"
    model_factor_cols: list[str] | None = None
    output_dir: Path = Path("artifacts")
    report_name: str = "report.md"
    html_report_name: str = "report.html"
    quantiles: int = 5
    generate_html: bool = True
    generate_charts: bool = True
    validation_splits: int = 3
    validation_train_fraction: float = 0.5
    validation_embargo_periods: int | None = None
    sensitivity_top_k_step: int = 2
    generate_manifest: bool = True
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
        if self.data_source not in {"synthetic", "csv", "yfinance"}:
            raise ValueError("data_source must be one of: synthetic, csv, yfinance.")
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
        if self.backtest_mode not in {"execution", "label_based"}:
            raise ValueError("backtest_mode must be one of: execution, label_based.")
        if self.weighting_mode not in {
            "equal_weight",
            "config_weight",
            "ic_weight_train_only",
            "rankic_weight_train_only",
        }:
            raise ValueError(
                "weighting_mode must be one of: equal_weight, config_weight, "
                "ic_weight_train_only, rankic_weight_train_only."
            )
        if self.model_type not in {"ridge", "linear"}:
            raise ValueError("model_type must be one of: ridge, linear.")
        if self.quantiles < 2:
            raise ValueError("quantiles must be at least 2.")
        if self.validation_splits < 0:
            raise ValueError("validation_splits cannot be negative.")
        if not 0.0 < self.validation_train_fraction < 1.0:
            raise ValueError("validation_train_fraction must be between 0 and 1.")
        if self.validation_embargo_periods is not None and self.validation_embargo_periods < 0:
            raise ValueError("validation_embargo_periods cannot be negative.")
        if self.sensitivity_top_k_step <= 0:
            raise ValueError("sensitivity_top_k_step must be positive.")
        if not self.factor_weights:
            raise ValueError("factor_weights cannot be empty.")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly config dictionary."""

        data = asdict(self)
        data["output_dir"] = str(self.output_dir)
        return data


def load_config(path: str | Path) -> ResearchConfig:
    """Load a ResearchConfig from a JSON file."""

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ResearchConfig(**data)


def write_config(path: str | Path, config: ResearchConfig | None = None) -> Path:
    """Write a JSON config file and return its path."""

    config = config or ResearchConfig()
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    return output_path
