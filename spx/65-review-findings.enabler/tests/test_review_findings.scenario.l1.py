"""Scenario evidence: end-to-end extraction over real reviewer comment bodies.

The comment payloads are inert fixture files captured from the spec-tree review
gate's own findings on outcomeeng/spx pull requests, read by path.
"""

from __future__ import annotations

import json
from pathlib import Path

from gh_actions.review_findings import (
    DEFAULT_REVIEWER,
    Comment,
    PathKind,
    build,
    main,
    parse_comment,
)


def _body(name: str) -> str:
    return (Path(__file__).parent / "fixtures" / name).read_text(encoding="utf-8")


def test_finding_comment_parses_into_records() -> None:
    findings, is_clean = parse_comment(_body("blocking_evidence.txt"))
    assert not is_clean
    assert len(findings) == 2
    assert all(f.severity == "blocking" and f.concern == "evidence" for f in findings)
    assert findings[0].file is not None and findings[0].file.endswith(
        "evidence-append.md"
    )
    assert findings[0].line == "11"
    assert findings[0].fields["required"].startswith("Either narrow the assertion")


def test_debt_comment_parses_both_entries_with_their_kinds() -> None:
    findings, is_clean = parse_comment(_body("debt_consistency.txt"))
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
    findings, is_clean = parse_comment(_body("no_findings.txt"))
    assert findings == []
    assert is_clean is True


def test_build_aggregates_counting_only_the_configured_reviewer() -> None:
    comments = {
        7: [
            Comment(
                id=1,
                created_at="t",
                url="u1",
                login=DEFAULT_REVIEWER,
                body=_body("blocking_evidence.txt"),
            ),
            Comment(
                id=3,
                created_at="t",
                url="u3",
                login=DEFAULT_REVIEWER,
                body=_body("no_findings.txt"),
            ),
            Comment(
                id=4,
                created_at="t",
                url="u4",
                login="an-author",
                body=_body("blocking_evidence.txt"),
            ),
        ],
        9: [
            Comment(
                id=2,
                created_at="t",
                url="u2",
                login=DEFAULT_REVIEWER,
                body=_body("debt_consistency.txt"),
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


def test_main_writes_a_json_report(tmp_path: Path) -> None:
    out = tmp_path / "report.json"
    comments = {
        7: [
            Comment(
                id=1,
                created_at="t",
                url="u1",
                login=DEFAULT_REVIEWER,
                body=_body("blocking_evidence.txt"),
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
