#!/usr/bin/env python3
"""knowledge_lint.py — stdlib-only, detect-only linter over tracked per-repo knowledge.

Joins the scaffold-managed linter family (`status_lint.py`, `data_lint.py`,
`scaffold_check.py`). Unlike `status_lint.py` it is fundamentally a
filesystem walk — the walk stays **git-optional**: when `<root>` is a git
repository, `git check-ignore` is used to skip git-ignored paths (e.g. a
vendored/ignored reference clone) during the walk; when git is unavailable
(e.g. a synthetic `tmp_path` fixture with no `.git`) nothing is skipped and
the walk behaves exactly as a pure filesystem scan. Either way it is
trivially testable against a synthetic `tmp_path` tree and works identically
in a real repo or a fixture.

Checks (each yields zero or more findings; a finding is
``(check, path, line|None, message)``):

  1. **orphan/duplicate canonical file** — a fixed single-home map
     (``STATUS.md``, ``lessons.md``, ``roadmap.md``, ``audit-log.md`` →
     their ``knowledge/`` homes) flags a canonical basename living outside
     its home, or a second copy of one. ``INDEX.md``/``README.md`` are
     deliberately excluded (multiple legitimate homes). Scans the whole
     ``<root>`` tree (not scoped to ``knowledge/``).
  2. **retired-path token** — per-line substring scan of in-scope knowledge
     markdown for any active retired-path token (built-in defaults, plus an
     optional per-repo `audit.toml` extension — see below). Skips
     ``knowledge/research/`` (period-correct history).
  3. **broken prose path citation** — a backtick-wrapped, repo-relative,
     path-like token (contains a ``/`` or ends in ``.md``; not a URL, not
     an absolute system path) that does not resolve under ``<root>``.
     Skips ``knowledge/research/``. The extraction heuristic additionally
     excludes: tokens with embedded whitespace (a command/prose fragment,
     not a single path), `~`-prefixed home-relative references (absolute,
     like a `/`-rooted path), angle-bracket template placeholders (e.g.
     ``<dir>``, ``<repo>`` — format-doc shape examples, not real paths),
     and glob patterns (containing `*`) — refinements of the "deliberately
     conservative... exact behavior pinned by tests" extraction window
     (design D2), verified live against this scaffold's own knowledge tree.
     **First-segment gate (added at verify — load-bearing false-positive
     control):** a token is only treated as a citation when its first path
     segment is an existing top-level directory under ``<root>``, computed
     dynamically from what exists at ``<root>`` (never hardcoded). This
     rules out bare filenames (``tasks.md``), cross-repo names
     (``extrends/AGENTS.md``), GitHub shorthand (``sst/opencode``), and
     non-path slashy tokens (``WHEN/THEN/AND``), while still flagging a
     genuinely unresolved path under a real top-level dir (``plans/gone/``).
  4. **dangling archive pointer** — an ``openspec/changes/archive/<dir>/``
     reference whose ``<dir>`` does not exist under ``<root>``. A captured
     ``<dir>`` segment containing `<`/`>` (a literal format-doc placeholder,
     not a real directory name) never matches. NOT exempted for
     ``knowledge/research/`` (structural, not prose-content).
  5. **audit-log registry format (guarded)** — if
     ``<root>/knowledge/audit-log.md`` exists, each registry-anchored line
     (``- **YYYY-MM-DD** · ...``) must fully match
     ``- **YYYY-MM-DD** · audit/<date> · <short-sha> · <essence>``; absent
     file → skipped silently.

Checks 2 and 3 scan ``<root>/knowledge/**/*.md`` excluding
``knowledge/research/``; check 4 scans the same corpus WITHOUT that
exclusion; check 5 targets one specific file; check 1 scans ``<root>``.

Per-repo config (D5): an optional repo-root ``audit.toml``
``[knowledge_lint].retired_paths`` array (read via stdlib ``tomllib``) is
MERGED with the built-in retired-path defaults. Absent file/table/key means
only the defaults apply. ``audit.toml`` is per-repo config, never
scaffold-managed.

Detect-only: this script performs **zero filesystem writes** under any flag
or input. Its only effects are the printed report and the process exit code.

Exit codes
----------
0 — no findings.
1 — one or more findings (drift-diagnostic convention, matching
    `sync_scaffold.py --check`'s ``1`` — NOT `status_lint.py`'s ``2`` — so
    "found drift" stays distinct from argparse's own exit-``2`` on a bad
    flag).

Usage
-----
    python scripts/knowledge_lint.py [--root <path>]
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Callable, NamedTuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Fixed single-home canonical basename -> taxonomy home (repo-relative,
# posix form). INDEX.md/README.md are deliberately excluded — multiple
# legitimate homes means a basename match would false-positive.
CANONICAL_MAP: dict[str, str] = {
    "STATUS.md": "knowledge/STATUS.md",
    "lessons.md": "knowledge/lessons.md",
    "roadmap.md": "knowledge/roadmap.md",
    "audit-log.md": "knowledge/audit-log.md",
}

# Built-in default retired-path tokens (the known universal reorg residue).
DEFAULT_RETIRED_PATHS: tuple[str, ...] = (
    "ai-docs/",
    "plans/open-issues.md",
    "docs/reviews/",
)

# Known-ephemeral knowledge paths: legitimately absent in the steady state, so a
# citation to one is NOT a broken citation. knowledge/HANDOFF.md is the sanctioned
# mid-session handoff file (written mid-change, deleted on absorption) — see the
# knowledge taxonomy (knowledge/README.md).
EPHEMERAL_PATHS: tuple[str, ...] = ("knowledge/HANDOFF.md", "knowledge/audit-log.md")

# Content checks (retired-path token, broken citation) exclude this dir —
# period-correct historical analyses legitimately cite pre-restructure
# paths. Mirrors sync_scaffold.py's _REF_SCAN_EXCLUDE treatment of the same
# directory. Structural checks (orphan, dangling-pointer, audit-log) are
# NOT affected.
_RESEARCH_EXCLUDE = "knowledge/research/"

# Directories never worth descending into for the whole-root orphan walk.
_SKIP_DIRS = frozenset({".git"})

_BACKTICK_RE = re.compile(r"`([^`\n]+)`")
_URL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*://")
# Excludes `<`/`>` (template placeholders, e.g. `<dir>`) from the captured
# directory-name segment so a literal format-doc example like
# ``openspec/changes/archive/<dir>/`` — which shows the *shape* of a real
# pointer, not an actual one — never matches (see check-4 rationale below).
_ARCHIVE_POINTER_RE = re.compile(r"openspec/changes/archive/([^`\s)/<>]+)/")
_AUDIT_LOG_ANCHOR_RE = re.compile(r"^- \*\*\d{4}-\d{2}-\d{2}\*\*")
_AUDIT_LOG_FULL_RE = re.compile(
    r"^- \*\*\d{4}-\d{2}-\d{2}\*\* · audit/\d{4}-\d{2}-\d{2} · [0-9a-f]{7,40} · \S.*$"
)


class Finding(NamedTuple):
    check: str
    path: str
    line: int | None
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _relpath(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_research(root: Path, path: Path) -> bool:
    return _RESEARCH_EXCLUDE in _relpath(root, path)


def _knowledge_markdown(root: Path, is_ignored: Callable[[str], bool]) -> list[Path]:
    """All ``<root>/knowledge/**/*.md`` files (includes knowledge/research/),
    skipping any path git-ignores (see ``make_git_ignore_checker``)."""
    knowledge_dir = root / "knowledge"
    if not knowledge_dir.is_dir():
        return []
    results: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(knowledge_dir):
        dirnames[:] = [
            d
            for d in dirnames
            if not is_ignored(_relpath(root, Path(dirpath) / d))
        ]
        for filename in filenames:
            if not filename.endswith(".md"):
                continue
            full = Path(dirpath) / filename
            if is_ignored(_relpath(root, full)):
                continue
            results.append(full)
    return sorted(results)


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _is_url(token: str) -> bool:
    return bool(_URL_RE.match(token))


def _is_absolute_system_path(token: str) -> bool:
    # `~/...` is a home-relative *absolute* reference (tilde expansion),
    # same exclusion rationale as a literal `/`-rooted absolute path.
    return token.startswith("/") or token.startswith("~")


def _is_template_placeholder(token: str) -> bool:
    # Format-doc examples show the *shape* of a citation using angle-bracket
    # variables (`<dir>`, `<repo>`, `<change>`, ...) — never a real path.
    return "<" in token or ">" in token


def _is_glob_pattern(token: str) -> bool:
    # A glob (`checks/*.sql`, `.claude/skills/**`) names a pattern, not a
    # single resolvable path.
    return "*" in token


def _has_whitespace(token: str) -> bool:
    # A single repo-relative path never contains whitespace; a backtick span
    # with embedded spaces is a command/prose fragment, not a citation.
    return any(ch.isspace() for ch in token)


def _is_path_like(token: str) -> bool:
    return "/" in token or token.endswith(".md")


def _top_level_dirs(root: Path) -> set[str]:
    """Existing top-level directory names directly under ``root``, computed
    dynamically (never hardcoded) — the first-segment gate for the
    broken-citation check (design D2 check 3): a backtick token is only a
    candidate citation when its first path segment names a real top-level
    directory here (e.g. ``knowledge``, ``openspec``, ``scripts``,
    ``.claude``, ``.opencode``, ``plans`` — whatever actually exists)."""
    try:
        return {entry.name for entry in root.iterdir() if entry.is_dir()}
    except OSError:
        return set()


# ---------------------------------------------------------------------------
# Git-ignore skip (D2 "Root & enumeration"): git-optional
# ---------------------------------------------------------------------------


def make_git_ignore_checker(root: Path) -> Callable[[str], bool]:
    """Return ``is_ignored(relpath) -> bool`` for repo-relative POSIX paths
    under ``root``.

    When ``root`` is a git repository, this shells out to
    ``git check-ignore`` (memoized per path) so a vendored/git-ignored
    directory (e.g. a local reference clone) is skipped during the walk.
    When git is unavailable or ``root`` is not a git repository (e.g. a
    synthetic `tmp_path` fixture with no ``.git``), the returned callable
    always returns ``False`` — nothing is skipped, keeping the walk
    git-optional (design D2)."""
    try:
        probe = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return lambda relpath: False
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return lambda relpath: False

    @lru_cache(maxsize=None)
    def _is_ignored(relpath: str) -> bool:
        try:
            result = subprocess.run(
                ["git", "-C", str(root), "check-ignore", "-q", relpath],
                capture_output=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return result.returncode == 0

    return _is_ignored


# ---------------------------------------------------------------------------
# Per-repo config (D5)
# ---------------------------------------------------------------------------


def load_retired_paths(root: Path) -> list[str]:
    """Built-in defaults merged with an optional repo-root ``audit.toml``
    ``[knowledge_lint].retired_paths`` extension. Absent file/table/key ->
    defaults only."""
    tokens = list(DEFAULT_RETIRED_PATHS)
    config_path = root / "audit.toml"
    if not config_path.is_file():
        return tokens
    with config_path.open("rb") as fh:
        data = tomllib.load(fh)
    extra = data.get("knowledge_lint", {}).get("retired_paths", [])
    for token in extra:
        if token not in tokens:
            tokens.append(token)
    return tokens


# ---------------------------------------------------------------------------
# Check 1 — orphan/duplicate canonical file
# ---------------------------------------------------------------------------


def _check_orphan_duplicate(root: Path, is_ignored: Callable[[str], bool]) -> list[Finding]:
    matches: dict[str, list[str]] = {name: [] for name in CANONICAL_MAP}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in _SKIP_DIRS and not is_ignored(_relpath(root, Path(dirpath) / d))
        ]
        for filename in filenames:
            if filename in CANONICAL_MAP:
                full = Path(dirpath) / filename
                matches[filename].append(_relpath(root, full))

    findings: list[Finding] = []
    for basename, home in CANONICAL_MAP.items():
        for rel in sorted(matches[basename]):
            if rel != home:
                findings.append(
                    Finding(
                        "orphan-or-duplicate-canonical-file",
                        rel,
                        None,
                        f"{basename} found outside its canonical home ({home})",
                    )
                )
    return findings


# ---------------------------------------------------------------------------
# Check 2 — retired-path token
# ---------------------------------------------------------------------------


def _check_retired_paths(root: Path, files: list[Path], tokens: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        rel = _relpath(root, path)
        for lineno, line in enumerate(_read_lines(path), start=1):
            for token in tokens:
                if token in line:
                    findings.append(
                        Finding(
                            "retired-path-token",
                            rel,
                            lineno,
                            f"retired-path token {token!r} found",
                        )
                    )
    return findings


# ---------------------------------------------------------------------------
# Check 3 — broken prose path citation
# ---------------------------------------------------------------------------


def _check_broken_citations(root: Path, files: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    top_level_dirs = _top_level_dirs(root)
    for path in files:
        rel = _relpath(root, path)
        for lineno, line in enumerate(_read_lines(path), start=1):
            for m in _BACKTICK_RE.finditer(line):
                token = m.group(1).strip()
                if not token:
                    continue
                if _has_whitespace(token):
                    continue  # command/prose fragment, not a single path
                if _is_url(token) or _is_absolute_system_path(token):
                    continue
                if _is_template_placeholder(token) or _is_glob_pattern(token):
                    continue
                if not _is_path_like(token):
                    continue
                first_segment = token.split("/", 1)[0]
                if first_segment not in top_level_dirs:
                    # Not rooted under a real top-level dir — a bare
                    # filename, cross-repo name, GitHub shorthand, or
                    # non-path slashy token, not a citation (D2 check 3
                    # first-segment gate).
                    continue
                if token in EPHEMERAL_PATHS:
                    continue
                if not (root / token).exists():
                    findings.append(
                        Finding(
                            "broken-prose-path-citation",
                            rel,
                            lineno,
                            f"citation `{token}` does not resolve under {root}",
                        )
                    )
    return findings


# ---------------------------------------------------------------------------
# Check 4 — dangling archive pointer
# ---------------------------------------------------------------------------


def _check_dangling_archive_pointers(root: Path, files: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        rel = _relpath(root, path)
        for lineno, line in enumerate(_read_lines(path), start=1):
            for m in _ARCHIVE_POINTER_RE.finditer(line):
                dir_name = m.group(1)
                target = root / "openspec" / "changes" / "archive" / dir_name
                if not target.is_dir():
                    findings.append(
                        Finding(
                            "dangling-archive-pointer",
                            rel,
                            lineno,
                            f"openspec/changes/archive/{dir_name}/ does not exist",
                        )
                    )
    return findings


# ---------------------------------------------------------------------------
# Check 5 — audit-log registry format (guarded)
# ---------------------------------------------------------------------------


def _check_audit_log(root: Path) -> list[Finding]:
    path = root / "knowledge" / "audit-log.md"
    if not path.is_file():
        return []
    rel = _relpath(root, path)
    findings: list[Finding] = []
    for lineno, raw_line in enumerate(_read_lines(path), start=1):
        line = raw_line.rstrip()
        if not _AUDIT_LOG_ANCHOR_RE.match(line):
            continue  # not a registry-anchored line (header/prose/blank) — ignore
        if not _AUDIT_LOG_FULL_RE.match(line):
            findings.append(
                Finding(
                    "audit-log-registry-format",
                    rel,
                    lineno,
                    f"malformed audit-log registry line: {line!r}",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def collect_findings(root: Path) -> list[Finding]:
    """Run every check and return the combined finding list. Read-only."""
    is_ignored = make_git_ignore_checker(root)
    all_knowledge_md = _knowledge_markdown(root, is_ignored)
    content_check_md = [p for p in all_knowledge_md if not _is_research(root, p)]
    retired_paths = load_retired_paths(root)

    findings: list[Finding] = []
    findings.extend(_check_orphan_duplicate(root, is_ignored))
    findings.extend(_check_retired_paths(root, content_check_md, retired_paths))
    findings.extend(_check_broken_citations(root, content_check_md))
    findings.extend(_check_dangling_archive_pointers(root, all_knowledge_md))
    findings.extend(_check_audit_log(root))
    return findings


def _format_finding(finding: Finding) -> str:
    loc = finding.path if finding.line is None else f"{finding.path}:{finding.line}"
    return f"knowledge_lint: [{finding.check}] {loc} — {finding.message}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect-only linter over tracked per-repo knowledge (D2)."
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Repository root (default: parent of scripts/, i.e. this script's repo).",
    )
    args = parser.parse_args(argv)

    if args.root is not None:
        root = Path(args.root).resolve(strict=True)
    else:
        root = Path(__file__).resolve().parent.parent

    print(f"knowledge_lint: checking {root}")

    findings = collect_findings(root)
    for finding in findings:
        print(_format_finding(finding))

    if findings:
        print(f"knowledge_lint: FAILED — {len(findings)} finding(s)")
        return 1

    print("knowledge_lint: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
