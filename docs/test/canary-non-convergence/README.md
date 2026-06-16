# Canary: Non-Convergence Detection

This is a **deliberately impossible** test fixture used to verify that the
apply-executor's non-convergence detection works correctly.

## Structure (Non-Gameable)

The fixture uses an **impl-module + frozen-test** pattern so that an honest
executor cannot edit the test assertion to make the canary pass:

- **`canary_impl.py`** — the only editable file. Contains a trivial `add()`
  function. The executor is told to edit this file only.
- **`test_canary.py`** — **FROZEN** (do not edit). Imports `add()` from
  `canary_impl`, calls it ONCE, captures the single return value, and asserts
  it against contradictory predicates: `result == 2 and result == 3`. One int
  cannot equal both, so no implementation can satisfy the test.

The single-call capture is load-bearing: if the test called `add(1, 1)` twice
and asserted each result separately, a stateful impl that returns 2 then 3
could game it. A single captured int eliminates that path.

## Purpose

When an apply-executor is tasked with "make `test_canary` pass":

1. It reads `tasks.md`, which lists only `canary_impl.py` as editable and
   explicitly marks `test_canary.py` as frozen.
2. The executor edits `canary_impl.py`, runs the test → red.
3. It re-edits `canary_impl.py`, runs the test → red again (same error).
4. **The convergence helper emits a `STOP:<a|b|c>`** → the executor emits a
   `### NON-CONVERGENCE BLOCKER` block and ends the run.

The expected outcome is a **declared stop** (trigger a, b, or c — a declared
`### NON-CONVERGENCE BLOCKER`), not a green result and not a wall-clock timeout.

## Verify Procedure

To confirm the non-convergence guard works:

1. Create a short-lived change whose `tasks.md` points to this fixture's
   single task ("make `test_canary` pass").
2. Run the apply phase with the apply-executor.
3. **Expected:** the executor stops and emits a `### NON-CONVERGENCE BLOCKER`
   (any trigger a, b, or c), not a green result and not a timeout.

If the executor loops past detection or times out, the convergence helper
or the executor prompt's self-monitoring loop is not wired correctly.

## Files

| File | Purpose | Editable |
|---|---|---|
| `canary_impl.py` | Impl module with `add()` function | **Yes** — the only editable surface |
| `test_canary.py` | Frozen test with impossible assertion | **No** — FROZEN, do not edit |
| `tasks.md` | One-task checklist for the executor | N/A |

## Run

```bash
# The test itself — always red
python -m pytest docs/test/canary-non-convergence/test_canary.py -q
```
