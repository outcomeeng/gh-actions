"""Scenario evidence: end-to-end extraction over real reviewer comment bodies.

The comment payloads are inert fixture files captured from the spec-tree review
gate's own findings on outcomeeng/spx pull requests, loaded through the
``gh_actions_testing`` review-comments harness.
"""

from __future__ import annotations

import json
from pathlib import Path

from gh_actions.review_findings import (
    DEFAULT_REVIEWER,
    PathKind,
    build,
    main,
    parse_comment,
)
from gh_actions_testing.harnesses.review_comments import (
    api_comment,
    comment_from_fixture,
    fixture_body,
)


def test_finding_comment_parses_into_records() -> None:
    findings, is_clean = parse_comment(fixture_body("blocking_evidence.txt"))
    assert not is_clean
    assert len(findings) == 2
    assert all(f.severity == "blocking" and f.concern == "evidence" for f in findings)
    assert findings[0].file is not None and findings[0].file.endswith(
        "evidence-append.md"
    )
    assert findings[0].line == "11"
    assert findings[0].fields["required"].startswith("Either narrow the assertion")


def test_debt_comment_parses_both_entries_with_their_kinds() -> None:
    findings, is_clean = parse_comment(fixture_body("debt_consistency.txt"))
    assert not is_clean
    assert len(findings) == 2

    assert findings[0].severity == "debt"
    assert findings[0].concern == "consistency"
    assert findings[0].file == "src/domains/verify/verify.ts"
    assert findings[0].line == "351"
    assert findings[0].path_kind is PathKind.CODE

    assert findings[1].severity == "debt"
    assert findings[1].concern == "evidence"
    assert findings[1].file == "testing/generators/verify/verify.ts"
    assert findings[1].line is None
    assert findings[1].path_kind is PathKind.TEST


def test_no_findings_comment_is_a_clean_pass() -> None:
    findings, is_clean = parse_comment(fixture_body("no_findings.txt"))
    assert findings == []
    assert is_clean is True


def test_build_aggregates_counting_only_the_configured_reviewer() -> None:
    comments = {
        7: [
            comment_from_fixture(
                "blocking_evidence.txt", id=1, url="u1", login=DEFAULT_REVIEWER
            ),
            comment_from_fixture(
                "no_findings.txt", id=3, url="u3", login=DEFAULT_REVIEWER
            ),
            comment_from_fixture(
                "blocking_evidence.txt", id=4, url="u4", login="an-author"
            ),
        ],
        9: [
            comment_from_fixture(
                "debt_consistency.txt", id=2, url="u2", login=DEFAULT_REVIEWER
            ),
        ],
    }
    result = build("owner/repo", [7, 9], fetch=lambda _repo, pr: comments[pr])

    classification = result["classification"]
    # PR 7 contributes two blocking/evidence/spec entries; PR 9 two debt entries
    # (consistency/code and evidence/test). The non-reviewer comment on PR 7 and
    # PR 7's clean pass contribute no findings.
    assert classification["total_findings"] == 4
    assert classification["clean_review_passes"] == 1
    assert classification["by_severity"] == {"blocking": 2, "debt": 2}
    assert classification["by_concern"] == {"evidence": 3, "consistency": 1}
    assert classification["by_path_kind"] == {"spec": 2, "code": 1, "test": 1}
    assert classification["by_pr"] == {"7": {"blocking": 2}, "9": {"debt": 2}}


def test_build_counts_a_real_rest_payload_under_the_default_reviewer() -> None:
    """The default reviewer login matches the one the REST API really reports.

    The payload is a real captured `repos/{repo}/issues/{pr}/comments` object whose
    author login comes from the fixture rather than from `DEFAULT_REVIEWER`, and
    `build()` runs with no explicit reviewer. If the default drifts from the login
    REST attaches to the reviewer's comments — for instance to the unsuffixed login
    GraphQL reports — the reviewer filter admits nothing and this reports zero.
    """
    comment = api_comment()

    result = build("outcomeeng/spx", [137], fetch=lambda _repo, _pr: [comment])

    assert result["meta"]["reviewer"] == comment.login
    assert result["classification"]["total_findings"] == 3
    assert result["classification"]["by_severity"] == {"debt": 2, "follow-up": 1}


def test_main_writes_a_json_report(tmp_path: Path) -> None:
    out = tmp_path / "report.json"
    comments = {
        7: [
            comment_from_fixture(
                "blocking_evidence.txt", id=1, url="u1", login=DEFAULT_REVIEWER
            ),
        ]
    }

    exit_code = main(
        ["7", "--repo", "owner/repo", "--out", str(out)],
        fetch=lambda _repo, pr: comments[pr],
    )

    assert exit_code == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["meta"]["repo"] == "owner/repo"
    assert report["classification"]["total_findings"] == 2
