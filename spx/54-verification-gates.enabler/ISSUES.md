# ISSUES — verification-gates

## 1. Pre-host `spec-tree-review.yml` still carries a baked-in prompt restatement

`spx/54-verification-gates.enabler` declares that this product cross-references the governed review prompt rather than restating it. The canonical prompt lives in `outcomeeng/plugins` at `src/plugins/spec-tree/skills/review-changes/references/review-prompt.md`, governed by `plugins/spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md`.

The canonical prompt has been hardened against phantom standards citations, and `.github/workflows/spec-tree-review.yml` now carries the same citation-discipline rule in its baked-in pre-host prompt. The remaining issue is the baked-in restatement itself: any future canonical prompt change still requires manual synchronization here until the host replacement removes the copy.

**Resolution path.** `spx/18-verification-host.adr.md` declares the resolution: the verification host installs the governed skill instead of restating its prompt, so the baked-in copy is removed when the host supersedes `spec-tree-review.yml`. This follow-on stays open until that replacement lands.

## 2. `SPX_VERDICT_*` sink contract is not canonically declared across both repos

`spx/18-verification-host.adr.md` declares the host's side of the `SPX_VERDICT_*`
sink contract — the variable names and the write credential. The same names are
read by the `spx` CLI (`outcomeeng/spx`), whose hosted-pull-request verdict-delivery
command — the command that posts a rendered verdict back to the pull request — does
not yet exist, so no single canonical declaration spans both repos. The `spx` CLI
runs hermetic-local today: it renders verdict projections but reserves remote
pull-request mutation to a separate, not-yet-built command.

Resolve when the `spx` CLI gains that hosted-PR verdict-delivery command: declare the
`SPX_VERDICT_*` contract canonically in that command's spec node in `outcomeeng/spx`,
then cite that path from `spx/18-verification-host.adr.md` so the host and the CLI
cannot drift on the names. This entry tracks that gap; it is not itself the contract.
