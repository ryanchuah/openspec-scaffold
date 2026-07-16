# Notes — split-outstanding-work-skills

## Tier & process (operator decisions, 2026-07-16)

- **Tier: COMPLEX artifact structure** — full set (proposal.md + design.md + specs/ + tasks.md).
  Chosen because a capability change needs delta specs (MEDIUM's tasks.md-only shape can't carry
  them) and the closest precedent (`product-audit-skill`, a new scaffold-managed skill) shipped
  COMPLEX. This change is heavier still (new skill **plus** a scaffold-managed skill rename).
- **Reviewer model: `deepseek/deepseek-v4-flash`** (NOT the pro default) for the propose-phase
  artifact reviews — operator's call, since COMPLEX is "a bit heavy for this change" and the
  checklist content is already pre-written in the source plan. Substituted per the propose skill's
  "If the user specified a different reviewer model, substitute it" allowance.

## Skill names (operator-confirmed, 2026-07-16)

- Cheap skill (rename of `outstanding-work-review`) → **`outstanding-work-scan`**.
- New deep skill → **`outstanding-work-deep-sweep`**.

## Spec modeling (operator-confirmed)

- **MODIFIED** `openspec/specs/outstanding-work-view/spec.md` — rename the `outstanding-work-review`
  → `outstanding-work-scan` skill-name references (Purpose + `pull-only-agent-neutral-invocation`
  requirement/scenarios). Capability name `outstanding-work-view` stays (names the snapshot
  contract, not the skill).
- **NEW** capability spec `outstanding-work-deep-sweep/spec.md` — the deep residual-sweep skill
  contract; pull-only, mirrors `correctness-audit`/`composition-audit`/`product-audit`.

## Source of truth

- `plans/outstanding-work-review-residual-sweep.md` — the five-category checklist + calibration
  findings + design analysis. Do NOT re-derive; condense into the new SKILL.md.
- `knowledge/HANDOFF.md` — operator decisions + rename reference-update checklist. Delete at archive.

## Change-specific acceptance criteria

1. `.claude/skills/outstanding-work-scan/SKILL.md` exists (renamed from `outstanding-work-review`),
   frontmatter `name: outstanding-work-scan`, `metadata.version` bumped; step 3 narrowed to the
   untriaged-bucket dedup-by-parent-ID judgment only (residual-prose-body scope removed, pointed at
   the deep skill). Old `outstanding-work-review/` dir no longer exists.
2. `.claude/skills/outstanding-work-deep-sweep/SKILL.md` exists: invokes the scan skill first, then
   the five-category residual sweep as parallel subagents, then triages into
   `knowledge/questions/INDEX.md` / `knowledge/roadmap.md`. Marked pull-only, `correctness-audit`-style
   guardrails. Category-5 nested-citation false-positive sentence retained.
3. `scripts/scaffold_manifest.txt`: line for the skill points to the new `outstanding-work-scan`
   path; a NEW entry for `outstanding-work-deep-sweep/SKILL.md`. Old
   `outstanding-work-review/SKILL.md` path added to `scripts/scaffold_manifest_removed.txt` (tombstone).
4. AGENTS.md "Working process" bullet renamed `outstanding-work-review` → `outstanding-work-scan`
   (shared span). `knowledge/decisions/INDEX.md` reference updated. Capability spec references updated.
   Research-dir mention left as-is (period-correct, lint-excluded).
5. `scripts/check.sh` green; `scripts/scaffold_lint.py` clean; `openspec validate --strict` exit 0.
6. Downstream propagation (sync to psc-monitor + extrends) is OPERATOR-GATED — NOT part of this
   apply; recorded on `knowledge/reference/pending-downstream-propagation.md` at archive.

## Apply-phase routing (operator decision at the apply gate)

This change is largely **prose surgery on skill files** (narrowing step 3; condensing the
five-category checklist into a new SKILL.md) — judgment-heavier than mechanical apply. Per AGENTS.md,
the operator MAY pre-route this apply to **Sonnet-first** rather than the deepseek-flash default.
Recommendation: Sonnet-first for tasks 1–2 (prose), flash is fine for 3–5 (manifest/AGENTS/verify),
or Sonnet-first throughout for simplicity. Surface at the apply gate.

## Out of scope

- Changing `scripts/outstanding.py` enumeration, `finding_id_pattern` defaults, or automated
  prose-body parsing. The point is documenting the human/LLM judgment step, not automating it.
- Wiring either skill into any auto-run/boot path — both stay pull-only.
- The actual downstream sync execution (operator-gated follow-on).

## Archive-reconciliation reminders (for the archive-executor / promotion review)

- **`knowledge/decisions/INDEX.md`**: rename the `outstanding-work-review` → `outstanding-work-scan`
  reference in the existing decision entry that names the skill (deferred from apply per
  write-discipline; do not miss it).
- The MODIFIED delta for `outstanding-work-view` carries only the normative
  `pull-only-agent-neutral-invocation` requirement (skill name → `outstanding-work-scan`).
  `apply_delta_spec.py` DEFERS MODIFIED (LLM merge). **Also rename the non-normative Purpose-preamble
  reference** in the promoted `openspec/specs/outstanding-work-view/spec.md` (currently line 9:
  "The companion `outstanding-work-review` skill …") — it is preamble, not a requirement, so the
  delta mechanism does not touch it; the archive-executor must rename it during promotion or it drifts.
- Record the `freeze_check.py` bold-`**`-tolerance follow-on (seen 3× this change on VERDICT/PREMISE
  bold-wrapping) in the trackers.
- NEW-capability delta `outstanding-work-deep-sweep/spec.md` is `## ADDED Requirements`-only (no
  Purpose preamble) per repo convention (archive-mechanization/product-audit). If a `## Purpose`
  section on the promoted `openspec/specs/outstanding-work-deep-sweep/spec.md` is wanted for
  consistency with sibling capability specs, the archive-executor authors it at promotion.

## Assumptions (non-blocking defaults; surface at next gate)

- `metadata.version` bump `1.0` → `1.1` — **confirmed** convention (`openspec-archive-change` is the
  one skill at `1.1`, bumped on a content change). No longer an open assumption.
