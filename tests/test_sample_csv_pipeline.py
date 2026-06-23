import shutil
from pathlib import Path

from alphalab_agent.config import ResearchConfig
from alphalab_agent.data.adapters import load_csv_ohlcv
from alphalab_agent.pipeline import run_v0_pipeline
from alphalab_agent.review.checks import summarize_review


def test_sample_csv_can_run_full_pipeline_and_write_artifacts():
    root = Path(__file__).resolve().parents[1]
    csv_path = root / "examples" / "sample_ohlcv.csv"
    output_dir = root / "artifacts" / "test_sample_csv"
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = load_csv_ohlcv(csv_path)
    config = ResearchConfig(
        data_source="csv",
        n_days=int(raw["date"].nunique()),
        n_symbols=int(raw["symbol"].nunique()),
        top_k=3,
        output_dir=output_dir,
    )

    artifacts = run_v0_pipeline(config, write_report=True, raw_data=raw)

    assert artifacts.data_quality.status in {"PASS", "WARN"}
    assert summarize_review(artifacts.review_checks) in {"PASS", "WARN"}
    assert artifacts.report_path is not None and artifacts.report_path.exists()
    assert artifacts.html_report_path is not None and artifacts.html_report_path.exists()
    assert artifacts.manifest_path is not None and artifacts.manifest_path.exists()
    assert "## Data Quality" in artifacts.report_markdown
    shutil.rmtree(output_dir, ignore_errors=True)
