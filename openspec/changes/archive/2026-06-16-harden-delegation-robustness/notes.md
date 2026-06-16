# Notes for archive — harden-delegation-robustness

Doc reconciliation is archive work (NOT in tasks.md). At archive, reconcile the project-tracked
docs as follows.

## ai-docs/decisions.md — record three decisions (with rationale)

1. **Delegated `opencode run` closes stdin (`< /dev/null`).** Keystone fix for the non-interactive
   hang: opencode's `external_directory` (and other guards) default to `ask`; with no TTY an `ask`
   blocks on stdin until the `timeout` wrapper kills it. Closing stdin makes the prompt auto-reject
   (fail-fast) — the fail-safe direction. Empirically verified (design.md `### Live Probe`). The
   rejected "inline file contents" workaround does not scale.
2. **Per-agent `external_directory` posture, split by destructive capability.** Read-only reviewer →
   `external_directory: allow` (no destructive capability). Write-capable executors (apply + archive)
   → `external_directory: { "*": deny, "/tmp/**": allow }` with the catch-all FIRST (opencode is
   last-match-wins) — keeps the apply-executor's `/tmp` convergence write working while hard-denying
   every other out-of-tree path (containment against a stray out-of-tree `rm`). `question: deny`
   deferred (unprobed; the stdin close covers it generically).
3. **The non-convergence canary is now an impl-module + instruction-frozen test.** The impossibility
   lives in code the frozen `test_canary.py` imports; `canary_impl.py` is the only editable surface.
   Hardens against the honest edit-the-assertion shortcut (instruction-gated, not malicious-rewrite-
   proof). Expected outcome: a declared `### NON-CONVERGENCE BLOCKER` (trigger a/b/c), not green/timeout.

## ai-docs/open-questions.md — resolve / narrow the two harden-delegation follow-ups

- **REMOVE** the "[REQUIRED] Harden the canary fixture" entry — resolved by this change (§3).
- **NARROW** the "[REQUIRED] Live-smoke-test the commit-test-gate hook" entry: the script layer is
  now verified and a smoke fixture + procedure exists (`docs/test/commit-gate-smoke/`, §4). The
  residual is only the live **hook-wiring** smoke, which must run in a gated Claude session — keep
  that as the remaining gated-session action item; do NOT remove the entry entirely.
- Optionally note the opencode non-interactive hang is now addressed (cross-ref the new
  `noninteractive-delegation-safety` spec).

## Spec promotion

New capability `noninteractive-delegation-safety` → promote to `openspec/specs/noninteractive-delegation-safety/spec.md`
(it already carries a `## Purpose`). Deltas for `apply-convergence-guard` and `commit-test-gate` are
ADDED requirements — append them to the existing specs (no baseline requirement text changed).

---

# VERIFY OUTCOME (2026-06-16) — orchestrator behavioral review

1. **Verdict: READY FOR ARCHIVE.** Behavioral review passed (V1–V5). One implementation defect was
   found and fixed during verify (see field 3).

2. **Eyeballed live output (behavior, not counts):**
   - **Commit-gate smoke (V5):** ran the corrected `docs/test/commit-gate-smoke/` script-layer snippet
     straight from the README — it produced the five documented exits IN ORDER: absent → allow,
     empty → allow, unresolvable → allow+warning, failing → **BLOCKED (exit 2)**, passing → allow.
   - **Canary (V4):** `pytest` on the rebuilt fixture renders `assert (2 == 2 and 2 == 3)` and FAILS —
     i.e. the single captured value (2) is tested against both predicates, genuinely impossible; a
     stateful impl returning 2-then-3 cannot game it (the value is captured once).
   - **Hang → fix (V3):** a stdin-open `external_directory` prompt hangs (timeout); the same call with
     `< /dev/null` auto-rejects in seconds. The exact apply/archive config `{ "*": deny, "/tmp/**": allow }`
     allows a `/tmp` read and denies an `/etc` read (probe).

3. **Defect found + how fixed (and who):** `docs/test/commit-gate-smoke/README.md` script-layer snippet
   was non-functional in THREE ways, all in the smoke fixture only:
   (a) the apply-executor's original used `(cd "$WORKDIR" && "$GATE")`, but `test-gate.sh` resolves
   `test-cmd` relative to its OWN dir (`BASH_SOURCE`), not cwd → cases 2–5 never exercised their branch.
   → **re-delegated** to a fresh deepseek-flash fix-executor (one attempt) with a corrected
   copy-the-gate-into-the-workspace snippet.
   (b) my fix-spec snippet had the wrong path depth (`../../scripts`; the smoke dir is three levels deep,
   needs `../../../scripts`) → **hand-fixed** (trivial one-token).
   (c) `set -euo pipefail` aborted the script at the intentional exit-2 case → **hand-fixed** (dropped `-e`).
   Re-verified by executing the snippet from the file: five exits correct. No other file was affected by
   the fix run (confirmed via git status).

4. **As-built delta:** none of substance — agents, skills, canary, and smoke fixture match design/specs.
   The smoke snippet's final shape (copy-the-gate; `set -uo pipefail`) is a concretization of tasks.md's
   "runnable snippet"; no spec/design change needed.

5. **Forward-looking items for ai-docs/open-questions.md (archive MUST fold these in — recorded nowhere
   else or only in design):**
   - **Live hook-wiring smoke STILL PENDING (narrowed, not resolved).** Only the script layer is verified;
     the `PreToolUse` wiring (fires on `git commit`, exit 2 blocks, `$CLAUDE_PROJECT_DIR` expands) needs a
     gated Claude session — procedure documented in `docs/test/commit-gate-smoke/`. Keep as the residual
     of the original `[REQUIRED]` hook-smoke open-question.
   - **Propagation to extrends/psc pending (HIGH).** This change is inert in extrends/psc; the hang
     persists there until single-source "change 2" carries the shared agent/skill files. Operator chose
     scaffold-only for now (2026-06-16).
   - **`question: deny` deferred** (design Open Questions) — unprobed; the stdin close covers it generically.
   - **Optional `bash` destructive-command denylist** for the write-capable executors (design Open Questions)
     — deferred unless the operator wants it in scope.
   - **`doom_loop` left at default `ask`** — neutralized generically by the stdin close, not pinned per agent.
     Monitor: if a doom_loop-specific hang is ever seen despite `< /dev/null`, pin it per-agent.
   - **Canary trigger is a/b/c, not a fixed `a`** — deliberate (pytest re-renders the signature on impl
     edits). If a deterministic single trigger is ever wanted, a different fixture is required.

## Still owned by archive
- `STATUS.md` — update to reflect this change shipped.
- `ai-docs/decisions.md` — record the three decisions (see the "decisions" section above).
- `ai-docs/open-questions.md` — remove the canary follow-up; narrow the hook-wiring follow-up; fold in all
  field-5 forward-looking items above.
- Spec promotion — `noninteractive-delegation-safety` → `openspec/specs/`; append the two ADDED-req deltas.
- Cleanup — throwaway probe agents under `/tmp/ocperm/` (and `/tmp/oc*` logs) may be removed; not tracked.
