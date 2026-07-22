# Outcome Engineering GitHub Actions

Reusable GitHub Actions workflows for Claude Code integration.

## Available Workflows

| Workflow                     | Description                                                                                           |
| ---------------------------- | ----------------------------------------------------------------------------------------------------- |
| `spec-tree.yml`              | `@spec-tree` mention handler — fires on issues, PRs, and review comments                              |
| `spec-tree-review.yml`       | PR review with `REVIEW.md`-aware prompt and an allowlist tuned for spec-tree's diff-chunking workflow |
| `spec-tree-verification.yml` | Preview verification host that runs a caller-selected spec-tree skill against a pull request          |
| `claude.yml`                 | `@claude` mention handler with the same self-contained implementation shape as `spec-tree.yml`        |
| `claude-code-review.yml`     | Generic Claude PR review with a compact prompt, `custom_prompt`, and a gh-only baseline allowlist     |
| `*-repo.yml`                 | This repo's own callers for the reusables above — used as an in-repo self-test harness                |

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
    # Release lane: pin to a full-length commit SHA — never @main or @v1. See "Security" below.
    uses: outcomeeng/gh-actions/.github/workflows/spec-tree.yml@a113491956c710dcdb7cb54174b4a52f9f6609d4 # main
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
```

**For automatic spec-tree PR reviews** — create `.github/workflows/spec-tree-review.yml`:

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
    # Release lane: pin to a full-length commit SHA — never @main or @v1. See "Security" below.
    uses: outcomeeng/gh-actions/.github/workflows/spec-tree-review.yml@a113491956c710dcdb7cb54174b4a52f9f6609d4 # main
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
```

**For spec-tree verification runs** — create `.github/workflows/spec-tree-verification.yml`:

```yaml
name: Spec Tree Verification

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: read

jobs:
  spec-tree-verification:
    # Release lane: pin to a full-length commit SHA — never @main or @v1. See "Security" below.
    uses: outcomeeng/gh-actions/.github/workflows/spec-tree-verification.yml@a113491956c710dcdb7cb54174b4a52f9f6609d4 # main
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
    with:
      # Production callers must pin the skill source ref as well.
      ref: ${{ vars.SPEC_TREE_VERIFICATION_SKILL_REF || '1a0a2474c50c2f60344e772576a0341fc3b4f8dd' }}
```

**For generic `@claude` mentions** — create `.github/workflows/claude.yml`:

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
    # Release lane: pin to a full-length commit SHA — never @main or @v1. See "Security" below.
    uses: outcomeeng/gh-actions/.github/workflows/claude.yml@a113491956c710dcdb7cb54174b4a52f9f6609d4 # main
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
```

**For generic Claude Code PR reviews** — create `.github/workflows/claude-code-review.yml`:

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
  actions: read

jobs:
  claude-code-review:
    # Release lane: pin to a full-length commit SHA — never @main or @v1. See "Security" below.
    uses: outcomeeng/gh-actions/.github/workflows/claude-code-review.yml@a113491956c710dcdb7cb54174b4a52f9f6609d4 # main
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
```

For complete copy-paste templates with every override documented inline, see `examples/caller-workflows/spec-tree.yml`, `examples/caller-workflows/spec-tree-review.yml`, `examples/caller-workflows/spec-tree-verification.yml`, `examples/caller-workflows/claude.yml`, and `examples/caller-workflows/claude-code-review.yml`.

For a generic Claude Code review, use the same `pull_request` trigger shape and call `.github/workflows/claude-code-review.yml` instead. That workflow keeps the default Claude review prompt compact and exposes `custom_prompt` for caller-specific review instructions.

### Branch-preview verification

`spec-tree-verification.yml` is the preview host for skill-based verification runs. It checks out a caller-selected skill source ref, loads the requested Claude Code plugin directory, launches Claude Code with a scrubbed process environment, and lets the skill write its `spx journal` output. When `ANTHROPIC_API_KEY` is present the host runs Claude Code in `--bare` mode; otherwise it omits `--bare` and passes `CLAUDE_CODE_OAUTH_TOKEN` when that secret is present. This preview host currently publishes the captured skill output to the job summary; hosted pull-request comment persistence waits on the `spx` hosted PR delivery command tracked in `spx/54-verification-gates.enabler/ISSUES.md`.

