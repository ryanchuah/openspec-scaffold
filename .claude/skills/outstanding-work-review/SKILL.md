---
name: outstanding-work-review
description: Surface all outstanding work — snapshot open items and newly surfaced findings, guide triage judgment. Operator-invoked, pull-only.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.4.1"
---

Surface all outstanding work on demand — a complete snapshot of tracked open
items and newly surfaced findings, followed by orchestrator judgment. The
snapshot is **regenerate-on-use** (never stale) and combines structured
extraction (questions, tasks, roadmap entries) with point-only enumeration
(per-item question files, plans).

**Pull-only.** This skill is never wired into session boot or `AGENTS.md`.
Invoke it explicitly when you need to triage outstanding work.

**Interpreter convention.** Use `<py>` below as a placeholder for the repo's
Python interpreter. Resolve it in this try-order:
1. A repo task-runner `audit-*` target, if one exists (e.g. `just audit-floor`);
2. `.venv/bin/python` if the virtual environment exists;
3. `python3` if available;
4. `python` otherwise.

**Steps**

1. **Gather.** Generate the outstanding-work snapshot:
   ```bash
   <py> scripts/facts.py --check outstanding
   ```
   This writes two files (both regenerated each run):
   - `output/facts/outstanding.md` — human/LLM-oriented prose snapshot.
   - `output/facts/outstanding.json` — structured payload for programmatic
     consumption.

2. **Read.** Load the snapshot. The JSON carries bucketed data:
   - **Open work (triaged)** — items already referenced into `knowledge/questions/`.
   - **Newly surfaced — untriaged (N; oldest <date>)** — findings IDs that
     appear in `FINDINGS*` files but are **not yet** cross-referenced into
     `knowledge/questions/`.
   - **Active config** (`findings_globs`, `finding_id_pattern`) + scan counts.

   Read `output/facts/outstanding.json` for the structured view and
   `output/facts/outstanding.md` for the prose orientation.

3. **Judge (orchestrator).** Apply human/LLM judgment:
    - **Residual sweep.** The deterministic gather (`facts.py --check
      outstanding`) enumerates point-level items from questions, plans, and
      FINDINGS* files. It does NOT read prose *bodies* — the detailed context
      inside `plans/*.md` and `knowledge/questions/*.md` (open each and
      classify as consumed / live / orphaned), in-code `TODO`/`FIXME` (a
      deliberate no-op in `outstanding.py`), or stray research docs. Convert
      the occasional human/LLM sweep of these residual sources into a
      documented, repeatable step here — do not change what the deterministic
      collector enumerates.
    - **Triage the untriaged bucket.** For each newly surfaced finding, decide:
      promote it into `knowledge/questions/INDEX.md` (or a per-item question
      file) if it represents real work to track; otherwise note why it was
      dismissed (refuted, duplicate, not actionable).
    - **Prioritize open work.** Review the triaged bucket: which items are
      stale, blocked, or need attention? Update `knowledge/roadmap.md` with
      any priority shifts.
    - **Record durable decisions.** Write triage outcomes into
      `knowledge/questions/INDEX.md` (and per-item files as needed) and
      priority/status changes into `knowledge/roadmap.md`.

    Durable reconciliation of `knowledge/questions/INDEX.md`,
    `knowledge/decisions/INDEX.md`, and `knowledge/roadmap.md` **normally
    happens at archive** (by the archive-executor). The judge step here is
    the *content* pass — what work to track and at what priority — not the
    structural reconciliation. Archive will reify the structural changes.

4. **Verify.** After judging, re-run the snapshot to confirm buckets reflect
   your triage:
   ```bash
   <py> scripts/facts.py --check outstanding
   ```

**Staleness cadence.** Run this skill periodically — there is no automated
trigger. The `knowledge_lint` drift check (`_check_untriaged_age`) provides a
safety-net CI signal when untriaged findings accumulate past the configured
window (default 14 days), but the skill itself is explicitly pull-only.

**Guardrails**
- This skill is **read-only with respect to repo state** until step 3, when
  the orchestrator writes triage outcomes into `knowledge/questions/` and
  `knowledge/roadmap.md` — standard tracked-file edits that the operator
  reviews before commit.
- Do **not** edit `scripts/outstanding.py`, `scripts/checks.py`, `facts.py`,
  or the `knowledge_lint` drift checks from this skill.
- Do **not** wire this skill into session boot, AGENTS.md, or any auto-run
  hook.
