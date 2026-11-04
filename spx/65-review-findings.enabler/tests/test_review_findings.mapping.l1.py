"""Mapping evidence: a cited path maps to its source-owned artifact kind.

The domain is every `PathKind` member owned by the module under test. Each case's
input paths come from the cited-path generator, which builds them from the path
conventions the same module owns; the expected kind is the member the generator
built the paths for.
"""

from __future__ import annotations

import pytest

from gh_actions.review_findings import PathKind, classify_path
from gh_actions_testing.generators.cited_paths import cited_paths


@pytest.mark.parametrize("kind", list(PathKind))
def test_cited_path_maps_to_each_artifact_kind(kind: PathKind) -> None:
    paths = cited_paths(kind)
    assert paths
    for path in paths:
        assert classify_path(path) is kind, path