This repository's `.github/workflows/spec-tree-verification-repo.yml` caller is intentionally branch-preview only. It passes `allow_branch_preview: true` and carries the required `# BETA TESTER:` marker, so maintainers can set `vars.SPEC_TREE_VERIFICATION_SKILL_REF` to a skill branch while testing this workflow branch. Production callers must keep the workflow and skill refs SHA-pinned.

Verification callers must grant the reusable `contents: read` and `pull-requests: read` at the caller-workflow level; the reusable narrows each job from that maximum. The first preview slice does not request `pull-requests: write` because it writes the captured skill output to the job summary rather than posting a PR comment. The verification host runs the agent only when the PR author's repository permission is `admin`, `maintain`, or `write`, protecting the agent credential and token quota from fork and read-only PRs.

## Configuration

The Claude-compatible variants are direct, self-contained reusables. They do not call the spec-tree workflows and do not check out composite actions from this repository at runtime.

### Mention workflow inputs (`spec-tree.yml` and `claude.yml`)

| Input                 | Default                  | Description                                                                                                                            |
| --------------------- | ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `runner`              | `ubuntu-slim`            | Runner selection. Single label (`ubuntu-latest`, `self-hosted`) or JSON array (`'["self-hosted","laptop"]'`)                           |
| `trigger_phrase`      | `@spec-tree` / `@claude` | Text that triggers the workflow (also forwarded to the action). Default is `@spec-tree` on `spec-tree.yml`, `@claude` on `claude.yml`. |
| `concurrency_cancel`  | `true`                   | Cancel in-progress runs on new mention                                                                                                 |
| `custom_prompt`       | (empty)                  | Override default behavior with a custom prompt                                                                                         |
| `model`               | (empty)                  | Claude model id (e.g. `claude-opus-4-7`); folded into `claude_args` as `--model`. Empty = action default                               |
| `claude_args`         | (empty)                  | Extra Claude Code CLI args (e.g. `--max-turns 20 --allowed-tools "Bash(gh pr comment:*)"`)                                             |
| `use_bedrock`         | `false`                  | Route Claude through Amazon Bedrock (caller handles AWS auth via `additional_env`)                                                     |
| `use_vertex`          | `false`                  | Route Claude through Google Vertex AI (caller handles GCP auth via `additional_env`)                                                   |
| `additional_env`      | `{}`                     | JSON object string of env vars set on the claude-code-action step                                                                      |
| `use_project_plugins` | `false`                  | Install plugins and marketplaces from the caller's `.claude/settings.json` (see section below)                                         |
| `plugin_marketplaces` | (empty)                  | Space-separated marketplaces to register (`owner/repo`); appends to project list when opted in                                         |
| `extra_plugins`       | (empty)                  | Space-separated plugins to install; appends to project list when opted in                                                              |
| `show_full_output`    | `false`                  | Stream full per-turn Claude JSON to the job log (debug only — may expose secrets in tool output)                                       |
| `timeout_minutes`     | `"30"`                   | Wall-clock budget (minutes) for the Run Claude Code step; cancels the step when exceeded (minimum 1)                                   |

### Review workflow inputs (`spec-tree-review.yml` and `claude-code-review.yml`)

Both review workflows are self-contained reusables with the same runner, authorization, workflow-validation, plugin, cloud-routing, timeout, and env-override machinery.

The review prompt and baseline allowlist intentionally differ:

- `spec-tree-review.yml` bakes in a `REVIEW.md`-aware review prompt and a baseline allowlist for diff chunking: `Bash(gh ...)` plus `Bash(sed:*),Bash(grep:*),Bash(head:*)`.
- `claude-code-review.yml` uses a compact generic Claude review prompt, exposes `custom_prompt`, and defaults to the `Bash(gh ...)` tools needed to read PR context and post the review comment.

