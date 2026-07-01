import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from alphalab_agent import __version__
from alphalab_agent.config import ResearchConfig, write_config


EXPECTED_VERSION = "0.9"


def test_version_consistency_across_project_files():
    root = Path(__file__).resolve().parents[1]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    package_version = (root / "src" / "alphalab_agent" / "_version.py").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    project_plan = (root / "docs" / "PROJECT_PLAN.md").read_text(encoding="utf-8")

    assert re.search(r'^version = "0\.9"$', pyproject, flags=re.MULTILINE)
    assert '__version__ = "0.9"' in package_version
    assert __version__ == EXPECTED_VERSION
    assert "v0.9" in readme
    assert "v0.9" in project_plan


def test_cli_version_and_demo_output_use_current_version():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    output_dir = root / "artifacts" / "test_version_consistency"
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    config_path = output_dir / "config.json"
    write_config(config_path, ResearchConfig(seed=111, n_days=120, n_symbols=10, top_k=3))

    version_result = subprocess.run(
        [sys.executable, "-m", "alphalab_agent.cli", "--version"],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    demo_result = subprocess.run(
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

    assert version_result.returncode == 0, version_result.stdout + version_result.stderr
    assert version_result.stdout.strip() == "AlphaLab Agent v0.9"
    assert demo_result.returncode == 0, demo_result.stdout + demo_result.stderr
    assert "AlphaLab Agent v0.9 demo complete" in demo_result.stdout
    shutil.rmtree(output_dir, ignore_errors=True)
