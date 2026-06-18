# Parked Follow-ons

Deferred, monitored, and low-priority follow-ons — the long tail that only matters when you next
work the relevant area. **Not part of the mandatory onboarding read** (see AGENTS.md): load the
relevant `## ` area section on demand when you start work in that area. Live blockers and
operator-decision items do NOT belong here — they live in `ai-docs/open-questions.md`. Resolved
items move to `ai-docs/archive/retired-notes.md`.

---

## migration

- **Extrends `open-questions.md` one-time horizon split — DONE (2026-06-17, extrends commit `4e46eb9`).** Split extrends' over-cap file into active + parked via `extrends/scripts/_open_questions_split_oneoff.py` — a byte-integrity-gated, section-level pure line-partition (recombine == source byte-for-byte; idempotent guard); classification authored by hand (not delegated); independent deepseek-v4-pro information-loss review READY, zero defects; the active file now reads in full under the Read cap. Full record: `ai-docs/open-questions.md` § "split-open-questions". Originating change: `split-open-questions`.
- **Scaffold `open-questions.md` one-time horizon split (LOW).** Same treatment when convenient (scaffold's file is borderline, not yet clearly over cap). Also de-rots the five stale "Propagation backlog (HIGH)" bullets that W6 resolved but were never pruned from the legacy file. Originating change: `split-open-questions`.

## instruction-surface

- **Redundant per-section summary paragraphs in legacy `open-questions.md` (LOW, overlaps C2/W7).** Each legacy `open-questions.md` section opens with a paragraph restating decisions.md/STATUS.md. The new §3c archive rule stops authoring these for new sections (one-line decisions.md pointer instead). Dropping the existing ones is a cleanup that pairs with the migration and with the C2/W7 rule-restatement dedup. Originating change: `split-open-questions`.
- **config.yaml `rules:` block per-repo drift risk (LOW).** `openspec/config.yaml` `rules:` block is per-repo and NOT manifest-synced, so workflow `rules` could drift between repos over time. A future hardening could sync the `rules:` block via span-logic (like the AGENTS.md span). Originating change: `single-source-rules`.

## state-bounding

- **extrends STATUS remaining entries unchecked (LOW).** During lean-boot-context's one-time mechanical fix, only the single over-cap entry was moved verbatim to `ai-docs/archive/status-log.md`. The 3 retained entries' word budgets were not enforced — they bind at extrends' next archive. Originating change: `lean-boot-context`. Archive: `openspec/changes/archive/2026-06-18-lean-boot-context`.

## sync-mechanism

- **Sync guard `350` is a new magic number (LOW, monitor).** Propagating the new state-bounding rules pushed lean `extrends/AGENTS.md` 299→302 lines, tripping the 300-line tail-separator guard. The threshold was bumped to 350 as a pragmatic fix. If the synced span keeps growing, lean repos could approach 350 again → revisit the threshold or adopt an explicit empty-tail convention for lean repos. Originating change: `lean-boot-context`. Archive: `openspec/changes/archive/2026-06-18-lean-boot-context`.

## psc-monitor

- **`plans/historical-reports.md` still references `AGENTS.md` as a file-update target (LOW).** Four plain `AGENTS.md` file-references (not `§`-citations to removed appendix sections; `--check-refs` confirms not dangling) remain in `plans/historical-reports.md` — they reference AGENTS.md as the target of a completed plan's update, not as a citation source. Decide whether to repoint at next psc-monitor work. Originating change: `lean-boot-context`. Archive: `openspec/changes/archive/2026-06-18-lean-boot-context`.
- **Minor intentional appendix drops (LOW).** The psc-monitor appendix relocation dropped three items judged low-value/discoverable: target-customer market sizing, `nameparser`/`rapidfuzz` lib names, and a `requirements.txt`-deleted historical note. Recorded here in case they're wanted back. Originating change: `lean-boot-context`. Archive: `openspec/changes/archive/2026-06-18-lean-boot-context`.
