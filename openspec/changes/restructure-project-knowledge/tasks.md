## 1. Scaffold — memory/ structure + universal taxonomy map

- [x] 1.1 Create `memory/README.md` — the universal taxonomy map (knowledge types, the one-line classification rule, the type→home table from design D-B/D-I). This is the synced, byte-identical map.
- [x] 1.2 Create the `memory/` skeleton: `decisions/INDEX.md`, `questions/INDEX.md` (with `## Active` and `## Parked` sections), `lessons.md`, `reference/` (with `.gitkeep`), `research/INDEX.md`. (`roadmap.md` is created by the move in 1.7.)
- [x] 1.3 Move scaffold `STATUS.md` → `memory/STATUS.md` (preserve the `## Latest change`/`## Prior change` format and ≤3-section cap); `git rm` the root `STATUS.md`.
- [x] 1.4 Transform scaffold `ai-docs/decisions.md` → `memory/decisions/INDEX.md` registry entries (design D-D format: `- **YYYY-MM-DD** · <slug> · <essence> → archive-path`, or `[inline]` when no archive). Map every existing entry — drop nothing. `git rm ai-docs/decisions.md`.
- [x] 1.5 Transform scaffold `ai-docs/open-questions.md` + `ai-docs/parked-follow-ons.md` → `memory/questions/`: each item becomes its own `memory/questions/<item>.md`, with `INDEX.md` Active holding blocker pointers and Parked holding non-blocker pointers. `git rm` both source files.
- [x] 1.6 Move scaffold `ai-docs/workflow-lessons.md` → `memory/lessons.md`; `git rm` the original.
- [x] 1.7 Move scaffold `ai-docs/improvement-roadmap.md` → `memory/roadmap.md`; move the prior-consolidation analysis docs (`consolidation-plan-2026-06-16.md`, `workflow-audit-2026-06-16.md`, `explore-agent-context-infra-2026-06-18.md`) → `memory/research/` (indexed in `research/INDEX.md`); `git rm` each original.
- [x] 1.8 Enumerate `ai-docs/archive/`; move substantive files (research/plans) into `memory/research/` or `memory/reference/`; discard `status-log.md` + `retired-notes.md`; then `git rm -r ai-docs/archive/`.
- [x] 1.9 Relocate the test fixtures out of `docs/` to `tests/`: move `docs/test/canary-non-convergence/`, `docs/test/commit-gate-smoke/`, and `docs/test/skill-enumeration-smoke/` to `tests/` (these are test infrastructure — the convergence canary required by the `apply-convergence-guard` spec, plus two smoke fixtures — not documentation). Update any self-referential `docs/test/` paths inside the moved files (the canary's `tasks.md` pytest command, the smoke READMEs' procedure paths) to the new `tests/` location. Drop the untracked `__pycache__`/`.pytest_cache` dirs with `rm -rf` (they are not git-tracked).
- [x] 1.10 Delete the now-empty scaffold `docs/`.
- [x] 1.11 Enumerate the root `tmp_*.md` files; salvage any not-in-code synthesized findings (the `tmp_spike*`/`tmp_research*`/`tmp_opt*` analyses) into `memory/research/` (indexed) or `memory/reference/`; then `git rm` all root `tmp_*.md`.
- [x] 1.12 Relocate `ai-docs/delegation-harness.md` → `.claude/skills/_shared/delegation-harness.md` (content unchanged); `git rm` `ai-docs/fast-track-workflow.md` and `ai-docs/research-fetch-convention.md`.
- [x] 1.13 Sweep: confirm `ai-docs/` is now empty; if any file remains, route it to its taxonomy home (per `memory/README.md`) and `git rm` it; then remove the empty `ai-docs/` directory.

## 2. Scaffold — AGENTS.md + config.yaml

- [x] 2.1 Slim `AGENTS.md` to identity + a "where everything lives" map that links to `memory/README.md`; preserve the three span anchors verbatim (`> **MANDATORY`, `## Roles`, `## After reading this file`); add the one-line fast-track tombstone ("autonomy is operator-told and ephemeral — no fast-track doc, by design").
- [x] 2.2 Add `rules.research` to `openspec/config.yaml` (the retired research-fetch convention), keeping `rules:` as the final top-level block.
- [x] 2.3 Rewrite `rules.archive` and any other `rules:` text that cites `ai-docs/...` or root `STATUS.md` to the new `memory/` paths.
- [x] 2.4 Fix the `context:` block's research-convention pointer to reference `openspec/config.yaml` `rules.research` (NOT a `memory/` path).
- [x] 2.5 (discovered during apply — not in the frozen list) Global path-reference rename: rewrite stale `ai-docs/` / root-`STATUS.md` / `docs/test/` references to their `memory/` / `.claude/skills/_shared/` / `tests/` homes across the SYNCED skill files (`.claude/skills/openspec-{apply,archive,propose,verify}-change/SKILL.md`), the migrated `memory/{STATUS,roadmap,lessons}.md` self-references, and `README.md` + `tests/skill-enumeration-smoke/README.md`. For deleted files (`fast-track-workflow.md`, `ai-docs/archive/*`, `research-fetch-convention.md`) rewrite the surrounding text (tombstone / single-archive / `rules.research`) rather than leaving a dangling path. The 3 non-delta main specs (`tier-confirmation-gate`, `commit-test-gate`, `verify-multimodel-gate`) are handled separately pending the delta-vs-hand-edit decision.

