from scripts import caller_workflows


def test_caller_workflow_outputs_match_manifest() -> None:
    assert caller_workflows.check_default_workspace() == []
