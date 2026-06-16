# Review Log — harden-delegation

## Review Round 1 — proposal.md — 2026-06-16 — deepseek-v4-pro (openspec-reviewer)

### Verdict: PASS (zero 🔴). Ready to freeze; 🟡 to be resolved in design.

**Reviewer summary:** Well-structured; Why is grounded in specific incidents; the three
Capabilities map cleanly to the three changes; Impact identifies affected files; the
non-convergence definition is precise and implementable. No 🔴. Several 🟡 where the
proposal is silent about downstream implications design.md must resolve.

### 🔴 Blocking
None.

### 🟡 Should fix
1. **Reviewer incremental output vs `edit: deny`.** Reviewer agent has `edit: deny` /
   `bash: deny` — it cannot write `review-log.md` today. Proposal must acknowledge the
   tension; resolution (scoped edit permission vs stream-to-stdout-and-primary-appends)
   to be picked in design.
2. **Failure-ladder change implied but not stated.** Current apply skill (step 6.4):
   Non-crash failure → **immediately** Sonnet. Proposal routes non-convergence to the
   orchestrator instead — a material ladder change that "What Changes" never states. A
   reader could add stop-conditions to the executor while leaving auto-Sonnet intact →
   broken flow. State the ladder modification explicitly.
3. **New reviewer timeout unspecified.** Proposal says "raise from 300s" but gives no
   target/principle. Provide a bounding principle (e.g. ≥ apply's 600s; exact TBD design).
4. **Impact lists openspec-verify-change without rationale.** Add a one-line why (commit
   gate fires on the orchestrator's verify-time commit).
5. **No explore-brief.md exists.** Design author lacks the incident/decision context
   (3 incidents, heartbeat rejection). Create it before authoring design.

### 💡 Suggestions
1. `--no-verify` can bypass a PreToolUse git-commit hook — note as accepted risk / design edge.
2. "Error signature" needs a normalization algorithm (strip line numbers/timestamps/addresses) — flag for design.
3. Move the OpenCode-plugin v2 deferral from Impact into Explicit non-goals (scope boundary).

---

## Disposition (primary) — 2026-06-16

Verdict was PASS (no 🔴) → frozen without a second paid review round (re-review is
mandatory only after a 🔴 fix; the reviewer pre-approved the freeze).

**Applied to proposal.md** (proposal-scope sharpening):
- 🟡#2 — added the failure-ladder modification to "What Changes" (non-convergence →
  orchestrator triage; opaque give-up → keeps auto-Sonnet).
- 🟡#4 — added the verify-skill rationale in Impact.
- 💡#3 — moved the OpenCode v2 deferral into Explicit non-goals.
- 💡#1 — added `--no-verify` bypass as an accepted-risk non-goal.

**Deferred to design.md** (captured in explore-brief.md as design open-questions; reviewer
agreed these belong in design): 🟡#1 (reviewer edit-permission mechanism), 🟡#3 (concrete
reviewer timeout value), 💡#2 (error-signature normalization algorithm).

