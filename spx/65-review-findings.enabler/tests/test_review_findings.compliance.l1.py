"""Compliance evidence: the extractor validates labels against no fixed set.

`followup_security.txt` is a real reviewer comment carrying a `FOLLOW-UP [security]`
entry — a legacy severity the current review taxonomy (governed in the plugins spec
tree) no longer sanctions. The extractor records it verbatim rather than dropping or
reclassifying it: it owns no taxonomy to gate labels against, so a non-governed label
surfaces in the extracted output for a maintainer to notice instead of vanishing.
"""

from __future__ import annotations

from pathlib import Path

from gh_actions.review_findings import parse_comment


def test_non_governed_severity_label_is_recorded_verbatim() -> None:
    body = (Path(__file__).parent / "fixtures" / "followup_security.txt").read_text(
        encoding="utf-8"
    )

    findings, is_clean = parse_comment(body)

    assert not is_clean
    assert len(findings) == 1
    assert findings[0].severity == "follow-up"
    assert findings[0].concern == "security"
