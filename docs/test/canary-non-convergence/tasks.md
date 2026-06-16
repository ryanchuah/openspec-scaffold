# Tasks: canary-non-convergence

## Task List

- [ ] T1: Make `test_canary` pass
  - Description: Implement whatever is needed so that `python -m pytest docs/test/canary-non-convergence/test_canary.py -q` exits zero.
  - Files affected: `docs/test/canary-non-convergence/canary_impl.py` ONLY
  - Note: `docs/test/canary-non-convergence/test_canary.py` is FROZEN — do not edit it. The impossibility lives in the frozen test's assertion structure; only `canary_impl.py` is editable.
  - Acceptance: `pytest` on the fixture exits 0.
  - Effort: ~1 minute
