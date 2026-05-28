# Evidence Model

## Purpose

This decision governs which evidence mechanism verifies which kind of assertion across the product — how a reusable-workflows product carries falsifiable evidence when its deliverable is workflow definitions rather than an importable code library.

## Context

**Business impact:** The product's value is reusable CI workflows other repositories pin and trust. Evidence that those workflows behave and stay secure is the product's quality guarantee. A mismatched evidence model either leaves workflow behavior unverified (review-only and unfalsifiable) or imposes a code-library test harness on artifacts that have no importable units — both produce phantom green CI.

**Technical constraints:** The product ships GitHub Actions reusable workflows (YAML), example caller templates, and a small amount of Python under `scripts/` (e.g. `push-secrets.py`). Workflow behavior is observable only by running a workflow on real GitHub events. Structural and shell-injection rules are checked by `actionlint` + `shellcheck` in `ci.yml`. The methodology's default `[test]` lane is pytest (`plugins/spx/15-test-language.adr.md`), and `plugins/spx/15-test-infrastructure.pdr.md` mandates a canonical `infrastructure → testing → {generators, fixtures, harnesses}` subtree — both assume a code product with importable units and a pytest collector.

## Decision

The product verifies each assertion through the evidence mechanism that matches its subject: `[review]` for workflow behavior and security/governance rules no finite automated test can falsify; conformance against `actionlint` + `shellcheck` for structural and shell-injection rules; the in-repo self-test harness (`spx/21-self-test-harness.enabler`) as scenario evidence that a reusable runs end-to-end on real events; and a pytest `[test]` lane scoped to deterministic Python under `scripts/`. The canonical `infrastructure → testing → {generators, fixtures, harnesses}` subtree and the pytest-everywhere default do not apply to workflow nodes.

## Rationale

Workflow behavior has no importable unit a pytest assertion can exercise; its only honest evidence is a real run plus review of the YAML against the governance rules. Forcing pytest over workflow behavior yields assertions over YAML strings — formatting, not behavior.

Structural and security rules — SHA-pinning, no secrets in `run:` bodies, the `permissions:` shape — are falsifiable by `actionlint` + `shellcheck` against the workflow files; that conformance lane in `ci.yml` is the `[test]`-equivalent for those rules.

The self-test harness is this product's analog of a test runner: it invokes each reusable against this repository on the real event shapes, so a reusable's end-to-end behavior is exercised before it ships.

Deterministic Python under `scripts/` (keychain reads, repository detection) is unit-testable and gets a pytest lane like any code.

Alternatives rejected:

- **Pytest everywhere** (the methodology default): pytest cannot exercise workflow runtime behavior; the result is string-shape assertions over YAML — phantom evidence. Retained only for `scripts/`.
- **Review-only:** loses the falsifiability `actionlint`/`shellcheck` already provide for structural rules and pytest provides for `scripts/` logic. Too weak.
- **Adopt the canonical `infrastructure → testing → {generators, fixtures, harnesses}` subtree:** that subtree presumes generators, fixtures, and harnesses feeding a pytest collector over product code; a workflows product has no such code surface, so the subtree would be empty scaffolding. The self-test harness enabler is this product's testing-infrastructure analog.

## Trade-offs accepted

| Trade-off                                                                                                                 | Mitigation / reasoning                                                                                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Workflow behavior leans on `[review]`, which CI does not enforce                                                          | The self-test harness exercises each reusable end-to-end on real events, and `actionlint`/`shellcheck` enforce the structural and security rules; review covers only the residue no run or linter can falsify |
| Diverging from the methodology's pytest-everywhere default and canonical test-infra subtree                               | A workflows product has no importable units; honest evidence is real runs plus conformance, and forcing the default produces phantom green CI                                                                 |
| The self-test harness's callers reference the reusables (a runtime consumer relationship) yet the harness is foundational | Testability leads — every node is built and verified against the harness; the consumer detail is subordinate to the harness as the verification substrate (`spx/21-self-test-harness.enabler`)                |

## Compliance

### Recognized by

Assertions across the tree carry `[review]` for workflow-behavior and governance rules, conformance to `actionlint`/`shellcheck` for structural rules, the self-test harness for end-to-end runs, and `[test]` (pytest) only on `scripts/` logic. No spec assertion forces pytest over a workflow definition.

### MUST

- A `[test]` assertion in the tree targets deterministic Python under `scripts/`, named per the canonical `test_<subject>.<evidence>.<level>.py` convention — the pytest lane is scoped to script logic ([review])
- A reusable workflow's end-to-end behavior is evidenced by a self-test caller in `spx/21-self-test-harness.enabler`, not by an assertion over its YAML ([review])
- Structural and shell-injection rules (SHA-pinning, no secrets in `run:`, the `permissions:` shape) are evidenced by `actionlint` + `shellcheck` conformance in `ci.yml` ([review])

### NEVER

- A workflow node carries a `[test]` assertion that asserts over workflow YAML strings rather than a real run — that is formatting evidence, not behavior ([review])
- The product authors the canonical `infrastructure → testing → {generators, fixtures, harnesses}` subtree — the self-test harness enabler is this product's testing-infrastructure analog ([review])
