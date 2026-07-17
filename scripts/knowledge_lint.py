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
      optional per-repo `checks.toml` extension — see below). Skips
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
      ``- **YYYY-MM-DD** · audit/<date> · <short-sha> · <essence>`` (plain)
      or ``- **YYYY-MM-DD** · audit/<date>-composition · <short-sha> · <essence>``
      (composition variant); absent file → skipped silently.
   6. **ratchet-log registry format (guarded)** — if
      ``<root>/knowledge/ratchet-log.md`` exists, each registry-anchored line
      must match the finding-closure-ratchet format
      ``- **YYYY-MM-DD** · <kebab-slug> · <disposition> — <essence>``; valid
      dispositions: ``check:<pointer>`` (file/symbol exists),
      ``test:<path>[::<name>]`` (file/symbol exists),
      ``waiver:review-by YYYY-MM-DD`` (valid date, not past, reason present),
      ``open:since YYYY-MM-DD`` (age-flagged at threshold),
      ``grandfathered`` (format only); absent file → skipped silently.

 Checks 2 and 3 scan ``<root>/knowledge/**/*.md`` excluding
``knowledge/research/``; check 4 scans the same corpus WITHOUT that
exclusion; checks 5 and 6 each target one specific file; check 1 scans ``<root>``.

Per-repo config (D5): an optional repo-root ``checks.toml``
``[knowledge_lint].retired_paths`` array (read via stdlib ``tomllib``) is
MERGED with the built-in retired-path defaults. Absent file/table/key means
only the defaults apply. ``checks.toml`` is per-repo config, never
scaffold-managed. The same ``[knowledge_lint]`` table also carries
``decisions_index_max_bytes`` (default 16,000 — see check 14 below); an
invalid value (non-``int``, including ``bool``, or negative) falls back to
the default with a one-line stderr note.

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
import hashlib
import os
import re
import subprocess
import sys
import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Callable, NamedTuple

# Ensure scripts/ is on sys.path so outstanding.py can be imported both when
# this script is run directly and when imported in tests.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import outstanding  # noqa: E402

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
    "ratchet-log.md": "knowledge/ratchet-log.md",
}

# Built-in default retired-path tokens (the known universal reorg residue).
DEFAULT_RETIRED_PATHS: tuple[str, ...] = (
    "ai-docs/",
    "plans/open-issues.md",
    "docs/reviews/",
)

# Default byte budget for knowledge/decisions/INDEX.md (check 14, D-roll —
# see scripts/roll_decisions.py). Per-repo overridable via
# [knowledge_lint].decisions_index_max_bytes in checks.toml.
DECISIONS_INDEX_MAX_BYTES = 16_000

# The sole sanctioned mid-session handoff file (written mid-change, deleted
# on absorption) — see the knowledge taxonomy (knowledge/README.md). Exempt
# from the prose-hygiene checks both as a citation TARGET (via
# EPHEMERAL_PATHS below) and as a scanned SOURCE (its own forward-referencing
# prose is not drift) — see `_is_sanctioned_handoff`.
SANCTIONED_HANDOFF: str = "knowledge/HANDOFF.md"

# Known-ephemeral knowledge paths: legitimately absent in the steady state, so a
# citation to one is NOT a broken citation. knowledge/HANDOFF.md is the sanctioned
# mid-session handoff file (written mid-change, deleted on absorption) — see the
# knowledge taxonomy (knowledge/README.md).
EPHEMERAL_PATHS: tuple[str, ...] = (
    SANCTIONED_HANDOFF,
    "knowledge/audit-log.md",
    "knowledge/ratchet-log.md",
)

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
    r"^- \*\*\d{4}-\d{2}-\d{2}\*\* · audit/\d{4}-\d{2}-\d{2}(?:-composition)? · [0-9a-f]{7,40} · \S.*$"
)
# Matches date/period placeholders like `YYYY`, `YYYY-Www`, `MM-DD`, or
# `YY-MM-DD`.  Built from a date-token alternation so all-caps component
# names like `API`, `SQL`, `CSV`, `JSON`, `YAML`, `TODO` do NOT match.
# Must anchor on the whole stem.
_DATE_TOKEN = r"(?:Y{2,4}|M{1,2}|D{1,2}|H{1,2}|S{1,2}|Www|Q[1-4]?)"
_DATE_FORMAT_PLACEHOLDER_RE = re.compile(rf"^{_DATE_TOKEN}(?:-{_DATE_TOKEN})*$")
# Matches a trailing `:N-M` line-range suffix (e.g. `:10-20`, `:490-524`)
# OR a `:N` single-line number (e.g. `:42`).
_LINE_RANGE_RE = re.compile(r":(\d+)(?:-(\d+))?$")


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


def _is_sanctioned_handoff(root: Path, path: Path) -> bool:
    """True only for the exact sanctioned handoff path. Uses **exact**
    equality, never a substring/`in` test — a substring match would wrongly
    exempt e.g. ``plans/knowledge/HANDOFF.md``."""
    return _relpath(root, path) == SANCTIONED_HANDOFF


def _knowledge_markdown(root: Path, is_ignored: Callable[[str], bool]) -> list[Path]:
    """All ``<root>/knowledge/**/*.md`` files (includes knowledge/research/),
    skipping any path git-ignores (see ``make_git_ignore_checker``)."""
    knowledge_dir = root / "knowledge"
    if not knowledge_dir.is_dir():
        return []
    results: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(knowledge_dir):
        dirnames[:] = [d for d in dirnames if not is_ignored(_relpath(root, Path(dirpath) / d))]
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
    if "<" in token or ">" in token:
        return True
    # Date/period placeholders like `YYYY-Www` — a path component whose
    # alphabetic stem is a sequence of 3-4 uppercase letters (ISO week / date
    # placeholder notation), optionally followed by a hyphen and mixed-case.
    for part in token.split("/"):
        stem = part.rsplit(".", 1)[0] if "." in part else part
        if _DATE_FORMAT_PLACEHOLDER_RE.match(stem):
            return True
    return False


def _is_glob_pattern(token: str) -> bool:
    # A glob (`checks/*.sql`, `.claude/skills/**`) names a pattern, not a
    # single resolvable path.
    return "*" in token


