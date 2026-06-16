# Canary: Non-Convergence Detection

This is a **deliberately impossible** test fixture used to verify that the
apply-executor's non-convergence detection works correctly.

## Purpose

When an apply-executor is tasked with "make `test_canary` pass", it will:

1. Run the test → red (AssertionError)
2. Try to fix → run the test → red again (same error)
3. **After 2 same-signature attempts, the convergence helper emits
   `STOP:a`** → the executor emits a `### NON-CONVERGENCE BLOCKER` block
   and ends the run without looping until the wall-clock timeout.

## Verify Procedure

To confirm the non-convergence guard works:

1. Create a short-lived change whose `tasks.md` points to this fixture's
   single task ("make `test_canary` pass").
2. Run the apply phase with the apply-executor.
3. **Expected:** the executor stops after 2 attempts and emits a
   `### NON-CONVERGENCE BLOCKER` with `trigger: a` (not a wall-clock
   timeout, and not endless looping).

If the executor loops past 2 attempts or times out, the convergence helper
or the executor prompt's self-monitoring loop is not wired correctly.

## Files

| File | Purpose |
|---|---|
| `tasks.md` | One-task checklist: "make `test_canary` pass" |
| `test_canary.py` | Python test with deliberately impossible assertion |

## Run

```bash
# The test itself — always red
python -m pytest docs/test/canary-non-convergence/test_canary.py -q
```
