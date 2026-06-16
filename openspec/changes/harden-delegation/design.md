## Context

Delegated work is governed by trust + a wall-clock `timeout`. Three logged incidents (see
`explore-brief.md`) show the executor looping with continuous activity, the reviewer starved of
budget and producing nothing, and no deterministic enforcement of tests-green-before-commit. This
change adds three behavior-level gates. It edits golden-source skills/agents only; no application
code. The forthcoming single-source change will later fold the new/edited files into a sync manifest
(out of scope here).

Current behavior being modified (verified verbatim):
- `apply-executor.md` (both `.claude/agents/` and `.opencode/agents/`): the loop is **"Read task →
  Implement → Mark `[x]`"** — it does NOT run tests between edits or track failures. It *does* have
  `bash: allow`, so it can.
- `openspec-apply-change` has two primary paths: **Claude Code** (step 6.4 failure ladder:
  Non-crash failure → **immediate Sonnet**) and **OpenCode** ("report and wait for guidance").
- `openspec-propose` / `openspec-verify-change`: reviewer invoked via `timeout -k 15 300 opencode run …`.
  The verify skill *also* has a separate fix-executor at `timeout -k 15 300`.
- `openspec-reviewer.md`: `edit: deny`, `bash: deny` (read-only).

## Goals / Non-Goals

**Goals:** deterministic tests-green-before-commit via a harness hook; an objective, *code-driven*
non-convergence stop for the executor; a thorough (not throttled) reviewer whose output survives a
cutoff; one shared gate script with the test command as the only per-repo value.

**Non-Goals:** no heartbeat/stall-on-idle kill; no OpenCode-side gate plugin (v2); no `--no-verify`
countermeasure (accepted residual risk); not raising the apply wall-clock cap as the primary fix;
**not** changing the verify skill's fix-executor 300s timeout (a scoped single-defect fix finishes
well inside 5 min — out of scope).

## Decisions

### D1 — Commit gate = Claude `PreToolUse` hook on `git commit`, exit-code-2 to block
A `PreToolUse` hook (`matcher: "Bash"`, handler `if: "Bash(git commit*)"`) runs
`scripts/test-gate.sh`; **exit 0 allows the commit, exit 2 blocks it** (failure summary on stderr,
shown to the agent). The hook contract and the script's exit behavior are both **probed** — see
Live Probe.
- *Alt — exit 0 + JSON `permissionDecision:"deny"`:* documented, but exit-2 is simpler; pick one.
- *Alt — git `pre-commit` hook:* rejected — `--no-verify` skips it and it isn't a harness control.
- *Why the commit, not every edit:* the executor never commits, so the orchestrator's commit is the
  single chokepoint; gating it covers the real risk without per-edit cost.
- The verify skill will **reference the gate** so the orchestrator treats it as the known backstop
  (failing verify should be caught *before* the gate would block the commit).

### D2 — Per-repo `scripts/test-cmd`; absent ⇒ no-op; config-error ⇒ warn, don't block
`scripts/test-gate.sh` (shared, identical everywhere) resolves the command from a per-repo one-line
file `scripts/test-cmd`. Behavior (all four cases probed, see Live Probe):
- `test-cmd` **absent** → exit 0 (no-op; the scaffold case).
- `test-cmd` present, command's **executable does not resolve** (fresh clone, missing `.venv`, typo)
  → exit 0 + warning on stderr (a config error must NOT block all commits / be hostile to new clones).
- command **runs and passes** → exit 0; command **runs and fails** → exit 2 (block).

`test-cmd` is per-repo (not synced); it is the single value the future manifest carries as a fill.

