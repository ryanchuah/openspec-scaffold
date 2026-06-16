# Review Log — harden-delegation-robustness

## Round 1 — proposal.md (2026-06-16) — deepseek-v4-pro via opencode run

**Verdict: NEEDS REVISION** (1🔴, 2🟡, 3💡)

- 🔴 #1 — `question: deny` is an unverified opencode-API assumption (no live probe). Keystone
  `< /dev/null` is probed/confirmed; `question: deny` is unprobed belt-and-suspenders.
  → **Accepted.** Dropped `question: deny` from scope; rely on the stdin close (which neutralizes
  question-prompts generically). Recorded as deferred in proposal + explore-brief.
- 🟡 #1 — "zero destructive capability" wrong for the archive executor (it has `bash`/`edit: allow`).
  → **Accepted, and it surfaced a real design fix.** Split by destructive capability: reviewer
  (read-only) → `external_directory: allow`; apply AND archive (write-capable) → scoped-deny
  `{ "*": deny, "/tmp/**": allow }`.
- 🟡 #2 — inconsistent skill file paths in Impact. → **Accepted.** Made all four paths explicit
  (`.claude/skills/<name>/SKILL.md`).
- 💡 #1 — canary "frozen test" enforcement mechanism not in the proposal. → **Accepted.** Added the
  by-instruction (not filesystem) freeze note.
- 💡 #2 — `open-questions.md` resolution scope ambiguous (hook-wiring only partially resolved).
  → **Accepted.** Proposal now states: canary entry resolved (removed); hook-wiring entry narrowed,
  not removed.
- 💡 #3 — `--dir <repoRoot>` placeholder semantics. → **Accepted.** Clarified it is an
  orchestrator-substituted placeholder like `<changeRoot>`.

The reviewer ran cleanly with `< /dev/null` + `--dir` applied (no fallback; exit 0; no hang) —
incidental end-to-end validation of the keystone fix on the real reviewer. No false claims in the
review (archive-executor permissions verified against disk).

## Round 2 — proposal.md (2026-06-16) — deepseek-v4-pro via opencode run

**Verdict: PASS** (0🔴, 0🟡, 2💡) — proposal FROZEN.

Confirmed the Round 1 🔴 is resolved and all six items addressed (reviewer supplied a resolution
checklist). 💡 #1 — "non-gameable" overclaims vs the body's honest limitation → applied: capability
now reads "hardened, instruction-gated." 💡 #2 — archive executor's `/tmp` allow is unnecessary but
harmless (single config for both write-capable executors) → no change, noted for awareness.

## design.md — review pass (2026-06-16) — deepseek-v4-pro via opencode run

**Verdict: PASS** (0🔴, 2🟡, 3💡) — design FROZEN. (Reviewer numbered it "Round 3" — continuous counter.)

- 🟡 #1 — V1 not grep-testable on the verify skill (it references the apply shape, only a short
  `timeout … opencode run …` snippet). → Applied: V1 now names the three concrete blocks + the verify
  snippet, and requires the verify snippet to carry `< /dev/null` explicitly (not only by reference);
  tasks must harden that snippet.
- 🟡 #2 — D1's "T3/T4/T5 hung because doom_loop/question" is an untestable inference (doom_loop was
  never probed) and contradicts the explore-brief's precision. → Applied: dropped the cause claim;
  D1 now states only that config-alone was insufficient and the stdin close is generic.
- 💡 — defined `doom_loop` in Context; noted the archive `/tmp` allow is uniformity-not-necessity;
  canary file names/assertions to be pinned in tasks.md (noted for the tasks author).

No false claims (Live Probe footing confirmed; reviewer agreed no unverified load-bearing external-API
assumption remains).

## specs/ (3 delta files) — review pass (2026-06-16) — deepseek-v4-pro via opencode run

**Verdict: PASS** (0🔴, 2🟡, 3💡) — specs FROZEN. Reviewer's consistency matrix all-green
(every requirement has a scenario; SHALL throughout; ADDED is the correct label; scope matches the
proposal contract; no baseline conflicts). Ran in parallel with the design review.

- 🟡 #1 — Req 2 heading implied it configures all `ask`-default guards, but only `external_directory`
  is configured. → Applied: body now states `doom_loop`/other ask-defaults are handled generically by
  Req 1's stdin close.
- 🟡 #2 — the two delta specs were not self-describing as deltas. → Applied: added a one-line preamble
  to each pointing at the baseline spec.
- 💡 — tightened the new-capability Purpose; labeled the gate exit-code case→result pairs explicitly;
  split the combined canary scenario into "produces non-convergence" + "emits declared blocker".

Re-validated `--strict` after edits: valid.

## Author-caught refinement (post-specs-freeze, during tasks authoring) — canary trigger