| Input                 | Default                  | Description                                                                                                                                                                  |
| --------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `runner`              | `ubuntu-slim`            | Runner selection. Single label or JSON array (see mention table above)                                                                                                       |
| `trigger_phrase`      | `@spec-tree` / `@claude` | Trigger phrase forwarded to the action (review does not use this to gate the run). Default is `@spec-tree` on `spec-tree-review.yml`, `@claude` on `claude-code-review.yml`. |
| `concurrency_cancel`  | `true`                   | Cancel in-progress reviews on new PR update                                                                                                                                  |
| `custom_prompt`       | (empty)                  | `claude-code-review.yml` only. Replaces the default generic review prompt. `spec-tree-review.yml` keeps its baked-in `REVIEW.md` prompt.                                     |
| `model`               | (empty)                  | Claude model id; folded into `claude_args` as `--model`. Empty = action default                                                                                              |
| `claude_args`         | (empty)                  | Extra Claude Code CLI args OTHER than `--allowed-tools` (use `append_allow_list` / `override_allow_list` for tools)                                                          |
| `append_allow_list`   | (empty)                  | Comma-separated tool patterns appended to that workflow's baseline allowlist                                                                                                 |
| `override_allow_list` | (empty)                  | Comma-separated tool patterns that REPLACE that workflow's baseline allowlist entirely                                                                                       |
| `use_bedrock`         | `false`                  | Route Claude through Amazon Bedrock                                                                                                                                          |
| `use_vertex`          | `false`                  | Route Claude through Google Vertex AI                                                                                                                                        |
| `additional_env`      | `{}`                     | JSON object string of env vars set on the claude-code-action step                                                                                                            |
| `use_project_plugins` | `false`                  | Install plugins and marketplaces from the caller's `.claude/settings.json` (see section below)                                                                               |
| `plugin_marketplaces` | (empty)                  | Space-separated marketplaces to register (`owner/repo`); appends to project list when opted in                                                                               |
| `extra_plugins`       | (empty)                  | Space-separated plugins to install; appends to project list when opted in                                                                                                    |
| `show_full_output`    | `false`                  | Stream full per-turn Claude JSON to the job log (debug only — may expose secrets in tool output)                                                                             |
| `timeout_minutes`     | `"30"`                   | Wall-clock budget (minutes) for the Run Claude Code Review step (minimum 1)                                                                                                  |

### Verification host inputs (`spec-tree-verification.yml`)

| Input                  | Default                 | Description                                                                                                  |
| ---------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------ |
| `runner`               | `ubuntu-slim`           | Runner selection. Single label or JSON array string.                                                         |
| `skill`                | `review-changes`        | Skill name to invoke, without a leading slash.                                                               |
| `skill_repository`     | `outcomeeng/plugins`    | GitHub repository containing the plugin source.                                                              |
| `ref`                  | required                | Skill source ref. Production callers pass a full commit SHA; branch refs require the beta-preview exception. |
| `skill_path`           | `src/plugins/spec-tree` | Path within the skill repository to the Claude plugin directory.                                             |
| `agent`                | `claude-code`           | Agent adapter. The first slice supports Claude Code only.                                                    |
| `model`                | (empty)                 | Claude model id. Empty = CLI default.                                                                        |
| `paths`                | (empty)                 | Optional newline-separated changed-path globs. Empty = every PR change is in scope.                          |
| `concurrency_suffix`   | (empty)                 | Optional discriminator when one caller runs the same skill more than once on a PR.                           |
| `allow_branch_preview` | `false`                 | Allows a same-repo beta caller with the marker comment to use a floating skill ref.                          |
| `spx_version`          | `0.6.7`                 | Version of `@outcomeeng/spx` to install.                                                                     |
| `claude_code_version`  | `2.1.195`               | Version of `@anthropic-ai/claude-code` to install.                                                           |
| `timeout_minutes`      | `"30"`                  | Wall-clock budget for the verification skill run.                                                            |

Secret required by the first Claude Code host slice: either `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN`. When `ANTHROPIC_API_KEY` is set, the host passes `--bare`; when only `CLAUDE_CODE_OAUTH_TOKEN` is set, the host omits `--bare` and passes that token through the scrubbed process environment.

### Per-environment overrides via repo variables

The example caller templates are **drop-in**: copy the file, set the repository secret, and the workflow runs with sensible defaults. To tune behavior per-environment, set the corresponding repository variable in Settings → Secrets and variables → Actions → Variables. The `with:` block in each template is active and reads `vars.SPEC_TREE_*` (mention) or `vars.SPEC_TREE_REVIEW_*` (review) values, falling back to the reusable's documented default when the variable is unset — no edits to the workflow file are needed.

