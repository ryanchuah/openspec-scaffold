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

Per-repo thresholds
-------------------
The WARN and FAIL thresholds may be overridden per-repo via a
``[boot_surface_lint]`` table in the repo-root ``checks.toml``::

    [boot_surface_lint]
    warn_bytes = 100000
    fail_bytes = 120000

Absent file / absent section / absent key falls back to the module-level
defaults (``WARN_BYTES=80000``, ``FAIL_BYTES=100000``).  If a value is not a
non-negative integer, or ``warn_bytes > fail_bytes``, the overrides are
silently ignored and the module defaults are used (one line is printed to
stderr explaining the fallback).

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
import tomllib
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
# Per-repo config
# ---------------------------------------------------------------------------


def _load_config(root: Path) -> dict:
    """Load ``[boot_surface_lint]`` from repo-root ``checks.toml``.

    Returns a dict with keys ``warn_bytes`` (default ``WARN_BYTES``) and
    ``fail_bytes`` (default ``FAIL_BYTES``).  Invalid values (negative,
    non-integer, or ``warn_bytes > fail_bytes``) cause a fallback to the
    module-level defaults, with a one-line explanation written to stderr.
    """
    cfg: dict = {}
    config_path = root / "checks.toml"
    if config_path.is_file():
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        cfg = data.get("boot_surface_lint", {})

    warn = cfg.get("warn_bytes", WARN_BYTES)
    fail = cfg.get("fail_bytes", FAIL_BYTES)

    # Validate types — must be int (not a float, str, etc.).
    if not isinstance(warn, int) or not isinstance(fail, int):
        print(
            "boot_surface_lint: [boot_surface_lint] warn_bytes / fail_bytes must be"
            " integers — falling back to defaults",
            file=sys.stderr,
        )
        return {"warn_bytes": WARN_BYTES, "fail_bytes": FAIL_BYTES}

    # Validate range — must be non-negative.
    if warn < 0 or fail < 0:
        print(
            "boot_surface_lint: [boot_surface_lint] warn_bytes / fail_bytes must be"
            " non-negative — falling back to defaults",
            file=sys.stderr,
        )
        return {"warn_bytes": WARN_BYTES, "fail_bytes": FAIL_BYTES}

    # Validate ordering.
    if warn > fail:
        print(
            "boot_surface_lint: [boot_surface_lint] warn_bytes must not exceed"
            " fail_bytes — falling back to defaults",
            file=sys.stderr,
        )
        return {"warn_bytes": WARN_BYTES, "fail_bytes": FAIL_BYTES}

    return {"warn_bytes": warn, "fail_bytes": fail}


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

    config = _load_config(repo_root)
    warn_bytes = config["warn_bytes"]
    fail_bytes = config["fail_bytes"]

    total = 0
    lines: list[str] = []

    for rel_path in BOOT_FILES:
        full_path = repo_root / rel_path
        if full_path.exists():
            size = full_path.stat().st_size
            total += size
            lines.append(f"  {rel_path}: {size}")

    lines.append(f"total: {total}")

    if total >= fail_bytes:
        lines.append(f"boot_surface_lint: FAIL — {total} bytes exceeds {fail_bytes}")
        print("\n".join(lines))
        return 2
    elif total >= warn_bytes:
        lines.append(f"boot_surface_lint: WARN — {total} bytes (threshold >= {warn_bytes})")
        print("\n".join(lines))
        return 1
    else:
        lines.append(f"boot_surface_lint: OK — {total} bytes")
        print("\n".join(lines))
        return 0


if __name__ == "__main__":
    sys.exit(main())
