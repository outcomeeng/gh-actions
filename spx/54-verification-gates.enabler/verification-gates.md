# Verification Gates

PROVIDES the four verification gates as CI surfaces — validation, test, audit, and review — each running an AI coding agent over a pull request and reporting findings
SO THAT a repository's pull-request flow
CAN obtain agent-run verification across the four layers, gated and invoked through the shared substrate

## Assertions

### Compliance

- ALWAYS: each gate runs on `pull_request` events, is authorized via `spx/32-security.enabler`, and is invoked via `spx/32-agent-invocation.enabler` ([review])
- ALWAYS: the review gate posts findings only and never a verdict — the reviewer reviews, the author decides — per the governance cross-referenced from `plugins/spx` (coordinated in `PLAN-review-skill-from-ci.md`) ([review])
- NEVER: this product restates the review-prompt taxonomy or the reviewer-only decision that `plugins/spx` governs — it cross-references them ([review])
