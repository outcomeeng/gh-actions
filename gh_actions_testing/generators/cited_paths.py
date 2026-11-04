"""Generator: cited paths for each ``PathKind``, built from the source conventions.

Every path is assembled from the path-convention constants that
``gh_actions.review_findings`` owns, combined with the node, stem, and extension
segments this generator owns as its input domain. A ``PathKind`` member the
generator has no construction for raises, so the mapping lane fails for a kind
added to the source without a matching case.
"""

from __future__ import annotations

from typing import assert_never

from gh_actions.review_findings import (
    ADR_SUFFIX,
    CODE_ROOTS,
    PDR_SUFFIX,
    SPEC_SUFFIX,
    TEST_HOME_DIR,
    TEST_MARKERS,
    TREE_ROOT,
    PathKind,
)

NODES = ("", "21-example.enabler/", "21-example.enabler/32-nested.capability/")
STEMS = ("example", "15-sample-name")
EXTENSIONS = (".py", ".ts")
PACKAGES = ("example", "gh_actions")


def cited_paths(kind: PathKind) -> tuple[str, ...]:
    """Return every cited path the generator builds for ``kind``."""
    match kind:
        case PathKind.DECISION_ADR:
            return tuple(
                f"{TREE_ROOT}{node}{stem}{ADR_SUFFIX}"
                for node in NODES
                for stem in STEMS
            )
        case PathKind.DECISION_PDR:
            return tuple(
                f"{TREE_ROOT}{node}{stem}{PDR_SUFFIX}"
                for node in NODES
                for stem in STEMS
            )
        case PathKind.TEST:
            roots = (*(f"{TREE_ROOT}{node}" for node in NODES), *CODE_ROOTS)
            in_tree = tuple(
                f"{root}{stem}{marker}{stem}{ext}"
                for root in roots
                for stem in STEMS
                for marker in TEST_MARKERS
                for ext in (SPEC_SUFFIX, *EXTENSIONS)
            )
            homes = (TEST_HOME_DIR, *(f"{pkg}_{TEST_HOME_DIR}" for pkg in PACKAGES))
            in_home = tuple(
                f"{home}/{stem}{ext}"
                for home in homes
                for stem in STEMS
                for ext in EXTENSIONS
            )
            return in_tree + in_home
        case PathKind.SPEC:
            return tuple(
                f"{TREE_ROOT}{node}{stem}{SPEC_SUFFIX}"
                for node in NODES
                for stem in STEMS
            )
        case PathKind.CODE:
            return tuple(
                f"{root}{stem}{ext}"
                for root in CODE_ROOTS
                for stem in STEMS
                for ext in EXTENSIONS
            )
        case PathKind.PRODUCT_TREE_OTHER:
            return tuple(f"{TREE_ROOT}{node}{stem}" for node in NODES for stem in STEMS)
        case PathKind.OTHER:
            return tuple(
                f"{stem}{suffix}"
                for stem in STEMS
                for suffix in (SPEC_SUFFIX, *EXTENSIONS)
            )
        case _:
            assert_never(kind)
