# Outcome Engineering GitHub Actions

Reusable GitHub Actions workflows for Claude Code integration.

## Available Workflows

| Workflow                      | Description                                                                                      |
| ----------------------------- | ------------------------------------------------------------------------------------------------ |
| `claude.yml`                  | Interactive Claude assistant triggered by `@claude` mentions                                     |
| `claude-code-review.yml`      | Automatic code review on pull requests                                                           |
| `spec-tree.yml`               | Stable-name mention wrapper for spec-tree consumers; calls `claude.yml`                          |
| `spec-tree-review.yml`        | Review wrapper with `REVIEW.md`-aware prompt and wider allowlist; calls `claude-code-review.yml` |
| `claude-repo.yml`             | Runs the mention workflow in this repository                                                     |
| `claude-code-review-repo.yml` | Runs PR review in this repository                                                                |
| `spec-tree-repo.yml`          | Runs the spec-tree mention workflow in this repository                                           |
| `spec-tree-review-repo.yml`   | Runs the spec-tree review workflow in this repository                                            |

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
```

**For automatic PR reviews** - create `.github/workflows/claude-code-review.yml`:

```yaml
name: Claude Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  issues: write
  id-token: write

jobs:
  review:
    uses: outcomeeng/gh-actions/.github/workflows/claude-code-review.yml@main
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
```

**For spec-tree variants** — copy `examples/caller-workflows/spec-tree.yml` (mention) and/or `examples/caller-workflows/spec-tree-review.yml` (review) into `.github/workflows/` in your repository. They share the same shape as the two examples above but call the spec-tree wrappers; the example files inline-document every override worth knowing.

## Configuration

### claude.yml Inputs

| Input                 | Default       | Description                                                                                                  |
| --------------------- | ------------- | ------------------------------------------------------------------------------------------------------------ |
| `runner`              | `ubuntu-slim` | Runner selection. Single label (`ubuntu-latest`, `self-hosted`) or JSON array (`'["self-hosted","laptop"]'`) |
| `trigger_phrase`      | `@claude`     | Text that triggers the workflow (also forwarded to the action)                                               |
| `concurrency_cancel`  | `true`        | Cancel in-progress runs on new mention                                                                       |
| `custom_prompt`       | (empty)       | Override default behavior with a custom prompt                                                               |
| `model`               | (empty)       | Claude model id (e.g. `claude-opus-4-7`); folded into `claude_args` as `--model`. Empty = action default     |
| `claude_args`         | (empty)       | Extra Claude Code CLI args (e.g. `--max-turns 20 --allowed-tools "Bash(gh pr comment:*)"`)                   |
| `use_bedrock`         | `false`       | Route Claude through Amazon Bedrock (caller handles AWS auth via `additional_env`)                           |
| `use_vertex`          | `false`       | Route Claude through Google Vertex AI (caller handles GCP auth via `additional_env`)                         |
| `additional_env`      | `{}`          | JSON object string of env vars set on the claude-code-action step                                            |
| `use_project_plugins` | `false`       | Install plugins and marketplaces from the caller's `.claude/settings.json` (see section below)               |
| `plugin_marketplaces` | (empty)       | Space-separated marketplaces to register (`owner/repo`); appends to project list when opted in               |
| `extra_plugins`       | (empty)       | Space-separated plugins to install; appends to project list when opted in                                    |
| `show_full_output`    | `false`       | Stream full per-turn Claude JSON to the job log (debug only — may expose secrets in tool output)             |
| `timeout_minutes`     | `"15"`        | Wall-clock budget (minutes) for the Run Claude Code step; cancels the step when exceeded (minimum 1)         |

### claude-code-review.yml Inputs

| Input                 | Default                 | Description                                                                                                         |
| --------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `runner`              | `ubuntu-slim`           | Runner selection. Single label or JSON array (see `claude.yml`)                                                     |
| `trigger_phrase`      | `@claude`               | Trigger phrase forwarded to the action (review wrappers do not use this to gate the run)                            |
| `concurrency_cancel`  | `true`                  | Cancel in-progress reviews on new PR update                                                                         |
| `custom_prompt`       | (default review prompt) | Replace the default review prompt                                                                                   |
| `model`               | (empty)                 | Claude model id; folded into `claude_args` as `--model`. Empty = action default                                     |
| `claude_args`         | (empty)                 | Extra Claude Code CLI args OTHER than `--allowed-tools` (use `append_allow_list` / `override_allow_list` for tools) |
| `append_allow_list`   | (empty)                 | Comma-separated tool patterns appended to the wrapper's baseline `gh`-only allowlist                                |
| `override_allow_list` | (empty)                 | Comma-separated tool patterns that REPLACE the wrapper's baseline allowlist entirely                                |
| `use_bedrock`         | `false`                 | Route Claude through Amazon Bedrock                                                                                 |
| `use_vertex`          | `false`                 | Route Claude through Google Vertex AI                                                                               |
| `additional_env`      | `{}`                    | JSON object string of env vars set on the claude-code-action step                                                   |
| `use_project_plugins` | `false`                 | Install plugins and marketplaces from the caller's `.claude/settings.json` (see section below)                      |
| `plugin_marketplaces` | (empty)                 | Space-separated marketplaces to register (`owner/repo`); appends to project list when opted in                      |
| `extra_plugins`       | (empty)                 | Space-separated plugins to install; appends to project list when opted in                                           |
| `show_full_output`    | `false`                 | Stream full per-turn Claude JSON to the job log (debug only — may expose secrets in tool output)                    |
| `timeout_minutes`     | `"15"`                  | Wall-clock budget (minutes) for the Run Claude Code Review step (minimum 1)                                         |

`spec-tree.yml` is a transparent pass-through to `claude.yml` — every input default is identical, and the wrapper exists only to give spec-tree consumers a stable name that won't drift if the generic mention defaults change. `spec-tree-review.yml` is behaviorally distinct from `claude-code-review.yml`: it bakes in a `REVIEW.md`-aware review prompt (so `custom_prompt` is not exposed as an input) and extends the baseline allowlist with `Bash(sed:*),Bash(grep:*),Bash(head:*)`. Every other shared input forwards through with the base's default.

## Plugins and marketplaces

The reusable workflows install plugins from two possible sources:

1. **Caller workflow inputs** (`extra_plugins`, `plugin_marketplaces`) — always applied.
2. **The caller repository's `.claude/settings.json`** (`enabledPlugins`, `extraKnownMarketplaces`) — only when `use_project_plugins: true`.

### Default: project plugins are NOT installed

`use_project_plugins` defaults to `false`. The review job and the mention job run with no project plugins. The reason is plugin skills: most non-trivial plugins ship skills with `ALWAYS invoke this skill before X` mandates that pull Claude into tools (`Read`, `Grep`, `Glob`, `Bash(git ...)`) that aren't on the wrapper's baked-in `gh`-only allowlist. The result is a run that spends turns on permission denials and never posts a review comment.

If the caller's `.claude/settings.json` exists while `use_project_plugins` is false, the workflow emits a `::notice::` saying the file is being ignored and how to opt in. To install specific plugins without enabling the whole `.claude/settings.json` set, list them in `extra_plugins` and their marketplaces in `plugin_marketplaces`.

### Opting in to project plugins

Set `use_project_plugins: true` in the caller workflow. Plugin keys in `enabledPlugins` use the form `name@marketplace-alias`; the alias must resolve to a marketplace source. The canonical place to declare the alias → source mapping is `extraKnownMarketplaces` inside the same `.claude/settings.json`, so the same file drives both local development and CI:

```json
{
  "enabledPlugins": {
    "github@claude-plugins-official": true,
    "rust@outcomeeng": true
  },
  "extraKnownMarketplaces": {
    "claude-plugins-official": {
      "source": { "source": "github", "repo": "anthropics/claude-plugins-official" }
    },
    "outcomeeng": {
      "source": { "source": "github", "repo": "outcomeeng/plugins", "ref": "main" }
    }
  }
}
```

When opted in, `enabledPlugins` keys flow into the action's `plugins` input and each `extraKnownMarketplaces` entry's `source.repo` becomes a `https://github.com/<repo>.git` URL passed as `plugin_marketplaces`. Only `source.source: "github"` entries are emitted; pin a ref via `source.ref` (Claude Code reads it during install).

