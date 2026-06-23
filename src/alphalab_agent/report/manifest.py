"""Run manifest generation for reproducible research artifacts."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from alphalab_agent._version import __version__
from alphalab_agent.config import ResearchConfig
from alphalab_agent.review.checks import ReviewCheck, summarize_review


def build_run_manifest(
    config: ResearchConfig,
    metrics: dict[str, float | int],
    checks: list[ReviewCheck],
    report_path: Path | None,
    html_report_path: Path | None,
    chart_paths: dict[str, Path],
    benchmark_summary: pd.DataFrame,
    data_quality: object | None = None,
    supervised_model: dict[str, Any] | None = None,
    ml_oos_evaluation: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable run manifest without secrets or local absolute paths."""

    data_quality_dict = data_quality.to_dict() if hasattr(data_quality, "to_dict") else {}
    return {
        "project_name": "AlphaLab Agent",
        "project_version": __version__,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "data_source": config.data_source,
        "seed": config.seed,
        "config": _safe_config(config),
        "artifacts": {
            "markdown_report": _safe_artifact_path(report_path),
            "html_report": _safe_artifact_path(html_report_path),
            "charts": {name: _safe_artifact_path(path) for name, path in chart_paths.items()},
        },
        "metrics_summary": _json_safe(metrics),
        "benchmark_summary": benchmark_summary.to_dict(orient="records") if not benchmark_summary.empty else [],
        "data_quality_summary": data_quality_dict.get("summary", {}),
        "data_quality_status": data_quality_dict.get("status", "UNKNOWN"),
        "data_quality_issues": data_quality_dict.get("issues", []),
        "supervised_model": _json_safe_any(supervised_model or {"enabled": False}),
        "ml_oos_evaluation": (
            _json_safe_any(ml_oos_evaluation.to_dict(orient="records"))
            if ml_oos_evaluation is not None and not ml_oos_evaluation.empty
            else []
        ),
        "reviewer_status": summarize_review(checks),
        "reviewer_checks": [check.__dict__ for check in checks],
    }


def write_run_manifest(path: Path, manifest: dict[str, Any]) -> Path:
    """Write a run manifest and return the path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _safe_artifact_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.name


def _safe_config(config: ResearchConfig) -> dict[str, Any]:
    data = config.to_dict()
    data["output_dir"] = _safe_artifact_path(Path(config.output_dir))
    return data


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            capture_output=True,
            check=False,
            timeout=5,
        )
    except Exception:
        return "unknown"
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip() or "unknown"


def _json_safe(values: dict[str, float | int]) -> dict[str, float | int]:
    return {key: float(value) if isinstance(value, float) else value for key, value in values.items()}


def _json_safe_any(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe_any(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe_any(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe_any(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value
