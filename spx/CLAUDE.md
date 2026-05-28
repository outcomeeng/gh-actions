# spx/ Directory Guide (Spec Tree)

This guide explains WHEN to invoke spec-tree skills for the **Outcome
Engineering GitHub Actions** product. It is a **router** — the skills contain
the HOW.

---

## Structure Overview

The `spx/` tree is a durable map of the product. Nothing moves because work is
"done" — specs are permanent product truth, not a backlog.

```text
spx/
  gh-actions.product.md                # Product spec (root)
  NN-{slug}.adr.md                     # Architecture decision
  NN-{slug}.pdr.md                     # Product decision
  NN-{slug}.enabler/                   # Shared infrastructure
    {slug}.md                          # Spec file
    tests/                             # Co-located evidence (see Evidence model)
    PLAN.md / ISSUES.md                # Escape hatches (optional)
    NN-{slug}.{enabler|outcome}/       # Children
  NN-{slug}.outcome/                   # Hypothesis + assertions
    {slug}.md
```

---

## Key Principles

1. **Durable map**: specs stay in place; nothing moves because work is "done."
2. **Two node types**: enabler (infrastructure) and outcome (hypothesis + assertions). No other types.
3. **Co-location**: evidence lives with its spec in `tests/`.
4. **Atemporal voice**: specs state product truth; never narrate history.
5. **Deterministic context**: the tree path defines what context an agent receives.
6. **Decision records win by hierarchy**: if a spec contradicts an ADR or PDR in its ancestry, the spec is wrong — reconcile the lower layer.
7. **Decision records updated in-place**: when a decision changes, edit the ADR/PDR directly; no "superseded" workflow.
8. **Escape hatches**: `PLAN.md` / `ISSUES.md` are node-local coordination files committed to git, read automatically by `/contextualizing`, not spec truth.

---

## Numeric Prefixes

Lower index constrains higher; same index means independent peers; numbers are
sibling-unique only. Files and directories share one number space.

**ALWAYS use the full path from `spx/` when referencing a node, ADR, or PDR** —
indices repeat under different parents. Use `/decomposing` to create or
restructure children; it owns boundaries, node types, ordering evidence, and
index assignment.

---

## Evidence model (product-specific)

This product's deliverable is reusable workflows, not a code library, so its
evidence chain differs from the methodology default:

- **`[review]`** for workflow behavior and security/governance compliance no finite automated test can falsify.
- **Conformance** against `actionlint` + `shellcheck` (the `ci.yml` lane) for the structural and shell-injection rules.
- **The self-test harness** (`*-repo.yml` callers) as scenario evidence that a reusable runs end-to-end against this repository.
- **A pytest `[test]` lane scoped to `scripts/`** (e.g. `push-secrets.py`) where deterministic Python logic exists.

The canonical `infrastructure → testing → {generators, fixtures, harnesses}`
subtree and the pytest-everywhere `[test]` default from
`plugins/spx/15-test-infrastructure.pdr.md` and `plugins/spx/15-test-language.adr.md`
do not fit a workflows product as-is. The evidence model is governed by
`spx/15-evidence-model.adr.md`.

---

## When to Invoke Skills

| Step                               | Skill                         |
| ---------------------------------- | ----------------------------- |
| Before ANY spec-tree work          | `/understanding` (BLOCKING)   |
| Before working on a node           | `/contextualizing` (BLOCKING) |
| Create specs / ADRs / PDRs / nodes | `/authoring`                  |
| Break down or compose a node       | `/decomposing`                |
| Restructure the tree               | `/refactoring`                |
| Check consistency / conformance    | `/aligning`                   |
| Write tests for a node             | `/testing`                    |
| Run the TDD flow                   | `/applying`                   |

---

## Excluded Nodes

Nodes with specs and tests but no implementation are listed in `spx/EXCLUDE`;
the quality gate skips their tests while linting still applies. Declared
surfaces and providers that are not yet built live here until implementation
begins.

---

## Session Management

Claude Code session handoffs live in `.spx/sessions/` (separate from the tree):
`todo/` (available for `/pickup`), `doing/` (claimed), `archive/` (completed).
Use `/handoff` to create, `/pickup` to claim.
