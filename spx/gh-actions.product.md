# Outcome Engineering GitHub Actions

## Why this product exists

Bringing an AI coding agent into a repository's CI — reviewing every pull
request, answering mentions, running the verification gates a team relies on —
takes workflow logic that is security-sensitive (token handling, supply-chain
pinning, authorization) and provider-specific. Authored per repository, that
logic drifts, regresses, and duplicates effort across every repo that wants it.
This product provides the integration once, as reusable workflows a repository
consumes by reference and pins by commit SHA.

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

| Excluded                                                               | Rationale                                                   |
| ---------------------------------------------------------------------- | ----------------------------------------------------------- |
| Upstream agent actions and CLIs (e.g. `anthropics/claude-code-action`) | Consumed as pinned dependencies, not built here             |
| Agent skill, prompt, and review-taxonomy logic                         | Governed in `plugins/spx`; cross-referenced, never restated |
| The AI models                                                          | Provided by the agent vendors                               |
| Non-GitHub CI platforms                                                | The product targets GitHub Actions                          |

## Product-level assertions

### Compliance

- ALWAYS: pin every third-party action and reusable workflow by full-length commit SHA with a trailing tag or branch comment — mutable references can be redirected after publication
- ALWAYS: declare top-level `permissions: {}` and grant each job only the permissions it needs — least privilege bounds the blast radius of a compromised step
- ALWAYS: gate every agent-invoking job behind an authorization check against the repository collaborator-permission API — only `admin`, `maintain`, or `write` actors trigger an agent run
- NEVER: interpolate a secret or user-controlled input into a `run:` script body — interpolation resolves before the shell parses the line and enables injection
- NEVER: restate agent skill, prompt, or review-taxonomy governance that lives in `plugins/spx` — cross-reference it so the two surfaces cannot drift

## Open decisions

| Decision topic           | Key question                                                                   | Options                                                                                                                        | Triggers ADR/PDR?   |
| ------------------------ | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | ------------------- |
| Evidence model           | How does a workflows product carry verifiable evidence without a pytest suite? | self-test harness as scenario evidence + actionlint/shellcheck conformance + `[review]`; pytest lane scoped to `scripts/` only | Yes                 |
| Surface × provider shape | How is the surface/provider space organized in the tree?                       | by-surface top level with provider as a config axis; by-provider top level                                                     | Yes (decomposition) |
