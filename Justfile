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

# Umbrella — what CI runs.
check: lint

# Run all linters.
lint: lint-actions lint-shell

# actionlint over .github/workflows/ — also runs shellcheck on inline run: blocks.
lint-actions:
    @echo "=== actionlint ==="
    actionlint -color

# shellcheck over scripts/ (inline run-blocks are covered by lint-actions).
lint-shell:
    @echo "=== shellcheck ==="
    @if find scripts -type f \( -name '*.sh' -o -name '*.bash' \) -print -quit 2>/dev/null | grep -q .; then \
        find scripts -type f \( -name '*.sh' -o -name '*.bash' \) -print0 | xargs -0 shellcheck --color=always; \
    else \
        echo "  (no shell scripts under scripts/ — nothing to check)"; \
    fi
