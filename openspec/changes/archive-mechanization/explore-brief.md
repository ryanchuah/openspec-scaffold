# Explore brief — archive-mechanization (OW-12)

## Problem

The **archive phase is entirely LLM-driven**, including its purely mechanical parts. Today the
archive-executor (deepseek-v4-pro, Sonnet fallback) performs, all by hand:

1. the change-dir **move** to `openspec/changes/archive/YYYY-MM-DD-<name>/` (plain `mv` +
   `mkdir -p` + a conflict guard — 3 lines of LLM-executed shell), and
2. **delta-spec promotion** — reading each `specs/<cap>/spec.md` delta and "intelligently"
   editing the main spec to apply ADDED / MODIFIED / REMOVED / RENAMED requirement blocks
   (`openspec-sync-specs` skill).

Two of the four promotion operations — **ADDED, REMOVED, RENAMED** — are whole-block
operations keyed by requirement name: mechanical, deterministic, and **correctness-critical**
(a botched edit corrupts a canonical spec). Handing them to an LLM spends tokens on
deterministic work *and* puts the canonical specs at the mercy of a stochastic editor. This
violates the repo's own load-bearing rule — *"Default to scripts over LLM token-burn for
deterministic work — everywhere … Spend tokens on judgment, not on re-deriving by hand what a
script reproduces for free."* Evidence the risk is real: the **RENAMED promotion path has never
been exercised** repo-wide (OUTSTANDING-WORK.md finding 4) — the one archived RENAMED delta was
promoted by hand, unverified against any contract.

Only **MODIFIED** merges (partial scenario additions into an *existing* requirement — genuine
"intelligent merge") and the **doc-reconciliation narrative** (STATUS/decisions/questions) are
genuine judgment. Those stay LLM (unchanged). Everything else is mechanizable.

## Root cause

The scaffold never built the deterministic surface, so the executor prompt/skill was written to
do the whole job in prose. The `openspec-sync-specs` skill is explicitly "agent-driven … you
will read delta specs and directly edit main specs" for *all four* operation kinds, when three
of them are pure transforms with an existing, tested parser already in the repo
(`checks.py:_validate_delta`'s `_SECTION_HEADER_RE` / `_REQUIREMENT_HEADER_RE` /
`_SCENARIO_HEADER_RE`).

## Proposed direction

Add two stdlib-only, tested scripts and rewire the archive/sync-specs surface to call them,
leaving the LLM **only** the two operations that are genuine judgment:

```
                 ARCHIVE PHASE — before → after
  ┌─────────────────────────┬──────────────────────────────────────────┐
  │ operation               │ today          →   after OW-12            │
  ├─────────────────────────┼──────────────────────────────────────────┤
  │ dir move + conflict grd  │ LLM shell      →   scripts/archive_move.py│
  │ ADDED   promotion        │ LLM edit       →   apply_delta_spec.py    │
  │ REMOVED promotion        │ LLM edit (unex)→   apply_delta_spec.py    │
  │ RENAMED promotion        │ LLM edit (unex)→   apply_delta_spec.py    │
  │ MODIFIED merge           │ LLM edit       →   LLM edit  (unchanged)  │
  │ doc reconciliation       │ LLM            →   LLM       (unchanged)  │
  └─────────────────────────┴──────────────────────────────────────────┘
```

- **`scripts/archive_move.py`** — deterministic dir move: assert `changeRoot` exists, assert
  `archivePath` does **not** exist (conflict → exit nonzero, touch nothing), `mkdir -p` the
  archive parent, move the dir. Single tested entry point replacing hand-run shell.

