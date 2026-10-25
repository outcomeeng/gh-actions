"""Compliance evidence: no plugin list a reusable derives carries the retired plugin id.

The rule is a boundary, so the violating cases are the payloads and inputs that
name the retired id: a settings file that enables it (the settings file this
repository carried before the rename, a real consumer payload), a caller input
that lists it, and a settings file that enables it beside its successor. The
conforming cases keep the rule from being met by a step that rewrites or drops
everything: a settings file that already enables the successor, one whose
retired entry is disabled, and one that enables a plugin of the same name from
another marketplace.

The expected plugins come from the fixture a case supplies, so the evidence does
not restate which plugins a consumer enabled. The shell under test is read from
the workflow file it ships in, and every workflow carrying the step is
exercised, which also establishes that the copies still agree.
"""

from __future__ import annotations

import json

import pytest

from gh_actions_testing.harnesses.plugin_derivation import (
    PLUGIN_DERIVATION_STEP,
    derive_plugins,
)
from gh_actions_testing.harnesses.workflow_steps import (
    fixture_path,
    read_step_shell,
    workflows_carrying_step,
)

# Discovered, not listed by hand, so a workflow that gains the step later is
# covered without anyone remembering to add it. test_step_is_carried guards the
# discovery: an empty list would let every parametrized case pass by running
# nothing.
WORKFLOWS = workflows_carrying_step(PLUGIN_DERIVATION_STEP)

RETIRED = "spec-tree@outcomeeng"
SUCCESSOR = "product-tree@outcomeeng"


def _enabled(fixture: str) -> list[str]:
    """The plugins a settings fixture enables, read from the fixture itself."""
    payload = json.loads(fixture_path(fixture).read_text(encoding="utf-8"))
    return [name for name, enabled in payload["enabledPlugins"].items() if enabled]


def test_step_is_carried() -> None:
    """The step exists somewhere, so the parametrized evidence runs at all."""
    assert WORKFLOWS, (
        f"no workflow carries a step named {PLUGIN_DERIVATION_STEP!r}; the "
        "parametrized cases below would all pass vacuously"
    )


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_enabled_retired_id_installs_the_successor_once(
    workflow: str, tmp_path
) -> None:
    fixture = "consumer_settings_retired_plugin.json"

    derived = derive_plugins(workflow, tmp_path, fixture_path(fixture))

    assert derived.returncode == 0, f"{workflow}: the step failed\n{derived.stderr}"
    assert RETIRED not in derived.plugins, (
        f"{workflow}: the derived list {derived.plugins} carries the retired id"
    )
    assert derived.plugins.count(SUCCESSOR) == 1, (
        f"{workflow}: the derived list {derived.plugins} does not carry the "
        "successor exactly once"
    )
    kept = [name for name in _enabled(fixture) if name != RETIRED]
    assert all(name in derived.plugins for name in kept), (
        f"{workflow}: the derived list {derived.plugins} dropped one of {kept}"
    )


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_extra_plugins_retired_id_installs_the_successor_once(
    workflow: str, tmp_path
) -> None:
    derived = derive_plugins(workflow, tmp_path, None, extra_plugins=RETIRED)

    assert derived.returncode == 0, f"{workflow}: the step failed\n{derived.stderr}"
    assert RETIRED not in derived.plugins, (
        f"{workflow}: the derived list {derived.plugins} carries the retired id"
    )
    assert derived.plugins.count(SUCCESSOR) == 1, (
        f"{workflow}: the derived list {derived.plugins} does not carry the "
        "successor exactly once"
    )


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_retired_and_successor_enabled_together_install_the_successor_once(
    workflow: str, tmp_path
) -> None:
    derived = derive_plugins(
        workflow,
        tmp_path,
        fixture_path("consumer_settings_retired_and_successor_plugins.json"),
    )

    assert derived.returncode == 0, f"{workflow}: the step failed\n{derived.stderr}"
    assert RETIRED not in derived.plugins, (
        f"{workflow}: the derived list {derived.plugins} carries the retired id"
    )
    assert derived.plugins.count(SUCCESSOR) == 1, (
        f"{workflow}: the derived list {derived.plugins} carries the successor "
        "other than once"
    )


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_retired_id_in_settings_and_extra_plugins_installs_the_successor_once(
    workflow: str, tmp_path
) -> None:
    derived = derive_plugins(
        workflow,
        tmp_path,
        fixture_path("consumer_settings_retired_plugin.json"),
        extra_plugins=RETIRED,
    )

    assert derived.returncode == 0, f"{workflow}: the step failed\n{derived.stderr}"
    assert RETIRED not in derived.plugins, (
        f"{workflow}: the derived list {derived.plugins} carries the retired id"
    )
    assert derived.plugins.count(SUCCESSOR) == 1, (
        f"{workflow}: the derived list {derived.plugins} carries the successor "
        "other than once"
    )


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_enabled_successor_alone_installs_the_successor_once(
    workflow: str, tmp_path
) -> None:
    derived = derive_plugins(
        workflow, tmp_path, fixture_path("consumer_settings_successor_plugin.json")
    )

    assert derived.returncode == 0, f"{workflow}: the step failed\n{derived.stderr}"
    assert RETIRED not in derived.plugins, (
        f"{workflow}: the derived list {derived.plugins} carries the retired id"
    )
    assert derived.plugins.count(SUCCESSOR) == 1, (
        f"{workflow}: the derived list {derived.plugins} carries the successor "
        "other than once"
    )


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_disabled_retired_id_installs_nothing_in_its_place(
    workflow: str, tmp_path
) -> None:
    derived = derive_plugins(
        workflow,
        tmp_path,
        fixture_path("consumer_settings_retired_plugin_disabled.json"),
    )

    assert derived.returncode == 0, f"{workflow}: the step failed\n{derived.stderr}"
    assert RETIRED not in derived.plugins, (
        f"{workflow}: the derived list {derived.plugins} carries the retired id"
    )
    assert SUCCESSOR not in derived.plugins, (
        f"{workflow}: the derived list {derived.plugins} installs the successor "
        "for a disabled entry"
    )


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_same_name_plugin_of_another_marketplace_stays_as_listed(
    workflow: str, tmp_path
) -> None:
    fixture = "consumer_settings_retired_plugin_other_marketplace.json"

    derived = derive_plugins(workflow, tmp_path, fixture_path(fixture))

    assert derived.returncode == 0, f"{workflow}: the step failed\n{derived.stderr}"
    assert sorted(derived.plugins) == sorted(_enabled(fixture)), (
        f"{workflow}: the derived list {derived.plugins} differs from the "
        f"enabled plugins {_enabled(fixture)}"
    )


def test_every_copy_of_the_step_is_identical() -> None:
    """The step's shell agrees across every workflow that carries it.

    The step is duplicated so a consumer pins one self-contained file. Nothing
    else establishes that a fix applied to one copy reached the others.
    """
    bodies = {
        workflow: read_step_shell(workflow, PLUGIN_DERIVATION_STEP).body
        for workflow in WORKFLOWS
    }
    reference = bodies[WORKFLOWS[0]]

    drifted = [workflow for workflow, body in bodies.items() if body != reference]

    assert not drifted, (
        f"the step's shell differs in {drifted} from {WORKFLOWS[0]}, so a change "
        "reached some workflows and not others"
    )
