# Review log — archive-mechanization

## proposal.md — Round 1 (deepseek-v4-pro, 2026-07-14) — PASS · PREMISE: AGREE

- **Verdict:** PASS, zero 🔴. `PREMISE: AGREE` (problem real — RENAMED path never exercised;
  root cause correct; solution targets it; scope right-sized). No explore-brief drift (D10 clean).
- **🟡 addressed pre-freeze (no re-review — quality polish, not 🔴):**
  1. REMOVED-absent behavior was an unresolved explore-brief design-question left unflagged →
     added an explicit "named here, settled in design.md" note in What Changes.
  2. sync-specs Step 4c prose being overridden not cross-referenced → Impact behavior-change bullet
     now cites `openspec-sync-specs/SKILL.md` Step 4c lines 60–61 verbatim.
  3. move-vs-promote ordering constraint not named → added to the same What Changes note as (1).
- **💡 addressed:** "kept byte-identical" → "both rewritten; must remain byte-identical";
  scaffold_lint guard expanded to name its checks; capability description broken into a scannable list.
- **Freeze:** zero 🔴 + PREMISE: AGREE → frozen. All three 🟡 land as explicit design.md decisions.

## design.md — Round 1 (deepseek-v4-pro, 2026-07-14) — PASS

- **Verdict:** PASS, zero 🔴. "Strong design; D4 truth table internally consistent, all rows
  correct; promote-then-move (D7) sound; recovery block still works."
- **Six 🟡 addressed pre-freeze (completeness/precision, no re-review — none directional):**
  1. REMOVED-absent detection surface → D4 now states the `skipped`/`target-absent` list is the
     operator-facing surface, surfaced at archive Step 6.
  2. D6 mid-write partial-state → added: per-file atomic write (`os.replace`) + explicit non-
     transactional-multi-file limit + recovery-block mitigation.
  3. Step-4 rewiring underspecified → D10 now describes the `--dry-run --json` assessment flow.
  4. Missing RENAMED+MODIFIED combo test → added to Verification.
  5. Intra-delta self-collision unaddressed → D4 note added (same rules apply within a delta).
  6. Report example only showed REMOVED skip → added ADDED (`body-equal`) + RENAMED
     (`already-renamed`) skip examples to the D11 schema.
- **💡 addressed:** empty-section + only-`## Purpose`-spec verification criteria; human-summary
  lists anomalies first; `--help` summarizes D4 semantics.
- **Freeze:** zero 🔴 → frozen.

## specs/archive-mechanization/spec.md + tasks.md — Rounds 1–2 (deepseek-v4-pro, 2026-07-14)

- **Round 1 — NEEDS REVISION (3 🔴):** (1) spec missing intra-delta self-collision scenario;
  (2) T4.3 old step-numbering ("step 1 = move") contradicted the D7 promote-then-move order — a
  flash executor could pick the rejected order; (3) spec missing the only-`## Purpose` main-spec
  edge case. Plus 🟡: exit-2 precision, body-normalization wording looser than D4, no RENAMED+MODIFIED
  combo scenario, no REMOVED/RENAMED-on-missing-spec anomaly, T1.2 regexes not given verbatim, T3.1
  over-scoped (adversarial fixtures are verify work).
- **Fixes:** added intra-delta self-collision + REMOVED/RENAMED-on-missing-spec + only-`## Purpose` +
  degenerate-delta + RENAMED+MODIFIED-combo scenarios; "exit non-zero" → "exit 2"; aligned
  body-normalization wording to D4; RENAMED scenario now shows the `- FROM:`/`- TO:` list-item format;
  T1.2 now quotes the three exact `checks.py` regex strings; T4.3 renumbered to promote-then-move
  (no "step 1 = move" anywhere) + byte-identity self-check; T3.1 rescoped to the core contract suite
  with adversarial fixtures explicitly deferred to the orchestrator at verify; group-4 apply-split
  annotation clarified.
- **Round 2 — PASS, zero 🔴.** All 🔴+🟡 confirmed resolved. Two residual 🟡 addressed pre-freeze:
  spec now points to `--help` for the JSON report schema (design.md leaves at archive; spec is the
  promoted canonical); T1.4 self-collision pointer corrected `(D4 note, D9)`→ D4 for self-collision,
  D9 for new-spec. 💡: kept exit 2 for anomaly (disambiguated from argparse-2 by report presence) —
  declined to reopen frozen design.md for the exit-3 UX nicety; intra-delta scenario notes the
  identical→skip case.
- **Freeze:** zero 🔴 → both frozen. `openspec validate --strict` clean.

## Verify (2026-07-14) — VERDICT: READY

- **Lens selection:** test-quality lens (default) — rationale: the change's dominant risk is
  parser/planner/transform decision-logic, not data-path volume; test-quality/adversarial-oracle is
  the right lens. (Recorded per the verify skill's lens-selection rule.)
- **Self review:** 16 orchestrator-authored adversarial fixtures caught 3 product defects
  (new-spec ADDED self-collision; blank-line drift; trailing-section reorder) → re-delegated fix to a
  fresh flash executor, zero Sonnet fallback, all fixtures green. Detail in notes.md.
- **Pro behavioral pass (deepseek-v4-pro):** READY, zero defects, no fallback.
- **Flash test-quality lens:** Round 1 NEEDS-REVISION (2 🟡 — discarded exit codes in two of my own
  fixtures); fixed inline; Round 2 READY, zero defects.
- **Simplicity gate:** PASS (low-priority None/else ADDED-collision duplication noted as follow-on).
- **Security gate:** N/A (stdlib-only local file ops).

