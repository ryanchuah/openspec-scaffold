## 1. Commit-test gate

- [x] 1.1 Create `scripts/test-gate.sh` (executable) implementing the probed exit contract: `scripts/test-cmd` absent OR present-but-empty/whitespace-only → exit 0 (no-op); present but executable does not resolve → exit 0 + stderr warning (config error, don't block); command runs and passes → exit 0; command runs and fails → exit 2 with the failure summary on stderr.
- [x] 1.2 Add a `PreToolUse` hook to `.claude/settings.json`: `matcher: "Bash"`, handler `if: "Bash(git commit*)"`, `type: "command"` running `scripts/test-gate.sh` via `$CLAUDE_PROJECT_DIR` (exec `args` form, since it references a path), `timeout: 600`.
- [x] 1.3 Document the per-repo `scripts/test-cmd` convention (one-line test command; absent ⇒ gate no-op) in the `test-gate.sh` header comment and a short note in `ai-docs/`. The scaffold ships NO `scripts/test-cmd` (gate stays inert here).

## 2. Convergence helper

- [x] 2.1 Create `scripts/_convergence.py`: read raw test output on stdin; accept `--task <id>`, `--change <slug>`, optional `--editing <file>`; extract the failing test id itself; normalize the error signature (strip line/col numbers, absolute & tmp paths, ISO/epoch timestamps, hex addresses incl. `object at 0x…`, elapsed-time numbers); read/update durable state `/tmp/apply-convergence-<slug>.json` (per failure key: attempts, last_signature, files_edited); print `CONTINUE` or `STOP:<a|b|c>:<detail>` (rule a = same signature after 2 attempts; rule b = 3rd edit of same file for same failure).
- [x] 2.2 Create `scripts/test_convergence.py` (stdlib `unittest`, no pytest dep) covering: cosmetic-only differences (line numbers / tmp paths / hex / timestamps) normalize to the same signature; genuinely different errors stay distinct; rule (a) trips after 2 same-signature attempts; rule (b) trips on the 3rd edit of one file. Run it and confirm green.

## 3. Apply-executor self-monitoring (both harnesses, kept byte-identical)

- [x] 3.1 (requires T2.1) Edit `.claude/agents/apply-executor.md`: replace the bare "Read → Implement → Mark `[x]`" loop with the D3 per-task loop — implement; run the per-repo test command (`scripts/test-cmd`, else the project's standard command, never improvised); green → mark `[x]`; red → pipe raw output (and `--editing <file>`) to `scripts/_convergence.py` and obey `CONTINUE` (fix → re-run the failing test's module, stay on this failure) / `STOP`. The executor STOPs on a `STOP:` verdict, on helper failure (⇒ rule c), OR when it itself detects a rule-(c) gap (fix needs info/decision absent from artifacts, needs editing proposal/design, or an external API contradicts design). On STOP, emit the exact 8-field `### NON-CONVERGENCE BLOCKER` block (`trigger`, `task`, `test`, `signature`, `attempts`, `files`, `missing`, `suspected_cause`) and END the run without starting remaining tasks.
- [x] 3.2 Apply the identical changes to `.opencode/agents/apply-executor.md` so the two stay in sync.

## 4. Apply-skill failure ladder (both delegation paths)

- [x] 4.1 (requires T3.1) Edit `.claude/skills/openspec-apply-change/SKILL.md` Claude path (step 6.3–6.4): detect a declared blocker by grepping the completion report for the literal `### NON-CONVERGENCE BLOCKER` heading; route declared → orchestrator triage (tighten brief + fresh executor / escalate to user / Sonnet by cause); opaque give-up (no block) → immediate Sonnet (unchanged).
- [x] 4.2 Edit the OpenCode path of the same skill: declared blocker → report it with the triage options to the user; opaque give-up → dispatch a fresh `@apply-executor` or escalate (NOT Sonnet).

## 5. Reviewer budget + incremental output (propose-only timeout)

- [x] 5.1 Edit `.opencode/agents/openspec-reviewer.md`: instruct header-first incremental emission (`## Review Round` header first, each finding as determined, verdict last); keep it read-only (`edit: deny`, `bash: deny`).
- [x] 5.2 Edit `.claude/skills/openspec-propose/SKILL.md`: change the reviewer wrapper `timeout -k 15 300` → `timeout -k 15 780`; and **replace step 4's `If opencode run fails …` clause** (the current discard-and-escalate path) with the salvage path — on a reviewer timeout, salvage partial review text from the jsonl, append it marked `PARTIAL — reviewer timed out`, and apply the heuristic (≥1 finding or killed >120s → re-run once at full budget; else escalate). Avoid creating a second, conflicting timeout-handling path.
- [x] 5.3 Edit `.claude/skills/openspec-verify-change/SKILL.md`: add a reference that the commit gate backstops "tests green before commit" (so failing verify is caught before the gate would block). Do NOT change the fix-executor `timeout -k 15 300`; verify has no reviewer invocation to retime.

## 6. Non-convergence canary fixture (for the verify acceptance test)

- [x] 6.1 Create the canary harness used by the verify step: a minimal one-task `tasks.md` whose task is "make `test_canary` pass" plus a committed fixture asserting an impossibility (e.g. `assert add(1, 1) == 3`) so it can never go green, stored under a docs/test path with run instructions. (Running it to confirm the executor STOPs with a `### NON-CONVERGENCE BLOCKER` after 2 attempts is the verify step, not an apply task.)
