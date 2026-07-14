# Premise review — archive-mechanization (direction gate)

Reviewer: `openspec-reviewer` @ `deepseek/deepseek-v4-pro` · via `opencode run` · wrapper status=ok, no fallback.

## Premise Verdict

**PREMISE: AGREE**

Problem real (archive burns pro-tier LLM tokens on deterministic dir-move + whole-block spec
promotion, violating the repo's "scripts over LLM token-burn" rule); root cause correct (scaffold
never built the deterministic surface); solution targets it (mechanize ADDED/REMOVED/RENAMED + move,
keep MODIFIED + reconciliation as LLM judgment); scope well-defined. Zero 🔴.

## Carry-forward into design.md (reviewer 🟡/💡 — all design-level, not direction-level)

1. **[🟡] RENAMED has a DIFFERENT format** — `- FROM: \`### Requirement: Old\`` / `- TO: \`### Requirement: New\``
   list items, NOT `### Requirement:` blocks. The existing `_validate_delta` grammar does **not**
   parse RENAMED — the applier needs a **separate RENAMED parser path** (list-item + backtick-quoted
   header extraction). Do not imply the existing parser handles all three uniformly.
2. **[🟡] ADDED-already-exists is a behavior CHANGE** — current `openspec-sync-specs` (SKILL line 61)
   treats ADDED-exists as implicit MODIFIED (silent overwrite). The new deterministic contract
   (identical→no-op, differ→**anomaly/halt**, never silent overwrite) is an intentional, safer
   departure. design.md must flag it as a deliberate contract change, not a mere preference.
3. **[🟡] Dual-invocation surface** — two callers with different discovery:
   - archive-executor → invokes on the already-moved change at `<archivePath>/`;
   - standalone `openspec-sync-specs` → discovers via `openspec status --change <name> --json`
     (`artifactPaths.specs.existingOutputPaths`).
   `apply_delta_spec.py` must accept a change-root (or explicit delta paths) so BOTH entry points
   work; design.md addresses both.
4. **[💡] Preserve the sync skill's `openspec` CLI discovery** (SKILL Steps 1–3); call
   `apply_delta_spec.py` as a subprocess for the deterministic portion only — do not redesign the
   discovery flow.
5. **[💡] New-capability path** — ADDED-only delta against a not-yet-existing main spec creates the
   `## Purpose` (TBD) + `## Requirements` skeleton. All 19 existing main specs share this shape
   (grep-confirmed) — skeleton is unambiguous. List it as an explicit design point.
