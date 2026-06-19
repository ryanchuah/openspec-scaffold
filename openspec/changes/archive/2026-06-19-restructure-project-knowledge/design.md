# Design: restructure-project-knowledge

## Context

Three repos share one workflow system. The **scaffold** (`openspec-scaffold`) is the golden source; it propagates shared mechanism files to **extrends** and **psc-monitor** via `scripts/sync_scaffold.py`. Today each repo's project knowledge is spread across five directories named by inconsistent logics (`ai-docs/`, `docs/`, `plans/`, `openspec/`, `tmp_*.md`), append-only files grow without bound (extrends `decisions.md`: 1,341 lines / 59 entries), two parallel archives record the same history, and hand-written codebase docs rot.

The cost we are paying is **orientation cost**: an agent spends its first chunk of every session discovering where things are and what's current, instead of working. Token efficiency is a side effect; the goal is a knowledge base whose *shape* tells a human or an LLM where everything is and where new knowledge goes.

Constraints (verified during exploration):
- `sync_scaffold.py` is **copy-only — it never deletes**. Removing or relocating a managed file leaves a stale orphan downstream that must be removed by hand.
- `openspec/config.yaml` is **not** synced today; its `context:` block is per-repo.
- `AGENTS.md` syncs by span-replace against three anchors (`> **MANDATORY`, `## Roles`, `## After reading this file`) and aborts if a long target has no tail separator.
- Both `archive-executor.md` bodies (`.claude/` + `.opencode/`) must stay byte-identical (`test_executor_body_agreement.py`).
- `status_lint.py` hardcodes `STATUS.md` and `ai-docs/decisions.md`.
- The migration targets are **extrends (primary, real volume)** and **psc-monitor (secondary)**; the scaffold carries the template + mechanism.

## Goals / Non-Goals

**Goals**
- One coherent structure organized by knowledge *type*, with a written, discoverable taxonomy and a single classification rule.
- Bounded boot load that does not grow with project history.
- A single archive.
- The new structure live in extrends and psc-monitor, with the scaffold's mechanism updated to propagate and enforce it.
- Zero loss of not-in-code knowledge.

**Non-Goals**
- Changing OpenSpec CLI behavior or the change-tiering system.
- Building a programmatic codebase-docs generator (only the decision to stop hand-maintaining them).
- A backward-compatibility shim layer — each repo is migrated atomically (see D-G).

## Decisions

### D-A — One change in scaffold, phased cross-repo execution
This change is authored and archived in the **scaffold**, because the mechanism it changes (sync, lint, manifest, executors, AGENTS spans, config rules) lives there and must change there or the next sync reverts any downstream restructure. Execution is phased: (1) scaffold mechanism + template skeleton, (2) extrends migration, (3) psc-monitor migration, (4) convergence verification. *Alternative rejected:* three independent OpenSpec changes (one per repo) — rejected because the design is shared and splitting it triples review for no benefit; the downstream migrations are one-time structural edits, not feature work that needs its own spec/archive.

### D-B — Final directory structure
```
<repo>/
├── AGENTS.md                  BOOT: identity + "where everything lives" map + standing rules + pointer to memory/README.md
├── memory/
│   ├── README.md              taxonomy: types + classification rule + home table (the agent-facing map)
│   │                          ← the ONE scaffold-managed (synced, byte-identical) file under memory/;
│   │                            everything else under memory/ is per-repo and never synced
│   ├── STATUS.md              BOOT: current state (≤3 recent changes, capped)
│   ├── questions/
│   │   ├── INDEX.md           BOOT(Active): blockers; Parked section = pointers to per-item files
│   │   └── <item>.md          per-item detail (on-demand)
│   ├── decisions/
│   │   └── INDEX.md           registry: one line/decision → change archive (or inline if no archive)
│   ├── lessons.md             process lessons (single file)
│   ├── reference/             durable not-in-code facts: runbook, external-API semantics, empirical findings,
│   │                          product strategy/vision, specs for unbuilt work
│   ├── research/
│   │   └── INDEX.md           hard-won synthesized investigation (indexed; full files alongside)
│   └── roadmap.md             long-term direction index
├── openspec/
│   ├── config.yaml            rules: (shared, synced — see D-C) + context: (per-repo)
│   ├── changes/ , changes/archive/ (sole history) , specs/
└── .claude/skills/_shared/delegation-harness.md   single shared procedure (RULES layer)
```

