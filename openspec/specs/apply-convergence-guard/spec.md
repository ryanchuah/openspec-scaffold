## Purpose

Stop the apply-executor from looping on a stuck failure by giving it an objective, deterministic non-convergence stop condition, and route a diagnosed blocker to orchestrator triage instead of reflexive escalation.

## Requirements

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

### Requirement: Non-convergence detection is deterministic, not in-context judgment
The rule (a) and (b) checks SHALL be computed by a helper script that normalizes the error signature
and maintains durable per-change state, so detection does not depend on the executor model's
in-context tracking. The executor SHALL pass the helper the raw test output. The helper derives the
edited-file set from `git diff` content fingerprints; the `--editing` input is an optional hint,
no longer load-bearing for rule (b)'s file-touch tracking. If the helper cannot run or returns no
parseable verdict, the executor SHALL treat that as a rule (c) gap and stop.

#### Scenario: Cosmetic-only differences count as no progress
- **WHEN** two test outputs differ only in line numbers, paths, timestamps, or hex addresses
- **THEN** the normalizer yields the same signature (no progress), so rule (a) can trip

#### Scenario: Genuinely different failures stay distinct
- **WHEN** two attempts fail with substantively different errors
- **THEN** the normalizer yields different signatures and rule (a) does NOT trip

#### Scenario: The signature is scoped to the failing test's section
- **WHEN** the test run produces output for several tests, only one of which fails
- **THEN** the convergence helper extracts only the failing test's section of the output before
  normalizing, so unrelated churn (summary counts, other failures, warnings) does NOT change the
  signature — rule (a) correctly fires when that targeted test fails identically
- **AND** if the section boundary cannot be located, the helper falls back to whole-output
  normalization (preserving legacy behavior)

#### Scenario: The state key is path-stable across node id formats
- **WHEN** the same test is identified with different path prefixes (e.g. absolute
  `/abs/tests/test_foo.py::test_bar` vs relative `tests/test_foo.py::test_bar`)
- **THEN** the helper reduces both to the same normalized key (`test_foo.py::test_bar`), so
  state tracking is robust against node id format changes — the raw `test_id` is preserved for
  human-readable detail

#### Scenario: Error messages differing only in path-ish substrings stay distinct
- **WHEN** two error messages differ only in their filesystem-like `/path/to/file.ext` substrings
- **THEN** the path normalizer matches only concrete `name.ext`-terminated paths, NOT extensionless
  paths (`/usr/bin/python`) or trailing-slash dirs (`/tmp/build/`) or non-path `/` tokens (regex
  `a/b`), so genuinely distinct errors do NOT collapse to the same signature

#### Scenario: Git-diff-derived edited files drive rule (b)
- **WHEN** the helper is invoked
- **THEN** it derives the list of edited files (per-attempt delta) from `git diff --name-only HEAD`
  content fingerprints, and tracks `files_edited` per failure — so rule (b) fires after 3 distinct
  edit events for the same file, even when the executor omits `--editing`
- **AND** `--editing` is retained as an optional hint; when git is unavailable the helper falls
  back to `--editing`-only, and when both are absent logs a warning about zero rule-(b) coverage

#### Scenario: Helper failure is fail-safe
- **WHEN** the convergence helper exits non-zero or emits no parseable verdict
- **THEN** the executor stops and emits a structured blocker with trigger `c` naming the helper failure

### Requirement: A declared blocker is machine-discriminable from an opaque give-up
On stopping, the executor SHALL emit a `### NON-CONVERGENCE BLOCKER` block carrying these distinct
fields: `trigger`, `task`, `test`, `signature`, `attempts`, `files`, `missing` (the blocking
info/decision/contradiction), and `suspected_cause` (a one-line diagnostic) — `missing` and
`suspected_cause` are separate fields, not merged. The primary SHALL distinguish a *declared* blocker
from an *opaque* give-up by detecting that exact heading in the completion report.

#### Scenario: Declared blocker present
- **WHEN** the completion report contains a `### NON-CONVERGENCE BLOCKER` block
- **THEN** the primary treats it as declared non-convergence and routes it to orchestrator triage

#### Scenario: Opaque give-up (Claude path)
- **WHEN** a non-crash failure occurs with no `### NON-CONVERGENCE BLOCKER` block on the Claude path
- **THEN** the primary treats it as an opaque give-up and falls back to the Sonnet subagent

#### Scenario: Opaque give-up (OpenCode path)
- **WHEN** a non-crash failure occurs with no `### NON-CONVERGENCE BLOCKER` block on the OpenCode path
- **THEN** the primary dispatches a fresh `@apply-executor` or escalates to the user (not Sonnet)

### Requirement: Recovery from a declared blocker is the orchestrator's decision
On a declared non-convergence blocker the primary SHALL choose recovery by triage rather than
reflexively escalating to Sonnet, on BOTH delegation paths. Triage options SHALL include: tighten
the brief / re-slice and dispatch a fresh executor (brief/plan gap); escalate to the user
(artifact/decision gap); or spawn a Sonnet subagent (model-capability gap). This recovery routing
SHALL hold in ALL autonomy modes: an autonomy grant relaxes interactive checkpointing but
SHALL NOT replace declared-blocker triage with an unconditional "non-crash failure → Sonnet
immediately" ladder.

#### Scenario: Claude delegation path
- **WHEN** the Claude-Code primary receives a declared blocker
- **THEN** it selects a triage branch (fresh executor / escalate / Sonnet) instead of auto-Sonnet

#### Scenario: OpenCode delegation path
- **WHEN** the OpenCode primary receives a declared blocker
- **THEN** it reports the blocker with the triage options to the user rather than silently waiting

#### Scenario: Recovery routing holds under autonomy
- **WHEN** the primary is operating under an autonomy grant and receives a declared blocker
- **THEN** it still selects a triage branch and does NOT reflexively escalate to Sonnet
- **AND** the autonomy guidance does NOT state an unconditional "non-crash failure → Sonnet immediately" ladder

### Requirement: The convergence guard ships with a hardened, instruction-gated canary
The repository SHALL carry an end-to-end canary fixture that an honest apply-executor cannot satisfy by editing the file it is instructed to edit. The impossibility SHALL live in an implementation module that a frozen test imports — NOT in an assertion inside the file the executor is told to edit. The canary's `tasks.md` SHALL list only the implementation module as editable and SHALL mark the test file do-not-edit. Running the apply-executor against the canary SHALL produce a declared `### NON-CONVERGENCE BLOCKER` (trigger a, b, or c — whichever the guard reaches first), not a green result and not a wall-clock timeout. The freeze is instruction-gated (it hardens against the honest edit-the-assertion shortcut, not a malicious rewrite), which is sufficient for the canary's purpose.

#### Scenario: The canary cannot be made green by editing the impl
- **WHEN** an honest apply-executor runs the canary, editing only the implementation module it is told to edit
- **THEN** no implementation of that module can satisfy the frozen test
- **AND** the executor never reaches a green result

#### Scenario: The canary forces a declared non-convergence blocker
- **WHEN** the apply-executor exhausts its convergence budget against the canary
- **THEN** it emits a `### NON-CONVERGENCE BLOCKER` whose trigger is a, b, or c — whichever the guard reaches first — rather than a green result or a wall-clock timeout

#### Scenario: The impossibility is not in the editable surface
- **WHEN** the canary fixture is inspected
- **THEN** the contradiction lives in a frozen test that imports an implementation module
- **AND** it is NOT an assertion inside a file the canary's `tasks.md` lists as editable
