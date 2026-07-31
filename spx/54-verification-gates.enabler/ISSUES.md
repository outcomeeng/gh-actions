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

## 3. Verification-host PR comment persistence waits on hosted delivery

The preview verification host runs the selected skill and publishes the captured
journal-rendered output to the GitHub Actions job summary. It does not set
`SPX_VERDICT_*` sink variables or run a host-owned persistence step yet.

Resolve when the `spx` CLI has the hosted-pull-request verdict-delivery command
tracked in Issue 2: add the host-owned persistence step to
`.github/workflows/spec-tree-verification.yml`, set the `SPX_VERDICT_*` sink
contract only on that step, and keep the agent subprocess free of sink routing
and write credentials per `spx/18-verification-host.adr.md`.

## 4. The invoking action reports success for an agent run that errored

`anthropics/claude-code-action` derives a run's outcome from the result
record's `subtype` alone and does not consult `is_error`
(`base-action/src/run-claude-sdk.ts`, pinned at
`558b1d6cab4085c7753fe402c10bef0fbb92ac7a`):

```ts
const isSuccess = resultMessage.subtype === "success";
result.conclusion = isSuccess ? "success" : "failure";
```

A run rejected before it does any work still emits
`{"subtype": "success", "is_error": true, "num_turns": 1, "total_cost_usd": 0}`,
so the action concludes success, the step stays green, and the gate's check
reports a review that never ran. An expired agent credential reproduces it in
under two seconds. Observed on a consumer repository, where three consecutive
runs reported a passing review check while posting no review.

The action is an upstream dependency this product consumes and does not build
(`spx/gh-actions.product.md`, excluded scope), so the root cause is not fixable
here. Each agent-invoking workflow instead resolves its own outcome from the
run's execution record, per the product-level assertions on outcome resolution.

**Resolution path.** The local check is a defence against a specific upstream
defect, not product truth of its own. Retire it if the action gains an outcome
that reflects `is_error`, or if the verification host of
`spx/18-verification-host.adr.md` supersedes these action-based surfaces —
that host invokes the agent CLI directly and owns its own outcome resolution,
so it never inherits this defect.

## 5. The outcome-resolution check has no regression evidence for its failure branches

The completion check of Issue 4 is inline shell in four workflow files. The
self-test harness exercises it end to end on every pull request, but only ever
along its success branch — a real agent run that completes. Its failure
branches (absent record, malformed record, no result entry, a result reporting
an error) run in no automated evidence lane, so a future edit to the shell can
silently stop rejecting the case the check exists to reject, which is the
original false-green failure mode wearing a different hat.

`spx/15-evidence-model.adr.md` scopes the pytest `[test]` lane to deterministic
Python in the top-level `gh_actions` package and forbids a workflow node
carrying a `[test]` assertion over workflow YAML. Inline workflow shell falls
between those: executing the extracted block against fixtures would assert real
behavior rather than YAML strings, but it is not `gh_actions` package Python and
the ADR admits no lane for it. Moving the logic into that package is not
available either — a consumer pins the reusable workflow alone, and this
product's workflows are deliberately self-contained so no second checkout of
`outcomeeng/gh-actions` is required at runtime.

Resolve at the ADR: decide whether the evidence model gains a lane for inline
workflow shell executed against fixtures, or whether `[audit]` plus the
success-path self-test is the accepted evidence for this class. Until then the
failure branches carry the fixtures recorded in the pull request that
introduced them and no checked-in lane.
