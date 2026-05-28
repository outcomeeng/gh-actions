# PLAN — composition state and deferred work

## Top-level composition (done)

`/decomposing spx/` composed six top-level enablers in three dependency tiers.
The product is infrastructure, so the behavior-change bet stays in the product
hypothesis and every top-level node is an enabler.

- `spx/21-self-test-harness.enabler` — foundational testability; every other node is exercised against it.
- `spx/32-security.enabler`, `spx/32-agent-invocation.enabler` — shared substrate (independent peers).
- `spx/54-agent-trigger.enabler`, `spx/54-verification-gates.enabler` — surfaces that consume the substrate (independent peers).
- `spx/76-distribution.enabler` — consumes the surface contracts (templates, repo-variable overrides, docs, secret provisioning).

Reserved index gaps `43`, `65`, and `87` hold space for future top-level insertion.

## Deferred / open

- **Evidence model — governed by `spx/15-evidence-model.adr.md`.** `[review]` + actionlint/shellcheck conformance + the self-test harness as scenario evidence, with a `scripts/`-scoped pytest lane (not the pytest-everywhere default or the canonical `infrastructure → testing → {generators, fixtures, harnesses}` subtree). The six enablers' `[review]` tags conform; `tests/` directories (for `scripts/` logic) and `spx/EXCLUDE` entries (for the declared gates) are created during `/testing` and implementation per that ADR.
- **Declared, not built.** In `spx/54-verification-gates.enabler`, the review gate is implemented; validation, test, and audit are declared and belong in `spx/EXCLUDE` once they carry specs and tests.
- **Per-node decomposition.** Each top-level enabler is a candidate for `/decomposing <node>` as its concerns grow — e.g. `spx/32-security.enabler` into supply-chain / authorization / validation, and `spx/54-verification-gates.enabler` into the four gates. `/authoring` deepens each node's assertions beyond the placeholder compliance rules.
- **plugins/spx cross-reference.** The review gate's prompt taxonomy and reviewer-only decision are governed in `plugins/spx` and cross-referenced, never restated (coordinated in `PLAN-review-skill-from-ci.md` on the `docs/review-skill-from-ci` branch).

## Resolved

- Surface × provider shape: surfaces are top-level with provider as a configuration axis (the `spx/32-agent-invocation.enabler` substrate), not a by-provider partition.