def _is_brace_pattern(token: str) -> bool:
    """Brace-expansion patterns like ``{a,b}`` or ``{a..b}`` — a deliberate
    notation, not a broken path."""
    return "{" in token and "}" in token


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
    """Built-in defaults merged with an optional repo-root ``checks.toml``
    ``[knowledge_lint].retired_paths`` extension. Absent file/table/key ->
    defaults only."""
    tokens = list(DEFAULT_RETIRED_PATHS)
    config_path = root / "checks.toml"
    if not config_path.is_file():
        return tokens
    with config_path.open("rb") as fh:
        data = tomllib.load(fh)
    extra = data.get("knowledge_lint", {}).get("retired_paths", [])
    for token in extra:
        if token not in tokens:
            tokens.append(token)
    return tokens


def _load_knowledge_lint_config(root: Path) -> dict:
    """Load [knowledge_lint] config from checks.toml with graceful defaults.

    Returns dict with keys ``untriaged_max_age_days`` (default 14),
    ``duplicate_scan_dirs`` (default []), ``ratchet_open_max_age_days``
    (default 30), and ``decisions_index_max_bytes`` (default
    ``DECISIONS_INDEX_MAX_BYTES`` = 16,000). An invalid
    ``decisions_index_max_bytes`` (non-``int`` — a ``bool`` counts as
    non-int — or negative) falls back to the default, with a one-line
    stderr note.
    """
    kl: dict = {}
    config_path = root / "checks.toml"
    if config_path.is_file():
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        kl = data.get("knowledge_lint", {})

    decisions_index_max_bytes = kl.get("decisions_index_max_bytes", DECISIONS_INDEX_MAX_BYTES)
    if (
        isinstance(decisions_index_max_bytes, bool)
        or not isinstance(decisions_index_max_bytes, int)
        or decisions_index_max_bytes < 0
    ):
        print(
            "knowledge_lint: [knowledge_lint] decisions_index_max_bytes must be a"
            " non-negative integer — falling back to the"
            f" {DECISIONS_INDEX_MAX_BYTES}-byte default",
            file=sys.stderr,
        )
        decisions_index_max_bytes = DECISIONS_INDEX_MAX_BYTES

    return {
        "untriaged_max_age_days": kl.get("untriaged_max_age_days", 14),
        "duplicate_scan_dirs": kl.get("duplicate_scan_dirs", []),
        "ratchet_open_max_age_days": kl.get("ratchet_open_max_age_days", 30),
        "decisions_index_max_bytes": decisions_index_max_bytes,
    }


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


def _check_broken_citations(
    root: Path, files: list[Path], is_ignored: Callable[[str], bool]
) -> list[Finding]:
    findings: list[Finding] = []
    top_level_dirs = _top_level_dirs(root)
    for path in files:
        rel = _relpath(root, path)
        for lineno, line in enumerate(_read_lines(path), start=1):
            # Inline suppression marker: a line containing the literal string
            # ``<!-- lint:planned -->`` means the author is deliberately
            # forward-referencing a not-yet-created file — skip the entire line.
            if "<!-- lint:planned -->" in line:
                continue
            for m in _BACKTICK_RE.finditer(line):
                token = m.group(1).strip()
                if not token:
                    continue
                if _has_whitespace(token):
                    continue  # command/prose fragment, not a single path
                if _is_url(token) or _is_absolute_system_path(token):
                    continue
                if (
                    _is_template_placeholder(token)
                    or _is_glob_pattern(token)
                    or _is_brace_pattern(token)
                ):
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
                if first_segment == "output":
                    # `output/` is ephemeral (generated/gitignored) —
                    # treat like EPHEMERAL_PATHS.
                    continue
                if token in EPHEMERAL_PATHS:
                    continue
                # Strip trailing `::symbol` node-id (pytest/symbol
                # reference), then `:N-M` line range, before the
                # existence check.  If the underlying file does not
                # exist, it still flags — drift is not blinded.
                check_token = token
                if "::" in check_token:
                    check_token = check_token.split("::", 1)[0]
                line_range_m = _LINE_RANGE_RE.search(check_token)
                if line_range_m:
                    check_token = check_token[: line_range_m.start()]
                if is_ignored(check_token):
                    # A citation to a gitignored (generated/rendered/ephemeral)
                    # target is not drift — its steady-state absence on a clean
                    # tree is expected. This generalizes the literal `output/`
                    # guard above; that literal remains as the git-unavailable
                    # fallback (design D2: is_ignored returns False when root is
                    # not a git repo). Covers e.g. a downstream repo's
                    # deploy-time-rendered `deploy/rendered/…` install artifact.
                    continue
                if not (root / check_token).exists():
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
# Check 6 — ratchet-log registry format (guarded)
# ---------------------------------------------------------------------------

# Matches the registry-anchor prefix (any line beginning with `- **<date>**`)
_RATCHET_LOG_ANCHOR_RE = re.compile(r"^- \*\*\d{4}-\d{2}-\d{2}\*\*")
# Full format: `- **YYYY-MM-DD** · <slug> · <disposition> — <essence>`
# Uses \S[^—]* for disposition to allow multi-word forms like
# "waiver:review-by 2026-12-31" while stopping at the em-dash.
_RATCHET_LOG_FULL_RE = re.compile(r"^- \*\*\d{4}-\d{2}-\d{2}\*\* · [a-z][a-z0-9-]* · \S[^—]* — .+$")
# Disposition keyword patterns — same structure with capture groups
_RATCHET_DISP_RE = re.compile(
    r"^- \*\*(\d{4}-\d{2}-\d{2})\*\* · ([a-z][a-z0-9-]*) · (\S[^—]*) — (.+)$"
)
# Valid ISO calendar date check
_ISO_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
# Extract `waiver:review-by YYYY-MM-DD`
_RATCHET_WAIVER_RE = re.compile(r"^waiver:review-by (\d{4}-\d{2}-\d{2})$")
# Extract `open:since YYYY-MM-DD`
_RATCHET_OPEN_RE = re.compile(r"^open:since (\d{4}-\d{2}-\d{2})$")