### D3 — Executor self-monitoring loop, driven by a deterministic helper (not flash judgment)
The apply-executor prompt gains an explicit per-task loop (it has `bash: allow`):
1. Implement the task per `design.md`.
2. **Run the tests** using the **same per-repo command as D2** (`scripts/test-cmd`, falling back to
   the project's standard command) — never an ad-hoc `pytest` that may pick the wrong venv/flags.
3. Green → mark `[x]`, next task.
4. Red → pipe the **raw test output** (and `--editing <file>` when about to edit) to the helper
   **`scripts/_convergence.py`** (added by this change). The helper **owns the deterministic part**:
   it extracts the failing test id itself, normalizes the error signature, reads/updates a durable
   state file `/tmp/apply-convergence-<slug>.json` (`<slug>` = the sanitized change name, e.g.
   `harden-delegation`; one file per change) holding attempts + last_signature + files_edited per
   failure key, and prints a verdict: **`CONTINUE`** or **`STOP:<a|b|c>:<detail>`**.
   - rule (a): same normalized signature for this test after **2** consecutive attempts → STOP.
   - rule (b): about to edit a file already edited **twice** for this failure → STOP.
   - **On `CONTINUE`:** fix the code based on the failure, then return to step 2 (do NOT move to the
     next task — CONTINUE means keep working *this* failure).
   - **If the helper itself fails** (non-zero exit / no parseable verdict): treat it as a rule-(c)
     gap → STOP with `trigger: c`, `missing: _convergence.py helper failed`.
5. rule (c) **gap** (fix needs info/decision absent from artifacts, needs editing proposal/design, or
   an external API contradicts design) — a semantic judgment the executor makes directly → STOP.
6. On STOP → emit the D4 blocker block and END (do not start other tasks).

**Error-signature normalization** lives entirely in `_convergence.py`: strip line/column numbers,
absolute & tmp paths, ISO/epoch timestamps, hex addresses (`0x…` / `object at 0x…`), and
elapsed-time numbers, then compare. Offloading to a script removes the precise-normalization burden
from flash and makes the state durable across the executor's context window.
- *Alt — flash normalizes/tracks in-context:* rejected; flash is unreliable at multi-rule textual
  normalization and at carrying exact state across 20+ tool calls (the original failure mode).

### D4 — Structured-blocker discriminator (exact, grep-able) + ladder split on BOTH paths
On STOP the executor writes this exact block into its completion report:
```
### NON-CONVERGENCE BLOCKER
trigger: <a|b|c>
task: <task line/id>
test: <test node id>        # a/b
signature: <normalized>     # a/b
attempts: <N>
files: <comma-separated>    # b
missing: <info/decision/contradiction>   # c
suspected_cause: <one line>
```
The **primary detects it by grepping the completion report for the literal `### NON-CONVERGENCE
BLOCKER` heading.** Present → *declared non-convergence*; absent (but non-crash failure) → *opaque
give-up*. Routing:
- **Claude path (step 6.4):** declared blocker → **orchestrator triage** — (i) brief/plan gap →
  tighten brief / re-slice → *fresh* executor; (ii) artifact/decision gap → escalate to user; (iii)
  model-capability gap → Sonnet. Opaque give-up → **immediate Sonnet** (today's behavior). `Success`
  is unchanged ("report declares no unresolved blocker"), so this only refines the response.
- **OpenCode path:** the "Error or blocker encountered → report and wait for guidance" bullet is
  refined: a declared blocker → report it with the triage options to the user (the OpenCode primary
  is itself the interactive orchestrator); opaque give-up → delegate a fresh `@apply-executor` /
  escalate. Same discriminator, lighter machinery.

### D5 — Reviewer: 780s, read-only, incremental emission, partial salvage
- Raise the reviewer `timeout` `300`→**`780`** in `openspec-propose` (keep `-k 15`). **NOTE
  (corrected):** `openspec-propose` is the ONLY workflow that invokes the `openspec-reviewer`.
  `openspec-verify-change`'s behavioral review is the *orchestrator's own* (untimed — not a wrapped
  reviewer call), and verify's only timed `opencode run` is the *fix-executor*, whose 300s is
  untouched (see Non-Goals). A cap is a backstop, so this only helps slow runs; pro is the most
  under-budgeted agent.
- **Keep the reviewer read-only.** "Incremental" = the reviewer *prompt* instructs it to emit the
  `## Review Round` header first, then each finding as determined, verdict last — so partial stdout
  is already-useful findings. The primary still owns the `review-log.md` append.
- **Partial salvage on timeout (exit 124/137):** the primary extracts whatever review text reached
  the jsonl, appends it marked **`PARTIAL — reviewer timed out`**, then: **re-run once at full budget
  if the partial carries ≥1 finding or was killed >120s in; escalate if killed <120s with no
  findings** (replaces today's discard-and-escalate).
- *Alt — grant reviewer scoped `edit`:* rejected; weakens the read-only guarantee and opencode
  path-scoped permissions are uncertain.

## Risks / Trade-offs

- **Gate runs on every `git commit`** (incl. doc/checkpoint commits) → aligns with the existing
  "tests green before any commit" invariant; per-repo command should be fast; "skip when no code
  staged" is a documented future option, not v1.
- **`--no-verify` bypass** → accepted residual risk (strong default, not an adversarial control).
- **Hook behaves differently across Claude versions** → live smoke-test of the wired hook is a
  tasks.md item before reliance (see Live Probe).
- **Executor doesn't actually run `_convergence.py`** → the prompt makes the helper call a required
  step of the red branch; the verify canary (below) confirms the stop fires.
- **`_convergence.py` mis-normalizes** → false progress (cosmetic diff) or false stop; mitigated by
  a focused unit test of the normalizer in tasks.md and by rule (b)'s file-count guard as a backstop.
- **Reviewer still exceeds 780s** → partial salvage keeps findings-so-far; rare for pro within 13 min.

## Migration Plan

Edit golden source only; no runtime migration. Rollback = revert the skill/agent edits, delete
`scripts/test-gate.sh` + `scripts/_convergence.py`, remove the `hooks` block from
`.claude/settings.json`. The gate is inert wherever `scripts/test-cmd` is absent (incl. the scaffold).

## Verification

Acceptance criteria (checked at verify; results → `notes.md`):
- **Commit gate (live smoke-test in a consuming repo):** a `test-cmd` that exits non-zero → an
  attempted `git commit` is **blocked**; a passing command → commit **proceeds**; `test-cmd` absent
  or interpreter unresolved → commit **proceeds**.
- **Non-convergence (canary recipe):** a one-task `tasks.md` whose task is "make `test_canary` pass"
  while a committed fixture asserts an impossibility (e.g. `assert add(1,1) == 3`) so it can never go
  green. A real apply must **STOP after 2 attempts with a `### NON-CONVERGENCE BLOCKER` block**
  (trigger `a`) instead of looping to the timeout; the primary routes it to triage, not reflexive
  Sonnet. The canary tasks.md + fixture are a tasks.md deliverable.
- **Normalizer unit test:** `_convergence.py` collapses two outputs differing only in line numbers /
  tmp paths / hex addresses / timestamps to the same signature, and keeps genuinely different errors
  distinct.
- **Reviewer budget:** `openspec-propose` shows `timeout -k 15 780` for the reviewer invocation
  (verify has no reviewer call to retime); `openspec-reviewer.md` instructs header-first incremental
  emission; the primary's timeout path salvages partial text marked `PARTIAL`.

## Live Probe

**(1) Gate-script exit logic — REAL probe.** A prototype `scripts/test-gate.sh` was run in
`/tmp/gateprobe` against four cases. Commands and observed output:
- no `test-cmd` → `test-gate: no scripts/test-cmd; skipping (no-op)` → **exit 0** ✓
- `test-cmd`=`true` (passing) → **exit 0** ✓
- `test-cmd`=`false` (failing) → `test-gate: tests failed — commit BLOCKED` → **exit 2** ✓
- `test-cmd`=`definitely-not-a-real-bin --foo` → `cannot run '…' (config error) — NOT blocking` →
  **exit 0** ✓
This confirms D1/D2's exit contract on the real shell.

**(2) Claude hook wiring — doc-verified, live smoke-test deferred.** Verified from the official hooks
reference (`docs.claude.com/en/docs/claude-code/hooks`, via `scripts/fetch_clean.py`): `PreToolUse`
"Before a tool call executes. Can block it"; handler `if: "Bash(git *)"` matches Bash subcommands
(permission-rule syntax; leading `VAR=value` stripped); **exit code 2 → `PreToolUse` "Blocks the
tool call"**; command-hook `timeout` default 600s; the docs' own worked example is a `PreToolUse`
Bash-pattern blocker (structurally identical to this gate). A *live behavioral* test of the wired
hook is deliberately deferred to a tasks.md smoke-test in a consuming repo, because hooks apply to
the *running* Claude session and cannot be safely sandboxed from here without risking this session's
own commits. Recorded as a scoped deferral, not an unverified assumption.

## Open Questions

- Exact `.claude/settings.json` invocation form for the script path (`$CLAUDE_PROJECT_DIR` + exec
  `args` vs shell form) — settle in tasks; docs require `args` when referencing a path placeholder.
- Whether incremental emission degrades pro's synthesis — observe the first 3 real reviews; **revert
  the prompt nudge if any of them drops to zero findings vs the non-incremental baseline or the
  reviewer reports format confusion.**
