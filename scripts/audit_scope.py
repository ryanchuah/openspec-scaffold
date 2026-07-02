#!/usr/bin/env python3
"""audit_scope.py — audit bookkeeping, delta scope, and hotspot ranking.

Three subcommands (``scan`` is the default when none is given):

``scan`` (read-only)
    Finds the latest ``audit/*`` git tag (``git tag --list 'audit/*'
    --sort=-creatordate``, most-recent first). If none exists, the scope is
    ``"full"`` — every tracked source file, churn measured against the
    empty-tree (so a file's churn is its full current size; there is no
    anchor to diff against yet). If a tag exists, the scope is ``"delta"`` —
    only files that changed between the tag and HEAD, via
    ``git diff --numstat <tag>..HEAD`` (churn = insertions + deletions;
    binary files, which numstat reports as ``-``/``-``, are skipped — they
    carry no textual churn signal).

    Per-file cyclomatic complexity comes from ``radon cc -j <path>``, run
    ONLY when ``radon`` is on PATH (graceful degradation — radon is pinned
    in each downstream repo's dev extras, not vendored here). When radon is
    unavailable, ``complexity_available`` is ``false`` and every file's
    ``complexity`` is ``null``; when it IS available, ``complexity`` is
    always a number (0 included) — a file with no blocks, or one that no
    longer exists on disk (deleted since the anchor), scores 0. A file's
    complexity is the MAXIMUM ``complexity`` value across all block entries
    (functions/methods/classes) radon reports for it.

    Hotspot score = churn * (1 + complexity) when radon is available, else
    churn * 1 (radon unavailable). Files are ranked by hotspot score,
    descending.

``tag --date YYYY-MM-DD``
    Creates an ANNOTATED tag ``audit/<date>`` at HEAD (message
    ``audit anchor <date>``). ``--date`` is required — no implicit "today" —
    so a documented invocation stays reproducible. If the tag already
    exists, this refuses (exit 3) rather than silently minting a second
    anchor. This is the ONLY mutating operation anywhere in this change
    (D3-compatible bookkeeping) and only fires on explicit invocation.

``log-line --date YYYY-MM-DD --essence "<free text>"``
    PRINTS (never writes) the audit-log registry line in the exact format
    ``- **<date>** · audit/<date> · <short-HEAD-sha> · <essence>``. The
    orchestrator appends the printed line to ``knowledge/audit-log.md``
    deliberately — this script stays write-free.

Output (scan only)
-------------------
JSON written to ``--json <path>`` (default ``audit_scope.json`` in CWD)::

    {
      "generated_by": "audit_scope.py",
      "tag": "audit/2026-06-10" | null,
      "anchor_commit": "<sha>" | null,
      "commits_since": <int> | null,
      "scope": "full" | "delta",
      "complexity_available": true | false,
      "files": [
        {"path": "...", "churn": <int>, "complexity": <int|null>, "hotspot_score": <int>}
      ]
    }

One stdout summary line:
``audit_scope: <n> files changed since <tag|full-repo> -> <json-path>``.

Exit codes
----------
0  — ran clean (``scan``/``log-line``) or the tag was created (``tag``).
3  — a git or radon subprocess failed, or (``tag`` only) the tag already
     exists.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

GENERATED_BY = "audit_scope.py"


def _write_json_atomic(path: Path, payload) -> None:
    """Write JSON to *path* atomically: full content to ``<path>.tmp``, then
    ``os.replace`` over the destination — a reader never observes a
    partially-written file (matches audit_bundle's ``_write_manifest``
    pattern)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)

# The well-known SHA of git's empty-tree object — a content-addressed
# constant, not something that needs to pre-exist in any particular repo.
# Diffing against it makes every tracked file show up as pure insertions,
# giving "full" scope a churn number (current file size) with no anchor tag.
EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


class GitError(RuntimeError):
    """Raised when a git subprocess exits nonzero."""


class RadonError(RuntimeError):
    """Raised when a radon subprocess exits nonzero or emits unparsable JSON."""


# ---------------------------------------------------------------------------
# git helpers
# ---------------------------------------------------------------------------