Caller-supplied `extra_plugins` and `plugin_marketplaces` inputs append to the project-declared lists when opted in, and are the sole source when opted out — useful for CI-only additions without touching the project file.

Whenever you widen the plugin set for review or mention runs, widen the allowlist to match via `append_allow_list` (on the review workflow) or `claude_args` (on the mention workflow). Otherwise the same permission-denial spiral that motivated the opt-in default will surface again.

## Authorization

Each reusable workflow has a small `authorize` job that queries `repos/{owner}/{repo}/collaborators/{actor}/permission` and the `claude-review` / `claude` job runs only when the actor's effective permission is `admin`, `maintain`, or `write`. Permission flows through team and org membership, so trusted org members are authorized without extra configuration. External contributors (including PRs from forks) come back as `none` (or 404), and the review job is `skipped` (gray check on the PR), not failed — so an unauthorized PR doesn't show a red X.

If you (an admin/maintainer) want Claude to review a PR opened by a non-collaborator, comment `@claude` on the PR. That triggers `claude.yml` from the `issue_comment` event with you as the actor; the API check sees your write permission and the action runs with the PR context.

`claude-code-review.yml` also has a `validate-workflow` job that compares the caller workflow file at the PR head to the default branch and skips the review with a clear notice if they differ. This pre-empts the Anthropic action's `Workflow validation failed` error in the two common cases — first installs where the workflow file isn't on the default branch yet, and PRs that modify a `.github/workflows/claude*.yml` file. Merge the workflow change to the default branch first, then later PRs are reviewed automatically.

