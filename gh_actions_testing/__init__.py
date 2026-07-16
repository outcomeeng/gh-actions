"""Test infrastructure for the ``gh_actions`` package.

Harnesses, generators, and inert fixtures that the ``gh_actions`` package's
pytest lane depends on. This home sits outside ``spx/`` and outside any
``tests/`` directory, and the build excludes it from the shipped package, per
``plugins/spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md``
and ``spx/15-evidence-model.adr.md``.
"""