def _check_ratchet_log(root: Path) -> list[Finding]:
    """Validate ``knowledge/ratchet-log.md`` registry format.

    Guarded on file existence (absent → silent clean, same as
    ``_check_audit_log``). Validates:
    - Registry-anchored lines match the full format.
    - Disposition keyword is one of the five known forms.
    - Slugs are kebab-case.
    - Dates are real ISO calendar dates (rejects ``2026-13-01``).
    - ``check:``/``test:`` pointers resolve to an existing file.
    - ``::<name>`` suffix on a pointer is textually present in the file.
    - ``waiver`` has non-empty essence and review-by date is not past.
    - ``open`` older than ``ratchet_open_max_age_days`` (config, default 30) is flagged.
    - ``grandfathered`` entries get format-only validation.
    - Lines that are NOT registry-anchored (header, blank, prose) are skipped.
    """
    path = root / "knowledge" / "ratchet-log.md"
    if not path.is_file():
        return []
    rel = _relpath(root, path)
    findings: list[Finding] = []

    kl_config = _load_knowledge_lint_config(root)
    max_open_age = kl_config.get("ratchet_open_max_age_days", 30)

    lines = _read_lines(path)
    for lineno, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip()
        if not _RATCHET_LOG_ANCHOR_RE.match(line):
            continue  # not a registry-anchored line — skip
        if not _RATCHET_LOG_FULL_RE.match(line):
            findings.append(
                Finding(
                    "ratchet-log-registry-format",
                    rel,
                    lineno,
                    f"malformed ratchet-log registry line: {line!r}",
                )
            )
            continue

        # Parse disposition
        m = _RATCHET_DISP_RE.match(line)
        if not m:
            continue  # already caught by FULL_RE above, but guard
        entry_date_str = m.group(1)
        slug = m.group(2)
        disposition = m.group(3)
        essence = m.group(4)

        # Validate entry date is a real calendar date
        date_err = _validate_date(entry_date_str)
        if date_err:
            findings.append(
                Finding(
                    "ratchet-log-registry-format",
                    rel,
                    lineno,
                    f"invalid entry date {entry_date_str!r}: {date_err}",
                )
            )
            continue

        # Validate slug is kebab-case
        if not re.match(r"^[a-z][a-z0-9-]*$", slug):
            findings.append(
                Finding(
                    "ratchet-log-registry-format",
                    rel,
                    lineno,
                    f"invalid slug {slug!r}: must be kebab-case (lowercase, digits, hyphens)",
                )
            )
            continue

        # Validate disposition
        disp_err = _validate_ratchet_disposition(
            disposition, essence, root, entry_date_str, max_open_age
        )
        if disp_err:
            findings.append(
                Finding(
                    "ratchet-log-registry-format",
                    rel,
                    lineno,
                    disp_err,
                )
            )

    return findings


def _validate_date(date_str: str) -> str | None:
    """Validate a ``YYYY-MM-DD`` string is a real ISO calendar date.
    Returns None on valid, or an error message string."""
    m = _ISO_DATE_RE.match(date_str)
    if not m:
        return "not a valid YYYY-MM-DD format"
    year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
    import calendar

    try:
        max_day = calendar.monthrange(year, month)[1]
    except calendar.IllegalMonthError:
        return f"invalid month {month:02d}"
    if day < 1 or day > max_day:
        return f"invalid day {day:02d} for month {month:02d}"
    return None


def _validate_ratchet_disposition(
    disposition: str, essence: str, root: Path, entry_date_str: str, max_open_age: int
) -> str | None:
    """Validate a single disposition keyword and its payload.
    Returns an error message string, or None if valid."""

    # --- grandfathered ---
    if disposition == "grandfathered":
        return None  # format only, no liveness checks

    # --- check:<pointer> ---
    cm = re.match(r"^check:(.+)$", disposition)
    if cm:
        return _validate_pointer(cm.group(1), root, disposition)

    # --- test:<path>[::<name>] ---
    tm = re.match(r"^test:(.+)$", disposition)
    if tm:
        return _validate_pointer(tm.group(1), root, disposition)

    # --- waiver:review-by YYYY-MM-DD ---
    wm = _RATCHET_WAIVER_RE.match(disposition)
    if wm:
        review_by = wm.group(1)
        # Validate review-by date is real
        err = _validate_date(review_by)
        if err:
            return f"invalid waiver review-by date {review_by!r}: {err}"
        # Validate essence (reason) is non-empty
        if not essence.strip().replace("\u2014", "").strip():
            return "waiver disposition must have a non-empty reason (essence)"
        # Check waiver is not past
        from datetime import date as _date

        try:
            parts = review_by.split("-")
            review_date = _date(int(parts[0]), int(parts[1]), int(parts[2]))
            if review_date < _date.today():
                return f"waiver review-by date {review_by} is in the past"
        except (ValueError, IndexError):
            return f"invalid waiver review-by date {review_by!r}"
        return None

    # --- open:since YYYY-MM-DD ---
    om = _RATCHET_OPEN_RE.match(disposition)
    if om:
        since = om.group(1)
        err = _validate_date(since)
        if err:
            return f"invalid open:since date {since!r}: {err}"
        # Check if open entry is older than the threshold
        from datetime import date as _date

        try:
            parts = since.split("-")
            since_date = _date(int(parts[0]), int(parts[1]), int(parts[2]))
            age = (_date.today() - since_date).days
            if age > max_open_age:
                return (
                    f"open:since entry is {age} days old "
                    f"(max {max_open_age} days configured in ratchet_open_max_age_days)"
                )
        except (ValueError, IndexError):
            return f"invalid open:since date {since!r}"
        return None

    # --- unknown disposition ---
    return f"unknown disposition keyword: {disposition!r}"


def _validate_pointer(pointer: str, root: Path, disposition: str) -> str | None:
    """Validate a ``check:`` or ``test:`` pointer.

    If pointer contains ``::<name>``, verify the file exists AND the name
    appears textually in it. Otherwise verify file existence only.
    Returns an error message string, or None if valid.
    """
    if "::" in pointer:
        file_part, symbol = pointer.split("::", 1)
    else:
        file_part = pointer
        symbol = None

    file_path = root / file_part
    if not file_path.is_file():
        return f"pointer file {file_part!r} does not exist ({disposition})"

    if symbol is not None:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return f"cannot read pointer file {file_part!r} ({disposition})"
        if symbol not in content:
            return f"symbol {symbol!r} not found in pointer file {file_part!r} ({disposition})"

    return None


# ---------------------------------------------------------------------------
# Check 7 — handoff-named files (repo-wide)
# ---------------------------------------------------------------------------


