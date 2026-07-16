"""Extract and classify spec-tree review-gate findings from pull-request comments.

The spec-tree review gate posts each review as a bot pull-request comment whose
body holds zero or more `### SEVERITY [concern]: location` finding entries. This
module fetches those comments, parses each finding into a record, and summarises
the set by severity, concern, cited-path kind, and pull request.

It records whatever severity and concern labels a finding comment carries; the
governed review taxonomy lives in the plugins spec tree
(`plugins/spx/21-spec-tree.enabler/68-reviewing.enabler/reviewing.md`) and is
cross-referenced, never restated or validated against here.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Final

# The reviewer's login as the REST API reports it. `fetch_pr_comments` reads
# `repos/{repo}/issues/{pr}/comments`, and REST names a GitHub App author in
# `user.login` *with* the `[bot]` suffix. GraphQL (`gh pr view --json comments`)
# names the same actor `claude`, *without* the suffix — so a login sampled from
# GraphQL does not match what this module filters on, and substituting it here
# silently yields zero findings against real data.
# `gh_actions_testing/fixtures/rest_comment.json` is a real captured REST payload
# carrying this suffixed login; the scenario lane runs `build()` over it with this
# default, so the two cannot drift apart unnoticed.
DEFAULT_REVIEWER: Final = "claude[bot]"

# A finding header: "### SEVERITY [concern]: location" (2-4 leading hashes seen in
# the wild). The shape is read off the reviewer's emitted output; no contract is
# shared with the prompt that writes it, which lives in the spec tree the module
# docstring cross-references. Should that prompt's wording, hash count, or field
# labels drift, a comment parses to no findings rather than raising.
HEADER_RE: Final = re.compile(
    r"^#{2,4}\s+([A-Z][A-Z-]+)\s+\[([a-z][a-z-]*)\]\s*:\s*(.*)$"
)

# Labelled body fields a finding entry may carry. BLOCKING/DEBT entries use
# Evidence/Required; a FOLLOW-UP entry uses Issue/Track under.
FIELD_LABELS: Final = (
    "Reference",
    "Evidence",
    "Required",
    "Issue",
    "Track under",
    "Track",
)
FIELD_RE: Final = re.compile(
    r"^(%s)\s*:\s*(.*)$" % "|".join(re.escape(x) for x in FIELD_LABELS)
)

NO_FINDINGS_RE: Final = re.compile(r"^\s*no findings\b", re.IGNORECASE)

# A language's test-infrastructure home, which holds harnesses, generators, and
# inert fixtures: `testing/` at the root for TypeScript, `<package>_testing/` for
# Python (this repository's own `gh_actions_testing/`, per
# `spx/15-evidence-model.adr.md`).
TEST_HOME_RE: Final = re.compile(r"^(testing|[A-Za-z_][A-Za-z0-9_]*_testing)/")

# A trailing "path:line" or "path:line-range" on a location string. A reviewer
# cites `path/to/file:42` — the only line-bearing shape the review format emits,
# across every finding on outcomeeng/spx#366 and #137. A lint-tool `path:line:col`
# location is not part of that format and is deliberately not parsed as one.
LOC_LINE_RE: Final = re.compile(
    r"^(?P<file>[^\s`]+?):(?P<line>\d+(?:[-,]\d+)*)(?:\s|$)"
)
LOC_FILE_RE: Final = re.compile(r"^(?P<file>[^\s`]+)")


class PathKind(StrEnum):
    """Artifact kind a finding's cited path resolves to."""

    DECISION_ADR = "decision-adr"
    DECISION_PDR = "decision-pdr"
    TEST = "test"
    SPEC = "spec"
    CODE = "code"
    SPEC_TREE_OTHER = "spec-tree-other"
    OTHER = "other"


@dataclass(frozen=True)
class Finding:
    """One parsed finding entry, with the pull-request context build() fills in."""

    severity: str
    concern: str
    location_raw: str
    file: str | None
    line: str | None
    path_kind: PathKind | None
    fields: dict[str, str]
    raw: str
    pr: int | None = None
    comment_id: int | None = None
    url: str | None = None
    created_at: str | None = None


