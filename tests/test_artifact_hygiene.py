from pathlib import Path


def test_gitignore_keeps_generated_artifacts_out_of_commits():
    text = Path(".gitignore").read_text(encoding="utf-8")

    for pattern in [
        "artifacts/*.md",
        "artifacts/*.html",
        "artifacts/*.png",
        "artifacts/*.json",
        "artifacts/run_manifest.json",
        "!artifacts/.gitkeep",
    ]:
        assert pattern in text


def test_artifacts_gitkeep_exists():
    assert Path("artifacts/.gitkeep").exists()


def test_docs_explain_generated_artifacts_should_not_be_committed():
    readme = Path("README.md").read_text(encoding="utf-8")
    runbook = Path("docs/RUNBOOK.md").read_text(encoding="utf-8")
    combined = f"{readme}\n{runbook}".lower()

    assert "generated artifacts" in combined
    assert "should not be committed" in combined


def test_dependabot_config_is_conservative_if_present():
    path = Path(".github/dependabot.yml")
    assert path.exists()
    text = path.read_text(encoding="utf-8")

    assert 'package-ecosystem: "pip"' in text
    assert "directory: \"/\"" in text
    assert "interval: \"monthly\"" in text
    assert "open-pull-requests-limit: 2" in text
    assert "automerge" not in text.lower()
