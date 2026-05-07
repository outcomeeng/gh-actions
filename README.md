# Outcome Engineering GitHub Actions

Reusable GitHub Actions workflows for Claude Code integration.

## Available Workflows

| Workflow                      | Description                                                  |
| ----------------------------- | ------------------------------------------------------------ |
| `claude.yml`                  | Interactive Claude assistant triggered by `@claude` mentions |
| `claude-code-review.yml`      | Automatic code review on pull requests                       |
| `claude-repo.yml`             | Runs the mention workflow in this repository                 |
| `claude-code-review-repo.yml` | Runs PR review in this repository                            |

## Quick Start

### 1. Set up secrets

Add `CLAUDE_CODE_OAUTH_TOKEN` to your repository secrets. See [Pushing Secrets](#pushing-secrets) below for an automated approach.

### 2. Create workflow files

**For `@claude` mentions** - create `.github/workflows/claude.yml`:

```yaml
name: Claude Code

on:
  issue_comment:
    types: [created, edited]
  pull_request_review_comment:
    types: [created, edited]
  issues:
    types: [opened, assigned]
  pull_request_review:
    types: [submitted]

permissions:
  contents: read
  pull-requests: write
  issues: write
  id-token: write
  actions: read

jobs:
  claude:
    uses: outcomeeng/gh-actions/.github/workflows/claude.yml@main
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
    with:
      authorized_roles: '["OWNER", "MEMBER", "COLLABORATOR"]'
      mention_trigger: "@claude"
```

**For automatic PR reviews** - create `.github/workflows/claude-code-review.yml`:

```yaml
name: Claude Code Review

on:
  pull_request:
    types: [opened, synchronize]

permissions:
  contents: read
  pull-requests: read
  issues: read
  id-token: write

jobs:
  review:
    uses: outcomeeng/gh-actions/.github/workflows/claude-code-review.yml@main
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
    with:
      authorized_roles: '["OWNER", "MEMBER", "COLLABORATOR"]'
```

## Configuration

### claude.yml Inputs

| Input                 | Default                               | Description                                                       |
| --------------------- | ------------------------------------- | ----------------------------------------------------------------- |
| `authorized_roles`    | `["OWNER", "MEMBER", "COLLABORATOR"]` | JSON array of GitHub author associations allowed to trigger       |
| `mention_trigger`     | `@claude`                             | Text that triggers the workflow                                   |
| `concurrency_cancel`  | `true`                                | Cancel in-progress runs on new mention                            |
| `allowed_tools`       | (unrestricted)                        | Claude Code `--allowed-tools` argument                            |
| `custom_prompt`       | (empty)                               | Override default behavior with custom prompt                      |
| `plugin_marketplaces` | `outcomeeng/plugins@main`             | Space-separated marketplaces to register (`owner/repo[@ref]`)     |
| `extra_plugins`       | (empty)                               | Space-separated plugins to install beyond `.claude/settings.json` |
| `skip_plugin_install` | `false`                               | Set `true` for repos that don't use the plugin marketplace        |

### claude-code-review.yml Inputs

| Input                 | Default                               | Description                                                       |
| --------------------- | ------------------------------------- | ----------------------------------------------------------------- |
| `authorized_roles`    | `["OWNER", "MEMBER", "COLLABORATOR"]` | JSON array of GitHub author associations allowed                  |
| `concurrency_cancel`  | `false`                               | Cancel in-progress reviews on new PR update                       |
| `allowed_tools`       | (gh read/comment only)                | Claude Code `--allowed-tools` argument                            |
| `custom_prompt`       | (default review prompt)               | Custom review instructions                                        |
| `plugin_marketplaces` | `outcomeeng/plugins@main`             | Space-separated marketplaces to register (`owner/repo[@ref]`)     |
| `extra_plugins`       | (empty)                               | Space-separated plugins to install beyond `.claude/settings.json` |
| `skip_plugin_install` | `false`                               | Set `true` for repos that don't use the plugin marketplace        |

## Common gotchas

Three non-obvious behaviors surfaced during real installs. Knowing about them in advance saves debugging time.

### `pull_request.author_association: NONE` for forked-repo PRs

When a PR is opened from a branch in a **forked** repository (the kind GitHub creates with the "Fork" button), the `pull_request` event payload reports `author_association: NONE` for users who are not trusted on the target repository. This is expected, but it can surprise maintainers who expected `COLLABORATOR` or `MEMBER` based on organization context.

After an external contributor has a PR merged, later PRs can report `CONTRIBUTOR`. Treat that as external trust too unless you explicitly want previous contributors to trigger reviews.

The reusable workflow's `if:` gate is:

```yaml
if: contains(fromJSON(inputs.authorized_roles), github.event.pull_request.author_association)
```

If `NONE` isn't in your `authorized_roles`, the auto-review job skips silently. The job appears in Actions with `conclusion: skipped` and no log lines.

**Safer workaround:** keep forked PRs from external contributors out of automatic `pull_request` review. Trigger those reviews from a trusted maintainer path instead, such as `workflow_dispatch`, an `issue_comment` trigger that checks the comment author, or a `pull_request_review` trigger that checks the reviewer. For example, a caller can route manual review comments through the mention workflow:

```yaml
on:
  issue_comment:
    types: [created]

jobs:
  claude:
    # Replace your-github-username with the trusted maintainer account.
    if: github.event.issue.pull_request && contains(fromJSON('["your-github-username"]'), github.actor)
    uses: outcomeeng/gh-actions/.github/workflows/claude.yml@main
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
    with:
      mention_trigger: "/review"
      custom_prompt: "Review this pull request."
```

**Quick workaround:** add `NONE` to the explicit `authorized_roles` in the caller workflow, accepting that any PR opener can trigger the bot:

```yaml
with:
  authorized_roles: '["OWNER", "MEMBER", "COLLABORATOR", "NONE"]'
```

Avoid this shortcut in production unless another gate limits who can trigger the workflow, such as an environment requiring approval or a separate manual trigger.

### Workflow file at PR head must match `main` exactly

The Anthropic action (`anthropics/claude-code-action`) validates that the workflow file running on the PR exists on the repo's default branch with matching content. This is a security check: without it, a PR could modify the workflow and abuse the bot.

In practice this means:

- **Adding the workflow files for the first time:** the first PR that contains the workflow files starts the job, but the action logs `Skipping action due to workflow validation: ...` with `Workflow validation failed` and exits without posting a review. Expand the **Run anthropics/claude-code-action** step and search for `Workflow validation`. This is normal: the file isn't on `main` yet, so there's nothing to compare against. Merge that workflow-only PR first; subsequent PRs review correctly.
- **Updating the workflow:** any PR that modifies `.github/workflows/claude*.yml` will fail the same check until the change is on `main`. Land workflow changes via a separate PR (no other content) so the bot run isn't blocked on unrelated review.

### Workflow never triggers on a branch created before the workflow existed

For `pull_request` events from a branch in the same repository (not a fork), GitHub Actions reads the workflow definition from the **PR head**, not from the base. A PR branched off `main` *before* the workflow files existed will not trigger the workflow even after they merge, until the branch is rebased or merged with `main`.

Use `gh pr checks <pr-number>` first, replacing `<pr-number>` with the actual PR number, to see whether GitHub scheduled the workflow. If the `Claude Code Review` check never appears in the PR's Checks tab after adding the workflow files to `main`, check whether the workflow file exists on the PR branch:

```bash
git fetch origin <pr-branch>
git ls-tree origin/<pr-branch> \
  .github/workflows/claude-code-review.yml \
  .github/workflows/claude.yml
```

If the workflow file you need isn't there, merge `main` into the PR branch:

```bash
git fetch origin main
git merge origin/main
```

Or rebase the branch:

```bash
git fetch origin main
git rebase origin/main
```

## Security

Both workflows include authorization checks. Only users with matching `author_association` can trigger Claude workflows.

**Best practices:**

- Never allow `CONTRIBUTOR` or `FIRST_TIME_CONTRIBUTOR` in production
- Restrict `allowed_tools` to minimum required
- Rotate tokens if compromise is suspected

## OpenAI Cloud Code Review

This repository includes `AGENTS.md` review guidance for OpenAI cloud code review. The repo-side setup is the instruction file; the review service still has to be enabled in ChatGPT settings.

To enable reviews:

1. Set up a cloud environment for `outcomeeng/gh-actions` in [ChatGPT environment settings](https://chatgpt.com/codex/settings/environments).
2. Open [code review settings](https://chatgpt.com/codex/settings/code-review).
3. Turn on code review for this repository.
4. Request a review from a pull request comment with `@codex review`, or turn on automatic reviews in the same settings page.

The reviewer reads `AGENTS.md` and applies the closest instruction file to each changed file. Keep the top-level review guidance current when workflow validation, security expectations, or example conventions change.

## Pushing Secrets

Setting `CLAUDE_CODE_OAUTH_TOKEN` in each repository is tedious. The `push-secrets.py` script automates this by:

1. Reading the secret value from your **macOS Keychain** (no manual input needed)
2. Finding the current GitHub repository from `git`
3. Checking that the Claude workflow is installed
4. Pushing the secret to that repository via `gh secret set`

### Prerequisites

- macOS (for Keychain integration)
- `gh` CLI authenticated (`gh auth login`)
- `uv` for running the script

### Usage

```bash
# Run from any subdirectory of the target repository.

# Check whether the current repository has the secret
uv run /path/to/gh-actions/scripts/push-secrets.py check

# Push secrets (reads from Keychain automatically)
uv run /path/to/gh-actions/scripts/push-secrets.py push
```

The target repository is the Git repository where you run the command.
If the repository does not have the Claude workflow installed, the script prints the setup URL for this repository.
It exits without reading or pushing secrets.

### How Keychain Integration Works

The script uses macOS `security` CLI to read from your login keychain:

```bash
security find-generic-password -s "Claude Code-credentials" -a "$USER" -w
```

It expects that keychain item to contain JSON with `claudeAiOauth.accessToken`.
On first run, macOS will prompt you to allow access. Click "Always Allow" to avoid future prompts.

If the keychain lookup fails, the script falls back to prompting for the value.

## License

MIT
