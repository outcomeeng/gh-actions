# Distribution

PROVIDES the consumer-adoption surface — copy-paste caller templates, per-environment repo-variable overrides, documentation, and secret provisioning tooling (`gh_actions/push_secrets.py`)
SO THAT a downstream repository
CAN adopt a reusable by copying a SHA-pinned caller stub, setting one secret, and tuning behavior through repo variables, without editing workflow logic

## Assertions

### Compliance

- ALWAYS: each surface ships a drop-in caller template under `examples/caller-workflows/`; its reusable reference, tracked branch comment, README release-lane snippets, and caller-template timeout default are checked against `examples/caller-workflows/manifest.yaml` and the reusable workflow default; generated examples and copied snippets cannot drift from the manifest-governed release lane ([test](tests/test_caller_workflows.compliance.l1.py))
- ALWAYS: README snippets teach the same beta and release consumer lanes that `examples/caller-workflows/` implements, so copy-paste documentation and caller templates present one adoption contract ([audit])
- ALWAYS: the distribution surface documents two consumer lanes: a beta lane that deliberately uses `@main` with an explicit `# BETA TESTER:` marker, and a release lane that uses a full-length SHA with trailing `# main` for Renovate-managed production consumers ([audit])
- ALWAYS: production consumers receive a shareable Renovate preset for `outcomeeng/gh-actions` reusable pins so copied caller workflows get grouped, SHA-pinned update PRs without each consumer inventing dependency-update policy ([audit])
- ALWAYS: secret provisioning reads the credential from the platform keystore and pushes it via `gh secret set`, never printing or committing the value ([audit])
- NEVER: a shipped caller template pins a mutable ref (`@main` / `@v1`) except under the documented beta-tester exception carrying an explicit marker comment ([audit])
