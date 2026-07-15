# SMALL plan — document a repeatable residual-sweep step in outstanding-work-review

**Source:** downstream psc-monitor session, 2026-07-15 — first real-world run of the
`outstanding-work-review` skill, followed by an operator-requested manual crawl to check whether
the deterministic collector (`scripts/outstanding.py`) misses real work due to its point-only /
heading-only enumeration choices. It does. This plan turns that one-off crawl into the repeatable
step the skill's own text already asks for (see `SKILL.md` step 3, "Residual sweep" bullet:
*"Convert the occasional human/LLM sweep of these residual sources into a documented, repeatable
step here — do not change what the deterministic collector enumerates."*). Full findings/evidence
from the source run live only in that psc-monitor session's transcript — this plan reconstructs
the generalizable procedure, not the repo-specific findings (those don't belong in the scaffold).

## Problem

`scripts/outstanding.py` is deliberately partial by design (see its own docstrings): it captures
*point-level* entries for `plans/*.md` and `knowledge/questions/*.md` per-item files (filename +
first heading only, never body content), only extracts `## ` *heading text* from
`knowledge/roadmap.md` (never the body beneath), no-ops in-code TODO/FIXME scanning entirely, and
never touches `knowledge/decisions/`, `knowledge/reference/` (or repo-specific reference/compliance
dirs), or non-`tasks.md` files inside `openspec/changes/<name>/`. These are reasonable engineering
trade-offs (full prose parsing would be brittle/expensive to do deterministically) — but the skill
currently gives the orchestrator no concrete procedure for compensating with judgment. In practice
this means real, uncaptured work quietly accumulates outside `knowledge/questions/INDEX.md` and
`knowledge/roadmap.md`, discoverable only by an ad-hoc full-repo crawl nobody schedules.

A live test of this on psc-monitor (175 collector-tracked items, 52 flagged "untriaged") found:
zero of the 52 untriaged findings were real gaps (all were either nested evidence-citations under
an already-tracked parent finding ID, or a single regex false-positive on a hash-name string) —
but the residual crawl of prose bodies surfaced ~13 genuinely uncaptured items the collector
structurally cannot see, including one case where 14 of 18 individually-actionable findings in a
`plans/` doc were invisible because only 4 were named in the tracker's one-line pointer, and a
tracker pointer that read as "fully closed" when 17 items inside the linked file were still
explicitly marked OPEN.

## Proposed approach

Add a concrete "Residual sweep checklist" to `SKILL.md` step 3, as five parallelizable sweep
categories an orchestrator can hand to subagents (mirrors what actually worked downstream):

1. **In-code markers** — grep tracked source dirs (exclude generated/vendored/test-fixture data)
   for TODO/FIXME/HACK/XXX/NotImplementedError/"not implemented"/"for now"/"temporary"/"workaround".
   Judge each hit: genuine deferred-work marker vs. stylistic/explanatory comment or test-double
   vocabulary (mock/stub naming). Report only genuine candidates — this category is usually clean
   and expected to stay clean; don't force findings.
2. **Questions/decisions/lessons body sweep** — read every `knowledge/questions/*.md` (excluding
   `INDEX.md`) in full, plus `knowledge/decisions/INDEX.md`, `knowledge/lessons.md`, and
   `knowledge/ratchet-log.md` (or repo-equivalent). Cross-reference against `INDEX.md`'s own
   Active/Parked summaries: flag content that (a) isn't reflected as a one-line pointer at all, or
   (b) contradicts/supersedes what the pointer currently says (staleness, not just omission).
3. **Plans body sweep** — read every `plans/**/*.md` (excluding `plans/archive/`) in full,
   prioritizing files shaped like findings/ledgers (multiple individually-numbered items, a
   findings register, an attack list, evidence docs) since those are most likely to hide
   individually-trackable work behind one aggregate pointer. Cross-reference against
   `knowledge/questions/INDEX.md` and `knowledge/roadmap.md`.
4. **Reference/compliance/roadmap-body sweep** — grep `knowledge/reference/*.md` and any
   repo-specific regulatory/compliance dir for TBD/"not yet built"/"not drafted"/"PROVISIONAL"/
   "pending" markers; read `knowledge/roadmap.md` in full (not just headings). For any "not yet
   built" claim, spot-check the claim against the actual codebase — if the feature now exists,
   that's a **doc-drift finding** (a different defect class from an uncaptured task) and should be
   reported separately.
5. **Change-dir prose + specs + untriaged-dedup sweep** — for each non-archived
   `openspec/changes/<name>/`, read `proposal.md`/`design.md`/`notes.md` (not just `tasks.md`) for
   open questions/deferred items with no corresponding checkbox. Skim `openspec/specs/*/spec.md`
   for TBD markers. For the untriaged-findings bucket specifically: before promoting an ID, check
   whether it's actually a citation *nested inside* a different, already-tracked parent finding ID
   (a known false-positive shape when `finding_id_pattern` is permissive) rather than a
   free-standing finding — this alone accounted for 51 of 52 "untriaged" hits in the live test.

Also record, as a **separate observation** (not a scope item for this plan): the untriaged-findings
regex can false-positive on nested evidence-citation IDs and incidental hash-shaped tokens (e.g. a
literal "SHA-256" mention). Repos with a two-tier ID scheme (parent finding ID + child evidence
citations sharing the same shape) may want a tighter `finding_id_pattern` in `checks.toml`, or to
document the dedup-by-parent-ID judgment call from sweep category 5 above as the standard
disposition. This plan does not change `outstanding.py`'s regex or defaults — config-tuning is a
per-repo decision, not a scaffold default change.

## Tasks (implement top to bottom, check each off)

- [ ] **T1** In `.claude/skills/outstanding-work-review/SKILL.md`, expand the existing "Residual
  sweep" bullet under step 3 into the five-category checklist above (condense the prose; keep it
  scannable — this is a skill file read by agents, not a report). Explicitly keep the existing
  "do not change what the deterministic collector enumerates" instruction.
