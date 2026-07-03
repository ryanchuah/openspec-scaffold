#!/usr/bin/env python3
"""Live-tree doc-lint gate: runs knowledge_lint and status_lint against the
real repo root.

Mirrors the real-root pattern from scripts/test_scaffold_lint.py.  Any drift
introduced into a knowledge doc, a broken citation, a root-handoff file, or a
STATUS.md / decisions/INDEX.md invariant violation will turn the suite red.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import knowledge_lint  # noqa: E402
import status_lint  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_knowledge_lint_live_tree_clean():
    """knowledge_lint against the real repo root reports zero findings."""
    findings = knowledge_lint.collect_findings(REPO_ROOT)
    assert findings == [], "\n".join(str(f) for f in findings)


def test_status_lint_live_tree_clean():
    """status_lint against the real repo root exits 0 (no violations)."""
    exit_code = status_lint.main([str(REPO_ROOT)])
    assert exit_code == 0
