# Agent Trigger

PROVIDES mention-triggered agent assistance — a workflow that fires when a configured trigger phrase appears on an issue, pull request, or review comment
SO THAT a repository's collaborators
CAN ask an AI coding agent to act on a thread by mentioning the trigger phrase, with the run authorized and the agent invoked through the shared substrate

## Assertions

### Compliance

- ALWAYS: the surface fires on the mention event shapes (issue and PR review comments, issues, PR reviews) and matches the configured trigger phrase ([review])
- ALWAYS: a run is gated by the authorization mechanism in `spx/32-security.enabler` and invoked through `spx/32-agent-invocation.enabler` ([review])
- NEVER: the surface acts for an actor the authorization gate rejects ([review])
