#!/usr/bin/env python3
"""Check total byte size of the mandatory boot-read file set.

The boot surface is the set of files unconditionally scanned at the start
of every session.  AGENTS.md states "the boot set is a fixed budget, not a
growing list."  This script mechanizes that rule by measuring the aggregate
byte size and reporting a three-way verdict.

File set (fixed):
  - AGENTS.md
  - knowledge/STATUS.md
  - knowledge/questions/INDEX.md
  - knowledge/decisions/INDEX.md

A missing file is silently skipped (contributes 0 bytes, NOT an error).

Exit codes
----------
0  — total < WARN threshold (clean, under budget).
1  — WARN threshold <= total < FAIL threshold (advisory, non-blocking).
2  — total >= FAIL threshold (blocking — boot surface over budget).

Usage
-----
    python scripts/boot_surface_lint.py [repo_root]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BOOT_FILES = (
    "AGENTS.md",
    "knowledge/STATUS.md",
    "knowledge/questions/INDEX.md",
    "knowledge/decisions/INDEX.md",
)

WARN_BYTES = 80_000
FAIL_BYTES = 100_000


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Run the boot-surface lint and return an exit code.

    Parameters
    ----------
    argv
        Optional argument list (defaults to sys.argv[1:]).

    Returns
    -------
    int
        0 (clean), 1 (WARN), or 2 (FAIL).
    """
    parser = argparse.ArgumentParser(
        description="Check total byte size of the mandatory boot-read file set."
    )
    parser.add_argument(
        "repo_root",
        nargs="?",
        default=None,
        help="Repository root (default: parent of script directory)",
    )
    args = parser.parse_args(argv)

    if args.repo_root is not None:
        repo_root = Path(args.repo_root).resolve(strict=True)
    else:
        repo_root = Path(__file__).resolve().parent.parent

    total = 0
    lines: list[str] = []

    for rel_path in BOOT_FILES:
        full_path = repo_root / rel_path
        if full_path.exists():
            size = full_path.stat().st_size
            total += size
            lines.append(f"  {rel_path}: {size}")

    lines.append(f"total: {total}")

    if total >= FAIL_BYTES:
        lines.append(f"boot_surface_lint: FAIL — {total} bytes exceeds {FAIL_BYTES}")
        print("\n".join(lines))
        return 2
    elif total >= WARN_BYTES:
        lines.append(f"boot_surface_lint: WARN — {total} bytes (threshold >= {WARN_BYTES})")
        print("\n".join(lines))
        return 1
    else:
        lines.append(f"boot_surface_lint: OK — {total} bytes")
        print("\n".join(lines))
        return 0


if __name__ == "__main__":
    sys.exit(main())
