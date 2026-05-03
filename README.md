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

Two non-obvious behaviors hit during real installs. Knowing about them in advance saves debugging time.

### `pull_request.author_association: NONE` for forked-repo PRs

When a PR is opened from a branch in a **forked** repository (the kind GitHub creates with the "Fork" button), the `pull_request` event payload reports `author_association: NONE` even when the GitHub API returns `MEMBER` for the same user querying the same PR.

The reusable workflow's `if:` gate is:

```yaml
if: contains(fromJSON(inputs.authorized_roles), github.event.pull_request.author_association)
```

If `NONE` isn't in your `authorized_roles`, the auto-review job skips silently. The job appears in Actions with `conclusion: skipped` and no log lines.

**Workaround:** add `NONE` to the explicit `authorized_roles` in the caller workflow, accepting that any PR opener can trigger the bot:

```yaml
with:
  authorized_roles: '["OWNER", "MEMBER", "COLLABORATOR", "CONTRIBUTOR", "NONE"]'
```

A more secure fix would gate on `github.actor` against a named user allowlist instead. That's a future enhancement to the reusable workflow itself.

### Workflow file at PR head must match `main` exactly

The Anthropic action (`anthropics/claude-code-action`) validates that the calling workflow file at the PR's head ref is byte-identical to the version on the repo's default branch. This is a security check — without it, a PR could modify the workflow and abuse the bot.

In practice this means:

- **Adding the workflow files for the first time:** the first PR that contains the workflow files gets a 401 "Workflow validation failed" from the action. This is normal — the file isn't on `main` yet, so there's nothing to compare against. Once the PR merges, subsequent PRs review correctly.
- **Updating the workflow:** any PR that modifies `.github/workflows/claude*.yml` will fail the same check until the change is on `main`. Land workflow changes via a separate PR (no other content) so the bot run isn't blocked on unrelated review.

### For same-repo PRs, GitHub reads the workflow from the head ref

For `pull_request` events from a branch in the same repository (not a fork), GitHub Actions reads the workflow definition from the **PR head**, not from the base. A PR branched off `main` *before* the workflow files existed will not trigger the workflow even after they merge — until the branch is rebased or merged with `main`.

If you see `Claude Code Review` runs with `conclusion: skipped` on a PR right after adding the workflow files, check whether the workflow file exists on the PR branch:

```bash
git ls-tree origin/<pr-branch> .github/workflows/
```

If `claude-code-review.yml` isn't there, merge `main` into the PR branch (or rebase) to bring it in.

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
