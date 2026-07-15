# HANDOFF — split `outstanding-work-review` into a cheap deterministic skill + a deep-sweep skill

> **Status:** deferred feature, fully scoped and operator-decided, **not started**. Pick this up in
> a fresh session. This is NOT a mid-change ran-out-of-context handoff — no partial work exists.
> The companion urgent fix from the same session (knowledge_lint gitignored-citation exemption)
> already shipped (commit `7f23eda`) and is unrelated to this. Delete this file once this feature
> is proposed/absorbed into a change dir.

## What and why (one paragraph)

psc-monitor ran the `outstanding-work-review` skill for the first time on real data (2026-07-15),
then did an operator-requested manual 5-subagent crawl to check whether the deterministic collector
(`scripts/outstanding.py`) misses real work. **It does** — the collector is point-only/heading-only
by design, so ~13 genuinely uncaptured items lived in prose bodies it structurally cannot read
(e.g. 14 of 18 actionable findings in one `plans/` doc were invisible behind a single one-line
tracker pointer; a tracker pointer read "CLOSED" while 17 items inside the linked file were still
OPEN). The full method + the exact collector mechanism that hides each of the five blind-spot
categories is already written up — **do not re-derive it, read the plan** (see below).

## THE source of truth for this work

**`plans/outstanding-work-review-residual-sweep.md`** — read it in full. It contains: the problem,
the five concrete residual-sweep categories with real calibration findings from the psc-monitor run,
the "why the collector can't see it" mechanism per category, the proposed checklist text, and the
Option A vs Option B design analysis. This handoff only records the operator decisions that resolve
the open questions in that plan, plus the rename scope the plan did not cover.

## Operator decisions (made 2026-07-16 — these resolve the plan's open questions)

