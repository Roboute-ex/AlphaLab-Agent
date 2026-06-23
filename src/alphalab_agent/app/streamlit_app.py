"""Optional Streamlit demo for AlphaLab Agent.

Streamlit is an optional dependency. This module is importable without
Streamlit installed so tests and the deterministic core keep working.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from alphalab_agent import __version__
from alphalab_agent.config import ResearchConfig
from alphalab_agent.review.checks import summarize_review
from alphalab_agent.workflow import run_agent_workflow


DEFAULT_GOAL = "Run a top-5 synthetic multi-factor research workflow with 5 day labels and 5 bps cost."


def build_demo_config(
    *,
    seed: int = 42,
    n_days: int = 504,
    n_symbols: int = 50,
    top_k: int = 5,
    forward_days: int = 5,
    rebalance_every: int = 5,
    transaction_cost_bps: float = 5.0,
    backtest_mode: str = "execution",
    weighting_mode: str = "equal_weight",
    enable_supervised_model: bool = False,
    model_type: str = "ridge",
    output_dir: str | Path = "artifacts",
) -> ResearchConfig:
    """Build a deterministic config from UI values."""

    return ResearchConfig(
        seed=seed,
        n_days=n_days,
        n_symbols=n_symbols,
        top_k=top_k,
        forward_days=forward_days,
        rebalance_every=rebalance_every,
        transaction_cost_bps=transaction_cost_bps,
        backtest_mode=backtest_mode,
        weighting_mode=weighting_mode,
        enable_supervised_model=enable_supervised_model,
        model_type=model_type,
        output_dir=Path(output_dir),
    )


def main() -> None:
    """Run the optional Streamlit UI."""

    try:
        import streamlit as st
    except ImportError:
        print("Streamlit is optional. Install it with: python -m pip install -e \".[app]\"")
        print("Then run: python -m streamlit run src/alphalab_agent/app/streamlit_app.py")
        return

    st.set_page_config(page_title=f"AlphaLab Agent v{__version__}", layout="wide")
    st.title(f"AlphaLab Agent v{__version__}")
    st.caption("Deterministic synthetic multi-factor research workflow. No real market data, no LLM, no trading.")

    with st.sidebar:
        st.header("Research Config")
        seed = st.number_input("Seed", min_value=0, value=42, step=1)
        n_days = st.slider("Business days", min_value=120, max_value=756, value=504, step=21)
        n_symbols = st.slider("Symbols", min_value=10, max_value=100, value=50, step=5)
        top_k = st.slider("Top-k long-only", min_value=1, max_value=min(20, n_symbols), value=min(5, n_symbols))
        forward_days = st.slider("Forward label days", min_value=1, max_value=20, value=5)
        rebalance_every = st.slider("Rebalance interval", min_value=1, max_value=20, value=5)
        transaction_cost_bps = st.number_input("Transaction cost bps", min_value=0.0, value=5.0, step=1.0)
        backtest_mode = st.selectbox("Backtest mode", ["execution", "label_based"], index=0)
        weighting_mode = st.selectbox(
            "Walk-forward weighting",
            ["equal_weight", "config_weight", "ic_weight_train_only", "rankic_weight_train_only"],
            index=0,
        )
        enable_supervised_model = st.checkbox("Enable supervised factor model", value=False)
        model_type = st.selectbox("Model type", ["ridge", "linear"], index=0)
        goal = st.text_area("Research goal", value=DEFAULT_GOAL, height=100)
        run_clicked = st.button("Run Deterministic Workflow", type="primary")

    if not run_clicked:
        st.info("Set parameters in the sidebar, then run the deterministic workflow.")
        return

    config = build_demo_config(
        seed=int(seed),
        n_days=int(n_days),
        n_symbols=int(n_symbols),
        top_k=int(top_k),
        forward_days=int(forward_days),
        rebalance_every=int(rebalance_every),
        transaction_cost_bps=float(transaction_cost_bps),
        backtest_mode=str(backtest_mode),
        weighting_mode=str(weighting_mode),
        enable_supervised_model=bool(enable_supervised_model),
        model_type=str(model_type),
    )

    with st.spinner("Running deterministic research workflow..."):
        workflow = run_agent_workflow(goal, base_config=config, write_artifacts=True)
    artifacts = workflow.research_artifacts
    metrics = artifacts.metrics
    review_status = summarize_review(artifacts.review_checks)

    _render_metrics(st, metrics, review_status)

    tab_report, tab_analysis, tab_validation, tab_benchmark, tab_ml, tab_positions, tab_logs = st.tabs(
        ["Report", "Factor Analysis", "Validation", "Benchmark", "ML", "Positions", "Workflow Logs"]
    )
    with tab_report:
        st.markdown(artifacts.report_markdown)
        if artifacts.report_path is not None:
            st.caption(f"Markdown report: {artifacts.report_path}")
        if artifacts.html_report_path is not None:
            st.caption(f"HTML report: {artifacts.html_report_path}")

    with tab_analysis:
        st.subheader("Factor IC / RankIC")
        st.dataframe(artifacts.factor_ic, use_container_width=True)
        st.subheader("Factor Diagnostics")
        st.dataframe(artifacts.factor_diagnostics, use_container_width=True)
        st.subheader("Quantile Returns")
        st.dataframe(artifacts.quantile_returns, use_container_width=True)
        if "equity_curve" in artifacts.chart_paths:
            st.image(str(artifacts.chart_paths["equity_curve"]), caption="Equity curve")

    with tab_validation:
        st.subheader("Walk-Forward Validation")
        st.dataframe(artifacts.walk_forward_validation, use_container_width=True)
        st.subheader("Parameter Sensitivity")
        st.dataframe(artifacts.sensitivity_analysis, use_container_width=True)
        st.subheader("Walk-forward Factor Weights")
        st.dataframe(artifacts.walk_forward_weights, use_container_width=True)

    with tab_benchmark:
        st.subheader("Benchmark Comparison")
        st.dataframe(artifacts.benchmark_comparison.comparison_summary, use_container_width=True)
        st.subheader("Benchmark Metrics")
        st.dataframe(artifacts.benchmark_comparison.benchmark_metrics, use_container_width=True)
        if artifacts.manifest_path is not None:
            st.caption(f"Run manifest: {artifacts.manifest_path}")

    with tab_ml:
        st.subheader("Data Quality")
        st.json(artifacts.data_quality.to_dict())
        st.subheader("Supervised Factor Model")
        st.json(artifacts.supervised_model)
        st.subheader("Out-of-sample ML Evaluation")
        st.dataframe(artifacts.ml_oos_evaluation, use_container_width=True)

    with tab_positions:
        st.subheader("Recent Portfolio Returns")
        st.dataframe(artifacts.backtest.portfolio_returns.tail(20), use_container_width=True)
        st.subheader("Recent Positions")
        st.dataframe(artifacts.backtest.positions.tail(30), use_container_width=True)

    with tab_logs:
        st.subheader("ResearchPlan")
        st.json(workflow.plan.to_dict())
        st.subheader("Step Logs")
        st.json([step.to_dict() for step in workflow.steps])


def _render_metrics(st: Any, metrics: dict[str, float | int], review_status: str) -> None:
    cols = st.columns(5)
    cols[0].metric("Reviewer", review_status)
    cols[1].metric("Total Return", f"{float(metrics['total_return']):.2%}")
    cols[2].metric("Sharpe", f"{float(metrics['sharpe']):.2f}")
    cols[3].metric("Max Drawdown", f"{float(metrics['max_drawdown']):.2%}")
    cols[4].metric("Turnover", f"{float(metrics['average_turnover']):.2%}")


if __name__ == "__main__":
    main()
