# Parked: PostToolUse large-Bash-output nudge hook (OW-14 item c — deferred)

- **From:** `instruction-surface-coherence` (OW-14), notes.md assumption A1.
- **What:** Add a Claude-only `PostToolUse` hook that nudges the orchestrator when a Bash
  invocation's output exceeds a threshold — pointing to the `delegation-by-default` rule
  so large mechanical output never sits in the orchestrator's context unexamined.
- **Why deferred:** It is Claude-only harness-private surface needing its own
  decision-record carve-out (like the commit-test-gate hook). The agent-neutral
  instruction edits (canonical delegation rule + point-of-action cues) already deliver
  the rule's substance. Reverse if the operator wants the hook in-scope before the
  wave-2 session closes.
- **Priority:** Low — monitoring-only until a concrete incident shows the gap matters.
