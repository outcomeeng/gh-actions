# Outcome Engineering GitHub Actions

## Why this product exists

Bringing an AI coding agent into a repository's CI — reviewing every pull
request, answering mentions, running the verification gates a team relies on —
takes workflow logic that is security-sensitive (token handling, supply-chain
pinning, authorization) and provider-specific. This product provides that
integration as reusable workflows a repository consumes by reference and pins
by commit SHA, so one hardened implementation serves every consuming
repository.

## Product hypothesis

WE BELIEVE THAT reusable, SHA-pinned GitHub Actions workflows that bring AI coding agents into a repository's CI
WILL let teams adopt and evolve agentic automation by pinning a reusable rather than authoring and maintaining workflow logic per repo
CONTRIBUTING TO lower CI-maintenance and security-regression cost and consistent agent automation across the organization

### Evidence of success

| Metric                          | Current           | Target                                  | Measurement approach                                            |
| ------------------------------- | ----------------- | --------------------------------------- | --------------------------------------------------------------- |
| Consumer repos on the reusables | existing installs | org-wide adoption                       | callers referencing `outcomeeng/gh-actions/.github/workflows/*` |
| Workflow logic per consumer     | duplicated inline | one pinned `uses:` stub plus a secret   | logic lines in each consumer's `.github/workflows/`             |
| Supply-chain pin currency       | manual            | Renovate-managed SHA pins, no bare refs | actionlint + Renovate status                                    |

## Scope

### What's included

- Agent-automation surfaces: mention-triggered assistance, automated PR review, and the verification gates (validation, test, audit, review)
- Provider and runtime integration: Anthropic (API, Bedrock, Vertex), OpenAI / cloud review, and further providers behind a common invocation shape
- Supply-chain security and least privilege: full-SHA pinning, Renovate-managed updates, top-level `permissions: {}` with explicit per-job grants, secrets that never cross a `run:` body
- Authorization and workflow-validation gating: collaborator-permission gate, caller-workflow byte-match validation
- Agent and plugin provisioning: plugin and marketplace install, tool-allowlist composition
- Consumer onboarding and configuration: copy-paste caller templates, repo-variable overrides, documentation
- Self-test harness: in-repo callers exercising the reusables against this repository
- Secret and credential provisioning tooling

### What's excluded

| Excluded                                                               | Rationale                                                                                                                                                                                                 |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Upstream agent actions and CLIs (e.g. `anthropics/claude-code-action`) | Consumed as pinned dependencies, not built here                                                                                                                                                           |
| Agent skill, prompt, review-taxonomy, and reviewer-only decision logic | Governed by `plugins/spx/21-spec-tree.enabler/68-reviewing.enabler/reviewing.md` (skill, prompt, taxonomy) and `plugins/spx/15-merging.pdr.md` (reviewer-only decision); cross-referenced, never restated |
| The AI models                                                          | Provided by the agent vendors                                                                                                                                                                             |
| Non-GitHub CI platforms                                                | The product targets GitHub Actions                                                                                                                                                                        |

## Product-level assertions

### Compliance

- ALWAYS: pin every action and reusable workflow referenced by `uses:` by full-length commit SHA with a trailing tag or branch comment — mutable references can be redirected after publication ([audit])
- ALWAYS: declare top-level `permissions: {}` and grant each job only the permissions it needs — least privilege bounds the blast radius of a compromised step ([audit])
- ALWAYS: gate every agent-invoking job behind an authorization check against the repository collaborator-permission API — only `admin`, `maintain`, or `write` actors trigger an agent run ([audit])
- NEVER: interpolate a secret or user-controlled input into a `run:` script body — interpolation resolves before the shell parses the line and enables injection ([audit])
- NEVER: restate the agent skill, prompt, and review-taxonomy governance (governed at `plugins/spx/21-spec-tree.enabler/68-reviewing.enabler/reviewing.md`) or the reviewer-only decision (governed at `plugins/spx/15-merging.pdr.md`) — cross-reference them so the two surfaces cannot drift ([audit])

## Open decisions

| Decision topic | Key question | Options | Triggers ADR/PDR? |
| -------------- | ------------ | ------- | ----------------- |
| None           | N/A          | N/A     | N/A               |
