# Explore brief — outstanding-work collector

**Slug:** `outstanding-work-collector`
**Stance:** direction-level brief for the premise (direction) gate. Not a proposal, not a tier decision.
**Repos in scope:** openspec-scaffold (golden source) → propagates to extrends, psc-monitor.

---

## Problem

As work happens in the downstream repos, outstanding work piles up with **no single, trustworthy
place to see all of it**. Two recurring situations create the pile-up:

1. **Incidental bugs found mid-complex-work.** A low-priority defect surfaces while the agent is
   deep in an unrelated change. Context-switching to fix it is undesirable, so it gets "noted
   somewhere for later" — but there is no obvious, guaranteed intake, so it lands in whichever of
   several surfaces is nearest, or in a code comment, or nowhere durable.
2. **Audit findings that are highlighted, not fixed.** Fable (a top-tier LLM) audits a repo to
   surface future work/issues rather than fix them immediately. This produces many findings with
   **no OpenSpec change and no archive event** attached.

The operator has been working around this by hand: running Sonnet subagents to regenerate a
`tmp/outstanding-work.md` in each repo. That process is **manual and error-prone** — the explicit
worry is *"what if the subagent misses something?"* — and the resulting file goes stale.

## Root cause

"What outstanding work exists?" is really **two jobs fused into one hand-authored artifact**:

- **Gathering** — visit every place work is noted and pull together everything open. Mechanical;
  the only failure mode is *skipping a source*. This is the "what if it misses something" fear.
- **Judging** — decide priority, dependencies, and who (Fable/Opus/operator) does each. Valuable,
  judgment-heavy; this is the actual content of the current `tmp/outstanding-work.md` files.

Doing both by hand at once yields the worst of each: **gathering can silently skip a source
(untrustworthy)** and **judging is frozen at authoring time (goes stale)**. Every restatement of an
item that already lives elsewhere is a **hand-synced duplicate** — the duplication-and-drift engine.

## Evidence (from the actual repos)

- **The workaround already exists and already rots.** `extrends/tmp/outstanding-work.md` carries
  **five stacked `UPDATE` banners from a ~24h window**, each patched in place despite its own header
  saying "regenerate, don't edit in place." `psc-monitor/tmp/outstanding-work.md` pins "State is
  current as of commit `084778b`" — stale the next commit. One even records a subagent error caught
  by luck ("Dropped: a subagent claimed … does not reproduce").
- **A hand-authored central view was already tried — and drifted.** psc-monitor built
  `knowledge/reference/go-live-readiness.md` (a cross-dimension view *with a provenance column*). It
  rotted into being **one of three verbatim copies** of the compliance to-do list
  (`compliance/README.md`, `questions/INDEX.md`, `go-live-readiness.md`). Empirical proof, in these
  repos, that a tracked hand-authored central doc drifts.
- **Concrete staleness:** extrends' `checks.toml` still says data-lint is disabled "blocked on
  upstream SQLite backend" — but the scaffold just shipped that backend (commit `e604990`).
- **`plans/` is a swamp:** ~60 files in extrends, ~23 in psc, no pruning, no convention separating
  live plans from permanent shipped-change citation-anchors from dead research docs. Both repos
  independently flagged this exact gap.
- **Deferred work lives in prose, not code:** near-zero genuine in-code `TODO/FIXME` markers in
  either repo — a deliberate discipline. Work sits in `questions/*.md`, `plans/*`, and audit
  `FINDINGS*.md`.
- **Audit findings never archive:** psc-monitor's audit findings are 4,000+ lines that never went
  through any change lifecycle. An archive-triggered mechanism would never see them.

## Proposed direction

**Split the two jobs. Let a mechanism do the gathering; keep judgment where judgment already lives.
Centralize the mechanism, not a document.**

