from datetime import datetime
from pathlib import Path

from alphalab_agent.config import ResearchConfig
from alphalab_agent.pipeline import run_v0_pipeline
from alphalab_agent.report.manifest import build_run_manifest


REQUIRED_MANIFEST_KEYS = {
    "project_name",
    "project_version",
    "created_at_utc",
    "data_source",
    "seed",
    "config",
    "artifacts",
    "metrics_summary",
    "benchmark_summary",
    "reviewer_status",
    "reviewer_checks",
    "data_quality_status",
    "data_quality_summary",
    "supervised_model",
    "ml_oos_evaluation",
}


def test_manifest_schema_contains_required_stable_keys_when_ml_disabled():
    config = ResearchConfig(seed=131, n_days=120, n_symbols=10, top_k=3)
    artifacts = run_v0_pipeline(config, write_report=False)
    manifest = build_run_manifest(
        config=config,
        metrics=artifacts.metrics,
        checks=artifacts.review_checks,
        report_path=Path("artifacts/report.md"),
        html_report_path=Path("artifacts/report.html"),
        chart_paths={},
        benchmark_summary=artifacts.benchmark_comparison.comparison_summary,
        data_quality=artifacts.data_quality,
        supervised_model=artifacts.supervised_model,
        ml_oos_evaluation=artifacts.ml_oos_evaluation,
    )

    assert REQUIRED_MANIFEST_KEYS.issubset(manifest)
    assert manifest["project_version"] == "0.10"
    datetime.fromisoformat(manifest["created_at_utc"])
    assert manifest["supervised_model"] == {"enabled": False}
    assert manifest["ml_oos_evaluation"] == []


def test_manifest_schema_contains_supervised_model_details_when_enabled():
    config = ResearchConfig(seed=132, n_days=120, n_symbols=10, top_k=3, enable_supervised_model=True)
    artifacts = run_v0_pipeline(config, write_report=False)
    manifest = build_run_manifest(
        config=config,
        metrics=artifacts.metrics,
        checks=artifacts.review_checks,
        report_path=Path("artifacts/report.md"),
        html_report_path=Path("artifacts/report.html"),
        chart_paths={},
        benchmark_summary=artifacts.benchmark_comparison.comparison_summary,
        data_quality=artifacts.data_quality,
        supervised_model=artifacts.supervised_model,
        ml_oos_evaluation=artifacts.ml_oos_evaluation,
    )

    assert manifest["supervised_model"]["enabled"] is True
    assert manifest["supervised_model"]["model_type"] == "ridge"
    assert "metrics" in manifest["supervised_model"]
    assert isinstance(manifest["ml_oos_evaluation"], list)
