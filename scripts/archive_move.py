#!/usr/bin/env python3
"""archive_move.py — deterministic change-dir move with a conflict guard.

Usage::

    archive_move.py --change-root <dir> --archive-path <dir>

- Asserts the source exists (else exit 2, nothing moved).
- Asserts the destination does NOT exist (conflict → exit 2, nothing moved).
- Creates the archive parent directory (``mkdir -p``).
- Moves the directory via ``shutil.move``.
- Prints a one-line result.
- Exit 0 on success.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Move a change directory to its archive path with a conflict guard."
    )
    parser.add_argument(
        "--change-root",
        required=True,
        help="Path to the change directory to move",
    )
    parser.add_argument(
        "--archive-path",
        required=True,
        help="Target archive path",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    src = Path(args.change_root)
    dst = Path(args.archive_path)

    if not src.is_dir():
        print(f"archive_move: source not found: {src}", file=sys.stderr)
        return 2

    if dst.exists():
        print(f"archive_move: destination already exists: {dst}", file=sys.stderr)
        return 2

    # Create the destination parent
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Move
    shutil.move(str(src), str(dst))

    print(f"Moved {src} → {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
