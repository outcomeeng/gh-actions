# ISSUES — gh-actions spec tree

## 1. `spx/EXCLUDE` is referenced but does not yet exist

`spx/CLAUDE.md` and `spx/PLAN.md` reference `spx/EXCLUDE` as the registry
for nodes with specs and tests but no implementation. The file does not
exist on this branch. Per `spx/PLAN.md`, `spx/EXCLUDE` entries are created
during `/testing` and implementation per `spx/15-evidence-model.adr.md`,
specifically for the three declared-but-not-built verification gates
(`validation`, `test`, `audit`) once they carry specs and tests.

## 2. OpenAI / cloud-review provider routing not yet implemented

`spx/32-agent-invocation.enabler` PROVIDES "Anthropic API, Bedrock, Vertex,
OpenAI / cloud review, and further providers" — declaring the full
provider scope from the product hypothesis. The current reusable
workflows (`spec-tree.yml`, `spec-tree-review.yml`, `claude.yml`,
`claude-code-review.yml`) carry `use_bedrock`, `use_vertex`, and `model`
inputs but no structured OpenAI routing input. Per the methodology,
the spec correctly declares the contract; the code-in-violation gap
closes when an OpenAI invocation path lands.

## 3. Generated spx/CLAUDE.md advertises `[eval]`, which the evidence model forbids

The spx-level guides are rendered from the spec-tree template
(`template_version: 0.21.4`) and list `[eval]` as an assertion tag and
`evals/` as a node subdirectory. `spx/15-evidence-model.adr.md` rules
`[eval]` out for this product (`NEVER: an assertion carries [eval] — this
product ships no LLM-graded output of its own`). The guides therefore name a
verification lane the product's evidence model prohibits.

The product is already protected: the ADR's NEVER rule governs by the truth
hierarchy, and `/authoring` loads it through the blocking `/contextualizing`
step before any assertion is written, so no `[eval]` spec can slip past. The
residual gap is guide-level only — the generated guide carries no
product-specific pointer to the prohibition.

Resolution owner: `/update-spx` renders the guides from the template
scoped only by the `languages` frontmatter and forbids product-specific
hand-edits, so a guide-level fix belongs in the upstream spec-tree template
as a capability-scoping mechanism
(`outcomeeng/plugins`) that omits `[eval]` for products that do not use it.
Flagged on PR #32 by the spec-tree CI reviewer.
