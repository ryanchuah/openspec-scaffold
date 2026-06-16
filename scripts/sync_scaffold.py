#!/usr/bin/env python3
"""Scaffold→downstream sync tool.

Copies manifest-listed files byte-identical from the scaffold golden source
to a target repo.  AGENTS.md uses a span-replace algorithm (sync_agents_md)
that preserves each repo's title, ## Project context, and tail.

Usage:
    scripts/sync_scaffold.py <target-repo-path>
    scripts/sync_scaffold.py --check <target-repo-path>
"""

from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import sys
from pathlib import Path


# ── helpers ────────────────────────────────────────────────────────────────

def _scaffold_root() -> Path:
    """The scaffold repo root (parent of the scripts/ directory)."""
    return Path(__file__).resolve().parent.parent


def _manifest_path() -> Path:
    return _scaffold_root() / "scripts" / "scaffold_manifest.txt"


def _read_manifest() -> list[str]:
    """Return non-blank, non-comment lines from the manifest."""
    lines: list[str] = []
    with open(_manifest_path()) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line)
    return lines


# ── D3: AGENTS.md span-replace (header-free) ──────────────────────────────

def sync_agents_md(scaffold_text: str, target_text: str) -> str:
    """Merge shared spans from *scaffold_text* into *target_text*.

    Raises ``ValueError`` if either file is missing a required anchor, if the
    scaffold carries an unexpected tail, or if a long (≥300 line) target has
    no tail separator.
    """
    # --- Scaffold anchors ---
    s_mandatory = re.search(r'^> \*\*MANDATORY', scaffold_text, re.M)
    s_roles = re.search(r'^## Roles\b', scaffold_text, re.M)
    s_after = re.search(r'^## After reading this file', scaffold_text, re.M)
    if not all([s_mandatory, s_roles, s_after]):
        raise ValueError("scaffold AGENTS.md missing required section anchor")

    # Invariant: scaffold must not carry a tail after '## After reading this file'
    if re.search(r'\n(---\s*\n|^# )', scaffold_text[s_after.start():], re.M):
        raise ValueError(
            "scaffold AGENTS.md has unexpected tail — update sync_scaffold.py"
        )

    s_proj_ctx = re.search(r'^## Project context', scaffold_text, re.M)
    span1_end = (s_proj_ctx or s_roles).start()
    span1 = scaffold_text[s_mandatory.start():span1_end]
    span2 = re.sub(r'\s+$', '\n', scaffold_text[s_roles.start():])

    # --- Target anchors ---
    t_mandatory = re.search(r'^> \*\*MANDATORY', target_text, re.M)
    t_proj_ctx = re.search(r'^## Project context', target_text, re.M)
    t_roles = re.search(r'^## Roles\b', target_text, re.M)
    t_after = re.search(r'^## After reading this file', target_text, re.M)
    if not all([t_mandatory, t_roles, t_after]):
        raise ValueError("target AGENTS.md missing required section anchor")

    t_title = target_text[:t_mandatory.start()]   # preserved verbatim — NO header
    proj_ctx = (target_text[t_proj_ctx.start():t_roles.start()]
                if t_proj_ctx else '')

    after_start = t_after.start()
    tail_match = re.search(r'\n(---\s*\n|# \w)', target_text[after_start:], re.M)
    if tail_match:
        tail = target_text[after_start + tail_match.start():]
    else:
        if len(target_text.splitlines()) > 300:
            raise ValueError(
                "target AGENTS.md is long but no tail-separator found — "
                "check anchors"
            )
        tail = ''

    return t_title + span1 + proj_ctx + span2 + tail


# ── Validate-first helpers ─────────────────────────────────────────────────

def _check_target_has_git(target_path: Path) -> None:
    """Raise SystemExit if *target_path* does not contain a .git entry."""
    if not target_path.exists():
        print(f"ERROR: target path does not exist: {target_path}", file=sys.stderr)
        sys.exit(1)
    if not (target_path / ".git").exists():
        print(
            f"ERROR: target path has no .git directory: {target_path}",
            file=sys.stderr,
        )
        sys.exit(1)


def _check_sources_exist(manifest_lines: list[str]) -> None:
    """Raise SystemExit if any manifest-listed source is missing in scaffold."""
    root = _scaffold_root()
    missing = [p for p in manifest_lines if not (root / p).exists()]
    if missing:
        for p in missing:
            print(f"ERROR: scaffold source file missing: {p}", file=sys.stderr)
        sys.exit(1)


# ── Copy pass ──────────────────────────────────────────────────────────────

def _sync_file(manifest_line: str, target_root: Path, scaffold_root: Path) -> None:
    """Copy one manifest entry from scaffold to *target_root*.

    AGENTS.md is routed through ``sync_agents_md``; everything else is a
    byte-identical shutil.copy2.
    """
    src = scaffold_root / manifest_line
    dst = target_root / manifest_line
    dst.parent.mkdir(parents=True, exist_ok=True)

    if manifest_line == "AGENTS.md":
        scaffold_text = src.read_text(encoding="utf-8")
        target_text = dst.read_text(encoding="utf-8") if dst.exists() else ""
        merged = sync_agents_md(scaffold_text, target_text)
        dst.write_text(merged, encoding="utf-8")
    else:
        shutil.copy2(str(src), str(dst))


def sync(target_path_str: str) -> None:
    """Validate preconditions then synchronise manifest-listed files."""
    target_path = Path(target_path_str).resolve()
    _check_target_has_git(target_path)

    manifest_lines = _read_manifest()
    _check_sources_exist(manifest_lines)

    scaffold_root = _scaffold_root()
    for line in manifest_lines:
        _sync_file(line, target_path, scaffold_root)


# ── Check mode ─────────────────────────────────────────────────────────────

def check(target_path_str: str) -> int:
    """Compare target files against scaffold; return 0 if all IDENTICAL else 1."""
    target_path = Path(target_path_str).resolve()
    manifest_lines = _read_manifest()
    scaffold_root = _scaffold_root()
    exit_code = 0

    for line in manifest_lines:
        src = scaffold_root / line
        dst = target_path / line

        if not dst.exists():
            print(f"MISSING  {line}")
            exit_code = 1
            continue

        if line == "AGENTS.md":
            scaffold_text = src.read_text(encoding="utf-8")
            target_text = dst.read_text(encoding="utf-8")
            expected = sync_agents_md(scaffold_text, target_text)
            if expected == target_text:
                print(f"IDENTICAL  {line}")
            else:
                print(f"DIFFERS   {line}")
                exit_code = 1
        else:
            if filecmp.cmp(str(src), str(dst), shallow=False):
                print(f"IDENTICAL  {line}")
            else:
                print(f"DIFFERS   {line}")
                exit_code = 1

    return exit_code


# ── CLI ────────────────────────────────────────────────────────────────────

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync scaffold-managed files to a downstream repo.",
    )
    parser.add_argument(
        "target",
        help="Path to the target repository root",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Drift-report mode: compare files, exit 1 on any difference",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.check:
        return check(args.target)
    sync(args.target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
