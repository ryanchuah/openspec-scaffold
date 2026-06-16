#!/usr/bin/env python3
"""Tests for _convergence.py — standard library unittest, no pytest dependency."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Import the module under test (sibling in scripts/)
# ---------------------------------------------------------------------------

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _convergence  # noqa: E402 — import after sys.path fix


class NormalizeSignatureTest(unittest.TestCase):
    """Tests for _normalize_signature: cosmetic diffs collapse; real diffs stay distinct."""

    def setUp(self):
        # Point state dir to a temp dir so tests don't collide
        self._orig_state_dir = _convergence._STATE_DIR
        self.tmpdir = tempfile.mkdtemp()
        _convergence._STATE_DIR = self.tmpdir

    def tearDown(self):
        _convergence._STATE_DIR = self._orig_state_dir
        for f in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)

    # --- Normalizer: cosmetic differences ---

    def test_line_numbers_normalize(self):
        """Outputs differing only in line numbers normalize to same signature."""
        a = "  test_foo.py:42: AssertionError: expected 5, got 3"
        b = "  test_foo.py:99: AssertionError: expected 5, got 3"
        self.assertEqual(
            _convergence._normalize_signature(a),
            _convergence._normalize_signature(b),
        )

    def test_absolute_paths_normalize(self):
        """Outputs with different absolute paths normalize to same signature."""
        a = "  File \"/home/user/project/foo.py\", line 10, in bar"
        b = "  File \"/home/other/project/foo.py\", line 20, in bar"
        self.assertEqual(
            _convergence._normalize_signature(a),
            _convergence._normalize_signature(b),
        )

    def test_tmp_paths_normalize(self):
        """Outputs with different tmp paths normalize to same signature."""
        a = "  Error in /tmp/test_123/input.txt"
        b = "  Error in /tmp/test_456/input.txt"
        self.assertEqual(
            _convergence._normalize_signature(a),
            _convergence._normalize_signature(b),
        )

    def test_hex_addresses_normalize(self):
        """Outputs with different hex addresses normalize to same signature."""
        a = "  ValueError at 0x7f1a2b3c4d5e"
        b = "  ValueError at 0x9f8e7d6c5b4a"
        self.assertEqual(
            _convergence._normalize_signature(a),
            _convergence._normalize_signature(b),
        )

    def test_timestamps_normalize(self):
        """Outputs with different ISO timestamps normalize to same signature."""
        a = "  2026-06-16T10:30:00 ERROR: timeout"
        b = "  2026-06-17T14:22:00 ERROR: timeout"
        self.assertEqual(
            _convergence._normalize_signature(a),
            _convergence._normalize_signature(b),
        )

    def test_elapsed_time_normalize(self):
        """Outputs with different elapsed times normalize to same signature."""
        a = "  Tests completed in 2.34s"
        b = "  Tests completed in 5.67s"
        self.assertEqual(
            _convergence._normalize_signature(a),
            _convergence._normalize_signature(b),
        )

    def test_object_at_hex_normalize(self):
        """'object at 0x...' normalizes across different addresses."""
        a = "  <Foo object at 0x7f1a2b3c4d5e>"
        b = "  <Foo object at 0x9f8e7d6c5b4a>"
        self.assertEqual(
            _convergence._normalize_signature(a),
            _convergence._normalize_signature(b),
        )

    # --- Normalizer: genuinely different errors stay distinct ---

    def test_different_error_types_stay_distinct(self):
        """Different error types yield different signatures."""
        a = "  AssertionError: expected 5, got 3"
        b = "  TypeError: unsupported operand type(s)"
        self.assertNotEqual(
            _convergence._normalize_signature(a),
            _convergence._normalize_signature(b),
        )

    def test_different_error_messages_stay_distinct(self):
        """Same error type with substantively different messages yields different sigs."""
        a = "  ValueError: invalid literal for int() with base 10: 'abc'"
        b = "  ValueError: list.remove(x): x not in list"
        self.assertNotEqual(
            _convergence._normalize_signature(a),
            _convergence._normalize_signature(b),
        )

    def test_different_test_names_stay_distinct(self):
        """Different failing test ids produce different contexts; the raw output differs."""
        a = "FAILED test_foo.py::test_bar - AssertionError: expected 5, got 3"
        b = "FAILED test_baz.py::test_qux - AssertionError: expected 5, got 3"
        # The test id on the FAILED line differs, so raw outputs differ
        self.assertNotEqual(
            _convergence._normalize_signature(a),
            _convergence._normalize_signature(b),
        )

    # --- Rule (a): same signature after 2 attempts ---

    def test_rule_a_continuues_after_first_attempt(self):
        """First attempt with a new signature returns CONTINUE."""
        raw = "FAILED test_foo.py::test_bar - AssertionError: expected 5, got 3"
        sig = _convergence._normalize_signature(raw)
        verdict = _convergence._verdict(
            test_id="test_foo.py::test_bar",
            signature=sig,
            editing_file=None,
            change_slug="test-change-a",
            task_id="T1",
        )
        self.assertTrue(verdict.startswith("CONTINUE"))

    def test_rule_a_trips_after_two_same_signatures(self):
        """Second same-signature attempt returns STOP:a."""
        raw = "FAILED test_foo.py::test_bar - AssertionError: expected 5, got 3"
        sig = _convergence._normalize_signature(raw)
        change_slug = "test-change-a2"

        # First attempt → CONTINUE
        v1 = _convergence._verdict(
            test_id="test_foo.py::test_bar",
            signature=sig,
            editing_file=None,
            change_slug=change_slug,
            task_id="T1",
        )
        self.assertTrue(v1.startswith("CONTINUE"))

        # Second attempt → STOP:a (same signature, now 2 attempts)
        v2 = _convergence._verdict(
            test_id="test_foo.py::test_bar",
            signature=sig,
            editing_file=None,
            change_slug=change_slug,
            task_id="T1",
        )
        self.assertTrue(v2.startswith("STOP:a"), f"Expected STOP:a, got: {v2}")

    def test_rule_a_does_not_trip_with_different_signatures(self):
        """Different signature on second attempt resets and does NOT trigger rule a."""
        raw1 = "FAILED test_foo.py::test_bar - AssertionError: expected 5, got 3"
        raw2 = "FAILED test_foo.py::test_bar - AssertionError: expected 10, got 3"
        sig1 = _convergence._normalize_signature(raw1)
        sig2 = _convergence._normalize_signature(raw2)
        change_slug = "test-change-a3"

        # First attempt → CONTINUE
        v1 = _convergence._verdict(
            test_id="test_foo.py::test_bar",
            signature=sig1,
            editing_file=None,
            change_slug=change_slug,
            task_id="T1",
        )
        self.assertTrue(v1.startswith("CONTINUE"))

        # Second attempt with different signature → CONTINUE (still trying, progress made)
        v2 = _convergence._verdict(
            test_id="test_foo.py::test_bar",
            signature=sig2,
            editing_file=None,
            change_slug=change_slug,
            task_id="T1",
        )
        self.assertTrue(v2.startswith("CONTINUE"), f"Expected CONTINUE, got: {v2}")

    # --- Rule (b): 3rd edit of same file for same failure ---
    #
    # Rule (b) checks file-edit count for the same failure (test id).
    # To test it independently of rule (a), each attempt uses a *different*
    # normalized signature (simulating a changing error that still requires
    # touching the same file). Rule (a) only fires when signatures match
    # across 2 attempts; rule (b) fires on the 3rd edit of the same file.

    def test_rule_b_trips_on_third_edit(self):
        """Third --editing of same file for same failure returns STOP:b."""
        change_slug = "test-change-b"
        test_id = "test_bar.py::test_baz"

        # Each attempt has a different error message (different signature)
        # so rule (a) never fires, but we edit the same file each time.
        raw1 = "FAILED test_bar.py::test_baz - AssertionError: attempt 1"
        raw2 = "FAILED test_bar.py::test_baz - AssertionError: attempt 2"
        raw3 = "FAILED test_bar.py::test_baz - AssertionError: attempt 3"

        sig1 = _convergence._normalize_signature(raw1)
        sig2 = _convergence._normalize_signature(raw2)
        sig3 = _convergence._normalize_signature(raw3)

        # First edit of foo.py → CONTINUE
        v1 = _convergence._verdict(
            test_id=test_id,
            signature=sig1,
            editing_file="foo.py",
            change_slug=change_slug,
            task_id="T2",
        )
        self.assertTrue(v1.startswith("CONTINUE"))

        # Second edit of foo.py with different sig → CONTINUE (rule a doesn't fire)
        v2 = _convergence._verdict(
            test_id=test_id,
            signature=sig2,
            editing_file="foo.py",
            change_slug=change_slug,
            task_id="T2",
        )
        self.assertTrue(v2.startswith("CONTINUE"))

        # Third edit of foo.py with different sig → STOP:b (3rd time)
        v3 = _convergence._verdict(
            test_id=test_id,
            signature=sig3,
            editing_file="foo.py",
            change_slug=change_slug,
            task_id="T2",
        )
        self.assertTrue(v3.startswith("STOP:b"), f"Expected STOP:b, got: {v3}")

    def test_rule_b_allows_editing_different_files(self):
        """Editing different files for the same failure does NOT trigger rule b."""
        change_slug = "test-change-b2"
        test_id = "test_bar.py::test_baz"

        raw1 = "FAILED test_bar.py::test_baz - AssertionError: v1"
        raw2 = "FAILED test_bar.py::test_baz - AssertionError: v2"

        sig1 = _convergence._normalize_signature(raw1)
        sig2 = _convergence._normalize_signature(raw2)

        # Edit foo.py with sig1 → CONTINUE
        _convergence._verdict(
            test_id=test_id,
            signature=sig1,
            editing_file="foo.py",
            change_slug=change_slug,
            task_id="T2",
        )

        # Edit bar.py with sig2 → CONTINUE (different file, no rule b)
        v = _convergence._verdict(
            test_id=test_id,
            signature=sig2,
            editing_file="bar.py",
            change_slug=change_slug,
            task_id="T2",
        )
        self.assertTrue(v.startswith("CONTINUE"))

    # --- State isolation between different failures ---

    def test_different_failures_are_independent(self):
        """State for one failure should not affect another."""
        change_slug = "test-change-iso"

        # Setup: give test_a 2 attempts
        raw_a = "FAILED test_a.py::test_a1 - AssertionError: a"
        sig_a = _convergence._normalize_signature(raw_a)
        _convergence._verdict(
            test_id="test_a.py::test_a1",
            signature=sig_a,
            editing_file="a.py",
            change_slug=change_slug,
            task_id="T1",
        )
        v_a2 = _convergence._verdict(
            test_id="test_a.py::test_a1",
            signature=sig_a,
            editing_file="a.py",
            change_slug=change_slug,
            task_id="T1",
        )
        self.assertTrue(v_a2.startswith("STOP:a"),
                        f"test_a should STOP:a after 2 same, got: {v_a2}")

        # test_b with same signature should have its own independent state
        raw_b = "FAILED test_b.py::test_b1 - TypeError: b"
        sig_b = _convergence._normalize_signature(raw_b)
        v_b1 = _convergence._verdict(
            test_id="test_b.py::test_b1",
            signature=sig_b,
            editing_file="b.py",
            change_slug=change_slug,
            task_id="T1",
        )
        self.assertTrue(v_b1.startswith("CONTINUE"),
                        f"test_b should CONTINUE on first attempt, got: {v_b1}")


if __name__ == "__main__":
    unittest.main()
