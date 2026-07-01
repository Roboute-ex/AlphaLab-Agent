from pathlib import Path


def test_changelog_contains_v0_9_maintenance_entry():
    text = Path("CHANGELOG.md").read_text(encoding="utf-8")

    assert "## v0.9" in text
    assert "maintenance" in text.lower()
    assert "Version consistency tests" in text
    assert "Safety Boundary" in text


def test_maintenance_docs_and_release_checklist_cover_required_topics():
    maintenance = Path("docs/MAINTENANCE.md").read_text(encoding="utf-8")
    log = Path("docs/MAINTENANCE_LOG.md").read_text(encoding="utf-8")
    checklist = Path("docs/RELEASE_CHECKLIST.md").read_text(encoding="utf-8")

    assert "artifacts/report.md" in maintenance
    assert "API key" in maintenance
    assert "Node.js deprecation warning" in maintenance
    assert "v0.9 maintenance update" in log
    assert "git status" in checklist
    assert "tag" in checklist.lower()
    assert "push" in checklist.lower()
    assert "GitHub Actions" in checklist
    assert "CI 失败" in checklist


def test_issue_and_pr_templates_exist_and_preserve_safety_boundary():
    bug = Path(".github/ISSUE_TEMPLATE/bug_report.md").read_text(encoding="utf-8")
    feature = Path(".github/ISSUE_TEMPLATE/feature_request.md").read_text(encoding="utf-8")
    pr = Path(".github/pull_request_template.md").read_text(encoding="utf-8")

    assert "Python 版本" in bug
    assert "synthetic / csv / yfinance" in bug or "synthetic" in bug
    assert "API key" in bug
    assert "是否需要新增依赖" in feature
    assert "是否影响安全边界" in feature
    assert "pytest" in pr
    assert "fallback runner" in pr
    assert "No real API key" in pr
    assert "No live trading" in pr
