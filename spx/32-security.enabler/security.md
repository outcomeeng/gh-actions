# Security

PROVIDES the product's trust boundary — full-SHA pinning with Renovate-managed updates, least-privilege `permissions: {}` with explicit per-job grants, the collaborator-permission authorization gate, the caller-workflow byte-match validation, the no-secrets-in-`run:` discipline, and verdict-skill environment containment on the verification host
SO THAT every reusable workflow and the surfaces built on it
CAN run only for authorized actors, against dependencies that cannot be redirected, with the narrowest permissions, and without leaking secrets

## Assertions

### Compliance

- ALWAYS: the `authorize` job resolves the actor's permission via `repos/{owner}/{repo}/collaborators/{actor}/permission` and the agent job runs only on `admin`, `maintain`, or `write`; other actors yield a skipped (not failed) job ([audit])
- ALWAYS: a surface whose behavior is driven by caller-supplied inputs — the review surface, and the verification host of `spx/18-verification-host.adr.md` whose `skill`/`ref` inputs select the judgment code — runs a `validate-workflow` job that compares the caller workflow at the PR head to the default branch and skips with a notice when they differ, so a same-repo PR cannot redirect those inputs ([audit])
- ALWAYS: every `uses:` reference is pinned by full-length commit SHA with a trailing `# tag` or `# branch` comment that Renovate advances ([audit])
- ALWAYS: the verification host's `skill` source `ref` — a `with:` input that selects the judgment code running with agent credentials — falls under the same full-SHA pinning discipline per `spx/18-verification-host.adr.md`: a production caller SHA-pins it, and a floating ref is admitted only for a trusted-boundary preview caller carrying the documented exception marker ([audit])
- NEVER: a secret or user-controlled input reaches a `run:` body via `${{ }}` interpolation — values flow through `with:` inputs or job-level `env:` only ([audit])
- ALWAYS: a verification-host surface launches its verdict agent and skill with the sanitized environment required by `spx/18-verification-host.adr.md`, so their environment and credentials match a local run ([audit])
