# Agent Invocation

PROVIDES a common agent-run setup — provider and runtime routing (Anthropic API, Bedrock, Vertex, OpenAI / cloud review, and further providers), agent plugin and marketplace installation, and tool-allowlist composition
SO THAT this product's agent-surface nodes
CAN invoke an AI coding agent through one configurable shape regardless of provider, with the required plugins installed and the matching tools allowed

## Assertions

### Compliance

- ALWAYS: provider and runtime selection is a configuration axis (inputs such as `use_bedrock`, `use_vertex`, `model`) over a single invocation shape, never a separate workflow per provider ([audit])
- ALWAYS: plugin and marketplace installation composes from caller inputs and, when opted in, the consumer's `.claude/settings.json`, and the tool allowlist is composed to match the installed tools ([audit])
- NEVER: a surface embeds provider-specific invocation logic that bypasses this shared setup — provider variation lives here ([audit])
