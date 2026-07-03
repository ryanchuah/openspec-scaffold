# Plan — prune-knowledge (SMALL) — succession-hardening portfolio CLOSER

**Status:** AWAITING operator tier+plan confirmation. Not yet executed.
**Tier:** SMALL (operator pre-approved AGGRESSIVE pruning; direction premise-gated `AGREE` 2026-07-02).
**Portfolio:** change 4 of 4 (closer). Prior three (`mechanize-invariants`, `repair-instruction-surface`,
`delegated-agent-safety`) all SHIPPED.

## Problem statement

The scaffold's own `knowledge/` tree carries accumulated drift and residue that the just-shipped
tooling now surfaces but nothing has yet cleaned:

- `python3 scripts/knowledge_lint.py` fails with **17 findings** (5 retired-path tokens, 12 broken
  prose-path citations) — a mix of genuine stale references, forward-references to files that don't
  exist yet, and structural false-positives (contrast citations, cross-repo refs, the linter's own
  self-documentation).
- Two parked question files are recorded as fully resolved but never closed.
- `knowledge_lint.py`'s `DEFAULT_RETIRED_PATHS` bakes a personal path (`/home/me/`) into golden-source
  defaults.
- The `openspec-onboard` skill (551 lines) re-implements the OpenSpec lifecycle inline as a user
  tutorial — a standing drift-risk against AGENTS.md + the per-phase skills, and misaligned with the
  operator's "mechanism over docs, agents orient via AGENTS.md not a tutorial" philosophy.
- Stray obsolete files under `plans/` from a shipped change.

Left alone, the lint gate stays red (eroding its value), the resolved trackers mislead, and the
tutorial skill keeps drifting from the real lifecycle.

## Proposed approach

Drive `knowledge_lint.py` to **exit 0 (green)** on this repo via targeted, meaning-preserving edits;
close resolved trackers; resolve the onboard-skill drift risk; scrub `plans/` residue. Every
disposition below preserves accurate content — where a citation is legitimate (contrast, cross-repo,
archived-change, or forward-reference), it is handled by the *correct* mechanism (linter
`EPHEMERAL_PATHS`, archive-path repoint, or de-citing prose that merely *names* a concept), never by
mangling a true statement.

### Per-finding disposition (all 17)

