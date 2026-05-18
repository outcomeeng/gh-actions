# Outcome Engineering GitHub Actions

Reusable GitHub Actions workflows for Claude Code integration.

## Repository Structure

```
gh-actions/
├── .github/
│   ├── actions/
│   │   ├── apply-additional-env/         # Compose additional env JSON onto the action step
│   │   ├── compose-claude-args/          # Build the action's claude_args + allowlist
│   │   └── derive-claude-plugins/        # Resolve plugins from settings.json + inputs
│   ├── dependabot.yml                    # github-actions ecosystem updates
│   └── workflows/
│       ├── claude.yml                    # Reusable @claude mention handler
│       ├── claude-code-review.yml        # Reusable automatic PR review
│       ├── spec-tree.yml                 # Reusable mention wrapper with spec-tree defaults
│       ├── spec-tree-review.yml          # Reusable review wrapper with REVIEW.md-aware prompt
│       ├── claude-repo.yml               # Self-test caller (mention)
│       ├── claude-code-review-repo.yml   # Self-test caller (review)
│       ├── spec-tree-repo.yml            # Self-test caller (spec-tree mention)
│       └── spec-tree-review-repo.yml     # Self-test caller (spec-tree review)
├── examples/
│   └── caller-workflows/                 # Copy-paste templates for downstream repos
├── AGENTS.md                             # Cloud review guidance
├── CLAUDE.md                             # This file
└── README.md                             # User documentation
```

## Workflow Design Principles

1. **Reusable via `workflow_call`** - All workflows are designed to be called from other repos
2. **Sensible defaults** - Work out of the box with minimal configuration
3. **Security first** - Authorization checks prevent unauthorized access
4. **Configurable** - All behavior can be customized via inputs

## Making Changes

### Testing Changes

The `*-repo.yml` workflows in `.github/workflows/` are an in-repo self-test harness: each uses `uses: ./.github/workflows/<name>.yml` so a branch push exercises the reusables against this repository's own issues, comments, and PRs. Use this for fast-feedback testing; use an external test repo (steps below) to validate the `@<ref>` consumption path.

1. Push changes to a branch
2. Either (a) mention `@claude` on an issue or PR in this repo / open a PR (the `*-repo.yml` callers fire the reusables locally), or (b) update an external test repo to use `@branch-name` instead of `@main`
3. Trigger the workflow and verify behavior
4. Merge to main when satisfied

### Versioning

Use tags for stable versions:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Consumers can then use `@v1` for the latest v1.x.x.

## Security Considerations

- `CLAUDE_CODE_OAUTH_TOKEN` is passed as a secret, never exposed in logs
- Authorization checks use `author_association` to limit who can trigger
- Tool restrictions limit what Claude can do in the repo
