# Local development commands. Match what CI runs so that `just check`
# passing is a near-guarantee that CI will pass too.
#
# Install prerequisites (one-time):
#   macOS:  brew install just actionlint shellcheck
#   Linux:  apt-get install shellcheck     # plus install actionlint manually
#
# Each recipe's `just --list` description is the single comment line
# directly above it.

default:
    @just --list

# Format repository-owned Markdown, YAML, and JSON instruction/workflow surfaces.
fmt:
    dprint fmt AGENTS.md CLAUDE.md README.md renovate.json .github/workflows/*.yml examples/caller-workflows/*.yml

# Validate the current diff has no whitespace errors.
check-diff:
    git diff --check

# Validate reusable workflows and caller examples with actionlint.
check-workflows:
    actionlint .github/workflows/*.yml examples/caller-workflows/*.yml

# Product-local verification before committing, opening a PR, or pushing a follow-up.
check-verify: check-diff check

# Full deterministic check for apply and merge readiness.
check-apply-merge: check-verify

# Umbrella — what CI runs.
check: check-lint check-test

# Remove every gitignored file and directory.
clean:
    git clean -fdX

# Run deterministic caller workflow tests.
check-test:
    python3 -m venv .venv
    .venv/bin/python -m pip install -q -e ".[test]"
    PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.check_caller_workflows --check
    PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q

# Run all linters.
check-lint: check-actions check-shell

# actionlint over .github/workflows/ — also runs shellcheck on inline run: blocks.
check-actions:
    @echo "=== actionlint ==="
    actionlint -color

# shellcheck over scripts/ (inline run-blocks are covered by lint-actions).
check-shell:
    @echo "=== shellcheck ==="
    @if find scripts -type f \( -name '*.sh' -o -name '*.bash' \) -print -quit 2>/dev/null | grep -q .; then \
        find scripts -type f \( -name '*.sh' -o -name '*.bash' \) -print0 | xargs -0 shellcheck --color=always; \
    else \
        echo "  (no shell scripts under scripts/ — nothing to check)"; \
    fi