- [ ] **T2** Add one sentence to the checklist's category 5 flagging the nested-evidence-citation
  false-positive shape for the untriaged-findings bucket, so orchestrators check *disposition of
  the parent ID* before promoting a child citation into `knowledge/questions/INDEX.md`.
- [ ] **T3** Bump `metadata.version` in the `SKILL.md` frontmatter (currently `"1.0"`) per this
  repo's normal versioning convention for skill content changes — check sibling skill files for the
  exact convention if `"1.0"` → `"1.1"` isn't it.
- [ ] **T4** Sync to at least psc-monitor (`python3 scripts/sync_scaffold.py psc-monitor`) and any
  other downstream repos with `outstanding-work-review` in `scripts/scaffold_manifest.txt`; verify
  with `--check` before syncing for real.
- [ ] **T5** Confirm `scripts/scaffold_check.py`'s pre-commit guard still passes in each synced
  downstream repo (no accidental hand-edit drift introduced by this change).

## Out of scope

- Changing `scripts/outstanding.py`'s enumeration logic, `finding_id_pattern` defaults, or adding
  automated prose-body parsing — the whole point of this plan is documenting the *human/LLM*
  judgment step, not automating it away.
- Any repo-specific findings from the psc-monitor session that prompted this (those were triaged
  directly into psc-monitor's own `knowledge/questions/INDEX.md` in that session, not carried here).
- Wiring this skill into any auto-run path — it stays pull-only per its existing guardrail.

## Verification

- `SKILL.md` still parses as valid frontmatter + markdown (no tooling changes needed to check this
  beyond a visual diff review).
- Re-run `python3 scripts/sync_scaffold.py --check <repo>` for each downstream repo after sync;
  exit 0 = converged.
