"""Compliance evidence: the extractor validates labels against no fixed set.

The extractor gates neither the severity nor the concern label against a fixed
set, so it owns no taxonomy and judges no label. `followup_security.txt` carries
the severity `FOLLOW-UP` and `standards_concern.txt` the concern `standards`;
both are real reviewer comments captured from live review runs. The extractor
records each label verbatim rather than dropping, normalizing, or reclassifying
it, so whatever vocabulary a reviewer configuration emits reaches the extracted
output for a maintainer to assess. These cases name no label governed or
otherwise: which taxonomy sanctions which label is the reviewing decision's to
state, and this node cross-references it rather than restating or judging it.
"""

from __future__ import annotations

from gh_actions.review_findings import parse_comment
from gh_actions_testing.harnesses.review_comments import fixture_body


def test_severity_label_is_recorded_verbatim() -> None:
    findings, is_clean = parse_comment(fixture_body("followup_security.txt"))

    assert not is_clean
    assert len(findings) == 1
    assert findings[0].severity == "follow-up"
    assert findings[0].concern == "security"


def test_concern_label_is_recorded_verbatim() -> None:
    findings, _ = parse_comment(fixture_body("standards_concern.txt"))

    assert findings[0].severity == "debt"
    assert findings[0].concern == "standards"
