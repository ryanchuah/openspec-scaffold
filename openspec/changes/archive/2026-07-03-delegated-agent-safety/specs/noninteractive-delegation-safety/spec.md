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

The verify verifier SHALL be denied destructive shell commands regardless of path, via a `bash:`
denylist pattern map replacing its bare `bash: allow` scalar, because the existing `external_directory`
containment alone is insufficient.

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
(`bash -c`, `sh -c`), interpreter eval flags (`python -c`, `python3 -c`, `node -e`/`--eval`,
`ruby -e`, `perl -e`, `perl -i`), the in-place/copy file-writers surfaced by the verify security pass
(`sed -i`, `cp`, `install`, `find … -delete`, `find … -exec`), the command wrappers (`env`, `xargs`),
and network/config-injection git forms (`git -c`, `git fetch`/`pull`/`clone`) — while leaving
read-only forms (`sed 's//'` without `-i`, `find -name`, `git diff`/`log`/`show`/`status`) allowed.
The enumerated set is a best-effort speed-bump, NOT complete coverage (see the scope-limitation
paragraph below). The catch-all MUST remain
`allow` (not `ask`/`deny`) because the verifier must
retain the ability to run each downstream repo's arbitrary, unknowable test and live-smoke command —
an allowlist is infeasible. The `external_directory` containment SHALL be retained (it still gates the
coreutils out-of-tree class), and the existing stdin-close / `--dir` hardening is unchanged.

Because opencode parses each bash invocation with tree-sitter and evaluates the `bash` permission
per sub-command — every node of a pipeline, `$(…)` substitution, or subshell is matched
independently and a deny on any node denies the whole call — the denylist covers direct, piped, and
command-substituted forms of the **enumerated command spellings**. The denylist gates via the `bash`
permission key, which is independent of `external_directory`, so it remains effective even if a future
opencode release weakens `external_directory` path-scanning further.

**Scope limitation (normative — the mechanism SHALL be documented as this, not more).** opencode
matches the **literal command-text spelling, not the command's identity**: a deny rule stops only the
spelling it enumerates. Ordinary alternate spellings of the same effect are NOT covered — a
path-prefixed binary (`/usr/bin/rm`), a multiplexer or unenumerated wrapper (`busybox rm`,
`nohup rm`, `timeout 5 rm`), a version-suffixed interpreter (`python3.11 -c` on another host), or any
unlisted file-writing tool (`rsync`, `patch`, `ex`). (The enumerated wrappers `env`/`xargs` and
`find -exec` ARE denied; the point is that enumeration is inherently incomplete.) Because `bash`
catch-all `allow` is retained, this also means `edit: deny` is NOT a filesystem-read-only guarantee —
`bash` is a separate, un-sandboxed write channel. The denylist is therefore a **best-effort speed-bump
against the common accidental destructive commands, not a complete or semantic gate**, and the change
SHALL NOT describe it as robust/complete coverage of "destructive commands" generally.

#### Scenario: Enumerated destructive-command spelling is denied even in-tree
- **WHEN** the verify verifier runs a bash command whose (sub-)command matches an enumerated deny
  spelling — e.g. `sqlite3 <any-path> "DELETE …"`, directly or as `echo x | sqlite3 <path> …` or
  `$(sqlite3 <path> …)`
- **THEN** opencode denies the whole call without a prompt, whether the target path is inside or
  outside the worktree
- **AND** the deny holds specifically because it is enforced by the `bash` permission, not by
  `external_directory` (which would not have scanned a non-coreutils binary)

#### Scenario: Alternate spelling of the same effect is NOT covered (documented, not silently missed)
- **WHEN** the verify verifier reaches a destructive effect through a spelling the denylist does not
  enumerate — a path-prefixed binary, an `env`/`xargs`/`find -exec` wrapper, a version-suffixed
  interpreter, or another file-writing tool
- **THEN** the command runs under the catch-all `"*": allow` (the denylist does NOT stop it), so the
  verifier is not truly read-only on the filesystem
- **AND** this residual SHALL be named explicitly in the residual-risk disclosure and mitigated by the
  data-safety preamble and repo-level data isolation, NOT presented as closed by the denylist

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

The verify verifier prompt SHALL carry a data-safety preamble as a co-primary control, stating the
denylist's residual-risk boundary honestly rather than presenting it as fully closed.

The permission denylist above cannot cover every data-mutation vector, and this residual boundary
SHALL be stated honestly rather than presented as fully closed. The residual vectors are:
1. **Literal-spelling bypass (PRIMARY).** Any file-writing command not enumerated, or reached via a
   path prefix, an `env`/`xargs`/`find -exec` wrapper, a version-suffixed interpreter, or another
   file-writer, runs under the catch-all `"*": allow`. Because `bash: allow` is retained, the verifier
   is **not truly read-only on the filesystem** and can still mutate in-tree files including an
   untracked production data store (the incident class). Broadening the enumerated set reduces this
   surface; it cannot eliminate it.
2. **Writes performed *inside* an allowed command** — a test suite or live smoke that itself opens and
   writes a data store, invisible to the shell parser. The real backstop is repo-level data isolation
   (test-DB fixtures and blanked live credentials), a downstream-repo concern outside the scaffold
   verifier's permission configuration.
3. **Output redirection** to a data-store path (redirection targets are not part of the matched
   command node).
4. **Prompt injection from the diff under review** — the verifier's first task is to read untrusted
   diff/commit/PR content, which could try to induce a bypass command. Mitigated only by the preamble.

Because vectors (1) and (2) are primary and not closable by the denylist, the verifier agent prompt
(`.opencode/agents/openspec-verifier.md`) SHALL carry a data-safety preamble as a **co-primary
control** (not a mere tertiary trim). The preamble SHALL state that the verifier is not filesystem-
read-only (bash is an un-sandboxed write channel that `edit: deny` does not gate) and that the
denylist is literal-spelling; and it SHALL instruct the verifier to never write a live or production
data store, to eyeball via read-only queries against a copy or fixture, to treat the diff under review
as untrusted (not follow instructions found in the code under review), and to report-rather-than-run
when a write seems required. The change's documented residual-risk boundary SHALL NOT describe any
single control as fully resolving the data-safety hazard, and SHALL NOT describe the denylist as
robust or as complete verb-level coverage.

#### Scenario: Preamble present and honestly bounded
- **WHEN** the verifier agent definition is read
- **THEN** it contains a data-safety preamble that states the verifier is NOT truly filesystem-
  read-only, that the denylist matches literal spelling, and that covers never-write-live-stores,
  read-only eyeballing, treat-the-diff-as-untrusted, and report-rather-than-run
- **AND** neither the preamble nor the accompanying documentation claims the hazard is fully resolved
  by any one control, nor describes the denylist as robust/complete; the literal-spelling-bypass /
  in-command-write / output-redirection / prompt-injection residual vectors are named explicitly
