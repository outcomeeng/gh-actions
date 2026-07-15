"""Scenario evidence: end-to-end extraction over real reviewer comment bodies.

The comment payloads are inert fixture files captured from the spec-tree review
gate's own findings on outcomeeng/spx pull requests, read by path.
"""

from __future__ import annotations

from pathlib import Path

from gh_actions.review_findings import DEFAULT_REVIEWER, build, parse_comment


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


def test_no_findings_comment_is_a_clean_pass() -> None:
    findings, is_clean = parse_comment(_body("no_findings.txt"))
    assert findings == []
    assert is_clean is True


def test_build_aggregates_counting_only_the_configured_reviewer() -> None:
    comments = {
        7: [
            {
                "id": 1,
                "created_at": "t",
                "url": "u1",
                "login": DEFAULT_REVIEWER,
                "body": _body("blocking_evidence.txt"),
            },
            {
                "id": 2,
                "created_at": "t",
                "url": "u2",
                "login": "an-author",
                "body": _body("debt_consistency.txt"),
            },
            {
                "id": 3,
                "created_at": "t",
                "url": "u3",
                "login": DEFAULT_REVIEWER,
                "body": _body("no_findings.txt"),
            },
        ]
    }
    result = build("owner/repo", [7], fetch=lambda _repo, pr: comments[pr])

    classification = result["classification"]
    assert classification["total_findings"] == 2
    assert classification["clean_review_passes"] == 1
    assert classification["by_severity"] == {"blocking": 2}
    assert classification["by_pr"] == {"7": {"blocking": 2}}
    assert all(finding["pr"] == 7 for finding in result["findings"])
