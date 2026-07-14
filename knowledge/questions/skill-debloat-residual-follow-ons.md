# skill-debloat-residual (OW-11 residual) follow-ons

Parked, non-blocking items surfaced by `skill-debloat-residual` (archived
`openspec/changes/archive/2026-07-14-skill-debloat-residual/`). None of these gate other work; this
change closed the entire wave-2 scaffold-hardening backlog.

1. **Reviewer `VERDICT:`-token compliance (monitor).** `freeze_check.py` matches a whole-line-anchored
   `VERDICT: PASS|NEEDS REVISION` and fails closed (→ `missing-verdict` → re-run) if the reviewer
   decorates the line with trailing prose or backticks. The reviewer contract forbids decoration, but
   this change's own propose flow used the pre-token reviewer, so the token path is not yet exercised
   end-to-end in a real freeze. Watch that downstream reviewers emit the bare token; if they habitually
   decorate it, consider a more lenient parse.

2. **Uppercase `[X]` checkbox edge.** The `notes-checkpoint-structure` detector's checkbox regexes
   match lowercase `[x]`/`[ ]` only; an uppercase `[X]` is invisible (treated as a non-checkbox, so the
   change may be seen as "no checkboxes" and skipped). Standard OpenSpec/markdown usage is lowercase,
   so this is a monitored edge, not a live bug.

3. **`--floor` still writes to cwd.** L5 fixed only `checks.py --check <name>`'s cwd-litter; `--floor`
   was deliberately out of scope. Candidate follow-on if `--floor` litter becomes a concern.

4. **notes-checkpoint field-5 completeness stays a human judgment by design** — a detector cannot know
   an open-question was omitted from the forward-looking field. The verify skill's step 18 keeps the
   field-5 enumeration as the forcing function; this is accepted design, not a gap to close.

5. **premise-review-gate overrule scenario is prose-only** (workflow, not script-testable); its
   behavior lives in the propose skill edit and is verified by reading, not by a fixture.
