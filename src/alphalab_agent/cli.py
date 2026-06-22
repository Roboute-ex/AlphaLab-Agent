"""Command line interface for AlphaLab Agent v0.7."""

from __future__ import annotations

import argparse
from pathlib import Path

from alphalab_agent.config import ResearchConfig, load_config
from alphalab_agent.data import load_market_data
from alphalab_agent.pipeline import run_v0_pipeline
from alphalab_agent.review.checks import summarize_review
from alphalab_agent.workflow import run_agent_workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AlphaLab Agent deterministic v0.7 workflow.")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the synthetic-data research demo and write artifacts/report.md.",
    )
    parser.add_argument(
        "--agent-demo",
        action="store_true",
        help="Run the deterministic agent-style workflow and write plan/log artifacts.",
    )
    parser.add_argument(
        "--config",
        help="Optional JSON config file. If omitted, the deterministic default config is used.",
    )
    parser.add_argument(
        "--goal",
        default="Run a top-5 synthetic multi-factor research workflow with 5 day labels and 5 bps cost.",
        help="Natural-language research goal for --agent-demo. Parsed by a rule-based PlannerAgent.",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts",
        help="Directory for generated artifacts. Defaults to artifacts/.",
    )
    parser.add_argument(
        "--data-source",
        choices=["synthetic", "csv", "yfinance"],
        default="synthetic",
        help="Explicit data source. Defaults to synthetic; real adapters are disabled unless selected.",
    )
    parser.add_argument("--csv-path", help="CSV path for --data-source csv.")
    parser.add_argument("--symbol", help="Symbol to use when CSV data has no symbol column.")
    parser.add_argument("--ticker", help="Ticker for --data-source yfinance.")
    parser.add_argument("--start", help="Start date for --data-source yfinance, YYYY-MM-DD.")
    parser.add_argument("--end", help="End date for --data-source yfinance, YYYY-MM-DD.")
    parser.add_argument("--interval", default="1d", help="Interval for --data-source yfinance.")
    parser.add_argument(
        "--backtest-mode",
        choices=["execution", "label_based"],
        help="Backtest mode. Defaults to execution.",
    )
    parser.add_argument(
        "--weighting-mode",
        choices=["equal_weight", "config_weight", "ic_weight_train_only", "rankic_weight_train_only"],
        help="Walk-forward factor weighting mode.",
    )
    parser.add_argument("--benchmark-seed", type=int, help="Seed for the random top-k benchmark.")
    parser.add_argument("--no-manifest", action="store_true", help="Disable artifacts/run_manifest.json output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.demo and not args.agent_demo:
        parser.print_help()
        return 2

    if args.config:
        config = load_config(args.config)
        config = ResearchConfig(**{**config.to_dict(), "output_dir": Path(args.output_dir)})
    else:
        config = ResearchConfig(output_dir=Path(args.output_dir), report_name="report.md")
    overrides = {}
    if args.backtest_mode:
        overrides["backtest_mode"] = args.backtest_mode
    if args.weighting_mode:
        overrides["weighting_mode"] = args.weighting_mode
    if args.benchmark_seed is not None:
        overrides["benchmark_seed"] = args.benchmark_seed
    if args.no_manifest:
        overrides["generate_manifest"] = False
    if overrides:
        config = ResearchConfig(**{**config.to_dict(), **overrides})
    raw_data = load_market_data(
        args.data_source,
        csv_path=args.csv_path,
        symbol=args.symbol,
        ticker=args.ticker,
        start=args.start,
        end=args.end,
        interval=args.interval,
    )
    if raw_data is not None:
        n_symbols = int(raw_data["symbol"].nunique())
        n_days = int(raw_data["date"].nunique())
        top_k = min(config.top_k, n_symbols)
        start_date = str(raw_data["date"].min().date())
        config = ResearchConfig(
            **{
                **config.to_dict(),
                "data_source": args.data_source,
                "n_symbols": n_symbols,
                "n_days": n_days,
                "top_k": top_k,
                "start_date": start_date,
            }
        )
    if args.agent_demo:
        if raw_data is not None:
            parser.error("--agent-demo currently supports synthetic data only; use --demo for explicit data adapters.")
        workflow_artifacts = run_agent_workflow(args.goal, base_config=config, write_artifacts=True)
        artifacts = workflow_artifacts.research_artifacts
    else:
        workflow_artifacts = None
        artifacts = run_v0_pipeline(config, write_report=True, raw_data=raw_data)
    metrics = artifacts.metrics

    if workflow_artifacts is not None:
        print("AlphaLab Agent v0.7 agent demo complete")
        print("Steps: goal -> ResearchPlan -> step logs -> deterministic research tools -> reviewer -> report")
        print(f"Plan: {workflow_artifacts.plan_path}")
        print(f"Step logs: {workflow_artifacts.step_log_path}")
    else:
        print("AlphaLab Agent v0.7 demo complete")
        print(
            "Steps: synthetic data -> panel -> factors -> labels -> factor analysis -> "
            "execution backtest -> benchmarks -> walk-forward validation -> sensitivity -> reviewer -> report"
        )
    print(f"Reviewer status: {summarize_review(artifacts.review_checks)}")
    print(f"Periods: {metrics['periods']}")
    print(f"Total return: {metrics['total_return']:.2%}")
    print(f"Annualized return: {metrics['annualized_return']:.2%}")
    print(f"Sharpe: {metrics['sharpe']:.2f}")
    print(f"Max drawdown: {metrics['max_drawdown']:.2%}")
    print(f"Average turnover: {metrics['average_turnover']:.2%}")
    print(f"Average cost drag: {metrics['average_cost_drag']:.3%}")
    print(f"Report: {artifacts.report_path}")
    if artifacts.html_report_path is not None:
        print(f"HTML report: {artifacts.html_report_path}")
    if artifacts.chart_paths:
        print(f"Charts: {', '.join(str(path) for path in artifacts.chart_paths.values())}")
    if artifacts.manifest_path is not None:
        print(f"Run manifest: {artifacts.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
