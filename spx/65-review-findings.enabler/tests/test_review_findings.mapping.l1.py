"""Mapping evidence: a cited path maps to its source-owned artifact kind.

The expected kinds are the `PathKind` members owned by the module under test; each
input path is a minimal representative of the pattern `classify_path` documents for
that kind, covering every member of the enumeration.
"""

from __future__ import annotations

from gh_actions.review_findings import PathKind, classify_path


def test_cited_path_maps_to_each_artifact_kind() -> None:
    assert (
        classify_path("spx/34-verification.enabler/15-audit-payload.pdr.md")
        is PathKind.DECISION_PDR
    )
    assert (
        classify_path("spx/13-verify-module-structure.adr.md") is PathKind.DECISION_ADR
    )
    assert (
        classify_path(
            "spx/26-release.enabler/tests/release-notes.compliance.l1.test.ts"
        )
        is PathKind.TEST
    )
    assert (
        classify_path("spx/34-verification.enabler/evidence-append.md") is PathKind.SPEC
    )
    assert (
        classify_path("gh_actions_testing/harnesses/review_comments.py")
        is PathKind.TEST
    )
    assert classify_path("src/domains/verify/verify.ts") is PathKind.CODE
    assert classify_path("gh_actions/review_findings.py") is PathKind.CODE
    assert (
        classify_path("spx/17-file-inclusion.enabler/EXCLUDE")
        is PathKind.SPEC_TREE_OTHER
    )
    assert classify_path("README.md") is PathKind.OTHER
