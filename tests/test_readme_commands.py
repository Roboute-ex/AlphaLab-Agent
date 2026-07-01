import os
import shutil
import subprocess
import sys
from pathlib import Path

from alphalab_agent.config import ResearchConfig, write_config


def test_readme_core_cli_commands_run_with_small_configs():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    output_root = root / "artifacts" / "test_readme_commands"
    shutil.rmtree(output_root, ignore_errors=True)
    output_root.mkdir(parents=True, exist_ok=True)
    config_path = output_root / "config.json"
    write_config(config_path, ResearchConfig(seed=121, n_days=120, n_symbols=10, top_k=3))

    commands = [
        [
            sys.executable,
            "-m",
            "alphalab_agent.cli",
            "--demo",
            "--config",
            str(config_path),
            "--output-dir",
            str(output_root / "default"),
        ],
        [
            sys.executable,
            "-m",
            "alphalab_agent.cli",
            "--demo",
            "--data-source",
            "csv",
            "--csv-path",
            str(root / "examples" / "sample_ohlcv.csv"),
            "--output-dir",
            str(output_root / "csv"),
        ],
        [
            sys.executable,
            "-m",
            "alphalab_agent.cli",
            "--demo",
            "--config",
            str(config_path),
            "--enable-supervised-model",
            "--output-dir",
            str(output_root / "ml"),
        ],
    ]

    try:
        for command in commands:
            result = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, check=False)
            assert result.returncode == 0, result.stdout + result.stderr
            assert "AlphaLab Agent v0.9 demo complete" in result.stdout
    finally:
        shutil.rmtree(output_root, ignore_errors=True)


def test_readme_streamlit_fallback_command_runs_without_streamlit():
    root = Path(__file__).resolve().parents[1]
    fake_dir = root / "artifacts" / "test_streamlit_missing"
    shutil.rmtree(fake_dir, ignore_errors=True)
    fake_dir.mkdir(parents=True, exist_ok=True)
    (fake_dir / "streamlit.py").write_text('raise ImportError("forced missing streamlit")\n', encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(fake_dir), str(root / "src")])

    try:
        result = subprocess.run(
            [sys.executable, "-m", "alphalab_agent.app.streamlit_app"],
            cwd=root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        shutil.rmtree(fake_dir, ignore_errors=True)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Streamlit is optional" in result.stdout
