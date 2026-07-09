#!/usr/bin/env python3
"""outstanding.py — Gather all configured outstanding-work sources (D1, D3–D6, D8, D10).

Shared gather module: single home of source-enumeration + finding-extraction
logic, consumed by ``facts.py --check outstanding`` via ``_run_delegate``
(checks.py) and by ``knowledge_lint.py``'s ``_check_untriaged_age`` (D8).

CLI
---
``python outstanding.py [--root PATH] [--out PATH]``

Exit codes
----------
0 — always (never non-zero on source content, per fact-family contract).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

GENERATED_BY = "outstanding.py"

# Default config for [facts.outstanding] (D10).
DEFAULT_FINDINGS_GLOBS = ["knowledge/research/**/FINDINGS*.md"]
# Permissive default: uppercase-letter-prefix + optional dash-separated
# tokens + trailing digits.  Repos with a scheme like CA-W\\d+-\\d+ override.
DEFAULT_FINDING_ID_PATTERN = r"\b[A-Z]{2,}(?:-[A-Z0-9]+)?-\d+\b"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def _load_config(config: dict) -> dict:
    """Extract [facts.outstanding] from the full config dict with graceful defaults.

    *config* is the full checks.py config (from checks.toml or {}).
    Returns a dict with ``findings_globs`` and ``finding_id_pattern``.
    """
    fc = config.get("facts", {}).get("outstanding", {})
    return {
        "findings_globs": fc.get("findings_globs", DEFAULT_FINDINGS_GLOBS),
        "finding_id_pattern": fc.get("finding_id_pattern", DEFAULT_FINDING_ID_PATTERN),
    }


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def _git_timestamp(repo_root: Path, path: Path) -> int | None:
    """Git last-commit timestamp (epoch seconds) for *path*.

    Returns None when git is unavailable (no git binary, not a repo, or
    the file is untracked).
    """
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        # Fall back to absolute path if not under repo_root.
        rel = path
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "log", "-1", "--format=%ct", "--", str(rel)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass
    return None


def _age_days(repo_root: Path, path: Path) -> int:
    """Age in days from git last-commit date, falling back to filesystem mtime."""
    ts = _git_timestamp(repo_root, path)
    now = datetime.now(timezone.utc)
    if ts is not None:
        commit_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return max(0, (now - commit_dt).days)
    try:
        mtime = path.stat().st_mtime
        mtime_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
        return max(0, (now - mtime_dt).days)
    except OSError:
        return 0


def _git_tracked(repo_root: Path, path: Path) -> bool:
    """Check if *path* is tracked by git."""
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", str(rel)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _rel(root: Path, path: Path) -> str:
    """Repo-relative string for *path* (falls back to the absolute string when
    *path* is not under *root*)."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Source enumeration
# ---------------------------------------------------------------------------


def _enumerate_questions_index(root: Path) -> list[dict]:
    """Extract structured items from ``knowledge/questions/INDEX.md`` (D3).

    Parses **both** markdown list items (``- `` / ``* `` / ``1. ``) and
    table rows (pipe-delimited, non-header/non-separator), scoped by the
    enclosing ``## Active`` / ``## Parked`` heading.  Each returned item
    carries ``source``, ``line``, ``content``, ``bucket``, and ``section``.
    """
    path = root / "knowledge" / "questions" / "INDEX.md"
    if not path.is_file():
        return []

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [
            {
                "source": _rel(root, path),
                "line": 1,
                "content": f"UNPARSEABLE — read manually: {path} ({exc})",
                "bucket": "triaged",
                "section": None,
            }
        ]

    lines = text.splitlines()
    items: list[dict] = []
    current_section: str | None = None  # "Active" or "Parked"
    in_comment = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Track multi-line HTML comment state.
        if "<!--" in line:
            in_comment = True
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue

        # Track ## section headings.
        heading_m = re.match(r"^##\s+(Active|Parked)\s*$", line)
        if heading_m:
            current_section = heading_m.group(1)
            continue

        if current_section is None:
            continue

        # List item form: bullets (``-`` / ``*``) or numbered (``1.``).
        list_m = re.match(r"^\s*[-*]\s+(.*)", line)
        if not list_m:
            list_m = re.match(r"^\s*\d+\.\s+(.*)", line)
        if list_m:
            content = list_m.group(1).strip()
            if content:
                items.append(
                    {
                        "source": _rel(root, path),
                        "line": i,
                        "content": content,
                        "bucket": "triaged",
                        "section": current_section,
                    }
                )
                continue

        # Table row form: pipe-delimited, non-header/non-separator.
        if "|" in stripped:
            # Separator row: |---|--- (columns of :--- or ---).
            if re.match(r"^\s*\|?\s*:?-{3,}", stripped):
                continue
            # Header row: the row immediately before a separator. `i` is the
            # 1-indexed line number (enumerate(lines, 1)), so the CURRENT
            # line is lines[i - 1] and the NEXT line (0-indexed) is
            # lines[i] — not lines[i + 1], which would look two lines ahead.
            if i < len(lines) and re.match(r"^\s*\|[\s:|]*-{2,}", lines[i]):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            content = " | ".join(cells)
            if content.strip():
                items.append(
                    {
                        "source": _rel(root, path),
                        "line": i,
                        "content": content,
                        "bucket": "triaged",
                        "section": current_section,
                    }
                )

    return items


