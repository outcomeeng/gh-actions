# PLAN — top-level composition intent (bootstrap)

This file records the product areas surfaced during bootstrapping so
`/decomposing spx/` can compose them into top-level children. The lists below
are **intent, not structure** — `/decomposing` owns child boundaries, node
types (enabler vs outcome), ordering evidence, and sparse index assignment. Do
not infer the tree shape from the order here.

## Candidate top-level areas

- **Workflow surfaces** — the consumable reusables, organized by what the agent does: mention-triggered assistance, automated PR review, and the verification gates (validation, test, audit, review).
- **Provider & runtime integration** — a common invocation shape across providers (Anthropic API, Bedrock, Vertex; OpenAI / cloud review; future providers).
- **Supply-chain security & least privilege** — full-SHA pinning, Renovate-managed updates, top-level `permissions: {}` with per-job grants, secret handling.
- **Authorization & workflow-validation gating** — the collaborator-permission gate and the caller-workflow byte-match validation.
- **Agent & plugin provisioning** — plugin/marketplace install and tool-allowlist composition.
- **Consumer onboarding & configuration** — copy-paste caller templates, repo-variable overrides, documentation.
- **Self-test harness** — the in-repo `*-repo.yml` callers that exercise the reusables against this repository.
- **Secret / credential provisioning** — the `push-secrets.py` tooling.

## Known constraints and examples

- Implemented surfaces today are the mention reusables (`spec-tree.yml`, `claude.yml`) and the review reusables (`spec-tree-review.yml`, `claude-code-review.yml`), plus the self-test callers. These are **specified slices** of the surface × provider space; the verification gates and additional providers (OpenAI / cloud) are **declared** and sit in `spx/EXCLUDE` until built.
- Provider routing already exists as inputs (`use_bedrock`, `use_vertex`) and OpenAI cloud review is partially present via `AGENTS.md` — provider-agnosticism is partially realized, not purely aspirational.
- The security posture (SHA-pinning, `permissions: {}`, no secrets in `run:`, actionlint + shellcheck) is enforced by `ci.yml` and documented in `README.md` / `CLAUDE.md` today; the tree should declare it as product-level compliance plus a security enabler.

## Unresolved questions (for `/decomposing` and `/interviewing`)

- **Evidence model** (also in the product spec's Open decisions): `[review]` + actionlint/shellcheck conformance + the self-test harness as scenario evidence, versus a pytest lane scoped to `scripts/`. Resolve via an ADR before `/testing` runs.
- **Surface × provider organization**: by-surface top level with provider as a config axis, versus by-provider top level. A decomposition decision.
- **Relationship to `plugins/spx`**: the review-prompt taxonomy and the reviewer-only decision are governed in `plugins/spx` and cross-referenced here, never restated. The workflow-side coordination for that work lives in `PLAN-review-skill-from-ci.md` (on the `docs/review-skill-from-ci` branch).

## Next step

Invoke `/decomposing spx/` to compose top-level children from these areas.
