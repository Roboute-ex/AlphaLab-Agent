import json
import subprocess
from pathlib import Path

from alphalab_agent.config import ResearchConfig
from alphalab_agent.pipeline import run_v0_pipeline
from alphalab_agent.report.manifest import build_run_manifest, write_run_manifest


def test_run_manifest_fields_and_gitignore_rule():
    config = ResearchConfig(seed=43, n_days=140, n_symbols=10, top_k=3, output_dir=Path("artifacts"))
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
    output = Path("artifacts") / "test_run_manifest.json"
    try:
        write_run_manifest(output, manifest)
        loaded = json.loads(output.read_text(encoding="utf-8"))
        assert loaded["project_name"] == "AlphaLab Agent"
        assert loaded["project_version"] == "0.9"
        assert loaded["data_source"] == "synthetic"
        assert loaded["data_quality_status"] in {"PASS", "WARN", "FAIL"}
        assert loaded["supervised_model"] == {"enabled": False}
        assert "ml_oos_evaluation" in loaded
        assert "created_at_utc" in loaded
        assert "git_commit" in loaded
        assert loaded["artifacts"]["markdown_report"] == "artifacts/report.md"

        result = subprocess.run(
            ["git", "check-ignore", "artifacts/run_manifest.json"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0
    finally:
        output.unlink(missing_ok=True)
