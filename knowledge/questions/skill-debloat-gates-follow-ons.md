# skill-debloat-gates (OW-11) follow-ons

Parked, non-blocking items surfaced by `skill-debloat-gates` (archived
`openspec/changes/archive/2026-07-14-skill-debloat-gates/`). None of these gate other work.

**OW-11-residual — RESOLVED 2026-07-14.** All four DEFERRED de-bloat sub-items (verify steps 12–16
de-bloat, the notes-checkpoint lint, the freeze-check script, and the explore gallery-prose trim)
shipped in `skill-debloat-residual`; the checks.py `--check` cwd-litter item (formerly #4 below) also
shipped there (L5). See `knowledge/decisions/INDEX.md` and
`knowledge/questions/skill-debloat-residual-follow-ons.md` for that change's own follow-ons.

Remaining low-priority items (unrelated to OW-11-residual):

1. **`_validate_delta` two-pass → single-pass merge** — `scripts/checks.py`'s spec-delta-structure
   parser uses a two-pass boundary state machine (found duplicative by the verify-time simplicity
   gate). Behavior-preserving refactor; the efficiency reviewer judged the merge not worth it at
   this input scale (one repo's few open changes), and it was deferred deliberately to avoid
   churning code that had just been fixed for a real correctness defect (the multi-section
   `requirement-no-scenario` false-negative). Low priority — revisit only if the detector's runtime
   or the parser's complexity becomes a live concern.

2. **Factor a shared `_parse_harness_table` + token-scan helper** between the `budget-agreement` and
   `model-id-agreement` checks in `scripts/scaffold_lint.py`. Both checks parse a `§`-table out of
   `.claude/skills/_shared/delegation-harness.md` and scan the same `_scan_file_set()` population —
   currently intentional parallel copies. This also dedups reading the harness file twice per lint
   run. A third such table-driven check would justify the extraction; until then, low priority.
