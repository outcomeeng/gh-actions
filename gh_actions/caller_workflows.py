from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import yaml


MANIFEST_PATH: Final = Path("examples/caller-workflows/manifest.yaml")
README_PATH: Final = Path("README.md")
WORKFLOWS_DIR: Final = Path(".github/workflows")
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
    default_expected_sha: str
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
        default_expected_sha=_load_expected_sha(raw),
        workflows=workflows,
    )


def _parse_manifest(text: str) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        msg = f"{MANIFEST_PATH}: invalid YAML"
        raise ValueError(msg) from exc
    if not isinstance(raw, dict):
        msg = f"{MANIFEST_PATH} must contain a YAML mapping"
        raise ValueError(msg)
    return raw


def _load_workflow(raw: dict[str, Any]) -> CallerWorkflow:
    return CallerWorkflow(
        id=str(raw["id"]),
        example=Path(str(raw["example"])),
        reusable=str(raw["reusable"]),
        timeout_var=str(raw["timeout_var"]),
        timeout_default=str(raw["timeout_default"]),
    )


def _load_expected_sha(raw: dict[str, Any]) -> str:
    expected_sha = str(raw["default_expected_sha"])
    if not FULL_SHA_RE.fullmatch(expected_sha):
        msg = f"{MANIFEST_PATH} default_expected_sha must be a full 40-character commit SHA"
        raise ValueError(msg)
    return expected_sha


def check_workspace(repo_root: Path, expected_sha: str) -> list[Drift]:
    manifest = load_manifest(repo_root)
    drifts = check_manifest_file_set(repo_root, manifest)
    declared_examples = {workflow.example for workflow in manifest.workflows}
    actual_examples = set(list_caller_examples(repo_root))
    missing_examples = declared_examples - actual_examples
    for workflow in manifest.workflows:
        if workflow.example in missing_examples:
            continue
        drifts.extend(check_example(repo_root, manifest, workflow, expected_sha))
        drifts.extend(
            check_readme_snippets(repo_root, manifest, workflow, expected_sha)
        )
    return drifts


def check_manifest_file_set(repo_root: Path, manifest: CallerManifest) -> list[Drift]:
    declared = {workflow.example for workflow in manifest.workflows}
    actual = set(list_caller_examples(repo_root))
    declared_reusables = {Path(workflow.reusable) for workflow in manifest.workflows}
    actual_reusables = set(list_reusable_workflows(repo_root))
    drifts: list[Drift] = []
    for path in sorted(actual - declared):
        drifts.append(
            Drift(
                path=path,
                message="caller workflow example is not declared in manifest",
            )
        )
    for path in sorted(declared - actual):
        drifts.append(
            Drift(
                path=path,
                message="manifest declares missing caller workflow example",
            )
        )
    for path in sorted(actual_reusables - declared_reusables):
        drifts.append(
            Drift(
                path=path,
                message="reusable workflow is not declared in manifest",
            )
        )
    for path in sorted(
        path
        for path in declared_reusables - actual_reusables
        if (repo_root / path).exists()
    ):
        drifts.append(
            Drift(
                path=path,
                message="manifest reusable workflow path does not declare workflow_call",
            )
        )
    return drifts


def list_reusable_workflows(repo_root: Path) -> tuple[Path, ...]:
    actual: set[Path] = set()
    for path in (repo_root / WORKFLOWS_DIR).glob("*.yml"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?m)^[ \t]+workflow_call:\s*$", text):
            actual.add(path.relative_to(repo_root))
    return tuple(sorted(actual))


def list_caller_examples(repo_root: Path) -> tuple[Path, ...]:
    examples_dir = MANIFEST_PATH.parent
    actual: set[Path] = set()
    for pattern in ("*.yml", "*.yaml"):
        actual.update(
            path.relative_to(repo_root)
            for path in (repo_root / examples_dir).glob(pattern)
            if path.is_file() and path.relative_to(repo_root) != MANIFEST_PATH
        )
    return tuple(sorted(actual))


def check_default_workspace() -> list[Drift]:
    repo_root = find_repo_root(Path.cwd())
    manifest = load_manifest(repo_root)
    return check_workspace(repo_root, manifest.default_expected_sha)


def check_example(
    repo_root: Path,
    manifest: CallerManifest,
    workflow: CallerWorkflow,
    expected_sha: str,
) -> list[Drift]:
    text = (repo_root / workflow.example).read_text(encoding="utf-8")
    drifts: list[Drift] = []
    uses_matches = tuple(_uses_pattern(workflow.reusable, manifest).finditer(text))
    if not uses_matches:
        drifts.append(
            Drift(
                path=workflow.example,
                message=f"missing release-lane uses line for {workflow.reusable}",
            )
        )
    else:
        for match in uses_matches:
            if match.group("ref") != expected_sha:
                drifts.append(
                    Drift(
                        path=workflow.example,
                        message=f"{workflow.reusable} pins {match.group('ref')}, expected {expected_sha}",
                    )
                )

    reusable_path = repo_root / workflow.reusable
    if not reusable_path.exists():
        drifts.append(
            Drift(
                path=Path(workflow.reusable),
                message="manifest reusable workflow path does not exist",
            )
        )
        return drifts

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
    try:
        reusable_default = read_reusable_timeout_default(repo_root, workflow)
    except ValueError as exc:
        drifts.append(Drift(path=Path(workflow.reusable), message=str(exc)))
    else:
        if reusable_default != workflow.timeout_default:
            drifts.append(
                Drift(
                    path=Path(workflow.reusable),
                    message=f"timeout_minutes default is {reusable_default}, expected manifest {workflow.timeout_default}",
                )
            )
    return drifts


