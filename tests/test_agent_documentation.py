from pathlib import Path


def test_readme_explains_agent_design_and_boundaries():
    text = Path("README.md").read_text(encoding="utf-8")

    assert "What is the Agent in AlphaLab Agent?" in text
    assert "deterministic" in text
    assert "PlannerAgent" in text
    assert "Reviewer" in text
    assert "not a financial chatbot" in text
    assert "not a live trading system" in text
    assert "Design Principles" in text
    assert "v0.10" in text


def test_agent_design_doc_contains_required_sections():
    text = Path("docs/AGENT_DESIGN.md").read_text(encoding="utf-8")

    assert "PlannerAgent" in text
    assert "Reviewer" in text
    assert "Anti-hallucination" in text
    assert "Reproducibility" in text
    assert "no live trading" in text
    assert "no LLM-generated" in text


def test_demo_walkthrough_doc_contains_required_sections():
    text = Path("docs/DEMO_WALKTHROUGH.md").read_text(encoding="utf-8")

    assert "Demo Walkthrough" in text
    assert "Minimal local run" in text
    assert "Extended run" in text
    assert "Common design questions" in text


def test_project_notes_doc_contains_required_sections():
    text = Path("docs/PROJECT_NOTES.md").read_text(encoding="utf-8")

    assert "Motivation" in text
    assert "Technical highlights" in text
    assert "Agent highlights" in text
    assert "Difference from a chatbot" in text
    assert "Future improvement ideas" in text
