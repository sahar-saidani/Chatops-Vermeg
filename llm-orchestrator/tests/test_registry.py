from agents.registry import AGENT_REGISTRY, get_agent_definition


def test_all_six_existing_agents_registered():
    # Only agents that actually exist in the repo and are wired into the
    # Spring Boot chatops.rabbitmq.queues config are registered.
    assert set(AGENT_REGISTRY.keys()) == {
        "git", "jenkins", "jira", "installation", "infrastructure", "log",
    }


def test_git_step_builds_repo_flag():
    definition = get_agent_definition("git")
    args = definition.steps[0].build({"repo": "owner/name"})
    assert args == ["main.py", "analyze", "--repo", "owner/name"]


def test_jira_has_two_sequential_steps():
    definition = get_agent_definition("jira")
    assert [s.build({}) for s in definition.steps] == [
        ["main.py", "collect"],
        ["main.py", "report"],
    ]


def test_infrastructure_working_dir_targets_app_subfolder():
    definition = get_agent_definition("infrastructure")
    assert definition.working_dir == "infrastructure-Agent/app"


def test_unknown_agent_raises():
    import pytest

    with pytest.raises(KeyError):
        get_agent_definition("oracle")