def _check_handoff_files(root: Path, is_ignored: Callable[[str], bool]) -> list[Finding]:
    """Flag any non-gitignored file anywhere in the repository whose name
    contains ``handoff`` or ``handover`` (case-insensitive substring match),
    exempting only the sanctioned ``knowledge/HANDOFF.md``. This widens the
    original root-only prefix check to a repo-wide, case-insensitive-substring
    scope."""

    findings: list[Finding] = []
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune directories: skip .git and gitignored dirs (mirrors
            # _check_orphan_duplicate's pruning).
            dirnames[:] = [
                d
                for d in dirnames
                if d not in _SKIP_DIRS and not is_ignored(_relpath(root, Path(dirpath) / d))
            ]
            for filename in filenames:
                rel = _relpath(root, Path(dirpath) / filename)
                # Sole sanctioned exemption.
                if rel == SANCTIONED_HANDOFF:
                    continue
                # Skip gitignored files.
                if is_ignored(rel):
                    continue
                # Case-insensitive substring match for handoff/handover.
                if "handoff" in filename.lower() or "handover" in filename.lower():
                    findings.append(
                        Finding(
                            "handoff-file",
                            rel,
                            None,
                            f"handoff-named file {rel}; the only sanctioned handoff file is {SANCTIONED_HANDOFF}",
                        )
                    )
    except OSError:
        pass
    return findings


# ---------------------------------------------------------------------------
# Check 7 — duplicate content blocks (D7)
# ---------------------------------------------------------------------------

_WINDOW_SIZE = 8


def _is_excluded_dir(rel: str, prefix: str) -> bool:
    """True when repo-relative dir *rel* IS *prefix* or lives under it.

    A plain ``rel.startswith(prefix + "/")`` misses the exact-match case:
    when ``os.walk`` visits the excluded directory itself, *rel* equals
    *prefix* with no trailing slash (e.g. ``"knowledge/research"``, not
    ``"knowledge/research/"``), so a strict prefix-with-slash check lets
    files sitting directly inside it slip through uncompared. Both the
    directory itself and anything nested under it must be excluded.
    """
    return rel == prefix or rel.startswith(prefix + "/")


def _duplicate_scan_files(root: Path, is_ignored: Callable[[str], bool]) -> list[Path]:
    """Build the narrow set of files compared for duplicate blocks.

    Includes markdown under ``knowledge/`` (excluding ``knowledge/research/``),
    top-level ``*.md`` files, and any extra dirs from
    ``[knowledge_lint].duplicate_scan_dirs``.  Excludes ``openspec/specs/``.
    """
    files: list[Path] = []
    kl_config = _load_knowledge_lint_config(root)

    # knowledge/ markdown excluding research/ and openspec/specs/.
    knowledge_dir = root / "knowledge"
    if knowledge_dir.is_dir():
        for dirpath, dirnames, filenames in os.walk(knowledge_dir):
            rel = _relpath(root, Path(dirpath))
            if _is_excluded_dir(rel, "knowledge/research") or _is_excluded_dir(
                rel, "openspec/specs"
            ):
                dirnames[:] = []  # prune: don't descend into the excluded subtree either
                continue
            # Exclude gitignored dirs.
            dirnames[:] = [d for d in dirnames if not is_ignored(f"{rel}/{d}")]
            for fn in filenames:
                if not fn.endswith(".md"):
                    continue
                full = Path(dirpath, fn)
                files.append(full)

    # Top-level *.md
    for entry in sorted(root.glob("*.md")):
        if entry.is_file():
            files.append(entry)

    # Extra scan dirs from config.
    for extra_dir in kl_config.get("duplicate_scan_dirs", []):
        extra_path = root / extra_dir
        if extra_path.is_dir():
            for dirpath, dirnames, filenames in os.walk(extra_path):
                rel = _relpath(root, Path(dirpath))
                if _is_excluded_dir(rel, "openspec/specs"):
                    dirnames[:] = []
                    continue
                dirnames[:] = [d for d in dirnames if not is_ignored(f"{rel}/{d}")]
                for fn in filenames:
                    if not fn.endswith(".md"):
                        continue
                    full = Path(dirpath, fn)
                    files.append(full)

    # The sanctioned handoff must not be one of the "2+ files" a duplicate
    # window is counted across — it legitimately quotes context forward.
    # Excluded here, at the single return chokepoint, rather than per
    # collection loop above: this guarantees no collection path — including
    # a configured ``duplicate_scan_dirs`` root that happens to re-cover
    # knowledge/ or "." — can re-add the sanctioned handoff to the compared
    # set.
    return sorted({f for f in files if _relpath(root, f) != SANCTIONED_HANDOFF})


def _contiguous_runs(sorted_ints: list[int]) -> list[list[int]]:
    """Split a sorted, deduplicated list of ints into runs of consecutive values."""
    if not sorted_ints:
        return []
    runs: list[list[int]] = [[sorted_ints[0]]]
    for value in sorted_ints[1:]:
        if value - runs[-1][-1] == 1:
            runs[-1].append(value)
        else:
            runs.append([value])
    return runs


def _check_duplicate_blocks(root: Path, is_ignored: Callable[[str], bool]) -> list[Finding]:
    """Flag ≥8 consecutive non-trivial lines identical (whitespace-normalized)
    across 2+ files in the narrow compared set (D7).

    A sliding 8-line window is hashed per file; a window whose exact content
    recurs in 2+ files is a duplicate. Because content shifts by one line at
    each step, consecutive overlapping windows within one contiguous
    duplicated span get DIFFERENT hash keys (each window's content differs),
    so a naive per-key report would emit one finding per 1-line offset across
    the whole span. To collapse that into ONE finding per maximal duplicated
    region, this builds a union-find over ``(file, window-start-index)``
    nodes: nodes sharing an exact-content window are unioned (same
    duplicate), and — separately — nodes adjacent within the same file
    (index i, i+1) are also unioned, chaining the shifting-hash windows of
    one contiguous span together. Each resulting connected component is
    reported as one finding per file, spanning from the first to the last
    matched line.

    A ``<!-- lint:dup-ok -->`` marker whose line falls inside a detected
    duplicate window suppresses that finding.
    """
    files = _duplicate_scan_files(root, is_ignored)

    # Per-file: raw lines (for marker-suppression scanning) and the
    # (raw_line_no, stripped_content) list restricted to non-blank lines
    # (for window-building — index i here is the node id's second element).
    file_raw_lines: dict[Path, list[str]] = {}
    file_nonempty: dict[Path, list[tuple[int, str]]] = {}
    for fpath in files:
        try:
            raw_lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        file_raw_lines[fpath] = raw_lines
        file_nonempty[fpath] = [(i + 1, s) for i, raw in enumerate(raw_lines) if (s := raw.strip())]

    # window content (tuple of _WINDOW_SIZE stripped lines) -> [(path, index), ...]
    window_map: dict[tuple[str, ...], list[tuple[Path, int]]] = {}
    for fpath, non_empty in file_nonempty.items():
        for i in range(len(non_empty) - _WINDOW_SIZE + 1):
            window = tuple(non_empty[i + k][1] for k in range(_WINDOW_SIZE))
            window_map.setdefault(window, []).append((fpath, i))

    # --- Union-Find over (path, index) nodes -------------------------------
    parent: dict[tuple[Path, int], tuple[Path, int]] = {}

    def find(node: tuple[Path, int]) -> tuple[Path, int]:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(a: tuple[Path, int], b: tuple[Path, int]) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Same exact-content window recurring in 2+ files -> union all its
    # occurrences together (this is what makes it a "duplicate" at all).
    for locations in window_map.values():
        if len({p for p, _ in locations}) < 2:
            continue
        for loc in locations:
            parent.setdefault(loc, loc)
        first = locations[0]
        for loc in locations[1:]:
            union(first, loc)

    # Chain adjacent window-start indices within the same file so a
    # contiguous duplicated span (whose per-offset hash keys all differ)
    # collapses into one component instead of one per 1-line offset.
    indices_by_file: dict[Path, set[int]] = {}
    for path, idx in parent:
        indices_by_file.setdefault(path, set()).add(idx)
    for path, idxs in indices_by_file.items():
        for idx in idxs:
            if (idx + 1) in idxs:
                union((path, idx), (path, idx + 1))

    components: dict[tuple[Path, int], list[tuple[Path, int]]] = {}
    for node in parent:
        components.setdefault(find(node), []).append(node)

    findings: list[Finding] = []
    for comp_nodes in components.values():
        by_file: dict[Path, list[int]] = {}
        for path, idx in comp_nodes:
            by_file.setdefault(path, []).append(idx)
        if len(by_file) < 2:
            continue  # adjacency-merge collapsed it below the 2-file floor

        # Split each file's indices into contiguous runs (a component can
        # hold >1 disjoint run per file, e.g. the same block repeated twice
        # in one file), then compute each run's raw-line-number span.
        occurrences: list[tuple[Path, int, int]] = []
        for path, idxs in by_file.items():
            non_empty = file_nonempty[path]
            for run in _contiguous_runs(sorted(set(idxs))):
                start_line = non_empty[run[0]][0]
                end_line = non_empty[run[-1] + _WINDOW_SIZE - 1][0]
                occurrences.append((path, start_line, end_line))

        distinct_file_count = len({p for p, _, _ in occurrences})
        if distinct_file_count < 2:
            continue

        # Suppress the whole region if a <!-- lint:dup-ok --> marker falls
        # inside ANY occurrence's window.
        suppressed = False
        for path, start_line, end_line in occurrences:
            all_lines = file_raw_lines.get(path, [])
            for i in range(start_line - 1, min(end_line, len(all_lines))):
                if "<!-- lint:dup-ok -->" in all_lines[i]:
                    suppressed = True
                    break
            if suppressed:
                break
        if suppressed:
            continue

        for path, start_line, end_line in occurrences:
            rel = _relpath(root, path)
            loc_str = (
                f"line {start_line}" if start_line == end_line else f"lines {start_line}-{end_line}"
            )
            findings.append(
                Finding(
                    "duplicate-content-block",
                    rel,
                    start_line,
                    f"duplicate block ({loc_str}) appears in {distinct_file_count} files",
                )
            )

    return findings


# ---------------------------------------------------------------------------
# Check 8 — closed-but-unpruned entries (D7)
# ---------------------------------------------------------------------------

_CLOSED_TOKEN_RE = re.compile(r"\b(?:CLOSED|DONE|COMPLETE)\b|✅|~~")


def _check_closed_unpruned(root: Path) -> list[Finding]:
    """Flag a ``knowledge/roadmap.md`` ``## `` entry or a top-level
    ``plans/*.md`` file whose heading / ``**Priority:**`` / ``**Status:**``
    line carries a closed-token (CLOSED, DONE, COMPLETE, ✅, ~~…~~).

    A ``<!-- lint:keep -->`` marker in the entry/file opts out.
    """
    findings: list[Finding] = []

    # -- Check knowledge/roadmap.md --
    roadmap_path = root / "knowledge" / "roadmap.md"
    if roadmap_path.is_file():
        try:
            roadmap_lines = roadmap_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            roadmap_lines = []

        if roadmap_lines:
            rel = _relpath(root, roadmap_path)
            i = 0
            while i < len(roadmap_lines):
                heading_m = re.match(r"^##\s+(.*)$", roadmap_lines[i])
                if not heading_m:
                    i += 1
                    continue
                heading_line = i
                heading_text = heading_m.group(1).strip()

                # Collect section until next ## or EOF.
                j = i + 1
                while j < len(roadmap_lines) and not re.match(r"^##\s", roadmap_lines[j]):
                    j += 1

                # Check for closed tokens in heading or Priority:/Status: lines.
                tokens_found: list[tuple[int, str]] = []
                if _CLOSED_TOKEN_RE.search(heading_text):
                    tokens_found.append((heading_line, heading_text))

                for k in range(heading_line + 1, j):
                    stripped = roadmap_lines[k].strip()
                    if re.match(
                        r"\*\*(?:Priority|Status):\*\*", stripped
                    ) and _CLOSED_TOKEN_RE.search(stripped):
                        tokens_found.append((k, stripped))

                if tokens_found:
                    # Check for <!-- lint:keep --> anywhere in this section.
                    if any(
                        "<!-- lint:keep -->" in roadmap_lines[ln] for ln in range(heading_line, j)
                    ):
                        i = j
                        continue
                    token_detail = "; ".join(f"line {ln + 1}: {txt}" for ln, txt in tokens_found)
                    findings.append(
                        Finding(
                            "closed-but-unpruned",
                            rel,
                            heading_line + 1,
                            f"closed entry '{heading_text}' — {token_detail}",
                        )
                    )

                i = j

    # -- Check plans/**/*.md, recursively, excluding plans/archive/** --
    plans_dir = root / "plans"
    if plans_dir.is_dir():
        for entry in sorted(plans_dir.rglob("*.md")):
            rel = _relpath(root, entry)
            if rel.startswith("plans/archive/"):
                continue
            if entry.name == "README.md":
                continue
            try:
                plan_text = entry.read_text(encoding="utf-8")
            except OSError:
                continue
            plan_lines = plan_text.splitlines()

            # Check all headings, Priority:, and Status: lines.
            tokens_found: list[tuple[int, str]] = []
            for ln, line in enumerate(plan_lines):
                heading_m = re.match(r"^#{1,3}\s+(.*)$", line)
                if heading_m:
                    if _CLOSED_TOKEN_RE.search(heading_m.group(1)):
                        tokens_found.append((ln, line))
                stripped = line.strip()
                if re.match(r"\*\*(?:Priority|Status):\*\*", stripped) and _CLOSED_TOKEN_RE.search(
                    stripped
                ):
                    tokens_found.append((ln, line))

            if tokens_found:
                if "<!-- lint:keep -->" in plan_text:
                    continue
                token_detail = "; ".join(f"line {ln + 1}: {txt}" for ln, txt in tokens_found)
                findings.append(
                    Finding(
                        "closed-but-unpruned",
                        rel,
                        tokens_found[0][0] + 1,
                        f"closed plan file '{entry.name}' — {token_detail}",
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# Check 9 — audit dossier format (D8)
# ---------------------------------------------------------------------------

# Matches a finding ID at the `## CA-W<N>-<seq>` heading level.
_FINDING_ID_HEADING_RE = re.compile(r"^## (CA-W\d+-\d+)")
# The four valid census dispositions (N/A- is a prefix match).
_VALID_CENSUS_DISPOSITIONS: tuple[str, ...] = (
    "AUDITED-clean",
    "AUDITED-finding",
    "LEAD-deferred",
    "N/A-",
)


def _check_audit_dossier(root: Path) -> list[Finding]:
    """Validate correctness-audit dossiers (marker-gated).

    Scans ``knowledge/research/correctness-audit-*/`` directories. Checks
    only those whose ``CHARTER.md`` contains the literal line
    ``format: correctness-audit/v1``. For marked dossiers flags:
    (a) duplicate finding IDs across ``FINDINGS*.md`` files,
    (b) census disposition values outside the D3 set,
    (c) graduated findings (any non-``LEAD`` evidence label) missing
        ``Prior:`` or ``Class:``.
    A directory with no ``CHARTER.md``, or a ``CHARTER.md`` without the
    marker, is skipped entirely. No dossier directory at all lints clean.
    """
    findings: list[Finding] = []

    dossier_dirs = sorted(root.glob("knowledge/research/correctness-audit-*/"))
    for dd in dossier_dirs:
        if not dd.is_dir():
            continue

        # Check for CHARTER.md with the format marker.
        charter_path = dd / "CHARTER.md"
        if not charter_path.is_file():
            continue
        try:
            charter_text = charter_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "format: correctness-audit/v1" not in charter_text:
            continue

        # (a) — duplicate finding IDs across FINDINGS*.md files.
        id_locations: dict[str, list[str]] = {}
        for fpath in sorted(dd.glob("FINDINGS*.md")):
            if not fpath.is_file():
                continue
            rel = _relpath(root, fpath)
            try:
                lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for lineno, line in enumerate(lines, start=1):
                m = _FINDING_ID_HEADING_RE.match(line)
                if m:
                    fid = m.group(1)
                    id_locations.setdefault(fid, []).append(f"{rel}:{lineno}")
        for fid, locs in sorted(id_locations.items()):
            if len(locs) > 1:
                findings.append(
                    Finding(
                        "audit-dossier-format",
                        _relpath(root, dd),
                        None,
                        f"duplicate finding ID {fid!r} appears in: {', '.join(locs)}",
                    )
                )

        # (b) — invalid census disposition.
        census_path = dd / "CENSUS.md"
        if census_path.is_file():
            try:
                census_lines = census_path.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines()
            except OSError:
                census_lines = []
            rel = _relpath(root, census_path)
            for lineno, line in enumerate(census_lines, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("<"):
                    # Skip blank lines, comments, and the template header line.
                    continue
                # Parse pipe-separated: surface | disposition | IDs | notes
                if "|" not in stripped:
                    continue
                parts = [p.strip() for p in stripped.split("|")]
                if len(parts) < 2:
                    continue
                disposition = parts[1]
                valid = any(
                    disposition == d if not d.endswith("-") else disposition.startswith(d)
                    for d in _VALID_CENSUS_DISPOSITIONS
                )
                if not valid:
                    findings.append(
                        Finding(
                            "audit-dossier-format",
                            rel,
                            lineno,
                            f"invalid census disposition {disposition!r} "
                            f"(must be one of AUDITED-clean / AUDITED-finding / "
                            f"LEAD-deferred / N/A-<reason>)",
                        )
                    )

        # (c) — graduated findings missing Prior: or Class:.
        for fpath in sorted(dd.glob("FINDINGS*.md")):
            if not fpath.is_file():
                continue
            rel = _relpath(root, fpath)
            try:
                text = fpath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            lines = text.splitlines()
            # Split into entries by ## CA- headings and graduation-log prefix.
            i = 0
            while i < len(lines):
                m = _FINDING_ID_HEADING_RE.match(lines[i])
                if not m:
                    i += 1
                    continue
                entry_start = i
                fid = m.group(1)
                i += 1
                # Collect lines until next ## CA- heading or EOF.
                while i < len(lines) and not _FINDING_ID_HEADING_RE.match(lines[i]):
                    # Also stop at ### Graduation log (the graduation log
                    # is an append-only block at the top of the file).
                    if lines[i].startswith("### "):
                        break
                    i += 1
                entry_lines = lines[entry_start:i]

                # Extract the evidence label (line after **Evidence**).
                evidence_label = None
                for j, el in enumerate(entry_lines):
                    if el.strip() == "**Evidence**":
                        if j + 1 < len(entry_lines):
                            candidate = entry_lines[j + 1].strip()
                            if candidate and not candidate.startswith("**"):
                                evidence_label = candidate
                        break

                # Only check graduated (non-LEAD) findings.
                if evidence_label is None or evidence_label == "LEAD":
                    continue

                # Check for Prior: and Class: lines.
                has_prior = any(el.strip().startswith("**Prior:") for el in entry_lines)
                has_class = any(el.strip().startswith("**Class:") for el in entry_lines)
                missing: list[str] = []
                if not has_prior:
                    missing.append("Prior:")
                if not has_class:
                    missing.append("Class:")
                if missing:
                    findings.append(
                        Finding(
                            "audit-dossier-format",
                            rel,
                            entry_start + 1,
                            f"finding {fid} has evidence label {evidence_label!r} "
                            f"but is missing {', '.join(missing)}",
                        )
                    )

    return findings


# ---------------------------------------------------------------------------
# Check 10 — untriaged-finding accumulation (D8)
# ---------------------------------------------------------------------------


def _check_untriaged_age(root: Path) -> list[Finding]:
    """Flag an untriaged finding (via ``outstanding.extract_untriaged``) whose
    age exceeds ``untriaged_max_age_days`` from ``[knowledge_lint]`` config
    (default 14).  Detect-only — imports the shared extraction, never
    re-implements (D8).
    """
    # Load checks.toml config (shared with outstanding module).
    config_path = root / "checks.toml"
    config: dict = {}
    if config_path.is_file():
        with open(config_path, "rb") as f:
            config = tomllib.load(f)

    kl_config = _load_knowledge_lint_config(root)
    max_age = kl_config.get("untriaged_max_age_days", 14)

    untriaged = outstanding.extract_untriaged(root, config)

    findings: list[Finding] = []
    for item in untriaged:
        age = item.get("age_days", 0)
        if age > max_age:
            findings.append(
                Finding(
                    "untriaged-finding-stale",
                    item.get("file", ""),
                    None,
                    f"untriaged finding {item.get('id', '?')} is {age} days old (max {max_age})",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Check 11 — audit-liveness drift (Delta 1)
# ---------------------------------------------------------------------------


def _active_questions_text(root: Path) -> str:
    """Return the text of the ``## Active`` section of
    ``knowledge/questions/INDEX.md`` (the region from the ``## Active``
    heading up to the next ``## `` heading), or an empty string when the
    file or the section is absent.  Read-only.  Wraps the ``read_text``
    in ``try/except OSError``, mirroring ``_check_audit_dossier``."""
    path = root / "knowledge" / "questions" / "INDEX.md"
    if not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    lines = text.splitlines()
    active_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("## ") and "## Active" in line:
            active_start = i
            break
    if active_start is None:
        return ""
    # Find the next ## heading after Active (or EOF).
    section_lines: list[str] = []
    for line in lines[active_start + 1 :]:
        if line.strip().startswith("## "):
            break
        section_lines.append(line)
    return "\n".join(section_lines)


def _check_audit_liveness(root: Path) -> list[Finding]:
    """Flag in-progress correctness-audit dossiers not referenced by an
    Active item in ``knowledge/questions/INDEX.md``.

    Mirrors the guarded ``_check_audit_dossier`` idiom: glob
    ``knowledge/research/correctness-audit-*/``; consider only dirs whose
    ``CHARTER.md`` contains the literal ``format: correctness-audit/v1``;
    skip any whose ``CHARTER.md`` also contains a ``status: closed`` line.
    For each remaining (in-progress) dossier, require the dossier directory
    basename (e.g. ``correctness-audit-2026-07``) to appear (substring
    membership) in ``_active_questions_text(root)``; if it does not, flag.

    Empty glob / markerless / charter-less / closed → no findings.
    Detect-only.
    """
    findings: list[Finding] = []
    active_text = _active_questions_text(root)
    dossier_dirs = sorted(root.glob("knowledge/research/correctness-audit-*/"))
    for dd in dossier_dirs:
        if not dd.is_dir():
            continue
        charter_path = dd / "CHARTER.md"
        if not charter_path.is_file():
            continue
        try:
            charter_text = charter_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "format: correctness-audit/v1" not in charter_text:
            continue
        if "status: closed" in charter_text:
            continue
        # Substring match on the unique correctness-audit-YYYY-MM basename.
        dir_basename = dd.name
        if dir_basename not in active_text:
            findings.append(
                Finding(
                    "audit-liveness",
                    _relpath(root, dd),
                    None,
                    "in-progress correctness-audit dossier not referenced "
                    "by an Active knowledge/questions/INDEX.md item",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Check 12 — post-close ledger format (Delta 4)
# ---------------------------------------------------------------------------


def _check_post_close_ledger(root: Path) -> list[Finding]:
    """Validate ``POST-CLOSE-LEDGER.md`` line format in marked dossiers.

    Glob ``knowledge/research/correctness-audit-*/``; for each dir whose
    ``CHARTER.md`` contains ``format: correctness-audit/v1``, look for
    ``POST-CLOSE-LEDGER.md``.  When present, treat as entry line every line
    that is NOT blank, NOT a markdown heading (stripped line starts with
    ``#``), NOT a table-separator row (stripped line consists only of
    ``|``, ``-``, ``:``, spaces), and NOT an HTML comment (stripped line
    starts with ``<!--``).  For each entry line: strip it, remove a single
    leading ``|`` and a single trailing ``|`` if present, split on ``|``,
    and require at least five cells each non-empty after trimming.  Otherwise
    flag.  Absent ledger / unmarked / no dossier → no findings.  Detect-only.
    """
    findings: list[Finding] = []
    dossier_dirs = sorted(root.glob("knowledge/research/correctness-audit-*/"))
    for dd in dossier_dirs:
        if not dd.is_dir():
            continue
        charter_path = dd / "CHARTER.md"
        if not charter_path.is_file():
            continue
        try:
            charter_text = charter_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "format: correctness-audit/v1" not in charter_text:
            continue

        ledger_path = dd / "POST-CLOSE-LEDGER.md"
        if not ledger_path.is_file():
            continue
        try:
            ledger_lines = ledger_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        rel = _relpath(root, ledger_path)

        for lineno, raw_line in enumerate(ledger_lines, start=1):
            stripped = raw_line.strip()

            # Skip blank lines.
            if not stripped:
                continue
            # Skip markdown headings.
            if stripped.startswith("#"):
                continue
            # Skip table-separator rows (e.g. |---|---|---|).
            if all(ch in "|-: " for ch in stripped):
                continue
            # Skip HTML comments.
            if stripped.startswith("<!--"):
                continue

            # Strip a single leading | and a single trailing | if present.
            cell_line = stripped
            if cell_line.startswith("|"):
                cell_line = cell_line[1:]
            if cell_line.endswith("|"):
                cell_line = cell_line[:-1]

            cells = [c.strip() for c in cell_line.split("|")]
            if len(cells) < 5 or any(c == "" for c in cells):
                findings.append(
                    Finding(
                        "post-close-ledger-format",
                        rel,
                        lineno,
                        "malformed post-close ledger line "
                        "(need commit | subsystem | wave-owner | spec? | review-tier): "
                        f"{raw_line!r}",
                    )
                )
    return findings


# ---------------------------------------------------------------------------
# Check 13 — claims-ledger staleness (product-audit/v1)
# ---------------------------------------------------------------------------


def _check_claims_ledger_staleness(root: Path) -> list[Finding]:
    """Flag staleness in product-audit claims ledgers.

    Globs ``knowledge/reference/*.md`` and checks only files containing
    the literal marker ``format: product-audit/v1``.  Parses the
    ``## Covered promise-surface files`` section for lines matching
    ``- <path> — sha256:<64-hex>``.  For each matched file:
    - if the file does not exist on disk → finding
    - if the file's current sha256 differs (case-insensitive) from the
      recorded hash → finding
    Lines that do not match the format are silently skipped (lenient parse).
    No ``## Covered promise-surface files`` section, an empty section,
    or no marker → zero findings.  Detect-only.
    """
    findings: list[Finding] = []
    _MANIFEST_LINE_RE = re.compile(
        r"\s*-\s*(?P<path>.+?)\s*[—–-]+\s*sha256:(?P<hash>[0-9a-fA-F]{64})\b"
    )

    for ledger in sorted(root.glob("knowledge/reference/*.md")):
        try:
            text = ledger.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "format: product-audit/v1" not in text:
            continue

        lines = text.splitlines()
        in_manifest = False
        for lineno, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Track manifest section boundaries.
            if stripped == "## Covered promise-surface files":
                in_manifest = True
                continue
            if in_manifest and stripped.startswith("## "):
                in_manifest = False
                continue
            if not in_manifest:
                continue

            # Lenient parse: silently skip non-matching lines.
            m = _MANIFEST_LINE_RE.match(line)
            if not m:
                continue

            target_rel = m.group("path")
            recorded_hash = m.group("hash")
            target_path = (root / target_rel).resolve()

            if not target_path.is_file():
                findings.append(
                    Finding(
                        "claims-ledger-staleness",
                        _relpath(root, ledger),
                        lineno,
                        f"claims ledger covers a missing promise-surface file: {target_rel}",
                    )
                )
                continue

            try:
                actual_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()
            except OSError:
                continue

            if actual_hash.lower() != recorded_hash.lower():
                findings.append(
                    Finding(
                        "claims-ledger-staleness",
                        _relpath(root, ledger),
                        lineno,
                        f"claims ledger stale: {target_rel} content changed since last reconciliation",
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# Check 14 — decisions-index byte budget (roll-decisions-index)
# ---------------------------------------------------------------------------


def _check_decisions_index_budget(root: Path) -> list[Finding]:
    """Flag `knowledge/decisions/INDEX.md` when it exceeds its configured
    byte budget (default `DECISIONS_INDEX_MAX_BYTES` = 16,000; per-repo
    overridable via `[knowledge_lint] decisions_index_max_bytes` in
    `checks.toml`).

    A missing INDEX.md produces no finding. `knowledge/decisions/HISTORY.md`
    — the never-boot-loaded rolled-entries file — is never inspected here;
    its size is irrelevant to this check by design.
    """
    index_path = root / "knowledge" / "decisions" / "INDEX.md"
    if not index_path.is_file():
        return []

    size = index_path.stat().st_size
    kl_config = _load_knowledge_lint_config(root)
    budget = kl_config["decisions_index_max_bytes"]

    if size <= budget:
        return []

    rel = _relpath(root, index_path)
    return [
        Finding(
            "decisions-index-budget",
            rel,
            None,
            f"{rel} is {size} bytes, over the {budget}-byte budget — roll it with"
            " `python3 scripts/roll_decisions.py` (rolls oldest entries to"
            " `knowledge/decisions/HISTORY.md`; see `knowledge/README.md`)."
            " Raising the budget is an operator decision recorded in the"
            " decisions registry.",
        )
    ]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def collect_findings(root: Path) -> list[Finding]:
    """Run every check and return the combined finding list. Read-only."""
    is_ignored = make_git_ignore_checker(root)
    all_knowledge_md = _knowledge_markdown(root, is_ignored)
    content_check_md = [
        p
        for p in all_knowledge_md
        if not _is_research(root, p) and not _is_sanctioned_handoff(root, p)
    ]
    archive_pointer_check_md = [p for p in all_knowledge_md if not _is_sanctioned_handoff(root, p)]
    retired_paths = load_retired_paths(root)

    findings: list[Finding] = []
    findings.extend(_check_orphan_duplicate(root, is_ignored))
    findings.extend(_check_retired_paths(root, content_check_md, retired_paths))
    findings.extend(_check_broken_citations(root, content_check_md, is_ignored))
    findings.extend(_check_dangling_archive_pointers(root, archive_pointer_check_md))
    findings.extend(_check_audit_log(root))
    findings.extend(_check_ratchet_log(root))
    findings.extend(_check_handoff_files(root, is_ignored))
    findings.extend(_check_duplicate_blocks(root, is_ignored))
    findings.extend(_check_closed_unpruned(root))
    findings.extend(_check_audit_dossier(root))
    findings.extend(_check_untriaged_age(root))
    findings.extend(_check_audit_liveness(root))
    findings.extend(_check_post_close_ledger(root))
    findings.extend(_check_claims_ledger_staleness(root))
    findings.extend(_check_decisions_index_budget(root))
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
