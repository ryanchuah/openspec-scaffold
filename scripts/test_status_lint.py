#!/usr/bin/env python3
"""Tests for status_lint.py — stdlib unittest, no pytest."""

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

import status_lint  # noqa: E402


# ===================================================================
# Helpers
# ===================================================================


def _make_repo(
    tmpdir: Path,
    status_md: str | None = None,
    decisions_index: str | None = None,
) -> Path:
    """Create a temporary repo and write optional memory/STATUS.md /
    memory/decisions/INDEX.md."""
    repo = tmpdir / "repo"
    repo.mkdir()
    if status_md is not None:
        mem = repo / "memory"
        mem.mkdir(parents=True, exist_ok=True)
        (mem / "STATUS.md").write_text(status_md, encoding="utf-8")
    if decisions_index is not None:
        dec = repo / "memory" / "decisions"
        dec.mkdir(parents=True, exist_ok=True)
        (dec / "INDEX.md").write_text(decisions_index, encoding="utf-8")
    return repo


def _make_archive_dir(repo: Path, archive_name: str) -> Path:
    """Create openspec/changes/archive/<archive_name>/ and return its path."""
    arc = repo / "openspec" / "changes" / "archive" / archive_name
    arc.mkdir(parents=True, exist_ok=True)
    return arc


def _n_words(n: int) -> str:
    """Return *n* space-separated single-letter tokens (e.g. ``"w0 w1 w2"``)."""
    return " ".join(f"w{i}" for i in range(n))


# ===================================================================
# Tests
# ===================================================================


