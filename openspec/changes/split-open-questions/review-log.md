# review-log — split-open-questions

## tasks.md — Round 1 (self-review)

Self-reviewed before the reviewer pass. Fixed two issues found:
- Delimiter risk: the authoritative rule text (1.3) and the §3c block (2.1) were wrapped in `>` /
  ```` ``` ```` purely as delimiters; clarified they are content to transcribe, not literal markup.
- §3c had dropped the "where to pull follow-ons from" sourcing (notes.md candidate section /
  design.md Risks); restored it.

## tasks.md — Round 2 (@openspec-reviewer, deepseek-v4-pro)

**Verdict: PASS** — no 🔴. Three 🟡 (should-fix), three 💡 (suggestions). Full review text below
the responses.

### Disposition

- 🟡1 (Task 1.1 insertion point ambiguous — the top blockquote paragraph spans more than implied,
  an executor could split at the wrong period) — **FIXED.** 1.1 now anchors the insertion to the
  exact preceding sentence ("…the closed decision it covers.") and gives the verbatim sentence to
  insert, preserving the `> ` marker.
- 🟡2 (Task 3.1 gave no exact replacement bullet text) — **FIXED.** 3.1 now quotes the exact current
  bullet and provides the verbatim replacement (active-only + parked routing + "no live blocker was
  parked").
- 🟡3 (Missing edit — AGENTS.md "Authored deliverables" bullet still lists open-questions.md as
  "(open follow-ons)" with no parked file) — **FIXED.** Added Task 1.4 to update that parenthetical
  and add `ai-docs/parked-follow-ons.md` to the directory listing.
- 💡1 (parked-follow-ons.md preamble in prose, not verbatim) — **ADOPTED.** Task 4.1 now provides the
  exact file content.
- 💡2 (§3c has a descriptive paragraph between heading and bullets, unlike §3a/§3b; a strict executor
  might drop it) — **ADDRESSED via wording.** Task 2.1 no longer says "match §3a/§3b style"; it now
  says to keep the intentional intro paragraph.
- 💡3 (existing open-questions.md preamble "Unresolved questions and user-action items…" is now stale)
  — **DECLINED for this change, with rationale.** Updating the preamble to "active items only" now
  would mis-describe the file's *current* (un-migrated) contents — the legacy parked items still live
  there until the one-time migration. The old preamble still accurately describes the un-split file.
  The preamble update is folded into the migration follow-on (notes.md) so the self-documentation
  flips exactly when the content does. AGENTS.md (the authoritative rule) already covers the split.

No 🔴 were raised, so no mandatory re-review; the 🟡/💡 edits are improvements layered on a PASS.
tasks.md is frozen.

---

### Reviewer text (Round 2, verbatim)

**Verdict: PASS.** Findings:

🟡 1 — Task 1.1 insertion point subtly ambiguous: the MANDATORY-read paragraph spans lines 5–13
(continues into the "resuming an in-progress change" guidance); a mechanical executor could insert
the new sentence at the wrong period. Fix: give the exact text + exact anchor, or the full replacement
paragraph.

🟡 2 — Task 3.1 gives no exact replacement text for the quality-check bullet (current bullet:
"`ai-docs/open-questions.md` entry must list the open follow-ons from notes.md or design.md, with
BLOCKING flags where appropriate."); executor must compose it, risking omission of the
"no live blocker was parked" assertion. Fix: provide exact bullet text.

🟡 3 — Missing edit: AGENTS.md "Authored deliverables" bullet still says open-questions.md is for
"(open follow-ons)" with no mention of the split or parked-follow-ons.md; the directory listing and
the new rule could conflict for a skimming reader. Fix: update the parenthetical + add the parked file.

💡 1 — Provide parked-follow-ons.md preamble verbatim to eliminate composition risk.
💡 2 — §3c's descriptive paragraph between heading and bullets differs from §3a/§3b (heading→bullets);
a strict executor might drop it. Cosmetic.
💡 3 — Existing open-questions.md preamble doesn't reflect the horizon split; a one-line note would
self-document it. Optional.

"PASS — ready to freeze and move to apply. The tasks are concrete, cover all necessary edit sites,
preserve no-blocker-burial, and are implementable by a mechanical executor. The three 🟡 issues would
reduce risk of executor misplacement/composition error but none would cause the implementation to go
in the wrong direction."
