"""Read a workflow step's inline shell from the file it ships in and run it.

The evidence this serves has to follow the shipped step, so the body is read
out of the workflow rather than copied here. A copy would keep passing while
the step it stands for drifted away from it.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

RUN_SHELL = "/bin/bash"

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def fixture_path(name: str) -> Path:
    """Locate one inert execution-record fixture in the fixtures home by name.

    The path is handed to the step under test rather than the content, because
    the step reads its input from disk and part of what the evidence covers is
    how it behaves when that file is unreadable or malformed.
    """
    return FIXTURES_DIR / name


@dataclass(frozen=True)
class StepShell:
    """One workflow step's inline shell, with the file and job it came from."""

    workflow: str
    job: str
    name: str
    body: str
    env: dict[str, str]


def repository_root() -> Path:
    """The checkout root, resolved from this file's location."""
    return Path(__file__).resolve().parents[2]


def workflow_path(workflow: str) -> Path:
    return repository_root() / ".github" / "workflows" / workflow


def workflows_carrying_step(step_name: str) -> list[str]:
    """Name every workflow file whose jobs carry a step with this name.

    The carrying set is discovered rather than listed by hand, so a workflow
    that gains the step later is covered without anyone remembering to add it.
    A caller that requires the step to exist must assert the result is
    non-empty: a renamed or deleted step yields an empty discovery, and a
    parametrization over an empty list would otherwise pass by running nothing.
    """
    workflows_dir = repository_root() / ".github" / "workflows"
    carrying = []
    for path in sorted(workflows_dir.glob("*.yml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        for job in (document.get("jobs") or {}).values():
            if any(step.get("name") == step_name for step in job.get("steps") or []):
                carrying.append(path.name)
                break
    return carrying


def read_step_shell(workflow: str, step_name: str) -> StepShell:
    """Return the named step's inline shell from the given workflow file.

    Raises LookupError when the workflow holds no such step, so a renamed or
    deleted step fails the evidence loudly instead of silently testing nothing.
    """
    path = workflow_path(workflow)
    document = yaml.safe_load(path.read_text(encoding="utf-8"))

    for job_name, job in (document.get("jobs") or {}).items():
        for step in job.get("steps") or []:
            if step.get("name") != step_name:
                continue
            if "run" not in step:
                raise LookupError(
                    f"{workflow}: step {step_name!r} in job {job_name!r} "
                    "carries no inline shell"
                )
            return StepShell(
                workflow=workflow,
                job=job_name,
                name=step_name,
                body=step["run"],
                env=dict(step.get("env") or {}),
            )

    raise LookupError(f"{workflow}: no step named {step_name!r}")


def run_step_shell(
    step: StepShell, environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    """Execute the step's shell with the supplied environment.

    The environment is passed whole rather than merged over the caller's, so a
    variable the step reads is present only when the case under test supplies
    it. PATH is carried through because the body invokes jq.
    """
    import os

    env = {"PATH": os.environ.get("PATH", "")}
    env.update(environment)

    return subprocess.run(  # noqa: S603 - fixed interpreter, body from the repo
        [RUN_SHELL, "-c", step.body],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
