from pathlib import Path


def test_runbook_contains_required_sections():
    text = Path("docs/RUNBOOK.md").read_text(encoding="utf-8")

    for section in [
        "Purpose",
        "Local Environment Checklist",
        "Standard Validation Commands",
        "Expected Outputs",
        "Release Routine",
        "When Not To Release",
    ]:
        assert section in text

    assert "py -m pytest -q" in text
    assert "py scripts\\run_tests.py" in text
    assert "generated artifacts and should not be committed" in text


def test_troubleshooting_contains_required_topics():
    text = Path("docs/TROUBLESHOOTING.md").read_text(encoding="utf-8")

    for topic in [
        "pytest cannot import alphalab_agent",
        "Streamlit command fails",
        "yfinance unavailable",
        "Reviewer WARN is not a failure",
        "GitHub Actions failed but local passed",
        "Version mismatch",
        "Generated artifacts accidentally staged",
    ]:
        assert topic in text


def test_config_guide_contains_required_topics():
    text = Path("docs/CONFIG_GUIDE.md").read_text(encoding="utf-8")

    for topic in [
        "Configuration Philosophy",
        "Minimal Synthetic Config",
        "CSV Config",
        "Supervised Model Config",
        "Output Config",
        "Safety-Related Config",
    ]:
        assert topic in text

    assert "examples/config_synthetic_minimal.json" in text
    assert "examples/config_csv_sample.json" in text
    assert "examples/sample_ohlcv.csv" in text
