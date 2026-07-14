#!/usr/bin/env python3
"""Tests for archive_move.py.

Covers: successful move, destination-exists conflict, missing source.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import archive_move  # noqa: E402


def _run(
    change_root: str | Path,
    archive_path: str | Path,
) -> tuple[int, str, str]:
    """Run archive_move.main() and return (exit_code, stdout, stderr)."""
    import io
    from contextlib import redirect_stderr, redirect_stdout

    argv = ["--change-root", str(change_root), "--archive-path", str(archive_path)]
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    with redirect_stdout(out_buf), redirect_stderr(err_buf):
        rc = archive_move.main(argv)
    return rc, out_buf.getvalue(), err_buf.getvalue()


class TestArchiveMove:
    """Tests for archive_move.py."""

    def test_move_success(self, tmp_path: Path) -> None:
        """Move succeeds: dest parent created, dir relocated, exit 0."""
        src = tmp_path / "changes" / "my-change"
        src.mkdir(parents=True)
        (src / "some-file.txt").write_text("hello")

        dest = tmp_path / "archive" / "my-change"

        rc, out, err = _run(src, dest)
        assert rc == 0
        assert "Moved" in out
        assert not src.exists()
        assert dest.is_dir()
        assert (dest / "some-file.txt").read_text() == "hello"

    def test_destination_exists_conflict(self, tmp_path: Path) -> None:
        """Dest exists → exit 2, nothing moved."""
        src = tmp_path / "changes" / "my-change"
        src.mkdir(parents=True)
        (src / "some-file.txt").write_text("hello")

        dest = tmp_path / "archive" / "my-change"
        dest.mkdir(parents=True)
        (dest / "existing.txt").write_text("existing")

        rc, out, err = _run(src, dest)
        assert rc == 2
        assert "already exists" in err
        assert src.exists()  # Source still there
        assert (dest / "existing.txt").read_text() == "existing"  # Dest untouched

    def test_missing_source(self, tmp_path: Path) -> None:
        """Missing source → exit 2."""
        src = tmp_path / "changes" / "nonexistent"
        dest = tmp_path / "archive" / "my-change"

        rc, out, err = _run(src, dest)
        assert rc == 2
        assert "source not found" in err
        assert not dest.exists()