- **`scripts/apply_delta_spec.py`** — deterministic promoter for **ADDED / REMOVED / RENAMED**
  only. Discovers a change's `specs/<cap>/spec.md` deltas, parses requirement blocks with the
  existing grammar, and:
  - **ADDED** → append the requirement block under the main spec's plain `## Requirements`
    (creating the main spec + `## Purpose`/`## Requirements` skeleton if the capability is new).
  - **REMOVED** → delete the named requirement block from the main spec.
  - **RENAMED** → rewrite the `### Requirement:` header line (FROM→TO), body untouched.
  - **MODIFIED** → **not applied**; emitted in a machine-readable report as *deferred to the LLM*
    (name + delta location), because partial-scenario merge into an existing requirement is the
    one operation that needs judgment.
  - **Anomaly = halt-and-report, never corrupt.** ADDED-name-already-present-with-different-body,
    REMOVED-name-absent, RENAMED-FROM-absent / TO-already-present → report all anomalies, **write
    nothing**, exit nonzero. The applier plans fully in memory and only commits writes when the
    deterministic plan is clean (all-or-nothing across the change's specs).
  - Emits a report (applied ADDED/REMOVED/RENAMED, deferred MODIFIED, anomalies) the
    archive-executor consumes to know exactly what MODIFIED work remains.

- **Rewire the surface** so the deterministic scripts are the path and the LLM does only
  MODIFIED + reconciliation: `openspec-archive-change` Step 5 executor prompt, both
  `archive-executor.md` bodies (byte-identical — `test_executor_body_agreement.py` guards this),
  and `openspec-sync-specs` (deterministic for ADD/REM/REN, LLM for MODIFIED).

- **New capability spec** (ADDED requirements) pinning the applier contract: the four operation
  semantics, the anomaly-halts-and-writes-nothing invariant, MODIFIED-deferral, main-spec
  creation shape, and the move conflict guard. This is where correctness is specified.

## Scope

**In:** the two scripts + their test files (with orchestrator-authored adversarial fixtures for
the parser/transform); manifest entries; the archive/sync-specs skill + executor-body rewiring;
one new capability spec (ADDED). Mechanizes RENAMED for the first time under a tested contract.

**Out (explicitly):** MODIFIED-merge automation (stays LLM — genuine judgment); doc
reconciliation (stays LLM-on-pro); OW-11 residual skill de-bloat (separate concern per HANDOFF
lesson #4); any change to the delta *format* or the `spec-delta-structure` linter; downstream
propagation (operator-gated, deferred).

## Key design questions to settle at propose/design

1. **Atomicity granularity** — all-or-nothing across the whole change's specs (lean yes) vs
   per-file. Anomaly handling must never leave a half-promoted spec.
2. **ADDED-already-present** — no-op if byte-identical block vs anomaly if body differs (lean:
   identical→no-op for idempotency, differ→anomaly).
3. **REMOVED-absent** — idempotent skip vs anomaly (lean: anomaly, matches "stop on first
   failure"; but idempotent re-runs argue for skip-with-note — settle in design).
4. **Move mechanism** — plain filesystem move (matches today; primary stages at commit) vs
   `git mv`. Lean plain move, keep git out of the script.
5. **Capability spec name + granularity** — one capability covering both scripts
   (`archive-mechanization` / `spec-delta-promotion`) vs two. Lean one.
6. **Report channel** — JSON to stdout vs a written report file the executor reads. Lean stdout
   JSON (executor/skill captures it), matching the repo's script-output-to-disk convention where
   a durable artifact helps.

## Tier

**COMPLEX.** It introduces a parser/transform that mutates *canonical specs* — decision-heavy and
correctness-critical — so it warrants proposal + design + tasks with a design.md that pins the
applier contract, plus the full multi-model verify with orchestrator-authored adversarial
fixtures. (Backlog estimated SMALL–MEDIUM; the spec-mutation correctness stakes justify the
heavier process.)

## Evidence / grounding
- Backlog: `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` OW-12 + finding 4.
- Prior-art parser: `scripts/checks.py:1173-1313` (`_validate_delta`).
- Current surface: `.claude/skills/openspec-sync-specs/SKILL.md`,
  `.claude/skills/openspec-archive-change/SKILL.md` Step 5, both `archive-executor.md` bodies.
- Real delta formats: `openspec/changes/archive/2026-07-13-outstanding-and-continuity-hardening/specs/knowledge-lint/spec.md`
  (RENAMED+MODIFIED), `.../2026-06-16-verify-multimodel-gate/specs/verify-multimodel-gate/spec.md` (ADDED).
