from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final


MANIFEST_PATH: Final = Path("examples/caller-workflows/manifest.yaml")
FULL_SHA_RE: Final = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class CallerWorkflow:
    id: str
    example: Path
    reusable: str
    timeout_var: str
    timeout_default: str


@dataclass(frozen=True)
class CallerManifest:
    repository: str
    tracked_ref: str
    default_expected_ref: str
    workflows: tuple[CallerWorkflow, ...]


@dataclass(frozen=True)
class Drift:
    path: Path
    message: str


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    msg = f"could not find repository root from {start}"
    raise RuntimeError(msg)


def resolve_git_sha(ref: str, repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", ref],
        cwd=repo_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    sha = result.stdout.strip()
    if not FULL_SHA_RE.fullmatch(sha):
        msg = f"{ref} resolved to non-SHA value {sha!r}"
        raise ValueError(msg)
    return sha


def load_manifest(repo_root: Path) -> CallerManifest:
    manifest_path = repo_root / MANIFEST_PATH
    with manifest_path.open(encoding="utf-8") as manifest_file:
        raw = _parse_manifest(manifest_file.read())
    if raw.get("schema_version") != 1:
        msg = f"{MANIFEST_PATH} schema_version must be 1"
        raise ValueError(msg)
    workflows = tuple(_load_workflow(item) for item in raw["workflows"])
    return CallerManifest(
        repository=str(raw["repository"]),
        tracked_ref=str(raw["tracked_ref"]),
        default_expected_ref=str(raw["default_expected_ref"]),
        workflows=workflows,
    )


def _parse_manifest(text: str) -> dict[str, Any]:
    raw: dict[str, Any] = {}
    workflows: list[dict[str, str]] = []
    active_workflow: dict[str, str] | None = None
    in_workflows = False

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "workflows:":
            in_workflows = True
            raw["workflows"] = workflows
            continue
        if in_workflows:
            if stripped.startswith("- "):
                active_workflow = {}
                workflows.append(active_workflow)
                key, value = _parse_key_value(stripped[2:], line_number)
                active_workflow[key] = value
                continue
            if active_workflow is None:
                msg = f"{MANIFEST_PATH}:{line_number}: workflow field before workflow item"
                raise ValueError(msg)
            key, value = _parse_key_value(stripped, line_number)
            active_workflow[key] = value
            continue
        key, value = _parse_key_value(stripped, line_number)
        raw[key] = int(value) if key == "schema_version" else value

    return raw


def _parse_key_value(line: str, line_number: int) -> tuple[str, str]:
    if ":" not in line:
        msg = f"{MANIFEST_PATH}:{line_number}: expected key: value"
        raise ValueError(msg)
    key, value = line.split(":", 1)
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return key.strip(), value


def _load_workflow(raw: dict[str, Any]) -> CallerWorkflow:
    return CallerWorkflow(
        id=str(raw["id"]),
        example=Path(str(raw["example"])),
        reusable=str(raw["reusable"]),
        timeout_var=str(raw["timeout_var"]),
        timeout_default=str(raw["timeout_default"]),
    )


def check_workspace(repo_root: Path, expected_sha: str) -> list[Drift]:
    manifest = load_manifest(repo_root)
    drifts: list[Drift] = []
    for workflow in manifest.workflows:
        drifts.extend(check_example(repo_root, manifest, workflow, expected_sha))
    return drifts


def check_default_workspace() -> list[Drift]:
    repo_root = find_repo_root(Path.cwd())
    manifest = load_manifest(repo_root)
    expected_sha = resolve_git_sha(manifest.default_expected_ref, repo_root)
    return check_workspace(repo_root, expected_sha)


def check_example(
    repo_root: Path,
    manifest: CallerManifest,
    workflow: CallerWorkflow,
    expected_sha: str,
) -> list[Drift]:
    text = (repo_root / workflow.example).read_text(encoding="utf-8")
    drifts: list[Drift] = []
    uses_match = _uses_pattern(workflow.reusable, manifest).search(text)
    if uses_match is None:
        drifts.append(
            Drift(
                path=workflow.example,
                message=f"missing release-lane uses line for {workflow.reusable}",
            )
        )
    elif uses_match.group("ref") != expected_sha:
        drifts.append(
            Drift(
                path=workflow.example,
                message=f"{workflow.reusable} pins {uses_match.group('ref')}, expected {expected_sha}",
            )
        )

    timeout_match = _timeout_pattern(workflow).search(text)
    if timeout_match is None:
        drifts.append(
            Drift(
                path=workflow.example,
                message=f"missing timeout default for vars.{workflow.timeout_var}",
            )
        )
    elif timeout_match.group("value") != workflow.timeout_default:
        drifts.append(
            Drift(
                path=workflow.example,
                message=f"vars.{workflow.timeout_var} defaults to {timeout_match.group('value')}, expected {workflow.timeout_default}",
            )
        )
    return drifts


def render_workspace(
    repo_root: Path,
    expected_sha: str,
    manifest: CallerManifest,
) -> dict[Path, str]:
    return render_examples(repo_root, expected_sha, manifest)


def render_examples(
    repo_root: Path,
    expected_sha: str,
    manifest: CallerManifest,
) -> dict[Path, str]:
    rendered: dict[Path, str] = {}
    for workflow in manifest.workflows:
        path = workflow.example
        rendered[path] = render_example(
            (repo_root / path).read_text(encoding="utf-8"),
            workflow,
            manifest,
            expected_sha,
        )
    return rendered


def write_workspace(repo_root: Path, expected_sha: str) -> None:
    manifest = load_manifest(repo_root)
    for relative_path, text in render_workspace(repo_root, expected_sha, manifest).items():
        (repo_root / relative_path).write_text(text, encoding="utf-8")


def render_example(
    text: str,
    workflow: CallerWorkflow,
    manifest: CallerManifest,
    expected_sha: str,
) -> str:
    text = _replace_release_lane_comment(text)
    text = _replace_uses_line(text, workflow.reusable, manifest, expected_sha)
    return _replace_timeout_default(text, workflow)


def _replace_release_lane_comment(text: str) -> str:
    old = (
        "# Renovate keeps this SHA current; the trailing `# main` comment is the branch\n"
        "    # Renovate tracks. See README \"Security\" for the full rationale."
    )
    new = (
        "# This example's release-lane SHA is rendered from examples/caller-workflows/manifest.yaml.\n"
        "    # Consumer repos keep the copied SHA current with the Renovate preset in README \"Security\"."
    )
    return text.replace(old, new)


def _replace_uses_line(
    text: str,
    reusable: str,
    manifest: CallerManifest,
    expected_sha: str,
) -> str:
    return _uses_pattern(reusable, manifest).sub(
        rf"\g<prefix>{expected_sha}\g<suffix>",
        text,
    )


def _replace_timeout_default(text: str, workflow: CallerWorkflow) -> str:
    return _timeout_pattern(workflow).sub(
        rf"\g<prefix>{workflow.timeout_default}\g<suffix>",
        text,
    )


def _uses_pattern(reusable: str, manifest: CallerManifest) -> re.Pattern[str]:
    escaped = re.escape(f"{manifest.repository}/{reusable}")
    return re.compile(
        rf"(?P<prefix>uses:\s+{escaped}@)(?P<ref>[0-9a-f]{{40}})(?P<suffix>\s+#\s+{re.escape(manifest.tracked_ref)})"
    )


def _timeout_pattern(workflow: CallerWorkflow) -> re.Pattern[str]:
    return re.compile(
        rf"(?P<prefix>timeout_minutes:\s+\$\{{\{{\s*vars\.{re.escape(workflow.timeout_var)}\s+\|\|\s+')(?P<value>[^']+)(?P<suffix>'\s*\}}\}})"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--expected-sha")
    args = parser.parse_args(argv)

    repo_root = args.repo_root or find_repo_root(Path.cwd())
    manifest = load_manifest(repo_root)
    expected_sha = args.expected_sha or resolve_git_sha(
        manifest.default_expected_ref,
        repo_root,
    )
    if not FULL_SHA_RE.fullmatch(expected_sha):
        parser.error("--expected-sha must be a full 40-character commit SHA")

    if args.write:
        write_workspace(repo_root, expected_sha)
        return 0

    drifts = check_workspace(repo_root, expected_sha)
    if drifts:
        for drift in drifts:
            print(f"{drift.path}: {drift.message}", file=sys.stderr)
        print(
            "Run `python3 -m scripts.check_caller_workflows --write` to refresh generated caller refs.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
