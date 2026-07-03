#!/usr/bin/env python3
"""Tests that .claude/ and .opencode/ executor agent bodies agree on shared content.

For each executor pair (apply-executor, archive-executor):
- Strip YAML frontmatter (everything between leading --- markers).
- Normalize away the one sanctioned divergence: the .claude/ intro sentence carries
  "(the Claude Code counterpart of the OpenCode `@<role>`)" which the .opencode/ version
  omits. Strip that clause from the .claude/ body before comparing.
- Assert the remainder is byte-identical. The test FAILS when the two bodies drift
  on any non-intro line.

Run with: python3 scripts/test_executor_body_agreement.py
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(os.path.abspath(__file__)).resolve().parent.parent

EXECUTOR_PAIRS: list[tuple[str, Path, Path]] = [
    (
        "apply-executor",
        REPO_ROOT / ".claude" / "agents" / "apply-executor.md",
        REPO_ROOT / ".opencode" / "agents" / "apply-executor.md",
    ),
    (
        "archive-executor",
        REPO_ROOT / ".claude" / "agents" / "archive-executor.md",
        REPO_ROOT / ".opencode" / "agents" / "archive-executor.md",
    ),
]

# Regex to strip "(the Claude Code counterpart of the OpenCode `@<role>`)" from the
# .claude/ intro line. The clause spans one or two lines (a newline may appear
# between "the" and "OpenCode"), so use `\s+` to handle the line break.
_INTRO_CLAUSE_RE = re.compile(r"\s*\(the Claude Code counterpart of the\s+OpenCode `@[\w-]+`\)")


def read_and_strip_frontmatter(path: Path) -> str:
    """Read a markdown agent file and return its body after YAML frontmatter.

    Frontmatter is delimited by a leading --- line and a closing --- line.
    If the file does not start with ---, the whole content is returned.
    """
    content = path.read_text()
    lines = content.splitlines(keepends=True)

    if not lines or lines[0].strip() != "---":
        return content

    # Find closing ---
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        # Malformed frontmatter — return everything
        return content

    return "".join(lines[end_idx + 1 :])


def normalize_intro(body: str) -> str:
    """Remove the sanctioned divergence clause from the body.

    The .claude/ body contains "(the Claude Code counterpart of the OpenCode `@<role>`)"
    after the first sentence. Normalization strips it so the body becomes directly comparable
    to the .opencode/ version.
    """
    return _INTRO_CLAUSE_RE.sub("", body)


# ===================================================================
# Tests
# ===================================================================


class ExecutorBodyAgreementTest(unittest.TestCase):
    """Each .claude/ agent body must agree with its .opencode/ counterpart."""

    def _assert_pair_agrees(self, name: str, claude_path: Path, opencode_path: Path):
        self.assertTrue(
            claude_path.exists(),
            f"Missing .claude agent file: {claude_path}",
        )
        self.assertTrue(
            opencode_path.exists(),
            f"Missing .opencode agent file: {opencode_path}",
        )

        claude_body = read_and_strip_frontmatter(claude_path)
        opencode_body = read_and_strip_frontmatter(opencode_path)

        claude_normalized = normalize_intro(claude_body)
        opencode_normalized = normalize_intro(opencode_body)

        # Show a diff context hint if they differ
        self.assertEqual(
            claude_normalized,
            opencode_normalized,
            f"\n\n--- {name}: .claude/ body (intro-normalized) differs from .opencode/ ---\n"
            f"  .claude: {claude_path}\n"
            f"  .opencode: {opencode_path}\n"
            f"  Hint: only the '(the Claude Code counterpart…)' clause is a sanctioned divergence.",
        )

    def test_apply_executor_agrees(self):
        self._assert_pair_agrees("apply-executor", *EXECUTOR_PAIRS[0][1:])

    def test_archive_executor_agrees(self):
        self._assert_pair_agrees("archive-executor", *EXECUTOR_PAIRS[1][1:])


if __name__ == "__main__":
    unittest.main()
