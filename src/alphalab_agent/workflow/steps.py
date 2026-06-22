"""Step logs for deterministic agent-style workflows."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StepLog:
    """One deterministic workflow step."""

    step: str
    status: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def write_step_logs(path: str | Path, steps: list[StepLog]) -> Path:
    """Write workflow step logs as JSON."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [step.to_dict() for step in steps]
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path
