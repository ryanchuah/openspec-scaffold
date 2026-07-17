#!/usr/bin/env python3
"""Tests for roll_decisions.py — stdlib unittest, no pytest."""

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Import module under test (sibling in scripts/)
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import roll_decisions  # noqa: E402

_ANCHOR_RE = re.compile(r"^- \*\*(\d{4}-\d{2}-\d{2})\*\*", re.MULTILINE)
_ENTRIES_START_RE = re.compile(r"^- \*\*\d{4}-\d{2}-\d{2}\*\*", re.MULTILINE)

_HEADER = (
    "# Decisions Registry\n"
    "\n"
    "One line per decision. Format:\n"
    "- Pointer: `- **YYYY-MM-DD** · <slug> · <one-line essence>`\n"
    "\n"
    "---\n"
    "\n"
)

_HEADER_NO_SEPARATOR = "# Decisions Registry (per-repo prose header, no --- line)\n\n"


# ===================================================================
# Helpers
# ===================================================================


def _bytes(s: str) -> int:
    return len(s.encode("utf-8"))


def _make_entry(date: str, pad: int, continuation_lines: list[str] | None = None) -> str:
    """Build one entry block: an anchor line padded to a controlled size,
    optionally followed by continuation lines (which must NOT themselves
    match the anchor pattern)."""
    text = f"- **{date}** · {'x' * pad}\n"
    for line in continuation_lines or []:
        text += line + "\n"
    return text


def _entries_region(text: str) -> str:
    """Return *text* from the first anchor line to EOF (empty if none)."""
    m = _ENTRIES_START_RE.search(text)
    return text[m.start() :] if m else ""


def _anchor_dates(text: str) -> list[str]:
    return _ANCHOR_RE.findall(text)


def _make_index_repo(tmpdir: Path, entries: list[str], header: str = _HEADER) -> Path:
    """Write a synthetic repo whose knowledge/decisions/INDEX.md is
    header + entries (concatenated verbatim). Returns the repo root."""
    repo = tmpdir / "repo"
    decisions_dir = repo / "knowledge" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    (decisions_dir / "INDEX.md").write_text(header + "".join(entries), encoding="utf-8")
    return repo


def _index_path(repo: Path) -> Path:
    return repo / "knowledge" / "decisions" / "INDEX.md"


def _history_path(repo: Path) -> Path:
    return repo / "knowledge" / "decisions" / "HISTORY.md"


# ===================================================================
# Tests
# ===================================================================


class RollDecisionsTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # 2.2 — basic roll
    # ------------------------------------------------------------------

    def test_basic_roll_oldest_entries_move_to_history(self):
        entries = [_make_entry(f"2026-01-0{i}", 150) for i in range(1, 7)]  # 6 entries
        entry_bytes = _bytes(entries[0])
        header_bytes = _bytes(_HEADER)
        pointer_bytes = _bytes(roll_decisions._POINTER_LINE + "\n")
        # Exactly enough room to retain the newest 3 entries once the
        # pointer line is added.
        target = header_bytes + pointer_bytes + 3 * entry_bytes

        repo = _make_index_repo(self.tmpdir, entries)
        rc = roll_decisions.main([str(repo), "--target-bytes", str(target)])
        self.assertEqual(rc, 0)

        new_index_text = _index_path(repo).read_text(encoding="utf-8")
        history_text = _history_path(repo).read_text(encoding="utf-8")

        # Oldest-first: dates 01-03 rolled to HISTORY, in order.
        self.assertEqual(_anchor_dates(history_text), ["2026-01-01", "2026-01-02", "2026-01-03"])
        # Newest 3 retained in INDEX, in order.
        self.assertEqual(_anchor_dates(new_index_text), ["2026-01-04", "2026-01-05", "2026-01-06"])

        self.assertLessEqual(_bytes(new_index_text), target)

        # Header lines intact; pointer line present exactly once, right
        # after the closing '---' separator.
        self.assertEqual(new_index_text.count(roll_decisions._POINTER_LINE), 1)
        header_prefix = _HEADER.split("---\n")[0] + "---\n"
        self.assertTrue(new_index_text.startswith(header_prefix))
        after_dash = new_index_text[len(header_prefix) :]
        self.assertTrue(after_dash.startswith(roll_decisions._POINTER_LINE + "\n"))

    # ------------------------------------------------------------------
    # 2.3 — byte conservation
    # ------------------------------------------------------------------

    def test_byte_conservation_and_header_preserved(self):
        entries = [_make_entry(f"2026-02-0{i}", 200) for i in range(1, 6)]  # 5 entries
        repo = _make_index_repo(self.tmpdir, entries)
        original_text = _index_path(repo).read_text(encoding="utf-8")

        rc = roll_decisions.main([str(repo), "--target-bytes", "700"])
        self.assertEqual(rc, 0)

        new_index_text = _index_path(repo).read_text(encoding="utf-8")
        history_text = _history_path(repo).read_text(encoding="utf-8")

        orig_entries = _entries_region(original_text)
        history_entries = _entries_region(history_text)
        index_entries_after = _entries_region(new_index_text)

        # Concatenating (HISTORY's appended blocks + rolled INDEX's
        # retained entry blocks) reproduces the original entry sequence
        # byte-for-byte.
        self.assertEqual(history_entries + index_entries_after, orig_entries)

        # Header unchanged apart from the one inserted pointer line.
        orig_header = original_text[: len(original_text) - len(orig_entries)]
        new_header = new_index_text[: len(new_index_text) - len(index_entries_after)]
        pointer_line_full = roll_decisions._POINTER_LINE + "\n"
        self.assertEqual(new_header.replace(pointer_line_full, "", 1), orig_header)

    # ------------------------------------------------------------------
    # 2.4 — continuation lines never split
    # ------------------------------------------------------------------

    def test_continuation_lines_move_as_one_block(self):
        multiline_entry = _make_entry(
            "2026-03-01",
            30,
            continuation_lines=["  continuation line one", "  continuation line two"],
        )
        rest = [_make_entry(f"2026-03-0{i}", 30) for i in (2, 3)]
        entries = [multiline_entry] + rest

        header_bytes = _bytes(_HEADER)
        pointer_bytes = _bytes(roll_decisions._POINTER_LINE + "\n")
        # Retain exactly the last two (single-line) entries; roll only the
        # multi-line entry.
        target = header_bytes + pointer_bytes + _bytes(rest[0]) + _bytes(rest[1])

        repo = _make_index_repo(self.tmpdir, entries)
        rc = roll_decisions.main([str(repo), "--target-bytes", str(target)])
        self.assertEqual(rc, 0)

        history_text = _history_path(repo).read_text(encoding="utf-8")
        new_index_text = _index_path(repo).read_text(encoding="utf-8")

        # The whole multi-line block — anchor plus both continuation
        # lines — landed together in HISTORY, never split.
        self.assertIn(multiline_entry, history_text)
        self.assertIn("continuation line one", history_text)
        self.assertIn("continuation line two", history_text)
        # Neither continuation line leaked into INDEX.
        self.assertNotIn("continuation line one", new_index_text)
        self.assertNotIn("continuation line two", new_index_text)

        self.assertEqual(_entries_region(new_index_text), rest[0] + rest[1])

    # ------------------------------------------------------------------
    # 2.5 — idempotence, no-op, re-roll, --target-bytes
    # ------------------------------------------------------------------

    def test_second_run_after_roll_is_noop(self):
        entries = [_make_entry(f"2026-04-0{i}", 150) for i in range(1, 7)]
        repo = _make_index_repo(self.tmpdir, entries)
        target = "700"

        rc1 = roll_decisions.main([str(repo), "--target-bytes", target])
        self.assertEqual(rc1, 0)
        index_after_first = _index_path(repo).read_text(encoding="utf-8")
        history_after_first = _history_path(repo).read_text(encoding="utf-8")

        rc2 = roll_decisions.main([str(repo), "--target-bytes", target])
        self.assertEqual(rc2, 0)
        self.assertEqual(_index_path(repo).read_text(encoding="utf-8"), index_after_first)
        self.assertEqual(_history_path(repo).read_text(encoding="utf-8"), history_after_first)

    def test_under_target_index_untouched(self):
        entries = [_make_entry("2026-05-01", 20)]
        repo = _make_index_repo(self.tmpdir, entries)
        original_text = _index_path(repo).read_text(encoding="utf-8")

        rc = roll_decisions.main([str(repo)])  # default target (12,000) — well under
        self.assertEqual(rc, 0)
        self.assertEqual(_index_path(repo).read_text(encoding="utf-8"), original_text)
        self.assertFalse(_history_path(repo).is_file())

    def test_reroll_pointer_line_stays_single_and_history_header_not_duplicated(self):
        entries = [_make_entry(f"2026-06-0{i}", 150) for i in range(1, 7)]
        repo = _make_index_repo(self.tmpdir, entries)
        target = "700"

        rc1 = roll_decisions.main([str(repo), "--target-bytes", target])
        self.assertEqual(rc1, 0)

        # Push INDEX back over target with fresh new entries.
        more_entries = [_make_entry(f"2026-06-1{i}", 150) for i in range(0, 4)]
        index_path = _index_path(repo)
        index_path.write_text(
            index_path.read_text(encoding="utf-8") + "".join(more_entries), encoding="utf-8"
        )

        rc2 = roll_decisions.main([str(repo), "--target-bytes", target])
        self.assertEqual(rc2, 0)

        new_index_text = index_path.read_text(encoding="utf-8")
        history_text = _history_path(repo).read_text(encoding="utf-8")

        self.assertEqual(new_index_text.count(roll_decisions._POINTER_LINE), 1)
        self.assertEqual(history_text.count("# Decisions Registry — history"), 1)
        self.assertLessEqual(_bytes(new_index_text), int(target))

    def test_target_bytes_flag_honored(self):
        entries = [_make_entry(f"2026-07-0{i}", 150) for i in range(1, 9)]
        repo = _make_index_repo(self.tmpdir, entries)
        n = 900

        rc = roll_decisions.main([str(repo), "--target-bytes", str(n)])
        self.assertEqual(rc, 0)
        new_index_text = _index_path(repo).read_text(encoding="utf-8")
        self.assertLessEqual(_bytes(new_index_text), n)

    # ------------------------------------------------------------------
    # 2.6 — guards
    # ------------------------------------------------------------------

    def test_no_anchor_lines_exits_2_writes_nothing(self):
        repo = self.tmpdir / "repo"
        decisions_dir = repo / "knowledge" / "decisions"
        decisions_dir.mkdir(parents=True)
        bad_text = "# Decisions Registry\n\nNo entries at all, no anchors.\n"
        (decisions_dir / "INDEX.md").write_text(bad_text, encoding="utf-8")

        rc = roll_decisions.main([str(repo), "--target-bytes", "10"])
        self.assertEqual(rc, 2)
        self.assertEqual(_index_path(repo).read_text(encoding="utf-8"), bad_text)
        self.assertFalse(_history_path(repo).is_file())

    def test_dry_run_over_target_leaves_files_untouched(self):
        entries = [_make_entry(f"2026-08-0{i}", 150) for i in range(1, 7)]
        repo = _make_index_repo(self.tmpdir, entries)
        original_text = _index_path(repo).read_text(encoding="utf-8")

        rc = roll_decisions.main([str(repo), "--target-bytes", "700", "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertEqual(_index_path(repo).read_text(encoding="utf-8"), original_text)
        self.assertFalse(_history_path(repo).is_file())

    def test_single_oversized_entry_never_emptied(self):
        entries = [_make_entry("2026-09-01", 500)]
        repo = _make_index_repo(self.tmpdir, entries)
        original_text = _index_path(repo).read_text(encoding="utf-8")

        rc = roll_decisions.main([str(repo), "--target-bytes", "50"])
        self.assertEqual(rc, 0)
        self.assertEqual(_index_path(repo).read_text(encoding="utf-8"), original_text)
        self.assertFalse(_history_path(repo).is_file())

    # ------------------------------------------------------------------
    # 2.7 — appending to an existing HISTORY.md
    # ------------------------------------------------------------------

    def test_appends_to_existing_history_without_duplicating_header(self):
        entries = [_make_entry(f"2026-10-0{i}", 150) for i in range(1, 7)]
        repo = _make_index_repo(self.tmpdir, entries)

        prior_history_text = (
            "# Decisions Registry — history\n"
            "\n"
            "Rolled verbatim from `INDEX.md`, same format, oldest first, never "
            "boot-loaded — grep `knowledge/decisions/` on demand.\n"
            "\n"
            "---\n"
            "\n"
            "- **2025-12-31** · pre-existing rolled entry\n"
        )
        history_path = _history_path(repo)
        history_path.write_text(prior_history_text, encoding="utf-8")

        rc = roll_decisions.main([str(repo), "--target-bytes", "700"])
        self.assertEqual(rc, 0)

        new_history_text = history_path.read_text(encoding="utf-8")
        self.assertTrue(new_history_text.startswith(prior_history_text))
        self.assertEqual(new_history_text.count("# Decisions Registry — history"), 1)
        # New blocks landed strictly after the prior content.
        appended = new_history_text[len(prior_history_text) :]
        self.assertTrue(appended)
        self.assertTrue(_ENTRIES_START_RE.match(appended))


if __name__ == "__main__":
    unittest.main()
