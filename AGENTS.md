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

## Spec tree and cross-repository review governance

This repository carries a Spec Tree under `spx/` — a durable, declarative map of the product. Specs declare; tests and code comply. When reviewing `spx/` changes, judge them against that hierarchy, not against the current workflow YAML.

The agent skill, prompt, review taxonomy, and reviewer-only decision are **governed in the sibling `outcomeeng/plugins` repository and cross-referenced from this tree, never restated** (a product-level NEVER assertion enforces this). Treat these cross-references as intentional — do not ask this repo to consolidate them into a local PDR or to inline the governed content. Each concern has one canonical file:

| Concern                                                   | Canonical file                                                                                                                                                                                        |
| --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Review skill and prompt                                   | `plugins/spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md` (prompt body: `src/plugins/spec-tree/skills/reviewing-changes/references/review-prompt.md`) |
| Review taxonomy and findings-only rule                    | `plugins/spx/21-spec-tree.enabler/68-reviewing.enabler/reviewing.md`                                                                                                                                  |
| Reviewer-only decision (reviewer reviews, author decides) | `plugins/spx/15-merging.pdr.md`                                                                                                                                                                       |

Path conventions for cross-references into the plugins repo: `plugins/spx/...` names a spec file in that repo's Spec Tree; `src/plugins/...` names a skill source file. Both resolve against the `outcomeeng/plugins` checkout, not against this repo. Before flagging a cross-repo path as unresolvable, resolve it against that checkout — a path that exists there is correct even though it is absent here. Citations name a specific file, never a bare directory node.

## Validation

- Run `actionlint .github/workflows/claude.yml .github/workflows/claude-code-review.yml .github/workflows/claude-repo.yml .github/workflows/claude-code-review-repo.yml examples/caller-workflows/claude.yml examples/caller-workflows/claude-code-review.yml` after workflow or example changes.
- Run `git diff --check` before committing.
- Use `dprint fmt <files>` for Markdown, YAML, JSON, HTML, CSS, JavaScript, and TypeScript formatting.
- Do not use Prettier in this repository.
