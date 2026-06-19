# ISSUES — verification-gates

## 1. Review gate: phantom-standards risk and pre-host migration of `spec-tree-review.yml`

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
cross-references the review-prompt governance at the prompt body
`src/plugins/spec-tree/skills/reviewing-changes/references/review-prompt.md`
(governed by the spec `plugins/spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md`)
and never restates it. Once the canonical prompt is
hardened upstream, apply the same citation-discipline rule to the baked-in copy
in `.github/workflows/spec-tree-review.yml` (the `Standards` category and the
`Reference:` instruction lines), or replace the restatement with a reference to
the shared prompt so the two surfaces cannot drift.

**Resolution path.** `spx/18-verification-host.adr.md` declares the resolution:
the verification host installs the governed skill instead of restating its
prompt, so the baked-in copy is removed when the host supersedes
`spec-tree-review.yml`. This follow-on stays open until that replacement lands.

## 2. `SPX_VERDICT_*` sink contract is not canonically declared across both repos

`spx/18-verification-host.adr.md` declares the host's side of the `SPX_VERDICT_*`
sink contract — the variable names and the write credential. The same names are
shared with the `spx` CLI in `outcomeeng/plugins` that reads them, and that CLI
does not yet exist, so no single canonical declaration spans both repos.

Resolve when the `spx` CLI lands its sink-routing support upstream: declare the
`SPX_VERDICT_*` variable list canonically in the CLI's own spec node in
`outcomeeng/plugins`, then cite that path from `spx/18-verification-host.adr.md`
so the host and the CLI cannot drift on the names. This entry tracks that gap; it
is not itself the contract.
