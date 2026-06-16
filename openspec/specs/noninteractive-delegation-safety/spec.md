## Purpose

Keep a delegated `opencode run` from hanging on an unanswerable permission prompt, while preserving each agent's legitimate tool access and containing write-capable executors to the worktree.

## Requirements

### Requirement: Delegated opencode invocations are hardened against permission hangs
Every delegated `opencode run` invocation in the OpenSpec workflow — the propose reviewer, the apply executor, the archive executor, and the verify fix-executor — SHALL close stdin (`< /dev/null`) so that any permission prompt opencode cannot resolve from configuration auto-rejects (fail-fast) instead of blocking on stdin that no one will answer. Each such invocation SHALL also pass `--dir <repoRoot>` so artifact paths resolve inside the worktree. Closing stdin is the load-bearing guarantee; `--dir` is hygiene and does not by itself prevent the hang.

#### Scenario: Unanswerable prompt fails fast instead of hanging
- **WHEN** a delegated `opencode run` triggers a permission that is not resolved to `allow`/`deny` by configuration and there is no TTY to answer it
- **THEN** the invocation auto-rejects that action and the run continues or returns, rather than blocking until the `timeout` wrapper kills it

#### Scenario: Every delegated invocation closes stdin
- **WHEN** any of the propose, apply, archive, or verify skills invokes `opencode run`
- **THEN** the documented invocation includes `< /dev/null`
- **AND** it includes `--dir <repoRoot>`

### Requirement: Delegated agents leave no reachable ask-permission on their legitimate path
Each delegated agent's permission configuration SHALL leave no `ask`-default guard reachable on the path the agent legitimately needs, split by destructive capability. The read-only reviewer (`bash: deny`, `edit: deny`) SHALL set `external_directory: allow`. The write-capable executors (apply and archive, both `bash: allow` and `edit: allow`) SHALL set `external_directory` to deny every out-of-tree path except `/tmp` (`{ "*": deny, "/tmp/**": allow }`). Because opencode evaluates permission patterns last-match-wins, the catch-all `"*"` rule SHALL be listed before any more-specific allow rule. Only `external_directory` requires explicit per-agent configuration here; `doom_loop` and any other `ask`-default permission are neutralized generically by the stdin close in the preceding requirement, not by per-agent rules.

#### Scenario: Read-only reviewer reads out-of-tree without a prompt
- **WHEN** the read-only reviewer reads an artifact located outside the worktree
- **THEN** the read is allowed without a permission prompt
- **AND** the reviewer still cannot write or execute anything, in or out of tree

#### Scenario: Write-capable executor is contained out-of-tree
- **WHEN** a write-capable executor touches a path outside the worktree other than `/tmp`
- **THEN** the action is denied without a prompt

#### Scenario: Apply-executor /tmp write is preserved
- **WHEN** the apply-executor writes its convergence verdict under `/tmp`
- **THEN** the write is allowed

#### Scenario: Catch-all ordering is correct
- **WHEN** an agent's `external_directory` object lists a catch-all deny and a specific allow
- **THEN** the catch-all `"*"` is listed first so the last-match-wins evaluation does not clobber the specific allow
