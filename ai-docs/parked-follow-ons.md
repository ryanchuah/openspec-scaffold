# Parked Follow-ons

Deferred, monitored, and low-priority follow-ons — the long tail that only matters when you next
work the relevant area. **Not part of the mandatory onboarding read** (see AGENTS.md): load the
relevant `## ` area section on demand when you start work in that area. Live blockers and
operator-decision items do NOT belong here — they live in `ai-docs/open-questions.md`. Resolved
items move to `ai-docs/archive/retired-notes.md`.

---

## migration

- **Extrends `open-questions.md` one-time horizon split (MED).** After the `split-open-questions` rule propagates downstream, split extrends' file (the real over-cap case) into active + parked via a byte-integrity-gated one-off (pure line-partition where each bullet lands in exactly one of {active, parked, retired}; recombine == source byte-for-byte; idempotent). Classification (active vs parked) is judgment — author it, get the independent deepseek-v4-pro information-loss review, do NOT delegate the classification to flash. Re-measure against the Read cap afterward. Reuse/adapt the `extrends/scripts/_open_questions_prune_oneoff.py` pattern. Originating change: `split-open-questions` (archive `openspec/changes/archive/2026-06-17-split-open-questions`).
- **Scaffold `open-questions.md` one-time horizon split (LOW).** Same treatment when convenient (scaffold's file is borderline, not yet clearly over cap). Also de-rots the five stale "Propagation backlog (HIGH)" bullets that W6 resolved but were never pruned from the legacy file. Originating change: `split-open-questions`.

## instruction-surface

- **Redundant per-section summary paragraphs in legacy `open-questions.md` (LOW, overlaps C2/W7).** Each legacy `open-questions.md` section opens with a paragraph restating decisions.md/STATUS.md. The new §3c archive rule stops authoring these for new sections (one-line decisions.md pointer instead). Dropping the existing ones is a cleanup that pairs with the migration and with the C2/W7 rule-restatement dedup. Originating change: `split-open-questions`.
