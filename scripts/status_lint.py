#!/usr/bin/env python3
"""Linter for memory/STATUS.md and memory/decisions/INDEX.md mechanical invariants.

Enforces the bounds specified in design.md §D-E:

  - memory/STATUS.md: at most 3 change-entry sections, each <=150 words.
  - memory/decisions/INDEX.md: every line matching the date-bullet anchor
    ``^- **YYYY-MM-DD**`` must be a valid registry entry of the form:
      - **YYYY-MM-DD** · <slug> · <one-line essence> → `openspec/changes/archive/<dir>/`
    or:
      - **YYYY-MM-DD** · <slug> · [inline] <short rationale>
    Violations: a malformed date-anchored line, or a pointer that does not
    resolve to an existing directory.  Lines that do NOT match the date-bullet
    anchor (section headers, prose, blank lines, format-doc bullets) are
    excluded from the check.

Exit codes
-----------
0  — all clean.
2  — one or more hard violations.

Usage
-----
    python scripts/status_lint.py [repo_root]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXEMPT_HEADINGS = frozenset({
    "current state",
    "immediate next action",
    "done",
    "pointers",
})

# Anchor: a dash-list item opening with a bolded ISO date.
# Matches lines like: - **2026-06-16** · slug · text
_DATE_ANCHOR_RE = re.compile(r'^- \*\*(\d{4}-\d{2}-\d{2})\*\*')

# Separator used in registry lines (space + U+00B7 MIDDLE DOT + space)
_REGISTRY_SEP = " · "

# Pointer suffix pattern: → `openspec/changes/archive/<dir>/`
_POINTER_RE = re.compile(r'→ `(openspec/changes/archive/[^`]+/)`$')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_heading(heading: str) -> str:
    """Lowercase the heading text, strip '## ' prefix, collapse whitespace."""
    h = heading
    if h.startswith("## "):
        h = h[3:]
    h = h.strip().lower()
    return re.sub(r"\s+", " ", h)


def _remove_fenced_code_blocks(text: str) -> str:
    """Strip fenced code blocks (lines between ``` delimiters, inclusive)."""
    lines = text.split("\n")
    out: list[str] = []
    in_fence = False
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue  # skip fence lines themselves
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def _word_count(text: str) -> int:
    """Return the number of ``\\S+`` tokens in *text*."""
    return len(re.findall(r"\S+", text))


def _split_sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Split markdown text into preamble + list of (heading_line, body).

    Heading detection uses the pattern ``^## `` (``## `` at the start of a
    line).  Everything before the first such heading is the *preamble*.
    """
    lines = text.split("\n")
    preamble_lines: list[str] = []
    sections: list[tuple[str, str]] = []
    current_heading: str | None = None
    current_body: list[str] = []
    in_preamble = True

    for line in lines:
        if line.startswith("## "):
            in_preamble = False
            if current_heading is not None:
                sections.append(
                    (current_heading, "\n".join(current_body).strip())
                )
            current_heading = line
            current_body = []
        elif in_preamble:
            preamble_lines.append(line)
        else:
            current_body.append(line)

    if current_heading is not None:
        sections.append(
            (current_heading, "\n".join(current_body).strip())
        )

    return ("\n".join(preamble_lines).strip(), sections)


# ---------------------------------------------------------------------------
# Checkers
# ---------------------------------------------------------------------------

def _check_status_md(repo_root: Path) -> list[str]:
    """Check memory/STATUS.md invariants.  Returns list of violation strings."""
    status_path = repo_root / "memory" / "STATUS.md"
    if not status_path.exists():
        return []

    text = status_path.read_text(encoding="utf-8")
    _preamble, sections = _split_sections(text)

    # Identify change-entry sections (non-exempt headings)
    change_entries: list[tuple[str, str, str]] = []
    for heading, body in sections:
        norm = _normalize_heading(heading)
        if norm in EXEMPT_HEADINGS:
            continue
        change_entries.append((heading, body, norm))

    violations: list[str] = []

    # C1 — cap count (max 3 change-entries)
    if len(change_entries) > 3:
        excess = change_entries[3:]  # beyond the 3 most recent
        excess_headings = [h for h, _b, _n in excess]
        violations.append(
            f"  memory/STATUS.md: {len(change_entries)} change-entries (max 3); "
            f"excess: {', '.join(excess_headings)}"
        )

    # C2 — per-entry word budget (max 150 words)
    for heading, body, _norm in change_entries:
        body_clean = _remove_fenced_code_blocks(body)
        wc = _word_count(body_clean)
        if wc > 150:
            violations.append(
                f"  memory/STATUS.md: {heading} body has {wc} words (max 150)"
            )

    return violations


def _check_decisions_index(repo_root: Path) -> list[str]:
    """Check memory/decisions/INDEX.md registry invariants.

    Every line matching the date-bullet anchor ``^- **YYYY-MM-DD**`` must be
    a valid registry entry with a resolving pointer or an ``[inline]``
    rationale.  All other lines are ignored.
    Returns list of violation strings.
    """
    decisions_path = repo_root / "memory" / "decisions" / "INDEX.md"
    if not decisions_path.exists():
        return []

    text = decisions_path.read_text(encoding="utf-8")
    violations: list[str] = []

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip()

        # Only examine lines that match the date-bullet anchor.
        if not _DATE_ANCHOR_RE.match(line):
            continue

        # Split into date, slug, text — maxsplit=2 so text may contain the sep.
        parts = line.split(_REGISTRY_SEP, 2)
        if len(parts) != 3:
            violations.append(
                f"  memory/decisions/INDEX.md:{lineno}: malformed registry line "
                f"(expected 3 parts separated by ' · '): {line!r}"
            )
            continue

        _date_part, slug_part, text_part = parts

        if not slug_part.strip():
            violations.append(
                f"  memory/decisions/INDEX.md:{lineno}: malformed registry line "
                f"(empty slug): {line!r}"
            )
            continue

        # Valid text: starts with [inline] OR ends with a pointer.
        if text_part.startswith("[inline]"):
            continue  # inline entry — valid

        m = _POINTER_RE.search(text_part)
        if not m:
            violations.append(
                f"  memory/decisions/INDEX.md:{lineno}: malformed registry line "
                f"(text is neither [inline] nor a valid → `pointer`): {line!r}"
            )
            continue

        # Pointer must resolve to an existing directory.
        archive_rel = m.group(1).rstrip("/")
        archive_path = repo_root / archive_rel
        if not archive_path.is_dir():
            violations.append(
                f"  memory/decisions/INDEX.md:{lineno}: dangling pointer "
                f"`{m.group(1)}` does not resolve to an existing directory"
            )

    return violations


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lint memory/STATUS.md and memory/decisions/INDEX.md invariants."
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

    print(f"status_lint: checking {repo_root}")

    total_violations: list[str] = []

    # memory/STATUS.md
    status_violations = _check_status_md(repo_root)
    status_path = repo_root / "memory" / "STATUS.md"
    if status_path.exists():
        if status_violations:
            print("memory/STATUS.md: FAIL")
            for v in status_violations:
                print(v)
            total_violations.extend(status_violations)
        else:
            print("memory/STATUS.md: OK")

    # memory/decisions/INDEX.md
    decisions_violations = _check_decisions_index(repo_root)
    decisions_path = repo_root / "memory" / "decisions" / "INDEX.md"
    if decisions_path.exists():
        if decisions_violations:
            print("memory/decisions/INDEX.md: FAIL")
            for v in decisions_violations:
                print(v)
            total_violations.extend(decisions_violations)
        else:
            print("memory/decisions/INDEX.md: OK")

    if total_violations:
        print(f"status_lint: FAILED — {len(total_violations)} violation(s)")
        return 2
    else:
        print("status_lint: OK")
        return 0


if __name__ == "__main__":
    sys.exit(main())