The generic Claude examples mirror the same shape with `vars.CLAUDE_*` for mentions and `vars.CLAUDE_REVIEW_*` for reviews; their tables follow the spec-tree ones below.

Mention workflow (`spec-tree.yml`):

| Repo variable                   | Maps to               | Default if unset | Notes                                                                                                                           |
| ------------------------------- | --------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `SPEC_TREE_RUNNER`              | `runner`              | `ubuntu-slim`    | Single label or JSON-array string. `'["self-hosted","laptop"]'` is one literal string.                                          |
| `SPEC_TREE_TRIGGER_PHRASE`      | `trigger_phrase`      | `@spec-tree`     | Mention text the workflow listens for. The reusable's authorize job rejects empty or whitespace-only values with a clear error. |
| `SPEC_TREE_CONCURRENCY_CANCEL`  | `concurrency_cancel`  | `true`           | Set the string `'false'` to opt out of cancel-on-new. Any other value preserves cancel behavior.                                |
| `SPEC_TREE_TIMEOUT_MINUTES`     | `timeout_minutes`     | `'30'`           | Wall-clock budget in minutes (quoted string).                                                                                   |
| `SPEC_TREE_MODEL`               | `model`               | (action default) | Claude model id (e.g. `claude-opus-4-7`); folded into `claude_args` as `--model <id>`.                                          |
| `SPEC_TREE_CLAUDE_ARGS`         | `claude_args`         | (empty)          | Extra CLI args, e.g. `--max-turns 20 --allowed-tools "Read,Grep,Bash(gh pr:*)"`.                                                |
| `SPEC_TREE_CUSTOM_PROMPT`       | `custom_prompt`       | (empty)          | Single-line custom prompt. Multi-line prompts are awkward in repo vars; edit the workflow file directly for those.              |
| `SPEC_TREE_USE_PROJECT_PLUGINS` | `use_project_plugins` | `false`          | Set `'true'` to install plugins declared in `.claude/settings.json`. Any other value (or unset) keeps the default off.          |
| `SPEC_TREE_SHOW_FULL_OUTPUT`    | `show_full_output`    | `false`          | Set `'true'` to stream per-turn JSON to the job log. WARNING: may expose secrets in tool outputs. Debug only.                   |

Review workflow (`spec-tree-review.yml`):

