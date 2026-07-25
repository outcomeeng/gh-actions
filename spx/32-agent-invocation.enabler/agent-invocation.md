# Agent Invocation

PROVIDES a common agent-run setup — coding-agent selection (Claude Code, Codex, Gemini), provider and runtime routing (Anthropic API, Bedrock, Vertex, OpenAI / cloud review, and further providers), subscription-backed agent authentication, agent plugin and marketplace installation, and tool-allowlist composition
SO THAT this product's agent-surface nodes
CAN invoke an AI coding agent through one configurable shape regardless of agent and provider, with the required plugins installed and the matching tools allowed

## Assertions

- ALWAYS: selecting the Codex agent runs the selected marketplace skill through Codex using ChatGPT-workspace subscription entitlement supplied by a Codex access token
- ALWAYS: the Codex adapter invokes the selected skill without exposing the raw Codex access token to the agent or skill process and leaves no authenticated Codex state in the checked-out repository or persisted workflow artifacts
- NEVER: the subscription-backed Codex adapter accepts or requires an OpenAI Platform API key — API-billed execution is a different authentication contract

### Compliance

- ALWAYS: provider and runtime selection is a configuration axis (inputs such as `use_bedrock`, `use_vertex`, `model`) over a single invocation shape, never a separate workflow per provider ([audit])
- ALWAYS: the coding agent (Claude Code, Codex, Gemini) is a configuration axis over the same single invocation shape, defaulting to the Claude Code agent ([audit])
- ALWAYS: plugin and marketplace installation composes from caller inputs and, when opted in, the consumer's agent-native project configuration, and the tool boundary is composed to match the installed tools ([audit])
- NEVER: a surface embeds provider-specific invocation logic that bypasses this shared setup — provider variation lives here ([audit])
- NEVER: a surface embeds agent-specific invocation logic that bypasses this shared setup — agent variation lives here ([audit])
