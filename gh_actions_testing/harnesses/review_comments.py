"""Harness: load captured reviewer-comment payloads and assemble Comment inputs.

The payloads are inert fixture files captured from the spec-tree review gate's
own findings on ``outcomeeng/spx`` pull requests. This harness owns reading them
from disk by path and constructing ``gh_actions.review_findings.Comment`` inputs
around them for ``build()``-level tests. It owns no severity, concern, or
expected-classification value — those come from the source module under test and
from the fixture content itself — and it replaces no behavior an assertion
verifies: parsing and classification stay in ``gh_actions.review_findings``.
"""

from __future__ import annotations

from pathlib import Path

from gh_actions.review_findings import Comment

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def fixture_body(name: str) -> str:
    """Read one captured reviewer-comment payload from the fixtures home by name."""
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def comment_from_fixture(
    fixture: str,
    *,
    id: int,
    login: str,
    url: str = "u",
    created_at: str = "t",
) -> Comment:
    """Build one ``Comment`` around a captured payload for ``build()``-level tests.

    The envelope fields (``id``, ``login``, ``url``, ``created_at``) are supplied
    per case by the caller; only the comment body comes from the fixture.
    """
    return Comment(
        id=id,
        created_at=created_at,
        url=url,
        login=login,
        body=fixture_body(fixture),
    )
