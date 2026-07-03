## MODIFIED Requirements

### Requirement: Delegated agents leave no reachable ask-permission on their legitimate path
Each delegated agent's permission configuration SHALL leave no `ask`-default guard reachable on the path the agent legitimately needs, split by destructive capability. The read-only reviewer (`bash: deny`, `edit: deny`) SHALL set `external_directory: allow`. The write-capable executors (apply and archive, both `bash: allow` and `edit: allow`) SHALL set `external_directory` to deny every out-of-tree path except `/tmp` (`{ "*": deny, "/tmp/**": allow }`). A bash-capable but write-denied agent — the verify verifier (`edit: deny`, and `bash` set to a destructive-command denylist per the "Verify verifier is denied destructive shell commands regardless of path" requirement rather than a blanket `bash: allow`) — SHALL take the same executor-style containment (`{ "*": deny, "/tmp/**": allow }`) rather than the read-only reviewer's `external_directory: allow`, because its catch-all `"*": allow` bash rule leaves it write-capable in practice and `external_directory` alone does not gate non-coreutils bash commands. Because opencode evaluates permission patterns last-match-wins, the catch-all `"*"` rule SHALL be listed before any more-specific allow rule. Only `external_directory` and (for the verifier) the `bash` denylist require explicit per-agent configuration here; `doom_loop` and any other `ask`-default permission are neutralized generically by the stdin close in the preceding requirement, not by per-agent rules.

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

#### Scenario: Bash-capable write-denied verifier is contained out-of-tree
- **WHEN** the verify verifier (bash catch-all allow with a destructive-command denylist, edit denied) touches a path outside the worktree other than `/tmp`
- **THEN** the action is denied without a prompt
- **AND** it still cannot edit files anywhere, because its `edit` permission is denied

#### Scenario: Catch-all ordering is correct
- **WHEN** an agent's `external_directory` object lists a catch-all deny and a specific allow
- **THEN** the catch-all `"*"` is listed first so the last-match-wins evaluation does not clobber the specific allow

## ADDED Requirements

### Requirement: Verify verifier is denied destructive shell commands regardless of path

The existing `external_directory` containment on the verify verifier
(`{ "*": deny, "/tmp/**": allow }`) is insufficient to prevent the verifier from mutating a
production data store, because opencode's `external_directory` path-scanning for bash commands is
applied ONLY to a hardcoded coreutils command allowlist (`rm, cp, mv, cat, chmod, chown, mkdir,
touch, …`). A destructive invocation whose binary is outside that allowlist — `sqlite3`, `psql`,
`mysql`, `mongo`, `redis-cli`, `dd`, `tee`, or an interpreter/redirection — is never path-scanned and
runs unimpeded under `bash: allow`. This is the confirmed 2026-06-28 incident class (the verifier
mutated a downstream production SQLite DB while `external_directory` scoping was already in force).

Therefore the verify verifier (`.opencode/agents/openspec-verifier.md`) SHALL replace its
`bash: allow` scalar with a `bash:` **denylist pattern map**: a catch-all `"*": allow` listed FIRST
(opencode evaluates permission patterns last-match-wins via `findLast`), followed by explicit `deny`
rules for destructive command verbs a read-only reviewer never legitimately needs — at minimum the
raw data-store clients (`sqlite3`, `psql`, `mysql`, `mongo`/`mongosh`, `redis-cli`), the filesystem
mutators (`rm`, `rmdir`, `mv`, `dd`, `truncate`, `shred`, `tee`), mutating git subcommands (`push`,
`commit`, `reset`, `checkout`, `restore`, `clean`, `rebase`, `merge`), shell wrappers
(`bash -c`, `sh -c`), and interpreter eval flags (`python -c`, `python3 -c`, `node -e`/`--eval`,
`ruby -e`, `perl -e`) — the primary single-command wrapper-evasion path. The catch-all MUST remain
`allow` (not `ask`/`deny`) because the verifier must
retain the ability to run each downstream repo's arbitrary, unknowable test and live-smoke command —
an allowlist is infeasible. The `external_directory` containment SHALL be retained (it still gates the
coreutils out-of-tree class), and the existing stdin-close / `--dir` hardening is unchanged.

Because opencode parses each bash invocation with tree-sitter and evaluates the `bash` permission
per sub-command — every node of a pipeline, `$(…)` substitution, or subshell is matched
independently and a deny on any node denies the whole call — the denylist covers direct, piped, and
command-substituted forms of the destructive commands. The denylist gates via the `bash` permission
key, which is independent of `external_directory`, so it remains effective even if a future opencode
release weakens `external_directory` path-scanning further.

#### Scenario: Destructive data-store command is denied even in-tree
- **WHEN** the verify verifier runs a bash command whose (sub-)command is a denied verb — e.g.
  `sqlite3 <any-path> "DELETE …"`, directly or as `echo x | sqlite3 <path> …` or `$(sqlite3 <path> …)`
- **THEN** opencode denies the whole call without a prompt, whether the target path is inside or
  outside the worktree
- **AND** the deny holds specifically because it is enforced by the `bash` permission, not by
  `external_directory` (which would not have scanned a non-coreutils binary)

#### Scenario: Legitimate read-only verification commands still run
- **WHEN** the verify verifier runs the commands its review legitimately requires — `git diff`,
  `git log`, `git show`, `git status`, the project's test command (`pytest`, `scripts/test-cmd`, or
  the documented equivalent), and read-only inspection
- **THEN** the catch-all `"*": allow` permits them (they match no deny rule), so the verifier's core
  behavioral review — re-run the full suite, eyeball real output, run live smokes — is unimpaired

#### Scenario: Catch-all ordering is correct for the bash map
- **WHEN** the verifier's `bash` permission lists a catch-all allow and specific deny rules
- **THEN** the catch-all `"*": allow` is listed FIRST so the last-match-wins evaluation lets each
  specific `deny` rule take effect

### Requirement: Verify verifier prompt carries a data-safety preamble as the judgment layer

The permission denylist above cannot cover every data-mutation vector, and this residual boundary
SHALL be stated honestly rather than presented as fully closed. After the eval-flag denials, the
residual vectors are: (1) — the PRIMARY residual — writes performed *inside* an allowed command, e.g.
a test suite or live smoke that itself opens and writes a data store, invisible to the shell parser;
(2) output redirection to a data-store path (redirection targets are not part of the matched command
node); and (3) determined multi-step evasion (writing a script to an allowed path such as `/tmp` then
executing it, or an eval form outside the enumerated set) — outside the accidental-incident threat
model but acknowledged, not hidden. The real backstop for vector (1) is repo-level test isolation
(test-DB fixtures and blanked live credentials), which is a downstream-repo concern outside the
scaffold verifier's permission configuration.

The verifier agent prompt (`.opencode/agents/openspec-verifier.md`) SHALL therefore carry a
data-safety preamble instructing it, as a judgment-layer control: never issue writes to a live or
production data store; when eyeballing real output, read via read-only queries against a copy or a
test fixture rather than the live store; and treat the permission denylist as a backstop, not a
license. The preamble is explicitly the tertiary control (mechanism first, then this), and the
verifier's documented residual-risk boundary SHALL NOT describe any single control as fully resolving
the data-safety hazard.

#### Scenario: Preamble present and honestly bounded
- **WHEN** the verifier agent definition is read
- **THEN** it contains a data-safety preamble covering read-only eyeballing and never-write-live-stores
- **AND** neither the preamble nor the accompanying documentation claims the hazard is fully resolved
  by any one control; the in-command-write / output-redirection / multi-step-evasion residual vectors
  are acknowledged
