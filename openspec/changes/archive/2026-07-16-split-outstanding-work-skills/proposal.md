<!-- Tier: COMPLEX artifact structure (proposal + design + specs + tasks), reviewed by
     deepseek/deepseek-v4-flash per operator (2026-07-16). New scaffold-managed skill + a
     scaffold-managed skill rename — heavier than the product-audit-skill precedent (COMPLEX). -->

## Why

The `outstanding-work-review` skill's cost profile is lopsided: its deterministic gather
(`facts.py --check outstanding`) runs in under a second and needs only cheap untriaged-bucket
judgment, but its step-3 "Residual sweep" bullet asks for a full-repo prose crawl that — as the
first real-world psc-monitor run proved (2026-07-15) — spawns ~5 parallel subagents each reading a
dozen-plus files. Folding both into one skill means every "what's open right now?" check implicitly
invites (or forces the orchestrator to remember to skip) that heavy sweep. The residual sweep is
also load-bearing: the deterministic collector is point-only/heading-only by design, so it
structurally cannot see work buried in prose bodies — the source run found ~13 genuinely uncaptured
items the collector missed (e.g. 14 of 18 actionable findings in one `plans/` doc invisible behind a
single one-line tracker pointer). Splitting keeps the cheap path cheap by construction and gives the
deep sweep a documented, repeatable procedure instead of an ad-hoc crawl nobody schedules.

## What Changes

- **Rename** the existing `outstanding-work-review` skill to **`outstanding-work-scan`** and
  **narrow** its scope to the cheap path: deterministic gather + read + verify + the
  untriaged-bucket dedup-by-parent-ID judgment. Its step-3 "read prose bodies" residual-sweep
  bullet is removed and pointed at the new deep skill. Safe to run every session.
- **Add** a new **`outstanding-work-deep-sweep`** skill: runs `outstanding-work-scan` first, then
  fans out the five-category residual prose sweep as parallel subagents (from the source plan), then
  triages results into `knowledge/questions/INDEX.md` / `knowledge/roadmap.md`. **Pull-only**, same
  guardrails as `correctness-audit` / `composition-audit` (never wired into boot / AGENTS.md /
  auto-run). Mirrors this repo's own deterministic-detector-vs-deep-LLM-audit separation.
- **Scaffold-rename mechanics** (this is a scaffold-managed skill): update
  `scripts/scaffold_manifest.txt` (repoint the skill path + add a new entry for the deep skill), add
  the old skill path to `scripts/scaffold_manifest_removed.txt` (tombstone → downstream sync deletes
  the stale dir), and update every site naming the skill: the AGENTS.md "Working process" bullet
  (shared span), `knowledge/decisions/INDEX.md`, and the capability spec.

## Capabilities

### New Capabilities
- `outstanding-work-deep-sweep`: the pull-only deep residual-sweep skill contract — five-category
  prose/marker/change-dir sweep run as parallel subagents on top of the cheap scan, with the
  untriaged nested-citation false-positive discipline, triaging findings into the trackers.

### Modified Capabilities
- `outstanding-work-view`: the skill-invocation surface requirement (`pull-only-agent-neutral-invocation`)
  and Purpose reference the skill by its old name `outstanding-work-review`; these change to
  `outstanding-work-scan`. The `outstanding` fact contract itself is unchanged.

## Out of Scope

- Changing `scripts/outstanding.py` enumeration logic, `finding_id_pattern` defaults, or adding
  automated prose-body parsing — the point is documenting the human/LLM judgment step, not
  automating it away.
- Wiring either skill into any auto-run / boot path — both stay pull-only.
- Executing the downstream `sync_scaffold.py` propagation — operator-gated, tracked separately.

## Impact

- **Skills (scaffold-managed):** `.claude/skills/outstanding-work-review/` → `outstanding-work-scan/`
  (rename + narrowed step 3); new `.claude/skills/outstanding-work-deep-sweep/SKILL.md`.
- **Scaffold manifest + tombstone:** `scripts/scaffold_manifest.txt`,
  `scripts/scaffold_manifest_removed.txt`.
- **Instruction surface:** `AGENTS.md` (shared span), `knowledge/decisions/INDEX.md`.
- **Specs:** MODIFIED `openspec/specs/outstanding-work-view/spec.md`; NEW
  `openspec/specs/outstanding-work-deep-sweep/spec.md`.
- **Downstream (operator-gated, NOT in this change):** `sync_scaffold.py` propagation to
  psc-monitor + extrends, confirming the tombstone deletes the old dir downstream — tracked on
  `knowledge/reference/pending-downstream-propagation.md`.
- **No product/runtime code changes:** `scripts/outstanding.py`, `checks.py`, `facts.py` and the
  `knowledge_lint` drift checks are untouched.
