# ISSUES — gh-actions spec tree

## 1. Coarse `plugins/spx` directory-level cross-references

Three locations in this tree cite `plugins/spx` as a directory-level
governance pointer rather than a specific file. A specific-file path
replaces each pointer once the canonical PDR governing the shared
Review-layer implementation is authored in `plugins/spx`. The working draft
sits at the root of the `outcomeeng/plugins` repository as
`PDR-DRAFT-shared-review-implementation.md`.

Affected locations:

- `spx/gh-actions.product.md` — the `What's excluded` table row "Agent
  skill, prompt, and review-taxonomy logic / Governed in `plugins/spx`;
  cross-referenced, never restated".
- `spx/gh-actions.product.md` — the product-level NEVER assertion:
  "restate agent skill, prompt, or review-taxonomy governance that lives
  in `plugins/spx` — cross-reference it so the two surfaces cannot drift".
- `spx/54-verification-gates.enabler/verification-gates.md` — the
  Compliance assertion citing "the governance cross-referenced from
  `plugins/spx`".
- `spx/PLAN.md` — the "plugins/spx cross-reference" bullet stating the
  review gate's prompt taxonomy and reviewer-only decision are "governed
  in `plugins/spx` and cross-referenced, never restated".

Resolve before the verification-gates review gate's implementation begins.

## 2. `spx/EXCLUDE` is referenced but does not yet exist

`spx/CLAUDE.md` and `spx/PLAN.md` reference `spx/EXCLUDE` as the registry
for nodes with specs and tests but no implementation. The file does not
exist on this branch. Per `spx/PLAN.md`, `spx/EXCLUDE` entries are created
during `/testing` and implementation per `spx/15-evidence-model.adr.md`,
specifically for the three declared-but-not-built verification gates
(`validation`, `test`, `audit`) once they carry specs and tests.
