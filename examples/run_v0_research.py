"""Run the deterministic AlphaLab Agent v0.7 research workflow."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from alphalab_agent import ResearchConfig, run_v0_pipeline  # noqa: E402
from alphalab_agent.review.checks import summarize_review  # noqa: E402


def main() -> None:
    config = ResearchConfig(output_dir=ROOT / "artifacts", report_name="report.md")
    artifacts = run_v0_pipeline(config)
    metrics = artifacts.metrics
    print("AlphaLab Agent v0.7 complete")
    print(f"Reviewer status: {summarize_review(artifacts.review_checks)}")
    print(f"Periods: {metrics['periods']}")
    print(f"Total return: {metrics['total_return']:.2%}")
    print(f"Annualized return: {metrics['annualized_return']:.2%}")
    print(f"Sharpe: {metrics['sharpe']:.2f}")
    print(f"Max drawdown: {metrics['max_drawdown']:.2%}")
    print(f"Report: {artifacts.report_path}")


if __name__ == "__main__":
    main()
