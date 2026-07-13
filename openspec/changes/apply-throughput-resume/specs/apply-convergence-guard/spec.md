# Delta — apply-convergence-guard (apply-throughput-resume)

OW-10 changes the apply-executor's green-path test cadence from "full documented suite after every
task" to "targeted tests (the same tool, scope-narrowed to the task's touched modules) per task, plus
the full documented command once before completing the assignment." Requirement 1's existing
"prefer the same per-repo test command … never an improvised command" clause was written to ban
wrong-venv/wrong-flags ad-hoc commands, not to ban scope-narrowing the same tool — this delta
reconciles the two so the cadence change does not read as a spec violation. Nothing else in the
capability changes (the red-path stop rules, the `_convergence.py` contract, blocker format, triage
routing, and the canary are all untouched).

## MODIFIED Requirements

### Requirement: The apply-executor stops on non-convergence
The apply-executor SHALL continue healthy `write → test → fix` iteration, but SHALL stop editing and report a blocker when it detects non-convergence, defined as ANY of: (a) the same failing test still fails with the same normalized error signature after 2 consecutive fix attempts aimed at it; (b) it has edited the same file a 3rd time to resolve the same failure; (c) the fix requires information or a decision absent from the artifacts, requires editing `proposal.md`/`design.md`, or an external API behaves contrary to `design.md`. For its test runs the executor SHALL use the same per-repo test **tool** as the commit-test-gate (`scripts/test-cmd`, falling back to the project's standard/documented test command when `scripts/test-cmd` is absent) — never an *improvised* command that could select the wrong venv or flags. It MAY scope-narrow that same tool to the task's touched modules for the per-task green-path check (e.g. running the documented tool against the test file(s) covering the files this task changed), and on the red path it re-runs the failing test's module; scope-narrowing the same tool is NOT an improvised command. The executor SHALL run the full documented command (unnarrowed) at least once before completing its assignment, so a cross-module regression is still gated within the apply invocation rather than escaping to verify. After emitting a blocker the executor SHALL end the run and SHALL NOT start any remaining task.

#### Scenario: Stalled failure (rule a)
- **WHEN** the same test fails with the same normalized error signature after 2 consecutive fix attempts
- **THEN** the executor stops editing and emits a structured blocker

#### Scenario: Repeated touch (rule b)
- **WHEN** the executor has edited a file a third time for the same failure
- **THEN** the executor stops editing and emits a structured blocker

#### Scenario: Knowledge or artifact gap (rule c)
- **WHEN** a fix would require information/decisions absent from the artifacts, editing the frozen proposal/design, or contradicts `design.md`'s stated external-API behavior
- **THEN** the executor stops editing and emits a structured blocker

#### Scenario: Healthy iteration is not interrupted
- **WHEN** consecutive attempts produce *different* normalized error signatures (the failure is changing)
- **THEN** the executor keeps iterating and is NOT stopped, UNLESS the high backstop ceiling
  `_MAX_ATTEMPTS` (20) is reached — at which point a declared blocker is emitted regardless of
  whether the signature is changing, as a final guarantee against a wall-clock timeout
- **AND** it stays on the *same* failure (fix → re-run that failing test's module, not necessarily the whole suite), rather than advancing to another task

#### Scenario: Oscillation is detected and stopped
- **WHEN** the normalized error signature alternates between two values (S1→S2→S1→S2…) such that
  `signature == prev_signature` and `attempts >= 3`
- **THEN** the executor stops and emits a declared blocker with trigger `a` naming the oscillation,
  even though consecutive signatures are different
- **AND** a genuinely progressing run (always-different signatures) is NOT interrupted before the
  high backstop ceiling

#### Scenario: Absolute backstop ceiling catches pathological cases
- **WHEN** the attempt count for a failure reaches `_MAX_ATTEMPTS` (20)
- **THEN** the executor stops and emits a declared blocker with trigger `a` naming the ceiling,
  even if the oscillation detection missed the pattern — this is the final guarantee that the run
  ends in a declared blocker rather than a wall-clock timeout

#### Scenario: Green-path per-task check may be scope-narrowed
- **WHEN** the executor finishes a task's edit and runs its green-path check
- **THEN** it MAY run the same documented test tool narrowed to the test(s) covering the files this task changed, rather than the whole suite
- **AND** this scope-narrowing is not treated as an "improvised command", because it is the same tool/venv/flags with a narrowed target

#### Scenario: Full suite gates the assignment before completion
- **WHEN** the executor has completed the last task in its assignment
- **THEN** it runs the full documented command (unnarrowed) once and only reports success if it passes
- **AND** if that full run is red, the run enters the normal red-path convergence handling rather than completing

#### Scenario: Stopping ends the run
- **WHEN** the executor emits a `### NON-CONVERGENCE BLOCKER` for a task
- **THEN** it ends the run immediately and does NOT begin any remaining task
