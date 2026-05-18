# Outcome Engineering GitHub Actions

Reusable GitHub Actions workflows for Claude Code integration.

## Repository Structure

```
gh-actions/
├── .github/
│   └── workflows/
│       ├── ci.yml                        # actionlint + shellcheck on every push and PR
│       ├── spec-tree.yml                 # @spec-tree mention handler (reusable)
│       ├── spec-tree-review.yml          # PR review with REVIEW.md-aware prompt (reusable)
│       ├── spec-tree-repo.yml            # Self-test caller (spec-tree mention)
│       └── spec-tree-review-repo.yml     # Self-test caller (spec-tree review)
├── examples/
│   └── caller-workflows/                 # Copy-paste templates for downstream repos
├── AGENTS.md                             # Cloud review guidance
├── CLAUDE.md                             # This file
├── Justfile                              # Local lint commands (mirror of ci.yml)
├── README.md                             # User documentation
└── renovate.json                         # SHA-pinning + tag-tracking for GitHub Actions and reusable workflows
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
2. Either (a) mention `@spec-tree` on an issue or PR in this repo (fires `spec-tree-repo.yml`) / open a PR (fires `spec-tree-review-repo.yml`), or (b) update an external test repo to use `@branch-name` instead of `@main`
3. Trigger the workflow and verify behavior
4. Merge to main when satisfied

### Versioning

Use tags for stable versions:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Consumers can then use `@v1` for the latest v1.x.x.

## Security

The repo's security posture follows [GitHub's hardening guide](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions) and the OpenSSF baseline for GitHub Actions. The non-negotiables, in priority order:

1. **Every third-party action and reusable workflow is pinned by full-length commit SHA**, not by `@v1` or `@main`. Tags and branches are mutable; a SHA is the only reference an attacker can't redirect after publication. Each pin carries a trailing comment naming the tag or branch the SHA tracks (`@<sha> # v1.2.3` or `@<sha> # main`); Renovate uses that comment to advance the pin on each release.
2. **Renovate is the single update mechanism**, configured at `renovate.json` with `helpers:pinGitHubActionDigests`. The earlier `.github/dependabot.yml` has been removed — running both creates conflicting PRs against the same lines. Renovate opens grouped PRs on a weekly cadence; security advisories fire immediately under `vulnerabilityAlerts`.
3. **Top-level `permissions: {}`** on every reusable workflow (`spec-tree.yml`, `spec-tree-review.yml`) and on `ci.yml`. Jobs explicitly grant the narrow permissions they need, subject to the caller workflow's maximum grant. The caller workflow's permissions set the maximum; the reusable's per-job grants do the actual narrowing.
4. **`persist-credentials: false`** on every `actions/checkout` step that does not push back to the same repository. Drops the git-credentials persistence so later steps can't reuse the token.
5. **Secrets reach the runner via the action's `with:` inputs or via job-level `env:` blocks** — never interpolated into a `run:` script body. The pattern is enforced by actionlint + shellcheck.
6. **`actionlint` and `shellcheck` run on every push and PR** via `.github/workflows/ci.yml`. The same linters run locally via `just lint`. CI fails on any new warning.
7. **Authorization** to trigger a mention or review job is gated by the repo-permissions API (`repos/{owner}/{repo}/collaborators/{actor}/permission`), not by `author_association`. Only actors with `admin`, `maintain`, or `write` permission pass the authorize job.

### Updating action / reusable-workflow pins

Renovate opens the PR. Reviewer responsibilities:

1. Read the release notes linked in the Renovate PR body.
2. Confirm the new SHA resolves to a tag — Renovate's PR title includes both. Sanity-check by clicking through to the release.
3. Merge when CI is green. The Renovate PR title carries `ci(deps):` or `chore(deps):` per the `:semanticCommits` preset.

For consumers of this repo (downstream `.github/workflows/*.yml` callers that reference `outcomeeng/gh-actions`), the same rule applies: pin by SHA, let Renovate advance.

### Running lint locally

macOS:

```bash
brew install just actionlint shellcheck
just check
```

Linux (any distro — actionlint is not in apt; install via the same sha256-verified release path that CI uses):

```bash
sudo apt-get install -y just shellcheck

ACTIONLINT_VERSION=1.7.12   # advance in lockstep with .github/workflows/ci.yml
base=https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}
curl -sSLO "${base}/actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz"
curl -sSLO "${base}/actionlint_${ACTIONLINT_VERSION}_checksums.txt"
sha256sum --check --ignore-missing --strict "actionlint_${ACTIONLINT_VERSION}_checksums.txt"
tar -xzf "actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz" actionlint
sudo install -m 0755 actionlint /usr/local/bin/actionlint

just check
```

Both linters fail loudly on shell-injection-prone patterns (unquoted variables, `${var}` inside patterns, etc.) so `run:` blocks that handle user input get caught before merge.
