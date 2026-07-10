# Delta — noninteractive-delegation-safety (verify-stack-redirect)

Corrective delta: the promoted requirement still describes an abandoned OpenCode Task-tool
verifier spawn path (superseded by the `tier-review-tightening` decision, 2026-06-17 — both
platforms invoke the verifier via `opencode run`), and its pass parenthetical names the
pre-redirect pro+flash same-checklist chain. Permission-posture requirements are untouched:
the lens pass uses the same `openspec-verifier` agent, so every existing containment
requirement applies to it unchanged.

## MODIFIED Requirements

### Requirement: Delegated opencode invocations are hardened against permission hangs
Every delegated `opencode run` invocation in the OpenSpec workflow — the propose reviewer, the apply executor, the archive executor, the verify fix-executor, and the verify verifier passes (the `deepseek/deepseek-v4-pro` behavioral pass and, for COMPLEX changes, the `deepseek/deepseek-v4-flash` lens pass) — SHALL close stdin (`< /dev/null`) so that any permission prompt opencode cannot resolve from configuration auto-rejects (fail-fast) instead of blocking on stdin that no one will answer. Each such invocation SHALL also pass `--dir <repoRoot>` so artifact paths resolve inside the worktree. Closing stdin is the load-bearing guarantee; `--dir` is hygiene and does not by itself prevent the hang. Both orchestrator platforms invoke the verifier via `opencode run`, so this requirement applies to every verifier pass on either platform.

#### Scenario: Unanswerable prompt fails fast instead of hanging
- **WHEN** a delegated `opencode run` triggers a permission that is not resolved to `allow`/`deny` by configuration and there is no TTY to answer it
- **THEN** the invocation auto-rejects that action and the run continues or returns, rather than blocking until the `timeout` wrapper kills it

#### Scenario: Every delegated invocation closes stdin
- **WHEN** any of the propose, apply, archive, or verify skills invokes `opencode run` (including the verify verifier behavioral and lens passes)
- **THEN** the documented invocation includes `< /dev/null`
- **AND** it includes `--dir <repoRoot>`
