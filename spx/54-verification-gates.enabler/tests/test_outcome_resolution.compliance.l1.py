"""Compliance evidence: a job fails unless the agent run's record shows it completed.

The rule is a boundary, so the cases are the records that must be rejected: a
record that is absent, unreadable as the array of messages the step iterates,
carrying no result entry, or carrying a result that reports an error. One record
stands for the passing side so the rejection cannot be produced by a step that
rejects everything.

`execution_completed.json` and `execution_error_flag.json` are real records
captured from live runs — the second is the one that produced a passing check
for a run that never reviewed anything, which is the condition this step exists
to reject.

The shell under test is read from the workflow file it ships in, so the evidence
follows an edit to the shipped step. Every workflow carrying the step is
exercised, which is also what establishes that the copies still agree.
"""

from __future__ import annotations

import pytest

from gh_actions_testing.harnesses.workflow_steps import (
    fixture_path,
    read_step_shell,
    run_step_shell,
)

STEP_NAME = "Verify the agent run completed"

WORKFLOWS = [
    "spec-tree-review.yml",
    "claude-code-review.yml",
    "claude.yml",
    "spec-tree.yml",
]

REJECTED_RECORDS = [
    ("execution_error_flag.json", "a result reporting an error"),
    ("execution_error_subtype.json", "a result whose subtype is not success"),
    ("execution_no_result.json", "no result entry"),
    ("execution_no_messages.json", "no messages at all"),
    ("execution_truncated.json", "a record truncated mid-write"),
    ("execution_null.json", "a null record"),
    ("execution_object.json", "an object where the array is expected"),
    ("execution_number.json", "a number where the array is expected"),
    ("execution_string.json", "a string where the array is expected"),
    ("execution_scalar_element.json", "a scalar among the message objects"),
]


def _run(workflow: str, execution_file: str):
    step = read_step_shell(workflow, STEP_NAME)
    return run_step_shell(step, {"EXECUTION_FILE": execution_file})


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_completed_run_passes(workflow: str) -> None:
    """A record showing the run completed leaves the job passing."""
    result = _run(workflow, str(fixture_path("execution_completed.json")))

    assert result.returncode == 0, (
        f"{workflow}: a completed run was rejected\n{result.stderr}"
    )


@pytest.mark.parametrize("workflow", WORKFLOWS)
@pytest.mark.parametrize("fixture,condition", REJECTED_RECORDS)
def test_incomplete_run_fails(workflow: str, fixture: str, condition: str) -> None:
    """Every record that does not show a completed run fails the job."""
    result = _run(workflow, str(fixture_path(fixture)))

    assert result.returncode != 0, (
        f"{workflow}: accepted {condition} ({fixture}), so the check would report "
        f"a completed agent run that did not happen\n{result.stdout}"
    )


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_absent_record_fails(workflow: str, tmp_path) -> None:
    """A record the agent never wrote fails the job."""
    result = _run(workflow, str(tmp_path / "claude-execution-output.json"))

    assert result.returncode != 0, f"{workflow}: accepted an absent record"


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_unset_record_path_fails(workflow: str) -> None:
    """An empty record path fails the job rather than reading an unrelated file."""
    result = _run(workflow, "")

    assert result.returncode != 0, f"{workflow}: accepted an empty record path"


@pytest.mark.parametrize("workflow", WORKFLOWS)
@pytest.mark.parametrize("fixture,condition", REJECTED_RECORDS)
def test_rejection_names_the_condition(
    workflow: str, fixture: str, condition: str
) -> None:
    """A rejection reports why, rather than surfacing a raw parser failure.

    The step's own reason for existing is that a check must not stand for
    something it did not establish; a rejection an operator cannot act on
    repeats that fault in a smaller way.
    """
    result = _run(workflow, str(fixture_path(fixture)))

    assert "::error::" in result.stderr, (
        f"{workflow}: rejected {condition} ({fixture}) without an actionable "
        f"message\nstderr: {result.stderr}"
    )


def test_every_copy_of_the_step_is_identical() -> None:
    """The step's shell agrees across every workflow that carries it.

    The step is duplicated so a consumer pins one self-contained file. Nothing
    else establishes that a fix applied to one copy reached the others.
    """
    bodies = {w: read_step_shell(w, STEP_NAME).body for w in WORKFLOWS}
    reference = bodies[WORKFLOWS[0]]

    drifted = [w for w, body in bodies.items() if body != reference]

    assert not drifted, (
        f"the step's shell differs in {drifted} from {WORKFLOWS[0]}, so a change "
        "reached some workflows and not others"
    )
