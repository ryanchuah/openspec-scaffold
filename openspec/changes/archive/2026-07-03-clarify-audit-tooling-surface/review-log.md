# Review log — clarify-audit-tooling-surface

## proposal.md — Round 1 (openspec-reviewer @ deepseek-v4-pro), 2026-07-03

**Verdict: no 🔴; PREMISE: AGREE.** 4 🟡 (should-fix), 2 💡.

Premise AGREE on all four checks: naming collision is a real design defect (not training),
solution maps 1:1 to causes, scope bounded (propagation deferred), no blind spot (correctly leaves
the historical decisions-registry `lint-knowledge` mention untouched).

Resolution of 🟡:
1. **scaffold_lint generalization mechanism underspecified** → CARRIED TO design.md (must give a
   concrete detection strategy; the live-repo SEAL `test_live_repo_lints_clean` must stay green).
2. **spec has 6 `lint-knowledge` refs incl. Purpose prose, not just "name/path"** → FIXED in
   proposal Modified Capabilities (now enumerates all 6; design.md pins each edit).
3. **AGENTS.md rewrite scope open-ended** → CARRIED TO design.md (annotate-in-place, not a
   structural rewrite; exact boundary pinned there).
4. **manifest line-level deltas not enumerated** → FIXED in proposal Impact (the 3 deltas listed).

💡: (1) interpreter-detection strategy for run-audit → design.md will give the try-order table;
(2) tombstone cleanup one-liner → added to proposal Impact.

Frozen on zero 🔴 + PREMISE: AGREE. Design-level items (🟡1, 🟡3, and per-occurrence spec
enumeration) carried into design.md.

## design.md — Round 1 (openspec-reviewer @ deepseek-v4-pro), 2026-07-03

**Verdict: no 🔴.** 4 🟡, 4 💡 — all incorporated:
1. D2 refinement vs proposal's auto-derive wording not acknowledged → ADDED the acknowledgment in D2.
2. `run-audit` `tag` operator-gating mechanism unspecified → PINNED: tag only when the invocation
   explicitly says "tag"/"anchor"; else read-only (D3 + tasks 5).
3. `run-audit` cycle error handling undefined → ADDED: stop on first non-zero exit + report;
   pre-existing `output/audit/<date>/` reported, not overwritten (D3 + tasks 5).
4. Verification criterion-1 test underspecified → PINNED the construction (knowledge-drift-review dir
   present, run-audit dir absent → the latter flags) in design Verification + tasks 4.
💡: S-delta count 6→7; follow-ons FILENAME stays (concept name); `_SKILL_CLEAN` fixture exact text;
run-audit step-0 pre-check — all folded in.

Frozen on zero 🔴.

## specs/knowledge-lint/spec.md — Round 1 (openspec-reviewer @ deepseek-v4-pro), 2026-07-03

**Verdict: PASS — no 🔴, no 🟡.** Occurrence-by-occurrence table confirmed all 6 requirement/scenario
renames correct, both MODIFIED blocks copied in full (no lost content), all scenarios use 4 hashtags.
The 7th (Purpose prose) correctly deferred to the archive instruction in `notes.md`.
💡: make the 6-in-delta / 7th-at-archive split explicit in design.md S-delta → DONE (split note added).

Frozen.

## tasks.md — Round 1 (openspec-reviewer @ deepseek-v4-pro), 2026-07-03

**Verdict: PASS — no 🔴.** All 8 tasks confirmed apply-phase-only, fully covering D1–D5 + S-delta;
SEAL green after T8. 3 🟡 (executor-clarity, not missing work) — all folded in:
1. Task 1 forward-reference to task 5's convention → inlined the interpreter try-order in task 1.
2. Task 4 fixture-tree dict KEY rename (`_clean_tree()` ~line 134) underspecified → made explicit,
   plus the full `_SKILL_CLEAN` before/after text.
3. Task 2 lists run-audit before task 5 authors it → added the "harmless, SEAL checked at T8" note.
💡: `--check-refs` vs scaffold_lint invariant distinction → added to task 8.

Frozen. All four artifacts frozen — phase gate: STOP before apply.

## VERIFY (orchestrator behavioral review), 2026-07-03

**Verdict: READY.** Read every diff (scaffold_lint D2, AGENTS.md D4, renamed skill + interpreter
note, run-audit D3, test fixtures + new regression test) — all match the frozen artifacts. Full
suite green. Eyeballed real `check_dangling_skill_refs` behavior via a live probe (valid non-openspec
skills validate; `openspec-ghost` flags; removed `lint-knowledge` not detected = documented D2
trade-off, grep sweep clean). No external API (no live smoke needed). No security surface.
Multi-model passes WAIVED by operator directive (no uncertainty). Simplicity self-checklist: clean.
No defects. Details in notes.md verify checkpoint.
