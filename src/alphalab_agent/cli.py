"""Command line interface for AlphaLab Agent v0.1."""

from __future__ import annotations

import argparse
from pathlib import Path

from alphalab_agent.config import ResearchConfig
from alphalab_agent.pipeline import run_v0_pipeline
from alphalab_agent.review.checks import summarize_review


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AlphaLab Agent deterministic v0.1 workflow.")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the synthetic-data v0.1 demo and write artifacts/report.md.",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts",
        help="Directory for generated artifacts. Defaults to artifacts/.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.demo:
        parser.print_help()
        return 2

    config = ResearchConfig(output_dir=Path(args.output_dir), report_name="report.md")
    artifacts = run_v0_pipeline(config, write_report=True)
    metrics = artifacts.metrics

    print("AlphaLab Agent v0.1 demo complete")
    print("Steps: synthetic data -> panel -> factors -> labels -> backtest -> metrics -> reviewer -> report")
    print(f"Reviewer status: {summarize_review(artifacts.review_checks)}")
    print(f"Periods: {metrics['periods']}")
    print(f"Total return: {metrics['total_return']:.2%}")
    print(f"Annualized return: {metrics['annualized_return']:.2%}")
    print(f"Sharpe: {metrics['sharpe']:.2f}")
    print(f"Max drawdown: {metrics['max_drawdown']:.2%}")
    print(f"Average turnover: {metrics['average_turnover']:.2%}")
    print(f"Average cost drag: {metrics['average_cost_drag']:.3%}")
    print(f"Report: {artifacts.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
