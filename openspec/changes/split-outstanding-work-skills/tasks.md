## 1. Rename & narrow the cheap skill → `outstanding-work-scan`

- [ ] 1.1 `git mv .claude/skills/outstanding-work-review .claude/skills/outstanding-work-scan`.
- [ ] 1.2 In `.claude/skills/outstanding-work-scan/SKILL.md` frontmatter: set `name: outstanding-work-scan`
      and bump `metadata.version: "1.0"` → `"1.1"`. Leave `description`, `license`, `compatibility`,
      `author`, `generatedBy` as-is unless the description text needs no change (it does not name the
      skill by slug).
- [ ] 1.3 Narrow the skill body to the cheap path. Under **Steps → 3. Judge (orchestrator)**: REMOVE
      the "Residual sweep" bullet (the prose-body-reading scope moves to the new deep skill) and
      replace it with a one-line pointer: the deep full-repo residual prose sweep now lives in the
      `outstanding-work-deep-sweep` skill; invoke that when a deep sweep is wanted. KEEP the
      "Triage the untriaged bucket" bullet (the untriaged-bucket dedup-by-parent-ID judgment) and its
      "Record durable decisions" wording. KEEP the "do not change what the deterministic collector
      enumerates" instruction. The broad "Prioritize open work / update roadmap" scope also moves to
      the deep skill — in the scan skill leave only recording of the untriaged-dedup outcomes.
- [ ] 1.4 Update any body prose in the scan SKILL.md that self-references the old name
      `outstanding-work-review` → `outstanding-work-scan` (e.g. the pull-only paragraph, guardrails).

## 2. Create the deep-sweep skill → `outstanding-work-deep-sweep`

- [ ] 2.1 Create `.claude/skills/outstanding-work-deep-sweep/SKILL.md` with frontmatter mirroring
      `correctness-audit/SKILL.md`'s shape: `name: outstanding-work-deep-sweep`, a `description` that
      says "deep residual-sweep of outstanding work; operator-invoked, pull-only", `license: MIT`,
      `compatibility: Requires openspec CLI.`, `metadata.author: openspec`, `metadata.version: "1.0"`,
      `metadata.generatedBy` matching siblings.
- [ ] 2.2 Body Step 1 — **Run the deterministic scan first:** invoke the `outstanding-work-scan`
      skill (its gather + read + verify + untriaged-bucket dedup) and consume its snapshot before any
      residual sweep.
- [ ] 2.3 Body Step 2 — **Five-category residual sweep as parallel subagents.** Condense the five
      categories from `plans/outstanding-work-review-residual-sweep.md` "Proposed approach" section
      into a scannable checklist (this is an agent-read skill file, not a report — keep it tight):
      (1) in-code markers; (2) questions/decisions/lessons body sweep; (3) plans body sweep;
      (4) reference/compliance/roadmap-body sweep; (5) change-dir prose + specs + untriaged-dedup.
      Instruct that each category runs as its own subagent checkpointing findings to disk, and each
      cross-references `knowledge/questions/INDEX.md` + `knowledge/roadmap.md` to avoid re-reporting
      tracked work. In category 5, KEEP the sentence flagging the nested-evidence-citation
      false-positive: before promoting an untriaged ID, check the **parent-ID disposition** (child
      citations nested inside an already-dispositioned parent are not free-standing findings) — this
      alone was 51 of 52 "untriaged" hits in the source run.
- [ ] 2.4 Body Step 3 — **Triage into trackers:** promote genuinely uncaptured items into
      `knowledge/questions/INDEX.md` (or per-item files) / `knowledge/roadmap.md`; record why dismissed
      items were dismissed. Note that durable structural reconciliation still normally happens at
      archive — this is the content pass.
- [ ] 2.5 Add a **Guardrails** block mirroring `correctness-audit`: operator-invoked, pull-only; NEVER
      wired into session boot, `AGENTS.md`, any mandatory-read set, or any auto-run hook; read-only
      w.r.t. repo state until the Step-3 triage writes; do NOT edit `scripts/outstanding.py`,
      `scripts/checks.py`, `scripts/facts.py`, or the `knowledge_lint` drift checks.

## 3. Scaffold manifest + tombstone

- [ ] 3.1 In `scripts/scaffold_manifest.txt`, repoint the existing
      `.claude/skills/outstanding-work-review/SKILL.md` line to
      `.claude/skills/outstanding-work-scan/SKILL.md` (preserve the file's ordering convention).
- [ ] 3.2 In `scripts/scaffold_manifest.txt`, ADD a new line
      `.claude/skills/outstanding-work-deep-sweep/SKILL.md` in the correct ordered position.
- [ ] 3.3 In `scripts/scaffold_manifest_removed.txt`, append
      `.claude/skills/outstanding-work-review/SKILL.md` with a dated comment, matching the existing
      `lint-knowledge`/`openspec-onboard` tombstone-entry format (so downstream sync deletes the stale
      old skill dir).

## 4. Instruction-surface reference (AGENTS.md shared span)

- [ ] 4.1 In `AGENTS.md`, "Working process" section, rename the pull-only bullet reference
      `outstanding-work-review` → `outstanding-work-scan` (single shared-span edit). Do NOT make any
      other AGENTS.md edits (prefix-cache batching).

## 5. Verify (apply-phase self-check)

- [ ] 5.1 `scripts/check.sh` runs green (ruff + format + pytest, incl. scaffold_lint invariant).
- [ ] 5.2 `python3 scripts/scaffold_lint.py` clean.
- [ ] 5.3 `openspec validate split-outstanding-work-skills --strict` exits 0.
- [ ] 5.4 `grep -rn "outstanding-work-review" .` shows stale refs ONLY in the expected
      archive-deferred / historical locations: `openspec/specs/outstanding-work-view/spec.md`
      (renamed at archive via the MODIFIED delta + Purpose promotion), `knowledge/decisions/INDEX.md`
      (renamed at archive by the archive-executor), `knowledge/research/**` (period-correct,
      lint-excluded), `openspec/changes/archive/**` (historical), `scripts/scaffold_manifest_removed.txt`
      (the tombstone — intentional), and this change's own dir (`openspec/changes/split-outstanding-work-skills/**`
      and `plans/outstanding-work-review-residual-sweep.md`). Any ref OUTSIDE that allowlist is a miss to fix.