## 3. Scaffold — sync_scaffold.py + manifest

- [x] 3.1 Add `openspec/config.yaml` `rules:`-block partial sync: replace the target `rules:` block with scaffold's, preserve the per-repo `context:` block; append scaffold's `rules:` at EOF if the target has none; abort if a non-comment top-level key follows `rules:`.
- [x] 3.2 Add `openspec/config.yaml` handling to `--check`: compare the `rules:` block only (a differing per-repo `context:` is not drift).
- [x] 3.3 Update the reference-checker for the rename: `_AIDOC_PATH_RE` → `memory/`, the `_synced_files()` return filter, and the `cited_file.startswith("ai-docs/")` guard; drop the now-dead `ai-docs/archive/` and `docs/reviews/` entries from `_REF_SCAN_EXCLUDE`.
- [x] 3.4 Update `scripts/scaffold_manifest.txt`: add `memory/README.md`, `openspec/config.yaml`, and `.claude/skills/_shared/delegation-harness.md`; remove `ai-docs/delegation-harness.md`, `ai-docs/fast-track-workflow.md`, `ai-docs/research-fetch-convention.md`.

## 4. Scaffold — status_lint.py + tests

- [x] 4.1 Repath `status_lint.py` to `memory/STATUS.md` and `memory/decisions/INDEX.md` (STATUS checks: ≤3 sections, ≤150 words — unchanged).
- [x] 4.2 Rewrite the decisions check to the registry format (design D-D/D-E): for every line matching `^- \*\*YYYY-MM-DD\*\*`, require the `· <slug> · <text>` shape where `<text>` is either `<essence> → ` a `openspec/changes/archive/<dir>/` pointer that resolves, or `[inline] <rationale>`; flag malformed date-lines and dangling pointers. Drop the word-count, `**Status:**`, and `--since` logic.
- [x] 4.3 Rewrite `scripts/test_status_lint.py` for the new invariants: resolving-pointer entry passes, dangling-pointer entry fails, `[inline]` entry passes, malformed date-line fails; keep STATUS cap/word tests.

## 5. Scaffold — archive-executor reconciliation (both bodies, byte-identical)

- [x] 5.1 Rewrite `.claude/agents/archive-executor.md` step 3: targets become `memory/STATUS.md` (cap retained, **no** prune-to-status-log), `memory/decisions/INDEX.md` (append one D-D registry line), `memory/questions/` (Active blockers / Parked pointers); retire the separate `parked-follow-ons.md`; keep the trailing `status_lint.py` reconciliation loop.
- [x] 5.2 Write `.opencode/agents/archive-executor.md` body byte-identical to 5.1 (only the sanctioned frontmatter/intro clause may differ).
- [x] 5.3 Run `scripts/test_executor_body_agreement.py` (pre-check); resolve any divergence until the two bodies agree.

## 6. Scaffold — validation, sync tests, spec text, green suite

- [x] 6.1 Add `sync_scaffold.py` tests for the config `rules:` sync: rules-block replaced, `context:` preserved, idempotent (twice = no-op), drift detected by `--check`, append-if-absent, and abort when a key follows `rules:`.
- [x] 6.2 Verify the `scaffold-sync-mechanism` **delta** spec (`specs/scaffold-sync-mechanism/spec.md` in this change) covers every `ai-docs/`→`memory/` and root-`STATUS.md`→`memory/STATUS.md` path update to that capability's requirements; if any are missed, fix the **delta** (archive syncs the delta to the main spec — do not hand-edit the main spec).
- [x] 6.3 Run `openspec validate restructure-project-knowledge`; resolve any spec/format defect.
- [x] 6.4 Run the full scaffold suite (`pytest`) and `ruff`; resolve failures until green (this is the final gate, incl. `test_executor_body_agreement.py` and `test_status_lint.py`).

## 7. extrends migration (primary)

*Prerequisite: extrends is checked out at an operator-provided path; `sync_scaffold.py` is run from the scaffold checkout, targeting that path (never from inside extrends).*

