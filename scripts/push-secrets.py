#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Push GitHub secrets to the current repository.

Usage:
    uv run scripts/push-secrets.py check
    uv run scripts/push-secrets.py push
    uv run scripts/push-secrets.py push --dry-run
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from collections.abc import Sequence

SECRET_NAME = "CLAUDE_CODE_OAUTH_TOKEN"
SECRET_DESCRIPTION = "OAuth token for Claude Code GitHub Action"
KEYCHAIN_SERVICE = "Claude Code-credentials"
KEYCHAIN_JSON_PATH = "claudeAiOauth.accessToken"
GH_ACTIONS_URL = "https://github.com/outcomeeng/gh-actions"
WORKFLOW_DIR = Path(".github") / "workflows"
WORKFLOW_PATTERNS = ("*.yml", "*.yaml")
CLAUDE_WORKFLOW_MARKERS = (
    SECRET_NAME,
    "anthropics/claude-code-action",
    "outcomeeng/gh-actions/.github/workflows/claude",
)
GITHUB_HOST = "github.com"
GIT_REMOTE_PREFIX = "git@github.com:"
GIT_SUFFIX = ".git"


@dataclass
class CurrentRepo:
    """Current GitHub repository context."""

    root: Path
    name: str


def run_git(
    args: Sequence[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a git command."""
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def current_repo() -> CurrentRepo | None:
    """Resolve the current GitHub repository from git."""
    root_result = run_git(["rev-parse", "--show-toplevel"], check=False)
    if root_result.returncode != 0:
        return None

    root = Path(root_result.stdout.strip())
    remote_result = run_git(
        ["config", "--get", "remote.origin.url"],
        cwd=root,
        check=False,
    )
    if remote_result.returncode != 0:
        return None

    repo_name = parse_github_remote(remote_result.stdout.strip())
    if not repo_name:
        return None

    return CurrentRepo(root=root, name=repo_name)


def parse_github_remote(remote_url: str) -> str | None:
    """Parse a GitHub remote URL into owner/name form."""
    if remote_url.startswith(GIT_REMOTE_PREFIX):
        path = remote_url.removeprefix(GIT_REMOTE_PREFIX)
    else:
        parsed = urlparse(remote_url)
        if parsed.hostname != GITHUB_HOST:
            return None
        path = parsed.path.lstrip("/")

    if path.endswith(GIT_SUFFIX):
        path = path[: -len(GIT_SUFFIX)]

    parts = path.split("/")
    if len(parts) != 2 or not all(parts):
        return None

    return f"{parts[0]}/{parts[1]}"


def has_claude_workflow(repo: CurrentRepo) -> bool:
    """Return whether the current repo has a Claude workflow installed."""
    workflow_dir = repo.root / WORKFLOW_DIR
    for pattern in WORKFLOW_PATTERNS:
        for workflow_path in workflow_dir.glob(pattern):
            content = workflow_path.read_text(encoding="utf-8")
            if any(marker in content for marker in CLAUDE_WORKFLOW_MARKERS):
                return True
    return False


def require_current_repo() -> CurrentRepo | None:
    """Print a helpful error unless the current GitHub repo is usable."""
    repo = current_repo()
    if not repo:
        print("Error: Run this command from a GitHub repository with an origin remote.")
        return None

    if not has_claude_workflow(repo):
        print(f"Error: {repo.name} does not have the Claude workflow installed.")
        print(f"Install it from {GH_ACTIONS_URL}, then run this command again.")
        return None

    return repo


def get_from_keychain() -> str | None:
    """Get a secret value from macOS Keychain.

    Returns the value if found, None otherwise.
    """
    if sys.platform != "darwin":
        return None

    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s", KEYCHAIN_SERVICE,
                "-a", os.environ.get("USER", ""),
                "-w",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        value = result.stdout.strip()

        if KEYCHAIN_JSON_PATH and value:
            data = json.loads(value)
            for key in KEYCHAIN_JSON_PATH.split("."):
                data = data[key]
            return str(data)

        return value
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
        return None


def run_gh(
    args: Sequence[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a gh CLI command."""
    return subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=check,
    )


def secret_exists(repo: str, name: str) -> bool:
    """Check if a secret exists in a repository."""
    result = run_gh(["secret", "list", "--repo", repo], check=False)
    if result.returncode != 0:
        return False
    # Each line is: NAME\tUpdated ...\n
    for line in result.stdout.splitlines():
        if line.split("\t")[0] == name:
            return True
    return False


def set_secret(repo: str, name: str, value: str, *, dry_run: bool = False) -> bool:
    """Set a secret in a repository."""
    if dry_run:
        print(f"  [dry-run] Would set {name} in {repo}")
        return True

    result = run_gh(
        ["secret", "set", name, "--repo", repo, "--body", value],
        check=False,
    )
    if result.returncode != 0:
        print(f"  ✗ Failed to set {name} in {repo}: {result.stderr.strip()}")
        return False
    print(f"  ✓ Set {name} in {repo}")
    return True


def cmd_check(_args: argparse.Namespace) -> int:
    """Check secret status in the current repository."""
    repo = require_current_repo()
    if not repo:
        return 1

    print(f"\n{repo.name}")
    exists = secret_exists(repo.name, SECRET_NAME)
    status = "✓ set" if exists else "✗ missing"
    print(f"  {status} {SECRET_NAME}")
    print(f"    {SECRET_DESCRIPTION}")

    return 0


def cmd_push(args: argparse.Namespace) -> int:
    """Push secrets to the current repository."""
    repo = require_current_repo()
    if not repo:
        return 1

    value = ""
    if not args.dry_run:
        value = get_from_keychain() or ""
        if value:
            print(f"  ✓ Got {SECRET_NAME} from keychain")

        if not value:
            if sys.stdin.isatty():
                value = getpass.getpass(f"Enter value for {SECRET_NAME}: ")
            else:
                value = sys.stdin.readline().strip()

        if not value:
            print(f"Error: Empty value for {SECRET_NAME}")
            return 1

    print(f"\nPushing secrets to {repo.name}...")
    if args.dry_run:
        set_secret(repo.name, SECRET_NAME, "", dry_run=True)
    elif not set_secret(repo.name, SECRET_NAME, value):
        return 1

    print("\nDone.")
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Push GitHub secrets to the current repository"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Check secret status")
    check_parser.set_defaults(func=cmd_check)

    push_parser = subparsers.add_parser("push", help="Push secrets")
    push_parser.add_argument(
        "--dry-run", action="store_true", help="Preview without making changes"
    )
    push_parser.set_defaults(func=cmd_push)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