### 1. Gather — a deterministic, regenerate-on-use snapshot (no authored state)
A scaffold-managed script (a new `facts.py` fact, matching the existing "regenerate-on-use, never
fails, output under `output/facts/`" pattern) that, on demand, enumerates **every open-work-bearing
source** and prints one complete snapshot with per-item provenance (`source:line`):
- `knowledge/questions/INDEX.md` (Active + Parked) and every `knowledge/questions/*.md`;
- unchecked `- [ ]` items in non-archive `openspec/changes/*/tasks.md`;
- `plans/**` (respecting the live-vs-archived convention below);
- `knowledge/roadmap.md` entries (flagging closed-but-unpruned);
- audit `FINDINGS*.md` (see Fable section);
- in-code `TODO/FIXME/HACK/XXX` (minor here, but free).

It **owns no data** — it points at sources, so there is nothing to drift. Because it regenerates on
every run, it is never stale. It makes **no priority judgment** — it only guarantees completeness.

### 2. Judge — stays LLM, stays where it already is
The judgment layer (priority, dependency chains, Fable/Opus/operator assignment) remains an
orchestrator (Claude or OpenCode/Fable) reading the complete snapshot. Its **durable home is the
existing `knowledge/questions/INDEX.md` + `knowledge/roadmap.md`, reconciled at archive by the
archive-executor** — i.e. the "central doc updated at archive" already exists; we do not add a new
tracked backlog file. Mid-cycle re-planning produces a disposable view (regenerated from the
snapshot, never patched in place); anything in it worth keeping is demoted into a source
(`questions/`), preserving one-canonical-home.

### 3. Detect rot — automatic, no LLM, no context
Structural invariants (orphan/dangling pointers, duplicated blocks, closed-but-unpruned roadmap/
plans entries, lapsed audit-log) run as deterministic checks in CI / the audit floor. **Half of this
already exists**: `scripts/knowledge_lint.py` already flags orphan/duplicate canonical files, broken
citations, and dangling pointers. New detection is modest (duplicate-block, unpruned-closed, the
`plans/` convention). This is the safety net: rot is caught mechanically even if nobody runs the
gather.

## Runtime / trigger model (agent-agnostic)

Both gather and judge are **pull, never push** — invoked when planning/triaging, **never at session
boot** (that would tax boot context, which the scaffold deliberately minimises).

- **Not a session-start hook** — Claude-only (violates the agent-agnostic rule), fires every session
  wastefully, and can't do the judging half.
- **Not a procedure in AGENTS.md** — permanent per-session boot-context tax. At most a one-line
  pointer.
- **A skill** (in `.claude/skills/`, on demand) — the right home. This does **not** violate the
  agent-agnostic rule: `.claude/skills/` is the explicit carve-out — version-controlled and
  auto-discovered by **both** Claude and OpenCode, loaded on demand (**zero boot cost**). Exactly how
  `run-audit` and `knowledge-drift-review` already work: an operator-invoked skill that runs
  deterministic scripts and then does LLM work on top. The skill runs the gather, then guides the
  judging.
- **Drift-checks** ride CI automatically; **durable judgment** reconciles at archive via the
  existing archive-executor. Forgetting to invoke the skill therefore never lets work silently rot.

Every component is agent-neutral: plain script in `scripts/`, skill file loaded by both harnesses,
judging done by whatever orchestrator is running. No harness-private state.

## Fable findings as first-class (operator requirement)

Audit findings must count as outstanding the **moment Fable writes them**, not after triage:
- Fable writes findings to a **predictable scanned location** with a recognizable handle (they
  already carry IDs like `CA-W2-19` + a one-line title); the gather includes that path.
- The snapshot shows them in a **distinct "newly surfaced — untriaged" bucket**, separate from
  triaged open work — so immediate visibility does **not** imply "confirmed backlog." (Raw leads are
  often refuted on graduation; conflating them would poison trust in the list.)
- **Triage (verify → keep/drop) is the visible bridge** from the untriaged bucket into `questions/`.
  A growing untriaged pile is itself a signal.

## The prose-item gap — resolved (design rationale)

Because deferred work here lives in prose, the gather deliberately does **not** try to parse
prose item-state. Its value is precisely three things, and this is what it is worth building for:
1. **Completeness of the source set** — guarantees every open-work file is enumerated; nothing
   skipped. (Directly answers "what if it misses something.")
2. **Structured-skeleton extraction where structure exists** — INDEX bullets/pointers, `tasks.md`
   checkboxes, `FINDINGS` IDs+titles, roadmap headings + closed-markers extract cleanly.
3. **The untriaged-findings guarantee** — nothing Fable writes is ever silently lost.
For prose-heavy sources it lists the file/section as "read this," rather than faking item extraction.
The judging LLM then reads a **known-complete, deduplicated** set. Net: the *anti-rot* value is
largely free (extend `knowledge_lint`), and the new build (gather fact + skill + untriaged bucket) is
modest.

## Alternatives considered (and why not)

- **A new tracked central backlog doc updated at archive.** Natural fit with the write-deferred-at-
  archive discipline, and tracked/visible to all agents — but (a) **audits never archive**, so it
  would never capture Fable's findings; (b) it drifts **between** archives; (c) it is **still a
  hand-synced duplicate** of `questions/`/`plans/`/`FINDINGS` — the duplication engine; (d) already
  tried as `go-live-readiness.md` and it rotted. Its one unique strength (holds judgment) is already
  provided by `questions/INDEX.md` + `roadmap.md`, which *are* reconciled at archive.
- **Cross-repo centralized document.** Fights the deliberate per-repo knowledge model (`STATUS`/
  `questions` are never synced) and would be invisible in the repo you're actually working in.
  Resolved by centralizing the **mechanism** (scaffold-managed script + skill propagate) rather than
  a document; an orchestrator can run the gather across repos on demand for a unified view.

## Scope

**In scope (direction):** the gather mechanism (regenerate-on-use snapshot with provenance + an
untriaged-findings bucket); the invoke path as an on-demand skill; extending the deterministic
drift-checks; the `plans/` live-vs-archived convention that the gather depends on; keeping durable
judgment in `questions/`/`roadmap` reconciled at archive. All scaffold-managed so it propagates.

**Out of scope:** any new tracked cross-repo or per-repo backlog *document*; automatic session-boot
execution; replacing the LLM judging with a script; a heavyweight ticketing system; retroactively
cleaning existing `plans/`/duplicate-list debt (that is one-time downstream hygiene, tracked
separately).

## Open questions for propose

- Exact snapshot output format (markdown page vs JSON sibling for the judging LLM to consume).
- The precise scanned path/pattern + minimal finding convention for Fable's audit findings.
- Whether the new drift-detections (duplicate-block, unpruned-closed) live in `knowledge_lint.py` or
  a sibling detector, and which fail the build vs. warn.
- The `plans/` convention's concrete shape (`plans/archive/` subdir vs. a status marker).
- Tier (likely MEDIUM; decided at propose, not here).
