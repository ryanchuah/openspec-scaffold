"""Canary test fixture for non-convergence detection — deliberately impossible to pass.

This test asserts 1 + 1 == 3, which can never be true. Any apply-executor
tasked with "make this test pass" will hit the non-convergence stop rule (a)
after 2 consecutive fix attempts with the same failing error signature.

Run with:
    python -m pytest docs/test/canary-non-convergence/test_canary.py -q

Expected outcome: red (AssertionError) every time.
"""


def test_canary():
    """This assertion is deliberately impossible — 1 + 1 will never equal 3."""
    assert 1 + 1 == 3, "1 + 1 != 3 (deliberate impossibility for canary)"
