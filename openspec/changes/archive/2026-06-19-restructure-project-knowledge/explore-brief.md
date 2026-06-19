# Explore Brief: Restructure Project Knowledge

## User Goal

Reorganize how project knowledge is maintained across scaffold, extrends, and psc-monitor to eliminate directory sprawl, confusing naming, dual archives, and unbounded file growth — while preserving execution quality and the load-bearing OpenSpec infrastructure.

## Current Problems

### 1. Directory sprawl with no organizing principle
Five directories serving overlapping purposes, each named by a different logic:

| Directory | Named by | What it contains |
|---|---|---|
| `ai-docs/` | Who wrote it (AI) | Decisions, questions, follow-ons, lessons, roadmap, operational docs |
| `openspec/` | What process (OpenSpec) | Active changes, archived changes, subsystem specs |
| `docs/` | Audience (humans) | Human-oriented documentation, no longer maintained |
| `plans/` | Horizon (long-term) | Pre-change design docs, roadmap |
| `tmp_*.md` | Duration (temporary) | Spike artifacts, brain dumps, never cleaned up |

A human or agent cannot look at the directory structure and understand where to find anything without first reading AGENTS.md.

### 2. Dual archives
`ai-docs/archive/status-log.md` and `openspec/changes/archive/` both serve as historical record. The same shipped change spawns entries in both. One is a STATUS cap-rule band-aid; the other is the natural OpenSpec lifecycle artifact.

### 3. Confusing file placement
- `STATUS.md` is at root but `open-questions.md` is in `ai-docs/` — both are boot-reads about current state, filed by different rules.
- `delegation-harness.md` and `fast-track-workflow.md` are operational docs, not project memory, but live in `ai-docs/`.
- Extrends has 13 `plans/` files and a `roadmap.md` — answering the same question through two different mechanisms.

### 4. Boot context overhead
Every session reads ~634 lines (AGENTS.md + STATUS.md + open-questions.md) plus scans 56 decision headers. Much of AGENTS.md is procedural rules duplicated in skill files. Much of open-questions.md is deferred items that should not be loaded at boot.

### 5. Unbounded file growth
Append-only files (decisions.md at 1,322 lines, 56 entries; questions.md at 182 entries) grow with every change. "Scan headers" works at 56 entries but breaks at 200. No index or search mechanism.

## Key Decisions Made

### D1: Organize by what knowledge IS, not what process created it
Three categories: **STATE** (where are we now?), **MEMORY** (what have we learned?), **HISTORY** (what did we do?). Plus **RULES** (how do agents behave?) which lives in harness-required paths.

### D2: `ai-docs/` → `memory/`
Rename to a purpose-oriented name. One directory for all tracked project knowledge. `STATUS.md` moves from root into `memory/`.

### D3: Boot files answer exactly one question each
- `AGENTS.md` → "What is this project and where is everything?" (~50 lines)
- `memory/STATUS.md` → "Where are we right now?" (~30 lines)
- `memory/questions/INDEX.md` § Active → "What's blocking us?" (~10 lines)

Procedural rules move to phase-specific skill files, loaded on phase entry, not at boot.

### D4: Registry-not-repository for scalable knowledge
Files that grow unbounded become directories with an INDEX.md:
- `memory/decisions/INDEX.md` — one line per decision, pointer to the change archive that holds full rationale
- `memory/questions/INDEX.md` — § Active (blockers) + § Parked (deferred), each pointing to an individual `.md` file in the same directory
- `memory/lessons/INDEX.md` — same pattern

The archive (`openspec/changes/archive/`) is the permanent record. memory/ files are registries that help agents *find* the right entry. Full content is only loaded when relevant.

### D5: `plans/` dies; pre-change design lives in openspec
A design doc means a change has conceptually begun. It lives in `openspec/changes/<name>/`. Roadmap is `memory/roadmap.md` — a single index with pointers.

### D6: `docs/` deleted
No longer maintained. Not archived.

### D7: `fast-track-workflow.md` removed
Operator says "go" = agent is autonomous. No document needed.

### D8: `delegation-harness.md` inlined into skills
Operational infra, not project memory. Canonical copy lives in the apply skill (first consumer); other skills cite it.

### D9: `research-fetch-convention.md` inlined into `openspec/config.yaml`
Added as `rules.research` block. Original file archived.

## Proposed Structure

