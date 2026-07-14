# Notes — archive-mechanization (OW-12)

## Acceptance criteria
See design.md `## Verification`. Change-specific acceptance = every D4 truth-table row behaves per
spec, atomicity holds (any anomaly → zero writes, exit 2), `archive_move.py` conflict guard, all guards
green (`check.sh`, `scaffold_lint`, `test_executor_body_agreement.py`).

## Assumptions (non-blocking; recorded per AGENTS.md)
- A1 · Exit-code convention: `apply_delta_spec.py` & `archive_move.py` use `0`=success, `2`=anomaly/
  refusal. Kept exit 2 (not exit 3) despite the argparse-2 overlap; callers disambiguate an anomaly
  from a usage error by report presence (review-log Round 2 💡).
- A2 · Move mechanism: plain `shutil.move` (git stays out of the script; primary stages at commit) — D11.
- A3 · Parser grammar: own copy of the three `checks.py` regexes + a frozen agreement test, NOT a
  shared module (avoids churning the load-bearing detector) — D2.

## Apply-split (disclosed per HANDOFF lesson #1)
Group 4 (skill/executor prose rewiring — fence-heavy, byte-identical-executor-bodies) is
**orchestrator-authored** and checked off BEFORE delegating; the flash apply-executor implements
groups 1–3 (deterministic Python + tests + manifest) only.

## Verify results
<!-- filled at verify -->

## Candidate open-questions / follow-ons for archive
<!-- filled at verify -->
