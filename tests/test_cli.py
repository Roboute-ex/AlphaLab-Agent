import os
import shutil
import subprocess
import sys
from pathlib import Path

from alphalab_agent.config import ResearchConfig, write_config
from alphalab_agent.data import generate_synthetic_ohlcv


def test_cli_demo_generates_report():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    output_dir = root / "artifacts" / "test_cli"
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    config_path = output_dir / "config.json"
    write_config(config_path, ResearchConfig(seed=101, n_days=140, n_symbols=12, top_k=4))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alphalab_agent.cli",
            "--demo",
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = output_dir / "report.md"
    assert report.exists()
    assert "AlphaLab Agent v0.10 demo complete" in result.stdout
    assert "Reviewer status:" in result.stdout
    assert "HTML report:" in result.stdout
    assert "Run manifest:" in result.stdout
    assert (output_dir / "run_manifest.json").exists()
    shutil.rmtree(output_dir, ignore_errors=True)


def test_cli_agent_demo_generates_plan_and_step_logs():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    output_dir = root / "artifacts" / "test_cli_agent"
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    config_path = output_dir / "config.json"
    write_config(config_path, ResearchConfig(seed=102, n_days=140, n_symbols=12, top_k=4))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alphalab_agent.cli",
            "--agent-demo",
            "--config",
            str(config_path),
            "--goal",
            "Run top-4 synthetic research with 5 day labels and 5 bps cost",
            "--output-dir",
            str(output_dir),
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (output_dir / "report.md").exists()
    assert (output_dir / "report.html").exists()
    assert (output_dir / "research_plan.json").exists()
    assert (output_dir / "step_logs.json").exists()
    assert "AlphaLab Agent v0.10 agent demo complete" in result.stdout
    assert "Step logs:" in result.stdout
    assert (output_dir / "run_manifest.json").exists()
    shutil.rmtree(output_dir, ignore_errors=True)


def test_cli_csv_data_source_generates_report():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    output_dir = root / "artifacts" / "test_cli_csv"
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "input.csv"
    generate_synthetic_ohlcv(ResearchConfig(seed=7, n_days=90, n_symbols=8)).to_csv(csv_path, index=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alphalab_agent.cli",
            "--demo",
            "--data-source",
            "csv",
            "--csv-path",
            str(csv_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = output_dir / "report.md"
    assert report.exists()
    assert "AlphaLab Agent v0.10 demo complete" in result.stdout
    report_text = report.read_text(encoding="utf-8")
    assert "using explicit local CSV market data" in report_text
    assert "| Data source | `csv` |" in report_text
    shutil.rmtree(output_dir, ignore_errors=True)


def test_cli_supervised_model_demo_generates_report():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    output_dir = root / "artifacts" / "test_cli_ml"
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    config_path = output_dir / "config.json"
    write_config(config_path, ResearchConfig(seed=103, n_days=140, n_symbols=12, top_k=4))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alphalab_agent.cli",
            "--demo",
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--enable-supervised-model",
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "AlphaLab Agent v0.10 demo complete" in result.stdout
    report_text = (output_dir / "report.md").read_text(encoding="utf-8")
    assert "## Supervised Factor Model" in report_text
    assert "## Out-of-sample ML Evaluation" in report_text
    shutil.rmtree(output_dir, ignore_errors=True)
