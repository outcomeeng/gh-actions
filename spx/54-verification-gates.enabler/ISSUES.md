# ISSUES — verification-gates

## 1. Review gate cites phantom standards it never read

The review gate's reviewer emits `standards` findings against rules that do not
exist in the repository under review. On `outcomeeng/spx` PR #109 the reviewer
posted a `DEBT [standards]` finding whose `Reference:` quoted `CLAUDE.md` as
saying *"Never write multi-paragraph docstrings or multi-line comment blocks —
one short line max."* No such rule exists in that repository's `CLAUDE.md`. The
rule leaked from the underlying coding agent's own system prompt / global
instructions (or is an outright hallucination), and the reviewer attributed it
to the repository's `CLAUDE.md`.

**Canonical source — not this repo.** The review prompt is governed in the
`outcomeeng/plugins` repo by the `reviewing-changes` skill: the prompt body
lives at
`src/plugins/spec-tree/skills/reviewing-changes/references/review-prompt.md`,
and the governing spec node is
`spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler`.
The full diagnosis and the required prompt-hardening (a strongly worded rule
that the reviewer may cite a standard only after reading that exact text from a
file present in the repository under review, and must discard any rule it merely
recalls — comment-length and docstring-length rules named as the known failure
mode) are tracked there as Issue 3 in that node's `ISSUES.md`. Fix it at the
canonical source.

**This repo's follow-on.** The `spec-tree-review.yml` workflow carries a
baked-in restatement of that prompt. Per this tree's
`spx/54-verification-gates.enabler` Compliance assertions, this product
cross-references the review-prompt governance at
`plugins/spx/21-spec-tree.enabler/68-reviewing.enabler/reviewing.md` and never
restates it. Once the canonical prompt is
hardened upstream, apply the same citation-discipline rule to the baked-in copy
in `.github/workflows/spec-tree-review.yml` (the `Standards` category and the
`Reference:` instruction lines), or replace the restatement with a reference to
the shared prompt so the two surfaces cannot drift.
