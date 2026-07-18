# notes.md — detect-truncated-stream

## Decisions

- **Signal = count-based (`step_start > step_finish`), keyed on top-level `type`.** Confirmed
  against the real incident file `/tmp/archive-out.jsonl` (still on disk this session): top-level
  `type` is underscore (`step_start`/`step_finish`); nested `part.type` is hyphen. Count-based is
  order-independent and robust to trailing metadata; the incident (`17 > 16`, final event a bare
  `step_start`) satisfies both the count and last-event signals.
- **Precedence: after `crash`, before `marker-missing`.** `timeout` (124/137) and `crash` (no text)
  keep their unambiguous labels; `truncated-stream` outranks `marker-missing` because it explains
  *why* output is incomplete. No failure-ladder change: any non-`ok` status already exits 1.
- **No ledger schema change.** `status` carries `"truncated-stream"`; the 12-core-key ledger
  contract is test-pinned and left intact. `truncated` is surfaced only in the result-JSON.

## Declined / considered

- **Fix direction #2 (required marker on archive invocation):** DECLINED — #1 catches archive
  truncation regardless of markers, so #2 adds no detection value and would widen the scaffold
  surface (skill + harness edits + propagation) for no gain.
- **Fix direction #3 (upstream opencode empty-stream handling):** out of this repo's control —
  parked as a monitoring/reporting follow-on in `knowledge/questions/`.

## Follow-ons to record at archive

- Park #3 (upstream opencode empty-completion-as-success; consider issue report / version pin) in
  `knowledge/questions/`.
- After ship: fold-and-delete the source diagnosis file
  `../extrends/plans/deepseek-stream-truncation-diagnosis-2026-07-18.md` (cross-repo, operator-
  gated — flag to operator; do not delete a sibling-repo file autonomously).

## Assumptions (non-blocking, recorded default)

- A1: The two script files are scaffold-managed (confirmed in `scaffold_manifest.txt`); downstream
  propagation of this change is a separate operator-gated step, NOT part of this change.
