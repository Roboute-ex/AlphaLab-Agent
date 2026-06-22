"""HTML report rendering without extra dependencies."""

from __future__ import annotations

import html
from pathlib import Path


def render_html_report(markdown_report: str, title: str = "AlphaLab Agent Report") -> str:
    """Render a simple self-contained HTML report from Markdown text."""

    escaped = html.escape(markdown_report)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; line-height: 1.5; margin: 2rem; color: #202124; }}
    main {{ max-width: 1100px; margin: 0 auto; }}
    pre {{ white-space: pre-wrap; background: #f7f7f7; padding: 1rem; border-radius: 6px; }}
  </style>
</head>
<body>
<main>
<pre>{escaped}</pre>
</main>
</body>
</html>
"""


def write_html_report(path: Path, html_report: str) -> Path:
    """Write an HTML report and return its path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_report, encoding="utf-8")
    return path
