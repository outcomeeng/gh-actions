# ISSUES — distribution

## 1. Caller-workflow compliance test owns its fixtures and setup inline

`spx/76-distribution.enabler/tests/test_caller_workflows.compliance.l1.py`
builds its violating payloads, manifest text, reusable-workflow text, README
text, and shared values (`EXPECTED_SHA`, `OTHER_SHA`, the `'15'` timeout) in
test-file helpers (`_example_text`, `_manifest_text`, `_write_reusable`,
`_write_workflow_call`, `_write_readme`, `_init_git_repo`). About fifteen tests
repeat the same temporary caller-workspace scaffolding and git-repo setup.

`spx/15-evidence-model.adr.md` places the `gh_actions` package's test
infrastructure — harnesses, generators, and inert fixtures — at
`gh_actions_testing/{harnesses,generators,fixtures}/`, outside any `tests/`
directory. The test file imports nothing from that home, so its fixtures and
scaffolding sit in the test file the ADR reserves for typed assertion evidence.

Raised as two filed findings (test-owned data; architectural duplication) by
the test-evidence audit of this node.

**Settled when** the caller-workspace scaffolding and git-repo setup live in a
harness under `gh_actions_testing/harnesses/`, the violating payloads and
shared values come from `gh_actions_testing/` generators or fixtures, and the
test file holds only assertions over them.