```
Root
├── AGENTS.md                    (~50 lines, BOOT)
│   • Project identity (1 paragraph)
│   • Map: where everything lives
│   • Standing rules (one-liners pointing to full detail)

├── memory/                      ← All tracked project knowledge
│   ├── STATUS.md                (~30 lines, BOOT)
│   │   Current state, last 3 changes, immediate next action
│   │
│   ├── decisions/               (on-demand, registry)
│   │   └── INDEX.md             One line per decision → change archive
│   │
│   ├── questions/               (BOOT § Active only)
│   │   ├── INDEX.md             § Active (blockers, operator decisions)
│   │   │                       § Parked (deferred follow-ons → .md files)
│   │   ├── <item>.md            Full detail per active/parked item
│   │   └── ...
│   │
│   ├── lessons/                 (on-demand, registry)
│   │   ├── INDEX.md             Process lessons, rationale for rules
│   │   └── <lesson>.md
│   │
│   └── roadmap.md               (on-demand)
│       Long-term improvement direction index

├── openspec/                    (load-bearing, can't rename)
│   ├── config.yaml
│   │   schema, context block, rules (tasks, verify, archive, research)
│   ├── changes/                 STATE: active work
│   ├── changes/archive/         HISTORY: sole archive
│   └── specs/                   MEMORY: subsystem contracts

├── .claude/skills/openspec-*/   RULES: phase procedures (loaded on entry)
├── .claude/agents/              Harness-required
└── .opencode/agents/            Harness-required
```

## What Dies

| Current path | Disposition |
|---|---|
| `ai-docs/` | Renamed to `memory/`, internals restructured |
| `ai-docs/archive/` | Redundant with `openspec/changes/archive/` — contents either discarded (status-log.md, retired-notes.md) or archived into openspec archive (research files) |
| `ai-docs/delegation-harness.md` | Inlined into skills, original archived |
| `ai-docs/fast-track-workflow.md` | Removed, original archived |
| `ai-docs/parked-follow-ons.md` | Merged into `memory/questions/INDEX.md` § Parked |
| `ai-docs/open-questions.md` | Split into `memory/questions/INDEX.md` + individual `.md` files |
| `ai-docs/decisions.md` | Split into `memory/decisions/INDEX.md` (registry) — full rationale stays in change archives |
| `docs/` | Deleted |
| `plans/` | Contents moved to `openspec/changes/<name>/` or `memory/roadmap.md` |
| `tmp_*.md` | Archived or deleted |
| `STATUS.md` (root) | Moved to `memory/STATUS.md` |

## Constraints

- `openspec/` cannot be renamed — it's a load-bearing path for the OpenSpec CLI
- `.claude/skills/` is discovered by both Claude and OpenCode harnesses — can't move
- `.claude/agents/` and `.opencode/agents/` must remain in dual copies (model formats differ)
- The redesign propagates to extrends and psc-monitor via `sync_scaffold.py`
- Archive operations (reconciliation of STATUS, decisions, questions) must be updated in both archive-executor bodies (`.claude/agents/archive-executor.md` and `.opencode/agents/archive-executor.md`)
- Any path references in skill files, AGENTS.md, and `openspec/config.yaml` rules must be updated

## Open Questions

1. **Does `lessons/` earn its directory?** Or should process lessons just be entries in `decisions/INDEX.md`? They're also "things we decided/determined."

2. **What's the archive-executor's new reconciliation flow?** Currently it reconciles `STATUS.md`, `ai-docs/decisions.md`, and `ai-docs/open-questions.md`. After the restructure it reconciles `memory/STATUS.md`, `memory/decisions/INDEX.md`, and `memory/questions/INDEX.md` + individual files. This needs a detailed design.

3. **How do we handle the interim state?** While the restructure is in progress, agents opening the repo see a mix of old and new paths. Do we add compatibility pointers, do it atomically in one commit, or something else?

4. **Does `sync_scaffold.py` need changes?** It currently propagates managed files to downstream repos. If paths change, the sync script must be updated to reflect new paths.

5. **Does `scripts/status_lint.py` need updating?** It currently validates bounds on `STATUS.md` and `ai-docs/decisions.md`. Paths will change.

## Scope

### In Scope
- Restructure scaffold's directory layout
- Create INDEX.md registries for decisions and questions
- Slim AGENTS.md to ~50 lines, move procedural rules to skills
- Inline delegation-harness into apply skill
- Add `rules.research` to openspec/config.yaml
- Update archive-executor bodies for new reconciliation flow
- Update `sync_scaffold.py` for new paths
- Update `scripts/status_lint.py` for new paths
- Clean up tmp_*.md files
- Delete docs/

### Out of Scope
- Propagating the restructure to extrends or psc-monitor (separate follow-on change)
- Changing any OpenSpec CLI behavior
- Changing the change tiering system
