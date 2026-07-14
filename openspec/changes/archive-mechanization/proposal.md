## Why

The archive phase is **entirely LLM-driven**, including its purely mechanical parts: the
archive-executor (deepseek-v4-pro, Sonnet fallback) hand-runs the change-dir move (shell `mv` +
`mkdir` + conflict guard) and "intelligently" edits canonical specs to promote every
ADDED / MODIFIED / REMOVED / RENAMED requirement block. Three of those four promotion operations
are whole-block transforms keyed by requirement name — mechanical, deterministic, and
**correctness-critical** (a botched edit corrupts a canonical spec). Handing them to a stochastic
editor spends tokens on deterministic work *and* puts the specs at the mercy of that editor,
violating the repo's load-bearing rule: *"Default to scripts over LLM token-burn for deterministic
work — everywhere."* The risk is not hypothetical — the **RENAMED promotion path has never been
exercised** repo-wide (`OUTSTANDING-WORK.md` finding 4); the one archived RENAMED delta was
promoted by hand against no tested contract. This is OW-12, the last item on the scaffold-hardening
backlog. Only **MODIFIED** merges (partial-scenario merge into an *existing* requirement) and the
**doc-reconciliation narrative** are genuine judgment; those stay LLM.

## What Changes

- Add **`scripts/apply_delta_spec.py`** — a stdlib-only deterministic promoter for
  **ADDED / REMOVED / RENAMED** requirement blocks. It discovers a change's `specs/<cap>/spec.md`
  deltas, plans all operations in memory against the main specs, and writes **all-or-nothing**:
  any anomaly (e.g. ADDED clashes with a different existing body, RENAMED target ambiguous) →
  report every anomaly, **write nothing**, exit nonzero. (Two operation-semantics questions —
  REMOVED-target-absent = idempotent-skip vs anomaly, and the applier-vs-move ordering — are
  named here and **settled in design.md**, not left implicit.) **MODIFIED** blocks are never applied —
  they are emitted in a machine-readable report as *deferred to the LLM*. Emits a JSON report the
  caller consumes to know exactly what MODIFIED work remains. Supports `--dry-run` (plan + report,
  no writes) so the archive skill's pre-prompt sync assessment is deterministic too.
- Add **`scripts/archive_move.py`** — a stdlib-only deterministic change-dir move: assert source
  exists, assert destination does **not** (conflict → exit nonzero, touch nothing), create the
  archive parent, move. Single tested entry point replacing hand-run shell.
- Add test suites **`scripts/test_apply_delta_spec.py`** + **`scripts/test_archive_move.py`**
  (parser/transform + move-guard coverage; orchestrator authors adversarial fixtures at verify).
- **Rewire the archive surface** so the deterministic scripts are the path and the LLM does only
  MODIFIED + reconciliation: `openspec-archive-change` SKILL Step 5 and both `archive-executor.md`
  bodies (both rewritten; must **remain** byte-identical — enforced by
  `test_executor_body_agreement.py`).
- **Rewire `openspec-sync-specs`** so its `openspec` CLI change-discovery is preserved but
  ADDED/REMOVED/RENAMED promotion calls `apply_delta_spec.py`; the skill's LLM path handles only
  MODIFIED merges. **BREAKING (intentional contract change):** the current skill (Step 4c, lines
  60–61: *"if requirement already exists → update it to match (treat as implicit MODIFIED)"*)
  silently overwrites an ADDED whose name already exists. That prose is replaced — an ADDED
  name-collision is now a no-op when byte-identical and a halting **anomaly** when the body
  differs. Never a silent overwrite.
- Register the four new scripts in `scripts/scaffold_manifest.txt` (scaffold-managed; propagate
  downstream when the operator gates it).

## Capabilities

### New Capabilities
- `archive-mechanization`: deterministic archive-phase mechanics, reserving LLM judgment for
  MODIFIED merges and doc reconciliation. Covers:
  - the change-dir move with its conflict guard;
  - ADDED/REMOVED/RENAMED spec-delta promotion **operation semantics** (per-op truth table);
  - the **anomaly-halts-and-writes-nothing** atomicity invariant;
  - **MODIFIED-deferral** (emitted for the LLM, never applied deterministically);
  - **new-main-spec creation** for an ADDED-only delta on a not-yet-existing capability;
  - the **dual-invocation** surface (archive-executor + standalone `openspec-sync-specs`).

### Modified Capabilities
<!-- None. The archive/sync surface is skill+executor prose, not a specced capability today;
     this change introduces the capability spec rather than modifying an existing one. -->

## Impact

- **New code:** `scripts/apply_delta_spec.py`, `scripts/archive_move.py`, and their test files
  (all stdlib-only, no new runtime deps).
- **Rewired (scaffold-managed):** `.claude/skills/openspec-archive-change/SKILL.md`,
  `.claude/skills/openspec-sync-specs/SKILL.md`, `.claude/agents/archive-executor.md`,
  `.opencode/agents/archive-executor.md`, `scripts/scaffold_manifest.txt`.
- **Behavior change:** ADDED-name-collision is no longer a silent overwrite (see above) — the one
  intentional break, a strict safety improvement.
- **Unchanged:** MODIFIED-merge and doc reconciliation remain LLM-on-pro; the delta *format* and
  the `spec-delta-structure` linter are untouched; no downstream propagation in this change
  (operator-gated, deferred).
- **Guards to satisfy:** `check.sh` (ruff + format + pytest); `scaffold_lint`
  (manifest-completeness, dangling-skill-refs, model-id-agreement, budget-agreement);
  `test_executor_body_agreement.py`.
