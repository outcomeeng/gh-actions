# Outcome Engineering GitHub Actions

Reusable GitHub Actions workflows for Claude Code integration.

## Available Workflows

| Workflow                                          | Description                                                                                           |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `spec-tree.yml`                                   | `@spec-tree` mention handler — fires on issues, PRs, and review comments                              |
| `spec-tree-review.yml`                            | PR review with `REVIEW.md`-aware prompt and an allowlist tuned for spec-tree's diff-chunking workflow |
| `spec-tree-repo.yml`, `spec-tree-review-repo.yml` | This repo's own callers for the reusables above — used as an in-repo self-test harness                |

## Quick Start

### 1. Set up secrets

Add `CLAUDE_CODE_OAUTH_TOKEN` to your repository secrets. See [Pushing Secrets](#pushing-secrets) below for an automated approach.

### 2. Create workflow files

**For `@spec-tree` mentions** — create `.github/workflows/spec-tree.yml`:

```yaml
name: Spec Tree

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
  spec-tree:
    # Pin to a full-length commit SHA — never @main or @v1. See "Security" below.
    uses: outcomeeng/gh-actions/.github/workflows/spec-tree.yml@eedf66bdd69dbe899a746374419d5a3cfbecfd25 # main
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
```

**For automatic PR reviews** — create `.github/workflows/spec-tree-review.yml`:

```yaml
name: Spec Tree Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  issues: write
  id-token: write
  actions: read

jobs:
  spec-tree-review:
    # Pin to a full-length commit SHA — never @main or @v1. See "Security" below.
    uses: outcomeeng/gh-actions/.github/workflows/spec-tree-review.yml@eedf66bdd69dbe899a746374419d5a3cfbecfd25 # main
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
```

For complete copy-paste templates with every override documented inline, see `examples/caller-workflows/spec-tree.yml` and `examples/caller-workflows/spec-tree-review.yml`.

## Configuration

### Mention workflow inputs (`spec-tree.yml`)

| Input                 | Default       | Description                                                                                                  |
| --------------------- | ------------- | ------------------------------------------------------------------------------------------------------------ |
| `runner`              | `ubuntu-slim` | Runner selection. Single label (`ubuntu-latest`, `self-hosted`) or JSON array (`'["self-hosted","laptop"]'`) |
| `trigger_phrase`      | `@spec-tree`  | Text that triggers the workflow (also forwarded to the action)                                               |
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

### Review workflow inputs (`spec-tree-review.yml`)

`spec-tree-review.yml` bakes in a `REVIEW.md`-aware review prompt and an allowlist tuned for diff-chunking (`Bash(gh ...)` plus `Bash(sed:*),Bash(grep:*),Bash(head:*)`). It does not expose `custom_prompt` — to extend or replace the allowlist, use `append_allow_list` / `override_allow_list`.

| Input                 | Default       | Description                                                                                                         |
| --------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------- |
| `runner`              | `ubuntu-slim` | Runner selection. Single label or JSON array (see mention table above)                                              |
| `trigger_phrase`      | `@spec-tree`  | Trigger phrase forwarded to the action (review does not use this to gate the run)                                   |
| `concurrency_cancel`  | `true`        | Cancel in-progress reviews on new PR update                                                                         |
| `model`               | (empty)       | Claude model id; folded into `claude_args` as `--model`. Empty = action default                                     |
| `claude_args`         | (empty)       | Extra Claude Code CLI args OTHER than `--allowed-tools` (use `append_allow_list` / `override_allow_list` for tools) |
| `append_allow_list`   | (empty)       | Comma-separated tool patterns appended to the baked-in baseline allowlist                                           |
| `override_allow_list` | (empty)       | Comma-separated tool patterns that REPLACE the baked-in baseline allowlist entirely                                 |
| `use_bedrock`         | `false`       | Route Claude through Amazon Bedrock                                                                                 |
| `use_vertex`          | `false`       | Route Claude through Google Vertex AI                                                                               |
| `additional_env`      | `{}`          | JSON object string of env vars set on the claude-code-action step                                                   |
| `use_project_plugins` | `false`       | Install plugins and marketplaces from the caller's `.claude/settings.json` (see section below)                      |
| `plugin_marketplaces` | (empty)       | Space-separated marketplaces to register (`owner/repo`); appends to project list when opted in                      |
| `extra_plugins`       | (empty)       | Space-separated plugins to install; appends to project list when opted in                                           |
| `show_full_output`    | `false`       | Stream full per-turn Claude JSON to the job log (debug only — may expose secrets in tool output)                    |
| `timeout_minutes`     | `"15"`        | Wall-clock budget (minutes) for the Run Claude Code Review step (minimum 1)                                         |

### Per-environment overrides via repo variables

Several inputs are commonly tuned per-environment (one repo runs on `self-hosted`, another on `ubuntu-latest`; one tolerates 15-minute reviews, another caps at 5; one opts in to project plugins, another doesn't). The example caller templates wire these inputs through GitHub Actions repository variables (`vars.*`) so you can flip them in repo Settings → Secrets and variables → Actions → Variables without editing the workflow file.

| Repo variable                          | Maps to               | Default if unset | Notes                                                                                          |
| -------------------------------------- | --------------------- | ---------------- | ---------------------------------------------------------------------------------------------- |
| `SPEC_TREE_RUNNER`                     | `runner` (mention)    | `ubuntu-slim`    | Single label or JSON-array string. `'["self-hosted","laptop"]'` is one literal string.         |
| `SPEC_TREE_REVIEW_RUNNER`              | `runner` (review)     | `ubuntu-slim`    | Same.                                                                                          |
| `SPEC_TREE_CONCURRENCY_CANCEL`         | `concurrency_cancel`  | `true`           | Set the string `'false'` to opt out of cancel-on-new. Anything else preserves cancel behavior. |
| `SPEC_TREE_REVIEW_CONCURRENCY_CANCEL`  | `concurrency_cancel`  | `true`           | Same, review side.                                                                             |
| `SPEC_TREE_TIMEOUT_MINUTES`            | `timeout_minutes`     | `'15'`           | Wall-clock budget in minutes (quoted string).                                                  |
| `SPEC_TREE_REVIEW_TIMEOUT_MINUTES`     | `timeout_minutes`     | `'15'`           | Same.                                                                                          |
| `SPEC_TREE_USE_PROJECT_PLUGINS`        | `use_project_plugins` | `false`          | Set the string `'true'` to opt in. Anything else (including unset) keeps the default off.      |
| `SPEC_TREE_REVIEW_USE_PROJECT_PLUGINS` | `use_project_plugins` | `false`          | Same; usually combined with widening `append_allow_list` to match the plugin's tool needs.     |

Inputs **not** gated via `vars.*` in the example: `trigger_phrase` (security-adjacent — explicit edit reviewed by maintainers is safer), `custom_prompt` (multi-line), `additional_env` (structured JSON), `use_bedrock` / `use_vertex` (only meaningful when paired with `additional_env` for cloud auth), and the plugin / allow-list lists (rarely change per-environment). Nothing prevents you from wiring those to `vars.*` too in your caller — the example just omits them to keep the template tight.

## Plugins and marketplaces

The reusable workflows install plugins from two possible sources:

1. **Caller workflow inputs** (`extra_plugins`, `plugin_marketplaces`) — always applied.
2. **The caller repository's `.claude/settings.json`** (`enabledPlugins`, `extraKnownMarketplaces`) — only when `use_project_plugins: true`.

### Default: project plugins are NOT installed

`use_project_plugins` defaults to `false`. The review job and the mention job run with no project plugins. The reason is plugin skills: most non-trivial plugins ship skills with `ALWAYS invoke this skill before X` mandates that pull Claude into tools (`Read`, `Grep`, `Glob`, `Bash(git ...)`) that aren't on the review workflow's baked-in `gh`-only allowlist. The result is a run that spends turns on permission denials and never posts a review comment.

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

Each reusable workflow has a small `authorize` job that queries `repos/{owner}/{repo}/collaborators/{actor}/permission` and the downstream job runs only when the actor's effective permission is `admin`, `maintain`, or `write`. Permission flows through team and org membership, so trusted org members are authorized without extra configuration. External contributors (including PRs from forks) come back as `none` (or 404), and the review job is `skipped` (gray check on the PR), not failed — so an unauthorized PR doesn't show a red X.

If you (an admin/maintainer) want a review on a PR opened by a non-collaborator, comment `@spec-tree` on the PR. That triggers the mention workflow from the `issue_comment` event with you as the actor; the API check sees your write permission and the action runs with the PR context.

`spec-tree-review.yml` also has a `validate-workflow` job that compares the caller workflow file at the PR head to the default branch and skips the review with a clear notice if they differ. This pre-empts the Anthropic action's `Workflow validation failed` error in the two common cases — first installs where the workflow file isn't on the default branch yet, and PRs that modify the `.github/workflows/spec-tree-review.yml` file itself. Merge the workflow change to the default branch first, then later PRs are reviewed automatically.

If you need to allow specific external accounts, gate at the caller side: route mentions through the mention workflow with an `if:` that lists trusted usernames, or use a separate manual trigger.

```yaml
on:
  issue_comment:
    types: [created]

jobs:
  spec-tree:
    # Replace alice and bob with trusted accounts not on the repo's collaborators list.
    if: github.event.issue.pull_request && contains(fromJSON('["alice", "bob"]'), github.actor)
    # Pin to a full-length commit SHA — never @main or @v1. See "Security" below.
    uses: outcomeeng/gh-actions/.github/workflows/spec-tree.yml@eedf66bdd69dbe899a746374419d5a3cfbecfd25 # main
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

This repository follows [GitHub's hardening guide for GitHub Actions](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions) and the OpenSSF baseline. The rules below apply to **both** this repository and any caller workflow that consumes one of its reusables.

### Pin everything by full-length commit SHA

Every `uses:` reference — actions and reusable workflows alike — is pinned by a full-length 40-character commit SHA. Tags (`@v1`, `@v1.2.3`) and branches (`@main`) are mutable references; an attacker who gains write access to the publishing repo can move them after release. A SHA is the only reference that cannot be redirected after the fact.

```yaml
# Correct
uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
uses: outcomeeng/gh-actions/.github/workflows/spec-tree.yml@eedf66bdd69dbe899a746374419d5a3cfbecfd25 # main

# Forbidden
uses: actions/checkout@v6
uses: outcomeeng/gh-actions/.github/workflows/spec-tree.yml@main
```

The trailing `# v6.0.2` / `# main` comment names the tag or branch the SHA tracks. Renovate uses that comment to know which upstream reference to follow when advancing the pin.

### Renovate keeps pins fresh

[Renovate](https://docs.renovatebot.com/) is the recommended update mechanism — Dependabot also supports SHA pinning, but Renovate's `helpers:pinGitHubActionDigests` preset handles both the SHA and the trailing comment in one pass and groups action updates intelligently. This repository's `renovate.json` is configured for the recommended baseline (`config:recommended` + the digest helper). Enable Renovate on your caller repo by installing the [Renovate GitHub App](https://github.com/apps/renovate) and copying a similar config:

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    "helpers:pinGitHubActionDigests"
  ],
  "vulnerabilityAlerts": { "enabled": true }
}
```

Running both Renovate and Dependabot against the same files produces conflicting PRs — pick one.

### Least-privilege `permissions:`

The reusable workflows (`spec-tree.yml`, `spec-tree-review.yml`) and `ci.yml` declare top-level `permissions: {}` and then grant per-job permissions explicitly. Caller workflows should declare top-level `permissions:` with the maximum the reusable needs. The quick-start examples list the exact permissions each reusable expects.

Grants visible in this repo's quick-start examples are the maximum a caller should declare; tighten further if your project doesn't need a given grant.

### Never leak secrets through `run:` blocks

Pass secrets via `with:` inputs (to the action) or via `env:` (when needed in a shell). Never `${{ secrets.X }}` directly inside a `run:` script — interpolation happens before the shell sees the line, which means a maliciously-crafted secret can break out of quoting. The same rule applies to user-controlled inputs (`github.event.*`, `inputs.*`).

### `actionlint` + `shellcheck` enforce these patterns

Both linters run on every push and PR via [`.github/workflows/ci.yml`](.github/workflows/ci.yml). They also run locally:

```bash
brew install just actionlint shellcheck   # macOS
# (Linux: apt-get install shellcheck; install actionlint per its release notes)

just check
```

`actionlint` flags unpinned actions, deprecated inputs, and shell-injection-prone interpolation; `shellcheck` audits inline `run:` scripts (and standalone shell files under `scripts/`).

### Authorization (this repo's reusables)

The `authorize` job in each reusable queries `repos/{owner}/{repo}/collaborators/{actor}/permission` and the downstream Claude job runs only when the actor's effective permission is `admin`, `maintain`, or `write` — see [Authorization](#authorization) for the full mechanism and the rationale for replacing the earlier `author_association` gate.

### Operational best practices

- Keep `use_project_plugins` off (the default) unless the project plugins are appropriate for review or mention runs, and widen the allowlist (`append_allow_list` / `override_allow_list` on review, `claude_args` on mention) to match the tools those plugins' skills demand.
- Narrow `claude_args` (mention) or `append_allow_list` / `override_allow_list` (review) to the minimum the workflow needs; the review workflow's baked-in allowlist covers `gh issue` / `gh pr` read, `gh pr comment`, and `sed` / `grep` / `head` for diff chunking.
- Never set `self-hosted` runner labels on public repos or repos that accept PRs from untrusted forks — the runner host is shared across runs.
- Rotate `CLAUDE_CODE_OAUTH_TOKEN` if compromise is suspected.

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