The earlier `author_association` gating relied on the webhook field of the same name, which sometimes reported `NONE` or `CONTRIBUTOR` for legitimately-trusted org members and forced callers to expand the allowlist in unsafe ways. The `authorized_roles` input is no longer declared on either reusable; if a caller still passes it under `with:`, GitHub Actions rejects the workflow call with a clear "unexpected input" error. Remove it from caller `with:` blocks.

If you need to allow specific external accounts, gate at the caller side: route mentions through the mention workflow with an `if:` that lists trusted usernames, or use a separate manual trigger.

```yaml
on:
  issue_comment:
    types: [created]

jobs:
  claude:
    # Replace alice and bob with trusted accounts not on the repo's collaborators list.
    if: github.event.issue.pull_request && contains(fromJSON('["alice", "bob"]'), github.actor)
    uses: outcomeeng/gh-actions/.github/workflows/claude.yml@main
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
    with:
      trigger_phrase: "/review"
      custom_prompt: "Review this pull request."
```

## Common gotchas

One non-obvious behavior still surfaces during real installs.

### Same-repo branches created before the workflow existed won't trigger it

For `pull_request` events from a branch in the same repository (not a fork), GitHub Actions reads the workflow definition from the **PR head**, not from the base. A PR branched off `main` *before* the workflow files existed will not trigger the workflow even after they merge, until the branch is rebased or merged with `main`.

Use `gh pr checks <pr-number>` first to see whether GitHub scheduled the workflow. If the `Claude Code Review` check never appears in the PR's Checks tab after adding the workflow files to `main`, check whether the workflow file exists on the PR branch:

```bash
git fetch origin <pr-branch>
git ls-tree origin/<pr-branch> .github/workflows/
```

If the workflow file you need isn't listed, merge `main` into the PR branch:

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

Both workflows include authorization checks. The `authorize` job queries `repos/{owner}/{repo}/collaborators/{actor}/permission` and the downstream Claude job runs only when the actor's effective permission is `admin`, `maintain`, or `write` — see [Authorization](#authorization) for the full mechanism and the rationale for replacing the earlier `author_association` gate.

**Best practices:**

- Keep `use_project_plugins` off (the default) unless the project plugins are appropriate for review or mention runs, and widen the allowlist (`append_allow_list` / `override_allow_list` on review, `claude_args` on mention) to match the tools those plugins' skills demand
- Narrow `claude_args` (mention) or `append_allow_list` / `override_allow_list` (review) to the minimum the workflow needs; the review wrapper's baked-in allowlist covers `gh issue`/`gh pr` read and `gh pr comment`
- Never set `self-hosted` runner labels on public repos or repos that accept PRs from untrusted forks (the runner host is shared across runs)
- Rotate `CLAUDE_CODE_OAUTH_TOKEN` if compromise is suspected

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
