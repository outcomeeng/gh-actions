# Plan — run `spec-tree:reviewing-changes` from CI (gh-actions side)

## Why this plan exists

The `spec-tree-review.yml` workflow today runs a long inline prompt that
duplicates the taxonomy and render shape of the
`spec-tree:reviewing-changes` skill. Two parallel implementations of the
same prompt drift; the durable fix is one source of truth for the review
prompt and render — the skill — invoked from CI (the direction recorded in
`reviewing-changes/PLAN.md` item 6).

A `request_changes`↔`approve` flip across two runs on the same PR
(`leoherd` PR #287) looks like the drift to fix, but it is a symptom of a
deeper modeling error: the reviewer is emitting a *decision* it has no
business making.

**The reviewer reviews; the author decides.** A review produces findings —
each carrying a `severity` (`blocking`/`debt`/`follow_up`) — and nothing
more. The CI surface is therefore always a GitHub **COMMENT** review (or a
plain issue comment), never `APPROVE`/`REQUEST_CHANGES`. What must be
deterministic is the *findings*, not a verdict. The `decision` field the
skill emits today is the removable duality at the root of the flip; child 3
below never consumes it.

Policy lives with the consumer, keyed on severity and surface — not in the
reviewer:

- **Locally** (pre-push gate): every finding — `blocking`, `debt`,
  `follow_up` — is addressed, unless one needs major refactoring, in which
  case the changeset is split across branches/PRs rather than fixed inline.
- **In CI** (PR open): `blocking` and `debt` are addressed; `follow_up` is
  captured/tracked when fixing it would widen the PR.

Decision: refactor the workflow to install the skill and invoke it, in three
staged children. This file captures the workflow-side work for each. The
mirror file at `outcomeeng/plugins/PLAN-review-skill-from-ci.md` captures the
plugin side, and the spec node that governs all three children is authored
under `plugins/spx/...`.

## Verification taxonomy — where this work fits

The spx CLI's spec tree defines four execution domains that together form a
Verification umbrella. They are distinct enablers, not a single node — the
umbrella is implicit, enumerated in cross-cutting infrastructure docs:

| Layer      | Domain enabler in spx/spx        | CLI surface      | Implementation state               |
| ---------- | -------------------------------- | ---------------- | ---------------------------------- |
| Validation | `spx/spx/41-validation.enabler/` | `spx validation` | Built (`src/domains/validation/`)  |
| Test       | `spx/spx/41-testing.enabler/`    | `spx test`       | Built (`src/testing/`)             |
| Audit      | `spx/spx/36-audit.enabler/`      | `spx audit`      | Built (`src/domains/audit/`)       |
| Review     | `spx/spx/46-reviewing.enabler/`  | `spx review`     | **Spec-only — no `src/` code yet** |

Authoritative cross-cutting citations enumerating all four layers together:

- `spx/spx/17-file-inclusion.enabler/11-ignore-defaults.pdr.md` — names
  "Validation, testing, auditing, and reviewing" and how each layer's
  path-filter semantics differ.
- `spx/spx/17-file-inclusion.enabler/15-scope-composition.adr.md` — same
  enumeration as ADR-level rule.
- `spx/spx/16-config.enabler/PLAN.md` — coordinates all four layers'
  migration to shared config descriptors; Review (R1 packet) is in-flight.
- `spx/spx/spx.product.md` and `spx/spx/PLAN.md` — name the four as
  quality gates and execution domains at product level.

**The work this plan governs is the Review layer.** The `spec-tree-review.yml`
workflow is today's CI surface for the Review layer; the local
`changes-reviewer` agent is today's developer surface; `spx review pr <n>`
is the future unified surface defined at
`spx/spx/46-reviewing.enabler/65-pr-review.enabler/pr-review.md` but
unimplemented.

## Open architectural question

The plugins plan flags an architectural choice that affects this plan:
should children 2 and 3 anticipate `spx review pr <n>` shipping, or proceed
as if the skill is the long-term CI entry point?

Three possible framings — wait for the plugins session's `/interviewing`
outcome before starting workflow implementation:

1. **Standalone.** Workflow invokes the skill directly; `spx review pr`
   becomes a wrapper later. Children 1–3 ship in their current shape.
2. **Transitional bridge.** Workflow invokes the skill but avoids investing
   in logic that `spx review pr` will subsume (target resolution, descriptor
   loading, reviewer selection). Children 1–3 ship leaner.
3. **Reorder.** Ship `spx review pr` first; the workflow then invokes
   `spx review pr <n>` and the skill-in-CI children become unnecessary.

The plugins session owns this question. Sync before starting child 1 here.

## The decision PDRs

The decision driving this work has a canonical PDR authored in `plugins/`
(see `outcomeeng/plugins/PLAN-review-skill-from-ci.md`) and a cross-reference
PDR authored in `spx/` (see `outcomeeng/spx/PLAN-review-skill-from-ci.md`).
This repo has no spec tree, so no PDR is authored here.

What this session DOES regarding the decision record:

- Read the canonical PDR once it exists (path supplied by the plugins
  session).
- Add a reference to the canonical PDR in this repo's `README.md` and/or
  `AGENTS.md`, in a one-paragraph "Governing decisions" section. The
  reference points at the PDR path (or commit-pinned URL) so anyone
  modifying `spec-tree-review.yml` or the new `spec-tree-review-skill.yml`
  knows where the rule lives.
- All subsequent workflow-side work cites the canonical PDR rather than
  restating the rule inline.

## What I already gathered

- Workflow: `outcomeeng/gh-actions/.github/workflows/spec-tree-review.yml` —
  reusable `workflow_call` that runs `anthropics/claude-code-action@v1.0.123`.
  The inline prompt (lines 464–584) carries the entire review logic. The
  workflow ALREADY has inputs for plugin install
  (`use_project_plugins`, `extra_plugins`, `plugin_marketplaces`, lines
  101–123) and ALREADY has allowlist-composition logic (`append_allow_list`,
  `override_allow_list`, lines 59–80) — both currently default to "off".
- Allowlist baseline today (line 358):
  `Bash(gh issue view:*),Bash(gh issue list:*),Bash(gh pr comment:*),Bash(gh pr diff:*),Bash(gh pr view:*),Bash(gh pr list:*),Bash(sed:*),Bash(grep:*),Bash(head:*)`.
  The skill chain needs `Bash(python3:*)`, `Bash(git:*)`, and reads/writes
  files under `${RUNNER_TEMP}` (or the workspace). The `Read` tool is
  implicitly allowed; `Write` is not, but the skill chain writes via
  `subprocess`/`gh api`, not via Claude's `Write` tool.
- Repos that consume this workflow today: at least `leoherd`. Useful as the
  test consumer.
- `validate-workflow` job (lines 146–206) requires the caller's workflow file
  at PR head to match the default branch byte-for-byte. So any changes to the
  call site in the consumer repo have to land via a workflow-only PR first;
  budget for that round-trip when designing the verification plan.
- The existing `Run Claude Code Review` step (line 444) is the only place
  Claude actually runs. Plugin install and env composition happen in prior
  steps in the same job; they're already wired through to the action via
  `plugins:`, `plugin_marketplaces:`, and `GITHUB_ENV`.
- This repo has no `spx/` tree of its own. The governing specs for this
  workflow live in the plugins repo (`plugins/spx/...`) and the spx CLI's
  Review-layer spec (`spx/spx/46-reviewing.enabler/`). The new spec node is
  authored in the plugins session, not here.

## The three children, workflow-side

Decomposition the user specified — workflow-side implementation only.

### Child 1 — bare-minimum mechanics: skill reachable from CI

**Goal:** prove `spec-tree:reviewing-changes` is installable and reachable
inside the `claude-code-action` run. No actual review is generated yet.

**Workflow-side work:**

- Create a NEW workflow file alongside the existing one — proposed name
  `spec-tree-review-skill.yml`. Do not modify `spec-tree-review.yml` in this
  child. Running two workflows in parallel on the same PR for the duration
  of the staged rollout is the cleanest way to compare outputs and avoid
  regressing the live review.
- The new workflow installs the spec-tree plugin via the existing inputs
  (`extra_plugins: spec-tree@outcomeeng`, `plugin_marketplaces:
  outcomeeng/plugins`). Match the spec-tree marketplace name exactly as it
  appears in `plugins/plugins.json` (or whichever manifest the plugins repo
  uses).
- Widen the allowlist for the skill chain: add `Bash(python3:*)` and
  `Bash(git:*)` via `append_allow_list`. Keep the baseline so the existing
  `gh` patterns still apply.
- Inline prompt becomes a reachability check that does **not** invoke the
  reviewer: "Confirm the `spec-tree` plugin is installed and that the
  `spec-tree:reviewing-changes` skill and the `changes-reviewer` agent are
  registered in this run; report present/absent for each. Do NOT invoke the
  agent or the skill." Invoking `changes-reviewer` runs the full review
  chain — it parses the input, sets the env contract, and calls the skill
  (per `reviewing-changes/PLAN.md` D1) — so it cannot serve as a no-op probe.
  Reachability is provable from the plugin-install step's exit code plus the
  registration check.
- Use the consumer repo (`leoherd` or similar) to wire up the new workflow in
  a workflow-only PR, then a follow-up PR to exercise it. The
  `validate-workflow` gate requires the caller's workflow file to match the
  default branch, so the wire-up PR has to merge before the verify PR fires.
- Permissions: keep the existing `pull-requests: write`, `issues: write`,
  etc. — child 1 doesn't post anything yet, but child 2/3 will need them.

**Done when:** a CI run on a test PR shows the spec-tree plugin install step
exiting 0 and the reachability check reporting `reviewing-changes` and
`changes-reviewer` as present. The reviewer is not invoked; the job exits 0;
no PR comment is posted by the new workflow.

### Child 2 — full chain runs; post `review.md` as a plain comment

**Goal:** the skill produces both artifacts in a throwaway directory; the
workflow reads the rendered `review.md` and posts it as a plain PR comment —
the same surface the inline-prompt workflow uses today, and the correct
end-state surface for a reviewer that does not decide. `review-result.json`
is read for its findings (child 3 uses each finding's `file`/`line` for
inline placement); it is never turned into a verdict.

**Workflow-side work:**

- Fetch the base ref so `git diff <base>...HEAD` works. `compute_diff.py`
  runs a three-dot, merge-base diff (`<base>...<head>`, per
  `reviewing-changes` D2), so the merge-base commit must be present locally.
  The existing `actions/checkout@v6` step at line 275 uses `fetch-depth: 1` —
  change to `fetch-depth: 0` (or run `git fetch origin ${{ github.base_ref }}`
  as a separate step). A shallow checkout lacks the merge-base and breaks the
  diff.
- Export the env contract the skill expects, via the existing
  `additional_env` plumbing (or a dedicated step):
  - `SPX_VERIFY_BASE_REF=origin/${{ github.base_ref }}`
  - `SPX_VERIFY_HEAD_REF=HEAD` (or `origin/${{ github.head_ref }}`)
  - `SPX_VERIFY_BRANCH=${{ github.head_ref }}`
  - `SPX_VERIFY_LOCAL_ROOT=${{ runner.temp }}/spx-review` (throwaway —
    runner temp is wiped between jobs)
- Inline prompt becomes: "Invoke `spec-tree:changes-reviewer` with input
  `#${{ github.event.pull_request.number }}`. After the skill chain
  completes, read the rendered `review.md` from the thread store via the
  thread-store read CLI (`read_record.py`) and post it as a PR comment via
  `gh pr comment --body-file -`."
- Read through the thread-store CRUD CLI, not by cat-ing the backend path.
  `read_record.py` makes `--slug` optional and auto-derives it from
  `SPX_VERIFY_BRANCH` (per the thread-store contract), so the workflow never
  names the on-disk addressing scheme. A direct `${SPX_VERIFY_LOCAL_ROOT}/
  <slug>/review.md` read couples the workflow to the filesystem backend's
  path layout and breaks the backend-pluggability rule in `verification.md`
  (and the anticipated `gh_pr` backend). The slug derivation itself lives in
  `plugins/plugins/spec-tree/skills/thread-store/scripts/branch_slug.py`,
  re-exported through `thread_store.current_slug()` — the workflow does not
  reimplement it.
- Keep the comment-posting allowlist patterns from the baseline; they
  cover what child 2 needs.
- Compare outputs: for each PR the workflow runs on, the new workflow's
  comment and the existing workflow's comment should sit side-by-side on
  the PR thread. Treat this as the qualitative regression test while both
  run in parallel. (We're not aiming for byte-equivalence; we're checking
  that the skill-driven path catches roughly the same defects.)

**Done when:** on a test PR, both workflows run; the new workflow posts a
comment whose content was produced by the skill chain, and the JSON
artifact is not persisted past the job.

### Child 3 — add inline comments to the COMMENT review

**Goal:** keep child 2's surface — a GitHub **COMMENT** review — and enrich
it with inline comments placed on the diff lines each finding cites. The
event is always `COMMENT`; the reviewer reviews, it does not decide. No
`APPROVE`/`REQUEST_CHANGES`, no `decision` consumption, no decision→event
mapping. This child is **additive** to child 2, not a replacement.

**Workflow-side work:**

- Post one GitHub COMMENT review via
  `gh api repos/${OWNER}/${REPO}/pulls/${PR}/reviews --input -` with
  `event: COMMENT`. The review `body` is the rendered `review.md` (read via
  `read_record.py`, as in child 2). The `comments[]` array carries one entry
  per finding whose `file`/`line` falls inside a diff hunk — `Finding` carries
  structured `file: str` and `line: int`, so the placement is mechanical.
  Findings whose `file`/`line` lie outside the diff (GitHub 422s an inline
  comment off-diff) stay in the body alongside the summary.
- `event: COMMENT` is allowed on the author's own PR, so there is no
  self-review (422) case to guard — unlike `APPROVE`/`REQUEST_CHANGES`.
- The inline-placement transform (matching findings against diff hunks,
  building the `comments[]` payload) is GitHub-specific and stays
  workflow-side. The skill remains platform-neutral — it knows nothing about
  GitHub review events — and emits only `review.md` plus the findings in
  `review-result.json`. No new skill script (`render_github_review.py`) and
  no skill-side ADR amendment to the closed script set: the platform mapping
  does not belong in the platform-neutral skill.
- Permissions: posting a COMMENT review with inline comments requires
  `pull-requests: write` (already granted). The `id-token: write` and
  `actions: read` grants remain for the action's other needs.
- Allowlist additions: `Bash(gh api:*)` for the reviews POST.
- Do NOT remove child 2's comment step — child 3 enhances the same COMMENT
  surface with inline placement; it does not introduce a different surface.
- Swap question: at the end of child 3, decide whether the
  `spec-tree-review-skill.yml` workflow should replace `spec-tree-review.yml`.
  Track that decision as a follow-up node in the spec, not as part of this
  decomposition.

**Done when:** on a test PR, the new workflow posts a single COMMENT review
whose body contains the summary and every off-diff finding, with an inline
review comment on each finding whose `file`/`line` falls inside the PR diff.
No `APPROVE`/`REQUEST_CHANGES` event is ever emitted; no `decision` is read.

## Coordination with the plugins plan

The spec node + three child nodes are authored in the plugins repo session
(see `outcomeeng/plugins/PLAN-review-skill-from-ci.md`). This session
implements the workflow side only.

Per-child landing order:

1. The plugins-side change lands first (skill is callable, env contract
   stable). Child 3 needs no plugins-side transformation helper — the
   GitHub COMMENT-review payload, including inline-comment placement against
   the diff, is built workflow-side from `review.md` and the findings.
2. This session pins the workflow to the merged plugins commit and lands
   the workflow change.
3. End-to-end verification fires on a real PR in a consumer repo
   (`leoherd` is the easiest target).

The Open architectural question above is owned by the plugins session.
Wait for that decision before starting child 1 here — its answer changes
how much of this plan is durable work versus transitional scaffolding.

## What to do first in this session

1. Read the canonical PDR path from the plugins session (the user will
   paste it). All workflow-side work in this session cites this PDR.
2. Read the spec node path that the plugins session produced. The 3
   children of that node govern the per-child workflow changes here.
3. **Update `README.md` and/or `AGENTS.md`** with a one-paragraph
   "Governing decisions" reference pointing at the canonical PDR. Land
   this in a small PR before the workflow work begins so the rule has
   a home in this repo from day one.
4. `/contextualizing` against this repo to find any existing spec
   material that governs the workflow file (likely none — this repo has
   no `spx/` tree; the governing specs live in `plugins/spx/`).
5. Read `spx/spx/46-reviewing.enabler/reviewing.md` and its child
   enablers (`21-review-config.enabler/`,
   `32-hermetic-review-execution.enabler/`, `43-review-state.enabler/`,
   `54-branch-review.enabler/`, `65-pr-review.enabler/`) so the workflow
   stays consistent with how `spx review` will eventually behave.
6. Set up the new `spec-tree-review-skill.yml` file as a copy of the
   existing workflow, with the inputs and inline prompt swapped per
   child 1.
7. Open a workflow-only PR in a test consumer repo (e.g. `leoherd`) to
   wire up the new workflow. Wait for that to merge to default before
   landing the verify PR — the `validate-workflow` gate enforces this.

## Out of scope for this session

- Any changes under `outcomeeng/plugins/` — those are in the mirror plan.
- Authoring the spec node itself — that happens in the plugins session
  where the spec tree lives.
- Modifying or deleting `spec-tree-review.yml`. The existing workflow
  stays in place; the new one runs alongside it through all three
  children. A separate decommission node, authored after child 3 lands,
  decides the swap.
- Implementing `spx review pr <n>` itself. That's separate work in the
  spx CLI's spec tree (`spx/spx/46-reviewing.enabler/`), governed by
  its own PLAN.md.

## Source material for the next session

- `outcomeeng/gh-actions/.github/workflows/spec-tree-review.yml` — read in
  full. The plugin-install logic (lines 280–346), allowlist composition
  (lines 348–409), and additional-env plumbing (lines 411–442) are all
  reusable as-is. The inline prompt (lines 464–584) is what the new
  workflow replaces with a one-liner.
- The plugins repo's `plugins/plugins/spec-tree/agents/changes-reviewer.md`
  and `plugins/plugins/spec-tree/skills/reviewing-changes/SKILL.md` —
  reference the input contract (env vars) and the skill chain so the
  workflow exports the right variables and reads the right artifacts.
- The spx CLI's `spx/spx/46-reviewing.enabler/` subtree — the Review-layer
  spec the workflow should stay compatible with.
- The two-run comparison on `leoherd` PR #287 from the originating
  conversation, if the user can paste it. The `request_changes`↔`approve`
  flip is the evidence that the reviewer was emitting a verdict it should
  not — useful in the spec node's `Why` section to motivate both the
  single-source refactor and the reviewer-reviews-author-decides model.
