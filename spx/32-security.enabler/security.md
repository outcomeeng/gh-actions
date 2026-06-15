# Security

PROVIDES the product's trust boundary — full-SHA pinning with Renovate-managed updates, least-privilege `permissions: {}` with explicit per-job grants, the collaborator-permission authorization gate, the caller-workflow byte-match validation, and the no-secrets-in-`run:` discipline
SO THAT every reusable workflow and the surfaces built on it
CAN run only for authorized actors, against dependencies that cannot be redirected, with the narrowest permissions, and without leaking secrets

## Assertions

### Compliance

- ALWAYS: the `authorize` job resolves the actor's permission via `repos/{owner}/{repo}/collaborators/{actor}/permission` and the agent job runs only on `admin`, `maintain`, or `write`; other actors yield a skipped (not failed) job ([audit])
- ALWAYS: the review surface's `validate-workflow` job compares the caller workflow at the PR head to the default branch and skips with a notice when they differ ([audit])
- ALWAYS: every `uses:` reference is pinned by full-length commit SHA with a trailing `# tag` or `# branch` comment that Renovate advances ([audit])
- NEVER: a secret or user-controlled input reaches a `run:` body via `${{ }}` interpolation — values flow through `with:` inputs or job-level `env:` only ([audit])
