#!/usr/bin/env python3
"""Linter for STATUS.md and ai-docs/decisions.md mechanical invariants.

Enforces the bounds specified in
AGENTS.md §"State, write discipline, and the archive-as-handoff rule":

  - STATUS.md: at most 3 change-entry sections, each <=150 words.
  - ai-docs/decisions.md: dated entries must have **Status:**;
    change-record entries (fix-*/add-*/tune-* heading prefix) capped
    at 300 body words.
  - Enforcement applies only to entries whose **Date:** parses as a
    real date on/after --since (default: 2026-06-18, the adoption date
    of the decisions-entry rule).  Entries with no Date, an unparseable
    Date, or a Date before --since are skipped — no retroactive backfill.

Exit codes
-----------
0  — all clean.
2  — one or more hard violations.

Usage
-----
    python scripts/status_lint.py [repo_root]
    python scripts/status_lint.py --since YYYY-MM-DD [repo_root]

--since enforces decisions.md checks only on entries dated on/after
the given date (default: 2026-06-18).
"""

from __future__ import annotations

import argparse
import datetime
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

# Matches change-record heading prefixes exactly as named in AGENTS.md:
# fix-*, add-*, tune-*.  Applied against the normalized (lowercased) heading.
_CHANGE_RECORD_RE = re.compile(r"^(fix|add|tune)-")


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


def _parse_entry_date(body: str) -> datetime.date | None:
    """Extract and parse ``**Date:** YYYY-MM-DD`` from entry *body*.

    Returns ``None`` if the Date line is missing, if the value does not
    parse as a real date (e.g. the template placeholder ``YYYY-MM-DD``),
    or if the value is not a valid ISO date.
    """
    m = re.search(r"\*\*Date:\*\*\s*(\S+)", body)
    if not m:
        return None
    date_str = m.group(1)
    # Reject the template placeholder itself
    if date_str == "YYYY-MM-DD":
        return None
    try:
        return datetime.date.fromisoformat(date_str)
    except ValueError:
        return None


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
    """Check STATUS.md invariants.  Returns list of violation strings."""
    status_path = repo_root / "STATUS.md"
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
            f"  STATUS.md: {len(change_entries)} change-entries (max 3); "
            f"excess: {', '.join(excess_headings)}"
        )

    # C2 — per-entry word budget (max 150 words)
    for heading, body, _norm in change_entries:
        body_clean = _remove_fenced_code_blocks(body)
        wc = _word_count(body_clean)
        if wc > 150:
            violations.append(
                f"  STATUS.md: {heading} body has {wc} words (max 150)"
            )

    return violations


def _check_decisions_md(
    repo_root: Path, since_date: datetime.date
) -> list[str]:
    """Check ai-docs/decisions.md invariants.

    Only enforces on entries whose ``**Date:**`` value parses as a real
    date on or after *since_date* — entries with no Date line, an
    unparseable Date, or a Date before *since_date* are skipped (no
    retroactive backfill).
    Returns list of violation strings.
    """
    decisions_path = repo_root / "ai-docs" / "decisions.md"
    if not decisions_path.exists():
        return []

    text = decisions_path.read_text(encoding="utf-8")
    _preamble, entries = _split_sections(text)

    violations: list[str] = []

    for heading, body in entries:
        body_clean = _remove_fenced_code_blocks(body)

        # Determine whether this entry is in-scope by parsing its date.
        entry_date = _parse_entry_date(body_clean)
        if entry_date is None or entry_date < since_date:
            continue  # legacy / template / pre-since — skip

        has_status = "**Status:**" in body_clean
        if not has_status:
            violations.append(
                f"  ai-docs/decisions.md: entry \"{heading}\" is missing "
                "**Status:**"
            )

        norm = _normalize_heading(heading)
        if _CHANGE_RECORD_RE.match(norm):
            wc = _word_count(body_clean)
            if wc > 300:
                violations.append(
                    f"  ai-docs/decisions.md: entry \"{heading}\" body has "
                    f"{wc} words (max 300)"
                )

    return violations


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lint STATUS.md and ai-docs/decisions.md invariants."
    )
    parser.add_argument(
        "repo_root",
        nargs="?",
        default=None,
        help="Repository root (default: parent of script directory)",
    )
    parser.add_argument(
        "--since",
        default="2026-06-18",
        help="Enforce decisions.md checks only on entries dated on/after "
        "this date (default: 2026-06-18)",
    )
    args = parser.parse_args(argv)

    since_date = datetime.date.fromisoformat(args.since)

    if args.repo_root is not None:
        repo_root = Path(args.repo_root).resolve(strict=True)
    else:
        repo_root = Path(__file__).resolve().parent.parent

    print(f"status_lint: checking {repo_root}")

    total_violations: list[str] = []

    # STATUS.md
    status_violations = _check_status_md(repo_root)
    status_path = repo_root / "STATUS.md"
    if status_path.exists():
        if status_violations:
            print("STATUS.md: FAIL")
            for v in status_violations:
                print(v)
            total_violations.extend(status_violations)
        else:
            print("STATUS.md: OK")

    # ai-docs/decisions.md
    decisions_violations = _check_decisions_md(repo_root, since_date)
    decisions_path = repo_root / "ai-docs" / "decisions.md"
    if decisions_path.exists():
        if decisions_violations:
            print("ai-docs/decisions.md: FAIL")
            for v in decisions_violations:
                print(v)
            total_violations.extend(decisions_violations)
        else:
            print("ai-docs/decisions.md: OK")

    if total_violations:
        print(f"status_lint: FAILED — {len(total_violations)} violation(s)")
        return 2
    else:
        print("status_lint: OK")
        return 0


if __name__ == "__main__":
    sys.exit(main())
