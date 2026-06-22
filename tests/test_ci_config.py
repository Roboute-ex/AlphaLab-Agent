from pathlib import Path


def test_github_actions_ci_runs_core_tests_without_optional_dependencies():
    ci_path = Path(".github") / "workflows" / "ci.yml"
    text = ci_path.read_text(encoding="utf-8")

    assert "pull_request" in text
    assert 'python -m pip install -e ".[dev]"' in text
    assert "python -m pytest -q" in text
    assert "python scripts/run_tests.py" in text
    assert "streamlit" not in text
    assert "yfinance" not in text
