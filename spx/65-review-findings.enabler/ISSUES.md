# ISSUES — review-findings

## 1. Aggregation scenario restates `PathKind` values as string literals

`spx/65-review-findings.enabler/tests/test_review_findings.scenario.l1.py`
asserts `classification["by_path_kind"] == {"spec": 2, "code": 1, "test": 1}`
in `test_build_aggregates_counting_only_the_configured_reviewer`. The keys are
`PathKind` values copied as literals, while `PathKind` in
`gh_actions/review_findings.py` owns that vocabulary and the test file already
imports it. A renamed member value leaves the literal expectation stale.

Raised as a filed source-ownership finding by the test-evidence audit of this
node.

**Settled when** the expected `by_path_kind` keys derive from `PathKind`
members rather than literal strings.