| Repo variable                          | Maps to               | Default if unset | Notes                                                                                                                                                                                         |
| -------------------------------------- | --------------------- | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SPEC_TREE_REVIEW_RUNNER`              | `runner`              | `ubuntu-slim`    | Same form as mention.                                                                                                                                                                         |
| `SPEC_TREE_REVIEW_TRIGGER_PHRASE`      | `trigger_phrase`      | `@spec-tree`     | Forwarded to the action for content matching; review fires on every `pull_request` event regardless. The reusable's authorize job rejects empty or whitespace-only values with a clear error. |
| `SPEC_TREE_REVIEW_CONCURRENCY_CANCEL`  | `concurrency_cancel`  | `true`           | Same semantics as mention.                                                                                                                                                                    |
| `SPEC_TREE_REVIEW_TIMEOUT_MINUTES`     | `timeout_minutes`     | `'30'`           | Same.                                                                                                                                                                                         |
| `SPEC_TREE_REVIEW_MODEL`               | `model`               | (action default) | Same.                                                                                                                                                                                         |
| `SPEC_TREE_REVIEW_CLAUDE_ARGS`         | `claude_args`         | (empty)          | Extra CLI args OTHER than `--allowed-tools` (use the allow-list inputs below for tool changes).                                                                                               |
| `SPEC_TREE_REVIEW_APPEND_ALLOW_LIST`   | `append_allow_list`   | (empty)          | Comma-separated patterns appended to the baked-in spec-tree review baseline (`Bash(gh ...) + Bash(sed:*),Bash(grep:*),Bash(head:*)`). Widen when opting in to project plugins.                |
| `SPEC_TREE_REVIEW_USE_PROJECT_PLUGINS` | `use_project_plugins` | `false`          | Set `'true'` to install project plugins; pair with `SPEC_TREE_REVIEW_APPEND_ALLOW_LIST` so the plugin's tools are reachable.                                                                  |
| `SPEC_TREE_REVIEW_SHOW_FULL_OUTPUT`    | `show_full_output`    | `false`          | Same warning as mention.                                                                                                                                                                      |

Mention workflow (`claude.yml`):

| Repo variable                | Maps to               | Default if unset | Notes                                                                                                         |
| ---------------------------- | --------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------- |
| `CLAUDE_RUNNER`              | `runner`              | `ubuntu-slim`    | Same form as the spec-tree mention runner.                                                                    |
| `CLAUDE_TRIGGER_PHRASE`      | `trigger_phrase`      | `@claude`        | Mention text the workflow listens for; the generic default differs from `@spec-tree`.                         |
| `CLAUDE_CONCURRENCY_CANCEL`  | `concurrency_cancel`  | `true`           | Set the string `'false'` to opt out of cancel-on-new.                                                         |
| `CLAUDE_TIMEOUT_MINUTES`     | `timeout_minutes`     | `'30'`           | Wall-clock budget in minutes (quoted string).                                                                 |
| `CLAUDE_MODEL`               | `model`               | (action default) | Claude model id; folded into `claude_args` as `--model <id>`.                                                 |
| `CLAUDE_ARGS`                | `claude_args`         | (empty)          | Extra CLI args. Note the name: `CLAUDE_ARGS`, not `CLAUDE_CLAUDE_ARGS`.                                       |
| `CLAUDE_CUSTOM_PROMPT`       | `custom_prompt`       | (empty)          | Single-line custom prompt; edit the workflow file directly for multi-line prompts.                            |
| `CLAUDE_USE_PROJECT_PLUGINS` | `use_project_plugins` | `false`          | Set `'true'` to install plugins declared in `.claude/settings.json`.                                          |
| `CLAUDE_SHOW_FULL_OUTPUT`    | `show_full_output`    | `false`          | Set `'true'` to stream per-turn JSON to the job log. WARNING: may expose secrets in tool outputs. Debug only. |

Review workflow (`claude-code-review.yml`):

| Repo variable                       | Maps to               | Default if unset | Notes                                                                                                                     |
| ----------------------------------- | --------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `CLAUDE_REVIEW_RUNNER`              | `runner`              | `ubuntu-slim`    | Same form as mention.                                                                                                     |
| `CLAUDE_REVIEW_TRIGGER_PHRASE`      | `trigger_phrase`      | `@claude`        | Forwarded for content matching; review fires on every `pull_request` event regardless.                                    |
| `CLAUDE_REVIEW_CONCURRENCY_CANCEL`  | `concurrency_cancel`  | `true`           | Same semantics as mention.                                                                                                |
| `CLAUDE_REVIEW_TIMEOUT_MINUTES`     | `timeout_minutes`     | `'30'`           | Wall-clock budget in minutes (quoted string).                                                                             |
| `CLAUDE_REVIEW_MODEL`               | `model`               | (action default) | Same.                                                                                                                     |
| `CLAUDE_REVIEW_CLAUDE_ARGS`         | `claude_args`         | (empty)          | Extra CLI args OTHER than `--allowed-tools`. Note the name carries `CLAUDE_` twice.                                       |
| `CLAUDE_REVIEW_CUSTOM_PROMPT`       | `custom_prompt`       | (empty)          | Single-line custom prompt.                                                                                                |
| `CLAUDE_REVIEW_APPEND_ALLOW_LIST`   | `append_allow_list`   | (empty)          | Comma-separated patterns appended to the reusable's baseline allowlist.                                                   |
| `CLAUDE_REVIEW_USE_PROJECT_PLUGINS` | `use_project_plugins` | `false`          | Set `'true'` to install project plugins; pair with `CLAUDE_REVIEW_APPEND_ALLOW_LIST` so the plugin's tools are reachable. |
| `CLAUDE_REVIEW_SHOW_FULL_OUTPUT`    | `show_full_output`    | `false`          | Same warning as mention.                                                                                                  |

Inputs **left commented in the example template** (active when uncommented):

- `override_allow_list` (review) — replaces the entire baked-in allowlist. On `spec-tree-review.yml`, this also drops the `sed`/`grep`/`head` defaults the baked-in prompt depends on. Use `append_allow_list` unless you have a hard reason to start from zero.
- `use_bedrock` / `use_vertex` / `additional_env` — cloud-provider routing. Coupled inputs (set all three together) and requires the calling workflow to configure AWS or GCP auth before this job. Uncomment as a unit.
- `plugin_marketplaces` / `extra_plugins` — explicit install lists. Rarely change per-environment; set directly to opt in without using vars.

## Plugins and marketplaces

The reusable workflows install plugins from two possible sources:

1. **Caller workflow inputs** (`extra_plugins`, `plugin_marketplaces`) — always applied.
2. **The caller repository's `.claude/settings.json`** (`enabledPlugins`, `extraKnownMarketplaces`) — only when `use_project_plugins: true`.

### Default: project plugins are NOT installed

`use_project_plugins` defaults to `false`. The review job and the mention job run with no project plugins. The reason is plugin skills: most non-trivial plugins ship skills with `ALWAYS invoke this skill before X` mandates that pull Claude into tools (`Read`, `Grep`, `Glob`, `Bash(git ...)`) outside the default review allowlists. The result is a run that spends turns on permission denials and never posts a review comment.

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

Widening the tool patterns is not sufficient on its own to *run* a plugin's skills. When a plugin skill declares extra capabilities in its frontmatter (an `allowed-tools` list, as most spec-tree skills do), the pinned `anthropics/claude-code-action` denies the `Skill` tool call in a headless run, because the action grants no `Skill` rule for the plugins it installs. The prompt then fails with `Error: Execute skill: <name>`. Until the action derives these rules automatically ([anthropics/claude-code-action#1467](https://github.com/anthropics/claude-code-action/pull/1467)), grant them yourself — one `Skill(<plugin>:*)` entry per installed plugin, e.g. `Skill(spec-tree:*)`:

- **Review workflows** — add the pattern to `append_allow_list`. The action merges it as a set with the workflow's baked-in review baseline.
- **Mention workflows** — `claude_args` is forwarded to the CLI verbatim, so pass the grant as an `--allowed-tools` flag value, not a bare pattern: `--allowed-tools "Skill(spec-tree:*)"`. The mention workflows carry no baked-in allowlist, so this same `claude_args` value must also name every other tool pattern the run needs.

Once that fix ships in a release and the pin advances, the manual `Skill(...)` grant becomes redundant and can be dropped.

## Authorization

Each reusable workflow has a small `authorize` job that queries `repos/{owner}/{repo}/collaborators/{actor}/permission` and the downstream job runs only when the actor's effective permission is `admin`, `maintain`, or `write`. Permission flows through team and org membership, so trusted org members are authorized without extra configuration. External contributors (including PRs from forks) come back as `none` (or 404), and the agent job is `skipped` (gray check on the PR), not failed — so an unauthorized PR doesn't show a red X.

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
    # Release lane: pin to a full-length commit SHA — never @main or @v1. See "Security" below.
    uses: outcomeeng/gh-actions/.github/workflows/spec-tree.yml@a113491956c710dcdb7cb54174b4a52f9f6609d4 # main
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
uses: outcomeeng/gh-actions/.github/workflows/spec-tree.yml@a113491956c710dcdb7cb54174b4a52f9f6609d4 # main

# Forbidden
uses: actions/checkout@v6
```

