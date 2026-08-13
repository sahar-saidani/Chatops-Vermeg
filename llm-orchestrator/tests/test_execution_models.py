from execution.aggregator import ResultAggregator
from execution.models import AgentCommand, AgentResult, ExecutionPlan


def test_command_creation_and_result_correlation():
    plan = ExecutionPlan.create(
        tenant="MAIF",
        machine_reference="MAIF-WINDOWS-01",
        environment="DEV",
        # ExecutionPlan.create made operating_system a required keyword-only
        # argument; this call was never updated, so the test failed on a
        # TypeError before reaching a single assertion.
        operating_system="WINDOWS",
        agent_keys=["git", "jenkins"],
        action="analysis",
        parameters={"environment": "DEV"},
    )

    command = AgentCommand.from_plan(plan, "git")
    assert command.task_id == plan.task_id
    assert command.machine_reference == "MAIF-WINDOWS-01"
    assert command.agent == "git"

    aggregator = ResultAggregator()
    aggregator.register(plan)
    aggregator.record(
        AgentResult(
            task_id=plan.task_id,
            tenant="MAIF",
            machine_reference="MAIF-WINDOWS-01",
            agent="git",
            status="SUCCESS",
            data={"value": 1},
        )
    )
    aggregator.record(
        AgentResult(
            task_id=plan.task_id,
            tenant="MAIF",
            machine_reference="MAIF-WINDOWS-01",
            agent="jenkins",
            status="SUCCESS",
            data={"value": 2},
        )
    )

    context = aggregator.build_context(plan.task_id)
    assert context["task_id"] == plan.task_id
    assert context["tenant"] == "MAIF"
    assert context["machine_reference"] == "MAIF-WINDOWS-01"
    assert context["is_complete"] is True
    assert len(context["results"]) == 2