def _enumerate_tasks(root: Path) -> list[dict]:
    """Extract unchecked ``- [ ]`` items from non-archive ``openspec/changes/*/tasks.md``."""
    items: list[dict] = []
    for path in sorted(Path(root).glob("openspec/changes/*/tasks.md")):
        rel = str(path.relative_to(root))
        if rel.startswith("openspec/changes/archive/"):
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            items.append(
                {
                    "source": _rel(root, path),
                    "line": 1,
                    "content": f"UNPARSEABLE — read manually: {path} ({exc})",
                    "bucket": "triaged",
                }
            )
            continue

        for i, line in enumerate(text.splitlines(), 1):
            m = re.match(r"^\s*-\s+\[\s*]\s+(.*)", line)
            if m:
                content = m.group(1).strip()
                if content:
                    items.append(
                        {
                            "source": _rel(root, path),
                            "line": i,
                            "content": content,
                            "bucket": "triaged",
                        }
                    )
    return items


def _enumerate_roadmap(root: Path) -> list[dict]:
    """Extract non-closed ``## `` entries from ``knowledge/roadmap.md``.

    Skips entries whose heading carries a closed-token (CLOSED, DONE,
    COMPLETE, ✅, ``~~…~~``), matching the D7 closed-token set.
    Multi-line HTML comments are tracked by state (``in_comment``) to
    avoid picking up template examples inside ``<!-- ... -->`` blocks.
    """
    path = root / "knowledge" / "roadmap.md"
    if not path.is_file():
        return []

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [
            {
                "source": _rel(root, path),
                "line": 1,
                "content": f"UNPARSEABLE — read manually: {path} ({exc})",
                "bucket": "triaged",
            }
        ]

    items: list[dict] = []
    in_comment = False

    for i, line in enumerate(text.splitlines(), 1):
        # Track multi-line HTML comment state.
        if "<!--" in line:
            in_comment = True
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue

        m = re.match(r"^##\s+(.+)$", line)
        if not m:
            continue
        title = m.group(1).strip()
        # Skip closed entries per D7 closed-token set.
        if re.search(r"\b(?:CLOSED|DONE|COMPLETE)\b", title, re.IGNORECASE) or "✅" in title:
            continue
        if "~~" in title:
            continue
        items.append(
            {
                "source": _rel(root, path),
                "line": i,
                "content": title,
                "bucket": "triaged",
            }
        )
    return items


def _enumerate_todo_code(root: Path) -> list[dict]:
    """Best-effort scan for TODO/FIXME/HACK/XXX in tracked source files.

    Explicitly lowest-priority / optional per the design non-goal (§Non-Goals).
    Returns an empty list — may be skipped without failing any acceptance criterion.
    """
    # This is deliberately a no-op.  The design says in-code TODO scanning
    # is "optional / lowest-priority" and "may be skipped without failing
    # any acceptance criterion".  Implemented as a function so the gather
    # pipeline clearly accounts for the source slot even when it is empty.
    _ = root
    return []


def _enumerate_prose_files(root: Path) -> list[dict]:
    """Point-only enumeration of prose sources (D6, task 1.3).

    Covers:
    - every ``knowledge/questions/<item>.md`` per-item file (excluding INDEX.md)
    - every ``*.md`` under ``plans/`` (recursive), excluding ``plans/archive/**``

    Each returned item is a point-only entry: file path + first heading +
    git tracked/mtime metadata.  No fabricated line-items.
    """
    items: list[dict] = []

    # knowledge/questions/*.md per-item files (skip INDEX.md — handled separately).
    questions_dir = root / "knowledge" / "questions"
    if questions_dir.is_dir():
        for path in sorted(questions_dir.glob("*.md")):
            if path.name == "INDEX.md":
                continue
            items.append(_point_entry(root, path))

    # plans/ — recursive, excluding plans/archive/.
    plans_dir = root / "plans"
    if plans_dir.is_dir():
        for path in sorted(plans_dir.rglob("*.md")):
            rel = path.relative_to(root)
            if str(rel).startswith("plans/archive/"):
                continue
            if path == plans_dir:
                continue
            items.append(_point_entry(root, path))

    return items