1. **Option B, not Option A.** Split into two skills (the plan's recommended option), mirroring this
   repo's own `checks.py`/`facts.py`-deterministic vs `correctness-audit`-deep-LLM separation:
   - **cheap skill** (rename of today's `outstanding-work-review`) — deterministic gather
     (`facts.py --check outstanding`) + read + verify + the untriaged-bucket dedup-by-parent-ID
     judgment. No full-repo prose read. Safe to run every session. This is the "what's open right
     now?" check.
   - **new deep skill** `outstanding-work-deep-sweep` — invokes the cheap skill first, then fans out
     the five-category residual sweep as parallel subagents, then triages results into
     `knowledge/questions/INDEX.md` / `knowledge/roadmap.md`. **Pull-only**, same guardrails as
     `correctness-audit` / `composition-audit` (never wired into boot/AGENTS.md/auto-run).
2. **Rename the cheap skill to signal "deterministic".** Operator asked that the existing skill be
   renamed to include "deterministic" so the split is self-evident (verbatim: *"or any other rename
   as you see fit"*). **Recommended name: `outstanding-work-deterministic-review`.** Caveat to weigh:
   the cheap skill is *not purely* deterministic — it keeps the untriaged-bucket dedup-by-parent-ID
   **judgment** step (cheap, no full-repo read). So "deterministic" describes its *gather/basis*, not
   the whole skill. Alternatives if that overclaims: `outstanding-work-scan`. **Confirm the final two
   names with the operator as step 0** — everything else keys off them.

## Tier assessment (do this classification first, then get operator confirmation)

Likely **MEDIUM** (possibly COMPLEX): this is a **new capability** (new skill) **plus a
scaffold-managed skill rename**, which is heavier than the plan's original Option-B framing (the plan
assumed the cheap skill kept its name). A rename of a scaffold-managed skill dir touches the manifest,
needs a removal-tombstone, updates the capability spec, and must be repeated/synced downstream. Run
the normal MEDIUM lifecycle (propose → `tasks.md` reviewed by deepseek-v4-pro → apply → verify →
archive). Note there is an existing capability spec for this skill: `openspec/specs/outstanding-work-view/spec.md`
— decide whether the new deep skill is a new capability spec or an ADDED requirement set on the
existing one.

## Rename reference-update checklist (every site that names the skill today)

A rename is not just the dir — update **all** of these (grep `outstanding-work-review` to reconfirm
before you start; archive/ hits are historical and stay as-is):

- `.claude/skills/outstanding-work-review/SKILL.md` — the skill dir itself (rename dir + edit
  frontmatter `name:`, bump `metadata.version`).
- `scripts/scaffold_manifest.txt` line 19 — change the manifest path to the new dir; **add the OLD
  path to `scripts/scaffold_manifest_removed.txt`** (the tombstone mechanism) with a dated comment,
  so downstream sync DELETES the stale old skill dir instead of leaving both. (See the existing
  `lint-knowledge`/`openspec-onboard` tombstone entries there for the exact format.)
- `AGENTS.md` — the "Working process" bullet: *"invoke the pull-only `outstanding-work-review`
  skill"* (currently near line 371). This is a shared-span edit → propagates via sync. Batch it with
  any other AGENTS.md edits (prefix-cache invalidation warning at top of AGENTS.md).
- `openspec/specs/outstanding-work-view/spec.md` — the capability spec references the skill by name.
- `knowledge/decisions/INDEX.md` — a decision entry names it.
- `knowledge/research/workflow-audit-2026-07-11/caching-analysis.md` — **research dir; period-correct,
  leave as-is** (research is excluded from lint content checks by design; do NOT rewrite history).
- Add a **new** manifest entry for the new `outstanding-work-deep-sweep/SKILL.md`.

## Tasks (supersedes the plan's T1–T5; the plan's T1 fork is resolved to Option B + rename)

- [ ] **T0** Confirm the two final skill names with the operator (recommendation above). Classify tier
      (MEDIUM likely) and get tier+plan confirmation before executing.
- [ ] **T1** Create `.claude/skills/outstanding-work-deep-sweep/SKILL.md` <!-- lint:planned --> (not
      yet created): step 1 invokes the cheap
      skill; step 2 = the five-category residual-sweep checklist (from the plan's "Proposed approach",
      condensed + scannable — it's an agent-read skill file, not a report), run as parallel subagents;
      step 3 triages into `knowledge/questions/INDEX.md` / `knowledge/roadmap.md` exactly as the
      current skill's step 3 does. Mark pull-only, `correctness-audit`-style guardrails.
- [ ] **T2** Rename the existing skill (dir + frontmatter `name:` + version bump) and **narrow** its
      step 3 to just the untriaged-bucket dedup-by-parent-ID judgment (drop the "read prose bodies"
      residual-sweep bullet — that scope moves to the deep skill; point the old bullet at the new
      skill). Do the full rename reference-update checklist above (manifest + tombstone + AGENTS.md
      span + capability spec + decisions entry).
- [ ] **T3** In the deep skill's category-5 text, keep the sentence flagging the nested
      evidence-citation false-positive shape (check *parent-ID disposition* before promoting a child
      citation) — this alone was 51 of 52 "untriaged" hits in the source run.
- [ ] **T4** Propagate (operator-gated): `python3 scripts/sync_scaffold.py --check psc-monitor` then
      the real sync for each downstream repo (psc-monitor, extrends). Confirm the tombstone deletes the
      old skill dir downstream and `scaffold_check.py` passes with no hand-edit drift.
- [ ] **T5** Verify: `scripts/check.sh` green; `sync_scaffold.py --check <repo>` exit 0 (converged)
      for each downstream.

## Out of scope (unchanged from the plan)

- Changing `scripts/outstanding.py` enumeration logic, `finding_id_pattern` defaults, or adding
  automated prose-body parsing. The whole point is documenting the human/LLM judgment step, not
  automating it. (A tighter per-repo `finding_id_pattern` for two-tier ID schemes is a per-repo
  config decision, noted in the plan — not a scaffold default change here.)
- Wiring either skill into any auto-run path — both stay pull-only.
- The psc-monitor tracker edits that prompted this (they landed in psc-monitor's own
  `knowledge/questions/INDEX.md`) — only the generalizable method/mechanism carries over.
