"""Compliance evidence: the extractor validates labels against no fixed set.

The extractor gates neither the severity nor the concern label against a fixed set.
`followup_security.txt` carries a non-governed severity (`FOLLOW-UP`, a legacy label
the current taxonomy no longer sanctions) and `standards_concern.txt` a non-governed
concern (`standards`, outside the five governed concerns); both are real reviewer
comments. The extractor records each label verbatim rather than dropping or
reclassifying it — it owns no taxonomy to gate against — so a non-governed label
surfaces in the extracted output for a maintainer to notice instead of vanishing.
"""

from __future__ import annotations

from gh_actions.review_findings import parse_comment
from gh_actions_testing.harnesses.review_comments import fixture_body


def test_non_governed_severity_label_is_recorded_verbatim() -> None:
    findings, is_clean = parse_comment(fixture_body("followup_security.txt"))

    assert not is_clean
    assert len(findings) == 1
    assert findings[0].severity == "follow-up"
    assert findings[0].concern == "security"


def test_non_governed_concern_label_is_recorded_verbatim() -> None:
    findings, _ = parse_comment(fixture_body("standards_concern.txt"))

    assert findings[0].severity == "debt"
    assert findings[0].concern == "standards"