def _first_heading(path: Path) -> str | None:
    """Return the first ``# `` / ``## `` / ``### `` heading in a markdown file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            m = re.match(r"^#{1,3}\s+(.+)$", line.strip())
            if m:
                title = m.group(1).strip()
                title = title.replace("~~", "").strip()
                return title
    except OSError:
        pass
    return None


def _point_entry(root: Path, path: Path) -> dict:
    """Build a point-only entry for *path* (D6)."""
    first_h = _first_heading(path)
    tracked = _git_tracked(root, path)
    mtime: int | None = None
    try:
        mtime = int(path.stat().st_mtime)
    except OSError:
        pass

    status = "tracked" if tracked else "untracked"
    heading_str = first_h or "(no heading)"
    return {
        "source": _rel(root, path),
        "line": 1,
        "content": f"[{status}] {path.name} — {heading_str}",
        "bucket": "triaged",
        "_first_heading": first_h,
        "_tracked": tracked,
        "_mtime": mtime,
    }


# ---------------------------------------------------------------------------
# Finding extraction (D4, D8)
# ---------------------------------------------------------------------------


def extract_untriaged(root: Path, config: dict) -> list[dict]:
    """Extract finding IDs matched by the configured pattern across
    ``findings_globs`` that appear **nowhere** under ``knowledge/questions/``
    (scanning both INDEX.md and every ``*.md`` per-item file).

    Args:
        root: Repository root path.
        config: Full checks.py config dict (``[facts.outstanding]`` subsection
                is extracted internally via ``_load_config``).

    Returns:
        List of ``{"id": str, "file": str, "age_days": int}`` dicts, one per
        untriaged finding, ordered by ID.  An empty list when no findings
        match or the pattern is unparseable (graceful degradation).
    """
    fc = _load_config(config)
    pattern_str = fc["finding_id_pattern"]

    try:
        pattern = re.compile(pattern_str)
    except re.error:
        return []

    # Collect all finding IDs from FINDINGS files.
    findings: dict[str, dict] = {}  # id -> {"id", "file", "age_days"}

    for glob_expr in fc["findings_globs"]:
        for fpath in sorted(Path(root).glob(glob_expr)):
            try:
                text = fpath.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            age = _age_days(root, fpath)
            rel = str(fpath.relative_to(root))
            for m in pattern.finditer(text):
                fid = m.group(0).strip()
                if fid not in findings:
                    findings[fid] = {"id": fid, "file": rel, "age_days": age}

    # Collect all finding IDs referenced in knowledge/questions/.
    questions_ref: set[str] = set()

    idx_path = root / "knowledge" / "questions" / "INDEX.md"
    if idx_path.is_file():
        try:
            text = idx_path.read_text(encoding="utf-8")
            questions_ref.update(m.group(0).strip() for m in pattern.finditer(text))
        except (OSError, UnicodeDecodeError):
            pass

    qdir = root / "knowledge" / "questions"
    if qdir.is_dir():
        for fpath in sorted(qdir.glob("*.md")):
            if fpath.name == "INDEX.md":
                continue
            try:
                text = fpath.read_text(encoding="utf-8")
                questions_ref.update(m.group(0).strip() for m in pattern.finditer(text))
            except (OSError, UnicodeDecodeError):
                pass

    # Untriaged = finding IDs not referenced in questions/.
    return [findings[k] for k in sorted(findings) if k not in questions_ref]


# ---------------------------------------------------------------------------
# Output rendering (D5, task 1.6)
# ---------------------------------------------------------------------------


def _findings_scan_count(root: Path, config: dict) -> tuple[int, int]:
    """Count findings-files-scanned and IDs-matched for the report header."""
    fc = _load_config(config)
    files = 0
    ids = 0
    for glob_expr in fc["findings_globs"]:
        for fpath in sorted(Path(root).glob(glob_expr)):
            files += 1
            try:
                text = fpath.read_text(encoding="utf-8")
                pattern = re.compile(fc["finding_id_pattern"])
                ids += len(pattern.findall(text))
            except (OSError, UnicodeDecodeError, re.error):
                pass
    return files, ids


def _render_md(
    root: Path,
    config: dict,
    open_work: list[dict],
    untriaged: list[dict],
    md_path: Path,
) -> None:
    """Write the human-readable markdown snapshot."""
    fc = _load_config(config)
    files_scanned, ids_matched = _findings_scan_count(root, config)

    lines: list[str] = []
    lines.append("# Outstanding Work Snapshot")
    lines.append("")
    lines.append(f"*Generated by {GENERATED_BY}*")
    lines.append("")

    # Active config (task 1.6).
    lines.append("## Active Config")
    lines.append("")
    lines.append(f"- `findings_globs`: {fc['findings_globs']}")
    lines.append(f"- `finding_id_pattern`: `{fc['finding_id_pattern']}`")
    lines.append(f"- Findings files scanned: {files_scanned}")
    lines.append(f"- Finding IDs matched: {ids_matched}")
    lines.append("")

    # Bucket 1: Open work (triaged).
    lines.append(f"## Open work (triaged) — {len(open_work)} items")
    lines.append("")
    if open_work:
        for item in open_work:
            source = item.get("source", "")
            line_no = item.get("line", 1)
            content = item.get("content", "(empty)")
            # Truncate very long content for readability.
            if len(content) > 200:
                content = content[:200] + "..."
            lines.append(f"- `{source}:{line_no}` — {content}")
    else:
        lines.append("*No open work items found.*")
    lines.append("")

    # Bucket 2: Untriaged (task 1.6).
    if untriaged:
        oldest_age = min(u.get("age_days", 0) for u in untriaged)
        now = datetime.now(timezone.utc)
        oldest_dt = now - timedelta(days=oldest_age)
        oldest_str = oldest_dt.strftime("%Y-%m-%d")
        lines.append(f"## Newly surfaced — untriaged ({len(untriaged)}; oldest {oldest_str})")
    else:
        lines.append("## Newly surfaced — untriaged (0)")
    lines.append("")

    if untriaged:
        for item in untriaged:
            fid = item.get("id", "")
            ffile = item.get("file", "")
            age = item.get("age_days", 0)
            lines.append(f"- `{fid}` in `{ffile}` — {age} days old")
    else:
        lines.append("*No untriaged findings.*")
    lines.append("")

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run(root: Path, config: dict, out_path: Path) -> None:
    """Gather all configured outstanding-work sources and write both output
    artifacts (D5).

    Args:
        root: Repository root path.
        config: Full checks.py config dict (from ``checks.toml`` or ``{}``).
        out_path: Path for the JSON output (e.g. ``output/facts/outstanding.json``).
                  The markdown sibling is derived by swapping the suffix.
    """
    # Gather open work from all triaged sources.
    open_work: list[dict] = []
    open_work.extend(_enumerate_questions_index(root))
    open_work.extend(_enumerate_tasks(root))
    open_work.extend(_enumerate_roadmap(root))
    open_work.extend(_enumerate_todo_code(root))
    open_work.extend(_enumerate_prose_files(root))

    # Gather untriaged findings.
    untriaged = extract_untriaged(root, config)

    # Build JSON payload.
    fc = _load_config(config)
    payload = {
        "generated_by": GENERATED_BY,
        "config": {
            "findings_globs": fc["findings_globs"],
            "finding_id_pattern": fc["finding_id_pattern"],
        },
        "open_work": open_work,
        "untriaged": untriaged,
        "summary": {
            "open_work_count": len(open_work),
            "untriaged_count": len(untriaged),
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Write MD sibling (D5).
    md_path = out_path.with_suffix(".md")
    _render_md(root, config, open_work, untriaged, md_path)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.  Resolves repo root, loads config, calls ``run()``.

    Returns 0 unconditionally (fact-family contract — never non-zero on
    source content).  Callers that need payload counts should parse the
    written JSON artifact.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Outstanding-work gather fact.")
    parser.add_argument(
        "--root",
        default=None,
        help="Repo root (default: auto-detect via git or cwd).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output JSON path (default: <root>/output/facts/outstanding.json).",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    # Resolve repo root (mirrors checks.py _resolve_repo_root).
    if args.root:
        root = Path(args.root)
    else:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                root = Path(result.stdout.strip())
            else:
                root = Path.cwd()
        except OSError:
            root = Path.cwd()

    # Load config (graceful defaults when checks.toml absent — task 1.7).
    config_path = root / "checks.toml"
    config: dict = {}
    if config_path.is_file():
        try:
            with open(config_path, "rb") as f:
                import tomllib

                config = tomllib.load(f)
        except (OSError, ValueError, ImportError):
            pass  # Graceful defaults.

    out_path = Path(args.out) if args.out else root / "output" / "facts" / "outstanding.json"

    run(root, config, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