While writing tasks I caught a defect BOTH reviewer passes missed (the [[subagent-verification-discipline]]
pattern — primary catches what the reviewer didn't): the apply-convergence-guard spec + design V4
pinned the canary to `trigger: a`. But a genuinely non-gameable contradiction cannot promise rule (a):
pytest assertion-rewriting re-renders the failing values when the executor edits the impl, so the
normalized signature shifts → the executor may oscillate (→ rule b) or recognize the only fix is editing
the frozen test (→ rule c). Over-pinning `trigger: a` would make V4 fail spuriously on a *correct*
implementation. Corrected design D4, V4, and the apply-convergence-guard spec scenarios to require a
**declared** `### NON-CONVERGENCE BLOCKER` (trigger a, b, or c — not green, not timeout). This makes the
claim weaker/safer and is a better test (exercises the whole guard, not just rule a). Re-validated
`--strict`: valid. No re-review run for this precision fix (it relaxes a falsifiable claim).

## tasks.md — Round 1 (2026-06-16) — deepseek-v4-pro via opencode run

**Verdict: NEEDS REVISION** (1🔴, 3🟡, 3💡)

- 🔴 — Section 5 (T5.1/T5.2) edited `ai-docs/decisions.md` + `open-questions.md` during APPLY, violating
  the scaffold write-discipline rule (those are reconciled ONCE at archive) and the propose guardrail
  (tasks.md = apply-phase implementation only). Concrete hazard: the archive-executor appends the same
  design.md decisions → guaranteed duplicates. → **Accepted (legitimate; I should have known).** Removed
  Section 5; moved the reconciliation intent into `notes.md` for the archive-executor.
- 🟡 #1 — tasks lacked effort estimates. → Applied: added `(~Xm)` per task.
- 🟡 #2 — inter-section dependency undocumented. → Applied: header note (1–2 and 3–4 independent;
  reconciliation is archive/notes.md).
- 🟡 #3 — T2.x acceptance didn't verify the rationale note. → Applied: acceptance now requires the note.
- 💡 — tightened T4.1 acceptance (runnable snippet → five exits); named `test_canary.py` as frozen in
  T3.3; kept the `## N` / `N.M` openspec template numbering (reviewer noted it's fine).

Re-validated `--strict`: valid. Cleared 🔴 → Round 2 re-review is MANDATORY (running next).

## tasks.md — Round 2 (2026-06-16) — deepseek-v4-pro via opencode run

**Verdict: NEEDS REVISION** (1🔴, 0🟡, 2💡) — Round 1 🔴 confirmed resolved (Section 5 gone, moved to
notes.md), but the reviewer found a NEW, subtle 🔴 that all prior rounds missed:

- 🔴 — the canary assertion `assert add(1, 1) == 2 and add(1, 1) == 3` calls `add` TWICE (Python `and`
  short-circuits per operand), so a stateful impl (counter/closure returning 2-then-3) makes it GREEN —
  gameable, contradicting the spec's "no implementation can satisfy." → **Accepted (correct, sharp catch).**
  Fixed: call `add` once, capture in `result`, assert `result == 2 and result == 3` (a single int cannot
  equal both). Fixed in lockstep in design.md D4 (same flawed example); the apply-convergence-guard spec
  is abstract ("no implementation can satisfy") and remains correct, so no spec edit needed. (A pathological
  `__eq__` could still cheat, but that's a malicious rewrite — out of the instruction-gated scope.)
- 💡 — added the within-§3 sequential-dependency note to the tasks header; path-anchoring note (no action).

Re-validated `--strict`: valid. Cleared 🔴 → Round 3 re-review MANDATORY (this is the 3rd/cap tasks pass;
if it surfaces another 🔴, escalate per the propose skill rather than loop).

## tasks.md — Round 3 (final) (2026-06-16) — deepseek-v4-pro via opencode run

**Verdict: PASS** (0🔴, 0🟡, 2💡) — tasks FROZEN. Round 2 🔴 confirmed resolved in BOTH tasks.md T3.2 and
design.md D4 (capture-once). Reviewer: "every task maps to a design decision or spec requirement … no
doc reconciliation leakage … No remaining substantive defect."
- 💡 — folded in: pinned a concrete suggested verify invocation form (T2.4) and a FROZEN header line for
  the canary test (T3.2), to reduce ambiguity for the deepseek-flash apply-executor. No re-review (💡 polish).

## PROPOSE PHASE COMPLETE
All four artifacts frozen (proposal 2 rounds, design 1, specs 1, tasks 3 + 2 author-caught fixes).
6 reviewer passes total, all real-agent (no fallback), all dogfooding `< /dev/null` + `--dir` — none hung.
Held at the apply gate pending explicit operator `apply harden-delegation-robustness`.

## APPLY (2026-06-16) — deepseek-flash apply-executor via opencode run (operator-authorized, scaffold-only)

Ran clean: EXIT=0, no agent fallback, no real NON-CONVERGENCE BLOCKER (14 jsonl matches were the executor
writing/quoting the heading into the canary README — err.log=0, report clean, all 13 tasks `[x]`). The
apply itself dogfooded `< /dev/null` (and did not hang). Judged FROM DISK — correct:
- 3 agent frontmatters: reviewer `external_directory: allow`; apply+archive `{ "*": deny, "/tmp/**": allow }`
  with catch-all FIRST. ✓
- canary: capture-once `result = add(1,1); assert result == 2 and result == 3`, FROZEN header, impl editable. ✓
- 4 skill invocations: `< /dev/null` bound to `opencode run` (before the `; echo` sentinel) + `--dir` + note;
  verify snippet carries both explicitly. ✓
- canary tasks.md marks test_canary FROZEN, lists only canary_impl.py editable. ✓

**ONE defect found from disk (→ fix at verify):** `docs/test/commit-gate-smoke/README.md` §Script-Layer
snippet is non-functional. `test-gate.sh` resolves `CMD_FILE` relative to its own `BASH_SOURCE` dir, NOT
cwd; the snippet points `GATE` at the real `scripts/test-gate.sh` and does `(cd "$WORKDIR" && "$GATE")`,
so the gate keeps reading the real (absent) `scripts/test-cmd` — cases 2–5 never exercise their branch and
the documented output block is fictional. FIX: copy `test-gate.sh` into `$WORKDIR/scripts/` and invoke the
COPY (so `SCRIPT_DIR` = `$WORKDIR/scripts`), exactly as the orchestrator's manual probe did. Held at the
VERIFY gate pending operator `verify`.