The trailing `# v6.0.2` / `# main` comment names the tag or branch the SHA tracks. Renovate uses that comment to know which upstream reference to follow when advancing the pin.

#### Documented exception: beta-tester consumers

Repositories that are deliberately tracking-latest against `outcomeeng/gh-actions` — typically internal repos under the same trust boundary as the reusables, used to surface upstream changes early before they go out to production consumers — MAY pin to `@main` instead of a SHA. This is an opt-out from rule 1 above, not a blanket weakening of it. The opt-out requires:

1. The consumer repo is under the same organizational trust boundary as `outcomeeng/gh-actions` (i.e. you, or someone you'd already trust with write access to the reusable repo, controls both).
2. The caller workflow carries an explicit `# BETA TESTER:` marker comment naming the trade-off, so a future reader can tell the relaxed pin is intentional rather than a regression.
3. The repo accepts that a compromise of the publishing branch propagates immediately, with no Renovate PR or human review intervening. For repos that hold production secrets or customer data, this is the wrong trade-off — SHA-pin.

Recommended template:

```yaml
# BETA TESTER: deliberately tracks outcomeeng/gh-actions @main to surface
# upstream changes early without a per-release follow-up PR. Production
# callers must SHA-pin per the gh-actions README "Security" section.
# Renovate cannot advance this reference; that is the point — pin it back
# to a SHA when this repo graduates to production usage.
uses: outcomeeng/gh-actions/.github/workflows/spec-tree.yml@main
```

The example caller templates in this repository (`examples/caller-workflows/`) ship SHA-pinned by default — they target the production-consumer path. Beta-tester consumers should copy the template, then change the pin to `@main` with the marker comment above.

### Renovate keeps pins fresh

[Renovate](https://docs.renovatebot.com/) is the recommended update mechanism — Dependabot also supports SHA pinning, but Renovate's `helpers:pinGitHubActionDigests` preset handles both the SHA and the trailing comment in one pass and groups action updates intelligently. This repository's `renovate.json` is configured for the recommended baseline (`config:recommended` + the digest helper). Enable Renovate on your caller repo by installing the [Renovate GitHub App](https://github.com/apps/renovate) and copying a similar config:

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    "github>outcomeeng/gh-actions//renovate-presets/gh-actions-consumer"
  ],
  "vulnerabilityAlerts": { "enabled": true }
}
```

The shared preset extends Renovate's GitHub Action digest helper and groups `outcomeeng/gh-actions` reusable updates. Renovate presets are JSON files; the `github>outcomeeng/gh-actions//renovate-presets/gh-actions-consumer` form resolves to `renovate-presets/gh-actions-consumer.json` on this repository's default branch.