- [ ] 7.1 On a fresh branch in extrends, selectively migrate `ai-docs/` knowledge into `memory/`, `git rm`-ing each original after transform: `decisions.md` → `decisions/INDEX.md` (registry; every entry mapped), `open-questions.md`+`parked-follow-ons.md` → `questions/` (each item its own `<item>.md` + Active/Parked pointers), `workflow-lessons.md` → `lessons.md`, `improvement-roadmap.md` (if present) → `memory/roadmap.md`. Then **sweep**: route any remaining `ai-docs/` knowledge file (e.g. `opencode-delegation-notes.md`) to its taxonomy home and `git rm` it, so `ai-docs/` is left holding ONLY the three managed files. **Do NOT touch the three managed `ai-docs/` files** (`delegation-harness.md`, `fast-track-workflow.md`, `research-fetch-convention.md`) — they stay at their `ai-docs/` paths for step 7.6.
- [ ] 7.2 Dissolve extrends `plans/`: pre-change design → `openspec/changes/<name>/`; `improvement-roadmap.md` → `memory/roadmap.md`; research/survey files → `memory/research/` (with INDEX); `product-strategy.md` + `product-vision.md` → `memory/reference/`.
- [ ] 7.3 Enumerate extrends `ai-docs/archive/`; preserve substantive files (e.g. `OPENSPEC_MIGRATION_PLAN.md`) into `memory/research/`; discard `status-log.md`; then `git rm -r ai-docs/archive/`.
- [ ] 7.4 Delete extrends `docs/` (all code-derivable per D-H) and any `tmp_*.md`.
- [ ] 7.5 Run `sync_scaffold.py <extrends>` from the scaffold checkout (brings `memory/README.md`, `.claude/skills/_shared/delegation-harness.md`, config `rules:`).
- [ ] 7.6 `git rm` the sync-orphans in extrends (`ai-docs/delegation-harness.md`, `ai-docs/fast-track-workflow.md`, `ai-docs/research-fetch-convention.md`); the now-empty `ai-docs/` should remove cleanly.
- [ ] 7.7 Update extrends `AGENTS.md` `## Project context` (one-paragraph identity + pointer to `memory/README.md`); preserve the span anchors so future syncs keep working.
- [ ] 7.8 Run `sync_scaffold.py --check <extrends>`, `--check-refs <extrends>`, and `status_lint.py <extrends>`; resolve any reported drift or dangling reference until all exit clean.

## 8. psc-monitor migration (secondary, with rescue)

*Prerequisite: psc-monitor is checked out at an operator-provided path; `sync_scaffold.py` is run from the scaffold checkout, targeting that path (never from inside psc-monitor). All rescues (8.1–8.5) MUST complete before the `docs/` deletion in 8.6.*

- [ ] 8.1 On a fresh branch in psc-monitor, rescue the not-in-code `docs/` content into `memory/reference/` per the D-H checklist: `entity-resolution.md`, `strategy-and-market.md`, the unbuilt specs (`05-anomaly-detection-spec.md`, `06-matcher-feedback-loop.md`), and `2026-06-stripe-webhook-review.md`; move the B5 post-mortem lesson (`19-postmortem-b5-livelock.md`) into `memory/lessons.md`.
- [ ] 8.2 Move psc-monitor not-in-code `ai-docs/` reference files (`ops-runbook.md`, `project-reference.md`) → `memory/reference/`; delete the code-derivable ones (`api-reference.md`, `schema-reference.md`, `repo-layout.md`).
- [ ] 8.3 Move psc-monitor research (`plans/gdpr-research/`, `plans/backup-cost-research/`) → `memory/research/` and index them in `memory/research/INDEX.md`.
- [ ] 8.4 Selectively migrate psc-monitor `ai-docs/` knowledge into `memory/`, `git rm`-ing each original after transform: `decisions.md` → `decisions/INDEX.md`, `open-questions.md`+`parked-follow-ons.md` → `questions/` (per-item `<item>.md` + Active/Parked), `workflow-lessons.md` → `lessons.md`, `improvement-roadmap.md` → `memory/roadmap.md`; dissolve the remaining `plans/` files (design → `openspec/changes/`, roadmap → `memory/roadmap.md`). Then **sweep**: route any remaining `ai-docs/` knowledge file (e.g. `opencode-delegation-notes.md`) to its taxonomy home and `git rm` it, leaving ONLY the three managed files. **Do NOT touch the three managed `ai-docs/` files** — they stay for step 8.8.
- [ ] 8.5 Enumerate psc-monitor `ai-docs/archive/`; preserve substantive content (e.g. the large `remove-legacy-hash.md`) into `memory/reference/` or `memory/research/`; discard `status-log.md`; then `git rm -r ai-docs/archive/`.
- [ ] 8.6 After 8.1–8.5 are in place, delete psc-monitor `docs/` (including `docs/reviews/` — its durable content is already rescued or promoted) and any `tmp_*.md`.
- [ ] 8.7 Run `sync_scaffold.py <psc-monitor>` from the scaffold checkout.
- [ ] 8.8 `git rm` the sync-orphans in psc-monitor (`ai-docs/delegation-harness.md`, `ai-docs/fast-track-workflow.md`, `ai-docs/research-fetch-convention.md`); the now-empty `ai-docs/` should remove cleanly.
- [ ] 8.9 Update psc-monitor `AGENTS.md` `## Project context` (identity + pointer to `memory/README.md`); preserve the span anchors and the `# Project reference` tail appendix.
- [ ] 8.10 Run `sync_scaffold.py --check <psc-monitor>`, `--check-refs <psc-monitor>`, and `status_lint.py <psc-monitor>`; resolve any reported drift or dangling reference until all exit clean.
