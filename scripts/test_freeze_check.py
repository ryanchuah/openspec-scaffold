#!/usr/bin/env python3
"""Tests for freeze_check.py — stdlib unittest, no pytest.

Every test asserts BOTH the exit code AND the printed output line (L3).
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import freeze_check  # noqa: E402


class FreezeCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_review(self, content: str) -> str:
        p = self.tmpdir / "review.txt"
        p.write_text(content, encoding="utf-8")
        return str(p)

    def _run(self, artifact: str, review_path: str) -> tuple[int, str, str]:
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = freeze_check.main(["--artifact", artifact, "--review", review_path])
        return rc, out_buf.getvalue().strip(), err_buf.getvalue().strip()

    # --- Proposal: all combinations ---

    def test_proposal_pass_agree_ready(self):
        """proposal: VERDICT PASS + PREMISE AGREE => FREEZE: READY."""
        review = "### Verdict\nVERDICT: PASS\n### Premise Verdict\nPREMISE: AGREE\n"
        rc, out, err = self._run("proposal", self._write_review(review))
        self.assertEqual(rc, 0)
        self.assertEqual(out, "FREEZE: READY")
        self.assertEqual(err, "")

    def test_proposal_pass_dissent_premise_dissent(self):
        """proposal: VERDICT PASS + PREMISE DISSENT => premise-dissent."""
        review = "### Verdict\nVERDICT: PASS\n### Premise Verdict\nPREMISE: DISSENT\n"
        rc, out, err = self._run("proposal", self._write_review(review))
        self.assertEqual(rc, 1)
        self.assertEqual(out, "FREEZE: BLOCKED — premise-dissent")

    def test_proposal_needs_revision_needs_revision(self):
        """proposal: VERDICT NEEDS REVISION (regardless of PREMISE) => needs-revision."""
        review = "### Verdict\nVERDICT: NEEDS REVISION\n### Premise Verdict\nPREMISE: AGREE\n"
        rc, out, err = self._run("proposal", self._write_review(review))
        self.assertEqual(rc, 1)
        self.assertEqual(out, "FREEZE: BLOCKED — needs-revision")

    def test_proposal_missing_verdict_missing_verdict(self):
        """proposal: no VERDICT line => missing-verdict."""
        review = "### Premise Verdict\nPREMISE: AGREE\n"
        rc, out, err = self._run("proposal", self._write_review(review))
        self.assertEqual(rc, 1)
        self.assertEqual(out, "FREEZE: BLOCKED — missing-verdict")

    def test_proposal_pass_missing_premise_missing_verdict(self):
        """proposal: VERDICT PASS but no PREMISE => missing-verdict."""
        review = "### Verdict\nVERDICT: PASS\n"
        rc, out, err = self._run("proposal", self._write_review(review))
        self.assertEqual(rc, 1)
        self.assertEqual(out, "FREEZE: BLOCKED — missing-verdict")

    def test_proposal_whitespace_tolerance(self):
        """Whitespace around VERDICT/PREMISE tokens is tolerated."""
        review = "### Verdict\n  VERDICT:   PASS  \n### Premise Verdict\n  PREMISE:   AGREE  \n"
        rc, out, err = self._run("proposal", self._write_review(review))
        self.assertEqual(rc, 0)
        self.assertEqual(out, "FREEZE: READY")

    def test_proposal_inline_backtick_not_matched(self):
        """An inline `` `VERDICT: PASS` `` in prose does NOT satisfy the
        anchored parse — only the real whole-line-anchored VERDICT counts."""
        review = (
            "The reviewer should emit `VERDICT: PASS` at the end.\n"
            "### Verdict\n"
            "VERDICT: NEEDS REVISION\n"
        )
        rc, out, err = self._run("proposal", self._write_review(review))
        self.assertEqual(rc, 1)
        self.assertEqual(out, "FREEZE: BLOCKED — needs-revision")

    def test_proposal_last_verdict_wins(self):
        """If multiple VERDICT lines exist, the last one wins."""
        review = "VERDICT: PASS\n### Verdict\nVERDICT: NEEDS REVISION\n"
        rc, out, err = self._run("proposal", self._write_review(review))
        self.assertEqual(rc, 1)
        self.assertEqual(out, "FREEZE: BLOCKED — needs-revision")

    def test_proposal_last_premise_wins(self):
        """If multiple PREMISE lines exist, the last one wins."""
        review = "PREMISE: DISSENT\nVERDICT: PASS\nPREMISE: AGREE\n"
        rc, out, err = self._run("proposal", self._write_review(review))
        self.assertEqual(rc, 0)
        self.assertEqual(out, "FREEZE: READY")

    # --- Design / tasks ---

    def test_design_pass_ready(self):
        """design: VERDICT PASS => FREEZE: READY."""
        review = "### Verdict\nVERDICT: PASS\n"
        rc, out, err = self._run("design", self._write_review(review))
        self.assertEqual(rc, 0)
        self.assertEqual(out, "FREEZE: READY")

    def test_design_needs_revision_needs_revision(self):
        """design: VERDICT NEEDS REVISION => needs-revision."""
        review = "### Verdict\nVERDICT: NEEDS REVISION\n"
        rc, out, err = self._run("design", self._write_review(review))
        self.assertEqual(rc, 1)
        self.assertEqual(out, "FREEZE: BLOCKED — needs-revision")

    def test_design_missing_verdict_missing_verdict(self):
        """design: no VERDICT line => missing-verdict."""
        review = "Some text without a verdict line.\n"
        rc, out, err = self._run("design", self._write_review(review))
        self.assertEqual(rc, 1)
        self.assertEqual(out, "FREEZE: BLOCKED — missing-verdict")

    def test_tasks_pass_ready(self):
        """tasks: VERDICT PASS => FREEZE: READY."""
        review = "### Verdict\nVERDICT: PASS\n"
        rc, out, err = self._run("tasks", self._write_review(review))
        self.assertEqual(rc, 0)
        self.assertEqual(out, "FREEZE: READY")

    # --- INFRA errors ---

    def test_infra_bad_artifact_choice(self):
        """Bad --artifact value => exit 3 + stderr."""
        review_path = self._write_review("VERDICT: PASS\n")
        rc, out, err = self._run("bad-artifact", review_path)
        self.assertEqual(rc, 3)
        self.assertIn("usage:", err.lower())

    def test_infra_unreadable_file(self):
        """Unreadable --review file => exit 3 + stderr."""
        fake_path = str(self.tmpdir / "nonexistent.txt")
        rc, out, err = self._run("proposal", fake_path)
        self.assertEqual(rc, 3)
        self.assertIn("INFRA-FAIL", err)
        self.assertIn("nonexistent.txt", err)

    def test_infra_missing_review_arg(self):
        """Missing --review => exit 3 + stderr."""
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = freeze_check.main(["--artifact", "design"])
        self.assertEqual(rc, 3)
        self.assertIn("required", err_buf.getvalue())


if __name__ == "__main__":
    unittest.main()