@dataclass(frozen=True)
class Comment:
    """One pull-request issue comment — the input the extractor parses."""

    id: int
    created_at: str
    url: str
    login: str
    body: str


def classify_path(path: str) -> PathKind:
    """Bucket a cited path by artifact kind, heuristically, from spec-tree path
    conventions: `.adr.md`/`.pdr.md` decisions, `spx/` specs and tree paths,
    `/tests/`|`.test.` tests alongside a language's test-infrastructure home
    (`TEST_HOME_RE`), and a `src/` or `gh_actions/` code root (`src/` for most
    spec-tree products, `gh_actions/` for this repository per
    `spx/15-evidence-model.adr.md`). Code laid out under any other root falls to
    OTHER.
    """
    p = path.strip("`")
    if p.endswith(".adr.md"):
        return PathKind.DECISION_ADR
    if p.endswith(".pdr.md"):
        return PathKind.DECISION_PDR
    if ".test." in p or "/tests/" in p or TEST_HOME_RE.match(p):
        return PathKind.TEST
    if p.endswith(".md") and p.startswith("spx/"):
        return PathKind.SPEC
    if p.startswith("src/") or p.startswith("gh_actions/"):
        return PathKind.CODE
    if p.startswith("spx/"):
        return PathKind.SPEC_TREE_OTHER
    return PathKind.OTHER


def parse_location(raw: str) -> tuple[str | None, str | None]:
    """Split a location string into (file, line); line may be a range or None."""
    loc = raw.strip().lstrip("`").strip()
    if not loc:
        return None, None
    m = LOC_LINE_RE.match(loc)
    if m:
        return m.group("file").rstrip("`,;."), m.group("line")
    m = LOC_FILE_RE.match(loc)
    assert m is not None  # loc is non-empty and opens with neither space nor backtick
    return m.group("file").rstrip("`,;."), None


def parse_fields(block_lines: list[str]) -> dict[str, str]:
    """Collect labelled fields from a finding block, preserving multi-line values."""
    fields: dict[str, list[str]] = {}
    current: str | None = None
    for line in block_lines:
        m = FIELD_RE.match(line)
        if m:
            current = m.group(1).lower().replace(" ", "_")
            fields[current] = [m.group(2)]
        elif current is not None:
            fields[current].append(line)
    return {k: "\n".join(v).strip() for k, v in fields.items()}


def build_finding(
    severity: str, concern: str, loc_raw: str, block_lines: list[str], raw: str
) -> Finding:
    """Assemble one finding record from its header parts, body lines, and raw text."""
    file_, line_ = parse_location(loc_raw)
    return Finding(
        severity=severity.strip().lower(),
        concern=concern.strip().lower(),
        location_raw=loc_raw.strip(),
        file=file_,
        line=line_,
        path_kind=classify_path(file_) if file_ else None,
        fields=parse_fields(block_lines),
        raw=raw,
    )


def parse_comment(body: str) -> tuple[list[Finding], bool]:
    """Parse one comment body into (findings, is_clean_review).

    A comment with no finding headers is a clean review only when it opens with
    "No findings"; otherwise it carries no review findings at all.
    """
    lines = body.replace("\r\n", "\n").split("\n")
    header_idx = [i for i, ln in enumerate(lines) if HEADER_RE.match(ln)]
    if not header_idx:
        return [], bool(NO_FINDINGS_RE.match(body))

    findings: list[Finding] = []
    for n, start in enumerate(header_idx):
        end = header_idx[n + 1] if n + 1 < len(header_idx) else len(lines)
        m = HEADER_RE.match(lines[start])
        assert m is not None  # start came from HEADER_RE above
        findings.append(
            build_finding(
                m.group(1),
                m.group(2),
                m.group(3),
                lines[start + 1 : end],
                raw="\n".join(lines[start:end]).strip(),
            )
        )
    return findings, False


