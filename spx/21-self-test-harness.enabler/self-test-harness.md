# Self-Test Harness

PROVIDES an in-repo harness — caller workflows that invoke this repository's own reusables via `uses: ./.github/workflows/<name>.yml` against its own issues, comments, and pull requests
SO THAT this product's maintainers
CAN observe each reusable's end-to-end runtime behavior on real GitHub events before it reaches an external consumer

## Assertions

### Compliance

- ALWAYS: each reusable workflow has a corresponding in-repo caller (`*-repo.yml`) that invokes it via `uses: ./.github/workflows/<name>.yml` — a branch push exercises the reusable against this repository ([audit])
- ALWAYS: the self-test callers fire on the same event shapes a consumer uses (mention events, `pull_request`) so the harness exercises the real trigger path ([audit])
- NEVER: a reusable ships without an in-repo caller exercising it — an unexercised reusable has no end-to-end evidence ([audit])