**Process:** created explore-brief.md (🟡#5) capturing the 3 incidents, the decisions, the
rejected approaches (heartbeat, cap-raise-as-primary, reviewer throttle), and the design
open-questions above.

---

## Review Round 2 — design.md — 2026-06-16 — deepseek-v4-pro (openspec-reviewer)

### Verdict: NEEDS REVISION (2 🔴). Re-review mandatory after fixes.

### 🔴 Blocking
1. **D3 presupposes a `write→test→fix` loop the executor prompt doesn't mandate.** Verified:
   `apply-executor.md` says only "Read task → Implement → Mark [x]" — no test-run-between-edits,
   no signature tracking. The stop rule would be dead code. (Executor *does* have `bash: allow`.)
2. **D4 has no parseable discriminator** for structured-blocker vs opaque give-up. Primary would
   misroute every non-crash failure (→ reflexive Sonnet, defeating D4).

### 🟡 Should fix
1. Normalization burden too high for flash in-context → give it a deterministic helper script.
2. D4 ignores the apply skill's **OpenCode delegation path** (only the Claude path has a ladder).
3. `### Live Probe` was a doc-citation, not a live probe (skill requires command+observed output).
4. Verification "canary apply" underspecified — give a construction recipe.
5. test-gate behavior when `test-cmd` present but interpreter missing (fresh clone) unspecified.
6. Partial-salvage "re-run or escalate" has no decision heuristic.

### 💡 Suggestions
1. Convergence state needs a durable store (state file), not flash's context.
2. Add a verify-skill↔gate verification criterion.
3. Note the verify fix-executor 300s timeout is intentionally unchanged.
4. Give the incremental-emission observation a concrete revert trigger.

### Disposition (primary) — 2026-06-16
All 🔴/🟡/💡 verified against real files (reviewer was accurate). Revising design v2:
- 🔴1 + 🟡1 + 💡1 → new **D3**: executor self-monitoring loop driven by a deterministic helper
  `scripts/_convergence.py` (normalizes signature + reads/updates a state file + prints
  CONTINUE/STOP) so a/b are code, not flash judgment.
- 🔴2 + 🟡2 → new **D4**: exact `### NON-CONVERGENCE BLOCKER` block as the grep-able discriminator;
  applied to BOTH the Claude and OpenCode delegation paths.
- 🟡3 → ran a REAL `/tmp` gate-script probe (4 cases, command+output recorded); hook-wiring stays
  doc-verified + deferred live smoke-test (session-hook sandboxing genuinely unsafe from here).
- 🟡4 → concrete canary recipe in Verification. 🟡5 → D2 config-error path (probed: exit 0 + warn).
  🟡6 → D5 salvage heuristic. 💡2/💡3/💡4 → added.

---

## Review Round 3 — design.md (re-review of v2) — 2026-06-16 — deepseek-v4-pro

### Verdict: PASS. Both prior 🔴 fully resolved; all six prior 🟡 addressed.

3 new 🟡 (implementation-quality, "tasks.md can nail down") + 3 💡 — applied to design before freeze:
- 🟡1 → D3 step 2 now uses D2's per-repo test command (not ad-hoc pytest).
- 🟡2 → D3 spells out the CONTINUE action (fix → return to step 2, don't advance task).
- 🟡3 → D3 adds the helper-failure fallback (treat as rule-(c) STOP).
- 💡1 → `_convergence.py` now takes raw test output and extracts the test id itself.
- 💡2 → state-file `<slug>` defined (sanitized change name).
- 💡3 → Verify↔gate moved from a (self-referential) verification criterion into D1 as a design point.

Frozen on the PASS verdict (no 🔴; the applied items are the reviewer's own clarifications, so no
further paid round). Design took 2 reviewer passes (Round 2 NEEDS REVISION → Round 3 PASS).

---

## Review Round 4 — spec deltas — 2026-06-16 — deepseek-v4-pro

### Verdict: NEEDS REVISION (1 🔴). Re-review mandatory after fixes.

Three capabilities cleanly separated; commit-test-gate + reviewer-budget nearly complete.

### 🔴 Blocking
1. `apply-convergence-guard` collapsed `missing` + `suspected_cause` into one phrase; design D4 has
   them as 2 of 8 distinct blocker fields. → enumerated both as separate fields.

### 🟡 Should fix (all apply-convergence-guard)
1. STOP must END the run (don't start remaining tasks) — added clause + "Stopping ends the run" scenario.
2. CONTINUE must stay on the SAME failure (don't advance task) — tightened the healthy-iteration scenario.
3. Opaque give-up scenario was Claude-only (Sonnet); OpenCode opaque give-up = fresh executor/escalate —
   split into per-path scenarios.

### 💡 (applied the load-bearing ones)
- 💡1 commit-test-gate: noted `Bash(git commit*)` pattern scope (catches `-am`/`--amend`).
- 💡2 apply: noted the helper's `--editing <file>` input (load-bearing for rule b).
- 💡3 apply: executor SHALL use the same `scripts/test-cmd` as the gate (no ad-hoc pytest).
- 💡4 reviewer: noted `-k 15` soft-kill grace (load-bearing for salvage).
- 💡5 reviewer: named both invocation points (propose + verify) in the requirement text.

### Disposition (primary) — 2026-06-16
All findings verified against frozen design (reviewer accurate). Fixed 🔴 + all 3 🟡 + all 5 💡;
`openspec validate` still passes. Re-review (round 2) follows.

---

## Review Round 5 — spec deltas (re-review of v2) — 2026-06-16 — deepseek-v4-pro

### Verdict: PASS. Prior 🔴 + all three 🟡 resolved; no new 🔴.

1 new 🟡 + 2 💡 — applied before freeze:
- 🟡 (spec↔design gap): apply-convergence-guard dropped design D3's test-command *fallback*. Aligned
  the spec: prefer `scripts/test-cmd`, fall back to the project's standard command, never improvised.
- 💡2: clarified healthy-iteration re-runs the failing test's module, not necessarily the whole suite.
- 💡1 (forward-ref readability): skipped as cosmetic.

Frozen on PASS (no 🔴; the applied items are the reviewer's own alignment/precision asks). Specs took
2 reviewer passes (Round 4 NEEDS REVISION → Round 5 PASS). `openspec validate` clean.

---

## Primary-caught defect (post-specs-freeze, while authoring tasks) — 2026-06-16

**Defect the reviewer MISSED across Rounds 2–5:** design D5 + reviewer-budget spec claimed the
reviewer timeout should be raised in `openspec-verify-change` too. Grounding in the actual file shows
**verify has NO `openspec-reviewer` invocation** — its behavioral review is the orchestrator's own
("do not delegate this"), and its only timed `opencode run` is the *fix-executor* (300s, intentionally
untouched). So the reviewer-budget change is **propose-only**.

**Action:** corrected design D5 + design Verification + reviewer-budget spec (Requirement 1 text and
the "Reviewer budget" scenario) to scope to `openspec-propose`. `openspec validate` re-checked. This
is a grounded scope *reduction* (no new behavior); the upcoming tasks.md review is asked to confirm
the corrected cross-artifact consistency rather than spending two more full re-review rounds.
(Lesson: the separate-model reviewer can be confidently wrong on falsifiable file-content specifics —
verify before trusting.)

---

## Review Round 6 — tasks.md — 2026-06-16 — deepseek-v4-pro

### Verdict: PASS. No 🔴. Cross-artifact correction confirmed consistent (reviewer grepped the files).

3 🟡 + 2 💡 — applied before freeze:
- 🟡1: T3.1 now states the executor STOPs on a self-detected rule-(c) gap too, not only helper failure.
- 🟡2: T1.1 now covers a present-but-empty/whitespace `scripts/test-cmd` (→ no-op).
- 🟡3: T5.2 now names the exact propose-skill clause to replace (step 4's `If opencode run fails …`),
  avoiding a second conflicting timeout path.
- 💡1: added `(requires T2.1)` / `(requires T3.1)` dependency annotations.
- 💡2: already satisfied (T2.1 already lists the state-file fields).

Frozen on PASS (no 🔴; applied items are the reviewer's own precision asks). tasks.md took 1 pass.
`openspec validate` clean; change `isComplete: true`.

---

## Summary — review rounds per artifact
- proposal.md: 1 pass (PASS).
- design.md: 2 passes (NEEDS REVISION → PASS).
- specs: 2 passes (NEEDS REVISION → PASS) + 1 primary-caught defect correction.
- tasks.md: 1 pass (PASS).
All artifacts frozen. Phase gate: STOP — awaiting explicit `apply harden-delegation`.
