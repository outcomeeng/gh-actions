# Review Findings

PROVIDES structured extraction and classification of the spec-tree review gate's findings from a pull request — parsing the reviewer's posted finding comments into records and aggregating them by severity, concern, cited-path kind, and pull request
SO THAT this product's maintainers
CAN preserve and assess what the review gate catches across pull requests

## Assertions

### Scenarios

- Given a reviewer comment whose body carries finding entries, when the extractor parses it, then each entry becomes a record holding its severity, concern, cited location, file, and line ([test](tests/test_review_findings.scenario.l1.py))
- Given a reviewer comment that opens with "No findings", when the extractor parses it, then the comment is recorded as a clean review pass carrying no findings ([test](tests/test_review_findings.scenario.l1.py))
- Given comments across a set of pull requests, when the extractor builds its result, then it aggregates the findings and reports counts by severity, concern, cited-path kind, and pull request, counting only comments authored by the configured reviewer ([test](tests/test_review_findings.scenario.l1.py))

### Mappings

- A finding's cited path maps to its artifact kind — an ADR or PDR decision, a spec, a test, code, another spec-tree path, or other ([test](tests/test_review_findings.mapping.l1.py))

### Compliance

- ALWAYS: the extractor records whatever severity and concern labels a finding comment carries, without validating them against a fixed set — the label vocabulary it reads is the reviewer's output, not a contract this node owns ([test](tests/test_review_findings.compliance.l1.py))
- NEVER: this node restates or judges findings against the governed review taxonomy — the taxonomy is governed by `plugins/spx/21-spec-tree.enabler/68-reviewing.enabler/reviewing.md` and cross-referenced, never copied ([audit])
