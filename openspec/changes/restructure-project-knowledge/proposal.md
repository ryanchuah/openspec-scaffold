## Why

The project knowledge base is rotting. Knowledge is scattered across five directories named by five different logics — who wrote it (`ai-docs/`), what process made it (`openspec/`), who reads it (`docs/`), its time horizon (`plans/`), and its lifespan (`tmp_*.md`). Because the directory names don't share an organizing principle, neither a human nor an agent can tell where a new piece of knowledge belongs, or where to find an existing one, without first reading AGENTS.md end to end. On top of that, append-only files grow without bound (extrends' `decisions.md` is already 1,341 lines / 59 entries), the same shipped change is recorded in two parallel archives, and hand-written codebase docs silently drift out of date.

The point of fixing this is **not** token savings for their own sake. It's that today an agent spends its first chunk of every session just figuring out where things are and what's current — effort that should go to the actual task. We want a knowledge base that a human or an LLM can navigate by its shape alone, and that scales as the projects grow.

**Scope note (supersedes the explore-brief).** The original explore-brief listed "propagating the restructure to extrends or psc-monitor" as a *separate follow-on*. Per operator direction, that is now folded into this change: the deliverable is that **extrends (primary) and psc-monitor (secondary) end up on the new structure**, with the scaffold carrying the template skeleton and the shared mechanism. Where the explore-brief and this proposal disagree, this proposal wins.

## What Changes

The change has two halves: **(A) define the new structure once** (a universal contract that applies to every repo), and **(B) migrate the live repos into it**. Keeping these separate matters — the structure is the same everywhere; only the physical move differs per repo.

### A. Define the new structure (universal)

**A1 — One explicit knowledge taxonomy, written down.** Define the distinct *types* of knowledge, a single rule for classifying any piece, and exactly where each type lives, in a document future agents can read. The classifying rule: **store knowledge that cannot be recovered from the source code; do not store knowledge that merely duplicates the code — it rots.** The knowledge types and their homes:

| Type | Question it answers | Home | Load |
|---|---|---|---|
| State | Where are we right now? | `memory/STATUS.md` + `memory/questions/INDEX.md` (Active) | boot |
| Decisions | What did we choose, and why? | `memory/decisions/INDEX.md` (one line per decision → archive; rationale inline when no archive exists) | on-demand |
| Questions | What's open / parked? | `memory/questions/` (Active = boot; Parked + per-item files = on-demand) | split |
| Lessons | What did we learn about how to work? | `memory/lessons.md` (single file) | on-demand |
| Reference | Durable facts not in the code (runbook, external-API semantics, empirical findings) | `memory/reference/` | on-demand |
| Research | Hard-won synthesized investigation (e.g. GDPR, vendor pricing) | `memory/research/` *or* a `reference/` subsection — indexed either way (design.md picks the layout) | on-demand |
| Roadmap | Where are we headed long-term? | `memory/roadmap.md` | on-demand |
| History | What did we do? | `openspec/changes/archive/` (the *sole* archive) | search-only |
| Contracts | What must each subsystem guarantee? | `openspec/specs/` | on-demand |
| Rules | How do agents behave? | `.claude/skills/`, `openspec/config.yaml`, AGENTS standing rules | phase-entry |

