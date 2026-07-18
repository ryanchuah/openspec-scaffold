# SAST tool JSON version sensitivity — monitored

Deferred follow-on from `graduate-sast-scanners` (shipped 2026-07-18).

## What
The `_parse_bandit` and `_parse_semgrep` parsers were validated against specific tool versions:
bandit 1.9.4 and semgrep 1.170.0. Both key on stable top-level JSON fields (`results[]`,
`test_id`/`check_id`, `filename`/`path`, `line_number`/`start.line`, `issue_text`/`extra.message`)
that are unlikely to change in minor/patch bumps.

## Risk
A future major version bump (bandit 2.x, semgrep 2.x) could change the JSON output shape. The
parsers use `.get()` with `or {}`/`or ""` fallbacks and `None`-tolerant `line` fields, so a
missing/renamed key produces a degraded finding rather than a crash — but could silently lose
information or produce empty findings on a format change.

## Mitigation
- Both tools are **version-recorded-not-gated** (absent from `EXPECTED_TOOL_VERSIONS`), so a version
  bump never INFRA-FAILs.
- The `test_checks.py` stubs exercise the exact key-paths; a breaking JSON change would be caught
  when a downstream repo enables the check with a real tool and sees empty/nonsensical findings.
- The real-tool smoke (verify checkpoint) confirmed both versions produce the expected shape.

## Monitored
No action needed now. If a downstream operator reports bandit/semgrep producing empty findings on a
new version, update the parser key-paths.
