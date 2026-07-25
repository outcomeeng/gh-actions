# ISSUES — gh-actions spec tree

## 1. `spx/EXCLUDE` is referenced but does not yet exist

`spx/PLAN.md` references `spx/EXCLUDE` as the registry for nodes with specs
and tests but no implementation. The file does not exist on this branch. Per
`spx/PLAN.md`, `spx/EXCLUDE` entries are created during `/testing` and
implementation per `spx/15-evidence-model.adr.md`, specifically for the three
declared-but-not-built verification gates (`validation`, `test`, `audit`) once
they carry specs and tests.

## 2. Codex adapter and OpenAI / cloud-review provider routing not yet implemented

`spx/32-agent-invocation.enabler` PROVIDES "Anthropic API, Bedrock, Vertex,
OpenAI / cloud review, and further providers" and subscription-backed Codex
authentication — declaring the full provider and agent scope from the product
hypothesis. The verification host implements only its Claude Code adapter, and
the other reusable workflows (`spec-tree.yml`, `spec-tree-review.yml`,
`claude.yml`, `claude-code-review.yml`) carry `use_bedrock`, `use_vertex`, and
`model` inputs but no structured OpenAI routing input. The first closure step is
the verification host's Codex adapter governed by
`spx/18-verification-host.adr.md`; the remaining code-in-violation gap closes
when the other applicable OpenAI invocation paths land.

## 3. Managed instruction blocks blur eval-evidence routing against this product's evidence model

The root managed instruction blocks are rendered from the spec-tree template
(`template_version: 0.21.5`) and include eval-evidence auditor routing. The
product's `spx/15-evidence-model.adr.md` rules `[eval]` out for this product
(`NEVER: an assertion carries [eval] — this product ships no LLM-graded output
of its own`). The ADR governs spec assertions; it does not prohibit the
spec-tree template from listing the generic eval-evidence auditor role.

The product is already protected: the ADR's NEVER rule governs by the truth
hierarchy, and `/authoring` loads it through the blocking `/contextualizing`
step before any assertion is written, so no `[eval]` spec can slip past. The
residual gap is guide-level ambiguity — the generated guide carries no
product-specific pointer that this product has no valid `[eval]` assertions for
that auditor role to inspect.

Resolution owner: `/update-instruction-block` renders the root managed blocks
from the template scoped only by detected test languages and harness spans, and
forbids product-specific hand-edits inside the block. A block-level improvement
belongs in the upstream spec-tree template as a capability-scoping mechanism
(`outcomeeng/plugins`) that distinguishes generic eval-evidence audit routing
from products that do not author `[eval]` assertions. Flagged on PR #32 by the
spec-tree CI reviewer.