| Finding (file:line — token) | Class | Disposition |
|---|---|---|
| `knowledge/audit-log.md` ×4 — README:16, deterministic-tooling-layer-follow-ons:51, knowledge-lint-follow-ons:12,24 | forward-ref (created on first audit) | Add `knowledge/audit-log.md` to `EPHEMERAL_PATHS` in `knowledge_lint.py` (existing mechanism, mirrors `knowledge/HANDOFF.md`). No stub file. |
| `mechanize-invariants-follow-ons.md:29 — /home/me/` | documents the scope-(d) issue | Auto-clears once `/home/me/` is removed from `DEFAULT_RETIRED_PATHS`. |
| `roadmap.md:29 — ai-docs/` | stale roadmap item ("Context onboarding") — its work (1A appendix relocation, 1B state-bounding) SHIPPED via lean-boot-context + add-status-lint; 1C ruled out | Close the item (mark `✅ DONE`, matching the file's other closed items) — removes the retired-path token. |
| `decisions/INDEX.md:38 — ai-docs/` | accurate historical record (restructure migration `ai-docs/→memory/`) | Meaning-preserving reword `ai-docs/→memory/` → `ai-docs → memory` (drops the trailing-slash token; history intact). |
| `lessons.md:76 — openspec/changes/fix-convergence-guard/` | archived change, missing archive prefix | Repoint to `openspec/changes/archive/2026-06-17-fix-convergence-guard/`. |
| `.opencode/skills/` ×2 — decisions:10, lessons:12 | contrast citations ("this path should NOT exist / was hallucinated") | De-cite: name the concept in prose without formatting it as a resolvable path citation (drop backticks/trailing-slash). Meaning preserved. |
| `parked-psc-monitor.md:3 — plans/historical-reports.md` ×2 | cross-repo ref (psc-monitor's file, not this repo's) | De-cite / mark explicitly as the psc-monitor-repo path. |
| `knowledge-lint-follow-ons.md` self-refs — :9 (fix-convergence-guard), :9,10 (ai-docs/), :12,24 (audit-log), :14 (.opencode/skills/), :15 (historical-reports) | the file *documents* these very findings | Update the file (see scope b): its bullet-1 drift is now RESOLVED and its bullet-2 open-question is answered — rewrite those bullets to record the resolution without re-embedding the literal tokens; keep the still-open follow-ons (downstream burn-down, latent audit-log check, count-check idea, predicate-pruning). |

**Success criterion:** `python3 scripts/knowledge_lint.py` exits 0. If any single citation genuinely
cannot be de-cited without harming meaning, it is *recorded* as a documented residual — not mangled —
but the analysis above finds all 17 cleanly resolvable to zero.

### Tasks (ordered; apply-executor works top-to-bottom)

1. **Linter edits** (`scripts/knowledge_lint.py`, scaffold-managed → propagates):
   - Add `"knowledge/audit-log.md"` to `EPHEMERAL_PATHS`.
   - Remove `"/home/me/"` from `DEFAULT_RETIRED_PATHS`.
2. **Genuine-drift fixes:**
   - `knowledge/roadmap.md`: close the "Context onboarding — lean AGENTS.md + bound the mutable state
     files" item as `✅ DONE` (verify 1A/1B shipped via the decisions registry first).
   - `knowledge/lessons.md:76`: repoint to the archive path.
   - `knowledge/decisions/INDEX.md:38`: de-slash the `ai-docs/→memory/` historical mention.
3. **De-cite legitimate non-resolving citations:** `.opencode/skills/` in `decisions/INDEX.md:10` and
   `lessons.md:12`; `plans/historical-reports.md` in `parked-psc-monitor.md`.
4. **Close resolved trackers** (scope b):
   - `knowledge/questions/cap-status-log-follow-ons.md` — verified fully resolved → close (remove its
     `INDEX.md` Parked pointer + delete the file, OR mark resolved-in-place per the split rule; flag
     the deletion).
   - `knowledge/questions/split-open-questions-follow-ons.md` — verified fully resolved → close.
   - Sweep the remaining Parked pointers for any other fully-resolved files (report, don't mass-delete).
   - `knowledge/questions/knowledge-lint-follow-ons.md` — rewrite resolved bullets (1, and 2's
     concrete instances) to record resolution; retain genuinely-open items.
5. **`plans/` residue** (scope e — FLAG DELETIONS): delete `plans/premise-review.md` and
   `plans/pro-agent-flash-delegation.md` (both belong to `pro-agent-flash-delegation`, SHIPPED +
   archived 2026-06-26 — verified obsolete).
6. **`openspec-onboard` fate** (scope c — OPERATOR DECISION, see below): if DELETE — remove
   `.claude/skills/openspec-onboard/`, its `scripts/scaffold_manifest.txt` line (13), and its line in
   `tests/skill-enumeration-smoke/README.md`; record the no-tombstone downstream-deletion obligation
   in the pending-sync note. If SLIM — reduce to a thin pointer at AGENTS.md + the per-phase skills.
7. **Re-run gates:** `python3 scripts/knowledge_lint.py` (exit 0) and `pytest -q` (green, incl. the
   `scaffold_lint` SEAL) before any commit.

## Operator decisions to confirm (fold into tier+plan confirmation)

- **D1 — `openspec-onboard` fate.** RECOMMEND **DELETE**. It is a 551-line user tutorial that
  re-implements the lifecycle inline (drift-prone), is not referenced by AGENTS.md or any live skill
  (only by historical research docs + the smoke fixture), and contradicts the "mechanism over docs /
  no maintainer handbook" philosophy. Deletion is clean but has a **tombstone consequence**: the
  scaffold manifest has no deletion mechanism, so the `extrends` + `psc-monitor` copies must be
  **manually deleted per-repo when the sync freeze lifts** — recorded in the pending-sync note.
  Alternatives: SLIM to a thin pointer; or KEEP.
- **D2 — deletions to approve** (standing "flag deletions" preference): the two `plans/` files (task 5),
  the two resolved parked files (task 4), and — pending D1 — the onboard skill dir.

## Out of scope

- **Downstream propagation** of the `knowledge_lint.py` edits (and any onboard deletion) — the sync
  freeze holds; these join the pending-sync queue. No `sync_scaffold.py` run.
- **A general known-absent/allowlist mechanism in the linter** — the bullet-2 "OPEN QUESTION" is
  answered by resolving the concrete instances (YAGNI holds); the residual *linter-smarts* gap (it
  cannot natively distinguish contrast / cross-repo / archived-change citations from real drift)
  stays a recorded `knowledge-lint` follow-on, not built here.
- **Predicate-pruning / `python`-vs-`python3` cleanups** inside `knowledge_lint.py` (follow-on bullet 6).
- **The `succession-hardening/` plan-dir residency + transient-handoff deletion** — handled at
  prune-knowledge's ARCHIVE step (the handoff is still guiding this change), not in the apply body.
- Any new capability/behavior. This is cleanup only.

## Process (SMALL)

Plan (this file) → **flash premise pass** (orchestrator-invoked, before apply) → operator tier+plan
confirmation (premise verdict folded in) → delegate apply to `deepseek-v4-flash` via
`opencode run --agent apply-executor` → orchestrator verification + a single `deepseek-v4-flash`
verifier pass → commit in small reviewed checkpoints (local `main`; no push) → archive/closeout
(portfolio close: reconcile STATUS via archive-executor, resolve `succession-hardening/` residency,
delete the transient handoff).

## Verification

- `python3 scripts/knowledge_lint.py` → exit 0 (mechanism-checked completion of scope a).
- `pytest -q` green, including the `scaffold_lint` SEAL (guards manifest-completeness + dangling-skill
  refs after any onboard deletion).
- Orchestrator behavioral review of every diff + a single flash verifier pass.
