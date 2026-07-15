from pathlib import Path

from google.adk.agents import SequentialAgent

from nyxnight_factory.agents import build_workflow


def test_factory_is_real_adk_sequential_workflow(tmp_path: Path) -> None:
    workflow = build_workflow(tmp_path / "output")
    assert isinstance(workflow, SequentialAgent)
    assert workflow.name == "nyxnight_creation_workflow"
    assert [agent.name for agent in workflow.sub_agents] == [
        "requirements_agent",
        "backend_builder",
        "frontend_builder",
        "verification_agent",
    ]


def test_scopes_are_disjoint(tmp_path: Path) -> None:
    workflow = build_workflow(tmp_path / "output")
    scopes = [
        set(getattr(agent, "file_paths", ()))
        for agent in workflow.sub_agents
        if hasattr(agent, "file_paths")
    ]
    assert scopes
    for index, scope in enumerate(scopes):
        assert all(scope.isdisjoint(other) for other in scopes[index + 1 :])