class StatusLintTest(unittest.TestCase):
    """Coverage of STATUS cap/word-budget and decisions registry checks."""

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
    # C1 — Cap count
    # ------------------------------------------------------------------

    def test_cap_3_change_entries_pass(self):
        """Exactly 3 change-entries + preamble + exempt sections => pass."""
        status = (
            "# Status\n\n"
            "## Current state\npreamble-ish\n"
            "## Immediate next action\ndo stuff\n"
            "## Done\nsome done items\n"
            "## Pointers\nsome pointers\n"
            "## Latest change — one\nbody1\n"
            "## Prior change — two\nbody2\n"
            "## Prior change — three\nbody3\n"
        )
        repo = _make_repo(self.tmpdir, status_md=status)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    def test_cap_4_change_entries_fail(self):
        """4 change-entries => C1 violation, exit 2."""
        status = (
            "# Status\n\n"
            "## Latest change — one\nbody1\n"
            "## Prior change — two\nbody2\n"
            "## Prior change — three\nbody3\n"
            "## Even older change\nbody4\n"
        )
        repo = _make_repo(self.tmpdir, status_md=status)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 2)

    # ------------------------------------------------------------------
    # ## Operations … counts as change-entry
    # ------------------------------------------------------------------

    def test_operations_counts_as_change_entry(self):
        """3 normal + 1 ``## Operations`` => 4 change-entries => C1 fail."""
        status = (
            "# Status\n\n"
            "## Latest change — one\nbody1\n"
            "## Prior change — two\nbody2\n"
            "## Prior change — three\nbody3\n"
            "## Operations — deploy\nbody4\n"
        )
        repo = _make_repo(self.tmpdir, status_md=status)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 2)

    # ------------------------------------------------------------------
    # Exact-match guard (## Done-archive migration not exempt)
    # ------------------------------------------------------------------

    def test_done_dash_archive_not_exempt(self):
        """``## Done-archive migration`` is a change-entry (prefix not exempt)."""
        status = (
            "# Status\n\n"
            "## Latest change — one\nbody1\n"
            "## Prior change — two\nbody2\n"
            "## Prior change — three\nbody3\n"
            "## Done-archive migration\nbody4\n"
        )
        repo = _make_repo(self.tmpdir, status_md=status)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 2)

    # ------------------------------------------------------------------
    # C2 — Word budget
    # ------------------------------------------------------------------

    def test_word_budget_over_150_fails(self):
        """A change-entry with >150 body words => C2 violation."""
        status = (
            "# Status\n\n"
            "## Latest change — big\n"
            + _n_words(151)
            + "\n"
        )
        repo = _make_repo(self.tmpdir, status_md=status)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 2)

    def test_word_budget_under_150_passes(self):
        """A ~100-word change-entry => no violation."""
        status = (
            "# Status\n\n"
            "## Latest change — small\n"
            + _n_words(100)
            + "\n"
        )
        repo = _make_repo(self.tmpdir, status_md=status)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    def test_word_budget_exactly_150_passes(self):
        """A 150-word change-entry => no violation (<=150)."""
        status = (
            "# Status\n\n"
            "## Latest change — fence\n"
            + _n_words(150)
            + "\n"
        )
        repo = _make_repo(self.tmpdir, status_md=status)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    def test_word_budget_code_fence_excluded(self):
        """Words inside a fenced code block are excluded from the count."""
        # 140 words outside fence + 200 words inside fence => 140 counted => pass
        status = (
            "# Status\n\n"
            "## Latest change — coded\n"
            + _n_words(140)
            + "\n```\n"
            + _n_words(200)
            + "\n```\n"
        )
        repo = _make_repo(self.tmpdir, status_md=status)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    def test_word_budget_heading_line_excluded(self):
        """The heading line is not part of the body word count."""
        # Heading is 20 words, body is 140 words => body count = 140 => pass
        status = (
            "# Status\n\n"
            "## Latest change " + _n_words(20) + "\n"
            + _n_words(140)
            + "\n"
        )
        repo = _make_repo(self.tmpdir, status_md=status)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    # ------------------------------------------------------------------
    # Exempt sections skip C2
    # ------------------------------------------------------------------

    def test_exempt_sections_skip_c2(self):
        """Exempt sections >150w + 3 under-budget change-entries => pass."""
        status = (
            "# Status\n\n"
            "## Current state\n" + _n_words(500) + "\n"
            "## Immediate next action\n" + _n_words(200) + "\n"
            "## Done\n" + _n_words(500) + "\n"
            "## Pointers\n" + _n_words(500) + "\n"
            "## Latest change — one\n" + _n_words(100) + "\n"
            "## Prior change — two\n" + _n_words(100) + "\n"
            "## Prior change — three\n" + _n_words(100) + "\n"
        )
        repo = _make_repo(self.tmpdir, status_md=status)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    # ------------------------------------------------------------------
    # Zero change-entries
    # ------------------------------------------------------------------

    def test_zero_change_entries(self):
        """Only preamble + exempt sections => passes C1 and C2."""
        status = (
            "# Status\n\n"
            "## Current state\nproject running\n"
            "## Immediate next action\nnothing\n"
        )
        repo = _make_repo(self.tmpdir, status_md=status)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    # ------------------------------------------------------------------
    # Graceful absence
    # ------------------------------------------------------------------

    def test_graceful_absence_both_missing(self):
        """No STATUS.md and no INDEX.md => exit 0."""
        repo = _make_repo(self.tmpdir)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    def test_asymmetric_absence(self):
        """STATUS present, decisions absent => decisions skipped, no error."""
        status = "# Status\n\n## Latest change — one\nbody\n"
        repo = _make_repo(self.tmpdir, status_md=status)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    # ------------------------------------------------------------------
    # decisions/INDEX.md — registry format (D-E)
    # ------------------------------------------------------------------

    def test_registry_inline_passes(self):
        """An [inline] registry entry passes."""
        index = (
            "# Decisions Registry\n\n"
            "- **2026-06-13** · some-slug · [inline] short rationale here\n"
        )
        repo = _make_repo(self.tmpdir, decisions_index=index)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    def test_registry_pointer_resolves_passes(self):
        """A pointer to an existing archive directory passes."""
        index = (
            "# Decisions Registry\n\n"
            "- **2026-06-16** · my-change · the rationale "
            "→ `openspec/changes/archive/2026-06-16-my-change/`\n"
        )
        repo = _make_repo(self.tmpdir, decisions_index=index)
        _make_archive_dir(repo, "2026-06-16-my-change")
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    def test_registry_dangling_pointer_fails(self):
        """A pointer to a non-existing directory fails."""
        index = (
            "# Decisions Registry\n\n"
            "- **2026-06-16** · missing-change · the rationale "
            "→ `openspec/changes/archive/2026-06-16-missing-change/`\n"
        )
        repo = _make_repo(self.tmpdir, decisions_index=index)
        # Do NOT create the archive directory — it's dangling.
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 2)

    def test_registry_malformed_line_fails(self):
        """A date-anchored line that is not a valid registry entry fails."""
        # Matches the anchor but has only 2 parts, not 3.
        index = (
            "# Decisions Registry\n\n"
            "- **2026-06-16** · only-two-parts\n"
        )
        repo = _make_repo(self.tmpdir, decisions_index=index)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 2)

    def test_registry_malformed_text_not_pointer_or_inline_fails(self):
        """A date-anchored line whose text is neither [inline] nor → pointer fails."""
        index = (
            "# Decisions Registry\n\n"
            "- **2026-06-16** · my-slug · some free-form text with no pointer\n"
        )
        repo = _make_repo(self.tmpdir, decisions_index=index)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 2)

    def test_registry_non_date_bullets_excluded(self):
        """Lines without the date-bullet anchor are excluded from the check."""
        # These format-doc bullets look like list items but lack a bolded ISO date.
        index = (
            "# Decisions Registry\n\n"
            "One line per decision. Format:\n"
            "- Pointer: `- **YYYY-MM-DD** · <slug> · <essence> → `path/`\n"
            "- Inline (no archive): `- **YYYY-MM-DD** · <slug> · [inline] ...\n"
            "\n"
            "---\n"
            "\n"
            "- **2026-06-13** · good-slug · [inline] all state in tracked files\n"
        )
        repo = _make_repo(self.tmpdir, decisions_index=index)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    def test_registry_multiple_entries_one_dangling_fails(self):
        """Multiple entries where one has a dangling pointer => fail."""
        index = (
            "# Decisions Registry\n\n"
            "- **2026-06-13** · inline-ok · [inline] fine\n"
            "- **2026-06-16** · real-change · good pointer "
            "→ `openspec/changes/archive/2026-06-16-real-change/`\n"
            "- **2026-06-17** · bad-change · dangling pointer "
            "→ `openspec/changes/archive/2026-06-17-bad-change/`\n"
        )
        repo = _make_repo(self.tmpdir, decisions_index=index)
        _make_archive_dir(repo, "2026-06-16-real-change")
        # 2026-06-17-bad-change directory intentionally not created
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 2)

    def test_registry_combined_status_and_decisions_both_fail(self):
        """STATUS over cap + dangling pointer => violations, exit 2."""
        status = (
            "# Status\n\n"
            "## Latest change — one\nbody1\n"
            "## Prior change — two\nbody2\n"
            "## Prior change — three\nbody3\n"
            "## Even older change\nbody4\n"
        )
        index = (
            "# Decisions Registry\n\n"
            "- **2026-06-16** · missing-arc · rationale "
            "→ `openspec/changes/archive/2026-06-16-missing-arc/`\n"
        )
        repo = _make_repo(self.tmpdir, status_md=status, decisions_index=index)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 2)


