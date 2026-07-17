---
name: outstanding-work-deep-sweep
description: Deep residual-sweep of outstanding work; operator-invoked, pull-only.
license: MIT
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.4.1"
---

Deep residual-sweep of outstanding work — a scaffold-owned, repeatable procedure for the
full-repo prose crawl the deterministic collector (`scripts/outstanding.py`) structurally
cannot perform (it is point-only/heading-only by design). Mirrors this repo's own
deterministic-detector-vs-deep-LLM-audit separation (`checks.py`/`facts.py` vs
`correctness-audit`): the sibling `outstanding-work-scan` skill is the cheap, always-safe
"what's open right now?" check; this skill is the heavier, periodic body-sweep that layers
on top of it.

**Operator-invoked / pull-only.** Never wired into session boot, `AGENTS.md`, any
mandatory-read set, or any auto-run hook. Invoke on demand — e.g. before a launch/deploy
gate, before a large archive batch, or on a fixed cadence the operator sets.

**Interpreter convention.** Use `<py>` below as a placeholder for the repo's Python
interpreter. Resolve it in this try-order:
1. A repo task-runner `audit-*` target, if one exists (e.g. `just audit-floor`);
2. `.venv/bin/python` if the virtual environment exists;
3. `python3` if available;
4. `python` otherwise.

## Procedure

### Step 1 — run the deterministic scan first

Invoke the `outstanding-work-scan` skill (its gather + read + verify + untriaged-bucket
dedup-by-parent-ID judgment) and consume its snapshot
(`output/facts/outstanding.json` / `.md`) before starting any residual sweep. Do not
duplicate or replace that gather here.

### Step 2 — five-category residual sweep, as parallel subagents

The deterministic collector enumerates point-level items only (filename + first heading,
or heading text) — it never reads prose *bodies*. Run each category below as its own
subagent, checkpointing findings to disk as it goes (so the sweep survives interruption).
Every category cross-references `knowledge/questions/INDEX.md` and `knowledge/roadmap.md`
first, so already-tracked work is not re-reported.

1. **In-code markers.** Grep tracked source dirs (exclude generated/vendored/test-fixture
   data) for TODO/FIXME/HACK/XXX/NotImplementedError/"not implemented"/"for now"/
   "temporary"/"workaround" (and a broadened pass for "not yet"/"stub"/"placeholder"/
   "unimplemented"/"deferred"/"kludge"/"shortcut"). Judge each hit: genuine deferred-work
   marker vs. stylistic/explanatory comment or test-double vocabulary (mock/stub naming).
   Report only genuine candidates — this category is usually clean; don't force findings.

2. **Questions/decisions/lessons body sweep.** Read every `knowledge/questions/*.md`
   (excluding `INDEX.md`) in full, plus `knowledge/decisions/INDEX.md`,
   `knowledge/lessons.md`, and `knowledge/ratchet-log.md` (or repo-equivalent).
   Cross-reference against `INDEX.md`'s own Active/Parked one-line pointers: flag content
   that (a) isn't reflected as a pointer at all, or (b) contradicts/supersedes what the
   pointer currently says (staleness, not just omission).

3. **Plans body sweep.** Read every `plans/**/*.md` (excluding `plans/archive/`) in full,
   prioritizing files shaped like findings/ledgers (multiple individually-numbered items,
   a findings register, an attack list, evidence docs) — those are most likely to hide
   individually-trackable work behind one aggregate pointer. Cross-reference against
   `knowledge/questions/INDEX.md` and `knowledge/roadmap.md`.

4. **Reference/compliance/roadmap-body sweep.** Grep `knowledge/reference/*.md` and any
   repo-specific regulatory/compliance dir for TBD/"not yet built"/"not drafted"/
   "PROVISIONAL"/"pending" markers; read `knowledge/roadmap.md` in full (not just
   headings — the collector only ever surfaces `## ` heading text). For any "not yet
   built" claim, spot-check it against the actual codebase — if the feature now exists,
   that's a **doc-drift finding** (a different defect class from an uncaptured task) and
   should be reported separately.

5. **Change-dir prose + specs + untriaged-dedup sweep.** For each non-archived
   `openspec/changes/<name>/`, read `proposal.md`/`design.md`/`notes.md` (not just
   `tasks.md`) for open questions/deferred items with no corresponding checkbox. Skim
   `openspec/specs/*/spec.md` for TBD markers. For the untriaged-findings bucket
   specifically: **before promoting an ID, check the parent-ID disposition** — an ID may
   be a child evidence-citation nested *inside* a different, already-dispositioned parent
   finding (scheduled, refuted, or closed) rather than a free-standing finding. This is a
   known false-positive shape whenever `finding_id_pattern` is permissive, and alone
   accounted for 51 of 52 "untriaged" hits in the source calibration run — check parent
   disposition before promoting the child.

### Step 3 — triage into trackers

Promote genuinely uncaptured items into `knowledge/questions/INDEX.md` (or per-item
files) / `knowledge/roadmap.md`; record why dismissed items were dismissed (refuted,
duplicate, already-tracked, not actionable) rather than silently dropping them. This is
the full body-triage the renamed `outstanding-work-scan` skill deliberately no longer
performs (its own step 3 is narrowed to the untriaged-bucket dedup only). Durable
structural reconciliation of the trackers still normally happens at archive (by the
archive-executor) — this triage is the *content* pass: what to track, at what priority,
not the structural reconciliation.

## Guardrails

- **Operator-invoked / pull-only.** NEVER wired into session boot, `AGENTS.md`, any
  mandatory-read set, or any auto-run hook.
- **Read-only with respect to repo state** until Step 3, when the orchestrator writes
  triage outcomes into `knowledge/questions/` and `knowledge/roadmap.md` — standard
  tracked-file edits the operator reviews before commit.
- Do **not** edit `scripts/outstanding.py`, `scripts/checks.py`, `scripts/facts.py`, or
  the `knowledge_lint` drift checks from this skill — the point is documenting the
  human/LLM judgment step, not automating the collector.
- Category 1 (in-code markers) is expected to usually report nothing — do not force
  findings to justify the sweep.
