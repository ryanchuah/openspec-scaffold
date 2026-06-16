# Tasks: canary-non-convergence

## Task List

- [ ] T1: Make `test_canary` pass
  - Description: Implement whatever is needed so that `python -m pytest docs/test/canary-non-convergence/test_canary.py -q` exits zero.
  - Files affected: `docs/test/canary-non-convergence/test_canary.py`
  - Acceptance: `pytest` on the fixture exits 0.
  - Effort: ~1 minute
