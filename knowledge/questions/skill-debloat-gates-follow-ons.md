# skill-debloat-gates (OW-11) follow-ons

Parked, non-blocking items surfaced by `skill-debloat-gates` (archived
`openspec/changes/archive/2026-07-14-skill-debloat-gates/`). None of these gate other work.

1. **OW-11-residual** — the four DEFERRED de-bloat items from OW-11's original charter, independent
   of each other and of the mechanized-gates half already shipped:
   - #1 verify steps 12–16 de-bloat: the fuzzy "search codebase / assess if implementation likely
     exists" prose → a structural scan + coherence note. Needs a design call — `openspec status
     --json` only gives artifact-level done/blocked, not requirement-level, so mechanization is
     non-trivial. Highest risk of the eight original sub-items; that's why it was deferred rather
     than folded into this change.
   - #2 `notes_lint` — mechanize the 5-field `notes.md` verify-checkpoint ritual into a lint.
     Marginal value (the ritual was already being skipped in 2/3 recent MEDIUM changes before this
     one); pairs naturally with #1's verify-skill de-bloat, so defer together.
   - #3 freeze-check script — needs a companion prompt change (a new `FREEZE:` token) before it can
     be scripted. Defer until that token exists.
   - #8 explore gallery-prose trim — explicitly secondary per the 2026-07-11 workflow audit
     (`knowledge/research/workflow-audit-2026-07-11/AUDIT.md`, finding 5).

2. **`_validate_delta` two-pass → single-pass merge** — `scripts/checks.py`'s spec-delta-structure
   parser uses a two-pass boundary state machine (found duplicative by the verify-time simplicity
   gate). Behavior-preserving refactor; the efficiency reviewer judged the merge not worth it at
   this input scale (one repo's few open changes), and it was deferred deliberately to avoid
   churning code that had just been fixed for a real correctness defect (the multi-section
   `requirement-no-scenario` false-negative). Low priority — revisit only if the detector's runtime
   or the parser's complexity becomes a live concern.

3. **Factor a shared `_parse_harness_table` + token-scan helper** between the `budget-agreement` and
   `model-id-agreement` checks in `scripts/scaffold_lint.py`. Both checks parse a `§`-table out of
   `.claude/skills/_shared/delegation-harness.md` and scan the same `_scan_file_set()` population —
   currently intentional parallel copies. This also dedups reading the harness file twice per lint
   run. A third such table-driven check would justify the extraction; until then, low priority.

4. **`checks.py --check <name>` litters the CWD with `<name>.json`** — `out_dir` defaults to `.`, so
   any direct `--check` invocation (not just `spec-delta-structure`, which surfaced this during its
   own dogfood run) drops a disposable JSON file at the repo root that must be deleted by hand and
   must never be committed. Pre-existing wart affecting every detector, not introduced by this
   change. Consider defaulting `--check` output under `output/`, or gitignoring root `/*.json`. Low
   priority.
