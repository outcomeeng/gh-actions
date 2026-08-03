"""Compliance evidence: a job fails unless the agent run's record shows it completed.

The rule is a boundary, so the cases are the records that must be rejected: a
record that is absent, unreadable as the array of messages the step iterates,
carrying no result entry, or carrying a result that reports an error. The
passing side is a differential pair — a completed run reporting nothing and a
completed run reporting many findings — so the rejection cannot be produced by
a step that rejects everything, and a step that started reading findings could
not treat the two alike. The two error records isolate one disjunct each:
`execution_error_flag.json` raises only the error flag and
`execution_error_subtype.json` only the non-success subtype.

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
    workflows_carrying_step,
)

STEP_NAME = "Verify the agent run completed"

# Discovered, not listed by hand, so a workflow that gains the step later is
# covered without anyone remembering to add it here. test_step_is_carried
# guards the discovery: an empty list would let every parametrized case pass
# by running nothing.
WORKFLOWS = workflows_carrying_step(STEP_NAME)


def test_step_is_carried() -> None:
    """The step exists somewhere, so the parametrized evidence runs at all.

    A renamed or deleted step yields an empty discovery; without this guard the
    suite would go green while exercising nothing.
    """
    assert WORKFLOWS, (
        f"no workflow carries a step named {STEP_NAME!r}; the parametrized "
        "cases below would all pass vacuously"
    )


PASSING_RECORDS = [
    ("execution_completed.json", "a completed run reporting no findings"),
    ("execution_completed_findings.json", "a completed run reporting findings"),
]

REJECTED_RECORDS = [
    ("execution_error_flag.json", "a result raising only the error flag"),
    ("execution_error_subtype.json", "a result with only a non-success subtype"),
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
@pytest.mark.parametrize("fixture,condition", PASSING_RECORDS)
def test_completed_run_passes(workflow: str, fixture: str, condition: str) -> None:
    """A record showing the run completed leaves the job passing.

    The two records agree on completion and differ only in the findings they
    carry, so a step that passes one and not the other has started reading
    findings — the boundary the check must never cross.
    """
    result = _run(workflow, str(fixture_path(fixture)))

    assert result.returncode == 0, (
        f"{workflow}: rejected {condition} ({fixture})\n{result.stderr}"
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
