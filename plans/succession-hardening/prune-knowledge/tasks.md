# tasks — prune-knowledge (SMALL)

Work top-to-bottom. Check off each `[ ]` → `[x]` in THIS file as it lands. Do NOT commit.
Full rationale + per-finding disposition is in `plan.md` (same dir) — read it first.
**Line numbers below are approximate — locate by the quoted text, not the number.**
Success is mechanically defined: after task 7.1, `python3 scripts/knowledge_lint.py` exits 0.

## 1. Linter edits (`scripts/knowledge_lint.py` — scaffold-managed)

- [x] 1.1 In the `EPHEMERAL_PATHS` tuple (currently `("knowledge/HANDOFF.md",)`), ADD
  `"knowledge/audit-log.md"`. Result: `("knowledge/HANDOFF.md", "knowledge/audit-log.md")`.
- [x] 1.2 In the `DEFAULT_RETIRED_PATHS` tuple, REMOVE the `"/home/me/",` entry. Leave
  `"ai-docs/"`, `"plans/open-issues.md"`, `"docs/reviews/"`.

## 2. Genuine-drift fixes

- [x] 2.1 `knowledge/roadmap.md` — the item `## Context onboarding — lean AGENTS.md + bound the
  mutable state files`. Its work has SHIPPED (verify against `knowledge/decisions/INDEX.md`:
  `lean-boot-context` 2026-06-18 relocated the psc-monitor appendix = lever 1A; `add-status-lint`
  2026-06-18 bounded the state files = lever 1B; lever 1C was ruled out). CLOSE the item the same way
  the file's other closed items are done: retitle to `## Context onboarding … — ✅ DONE 2026-06-18 —
  COMPLETE` and replace the multi-line `**Summary:**`/`**Dependencies:**` body with a one-line
  `**Resolution:**` note. **The closed item MUST NOT contain the literal token `ai-docs/`** (that is
  the finding). Reference the shipped changes by name instead of the retired path.
- [x] 2.2 `knowledge/lessons.md` — find the sentence citing `openspec/changes/fix-convergence-guard/`
  (the W3-apply lesson, ~line 76). Repoint it to
  `openspec/changes/archive/2026-06-17-fix-convergence-guard/`.
- [x] 2.3 `knowledge/decisions/INDEX.md` — the `restructure-project-knowledge` registry line (~line 38)
  contains `ai-docs/→memory/`. Reword to `ai-docs → memory` (drop BOTH trailing slashes; keep the
  historical meaning). This removes the literal `ai-docs/` retired-path token.

## 3. De-cite legitimate non-resolving citations (remove backticks so they aren't parsed as live path citations)

The broken-citation check only flags a **backtick-wrapped** token whose first path segment is a real
top-level dir. These citations are legitimate (a path that intentionally does NOT exist / a
downstream-repo path); removing the backticks fixes the finding without changing meaning.

- [x] 3.1 `knowledge/decisions/INDEX.md` — `skills-in-dot-claude-only` entry (~line 10). Remove the
  backticks around `` `.opencode/skills/` `` only. LEAVE `` `.claude/skills/**` `` backticked (it
  resolves via glob). Result prose: "…a second .opencode/skills/ copy would create a divergence hazard".
- [x] 3.2 `knowledge/lessons.md` (~line 12) — remove the backticks around `` `.opencode/skills/` ``.
  LEAVE the trailing `` `.claude/skills/` `` backticked. Result: "An .opencode/skills/ discovery
  convention exists (hallucinated — OpenCode ≥1.16 auto-loads `.claude/skills/`)."
- [x] 3.3 `knowledge/questions/parked-psc-monitor.md` (line 3) — the TWO `` `plans/historical-reports.md` ``
  citations refer to **psc-monitor's** file, not this repo's. Remove the backticks around both (and,
  for clarity, you may prefix "psc-monitor's "). No other change to that item.

## 4. Close resolved trackers (scope b)

- [x] 4.1 `knowledge/questions/cap-status-log-follow-ons.md` — both items are recorded DONE/RESOLVED
  (verified). **DELETE the file** and remove its pointer line from the `## Parked` section of
  `knowledge/questions/INDEX.md`.
- [x] 4.2 `knowledge/questions/split-open-questions-follow-ons.md` — both items DONE (verified).
  **DELETE the file** and remove its `## Parked` pointer line from `knowledge/questions/INDEX.md`.
- [x] 4.3 `knowledge/questions/knowledge-lint-follow-ons.md` — rewrite the now-resolved content:
  - **Bullet 1** ("Scaffold's own pre-existing knowledge drift…"): all three sub-items (roadmap
    `ai-docs`, lessons `fix-convergence-guard` prefix, decisions:38) are FIXED by this change. Replace
    the bullet with a one-line "RESOLVED 2026-07-03 by `prune-knowledge`" note. **Ensure the rewritten
    bullet contains no literal `ai-docs/` token and no `` `openspec/changes/fix-convergence-guard/` ``
    citation** (those are findings on this file).
  - **Bullet 2** ("Known-absent-by-design paths…"): `knowledge/audit-log.md` is now handled via the
    linter's `EPHEMERAL_PATHS`; the `.opencode/skills/` + cross-repo `historical-reports.md` cases are
    handled by de-citing (tasks 3.1–3.3). Rewrite the bullet to record this resolution and to state the
    remaining decision: a **general** known-absent/allowlist mechanism is NOT added (YAGNI holds); the
    residual *linter-smarts* gap — it cannot natively distinguish contrast / cross-repo / archived-change
    citations from real drift — stays a deferred follow-on. **Rewrite so the bullet contains no
    backtick-wrapped token whose first segment is a real top-level dir** (e.g. write the paths without
    backticks, or without a trailing slash) — otherwise it re-flags itself.
  - **Keep bullets 3, 4, 5, 6** (downstream burn-down, latent audit-log check, count-check idea,
    predicate-pruning) unchanged — still open.
- [x] 4.4 `knowledge/questions/mechanize-invariants-follow-ons.md` (~line 29) — the item noting
  `DEFAULT_RETIRED_PATHS` bakes a personal path: mark it RESOLVED 2026-07-03 (removed from defaults in
  task 1.2). The `/home/me/` mention no longer flags (it is no longer a token), so the entry text may
  keep or drop it; prefer a short "RESOLVED" rewrite.
- [x] 4.5 Skim the remaining `## Parked` pointers in `knowledge/questions/INDEX.md` and open each
  referenced file only enough to judge if it is FULLY resolved. **Do NOT delete any others** — just
  LIST any that look fully-resolved in your completion report for the orchestrator to review.

## 5. `plans/` residue — FLAG deletions (scope e)

- [x] 5.1 DELETE `plans/premise-review.md` (premise pass for the shipped `pro-agent-flash-delegation`).
- [x] 5.2 DELETE `plans/pro-agent-flash-delegation.md` (that change SHIPPED + archived 2026-06-26).
  (Do NOT touch anything under `plans/succession-hardening/`.)

## 6. Delete the `openspec-onboard` skill (scope c — operator-approved)

- [x] 6.1 DELETE the directory `.claude/skills/openspec-onboard/` (including its `SKILL.md`).
- [x] 6.2 Remove the line `.claude/skills/openspec-onboard/SKILL.md` from `scripts/scaffold_manifest.txt`.
- [x] 6.3 `tests/skill-enumeration-smoke/README.md` — this is a MANUAL smoke doc (not pytest). Update it
  for accuracy: remove the `"name": "openspec-onboard"` line from the expected list, and change every
  "**7** / seven skills" reference to **6 / six** and drop `onboard` from the parenthetical
  `(apply-change, archive-change, explore, onboard, propose, sync-specs, verify-change)`.
- [x] 6.4 In your completion report, record VERBATIM: "TOMBSTONE: openspec-onboard deleted; the scaffold
  manifest has no deletion mechanism, so the extrends and psc-monitor copies must be manually deleted
  per-repo when the sync freeze lifts."

## 7. Gates (must pass; do NOT commit)

- [x] 7.1 Run `python3 scripts/knowledge_lint.py`. It MUST exit 0 (zero findings). If any finding
  remains, fix it per the plan's disposition table (EPHEMERAL / de-cite / archive-repoint / de-slash)
  and re-run until clean.
- [x] 7.2 Run `pytest -q` from the repo root (NOTE: use `pytest`, NOT `python3 -m pytest`). It MUST be
  green, including the `scaffold_lint` SEAL test (which re-validates manifest-completeness and
  dangling-skill-refs after the onboard deletion).
- [x] 7.3 Do NOT commit. End with a completion report: files changed, any deviations from this list,
  the task-4.5 sweep findings, the task-6.4 TOMBSTONE line, and anything the primary should re-check at
  verify.
