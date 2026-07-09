## Why

Outstanding work piles up across the downstream repos with no trustworthy single view: incidental
bugs found mid-complex-work, and Fable audit findings (which never go through an archive), get "noted
somewhere" and are then lost or duplicated. The current workaround — hand-running LLM subagents to
regenerate a `tmp/outstanding-work.md` — is **error-prone** (a subagent can silently skip a source)
and **stale** (proven in-repo: five stacked in-place `UPDATE` banners in one day; and a prior
hand-built view, `go-live-readiness.md`, rotted into one of three verbatim copies of a to-do list).
Root cause: **mechanical "gathering" and judgment-heavy "prioritizing" are fused into one
hand-authored file**, so the result inherits the untrustworthiness of hand-gathering *and* the
staleness of frozen judgment.

## What Changes

- **New deterministic "gather".** A regenerate-on-use fact (`scripts/facts.py` family) enumerates
  **every** open-work source — `knowledge/questions/` (Active + Parked + per-item files), unchecked
  `- [ ]` items in non-archive `openspec/changes/*/tasks.md`, `plans/`, `knowledge/roadmap.md`
  non-closed entries, and audit `FINDINGS*` files (in-code `TODO/FIXME/HACK/XXX` markers are
  lowest-priority — near-zero in these repos by deliberate discipline — and may be omitted from the
  initial cut without weakening the completeness promise for the prose sources) — into one
  complete, provenance-tagged (`source:line`) snapshot under `output/facts/`. It **owns no data**
  (points at sources), makes **no priority judgment**, and, like every fact, **regenerates on use so
  it can never be stale**. Its guarantee is completeness of the source set, **within the fact
  family's graceful-degradation bounds** (malformed-source handling is resolved in `design.md`) — not
  clever prose parsing.
- **Fable findings become first-class the moment written.** The gather scans a designated findings
  location and surfaces those findings in a **distinct "newly surfaced — untriaged" bucket**,
  separate from triaged open work — so raw, ungraduated leads are visible immediately without being
  mistaken for confirmed backlog.
- **New on-demand skill** (`outstanding-work-review`; agent-neutral, in `.claude/skills/`,
  auto-loaded by both Claude and OpenCode, **zero boot-context cost**) that runs the gather and then
  drives the LLM judging.
  Invocation is **pull-only** — never at session boot, never an AGENTS.md procedure, never a
  Claude-only hook.
- **Judgment stays where it already lives** — `knowledge/questions/INDEX.md` + `knowledge/roadmap.md`,
  reconciled at archive by the existing archive-executor. **No new tracked backlog document is
  introduced** (the already-tried tracked view rotted).
- **Extended deterministic drift-detection** in `scripts/knowledge_lint.py`: duplicate-block
  detection (catches verbatim list copies) and closed-but-unpruned roadmap/`plans/` entries — riding
  CI as the automatic rot safety-net so nothing silently rots even when the skill is not run.
- **A minimal `plans/` live-vs-archived convention** so the gather can distinguish open plans from
  permanent shipped-change citation-anchors.
- **All scaffold-managed** — propagates to `extrends` and `psc-monitor` via `sync_scaffold.py`
  (centralize the *mechanism*, not a document).

## Capabilities

### New Capabilities
- `outstanding-work-view`: a deterministic, complete, on-demand snapshot of all outstanding work
  (with `source:line` provenance and a separate untriaged-findings bucket), plus the agent-neutral,
  pull-only `outstanding-work-review` skill that produces it and drives the LLM judging; includes the
  minimal `plans/` live-vs-archived convention the gather depends on.

### Modified Capabilities
- `knowledge-lint`: add two deterministic drift detections to the linter — **duplicate content-block
  across tracked docs**, and **closed-but-unpruned entries** in `knowledge/roadmap.md` and `plans/`.

## Impact

- **New code:** a `facts.py` fact entry + its gather logic; a new `.claude/skills/<name>/SKILL.md`;
  extensions to `scripts/knowledge_lint.py`; a `plans/` convention (likely a `plans/archive/` subdir).
- **Scaffold surface:** any new scaffold-managed file is added to `scripts/scaffold_manifest.txt` and
  propagates to `extrends` + `psc-monitor`; the new fact is registered in `scripts/checks.py`'s
  shared `_REGISTRY` (the checks/facts registry), while `checks.toml` only overrides
  `enabled`/per-repo settings for registered entries.
- **Agent-neutral:** plain stdlib scripts + a skill loaded by both harnesses; **no harness-private
  state**; pull-only, so no boot-context tax.
- **Out of scope (tracked separately):** per-repo one-time hygiene — designating each repo's Fable
  findings scan-path, applying the `plans/` convention to existing files, and cleaning existing
  duplicate-list / stale-note debt.
- **Design inputs to resolve in `design.md`** (carried from the premise review + this proposal
  review):
  - quantify-the-prose-gap sampling of `extrends` + `psc-monitor` (may reshape how much extraction
    the gather does) — **opens the design phase**;
  - the pull-only accumulation-visibility tension (is "the untriaged pile is itself a signal" enough);
  - the concrete Fable findings location + machine-readable finding handle;
  - fact-family "never-fails" vs. the completeness guarantee on malformed input (skip-and-flag vs.
    fail) — and the snapshot output format (markdown page vs. JSON sibling for the judging LLM);
  - the **mechanically-detectable "closed" convention** the linter must pattern-match before
    closed-but-unpruned detection is possible (roadmap `~~strikethrough~~` / a `plans/` status marker);
  - the **duplicate-block comparison scope** (which doc set is compared — narrowed to where
    duplication is actually harmful, not all of `knowledge/`/`AGENTS.md`);
  - the **per-repo configuration surface** for the gather (which `checks.toml` keys, their defaults,
    and behavior when a repo is unconfigured).
