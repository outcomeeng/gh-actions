# Evidence Model

The product verifies each assertion through the evidence mechanism that matches its subject: `[audit]` for workflow behavior and security/governance rules no finite automated test can falsify; conformance against `actionlint` + `shellcheck` for structural and shell-injection rules; the in-repo self-test harness (`spx/21-self-test-harness.enabler`) as scenario evidence that a reusable runs end-to-end on real events; and a pytest `[test]` lane scoped to deterministic Python under `scripts/`. The canonical `infrastructure → testing → {generators, fixtures, harnesses}` subtree and the pytest-everywhere default from `plugins/spx/15-test-language.adr.md` and `plugins/spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` do not apply to workflow nodes.

## Rationale

The product's deliverable is reusable CI workflows other repositories pin and trust, plus example caller templates and a small amount of Python under `scripts/` (e.g. `push-secrets.py`). Evidence that those workflows behave and stay secure is the product's quality guarantee. A mismatched evidence model either leaves workflow behavior unverified — review-only and unfalsifiable — or imposes a code-library test harness on artifacts that have no importable units. Both produce phantom green CI.

Workflow behavior has no importable unit a pytest assertion can exercise; its only honest evidence is a real run plus review of the YAML against the governance rules. Forcing pytest over workflow behavior yields assertions over YAML strings — formatting, not behavior.

Structural and security rules — SHA-pinning, no secrets in `run:` bodies, the `permissions:` shape — are falsifiable by `actionlint` + `shellcheck` against the workflow files; that conformance lane in `ci.yml` is the `[test]`-equivalent for those rules.

The self-test harness is this product's analog of a test runner: it invokes each reusable against this repository on the real event shapes, so a reusable's end-to-end behavior is exercised before it ships.

Deterministic Python under `scripts/` (keychain reads, repository detection) is unit-testable and gets a pytest lane like any code.

The model accepts that workflow behavior leans on `[audit]`, which CI does not enforce: the self-test harness and the `actionlint`/`shellcheck` conformance lane carry the falsifiable load, and audit covers only the residue no run or linter can falsify. It also accepts that the self-test harness's callers reference the reusables — a runtime consumer relationship — while the harness itself is foundational; testability leads, so every node is built and verified against the harness, and that consumer detail stays subordinate to the harness as the verification substrate (`spx/21-self-test-harness.enabler`).

Alternatives rejected:

- **Pytest everywhere** (the methodology default): pytest cannot exercise workflow runtime behavior; the result is string-shape assertions over YAML — phantom evidence. Retained only for `scripts/`.
- **Review-only:** loses the falsifiability `actionlint`/`shellcheck` already provide for structural rules and pytest provides for `scripts/` logic. Too weak.
- **Adopt the canonical `infrastructure → testing → {generators, fixtures, harnesses}` subtree:** that subtree presumes generators, fixtures, and harnesses feeding a pytest collector over product code; a workflows product has no such code surface, so the subtree would be empty scaffolding. The self-test harness enabler is this product's testing-infrastructure analog.

## Verification

### Audit

- ALWAYS: a `[test]` assertion in the tree targets deterministic Python under `scripts/`, named per the canonical `test_<subject>.<evidence>.<level>.py` convention — the pytest lane is scoped to script logic ([audit])
- ALWAYS: a reusable workflow's end-to-end behavior is evidenced by a self-test caller in `spx/21-self-test-harness.enabler`, not by an assertion over its YAML ([audit])
- ALWAYS: structural and shell-injection rules (SHA-pinning, no secrets in `run:`, the `permissions:` shape) are evidenced by `actionlint` + `shellcheck` conformance in `ci.yml` ([audit])
- NEVER: a workflow node carries a `[test]` assertion that asserts over workflow YAML strings rather than a real run — that is formatting evidence, not behavior ([audit])
- NEVER: the product authors the canonical `infrastructure → testing → {generators, fixtures, harnesses}` subtree — the self-test harness enabler is this product's testing-infrastructure analog ([audit])
- NEVER: an assertion carries `[eval]` — this product ships no LLM-graded output of its own; the agent's review behavior is governed by `plugins/spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md` and cross-referenced, so the `[audit]`, `actionlint`/`shellcheck` conformance, and `scripts/`-scoped `[test]` lanes above cover every assertion ([audit])
