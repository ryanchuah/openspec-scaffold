# opencode treats empty provider completion as clean exit-0 end-of-stream

Parked from `plans/archive/detect-truncated-stream/`. Out of this repo's control — upstream defect.
Non-blocking; monitored.

## The finding

When the model provider returns an empty completion (e.g. a dropped or truncated stream),
`opencode run` treats no-assistant-output as a clean end-of-stream and exits 0 with no errors on
stderr. The output JSONL just stops mid-conversation with unbalanced `step_start`/`step_finish`
counts — the last event is a bare `step_start` with no matching `step_finish`.

The `detect_truncated_stream()` helper in `scripts/opencode_delegate.py` now catches this signature
at the wrapper level, so the failure ladder fires on exit code 1. But the root cause is upstream in
opencode itself — it should NOT treat an empty completion as a clean exit-0.

## Candidate follow-ons

- File an upstream issue report against opencode recommending that an empty provider completion
  should NOT be treated as a clean end-of-stream (at minimum a non-zero exit or a `step_finish`
  for every `step_start`).
- Version-pin the known-safe opencode version once fixed, so a downstream repo can gate on it.

## Priority

Low/monitored — the wrapper-level detector now provides defense-in-depth. Revisit when opencode
releases a fix.
