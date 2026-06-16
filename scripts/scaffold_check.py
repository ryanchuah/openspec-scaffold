#!/usr/bin/env python3
"""Pre-commit guard for scaffold-managed files (Claude Code PreToolUse hook).

Coverage limitation (M1)
------------------------
This guard is a Claude Code ``PreToolUse`` hook that intercepts commits Claude
makes through its Bash tool. It does **not** cover:

* Operator-terminal commits (``git commit`` typed by a human).
* Commits made by an ``opencode`` / DeepSeek executor (which run outside the
  Claude Code harness).
* ``git commit --no-verify`` (the sanctioned escape for deliberate
  scaffold-managed edits — e.g. reverse-promoting an improvement back to
  scaffold, or applying a new sync).

A repo-wide ``core.hooksPath`` / ``.git/hooks/pre-commit`` was considered and
rejected for W1: it adds a per-repo install step and machinery for a guard
whose purpose is catching Claude's accidental edits, which this already does.

Exit codes
----------
0  — nothing scaffold-managed is staged (allow the commit).
2  — a scaffold-managed file is staged; the commit is **blocked** (exit 2 is
     the only ``PreToolUse`` code that blocks the tool in Claude Code).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    # Resolve the manifest relative to THIS file, not cwd — the prior plan read
    # it relative to cwd, which breaks when the hook fires from a subdirectory.
    # git diff --cached --name-only returns repo-root-relative paths regardless
    # of cwd, so the intersection stays correct as long as the manifest entries
    # are repo-relative.
    manifest = Path(__file__).resolve().parent / "scaffold_manifest.txt"
    with open(manifest) as f:
        managed = {l.strip() for l in f if l.strip() and not l.startswith("#")}

    staged = (
        subprocess.check_output(["git", "diff", "--cached", "--name-only"])
        .decode()
        .split()
    )
    hits = sorted(managed & set(staged))
    if hits:
        print("BLOCKED: scaffold-managed files staged for direct commit:")
        print("\n".join(f"  {f}" for f in hits))
        print(
            "Edit these in openspec-scaffold, "
            "then run scripts/sync_scaffold.py for each repo."
        )
        print(
            "Deliberate scaffold-managed change (e.g. applying a new sync, "
            "or reverse-promoting an"
        )
        print("improvement back to scaffold): git commit --no-verify.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
