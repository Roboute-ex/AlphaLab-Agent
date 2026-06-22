"""Deterministic ResearchPlan parser and PlannerAgent."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from alphalab_agent.config import ResearchConfig


@dataclass(frozen=True)
class ResearchPlan:
    """A structured plan for a deterministic synthetic research run."""

    goal: str
    data_source: str = "synthetic"
    universe_size: int = 50
    start_date: str = "2020-01-01"
    n_days: int = 504
    forward_days: int = 5
    rebalance_every: int = 5
    top_k: int = 5
    transaction_cost_bps: float = 5.0
    factor_set: tuple[str, ...] = field(
        default_factory=lambda: (
            "momentum_20",
            "reversal_5",
            "low_volatility_20",
            "volume_trend_20",
        )
    )

    def to_config(self, base_config: ResearchConfig | None = None) -> ResearchConfig:
        """Convert the plan to a ResearchConfig."""

        base = base_config or ResearchConfig()
        return ResearchConfig(
            seed=base.seed,
            start_date=self.start_date,
            n_days=self.n_days,
            n_symbols=self.universe_size,
            forward_days=self.forward_days,
            rebalance_every=self.rebalance_every,
            top_k=self.top_k,
            transaction_cost_bps=self.transaction_cost_bps,
            annualization=base.annualization,
            output_dir=base.output_dir,
            report_name=base.report_name,
            html_report_name=base.html_report_name,
            quantiles=base.quantiles,
            generate_html=base.generate_html,
            generate_charts=base.generate_charts,
            factor_weights=base.factor_weights,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly plan dictionary."""

        data = asdict(self)
        data["factor_set"] = list(self.factor_set)
        return data


class PlannerAgent:
    """Rule-based planner that parses a user goal without using an LLM."""

    def parse(self, goal: str, base_config: ResearchConfig | None = None) -> ResearchPlan:
        """Parse a lightweight natural-language goal into a ResearchPlan."""

        base = base_config or ResearchConfig()
        top_k = _extract_int(goal, patterns=[r"top[- ]?(\d+)", r"前\s*(\d+)"], default=base.top_k)
        forward_days = _extract_int(
            goal,
            patterns=[r"(\d+)\s*day", r"(\d+)\s*d", r"(\d+)\s*日"],
            default=base.forward_days,
        )
        cost_bps = _extract_float(goal, patterns=[r"(\d+(?:\.\d+)?)\s*bps"], default=base.transaction_cost_bps)
        universe_size = _extract_int(
            goal,
            patterns=[r"(\d+)\s*symbols?", r"(\d+)\s*stocks?", r"(\d+)\s*只"],
            default=base.n_symbols,
        )

        top_k = max(1, min(top_k, universe_size))
        return ResearchPlan(
            goal=goal.strip() or "Run the default deterministic synthetic multi-factor research workflow.",
            data_source="synthetic",
            universe_size=universe_size,
            start_date=base.start_date,
            n_days=base.n_days,
            forward_days=forward_days,
            rebalance_every=base.rebalance_every,
            top_k=top_k,
            transaction_cost_bps=cost_bps,
        )


def write_plan(path: str | Path, plan: ResearchPlan) -> Path:
    """Write a ResearchPlan JSON artifact."""

    import json

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
    return output_path


def _extract_int(goal: str, patterns: list[str], default: int) -> int:
    for pattern in patterns:
        match = re.search(pattern, goal, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return default


def _extract_float(goal: str, patterns: list[str], default: float) -> float:
    for pattern in patterns:
        match = re.search(pattern, goal, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return default
