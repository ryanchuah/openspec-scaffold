#!/usr/bin/env python3
"""Tests for boot_surface_lint.py — stdlib unittest, no pytest."""

from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

# ---------------------------------------------------------------------------
# Import module under test (sibling in scripts/)
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import boot_surface_lint  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

# ===================================================================
# Helpers
# ===================================================================


def _make_boot_repo(tmpdir: Path, sizes: dict[str, int], checks_toml: str | None = None) -> Path:
    """Create a temporary repo with boot files of exact byte sizes.

    For each BOOT_FILES-relative path in *sizes*, parent directories are
    created and a file of ``"x" * n`` ASCII bytes is written (bytes ==
    chars).  A path omitted from *sizes* is left absent (exercises the
    missing-file branch).

    If *checks_toml* is given, it is written verbatim as ``checks.toml`` in
    the repo root.

    Returns
    -------
    Path
        The repo root.
    """
    repo = tmpdir / "repo"
    repo.mkdir()
    for rel_path, n_bytes in sizes.items():
        full_path = repo / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("x" * n_bytes, encoding="ascii")
    if checks_toml is not None:
        (repo / "checks.toml").write_text(checks_toml, encoding="utf-8")
    return repo


def _run_main_capture(args: list[str]) -> tuple[int, str]:
    """Run boot_surface_lint.main(args), capturing stdout alongside the
    exit code (used to assert on/absence of the WARN/FAIL remedy line)."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = boot_surface_lint.main(args)
    return rc, buf.getvalue()


# ===================================================================
# Tests
# ===================================================================


class BootSurfaceLintTest(unittest.TestCase):
    """Coverage of boot-surface aggregate byte budget."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        for root, dirs, files in os.walk(self.tmpdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.tmpdir)

    # ------------------------------------------------------------------
    # Three-way verdicts
    # ------------------------------------------------------------------

    def test_under_warn_passes(self):
        """Total under 80,000 => exit 0, no remedy line."""
        repo = _make_boot_repo(self.tmpdir, {"AGENTS.md": 30_000, "knowledge/STATUS.md": 10_000})
        rc, output = _run_main_capture([str(repo)])
        self.assertEqual(rc, 0)
        self.assertNotIn(boot_surface_lint.REMEDY_LINE, output)

    def test_in_warn_band(self):
        """Total in [80_000, 100_000) => exit 1, remedy line present."""
        repo = _make_boot_repo(
            self.tmpdir,
            {"AGENTS.md": 40_000, "knowledge/STATUS.md": 40_001},
        )
        rc, output = _run_main_capture([str(repo)])
        self.assertEqual(rc, 1)
        self.assertIn(boot_surface_lint.REMEDY_LINE, output)

    def test_at_fail_or_above(self):
        """Total >= 100,000 => exit 2, remedy line present."""
        repo = _make_boot_repo(
            self.tmpdir,
            {"AGENTS.md": 50_000, "knowledge/STATUS.md": 50_000},
        )
        rc, output = _run_main_capture([str(repo)])
        self.assertEqual(rc, 2)
        self.assertIn(boot_surface_lint.REMEDY_LINE, output)

    # ------------------------------------------------------------------
    # Boundary values
    # ------------------------------------------------------------------

    def test_boundary_exactly_80k_warns(self):
        """Exactly 80,000 bytes => WARN side (exit 1)."""
        repo = _make_boot_repo(
            self.tmpdir,
            {"AGENTS.md": 40_000, "knowledge/STATUS.md": 40_000},
        )
        rc = boot_surface_lint.main([str(repo)])
        self.assertEqual(rc, 1)

    def test_boundary_exactly_100k_fails(self):
        """Exactly 100,000 bytes => FAIL side (exit 2)."""
        repo = _make_boot_repo(
            self.tmpdir,
            {"AGENTS.md": 50_000, "knowledge/STATUS.md": 50_000},
        )
        rc = boot_surface_lint.main([str(repo)])
        self.assertEqual(rc, 2)

    # ------------------------------------------------------------------
    # Missing file
    # ------------------------------------------------------------------

    def test_missing_file_skipped(self):
        """A missing boot file is skipped, not an error."""
        # Only AGENTS.md present; decisions/INDEX.md missing => fine
        repo = _make_boot_repo(self.tmpdir, {"AGENTS.md": 100})
        rc = boot_surface_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    # ------------------------------------------------------------------
    # Per-repo config overrides
    # ------------------------------------------------------------------

    def test_raised_fail_bytes_passes_over_100k(self):
        """fail_bytes=150000 lets an over-100k surface return 0 or 1 (not 2)."""
        sizes = {"AGENTS.md": 60_000, "knowledge/STATUS.md": 50_000}
        checks_toml = "[boot_surface_lint]\nfail_bytes = 150000\n"
        repo = _make_boot_repo(self.tmpdir, sizes, checks_toml=checks_toml)
        rc = boot_surface_lint.main([str(repo)])
        self.assertIn(rc, (0, 1))

    def test_lowered_thresholds_warn_and_fail(self):
        """Lowered warn_bytes/fail_bytes make a small surface WARN then FAIL."""
        sizes = {"AGENTS.md": 1_000, "knowledge/STATUS.md": 500}
        # warn at 1000, fail at 1500 — total is 1500 => FAIL
        checks_toml = "[boot_surface_lint]\nwarn_bytes = 1000\nfail_bytes = 1500\n"
        repo = _make_boot_repo(self.tmpdir, sizes, checks_toml=checks_toml)
        rc = boot_surface_lint.main([str(repo)])
        self.assertEqual(rc, 2)

    def test_absent_config_falls_back_to_defaults(self):
        """No checks.toml => defaults of 80k warn / 100k fail."""
        repo = _make_boot_repo(self.tmpdir, {"AGENTS.md": 40_000, "knowledge/STATUS.md": 40_001})
        rc = boot_surface_lint.main([str(repo)])
        self.assertEqual(rc, 1)

    def test_malformed_config_falls_back_to_defaults(self):
        """Malformed config (float instead of int) falls back to 80k/100k defaults.

        The override floats are chosen to DIFFER from the defaults so the test is
        non-vacuous: if the isinstance guard did NOT fire, warn=50000.0/fail=60000.0
        would make total 80001 a FAIL (rc=2); the guard's fallback to 80k/100k makes
        it a WARN (rc=1). Asserting rc==1 therefore proves the type-check fired.
        """
        sizes = {"AGENTS.md": 40_000, "knowledge/STATUS.md": 40_001}
        checks_toml = "[boot_surface_lint]\nwarn_bytes = 50000.0\nfail_bytes = 60000.0\n"
        repo = _make_boot_repo(self.tmpdir, sizes, checks_toml=checks_toml)
        rc = boot_surface_lint.main([str(repo)])
        self.assertEqual(rc, 1)

    def test_inverted_thresholds_fall_back_to_defaults(self):
        """warn_bytes > fail_bytes falls back to defaults (warn=80k, fail=100k)."""
        sizes = {"AGENTS.md": 40_000, "knowledge/STATUS.md": 40_001}
        checks_toml = "[boot_surface_lint]\nwarn_bytes = 150000\nfail_bytes = 50000\n"
        repo = _make_boot_repo(self.tmpdir, sizes, checks_toml=checks_toml)
        rc = boot_surface_lint.main([str(repo)])
        self.assertEqual(rc, 1)

    # ------------------------------------------------------------------
    # Live-tree gate
    # ------------------------------------------------------------------

    def test_boot_surface_live_tree_not_fail(self):
        """The live tree must not cross the FAIL threshold (exit 2)."""
        rc = boot_surface_lint.main([str(REPO_ROOT)])
        self.assertNotEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
