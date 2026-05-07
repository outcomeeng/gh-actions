# Repository Instructions

This repository publishes reusable GitHub Actions workflows. Treat workflow behavior, inputs, permissions, and examples as public API for downstream repositories.

## Review guidelines

- Prioritize findings that can break caller workflows, weaken security, expose secrets, make reviews unreliable, or make documented setup diverge from actual behavior.
- Check reusable workflow inputs, defaults, permissions, event contexts, concurrency groups, cache keys, shell quoting, and GitHub expression syntax together. A value documented in `README.md` or `examples/` should match the reusable workflow.
- Treat GitHub Actions YAML as executable code. Validate syntax with `actionlint` when workflow files change.
- Verify third-party actions are pinned to full commit SHAs with a version comment when this repo already follows that pattern.
- Review shell blocks for `set -euo pipefail`, quoted paths and variables, safe GitHub output delimiters, and visible failures for malformed configuration files.
- Flag documentation issues when they would cause a caller to copy a broken workflow, use the wrong secret, or misunderstand a security boundary.
- Keep review findings focused on high-priority risks. Avoid style-only comments unless the style issue can mislead callers or hide a workflow bug.

## Validation

- Run `actionlint .github/workflows/claude.yml .github/workflows/claude-code-review.yml .github/workflows/claude-repo.yml .github/workflows/claude-code-review-repo.yml examples/caller-workflows/claude.yml examples/caller-workflows/claude-code-review.yml` after workflow or example changes.
- Run `git diff --check` before committing.
- Use `dprint fmt <files>` for Markdown, YAML, JSON, HTML, CSS, JavaScript, and TypeScript formatting.
- Do not use Prettier in this repository.