### D-C — config.yaml `rules:` sync via "rules-is-last-block" span replace
`openspec/config.yaml` joins the manifest as the second partial-sync file (with `AGENTS.md`). The sync replaces the top-level `rules:` block and preserves everything above it (`schema:`, per-repo `context:`). To make the span unambiguous, **`rules:` SHALL be the final top-level block** in `config.yaml` (a fixed-point invariant mirroring AGENTS.md's tail rule); the sync aborts with a clear error if a non-comment top-level key follows `rules:`. The span is `^rules:` → EOF. If the target has **no** `rules:` block at all (a fresh or pre-`rules:` repo), the sync **appends** scaffold's `rules:` block at EOF rather than aborting. `--check` compares only the `rules:` block. *Alternative rejected:* full-file byte-copy (clobbers per-repo `context:`); a separate non-manifest sync pass (loses pre-commit-guard coverage and `--check` integration).

### D-D — New archive reconciliation flow (kills the dual archive)
Both `archive-executor.md` bodies change their step-3 targets, and **both must stay byte-identical** (`test_executor_body_agreement.py`). The separate `parked-follow-ons.md` file is retired — parked items live in the Parked section / per-item files under `memory/questions/`. The rewritten step 3:
- **`memory/STATUS.md`**: keep the existing dense `## Latest change`/`## Prior change` format, the ≤3-section cap, and the ≤150-word headline bound, but **drop the prune-to-`status-log.md` step** — when the cap is exceeded the oldest section is simply removed (the full record already lives in `openspec/changes/archive/`). This is what retires the second archive.
- **`memory/decisions/INDEX.md`**: append exactly one registry line, in this machine-parseable format:
  ```
  - **YYYY-MM-DD** · <change-slug> · <one-line essence> → `openspec/changes/archive/<dated-change>/`
  ```
  For a decision with no change archive (pre-OpenSpec), use the inline form:
  ```
  - **YYYY-MM-DD** · <slug> · [inline] <short rationale>
  ```
  No `**Status:**` field (a registered decision is final; status mattered only while the change was active). This replaces the old ≤300-word Date+Status block — full rationale now lives in the pointed-to archive.
- **`memory/questions/INDEX.md`**: Active holds blockers only; non-blocking follow-ons become one-line pointers in the Parked section to `memory/questions/<item>.md`. Routing is as today; only the path and the death of `parked-follow-ons.md` differ.
- Re-run `status_lint.py` (D-E) until clean.

### D-E — status_lint.py updates
Repath to `memory/STATUS.md` and `memory/decisions/INDEX.md`. The STATUS checks (≤3 sections, ≤150 words) carry over unchanged. The decisions check is **rewritten** for the registry format (D-D): every line matching the anchor `^- \*\*YYYY-MM-DD\*\*` (a dash-list item with a bolded ISO date) SHALL be a valid registry entry of the form `- **YYYY-MM-DD** · <slug> · <text>`, where `<text>` is **either** `<one-line essence> → \`openspec/changes/archive/<dir>/\`` (the pointer must resolve to an existing directory) **or** `[inline] <short rationale>`. Lines that don't match the date-bullet anchor (section headers, prose, blanks) are excluded from the check. Violations: a date-anchored line that is malformed, or a pointer that does not resolve. No word-count, `**Date:**`-parse, or `**Status:**` checks remain, and the `--since` backfill flag is dropped (a registry entry is valid by format, not by date). `test_status_lint.py` is rewritten to these invariants: a resolving-pointer entry passes, a dangling-pointer entry fails, an `[inline]` entry passes, a malformed line fails.

### D-F — Decisions registry is a hybrid (pointer-or-inline)
The registry entry points into the archive by default; for decisions predating OpenSpec (or otherwise archiveless) it holds a short inline rationale. This is the one place the explore-phase analysis flagged the original "always points to archive" assumption would break (psc-monitor's pre-OpenSpec `remove-legacy-hash.md`). The migration of existing `decisions.md` files maps every current entry to a registry line; entries whose change is already archived get a pointer, the rest go inline. **No decision content is dropped.**

### D-G — Migration is atomic per repo; sync-orphans removed by hand
`sync_scaffold.py` is always invoked **from the scaffold checkout** (it resolves its own root via `__file__`), targeting each downstream path — never run from inside the target. Each downstream repo is migrated on its own branch in one coherent pass (no long-lived mixed old/new state — answers the explore-brief's interim-state question). Per-repo sequence:
1. **Selectively** move the per-repo **knowledge** files from `ai-docs/` into `memory/` — `decisions.md`→`decisions/INDEX.md`, `open-questions.md`+`parked-follow-ons.md`→`questions/` (each question/parked item becomes its own `memory/questions/<item>.md`, with `INDEX.md`'s Active section holding blocking-item pointers and its Parked section holding non-blocking pointers), `workflow-lessons.md`→`lessons.md`, plus any reference/research content. **Do NOT wholesale-rename `ai-docs/`**: the three scaffold-managed files (`delegation-harness.md`, `fast-track-workflow.md`, `research-fetch-convention.md`) are deliberately left at their `ai-docs/` paths here and removed in step 3 (a wholesale `git mv ai-docs/ memory/` would move them too and break step 3's `git rm`). Dissolve `plans/` (design→`openspec/changes/`, roadmap→`memory/roadmap.md`, research→`memory/research/`, strategy/vision→`memory/reference/`). **Enumerate `ai-docs/archive/`**, preserve substantive files (research, plans) into `memory/research/` or `reference/`, then `git rm -r ai-docs/archive/`. Rescue-then-delete `docs/` (D-H). Clean up `tmp_*.md`.
2. Run `sync_scaffold.py <repo>` (from scaffold) to receive the new mechanism: the relocated `.claude/skills/_shared/delegation-harness.md` arrives, `memory/README.md` arrives, and the manifest no longer carries fast-track/research-convention.
3. **`git rm` the sync-orphans** the copy-only sync left behind: `ai-docs/delegation-harness.md`, `ai-docs/fast-track-workflow.md`, `ai-docs/research-fetch-convention.md`. With step 1 done, `ai-docs/` is now empty → remove it.
4. Run `sync_scaffold.py --check <repo>`, `sync_scaffold.py --check-refs <repo>` (verifies every `memory/` citation in synced files resolves to an existing target — relies on the Phase 1 reference-checker update), and `status_lint.py <repo>` → all clean.

### D-H — psc-monitor docs/ rescue-before-delete (note 3)
extrends `docs/` (~2,191 lines, all code-derivable) is deleted outright. psc-monitor `docs/` is **not**: before deletion, rescue ~967 not-in-code lines into `memory/reference/` — `entity-resolution.md`, `strategy-and-market.md`, the two unbuilt specs (`anomaly-detection-spec`, `matcher-feedback-loop`), the Stripe webhook semantics, the B5 post-mortem lessons (→ `memory/lessons.md`), and `ai-docs/{ops-runbook,project-reference}.md` (→ `reference/`). psc-monitor's `plans/gdpr-research/` + `plans/backup-cost-research/` (~3,400 lines) move to `memory/research/`. A migration checklist enumerates each file's destination and is verified before any deletion.

### D-I — Taxonomy lives in three coordinated places, normative in the spec
- **Normative contract:** `openspec/specs/knowledge-organization/spec.md` (created by this change).
- **Agent-facing map:** `memory/README.md` — the type→home table + the one-line classification rule, in plain language. This is **scaffold-managed and synced byte-identical** to every repo (the one managed file under `memory/`, per the `scaffold-sync-mechanism` delta), so the taxonomy can't drift per-repo.
- **Boot pointer:** `AGENTS.md`'s "where everything lives" map links to `memory/README.md`. This satisfies the spec's "documented and discoverable from AGENTS.md" requirement. *Alternative rejected:* putting the full taxonomy in AGENTS.md (bloats the boot file we're trying to slim); leaving `README.md` per-repo (taxonomy drift — the reason it's synced).

### D-J — Research and strategy homes
Research gets its **own** `memory/research/` directory (not a subsection of `reference/`): the volume justifies it (psc-monitor ~3,400 + extrends strategy/research lines) and it is conceptually distinct (synthesized investigation vs. operational fact). Product **strategy/vision** lands in `memory/reference/` (durable not-in-code product context), with a one-paragraph identity summary + pointer in AGENTS.md `## Project context`.

## Risks / Trade-offs

- **Copy-only sync leaves orphans** → D-G step 3 makes `git rm` an explicit, checklisted step; `--check` after each migration confirms convergence.
- **Both executor bodies must stay byte-identical** → edit both, run `test_executor_body_agreement.py` in the same pass.
- **config.yaml span breaks if `rules:` isn't last** → enforce the rules-is-last invariant with an abort guard + a sync test.
- **Deleting psc-monitor docs/ could lose irreplaceable knowledge** → D-H rescue checklist verified before deletion; deletion is the last migration step, not the first.
- **AGENTS.md slimming could break span anchors** → preserve the three anchors verbatim; `sync_scaffold.py --check` validates reconstruction.
- **Decisions registry pointer rot** → the hybrid (D-F) + lint pointer-resolution check (D-E) catch dangling pointers.
- **Scaffold has little content to validate the structure against** → the structure was designed against extrends' real volume (per operator direction); the scaffold receives only the skeleton.

## Migration Plan

1. **Phase 1 — scaffold mechanism + template.** Create the `knowledge-organization` spec + `memory/` skeleton (incl. scaffold-managed `README.md`). `scaffold_manifest.txt`: add `memory/README.md`, relocate `delegation-harness.md` to `.claude/skills/_shared/`, drop `fast-track-workflow.md` + `research-fetch-convention.md`. Slim AGENTS.md (three span anchors preserved) and link it to `memory/README.md`. `openspec/config.yaml`: add `rules.research` (keep `rules:` as the last block), and **rewrite `rules.archive` and any other `rules:` text that cites `ai-docs/` or root `STATUS.md` to the new `memory/` paths** (else the new config sync spreads dead paths to every repo). `sync_scaffold.py`: add the config `rules:` span-sync + `--check`/append-if-absent handling, and update the reference-checker for the rename — `_AIDOC_PATH_RE`→`memory/`, the `_synced_files()` return filter, and the `cited_file.startswith("ai-docs/")` section-citation guard, plus drop the now-dead `ai-docs/archive/` and `docs/reviews/` entries from `_REF_SCAN_EXCLUDE`. `status_lint.py`: repath + rewrite the decisions check (D-E). Rewrite **both** archive-executor bodies (D-D), kept byte-identical. Update the `scaffold-sync-mechanism` spec text paths. All scaffold tests green — explicitly including `test_executor_body_agreement.py`, `test_status_lint.py`, and the new config-sync tests.
2. **Phase 2 — extrends migration** (D-G), `docs/` deleted outright.
3. **Phase 3 — psc-monitor migration** (D-G + D-H rescue).
4. **Phase 4 — convergence.** `sync_scaffold.py --check` + `status_lint.py` clean in both downstream repos; spot-check boot files answer one question each.

**Rollback:** each phase is a branch; scaffold changes are guarded by the test suite, downstream migrations by per-repo branches that can be reverted without touching scaffold.

## Verification (acceptance criteria)

- `openspec validate restructure-project-knowledge` passes; the `knowledge-organization` spec and `scaffold-sync-mechanism` delta are present.
- Scaffold: `pytest` green, including `test_status_lint.py`, `test_executor_body_agreement.py`, and sync tests covering the config `rules:` span (replace, context-preserved, idempotent, drift-detected, rules-not-last aborts).
- `sync_scaffold.py --check <extrends>` and `<psc-monitor>` exit 0 after migration; no stale orphan at any old managed path (`ai-docs/delegation-harness.md`, `fast-track-workflow.md`, `research-fetch-convention.md`); `ai-docs/` no longer exists.
- `sync_scaffold.py --check-refs <extrends>` and `<psc-monitor>` exit 0 — no dangling citations after the `ai-docs/`→`memory/` rewrite.
- `status_lint.py` exits 0 in all three repos against the new `memory/` paths.
- In both downstream repos: `ai-docs/`, `plans/`, `docs/`, and `tmp_*.md` are gone; `memory/` exists with the D-B layout; `memory/README.md` documents the taxonomy and is linked from AGENTS.md.
- **Knowledge-preservation check:** every entry in each old `decisions.md` and `open-questions.md` is represented in the new registries; the D-H rescue checklist is fully accounted for (every not-in-code file has a verified destination before its source directory is deleted).
- No second archive: no `ai-docs/archive/status-log.md` remains; `openspec/changes/archive/` is the only history.

## Open Questions

- **Growth-trigger is forward-looking, not built here.** The `knowledge-organization` spec's `growth-trigger-splits-file` requirement is a standing rule for the future; this change does NOT build an auto-splitter. The only enforcement shipped is the existing `status_lint.py` bounds (≤3 STATUS sections, ≤150 words). The implementer SHALL NOT build a splitting mechanism the tasks don't call for.
- **psc-monitor `docs/reviews/` executed/promoted artifacts** — the exploration found most were already promoted or executed (safe to delete); the rescue list (D-H) captures the unbuilt specs, the post-mortem lesson, and Stripe semantics. Final per-file dispositions are confirmed against the checklist during Phase 3, not guessed.
