import os
import shutil
import subprocess
import sys
from pathlib import Path


def test_cli_demo_generates_report():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    output_dir = root / "artifacts" / "test_cli"
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alphalab_agent.cli",
            "--demo",
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
    assert "AlphaLab Agent v0.1 demo complete" in result.stdout
    assert "Reviewer status:" in result.stdout
    shutil.rmtree(output_dir, ignore_errors=True)
