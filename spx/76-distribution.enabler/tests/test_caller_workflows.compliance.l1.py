from pathlib import Path
import subprocess

import pytest

from gh_actions import caller_workflows


EXPECTED_SHA = "a" * 40
OTHER_SHA = "b" * 40


def test_caller_workflow_outputs_match_manifest() -> None:
    assert caller_workflows.check_default_workspace() == []


def test_drift_reports_mismatched_sha_and_timeout(tmp_path: Path) -> None:
    workflow = _workflow()
    _write_reusable(tmp_path, workflow)
    (tmp_path / workflow.example).write_text(
        "\n".join(
            [
                "jobs:",
                "  call:",
                f"    uses: outcomeeng/gh-actions/{workflow.reusable}@{OTHER_SHA} # main",
                "    with:",
                "      timeout_minutes: ${{ vars.TEST_TIMEOUT || '10' }}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    drifts = caller_workflows.check_example(
        tmp_path, _manifest(workflow), workflow, EXPECTED_SHA
    )

    assert drifts == [
        caller_workflows.Drift(
            path=workflow.example,
            message=f"{workflow.reusable} pins {OTHER_SHA}, expected {EXPECTED_SHA}",
        ),
        caller_workflows.Drift(
            path=workflow.example,
            message="vars.TEST_TIMEOUT defaults to 10, expected 15",
        ),
    ]


def test_drift_ignores_commented_uses_lines(tmp_path: Path) -> None:
    workflow = _workflow()
    _write_reusable(tmp_path, workflow)
    (tmp_path / workflow.example).write_text(
        "\n".join(
            [
                f"    # uses: outcomeeng/gh-actions/{workflow.reusable}@{EXPECTED_SHA} # main",
                f"    uses: outcomeeng/gh-actions/{workflow.reusable}@{OTHER_SHA} # main",
                "    timeout_minutes: ${{ vars.TEST_TIMEOUT || '15' }}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    drifts = caller_workflows.check_example(
        tmp_path, _manifest(workflow), workflow, EXPECTED_SHA
    )

    assert drifts == [
        caller_workflows.Drift(
            path=workflow.example,
            message=f"{workflow.reusable} pins {OTHER_SHA}, expected {EXPECTED_SHA}",
        )
    ]


def test_drift_reports_each_stale_executable_uses_line(tmp_path: Path) -> None:
    workflow = _workflow()
    _write_reusable(tmp_path, workflow)
    (tmp_path / workflow.example).write_text(
        "\n".join(
            [
                "jobs:",
                "  first:",
                f"    uses: outcomeeng/gh-actions/{workflow.reusable}@{OTHER_SHA} # main",
                "    with:",
                "      timeout_minutes: ${{ vars.TEST_TIMEOUT || '15' }}",
                "  second:",
                f"    uses: outcomeeng/gh-actions/{workflow.reusable}@{OTHER_SHA} # main",
                "",
            ]
        ),
        encoding="utf-8",
    )

    drifts = caller_workflows.check_example(
        tmp_path, _manifest(workflow), workflow, EXPECTED_SHA
    )

    assert drifts == [
        caller_workflows.Drift(
            path=workflow.example,
            message=f"{workflow.reusable} pins {OTHER_SHA}, expected {EXPECTED_SHA}",
        ),
        caller_workflows.Drift(
            path=workflow.example,
            message=f"{workflow.reusable} pins {OTHER_SHA}, expected {EXPECTED_SHA}",
        ),
    ]


def test_drift_rejects_tracked_ref_comment_prefix_match(tmp_path: Path) -> None:
    workflow = _workflow()
    _write_reusable(tmp_path, workflow)
    (tmp_path / workflow.example).write_text(
        "\n".join(
            [
                "jobs:",
                "  call:",
                f"    uses: outcomeeng/gh-actions/{workflow.reusable}@{EXPECTED_SHA} # maintainer note",
                "    with:",
                "      timeout_minutes: ${{ vars.TEST_TIMEOUT || '15' }}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    drifts = caller_workflows.check_example(
        tmp_path, _manifest(workflow), workflow, EXPECTED_SHA
    )

    assert drifts == [
        caller_workflows.Drift(
            path=workflow.example,
            message=f"missing release-lane uses line for {workflow.reusable}",
        )
    ]


def test_drift_reports_missing_uses_and_timeout(tmp_path: Path) -> None:
    workflow = _workflow()
    _write_reusable(tmp_path, workflow)
    (tmp_path / workflow.example).write_text(
        "jobs:\n  noop:\n    runs-on: ubuntu-latest\n", encoding="utf-8"
    )

    drifts = caller_workflows.check_example(
        tmp_path, _manifest(workflow), workflow, EXPECTED_SHA
    )

    assert drifts == [
        caller_workflows.Drift(
            path=workflow.example,
            message=f"missing release-lane uses line for {workflow.reusable}",
        ),
        caller_workflows.Drift(
            path=workflow.example,
            message="missing timeout default for vars.TEST_TIMEOUT",
        ),
    ]


def test_workspace_reports_manifest_entry_missing_reusable_file(
    tmp_path: Path,
) -> None:
    workflow = _workflow(Path("examples/caller-workflows/example.yml"))
    _write_workspace_fixture(tmp_path, workflow, EXPECTED_SHA, write_reusable=False)
    _write_readme(tmp_path, workflow, EXPECTED_SHA)

    assert caller_workflows.check_workspace(tmp_path, EXPECTED_SHA) == [
        caller_workflows.Drift(
            path=Path(workflow.reusable),
            message="manifest reusable workflow path does not exist",
        )
    ]


def test_workspace_reports_reusable_workflow_missing_manifest_entry(
    tmp_path: Path,
) -> None:
    workflow = _workflow(Path("examples/caller-workflows/example.yml"))
    _write_workspace_fixture(tmp_path, workflow, EXPECTED_SHA)
    _write_readme(tmp_path, workflow, EXPECTED_SHA)
    extra_reusable = Path(".github/workflows/extra.yml")
    _write_workflow_call(tmp_path / extra_reusable)

    assert caller_workflows.check_workspace(tmp_path, EXPECTED_SHA) == [
        caller_workflows.Drift(
            path=extra_reusable,
            message="reusable workflow is not declared in manifest",
        )
    ]


def test_workspace_reports_manifest_reusable_without_workflow_call(
    tmp_path: Path,
) -> None:
    workflow = _workflow(Path("examples/caller-workflows/example.yml"))
    _write_workspace_fixture(tmp_path, workflow, EXPECTED_SHA)
    _write_readme(tmp_path, workflow, EXPECTED_SHA)
    (tmp_path / workflow.reusable).write_text(
        "name: ordinary workflow\n", encoding="utf-8"
    )

    assert caller_workflows.check_workspace(tmp_path, EXPECTED_SHA) == [
        caller_workflows.Drift(
            path=Path(workflow.reusable),
            message="manifest reusable workflow path does not declare workflow_call",
        ),
        caller_workflows.Drift(
            path=Path(workflow.reusable),
            message=f"{workflow.reusable} missing timeout_minutes default",
        ),
    ]


def test_manifest_parser_rejects_invalid_yaml() -> None:
    with pytest.raises(ValueError, match="invalid YAML"):
        caller_workflows._parse_manifest("workflows: [")


def test_resolve_git_sha_returns_full_sha(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)

    sha = caller_workflows.resolve_git_sha("HEAD", tmp_path)

    assert caller_workflows.FULL_SHA_RE.fullmatch(sha)


def test_resolve_git_sha_rejects_non_sha_output(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)

    with pytest.raises(ValueError, match="resolved to non-SHA value"):
        caller_workflows.resolve_git_sha("--show-toplevel", tmp_path)


def test_main_checks_workspace_with_expected_ref_and_repo_root(
    tmp_path: Path,
) -> None:
    head_sha = _init_git_repo(tmp_path)
    workflow = _workflow(Path("examples/caller-workflows/example.yml"))
    _write_workspace_fixture(tmp_path, workflow, head_sha)
    _write_readme(tmp_path, workflow, head_sha)

    result = caller_workflows.main(
        ["--check", "--repo-root", str(tmp_path), "--expected-ref", "HEAD"]
    )

    assert result == 0


def test_main_rejects_conflicting_expected_sha_and_ref(
    tmp_path: Path,
) -> None:
    _init_git_repo(tmp_path)

    with pytest.raises(SystemExit):
        caller_workflows.main(
            [
                "--check",
                "--repo-root",
                str(tmp_path),
                "--expected-sha",
                EXPECTED_SHA,
                "--expected-ref",
                "HEAD",
            ]
        )


def test_main_rejects_empty_expected_sha(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    workflow = _workflow(Path("examples/caller-workflows/example.yml"))
    _write_workspace_fixture(tmp_path, workflow, EXPECTED_SHA)
    _write_readme(tmp_path, workflow, EXPECTED_SHA)

    with pytest.raises(SystemExit):
        caller_workflows.main(
            ["--check", "--repo-root", str(tmp_path), "--expected-sha", ""]
        )


def test_workspace_reports_extra_example_file(tmp_path: Path) -> None:
    workflow = _workflow(Path("examples/caller-workflows/example.yml"))
    examples_dir = tmp_path / "examples" / "caller-workflows"
    examples_dir.mkdir(parents=True)
    (tmp_path / workflow.example).write_text(
        _example_text(workflow, EXPECTED_SHA), encoding="utf-8"
    )
    extra = Path("examples/caller-workflows/extra.yml")
    (tmp_path / extra).write_text(
        _example_text(workflow, EXPECTED_SHA), encoding="utf-8"
    )
    (examples_dir / "manifest.yaml").write_text(
        _manifest_text(workflow), encoding="utf-8"
    )
    _write_reusable(tmp_path, workflow)
    _write_readme(tmp_path, workflow, EXPECTED_SHA)

    assert caller_workflows.check_workspace(tmp_path, EXPECTED_SHA) == [
        caller_workflows.Drift(
            path=extra,
            message="caller workflow example is not declared in manifest",
        )
    ]


def test_workspace_reports_extra_yaml_example_file(tmp_path: Path) -> None:
    workflow = _workflow(Path("examples/caller-workflows/example.yml"))
    examples_dir = tmp_path / "examples" / "caller-workflows"
    examples_dir.mkdir(parents=True)
    (tmp_path / workflow.example).write_text(
        _example_text(workflow, EXPECTED_SHA), encoding="utf-8"
    )
    extra = Path("examples/caller-workflows/extra.yaml")
    (tmp_path / extra).write_text(
        _example_text(workflow, EXPECTED_SHA), encoding="utf-8"
    )
    (examples_dir / "manifest.yaml").write_text(
        _manifest_text(workflow), encoding="utf-8"
    )
    _write_reusable(tmp_path, workflow)
    _write_readme(tmp_path, workflow, EXPECTED_SHA)

    assert caller_workflows.check_workspace(tmp_path, EXPECTED_SHA) == [
        caller_workflows.Drift(
            path=extra,
            message="caller workflow example is not declared in manifest",
        )
    ]


def test_workspace_reports_manifest_entry_missing_example_file(tmp_path: Path) -> None:
    workflow = _workflow(Path("examples/caller-workflows/example.yml"))
    examples_dir = tmp_path / "examples" / "caller-workflows"
    examples_dir.mkdir(parents=True)
    (examples_dir / "manifest.yaml").write_text(
        _manifest_text(workflow), encoding="utf-8"
    )
    _write_readme(tmp_path, workflow, EXPECTED_SHA)
    _write_reusable(tmp_path, workflow)

    assert caller_workflows.check_workspace(tmp_path, EXPECTED_SHA) == [
        caller_workflows.Drift(
            path=workflow.example,
            message="manifest declares missing caller workflow example",
        )
    ]


def test_workspace_reports_stale_readme_snippet(tmp_path: Path) -> None:
    workflow = _workflow(Path("examples/caller-workflows/example.yml"))
    _write_workspace_fixture(tmp_path, workflow, EXPECTED_SHA)
    _write_readme(tmp_path, workflow, OTHER_SHA)

    assert caller_workflows.check_workspace(tmp_path, EXPECTED_SHA) == [
        caller_workflows.Drift(
            path=caller_workflows.README_PATH,
            message=f"README {workflow.reusable} pins {OTHER_SHA}, expected {EXPECTED_SHA}",
        )
    ]


def test_workspace_reports_missing_readme_snippet(tmp_path: Path) -> None:
    workflow = _workflow(Path("examples/caller-workflows/example.yml"))
    _write_workspace_fixture(tmp_path, workflow, EXPECTED_SHA)
    (tmp_path / caller_workflows.README_PATH).write_text("", encoding="utf-8")

    assert caller_workflows.check_workspace(tmp_path, EXPECTED_SHA) == [
        caller_workflows.Drift(
            path=caller_workflows.README_PATH,
            message=f"README missing release-lane snippet for {workflow.reusable}",
        )
    ]


def test_workspace_reports_reusable_timeout_default_drift(tmp_path: Path) -> None:
    workflow = _workflow(Path("examples/caller-workflows/example.yml"))
    _write_workspace_fixture(tmp_path, workflow, EXPECTED_SHA, reusable_timeout="20")
    _write_readme(tmp_path, workflow, EXPECTED_SHA)

    assert caller_workflows.check_workspace(tmp_path, EXPECTED_SHA) == [
        caller_workflows.Drift(
            path=Path(workflow.reusable),
            message="timeout_minutes default is 20, expected manifest 15",
        )
    ]


def test_write_workspace_updates_examples_and_manifest(tmp_path: Path) -> None:
    workflow = _workflow(Path("examples/caller-workflows/example.yml"))
    examples_dir = _write_workspace_fixture(tmp_path, workflow, EXPECTED_SHA)
    _write_readme(tmp_path, workflow, EXPECTED_SHA)

    caller_workflows.write_workspace(tmp_path, OTHER_SHA)

    assert caller_workflows.check_workspace(tmp_path, OTHER_SHA) == []
    assert f"default_expected_sha: {OTHER_SHA}" in (
        examples_dir / "manifest.yaml"
    ).read_text(encoding="utf-8")
    assert f"@{OTHER_SHA} # main" in (tmp_path / workflow.example).read_text(
        encoding="utf-8"
    )
    assert f"@{OTHER_SHA} # main" in (
        tmp_path / caller_workflows.README_PATH
    ).read_text(encoding="utf-8")


def _workflow(example: Path = Path("example.yml")) -> caller_workflows.CallerWorkflow:
    return caller_workflows.CallerWorkflow(
        id="test",
        example=example,
        reusable=".github/workflows/test.yml",
        timeout_var="TEST_TIMEOUT",
        timeout_default="15",
    )


def _manifest(
    workflow: caller_workflows.CallerWorkflow,
) -> caller_workflows.CallerManifest:
    return caller_workflows.CallerManifest(
        repository="outcomeeng/gh-actions",
        tracked_ref="main",
        default_expected_sha=EXPECTED_SHA,
        workflows=(workflow,),
    )


def _example_text(workflow: caller_workflows.CallerWorkflow, sha: str) -> str:
    return "\n".join(
        [
            "jobs:",
            "  call:",
            f"    uses: outcomeeng/gh-actions/{workflow.reusable}@{sha} # main",
            "    with:",
            "      timeout_minutes: ${{ vars.TEST_TIMEOUT || '15' }}",
            "",
        ]
    )


def _manifest_text(workflow: caller_workflows.CallerWorkflow) -> str:
    return "\n".join(
        [
            "schema_version: 1",
            "repository: outcomeeng/gh-actions",
            "tracked_ref: main",
            f"default_expected_sha: {EXPECTED_SHA}",
            "workflows:",
            f"  - id: {workflow.id}",
            f"    example: {workflow.example}",
            f"    reusable: {workflow.reusable}",
            f"    timeout_var: {workflow.timeout_var}",
            f'    timeout_default: "{workflow.timeout_default}"',
            "",
        ]
    )


def _write_workspace_fixture(
    tmp_path: Path,
    workflow: caller_workflows.CallerWorkflow,
    sha: str,
    *,
    reusable_timeout: str = "15",
    write_reusable: bool = True,
) -> Path:
    examples_dir = tmp_path / "examples" / "caller-workflows"
    examples_dir.mkdir(parents=True)
    (tmp_path / workflow.example).write_text(
        _example_text(workflow, sha), encoding="utf-8"
    )
    (examples_dir / "manifest.yaml").write_text(
        _manifest_text(workflow), encoding="utf-8"
    )
    if write_reusable:
        _write_reusable(tmp_path, workflow, reusable_timeout)
    return examples_dir


def _write_reusable(
    tmp_path: Path,
    workflow: caller_workflows.CallerWorkflow,
    reusable_timeout: str = "15",
) -> None:
    reusable_path = tmp_path / workflow.reusable
    _write_workflow_call(reusable_path, reusable_timeout)


def _write_workflow_call(reusable_path: Path, reusable_timeout: str = "15") -> None:
    reusable_path.parent.mkdir(parents=True, exist_ok=True)
    reusable_path.write_text(
        "\n".join(
            [
                "on:",
                "  workflow_call:",
                "    inputs:",
                "      timeout_minutes:",
                "        required: false",
                "        type: string",
                f'        default: "{reusable_timeout}"',
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_readme(
    tmp_path: Path,
    workflow: caller_workflows.CallerWorkflow,
    sha: str,
) -> None:
    (tmp_path / caller_workflows.README_PATH).write_text(
        f"uses: outcomeeng/gh-actions/{workflow.reusable}@{sha} # main\n",
        encoding="utf-8",
    )


def _init_git_repo(tmp_path: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "tests@example.invalid"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Tests"],
        cwd=tmp_path,
        check=True,
    )
    (tmp_path / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "seed.txt"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "test seed"],
        cwd=tmp_path,
        check=True,
    )
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout.strip()
