from pathlib import Path

from alphalab_agent.config import ResearchConfig
from alphalab_agent.workflow import PlannerAgent, run_agent_workflow


def test_planner_agent_parses_research_plan_without_llm():
    config = ResearchConfig(n_symbols=30, top_k=4, forward_days=5, transaction_cost_bps=5.0)
    plan = PlannerAgent().parse("Run top-7 strategy on 30 symbols with 10 day labels and 3 bps cost", config)

    assert plan.data_source == "synthetic"
    assert plan.top_k == 7
    assert plan.universe_size == 30
    assert plan.forward_days == 10
    assert plan.transaction_cost_bps == 3.0


def test_agent_workflow_writes_plan_and_step_logs():
    import shutil

    root = Path(__file__).resolve().parents[1]
    output_dir = root / "artifacts" / "test_agent_workflow"
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = ResearchConfig(seed=21, n_days=120, n_symbols=10, top_k=3, output_dir=output_dir)
    artifacts = run_agent_workflow("Run top-3 research with 5 day labels", config, write_artifacts=True)

    assert artifacts.plan.top_k == 3
    assert artifacts.plan_path is not None
    assert artifacts.plan_path.exists()
    assert artifacts.step_log_path is not None
    assert artifacts.step_log_path.exists()
    assert [step.step for step in artifacts.steps] == [
        "parse_research_plan",
        "build_research_config",
        "run_research_pipeline",
        "review_results",
    ]
    assert artifacts.research_artifacts.report_path is not None
    assert artifacts.research_artifacts.report_path.exists()

    shutil.rmtree(output_dir, ignore_errors=True)
