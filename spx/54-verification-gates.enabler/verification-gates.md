# Verification Gates

PROVIDES the four verification gates as CI surfaces — validation, test, audit, and review — each running an AI coding agent over a pull request and reporting findings
SO THAT a repository's pull-request flow
CAN obtain agent-run verification across the four layers, gated and invoked through the shared substrate

## Assertions

### Compliance

- ALWAYS: each gate runs on `pull_request` events, is authorized via `spx/32-security.enabler`, and is invoked via `spx/32-agent-invocation.enabler` ([audit])
- ALWAYS: the realization of a verification gate is governed by `spx/18-verification-host.adr.md` — verdict logic lives in the installed skill, not the gate workflow ([audit])
- ALWAYS: a changed-file filter scopes the run before the agent starts, so a change outside a gate's declared paths starts no agent for that gate ([audit])
- NEVER: a gate's changed-file filter decides from the push event's file list alone when the gate makes a security-relevant decision — it resolves the changed set through a checkout- or API-based source the PR head cannot forge, per `spx/18-verification-host.adr.md` ([audit])
- ALWAYS: the review gate posts findings only and never a verdict — the reviewer reviews, the author decides — per `plugins/spx/21-spec-tree.enabler/68-reviewing.enabler/reviewing.md` (findings-only) and `plugins/spx/15-merging.pdr.md` (the reviewer reviews, the author decides) ([audit])
- NEVER: this product restates the review prompt (governed by `plugins/spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md`), the review taxonomy (governed by `plugins/spx/21-spec-tree.enabler/68-reviewing.enabler/reviewing.md`), or the reviewer-only decision (governed by `plugins/spx/15-merging.pdr.md`) — it cross-references them ([audit])
- ALWAYS: an agent-invoking gate job fails unless the agent run's execution record shows a completed run — an absent, truncated, non-array, result-less, or error-reporting record is rejected with an actionable message ([test](tests/test_outcome_resolution.compliance.l1.py))
- ALWAYS: the outcome-resolution step's inline shell agrees across every workflow file that carries it ([test](tests/test_outcome_resolution.compliance.l1.py))