def classify(findings: list[Finding], clean_review_passes: int) -> dict:
    """Summarise findings by severity, concern, cited-path kind, and pull request."""
    by_sev = Counter(f.severity for f in findings)
    by_concern = Counter(f.concern for f in findings)
    by_kind = Counter((f.path_kind or "unknown") for f in findings)

    by_sev_concern: dict[str, Counter] = defaultdict(Counter)
    by_pr: dict[int, Counter] = defaultdict(Counter)
    for f in findings:
        by_sev_concern[f.severity][f.concern] += 1
        if f.pr is not None:
            by_pr[f.pr][f.severity] += 1

    return {
        "total_findings": len(findings),
        "clean_review_passes": clean_review_passes,
        "by_severity": dict(by_sev.most_common()),
        "by_concern": dict(by_concern.most_common()),
        "by_severity_and_concern": {
            k: dict(v.most_common()) for k, v in by_sev_concern.items()
        },
        "by_path_kind": {str(k): n for k, n in by_kind.most_common()},
        "by_pr": {str(k): dict(v.most_common()) for k, v in by_pr.items()},
    }


# Injectable fetcher signature so build() runs against fixtures in tests.
Fetcher = Callable[[str, int], list[Comment]]


def comment_from_api(raw: dict) -> Comment:
    """Map one REST issue-comment object onto a `Comment`.

    `login` comes from `user.login`, which REST reports with the `[bot]` suffix for
    a GitHub App author — see `DEFAULT_REVIEWER`.
    """
    return Comment(
        id=raw["id"],
        created_at=raw["created_at"],
        url=raw["html_url"],
        login=raw["user"]["login"],
        body=raw["body"] or "",
    )


def fetch_pr_comments(repo: str, pr: int) -> list[Comment]:
    """Fetch a pull request's issue comments through the gh CLI.

    The gh invocation is spelled out here rather than shared with `run_gh` in
    `gh_actions/push_secrets.py`: that module is a self-contained `uv run` script
    (PEP 723), which resolves no sibling package module when invoked by path, so
    importing across the two would break its documented standalone usage.
    """
    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{repo}/issues/{pr}/comments",
            "--paginate",
            "--jq",
            ".[]",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return [
        comment_from_api(json.loads(line))
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def build(
    repo: str,
    prs: list[int],
    reviewer: str = DEFAULT_REVIEWER,
    fetch: Fetcher = fetch_pr_comments,
) -> dict:
    """Extract and classify every `reviewer` finding across `prs` in `repo`."""
    findings: list[Finding] = []
    clean_reviews: list[dict] = []
    for pr in prs:
        for comment in fetch(repo, pr):
            if comment.login != reviewer:
                continue
            parsed, is_clean = parse_comment(comment.body)
            context = {
                "pr": pr,
                "comment_id": comment.id,
                "url": comment.url,
                "created_at": comment.created_at,
            }
            if is_clean and not parsed:
                clean_reviews.append(dict(context))
            findings.extend(replace(f, **context) for f in parsed)
    return {
        "meta": {"repo": repo, "reviewer": reviewer, "prs": prs},
        "findings": [asdict(f) for f in findings],
        "clean_reviews": clean_reviews,
        "classification": classify(findings, len(clean_reviews)),
    }


def main(argv: list[str] | None = None, fetch: Fetcher = fetch_pr_comments) -> int:
    """Extract findings from the given pull requests and emit a JSON report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prs", nargs="+", type=int, help="pull-request numbers")
    parser.add_argument("--repo", required=True, help="owner/name of the repository")
    parser.add_argument(
        "--reviewer", default=DEFAULT_REVIEWER, help="reviewer login to extract"
    )
    parser.add_argument("--out", type=Path, help="write JSON here instead of stdout")
    args = parser.parse_args(argv)

    report = build(args.repo, args.prs, args.reviewer, fetch=fetch)
    text = json.dumps(report, indent=2)
    if args.out is not None:
        args.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
