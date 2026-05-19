# ISSUES

Known issues against the reusable workflows and their example caller templates. Each entry names the artifact, the constraint, the evidence that surfaced it, and a proposed handling.

Following the spec-tree methodology: FOLLOW-UP findings from PR reviews and other quality observations are recorded here rather than in GitHub Issues. Entries persist with the repo, are versioned with the change that introduced them, and remain visible during subsequent reviews. Entries are pruned (not marked "resolved") once the underlying issue no longer exists in the code — git history retains the record of the fix.

## Open

### FOLLOW-UP [docs]: README generic Claude variable tables

Evidence: `README.md` states that the generic Claude examples mirror the spec-tree repo-variable shape with `vars.CLAUDE_*` and `vars.CLAUDE_REVIEW_*`, but the README only provides full lookup tables for `SPEC_TREE_*` and `SPEC_TREE_REVIEW_*`.

Impact: Downstream callers can still use the examples directly, but readers must open `examples/caller-workflows/claude.yml` or `examples/caller-workflows/claude-code-review.yml` to discover the generic Claude variable names.

Handling: Add `CLAUDE_*` and `CLAUDE_REVIEW_*` tables to README "Per-environment overrides via repo variables", mirroring the existing spec-tree tables.
