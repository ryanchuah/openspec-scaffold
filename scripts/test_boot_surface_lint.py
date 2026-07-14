#!/usr/bin/env python3
"""Tests for boot_surface_lint.py — stdlib unittest, no pytest."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
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


def _make_boot_repo(tmpdir: Path, sizes: dict[str, int]) -> Path:
    """Create a temporary repo with boot files of exact byte sizes.

    For each BOOT_FILES-relative path in *sizes*, parent directories are
    created and a file of ``"x" * n`` ASCII bytes is written (bytes ==
    chars).  A path omitted from *sizes* is left absent (exercises the
    missing-file branch).

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
    return repo


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
        """Total under 80,000 => exit 0."""
        repo = _make_boot_repo(self.tmpdir, {"AGENTS.md": 30_000, "knowledge/STATUS.md": 10_000})
        rc = boot_surface_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    def test_in_warn_band(self):
        """Total in [80_000, 100_000) => exit 1."""
        repo = _make_boot_repo(
            self.tmpdir,
            {"AGENTS.md": 40_000, "knowledge/STATUS.md": 40_001},
        )
        rc = boot_surface_lint.main([str(repo)])
        self.assertEqual(rc, 1)

    def test_at_fail_or_above(self):
        """Total >= 100,000 => exit 2."""
        repo = _make_boot_repo(
            self.tmpdir,
            {"AGENTS.md": 50_000, "knowledge/STATUS.md": 50_000},
        )
        rc = boot_surface_lint.main([str(repo)])
        self.assertEqual(rc, 2)

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
    # Live-tree gate
    # ------------------------------------------------------------------

    def test_boot_surface_live_tree_not_fail(self):
        """The live tree must not cross the FAIL threshold (exit 2)."""
        rc = boot_surface_lint.main([str(REPO_ROOT)])
        self.assertNotEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
