# Distribution

PROVIDES the consumer-adoption surface — copy-paste caller templates, per-environment repo-variable overrides, documentation, and secret provisioning tooling (`push-secrets.py`)
SO THAT a downstream repository
CAN adopt a reusable by copying a SHA-pinned caller stub, setting one secret, and tuning behavior through repo variables, without editing workflow logic

## Assertions

### Compliance

- ALWAYS: each surface ships a drop-in caller template under `examples/caller-workflows/` that SHA-pins the reusable and reads `vars.*` overrides with documented defaults ([audit])
- ALWAYS: secret provisioning reads the credential from the platform keystore and pushes it via `gh secret set`, never printing or committing the value ([audit])
- NEVER: a shipped caller template pins a mutable ref (`@main` / `@v1`) except under the documented beta-tester exception carrying an explicit marker comment ([audit])
