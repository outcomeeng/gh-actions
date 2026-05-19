# ISSUES

Known issues against the reusable workflows and their example caller templates. Each entry names the artifact, the constraint, the evidence that surfaced it, and a proposed handling.

Following the spec-tree methodology: FOLLOW-UP findings from PR reviews and other quality observations are recorded here rather than in GitHub Issues. Entries persist with the repo, are versioned with the change that introduced them, and remain visible during subsequent reviews.

## `trigger_phrase` audit-trail gap and whitespace footgun

Artifact: `examples/caller-workflows/spec-tree.yml`, `examples/caller-workflows/spec-tree-review.yml` — `trigger_phrase` input wired to `${{ vars.SPEC_TREE_TRIGGER_PHRASE || '@spec-tree' }}` (and the review variant).

Surfaced by: [outcomeeng/gh-actions#24](https://github.com/outcomeeng/gh-actions/pull/24) review (HEAD `345bb48`).

Concern: two distinct sub-issues with the same source.

1. **Audit-trail gap.** Repo-variable changes do not appear in git history. A workflow-file change to `trigger_phrase` would go through PR review; setting `vars.SPEC_TREE_TRIGGER_PHRASE` in repo Settings is a silent admin-only action with no diff. Risk is bounded by repo admin scope, but the gap is real.

2. **Whitespace footgun.** GitHub Actions expression `${{ vars.X || '@spec-tree' }}` returns the variable value when it is any non-empty string — including `' '` (single space). An admin who sets the variable to a whitespace-only value would cause `contains(comment.body, ' ')` to match nearly every authorized comment, firing the mention workflow silently and repeatedly until the misconfiguration is detected. The `||` fallback does not guard against this because whitespace is truthy in the expression language.

Proposed handling — both are valid; pick one or both:

- Doc-only: add a warning paragraph to the example template's `trigger_phrase:` comment block explaining the trade-off, and reproduce it in the README "Per-environment overrides via repo variables" subsection. Mitigates via awareness; does not eliminate the footgun.
- Behavioral: introduce a defensive expression that rejects whitespace-only values, e.g. wrap with `trim()`-equivalent logic in the reusable workflow (`if: contains(... ) && trim(inputs.trigger_phrase) != ''`) so a whitespace-only variable produces a clear authorize-job skip rather than a flood of fires. Requires changes in the reusable, not just the example.

Owner: open for whoever next touches the reusable workflows.

Tracked: this file. Do not duplicate to GitHub Issues.
