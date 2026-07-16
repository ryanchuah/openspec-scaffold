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

**DECISION (operator, 2026-07-16): apply routed to Sonnet throughout** ("apply using sonnet"). The
whole `tasks.md` loop runs on a Sonnet `apply-executor` subagent, not the deepseek-flash default.
This is operator pre-routing (AGENTS.md-sanctioned), NOT a fallback — no deepseek failure occurred.

## Verify checkpoint (2026-07-16)

1. **Verdict:** READY for archive. COMPLEX verify: my behavioral self-review + pro behavioral pass
   (READY, no defects) + flash test-quality lens pass (READY, change confirmed test-neutral) + the
   simplicity gate. No decision logic / external API / data path / auth-credential surface in the
   diff, so adversarial fixtures, live smoke, the data-scale rule, and the security review do not
   trigger (recorded determination).

2. **What I confirmed by eyeballing live output** (behavior, not counts): both new/renamed skills are
   discoverable and structurally valid (the harness skill list now surfaces `outstanding-work-scan`
   and `outstanding-work-deep-sweep`); the scan skill's step 3 is correctly narrowed (pointer to the
   deep skill + untriaged-bucket dedup + record only; roadmap-prioritization moved out); the
   deep-sweep skill covers all five residual categories and retains the parent-ID-disposition
   discipline; `scaffold_manifest.txt` repointed to scan + deep-sweep added; `openspec validate
   --strict` passes; `spec-delta-structure` clean; full suite green. Crucially, a read-only
   `sync_scaffold.py --check ../psc-monitor` shows the dir-form tombstone emits
   `STALE .claude/skills/outstanding-work-review/` (sync would rmtree the whole old dir) and the two
   new skills as MISSING — the intended downstream behavior.

3. **Defect found & fix (who):** the apply-executor wrote the removal tombstone in **file form**
   (`.claude/skills/outstanding-work-review/SKILL.md`) instead of **dir form**
   (`.claude/skills/outstanding-work-review/`). Per the file's own header ("a trailing '/' marks a
   directory entry") and the `lint-knowledge` precedent + tasks.md 3.3, file form would only unlink
   the SKILL.md downstream and leave an empty stale dir. **Found by orchestrator self-review** —
   neither multi-model pass flagged it (both returned READY). **Fixed inline by the orchestrator**
   (one-line path-format correction; qualifies as the trivial one-line exception), then confirmed via
   the read-only `--check` above (STALE now fires on the dir).
   *Re-run judgment (recorded):* I did NOT re-run the two paid multi-model passes after this fix. It
   is a one-line downstream-sync tombstone path-format correction, behaviorally inert to both passes'
   assessment domains (pro = skill/spec behavioral correctness; flash lens = test quality), the file
   was already in both passes' review surface, and the fix was independently confirmed correct from
   disk. Re-running a pro-tier pass for a trailing-slash fix contradicts the operator's stated
   cost-consciousness (flash reviewers, "COMPLEX is heavy"). Orchestrator judgment per the skill's
   judge-from-disk / overrule-with-rationale discipline.

4. **As-built delta:** the Sonnet apply-executor made two small in-spirit consistency edits to the
   scan skill beyond the literal wording of tasks 1.3/1.4 — removing residual `knowledge/roadmap.md`
   write mentions from the post-step-3 paragraph and the first Guardrails bullet, to match the
   narrowed scope. Endorsed (on-scope with the narrowing). No other as-built delta.

5. **Forward-looking items for the project docs** (fold into `knowledge/questions/INDEX.md` /
   `knowledge/decisions/INDEX.md` at archive — recorded nowhere else):
   - **`freeze_check.py` bold-tolerance follow-on:** during this change's propose reviews the flash
     reviewer bold-wrapped `**VERDICT:**` / `**PREMISE:**` on 3 of 4 artifacts, which
     `freeze_check.py`'s anchored regex rejects as `missing-verdict` (false negative; each overruled
     with recorded rationale). `freeze_check` should tolerate optional `**` emphasis around the
     VERDICT/PREMISE tokens. New follow-on — track it.
   - **Downstream propagation pending:** syncing this change (new `outstanding-work-scan` +
     `outstanding-work-deep-sweep`; tombstone deletes old dir) to psc-monitor + extrends is
     operator-gated. Confirmed via read-only `--check`: psc-monitor is MISSING both new skills and
     STALE the old dir. Queue on `knowledge/reference/pending-downstream-propagation.md`.
   - **Archive-deferred renames** (also in the Archive-reconciliation reminders above, restated so
     nothing is lost): `knowledge/decisions/INDEX.md` skill-name ref; the main
     `openspec/specs/outstanding-work-view/spec.md` Purpose + requirement rename (MODIFIED delta
     promotion); optional `## Purpose` on the promoted `outstanding-work-deep-sweep` spec.
   - **Observation (not this change's work):** the shipped SMALL change
     `openspec/changes/knowledge-lint-gitignored-citation-exempt/` has an unarchived lingering
     `plan.md` (with the allowlisted period-correct old-skill-name ref at line 53). Cleanup is a
     separate matter for the operator, noted only so it isn't lost.

**Still owned by archive** (do NOT reconcile here — write-discipline): `knowledge/STATUS.md`,
`knowledge/decisions/INDEX.md` (skill-name rename + a new decision entry for this change),
`knowledge/questions/INDEX.md` (the freeze_check follow-on + a follow-ons pointer for this change),
spec promotion into `openspec/specs/` (MODIFIED `outstanding-work-view` incl. the Purpose-preamble
rename + NEW `outstanding-work-deep-sweep` with optional Purpose),
`knowledge/reference/pending-downstream-propagation.md` update, and deletion of the now-absorbed
source plan `plans/outstanding-work-review-residual-sweep.md` if the archive-executor deems it
consumed.

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