def check_readme_snippets(
    repo_root: Path,
    manifest: CallerManifest,
    workflow: CallerWorkflow,
    expected_sha: str,
) -> list[Drift]:
    text = (repo_root / README_PATH).read_text(encoding="utf-8")
    drifts: list[Drift] = []
    matches = tuple(_uses_pattern(workflow.reusable, manifest).finditer(text))
    if not matches:
        drifts.append(
            Drift(
                path=README_PATH,
                message=f"README missing release-lane snippet for {workflow.reusable}",
            )
        )
        return drifts
    for match in matches:
        if match.group("ref") != expected_sha:
            drifts.append(
                Drift(
                    path=README_PATH,
                    message=f"README {workflow.reusable} pins {match.group('ref')}, expected {expected_sha}",
                )
            )
    return drifts


def read_reusable_timeout_default(repo_root: Path, workflow: CallerWorkflow) -> str:
    text = (repo_root / workflow.reusable).read_text(encoding="utf-8")
    match = re.search(
        r"(?m)^      timeout_minutes:\n(?:^        .+\n)*?^        default:\s*[\"']?(?P<value>[^\"'\n]+)[\"']?$",
        text,
    )
    if match is None:
        msg = f"{workflow.reusable} missing timeout_minutes default"
        raise ValueError(msg)
    return match.group("value")


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
    for relative_path, text in render_workspace(
        repo_root, expected_sha, manifest
    ).items():
        (repo_root / relative_path).write_text(text, encoding="utf-8")
    (repo_root / README_PATH).write_text(
        render_readme(
            (repo_root / README_PATH).read_text(encoding="utf-8"),
            expected_sha,
            manifest,
        ),
        encoding="utf-8",
    )
    write_manifest_expected_sha(repo_root, expected_sha)


def write_manifest_expected_sha(repo_root: Path, expected_sha: str) -> None:
    manifest_path = repo_root / MANIFEST_PATH
    text = manifest_path.read_text(encoding="utf-8")
    rendered = re.sub(
        r"(?m)^(default_expected_sha:\s*)[0-9a-f]{40}$",
        rf"\g<1>{expected_sha}",
        text,
        count=1,
    )
    if rendered == text and f"default_expected_sha: {expected_sha}" not in text:
        msg = f"{MANIFEST_PATH} missing default_expected_sha"
        raise ValueError(msg)
    manifest_path.write_text(rendered, encoding="utf-8")


def render_example(
    text: str,
    workflow: CallerWorkflow,
    manifest: CallerManifest,
    expected_sha: str,
) -> str:
    text = _replace_release_lane_comment(text)
    text = _replace_uses_line(text, workflow.reusable, manifest, expected_sha)
    return _replace_timeout_default(text, workflow)


def render_readme(text: str, expected_sha: str, manifest: CallerManifest) -> str:
    for workflow in manifest.workflows:
        text = _replace_uses_line(text, workflow.reusable, manifest, expected_sha)
    return text


def _replace_release_lane_comment(text: str) -> str:
    old = (
        "# Renovate keeps this SHA current; the trailing `# main` comment is the branch\n"
        '    # Renovate tracks. See README "Security" for the full rationale.'
    )
    new = (
        "# This example's release-lane SHA is rendered from examples/caller-workflows/manifest.yaml.\n"
        '    # Consumer repos keep the copied SHA current with the Renovate preset in README "Security".'
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
        rf"(?m)^(?P<prefix>[ \t]*uses:\s+{escaped}@)(?P<ref>[0-9a-f]{{40}})(?P<suffix>\s+#\s+{re.escape(manifest.tracked_ref)}[ \t]*)$"
    )


def _timeout_pattern(workflow: CallerWorkflow) -> re.Pattern[str]:
    return re.compile(
        rf"(?m)^(?P<prefix>[ \t]*timeout_minutes:\s+\$\{{\{{\s*vars\.{re.escape(workflow.timeout_var)}\s+\|\|\s+')(?P<value>[^']+)(?P<suffix>'\s*\}}\}})"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("--repo-root", type=Path)
    expected = parser.add_mutually_exclusive_group()
    expected.add_argument("--expected-sha")
    expected.add_argument("--expected-ref")
    args = parser.parse_args(argv)

    repo_root = args.repo_root or find_repo_root(Path.cwd())
    manifest = load_manifest(repo_root)
    expected_sha = (
        args.expected_sha
        if args.expected_sha is not None
        else manifest.default_expected_sha
    )
    if args.expected_ref:
        expected_sha = resolve_git_sha(args.expected_ref, repo_root)
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
            "Run `python3 -m gh_actions.check_caller_workflows --write` to refresh generated caller refs.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