def _run_git(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def _git_or_raise(args: list[str]) -> str:
    result = _run_git(args)
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _latest_audit_tag() -> str | None:
    out = _git_or_raise(["tag", "--list", "audit/*", "--sort=-creatordate"])
    lines = [ln for ln in out.splitlines() if ln.strip()]
    return lines[0] if lines else None


_RENAME_BRACE_RE = re.compile(r"^(.*)\{(.*) => (.*)\}(.*)$")


def _resolve_renamed_path(path: str) -> str:
    """Resolve a ``git diff --numstat`` rename-arrow path to the NEW path.

    Renames are rendered either as the braced form (``dir/{old => new}/f``,
    when old and new share a common prefix/suffix) or the whole-path arrow
    form (``old.py => new.py``, no common prefix/suffix). Either way only
    the NEW path exists on disk — that is what churn should be attributed
    to. Non-rename paths pass through unchanged.
    """
    m = _RENAME_BRACE_RE.match(path)
    if m:
        prefix, _old, new, suffix = m.groups()
        return f"{prefix}{new}{suffix}"
    if " => " in path:
        _, _, new = path.rpartition(" => ")
        return new
    return path


def _numstat(range_spec: str) -> dict[str, tuple[int, int]]:
    """Return ``{path: (insertions, deletions)}`` from ``git diff --numstat``.

    Binary files (numstat reports ``-``/``-``) are skipped. Renames (both
    the braced ``dir/{old => new}/f`` form and the whole-path ``old => new``
    form) are resolved to the NEW path via ``_resolve_renamed_path`` — the
    old path no longer exists on disk, so churn/complexity must attribute to
    the new one.
    """
    out = _git_or_raise(["diff", "--numstat", range_spec])
    result: dict[str, tuple[int, int]] = {}
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        ins, dele, path = parts
        if ins == "-" or dele == "-":
            continue  # binary file — no textual churn signal
        path = _resolve_renamed_path(path)
        result[path] = (int(ins), int(dele))
    return result


# ---------------------------------------------------------------------------
# radon helpers
# ---------------------------------------------------------------------------


def _radon_available() -> bool:
    return shutil.which("radon") is not None


# Chunk size for batched `radon cc -j <p1> <p2> ...` invocations — scope is
# floor-tier "seconds-fast" (design D8e); one subprocess per file measured
# ~76ms/file overhead alone, which doesn't scale. ~50 paths per invocation
# keeps argv comfortably under OS limits while cutting subprocess count by
# ~50x on a large delta.
_RADON_BATCH_SIZE = 50


def _radon_complexity_batch(paths: list[str]) -> dict[str, int]:
    """Max ``complexity`` across radon's block entries for each of *paths*,
    keyed by path (0 for a path with no blocks, e.g. non-Python or empty).

    Paths that no longer exist on disk (deleted since the anchor commit) are
    excluded from the subprocess call entirely — nothing left to analyze —
    and simply absent from the returned dict; callers treat a missing key
    as complexity 0, same as before. Existing paths are chunked into groups
    of ``_RADON_BATCH_SIZE`` and run through ONE ``radon cc -j <p1> <p2>
    ...`` invocation per chunk; radon's JSON response maps each given path
    to its own block list, so results are merged straightforwardly.
    """
    result: dict[str, int] = {}
    existing = [p for p in paths if Path(p).exists()]
    for i in range(0, len(existing), _RADON_BATCH_SIZE):
        chunk = existing[i : i + _RADON_BATCH_SIZE]
        proc = subprocess.run(
            ["radon", "cc", "-j", *chunk], capture_output=True, text=True
        )
        if proc.returncode != 0:
            raise RadonError(
                f"radon cc -j {' '.join(chunk)} failed: {proc.stderr.strip()}"
            )
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise RadonError(
                f"radon cc -j {' '.join(chunk)} produced unparsable JSON: {exc}"
            )
        for path in chunk:
            blocks = data.get(path, [])
            result[path] = max((b.get("complexity", 0) for b in blocks), default=0)
    return result


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------


def cmd_scan(args: argparse.Namespace) -> int:
    try:
        tag = _latest_audit_tag()
        if tag is None:
            scope = "full"
            anchor_commit = None
            commits_since = None
            churn_map = _numstat(f"{EMPTY_TREE_SHA}..HEAD")
        else:
            scope = "delta"
            anchor_commit = _git_or_raise(["rev-parse", f"{tag}^{{commit}}"]).strip()
            commits_since = int(
                _git_or_raise(["rev-list", "--count", f"{tag}..HEAD"]).strip()
            )
            churn_map = _numstat(f"{tag}..HEAD")
    except GitError as exc:
        print(f"audit_scope: INFRA-FAIL — {exc}", file=sys.stderr)
        return 3

    complexity_available = _radon_available()

    complexity_by_path: dict[str, int] = {}
    if complexity_available:
        try:
            complexity_by_path = _radon_complexity_batch(list(churn_map))
        except RadonError as exc:
            print(f"audit_scope: INFRA-FAIL — {exc}", file=sys.stderr)
            return 3

    files = []
    for path, (ins, dele) in churn_map.items():
        churn = ins + dele
        if complexity_available:
            # A deleted-since-anchor path is absent from the batch result —
            # 0 (nothing left to analyze), same semantics as always.
            complexity = complexity_by_path.get(path, 0)
            multiplier = 1 + complexity
        else:
            complexity = None
            multiplier = 1
        files.append(
            {
                "path": path,
                "churn": churn,
                "complexity": complexity,
                "hotspot_score": churn * multiplier,
            }
        )

    files.sort(key=lambda f: f["hotspot_score"], reverse=True)

    payload = {
        "generated_by": GENERATED_BY,
        "tag": tag,
        "anchor_commit": anchor_commit,
        "commits_since": commits_since,
        "scope": scope,
        "complexity_available": complexity_available,
        "files": files,
    }

    json_path = Path(args.json)
    _write_json_atomic(json_path, payload)

    tag_or_full = tag if tag is not None else "full-repo"
    print(f"audit_scope: {len(files)} files changed since {tag_or_full} -> {json_path}")
    return 0


# ---------------------------------------------------------------------------
# tag
# ---------------------------------------------------------------------------


def cmd_tag(args: argparse.Namespace) -> int:
    tag_name = f"audit/{args.date}"

    existing = _run_git(["tag", "--list", tag_name])
    if existing.returncode != 0:
        print(f"audit_scope: INFRA-FAIL — git tag --list failed: {existing.stderr.strip()}", file=sys.stderr)
        return 3
    if existing.stdout.strip():
        print(f"audit_scope: tag {tag_name} already exists — refusing to create a duplicate anchor", file=sys.stderr)
        return 3

    result = _run_git(["tag", "-a", tag_name, "-m", f"audit anchor {args.date}"])
    if result.returncode != 0:
        print(f"audit_scope: INFRA-FAIL — failed to create tag {tag_name}: {result.stderr.strip()}", file=sys.stderr)
        return 3

    print(f"audit_scope: created annotated tag {tag_name}")
    return 0


# ---------------------------------------------------------------------------
# log-line
# ---------------------------------------------------------------------------


def cmd_log_line(args: argparse.Namespace) -> int:
    result = _run_git(["rev-parse", "--short", "HEAD"])
    if result.returncode != 0:
        print(f"audit_scope: INFRA-FAIL — git rev-parse failed: {result.stderr.strip()}", file=sys.stderr)
        return 3
    short_sha = result.stdout.strip()
    print(f"- **{args.date}** · audit/{args.date} · {short_sha} · {args.essence}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_SUBCOMMANDS = ("scan", "tag", "log-line")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:]) if argv is None else list(argv)

    # `scan` is the default subcommand — allow bare flags (e.g. `--json x`)
    # or no args at all without requiring the caller to spell out `scan`.
    if not argv or argv[0] not in _SUBCOMMANDS:
        argv = ["scan", *argv]

    parser = argparse.ArgumentParser(
        description="Audit bookkeeping, delta scope, and hotspot ranking."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser(
        "scan", help="Compute delta/full scope + hotspot ranking (read-only, default)."
    )
    scan_p.add_argument("--json", default="audit_scope.json", help="Output JSON path.")
    scan_p.set_defaults(func=cmd_scan)

    tag_p = sub.add_parser(
        "tag", help="Create the annotated audit/<date> anchor tag (the only mutating op)."
    )
    tag_p.add_argument("--date", required=True, help="Anchor date, YYYY-MM-DD.")
    tag_p.set_defaults(func=cmd_tag)

    log_p = sub.add_parser(
        "log-line", help="Print (never write) the audit-log registry line."
    )
    log_p.add_argument("--date", required=True, help="Audit date, YYYY-MM-DD.")
    log_p.add_argument("--essence", required=True, help="One-line free-text essence.")
    log_p.set_defaults(func=cmd_log_line)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
