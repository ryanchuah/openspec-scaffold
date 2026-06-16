# Verify Notes — harden-delegation (2026-06-16)

## 1. Verdict
**Ready for archive — WITH two required follow-ups** (no CRITICAL implementation defects; the
deterministic core is behaviorally verified). The two follow-ups (hook live smoke-test; canary
hardening) are environment/fixture limitations, not capability defects — see field 5. Operator should
decide whether the hook smoke-test must pass before archive or can be done at first real use.

## 2. What I confirmed by eyeballing live output
- **apply-convergence-guard core (`scripts/_convergence.py`), driven directly:** a stuck failure
  returned `CONTINUE` on the first observation and `STOP:a:… same normalized error after 2 attempts`
  on the second same-signature observation; a *changed* error signature returned `CONTINUE` (healthy
  iteration is NOT interrupted). Rule (a) and the healthy-iteration carve-out behave as specified.
- **commit-test-gate (`scripts/test-gate.sh`):** observed exit 0 + "skipping (no-op)" on an
  empty/whitespace `test-cmd`; earlier probe observed absent→0, passing→0, failing→exit 2 (block),
  unresolvable-interpreter→warn+0. The gate's exit contract holds on a real shell.
- **convergence unittest** (`scripts/test_convergence.py`): ran green.
- **NOT eyeballed live (see field 5):** the PreToolUse hook actually firing/blocking a commit
  (environment-blocked from this session); the end-to-end opencode canary (fixture is gameable).

## 3. Defects found and how/who fixed
- **Primary (orchestrator), during apply review:** (a) `.claude/settings.json` had malformed flat
  hook nesting → rewrote to the documented three-level structure (event→matcher-group→handlers),
  shell-form `command` with quoted `$CLAUDE_PROJECT_DIR`. (b) `ai-docs/decisions.md` self-contradicted
  the new hook → per the operator's decision (option B) superseded "No lifecycle hooks in the
  scaffold" and recorded a "Scaffold ships the commit-test-gate hook" carve-out. Both were
  config/decision-record edits, not implementation logic.
- **Open (NOT fixed):** the canary fixture is gameable (see field 5) — recommend re-delegating a
  hardening fix before relying on the e2e canary.

## 4. As-built deltas vs the artifacts
- Settings handler resolved to **shell-form `command`** with quoted `$CLAUDE_PROJECT_DIR` (design left
  exec-vs-shell form as an Open Question; resolved here).
- The **"No lifecycle hooks in the scaffold" decision is now superseded** (operator option B); design
  assumed the hook ships in the scaffold, decisions.md now records the deliberate carve-out + residual.
- `_convergence.py` **rule (a) stops on the 2nd same-signature *observation*** (counts the initial
  failure as attempt 1), i.e. it stops after the first unproductive fix — slightly stricter than a
  literal "2 fix attempts". Accepted as fail-fast; flagged for monitoring.

## 5. Forward-looking items (fold into ai-docs/open-questions.md at archive)
1. **[REQUIRED] Hook live smoke-test before relying on the gate.** The `PreToolUse` hook firing +
   block-on-exit-2 was NOT live-confirmed (hooks apply to the running Claude session; this verify
   session's project is `workflow-optimize`, not a gated repo). Smoke-test in a gated Claude session
   (after propagation to extrends/psc, or a scaffold-based session): failing `test-cmd` → `git commit`
   blocked; passing → proceeds; absent → proceeds. Also confirm `$CLAUDE_PROJECT_DIR` expands on the
   operator's Claude version. (Design deferred this deliberately.)
2. **[REQUIRED] Harden the canary fixture.** `docs/test/canary-non-convergence` is gameable — the
   impossibility (`assert 1+1==3`) lives in the same file the executor may edit, so it can be made
   green by editing the assertion. Move the contradiction into an impl module the test imports (e.g.
   `assert add(1,1)==2 and add(1,1)==3`) and forbid editing the test, so the executor is forced into
   genuine non-convergence. Until then the e2e canary is unreliable (core is independently verified).
3. **rule (a) threshold** stops after the first unproductive fix — monitor on real applies; loosen if
   too eager.
4. **OpenCode-side gate plugin (v2)** still deferred — OpenCode-driven commits are NOT gated. (Also in
   design Non-Goals + decisions.md.)
5. **Reviewer incremental-emission quality** — observe the first few real reviews; revert the prompt
   nudge if synthesis degrades (design Open Question).
6. **Propagation to extrends + psc-monitor** — this hardening is inert until propagated (change 2 /
   single-source). The scaffold gate is intentionally a no-op locally (no `scripts/test-cmd`).

## Still owned by archive
- Update `STATUS.md`.
- Promote the 3 spec deltas (`commit-test-gate`, `apply-convergence-guard`, `reviewer-budget`) into
  `openspec/specs/`.
- Fold field-5 items into `ai-docs/open-questions.md`.
- Confirm/keep the `ai-docs/decisions.md` supersede + carve-out (already written by the primary).
- Cleanup: remove the stray `docs/test/canary-non-convergence/__pycache__/*.pyc` (don't commit it);
  the `/tmp/apply-convergence-*.json` eyeball state files are throwaway.
