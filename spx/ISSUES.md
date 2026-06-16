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

The spx-level guide is rendered from the spec-tree template
(`template_version: 0.18.13`) and lists `[eval]` as an assertion tag and
`evals/` as a node subdirectory. `spx/15-evidence-model.adr.md` rules
`[eval]` out for this product (`NEVER: an assertion carries [eval] — this
product ships no LLM-graded output of its own`). The guide therefore names a
verification lane the product's evidence model prohibits.

The product is already protected: the ADR's NEVER rule governs by the truth
hierarchy, and `/authoring` loads it through the blocking `/contextualizing`
step before any assertion is written, so no `[eval]` spec can slip past. The
residual gap is guide-level only — the generated guide carries no
product-specific pointer to the prohibition.

Out of scope for this repo: `/update-spx` renders the guide from the template
scoped only by the `languages` frontmatter and forbids product-specific
hand-edits, so a guide-level fix would be reverted on the next re-render. The
real fix is a capability-scoping mechanism in the upstream spec-tree template
(`outcomeeng/plugins`) that omits `[eval]` for products that do not use it.
Flagged on PR #32 by both the spec-tree CI reviewer and Codex.
