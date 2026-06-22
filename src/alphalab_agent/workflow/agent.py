"""Lightweight deterministic agent-style workflow wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from alphalab_agent.config import ResearchConfig
from alphalab_agent.pipeline import ResearchArtifacts, run_v0_pipeline
from alphalab_agent.review.checks import summarize_review
from alphalab_agent.workflow.planner import PlannerAgent, ResearchPlan, write_plan
from alphalab_agent.workflow.steps import StepLog, write_step_logs


@dataclass(frozen=True)
class AgentWorkflowArtifacts:
    """Artifacts from the deterministic agent-style workflow."""

    plan: ResearchPlan
    steps: list[StepLog]
    research_artifacts: ResearchArtifacts
    plan_path: Path | None
    step_log_path: Path | None


def run_agent_workflow(
    goal: str,
    base_config: ResearchConfig | None = None,
    write_artifacts: bool = True,
) -> AgentWorkflowArtifacts:
    """Run PlannerAgent -> deterministic research pipeline -> logged summary."""

    base_config = base_config or ResearchConfig()
    steps: list[StepLog] = []

    planner = PlannerAgent()
    plan = planner.parse(goal, base_config=base_config)
    steps.append(
        StepLog(
            step="parse_research_plan",
            status="PASS",
            message="Parsed user goal into a deterministic ResearchPlan.",
            metadata=plan.to_dict(),
        )
    )

    config = plan.to_config(base_config)
    steps.append(
        StepLog(
            step="build_research_config",
            status="PASS",
            message="Converted ResearchPlan to ResearchConfig.",
            metadata={
                "top_k": config.top_k,
                "forward_days": config.forward_days,
                "n_symbols": config.n_symbols,
                "transaction_cost_bps": config.transaction_cost_bps,
            },
        )
    )

    research_artifacts = run_v0_pipeline(config, write_report=write_artifacts)
    steps.append(
        StepLog(
            step="run_research_pipeline",
            status="PASS",
            message="Executed deterministic synthetic research pipeline.",
            metadata={
                "periods": research_artifacts.metrics["periods"],
                "sharpe": research_artifacts.metrics["sharpe"],
                "max_drawdown": research_artifacts.metrics["max_drawdown"],
            },
        )
    )

    review_status = summarize_review(research_artifacts.review_checks)
    steps.append(
        StepLog(
            step="review_results",
            status=review_status,
            message="Collected deterministic Reviewer findings.",
            metadata={"review_status": review_status},
        )
    )

    plan_path = None
    step_log_path = None
    if write_artifacts:
        plan_path = write_plan(config.output_dir / "research_plan.json", plan)
        step_log_path = write_step_logs(config.output_dir / "step_logs.json", steps)

    return AgentWorkflowArtifacts(
        plan=plan,
        steps=steps,
        research_artifacts=research_artifacts,
        plan_path=plan_path,
        step_log_path=step_log_path,
    )
