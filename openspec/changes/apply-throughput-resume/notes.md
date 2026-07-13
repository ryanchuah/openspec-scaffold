# notes — apply-throughput-resume (OW-10)

**Tier:** MEDIUM. **Orchestrator:** Opus (design pre-made — AUDIT finding 4; recon `recon-ow10.md`).
**Apply:** delegated (deepseek-flash default; the edits are prose + two byte-synced executor-body
edits — precise, flash-viable). Closes **OW-10** in `OUTSTANDING-WORK.md`.

## Problem
Two apply-phase inefficiencies (AUDIT finding 4):
1. **Full suite after every task.** The apply-executor body's per-task loop step 2 runs the full
   documented test command (`scripts/test-cmd`, here `pytest -q` — the whole suite) **unconditionally
   after every task**, before the green/red branch. For a slow downstream suite this is what makes the
   ~600s executor ceiling bind and forces manual "slice" ceremony (recon §1a/§1b).
2. **No resume contract.** After an operational crash/timeout, the fresh-executor re-brief
   (`SKILL.md` failure ladder) only says "write a tight brief, forbid re-exploration" — it never
   states the **resume contract**: skip `[x]` tasks, resume at the first `[ ]`, and *reconcile the
   half-edited in-flight task* the dead run left mid-write. ~15–19% of downstream changes hit a
   crash/timeout→Sonnet escalation, each burning a 600–780s budget re-deriving context the
   orchestrator already had (recon §1c/§1d confirm the gap is total — net-new prose, nothing to fix).

## Design (decided)
### A. Green-path test cadence (executor body, both platforms, byte-synced)
Change the executor's per-task loop (`.claude/agents/apply-executor.md` step 2, identical in
`.opencode/agents/apply-executor.md` — **both must get the identical edit** or
`test_executor_body_agreement.py` fails): after a task's edit, run **targeted tests for the modules
this task touched** — the SAME test tool, scope-narrowed (e.g. `pytest -q <test file(s)>` for the
files in `git diff --name-only`), NOT an improvised different command — for fast per-task feedback;
then run the **full documented command ONCE before emitting the completion report** (i.e. before
finishing the assignment), so cross-module regressions are still a hard gate within the apply
invocation. If the targeted per-task run OR the final full run is red, the existing red-path
convergence loop is unchanged (it already narrows to the failing module on retry). Where a task's
touched-module→test mapping is unclear, fall back to the full command for that task.

### B. Resume contract (SKILL.md orchestrator prose ONLY — NOT the executor body)
Kept entirely in `SKILL.md`'s failure ladder (the orchestrator writes the fresh-executor brief), so
the executor-body sync constraint is **not** triggered (recon §2 recommendation — the cheaper design).
The retry/fresh-executor brief SHALL state, as a structured resume contract:
1. **Which tasks are already `[x]`** — the fresh executor SKIPS them (do not re-do completed work).
2. **Resume at the first `[ ]`** task.
3. **Reconcile the in-flight task** — the task at/after the last `[x]` may have been half-edited when
   the prior run died; the brief directs the fresh executor to re-read that task's current on-disk
   state (`git diff`) and complete/repair it rather than assume it is untouched or already done.
4. **Carry-forward distilled state** — front-load the facts the orchestrator has already verified;
   forbid codebase re-exploration (extends the existing "tight brief" bullet into an explicit contract).

## Acceptance criteria
1. Executor body step 2 (BOTH `.claude` + `.opencode` apply-executor.md, byte-identical save the one
   sanctioned intro clause) runs targeted tests per task + the full documented command once before
   completion; `test_executor_body_agreement.py` stays green.
2. `SKILL.md` failure ladder carries the four-point resume contract for the fresh-executor brief; the
   between-slice smoke text (OW-7-adjacent, `SKILL.md:128-145`) and OW-7's wrapper-invocation block
   (`SKILL.md:155-168`) are NOT disturbed.
3. **MODIFIED `apply-convergence-guard`** Requirement 1: reconciles "targeted tests per task" with the
   existing "prefer the same per-repo test command … never an improvised command" SHALL — scope-
   narrowing the SAME tool to the task's touched modules is permitted; only a *different/improvised*
   command (wrong venv/flags) is banned; the full documented command runs once before completion.
4. Green gate: `bash scripts/check.sh` exit 0.

## Spec delta
- **MODIFIED `apply-convergence-guard`** (Requirement 1 only — the test-command clause). The resume
  contract is skill-prose-only (recon §3: nothing in the spec governs the fresh-executor brief).

## Assumptions (batched)
- **A1 — resume contract in SKILL.md only**, not the executor body — avoids the byte-sync constraint
  (recon §2). Reverse only if a fresh executor must self-detect resume without a brief (not needed:
  the orchestrator always writes the brief).
- **A2 — targeted = same tool, narrowed target** inferred from `git diff --name-only` → sibling test
  files; fall back to the full command when the mapping is unclear. This is the reading that keeps
  Requirement 1's intent (ban improvised commands, allow scope-narrowing).
- **A3 — coverage tradeoff accepted:** a cross-module regression a task's targeted tests don't cover
  surfaces at the end-of-assignment full run rather than at the culprit task (slightly deferred
  attribution). The full suite remains a hard gate before the executor completes, and verify re-runs
  it — nothing escapes the apply phase. For the scaffold's own ~13s suite the change is near-neutral;
  the payoff is downstream (slow suites where the 600s ceiling binds). Edge (accepted): when the
  end-of-assignment full run IS red, the red-path `_convergence.py` state keys the failure to
  whatever test failed under the last `--task`, which may not be the task that introduced the
  cross-module regression — attribution is approximate on that path, but the full run still gates
  completion and verify re-runs the suite, so correctness is unaffected.

## Out of scope
- A numeric/structural slice-boundary trigger (AUDIT finding 4 doesn't ask; slice bounding stays
  orchestrator judgment). Consuming OW-7's telemetry. Any change to the red-path convergence mechanics
  or `_convergence.py`.

## Traceability
Closes **OW-10**. Depends on OW-7 landed first (shares the apply SKILL.md surface; OW-7's wrapper
block is left untouched).
