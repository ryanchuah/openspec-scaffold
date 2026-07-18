# SMALL plan — detect-truncated-stream

**Tier:** SMALL. **Change dir:** `plans/detect-truncated-stream/`.
**Source diagnosis:** `../extrends/plans/deepseek-stream-truncation-diagnosis-2026-07-18.md`
(fix direction #1 — the "best/cheapest" deterministic detector). Fold-and-delete that file at close.

## Problem statement

A delegated `opencode run` (deepseek) can terminate early with **exit 0, empty stderr, no fallback
warning**, and a stdout JSONL that just stops mid-conversation — the provider stream returned an
empty completion and opencode treated no-assistant-output as a clean end-of-stream and exited 0.
`scripts/opencode_delegate.py` then classifies the run `ok` (or `marker-missing` only if a
`--require-marker` happens to be set). On marker-less phases (archive; some apply/premise calls)
the truncation is **invisible** — the wrapper reports success, the failure ladder never fires, and
the orchestrator trusts a half-finished run.

**Ground-truth evidence** (incident file `/tmp/archive-out.jsonl`, dissected this session):
- Top-level `type` field uses underscore: `step_start`, `step_finish`, `tool_use`, `text`.
  (Nested `part.type` uses hyphen: `step-start`/`step-finish` — a second representation of the
  same event; the detector keys the top-level `type`, consistent with `extract_text`.)
- Incident counts: `step_start: 17`, `step_finish: 16` → **one unbalanced open step**; the final
  event is a bare `step_start`. Every healthy completed stream sampled has **balanced** counts
  (e.g. a clean apply run showed 63 `step_start` / 63 `step_finish`).

So a healthy run balances `step_start`/`step_finish`; a silently-truncated run leaves a
`step_start` with no matching `step_finish` (`step_start count > step_finish count`).

## Proposed approach (fix direction #1 — deterministic detector)

1. **New pure helper** `detect_truncated_stream(out_jsonl_text: str) -> bool` in
   `scripts/opencode_delegate.py`: count top-level `type == "step_start"` vs `type == "step_finish"`
   across parseable JSONL lines; return `starts > finishes`. Tolerate blank / non-JSON / non-dict
   lines (skip them), like the other helpers. Returns `False` when counts balance, when there are
   no step events at all, or on any parse degradation.
   - **Count-based, not last-event-based:** order-independent and robust to trailing metadata; the
     diagnosis endorses it and the incident satisfies it (`17 > 16`).
2. **Extend `classify_status`** with a new trailing keyword param `truncated: bool = False`
   (default keeps every existing positional call and test passing). Insert the new status in
   precedence **after** `crash`, **before** `marker-missing`:
   1. `fallback` → `"fallback"`
   2. `exit_code in (124, 137)` → `"timeout"`  (explicit budget kill wins — an unambiguous signal)
   3. `not text` → `"crash"`  (no output at all — existing empty-run label)
   4. `truncated` → `"truncated-stream"`  ← NEW (there IS partial text but a step never closed)
   5. `not marker_ok` → `"marker-missing"`
   6. otherwise → `"ok"`
   Rationale for placement: `truncated-stream` is strictly more informative than `marker-missing`
   (it says *why* the run is incomplete), so it wins over it; but a real 124/137 budget kill and a
   zero-output crash keep their unambiguous labels. Any non-`ok` status already exits 1 and routes
   to the existing failure ladder — no ladder change needed.
3. **Wire into `main()`**: compute `truncated = detect_truncated_stream(out_text)`, pass to
   `classify_status(...)`, and add `"truncated": truncated` to the result-JSON dict (observability
   for marker-less operators). Do **not** add a core ledger key — the `status` field already
   carries `"truncated-stream"`, and the ledger's 12-core-key contract is test-pinned.
4. **Docstrings**: update the module docstring status list (`ok|fallback|timeout|crash|marker-missing`
   → add `truncated-stream`) and the `classify_status` precedence docstring.
5. **Tests** (`scripts/test_opencode_delegate.py`) — the frozen regression the diagnosis asks for:
   - `TestDetectTruncatedStream`: balanced→False; `starts>finishes`→True; no step events→False;
     empty string→False; blank/non-JSON tolerated; more finishes than starts→False (defensive);
     an incident-shaped fixture (2 `step_start`, 1 `step_finish`, text present, final line a bare
     `step_start`)→True.
   - `TestClassifyStatus` additions: truncated+text+marker_ok→`truncated-stream`;
     truncated wins over `marker-missing`; `fallback`/`timeout`/`crash` each win over truncated
     (precedence); default param (`truncated` omitted) still yields `ok`.
   - `TestMainPipeline.test_truncated_stream_status`: end-to-end fixture (unbalanced steps + text +
     a satisfied marker) → `result["status"] == "truncated-stream"`, `rc == 1`.
6. **Enumeration truthfulness (orchestrator, quick doc edits)**: add `truncated-stream` to the
   status enumerations in `openspec/specs/delegation-wrapper/spec.md`,
   `.claude/skills/_shared/delegation-harness.md` (§b), and the illustrative ladder lists in
   `openspec-apply-change`, `openspec-propose`, `openspec-explore` SKILL.md. (verify SKILL uses
   general "operational crash" language — no enumeration edit needed.)

## Out of scope (declined / follow-on)

- **Fix direction #2 (required marker on the archive invocation)** — declined: #1 already catches
  archive truncation regardless of markers, so #2 adds no detection value; recorded in `notes.md`.
- **Fix direction #3 (upstream opencode empty-stream handling / issue report / upgrade)** — outside
  this repo's control; a monitoring/reporting follow-on, parked in `knowledge/questions/`.
- The pre-existing, distinct `extract_text` last-part-only defect
  (`knowledge/questions/opencode-delegate-extract-text-last-part-only.md`) — separate bug, untouched.
- No change to the failure ladder, budgets, invocation hardening, or the ledger schema.
