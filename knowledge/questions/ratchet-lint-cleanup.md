# ratchet-lint-cleanup (code-quality follow-on, low priority)

**Source:** `openspec/changes/archive/2026-07-13-lesson-check-ratchet/notes.md` (verify
checkpoint, field 5c) — surfaced by 3-4 simplicity-gate cleanup agents during verify and
deliberately parked rather than fixed inline, to avoid deviating from the frozen design or
regressing message-asserting tests mid-verify.

**Behavior-preserving, non-blocking.** All four items are internal code-quality cleanups
in the ratchet-lint implementation; none changes observable behavior if fixed correctly.

1. **`_validate_date` re-implements calendar validity twice.** In `knowledge_lint.py`,
   `_validate_date` uses `_ISO_DATE_RE` + `calendar.monthrange` to validate, and the
   waiver/`open` branches re-parse the same date string in an unreachable try/except. This
   collapses to a single `datetime.date.fromisoformat()` call that returns the date object
   directly. **Caveat:** the frozen design deliberately chose the explicit-message form (see
   design.md D1/D2), so this needs design-aware review plus updates to any tests that assert
   on the specific error message — not a blind swap.
2. **Unreachable slug re-check.** The slug re-check inside `_check_ratchet_log`
   (`scripts/knowledge_lint.py` around line 625) is unreachable: `_RATCHET_LOG_FULL_RE` /
   `_RATCHET_DISP_RE` already enforce the kebab-slug shape upstream, and a bad slug is caught
   as "malformed" first.
3. **Duplicate regex pair.** `_RATCHET_LOG_FULL_RE` duplicates `_RATCHET_DISP_RE`, leaving a
   dead `if not m: continue` guard behind it.
4. **Derivable `any_fail`.** In `scripts/repo_lint.py`, the `any_fail` flag is derivable from
   the post-loop `failing` list rather than tracked separately.

**Disposition suggestion (not pre-decided — leave to whoever picks this up):** a `check:` or
`test:` disposition once cleaned up, or fold into the next `knowledge_lint.py`-touching change
as incidental cleanup. Low priority; revisit opportunistically.
