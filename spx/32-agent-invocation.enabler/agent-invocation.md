# Agent Invocation

PROVIDES a common agent-run setup — coding-agent selection (Claude Code, Codex, Gemini), provider and runtime routing (Anthropic API, Bedrock, Vertex, OpenAI / cloud review, and further providers), agent authentication including subscription-backed Codex authentication, agent plugin and marketplace installation, and tool-boundary composition
SO THAT this product's agent-surface nodes
CAN invoke an AI coding agent through one configurable shape regardless of agent and provider, with the required plugins installed and the matching tools allowed

## Assertions

### Compliance

- ALWAYS: selecting the Codex agent runs the selected marketplace skill through Codex using ChatGPT-workspace subscription entitlement supplied by a Codex access token ([audit])
- ALWAYS: the Codex adapter invokes the selected skill without exposing or logging the raw Codex access token, stores authenticated state outside the checkout, never caches or uploads that state, and deletes it after success or failure before the job ends so none survives in the repository, workflow artifacts, or a shared self-hosted runner ([audit])
- NEVER: the subscription-backed Codex adapter accepts or requires an OpenAI Platform API key or routes through the API-key proxy in `openai/codex-action` — API-billed execution is a different authentication contract ([audit])
- ALWAYS: provider and runtime selection is a configuration axis (inputs such as `use_bedrock`, `use_vertex`, `model`) over a single invocation shape, never a separate workflow per provider ([audit])
- ALWAYS: the coding agent (Claude Code, Codex, Gemini) is a configuration axis over the same single invocation shape, defaulting to the Claude Code agent ([audit])
- ALWAYS: plugin and marketplace installation composes from caller inputs and, when opted in, the consumer's agent-native project configuration, and the tool boundary is composed to match the installed tools ([audit])
- NEVER: a surface embeds provider-specific invocation logic that bypasses this shared setup — provider variation lives here ([audit])
- NEVER: a surface embeds agent-specific invocation logic that bypasses this shared setup — agent variation lives here ([audit])