# ===================================================================
# Helper unit tests
# ===================================================================


class HelperTest(unittest.TestCase):
    """Direct tests for status_lint helper functions."""

    def test_word_count_empty(self):
        self.assertEqual(status_lint._word_count(""), 0)

    def test_word_count_simple(self):
        self.assertEqual(status_lint._word_count("hello world"), 2)

    def test_word_count_extra_whitespace(self):
        self.assertEqual(status_lint._word_count("  hello   world  "), 2)

    def test_remove_fenced_code_blocks_basic(self):
        text = "before\n```\ninside\n```\nafter"
        result = status_lint._remove_fenced_code_blocks(text)
        self.assertEqual(result, "before\nafter")

    def test_remove_fenced_code_blocks_no_fence(self):
        text = "no fence here"
        result = status_lint._remove_fenced_code_blocks(text)
        self.assertEqual(result, text)

    def test_normalize_heading(self):
        result = status_lint._normalize_heading("## Latest change — Foo")
        self.assertEqual(result, "latest change — foo")

    def test_normalize_heading_extra_spaces(self):
        result = status_lint._normalize_heading("##  Hello   World ")
        self.assertEqual(result, "hello world")

    def test_split_sections_preamble_and_sections(self):
        text = "preamble\n\n## H1\nbody1\nline2\n## H2\nbody2"
        preamble, sections = status_lint._split_sections(text)
        self.assertEqual(preamble, "preamble")
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0][0], "## H1")
        self.assertEqual(sections[0][1], "body1\nline2")
        self.assertEqual(sections[1][0], "## H2")
        self.assertEqual(sections[1][1], "body2")

    def test_split_sections_no_preamble(self):
        text = "## H1\nbody\n## H2\nbody2"
        preamble, sections = status_lint._split_sections(text)
        self.assertEqual(preamble, "")
        self.assertEqual(len(sections), 2)

    def test_split_sections_only_preamble(self):
        text = "just a preamble without any headings"
        preamble, sections = status_lint._split_sections(text)
        self.assertEqual(preamble, "just a preamble without any headings")
        self.assertEqual(len(sections), 0)


if __name__ == "__main__":
    unittest.main()
