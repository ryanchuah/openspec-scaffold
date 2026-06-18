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
    decisions_md: str | None = None,
) -> Path:
    """Create a temporary repo and write optional STATUS.md / decisions.md."""
    repo = tmpdir / "repo"
    repo.mkdir()
    if status_md is not None:
        (repo / "STATUS.md").write_text(status_md, encoding="utf-8")
    if decisions_md is not None:
        ai_docs = repo / "ai-docs"
        ai_docs.mkdir(parents=True, exist_ok=True)
        (ai_docs / "decisions.md").write_text(decisions_md, encoding="utf-8")
    return repo


def _n_words(n: int) -> str:
    """Return *n* space-separated single-letter tokens (e.g. ``"w0 w1 w2"``)."""
    return " ".join(f"w{i}" for i in range(n))


# ===================================================================
# Tests
# ===================================================================


class StatusLintTest(unittest.TestCase):
    """Coverage items from task 2.2 — cap count, word budget, decisions, etc."""

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
    # decisions.md — Date / Status / word budget
    # ------------------------------------------------------------------

    def test_decisions_date_no_status_fails(self):
        """Entry with **Date:** but no **Status:** => violation."""
        decisions = (
            "## add-foo: new feature\n"
            "**Date:** 2026-06-18\n"
            "Some description.\n"
        )
        repo = _make_repo(self.tmpdir, decisions_md=decisions)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 2)

    def test_decisions_date_and_status_passes(self):
        """Entry with both **Date:** and **Status:** => pass."""
        decisions = (
            "## add-foo: new feature\n"
            "**Date:** 2026-06-18\n"
            "**Status:** ACTIVE\n"
            "Some description.\n"
        )
        repo = _make_repo(self.tmpdir, decisions_md=decisions)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    def test_decisions_change_record_over_300_fails(self):
        """A fix-/add-/tune- entry with Date+Status and >300 words => fail."""
        decisions = (
            "## add-foo: large entry\n"
            "**Date:** 2026-06-18\n"
            "**Status:** ACTIVE\n"
            + _n_words(301)
            + "\n"
        )
        repo = _make_repo(self.tmpdir, decisions_md=decisions)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 2)

    def test_decisions_non_change_record_no_300_cap(self):
        """Non-change-record heading with >300 words => pass (no 300-cap)."""
        decisions = (
            "## Some prose heading\n"
            "**Date:** 2026-06-18\n"
            "**Status:** ACTIVE\n"
            + _n_words(500)
            + "\n"
        )
        repo = _make_repo(self.tmpdir, decisions_md=decisions)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    def test_decisions_no_date_legacy_skip(self):
        """Entry without **Date:** is skipped even with 500 words."""
        decisions = (
            "## old-legacy-entry\n"
            + _n_words(500)
            + "\n"
        )
        repo = _make_repo(self.tmpdir, decisions_md=decisions)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    # ------------------------------------------------------------------
    # Backfill-safety (legacy/template skipped)
    # ------------------------------------------------------------------

    def test_backfill_date_before_since_skipped(self):
        """Entry dated before --since with no Status and 500w => pass (legacy skip)."""
        decisions = (
            "## add-foo: pre-rule\n"
            "**Date:** 2026-06-13\n"
            + _n_words(500)
            + "\n"
        )
        repo = _make_repo(self.tmpdir, decisions_md=decisions)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    def test_backfill_template_date_skipped(self):
        """Entry with **Date:** YYYY-MM-DD (unparseable template) => pass (skipped)."""
        decisions = (
            "## template-entry\n"
            "**Date:** YYYY-MM-DD\n"
            + _n_words(500)
            + "\n"
        )
        repo = _make_repo(self.tmpdir, decisions_md=decisions)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    def test_backfill_since_override_brings_in_scope(self):
        """--since 2026-06-13 brings 2026-06-13 entry in-scope => fail."""
        decisions = (
            "## add-foo: in-scope\n"
            "**Date:** 2026-06-13\n"
            + _n_words(500)
            + "\n"
        )
        repo = _make_repo(self.tmpdir, decisions_md=decisions)
        rc = status_lint.main(["--since", "2026-06-13", str(repo)])
        self.assertEqual(rc, 2)

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
    # Combined decisions violations
    # ------------------------------------------------------------------

    def test_combined_decisions_violations(self):
        """add-foo with Date, no Status, >300 words => 2 violations."""
        decisions = (
            "## add-foo: combined violation\n"
            "**Date:** 2026-06-18\n"
            + _n_words(301)
            + "\n"
        )
        repo = _make_repo(self.tmpdir, decisions_md=decisions)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 2)

    # ------------------------------------------------------------------
    # Graceful absence
    # ------------------------------------------------------------------

    def test_graceful_absence_both_missing(self):
        """No STATUS.md and no decisions.md => exit 0."""
        repo = _make_repo(self.tmpdir)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)

    def test_asymmetric_absence(self):
        """STATUS present, decisions absent => decisions skipped, no error."""
        status = "# Status\n\n## Latest change — one\nbody\n"
        repo = _make_repo(self.tmpdir, status_md=status)
        rc = status_lint.main([str(repo)])
        self.assertEqual(rc, 0)


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