Running both Renovate and Dependabot against the same files produces conflicting PRs — pick one.

For this repository's own `anthropics/claude-code-action` dependency, Renovate runs a separate weekday lane because upstream publishes frequent `v1.0.x` releases. Beta-tester callers pinned to `outcomeeng/gh-actions@main` receive the reviewed upstream action update after the Renovate PR merges here. Production callers that SHA-pin `outcomeeng/gh-actions` receive it after this repository publishes a release commit and the caller's Renovate PR advances the reusable-workflow SHA.

### Least-privilege `permissions:`

The reusable workflows (`spec-tree.yml`, `spec-tree-review.yml`, `claude.yml`, `claude-code-review.yml`) and `ci.yml` declare top-level `permissions: {}` and then grant per-job permissions explicitly. Caller workflows should declare top-level `permissions:` with the maximum the reusable needs. The quick-start examples list the exact permissions each reusable expects.

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

`actionlint` flags unpinned actions, deprecated inputs, and shell-injection-prone interpolation; `shellcheck` audits inline `run:` scripts (and standalone shell files under `gh_actions/`).

### Authorization (this repo's reusables)

The `authorize` job in each reusable queries `repos/{owner}/{repo}/collaborators/{actor}/permission` and the downstream Claude job runs only when the actor's effective permission is `admin`, `maintain`, or `write` — see [Authorization](#authorization) for the full mechanism and the rationale for replacing the earlier `author_association` gate.

### Operational best practices

- Keep `use_project_plugins` off (the default) unless the project plugins are appropriate for review or mention runs, and widen the allowlist (`append_allow_list` / `override_allow_list` on review, `claude_args` on mention) to match the tools those plugins' skills demand.
- Narrow `claude_args` (mention) or `append_allow_list` / `override_allow_list` (review) to the minimum the workflow needs. `claude-code-review.yml` starts from `gh issue` / `gh pr` read plus `gh pr comment`; `spec-tree-review.yml` also includes `sed` / `grep` / `head` for diff chunking.
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

Setting `CLAUDE_CODE_OAUTH_TOKEN` in each repository is tedious. The `gh_actions/push_secrets.py` script automates this by:

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
uv run /path/to/gh-actions/gh_actions/push_secrets.py check

# Push secrets (reads from Keychain automatically)
uv run /path/to/gh-actions/gh_actions/push_secrets.py push
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
