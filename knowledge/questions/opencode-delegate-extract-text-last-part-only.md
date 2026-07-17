# opencode_delegate.py extract_text returns only the last text part

Parked from `openspec/changes/archive/2026-07-17-handoff-lint-exempt/notes.md` (field-5
"Forward-looking items"). Non-blocking, generalizable harness defect, out of scope for that change.

## The finding

`scripts/opencode_delegate.py`'s `extract_text` returns only the **last** `type:"text"` part of a
delegate's response. A delegate that emits its verdict block (e.g. `## Verify Pass` /
`VERDICT: READY`) and then appends a trailing summary line yields a false `status=marker-missing` —
and the verify skill's failure ladder treats `marker-missing` as an operational crash, escalating to
a Sonnet re-run that was not actually needed.

This fired live during `handoff-lint-exempt`'s verify: the re-run `deepseek/deepseek-v4-pro`
behavioral pass emitted a full `VERDICT: READY` block, then appended a one-line summary, and the
wrapper reported `marker-missing`. The **first** pro pass in that same session extracted fine because
its verdict block *happened* to land last — so the failure is intermittent and model-behavior
dependent, which makes it worse: it spuriously escalates otherwise-good passes.

## Candidate fix

Scan all `type:"text"` parts (or their concatenation) for the required marker(s) rather than only the
last part.

## Priority

Low/monitored — harness robustness, not correctness of any shipped feature. Revisit if
`marker-missing` false-escalations are observed again, or the next time `opencode_delegate.py` is
touched.
