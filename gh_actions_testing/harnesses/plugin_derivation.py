"""Run a reusable workflow's plugin-derivation step over a consumer's settings.

The step reads the caller repository's `.claude/settings.json` from its
checkout and writes the plugin list it derived to the file `GITHUB_OUTPUT`
names. This harness stages a settings payload as that checkout, runs the step
as the workflow ships it, and reports what the step derived. It decides
nothing about what the derived list ought to hold.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from gh_actions_testing.harnesses.workflow_steps import read_step_shell, run_step_shell

PLUGIN_DERIVATION_STEP = "Derive Claude plugins and marketplaces"

PLUGINS_OUTPUT = "plugins"


@dataclass(frozen=True)
class DerivedPlugins:
    """What one run of the derivation step reported."""

    workflow: str
    returncode: int
    stderr: str
    plugins: tuple[str, ...]


def parse_github_output(text: str) -> dict[str, str]:
    """Read the `name<<delimiter` blocks a step appended to `GITHUB_OUTPUT`."""
    values: dict[str, str] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        name, separator, delimiter = lines[index].partition("<<")
        index += 1
        if not separator:
            continue
        block: list[str] = []
        while index < len(lines) and lines[index] != delimiter:
            block.append(lines[index])
            index += 1
        index += 1
        values[name] = "\n".join(block)
    return values


def derive_plugins(
    workflow: str,
    work_directory: Path,
    settings_payload: Path | None,
    extra_plugins: str = "",
) -> DerivedPlugins:
    """Run the workflow's derivation step with the caller's project plugins opted in.

    `settings_payload` is copied to the checkout's `.claude/settings.json`; with
    none, the checkout holds no settings file. `extra_plugins` is the caller's
    space-separated input.
    """
    if settings_payload is not None:
        settings_home = work_directory / ".claude"
        settings_home.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(settings_payload, settings_home / "settings.json")

    output_file = work_directory / "github_output"
    output_file.touch()

    step = read_step_shell(workflow, PLUGIN_DERIVATION_STEP)
    result = run_step_shell(
        step,
        {
            "USE_PROJECT_PLUGINS": "true",
            "PLUGIN_MARKETPLACES": "",
            "EXTRA_PLUGINS": extra_plugins,
            "GITHUB_OUTPUT": str(output_file),
        },
        working_directory=work_directory,
    )

    derived = parse_github_output(output_file.read_text(encoding="utf-8"))
    plugins = tuple(
        line for line in derived.get(PLUGINS_OUTPUT, "").splitlines() if line
    )
    return DerivedPlugins(
        workflow=workflow,
        returncode=result.returncode,
        stderr=result.stderr,
        plugins=plugins,
    )
