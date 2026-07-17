#!/usr/bin/env python3
"""roll_decisions.py — roll the oldest knowledge/decisions/INDEX.md entries into HISTORY.md.

Convention (see knowledge/README.md): `knowledge/decisions/INDEX.md` holds only
the newest tail of the decisions registry (byte-budgeted, default 16,000 bytes
via the `decisions-index-budget` `knowledge_lint.py` check); older entries move
verbatim, oldest first, to `knowledge/decisions/HISTORY.md`, which is never
part of the mandatory boot-read set and is loaded on demand only (grep
`knowledge/decisions/` when history matters).

An **entry block** is a line matching the registry date-bullet anchor
``^- **YYYY-MM-DD**`` (byte-for-byte the same pattern as
`status_lint._DATE_ANCHOR_RE`) plus every following line up to the next
anchor line or EOF — single-line entries are the norm today, but a
multi-line entry's continuation lines always travel with their anchor. The
**header** is everything in INDEX.md before the first anchor line, and
always stays in INDEX.md.

Entries are appended to INDEX.md in chronological order — oldest directly
after the header, newest at EOF — so the oldest entry blocks sit nearest the
top of the entry list. Those are rolled out first, and appended verbatim, in
order, at the end of HISTORY.md (creating it with a short header if absent).
Because rolls always take INDEX's oldest remaining entries, appending at
HISTORY's end preserves global chronological order across both files by
construction.

When a roll happens, INDEX.md's header gains a standing pointer line to
HISTORY.md (inserted once, immediately after the header's closing `---`
separator, or appended as the last header line when no such separator
exists) — idempotent, never duplicated on re-runs.

Safety invariants (enforced before any write; abort with a message and exit
2 rather than write anything if violated):
  - INDEX.md has at least one anchor line.
  - Byte conservation — re-joining the original header with the rolled and
    retained entry blocks, in original file order, reproduces INDEX.md's
    original text exactly (a string comparison performed before any write).
  - Both files are written only after both new contents are fully computed.

INDEX.md is never emptied: at least one entry block always stays, even if a
single remaining entry alone exceeds the target byte size.

Usage
-----
    python scripts/roll_decisions.py [repo_root] [--target-bytes N] [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Hysteresis target: how small a roll shrinks INDEX.md to, so routine archive
# appends do not immediately re-trip the (larger) knowledge_lint budget.
TARGET_BYTES = 12_000

# Byte-for-byte the same pattern as status_lint._DATE_ANCHOR_RE.
_DATE_ANCHOR_RE = re.compile(r"^- \*\*(\d{4}-\d{2}-\d{2})\*\*")

_POINTER_LINE = "Older entries: `knowledge/decisions/HISTORY.md` (rolled, load on demand)."

_HISTORY_HEADER = (
    "# Decisions Registry — history\n"
    "\n"
    "Rolled verbatim from `INDEX.md`, same format, oldest first, never "
    "boot-loaded — grep `knowledge/decisions/` on demand.\n"
    "\n"
    "---\n"
    "\n"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _byte_len(s: str) -> int:
    return len(s.encode("utf-8"))


def _split_header_and_entries(text: str) -> tuple[list[str], list[list[str]]]:
    """Split INDEX.md text into ``(header_lines, entry_blocks)``.

    ``header_lines`` is every line before the first anchor line.
    ``entry_blocks`` is a list of blocks, each a list of lines starting with
    an anchor line up to (excluding) the next anchor line or EOF — the
    trailing block extends to EOF. Returns ``([], [])`` when there is no
    anchor line at all.
    """
    lines = text.splitlines(keepends=True)
    anchor_indices = [i for i, line in enumerate(lines) if _DATE_ANCHOR_RE.match(line)]
    if not anchor_indices:
        return [], []
    header_lines = lines[: anchor_indices[0]]
    entry_blocks: list[list[str]] = []
    for idx, start in enumerate(anchor_indices):
        end = anchor_indices[idx + 1] if idx + 1 < len(anchor_indices) else len(lines)
        entry_blocks.append(lines[start:end])
    return header_lines, entry_blocks


def _pointer_already_present(header_lines: list[str]) -> bool:
    return any(line.rstrip("\n") == _POINTER_LINE for line in header_lines)


def _insert_pointer_line(header_lines: list[str]) -> list[str]:
    """Return a new header-lines list with the pointer line inserted
    immediately after the header's closing ``---`` separator, or appended as
    the last header line when no such separator is present. Assumes the
    pointer line is not already present (callers check via
    ``_pointer_already_present`` first)."""
    for i, line in enumerate(header_lines):
        if line.rstrip("\n") == "---":
            return header_lines[: i + 1] + [_POINTER_LINE + "\n"] + header_lines[i + 1 :]
    return header_lines + [_POINTER_LINE + "\n"]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Roll the oldest knowledge/decisions/INDEX.md entry blocks into "
            "HISTORY.md once INDEX.md exceeds a byte target."
        )
    )
    parser.add_argument(
        "repo_root",
        nargs="?",
        default=None,
        help="Repository root (default: parent of script directory)",
    )
    parser.add_argument(
        "--target-bytes",
        type=int,
        default=TARGET_BYTES,
        help=f"Target max size for INDEX.md after rolling (default: {TARGET_BYTES})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and print the summary; write nothing",
    )
    args = parser.parse_args(argv)

    if args.repo_root is not None:
        repo_root = Path(args.repo_root).resolve(strict=True)
    else:
        repo_root = Path(__file__).resolve().parent.parent

    target_bytes = args.target_bytes
    dry_run = args.dry_run

    index_path = repo_root / "knowledge" / "decisions" / "INDEX.md"
    history_path = repo_root / "knowledge" / "decisions" / "HISTORY.md"

    if not index_path.is_file():
        print(f"roll_decisions: {index_path} does not exist", file=sys.stderr)
        return 2

    original_text = index_path.read_text(encoding="utf-8")
    original_bytes = _byte_len(original_text)

    # Safety invariant (a) — INDEX.md must have at least one anchor line,
    # checked unconditionally (even when the file is small).
    header_lines, entry_blocks = _split_header_and_entries(original_text)
    if not entry_blocks:
        print(
            "roll_decisions: INDEX.md has no registry anchor lines "
            f"(pattern {_DATE_ANCHOR_RE.pattern!r}) — refusing to touch it",
            file=sys.stderr,
        )
        return 2

    if original_bytes <= target_bytes:
        print(
            f"roll_decisions: no-op — INDEX.md is {original_bytes} bytes "
            f"(<= target {target_bytes}); nothing rolled"
        )
        return 0

    n_total = len(entry_blocks)
    block_texts = ["".join(block) for block in entry_blocks]
    block_bytes = [_byte_len(b) for b in block_texts]

    # suffix_bytes[i] = size in bytes of retaining entry_blocks[i:].
    suffix_bytes = [0] * (n_total + 1)
    for i in range(n_total - 1, -1, -1):
        suffix_bytes[i] = suffix_bytes[i + 1] + block_bytes[i]

    header_text = "".join(header_lines)
    pointer_needed = not _pointer_already_present(header_lines)
    header_with_pointer_lines = (
        _insert_pointer_line(header_lines) if pointer_needed else header_lines
    )
    header_with_pointer_text = "".join(header_with_pointer_lines)
    header_with_pointer_bytes = _byte_len(header_with_pointer_text)

    chosen_i = None
    for i in range(1, n_total):
        if header_with_pointer_bytes + suffix_bytes[i] <= target_bytes:
            chosen_i = i
            break
    if chosen_i is None:
        # Maximal rolling still doesn't fit — retain just the newest block
        # (never-empty guard: this is 0 when n_total == 1, i.e. no rolling
        # happens at all).
        chosen_i = n_total - 1

    if chosen_i == 0:
        print(
            f"roll_decisions: no-op — INDEX.md is {original_bytes} bytes "
            f"(> target {target_bytes}) but has only {n_total} entry block(s); "
            "keeping it rather than emptying the live registry"
        )
        return 0

    rolled_blocks = block_texts[:chosen_i]
    retained_blocks = block_texts[chosen_i:]
    rolled_text = "".join(rolled_blocks)
    retained_text = "".join(retained_blocks)

    # Safety invariant (b) — byte conservation: re-joining the ORIGINAL
    # header with rolled-then-retained entry text (original file order)
    # must reproduce INDEX.md's original text exactly, checked as strings
    # before any write.
    reconstructed = header_text + rolled_text + retained_text
    if reconstructed != original_text:
        print(
            "roll_decisions: internal error — byte-conservation check failed; writing nothing",
            file=sys.stderr,
        )
        return 2

    new_index_text = header_with_pointer_text + retained_text
    final_bytes = _byte_len(new_index_text)
    budget_met = final_bytes <= target_bytes

    history_exists = history_path.is_file()
    if history_exists:
        existing_history_text = history_path.read_text(encoding="utf-8")
        new_history_text = existing_history_text + rolled_text
    else:
        new_history_text = _HISTORY_HEADER + rolled_text

    # Both new contents (new_index_text, new_history_text) are now fully
    # computed — safety invariant (c): only write after both are ready.

    n_rolled = chosen_i
    n_retained = n_total - chosen_i

    summary_lines = [
        f"roll_decisions: INDEX.md {original_bytes} -> {final_bytes} bytes (target {target_bytes})",
        f"roll_decisions: {n_total} entries total — {n_rolled} rolled, {n_retained} retained",
        f"roll_decisions: pointer line added: {pointer_needed}",
        f"roll_decisions: HISTORY.md {'created' if not history_exists else 'appended'}",
    ]
    if not budget_met:
        summary_lines.append(
            "roll_decisions: note — could not fully satisfy the target; the "
            f"single retained entry alone is {block_bytes[-1]} bytes, over "
            f"target {target_bytes} (never emptying INDEX.md further)"
        )

    if dry_run:
        summary_lines.append("roll_decisions: --dry-run — nothing written")
        print("\n".join(summary_lines))
        return 0

    index_path.write_text(new_index_text, encoding="utf-8")
    history_path.write_text(new_history_text, encoding="utf-8")

    print("\n".join(summary_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
