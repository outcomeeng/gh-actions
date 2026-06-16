# Verification Gates

PROVIDES the four verification gates as CI surfaces — validation, test, audit, and review — each running an AI coding agent over a pull request and reporting findings
SO THAT a repository's pull-request flow
CAN obtain agent-run verification across the four layers, gated and invoked through the shared substrate

## Assertions

### Compliance

- ALWAYS: each gate runs on `pull_request` events, is authorized via `spx/32-security.enabler`, and is invoked via `spx/32-agent-invocation.enabler` ([audit])
- ALWAYS: the review gate posts findings only and never a verdict — the reviewer reviews, the author decides — per `plugins/spx/21-spec-tree.enabler/68-reviewing.enabler/reviewing.md` (findings-only) and `plugins/spx/15-merging.pdr.md` (the reviewer reviews, the author decides) ([audit])
- NEVER: this product restates the review-prompt taxonomy (governed by `plugins/spx/21-spec-tree.enabler/68-reviewing.enabler/reviewing.md`) or the reviewer-only decision (governed by `plugins/spx/15-merging.pdr.md`) — it cross-references them ([audit])
