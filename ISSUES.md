# ISSUES

Known issues against the reusable workflows and their example caller templates. Each entry names the artifact, the constraint, the evidence that surfaced it, and a proposed handling.

Following the spec-tree methodology, this file records quality observations against the repository rather than opening GitHub Issues for them, and it is also where a review finding goes when the author defers it. Severity is the reviewer's judgment of what a finding is; whether it is fixed in the pull request or recorded here is the author's disposition. A deferred finding reaches this file only when its fix is a separate, larger concern, and that entry names why — an observation recorded outside a review carries no severity and needs no such reason. Entries persist with the repo, are versioned with the change that introduced them, and remain visible during subsequent reviews. Entries are pruned (not marked "resolved") once the underlying issue no longer exists in the code — git history retains the record of the fix.

## Open

### README generic Claude variable tables

Evidence: `README.md` states that the generic Claude examples mirror the spec-tree repo-variable shape with `vars.CLAUDE_*` and `vars.CLAUDE_REVIEW_*`, but the README only provides full lookup tables for `SPEC_TREE_*` and `SPEC_TREE_REVIEW_*`.

Impact: Downstream callers can still use the examples directly, but readers must open `examples/caller-workflows/claude.yml` or `examples/caller-workflows/claude-code-review.yml` to discover the generic Claude variable names.

Handling: Add `CLAUDE_*` and `CLAUDE_REVIEW_*` tables to README "Per-environment overrides via repo variables", mirroring the existing spec-tree tables.
