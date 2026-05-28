# Self-Test Harness

PROVIDES an in-repo harness — caller workflows that invoke this repository's own reusables via `uses: ./.github/workflows/<name>.yml` against its own issues, comments, and pull requests
SO THAT every other node in this product — the `spx/32-security.enabler` and `spx/32-agent-invocation.enabler` substrate, the `spx/54-agent-trigger.enabler` and `spx/54-verification-gates.enabler` surfaces, and `spx/76-distribution.enabler`
CAN be exercised end-to-end on real GitHub events before it ships, so a reusable's runtime behavior is verifiable without an external consumer

## Assertions

### Compliance

- ALWAYS: each reusable workflow has a corresponding in-repo caller (`*-repo.yml`) that invokes it via `uses: ./.github/workflows/<name>.yml` — a branch push exercises the reusable against this repository ([review])
- ALWAYS: the self-test callers fire on the same event shapes a consumer uses (mention events, `pull_request`) so the harness exercises the real trigger path ([review])
- NEVER: a reusable ships without an in-repo caller exercising it — an unexercised reusable has no end-to-end evidence ([review])