(Exact directory layout — e.g. whether `research/` is its own directory or a section of `reference/`, and whether product strategy/vision lives in a `memory/` identity doc or in AGENTS' project-context — is finalized in design.md. The taxonomy and the classification rule are fixed here.)

**A2 — `ai-docs/` → `memory/`.** One home for all tracked project knowledge. **BREAKING** (path rename). `STATUS.md` moves from the repo root to `memory/STATUS.md` but **remains per-repo volatile state**: it stays excluded from scaffold sync (it is never propagated), and only its path — and `status_lint.py`'s reference to it — change.

**A3 — Append-only files become bounded.** `decisions.md` → `memory/decisions/INDEX.md` (registry → archive). `open-questions.md` + `parked-follow-ons.md` → `memory/questions/` (Active boots; Parked + per-item load on demand). These are **transformations, not deletions: every existing decision, question, and parked item is carried into the new structure — no content is dropped** (see Deletion flags for what genuinely goes away).

**A4 — Knowledge that isn't knowledge moves out.**
- `fast-track-workflow.md` is **removed**. The autonomy override becomes a spoken operator instruction with no tracked artifact; a one-line note in AGENTS records that this is by design, so agents don't recreate the file.
- `delegation-harness.md` moves out of the knowledge area into the rules layer as a **single shared file** (it's an operational procedure, not project memory — but it must stay single-source; four copies previously drifted).
- `research-fetch-convention.md` folds into `openspec/config.yaml` as a `rules.research` block; the standalone file is retired.

**A5 — Boot files each answer exactly one question.** `AGENTS.md` → "what is this project and where does everything live"; `memory/STATUS.md` → "where are we right now"; `memory/questions/INDEX.md` (Active) → "what's blocking us". Procedural rules that don't belong at boot move to the phase skills that already exist.

**A6 — One archive.** `openspec/changes/archive/` is the sole history; the parallel `ai-docs/archive/status-log.md` band-aid is retired.

### B. Update the mechanism and migrate the repos

**B1 — Make the rules block propagate.** Teach the sync tool to carry the `openspec/config.yaml` `rules:` block downstream (it can't today), so `rules.research` and future rule edits reach extrends and psc-monitor instead of drifting per-repo.

**B2 — Update the machinery for the new layout.** `status_lint.py` (new paths), `sync_scaffold.py` (config `rules:` partial sync + reference-checker that follows `ai-docs/`→`memory/` instead of hardcoding the old prefix), `scaffold_manifest.txt` (relocated/removed managed files), and both `archive-executor.md` bodies (reconcile into `memory/STATUS.md`, `memory/decisions/INDEX.md`, `memory/questions/`).

**B3 — Migrate the live repos into the structure.** extrends first (primary, real volume), then psc-monitor. This is where each repo's existing content physically moves: `ai-docs/`→`memory/`, the `decisions`/`questions` transformations, and **`plans/` is dissolved** (it exists only downstream) — pre-change design → `openspec/changes/<name>/`, roadmap → `memory/roadmap.md`, research → `memory/research/`, strategy/vision → project identity (AGENTS `## Project context` or a `memory/` identity doc — design.md decides). Because the sync tool only ever adds/overwrites and **never deletes**, every relocated or removed managed file leaves a stale copy downstream that is removed by hand (`git rm`) as an explicit migration step.

### Deletion flags (every removal of information, called out for sign-off)

- **extrends `docs/` (~2,191 lines): safe to delete, zero loss** — every file is an auto-generated description of the code.
- **psc-monitor `docs/` (~6,002 lines): NOT safe to bulk-delete** — ~967 lines exist nowhere else and are not in the code (empirical company-data findings, market/regulatory facts, two unbuilt feature specs, Stripe integration semantics incl. an apparently-unfixed billing bug). These are rescued into `memory/reference/` *before* the directory is removed.
- **psc-monitor research (`plans/gdpr-research/`, `plans/backup-cost-research/`, ~3,400 lines): preserved** in `memory/research/`, not deleted.
- **`ai-docs/archive/` (whole directory): retired** — `status-log.md` and `retired-notes.md` are discarded (superseded by the single openspec archive); any substantive content (e.g. `workflow-harmonization-plan-2026-06.md`, research files) is preserved into `memory/research/` or the openspec archive first. Per-repo contents differ; the migration enumerates each.
- **`fast-track-workflow.md`, `tmp_*.md`: deleted** — re-statable, or scratch.

## Capabilities

### New Capabilities
- `knowledge-organization`: The contract for how project knowledge is structured — the knowledge types, the single classification rule, the home for each type, the boot-vs-on-demand loading discipline, the requirement that **knowledge storage stays scalable (the boot-read load must not grow as the project accumulates history)**, and the requirement that the archive step reconciles current state into this structure. (The mechanism that satisfies the scalability requirement — registries, growth triggers — is design.md's job.)

### Modified Capabilities
- `scaffold-sync-mechanism`: Add partial propagation of the `openspec/config.yaml` `rules:` block (so `rules.research` and future rule edits reach downstream repos), and update the reference-checker so it follows the `ai-docs/`→`memory/` rename instead of hardcoding the old prefix.

## Impact

- **Three repos.** scaffold = template skeleton + shared mechanism; **extrends** = full content migration (primary); **psc-monitor** = full content migration with not-in-code rescue (secondary).
- **Scripts:** `scripts/status_lint.py`, `scripts/sync_scaffold.py`, `scripts/scaffold_manifest.txt`.
- **Agents:** both `archive-executor.md` bodies (`.claude/` + `.opencode/`).
- **Boot surface:** `AGENTS.md` in all three repos — slimmed, new "where everything lives" map; the span-sync anchors (`> **MANDATORY`, `## Roles`, `## After reading this file`) are preserved so propagation keeps working.
- **Config:** `openspec/config.yaml` gains `rules.research`; `rules.archive` and any other `ai-docs/` references update to `memory/`.
- **References to update for the rename:** `status_lint.py`, both `archive-executor.md` bodies, `sync_scaffold.py`, `openspec/config.yaml`, `AGENTS.md`, and any skill file citing `ai-docs/`. This includes the **`scaffold-sync-mechanism` spec text itself** — its `manifest-excludes-volatile-state` requirement hardcodes `STATUS.md` and several `ai-docs/` paths, which must move with the rename (update the spec, not just the code).
- **One reference that must NOT be rewritten to `memory/`:** `openspec/config.yaml`'s `context:` block currently points to `ai-docs/research-fetch-convention.md`; since that convention moves *into* config as `rules.research`, this pointer targets `rules.research`, not a `memory/` path.
- **Out of scope:** changing any OpenSpec CLI behavior; changing the change-tiering system; building a programmatic docs generator (only the decision to stop hand-maintaining codebase docs is in scope).
