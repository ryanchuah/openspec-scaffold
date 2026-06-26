#!/usr/bin/env python3
"""Scaffold→downstream sync tool.

Copies manifest-listed files byte-identical from the scaffold golden source
to a target repo.  AGENTS.md uses a span-replace algorithm (sync_agents_md)
that preserves each repo's title, ## Project context, and tail.
openspec/config.yaml uses a rules-block replace (sync_config_yaml) that
preserves each repo's context: block.

Usage:
    scripts/sync_scaffold.py <target-repo-path>
    scripts/sync_scaffold.py --check <target-repo-path>
    scripts/sync_scaffold.py --check-refs <target-repo-path>
"""

from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import subprocess
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
    scaffold carries an unexpected tail, or if the target's after-section
    carries more content than the scaffold's but no tail separator was found
    (signalling an undetected project tail).
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
        # No separator → no project tail by convention. Backstop: if the
        # target's after-section carries MORE content than the scaffold's,
        # the anchors are likely wrong and we'd be dropping a project tail —
        # abort. (An absolute line cap misfires once the shared span alone
        # crosses it, which it now does for any tail-less downstream repo.)
        s_after_lines = len(scaffold_text[s_after.start():].rstrip().splitlines())
        t_after_lines = len(target_text[after_start:].rstrip().splitlines())
        if t_after_lines > s_after_lines:
            raise ValueError(
                "target AGENTS.md after-section longer than scaffold's but "
                "no tail-separator found — check anchors"
            )
        tail = ''

    return t_title + span1 + proj_ctx + span2 + tail


# ── D-C: openspec/config.yaml rules-block replace ─────────────────────────

def _extract_rules_block(text: str) -> str | None:
    """Return the ``rules:`` block from a config.yaml, or ``None`` if absent.

    The returned string starts at ``rules:`` and runs to EOF, with trailing
    whitespace stripped and a single trailing newline appended.
    """
    m = re.search(r'^rules:', text, re.M)
    if not m:
        return None
    return text[m.start():].rstrip() + "\n"


def sync_config_yaml(scaffold_text: str, target_text: str) -> str:
    """Merge the ``rules:`` block from *scaffold_text* into *target_text*.

    Preserves the target's ``context:`` block and everything above ``rules:``.

    Raises ``ValueError`` if a non-comment top-level key follows ``rules:`` in
    the target (``rules:`` must be the last top-level block — invariant D-C).

    If the target has no ``rules:`` block at all, scaffold's block is appended
    at EOF rather than aborting (supports fresh or pre-``rules:`` repos).
    """
    scaffold_rules = _extract_rules_block(scaffold_text)
    if scaffold_rules is None:
        raise ValueError("scaffold openspec/config.yaml has no rules: block")

    t_rules = re.search(r'^rules:', target_text, re.M)

    if t_rules:
        # Validate: no non-comment top-level key follows rules: in target
        after_rules = target_text[t_rules.end():]
        for line in after_rules.splitlines():
            stripped = line.lstrip()
            if not stripped or stripped.startswith('#'):
                continue
            if re.match(r'^[A-Za-z][\w-]*\s*:', line):
                key = line.split(':')[0].strip()
                raise ValueError(
                    f"openspec/config.yaml: non-comment top-level key "
                    f"'{key}:' follows rules: — move it before rules: or "
                    f"remove it; rules: must be the last top-level block"
                )
        return target_text[:t_rules.start()] + scaffold_rules
    else:
        # Append scaffold's rules: block at EOF
        return target_text.rstrip('\n') + "\n\n" + scaffold_rules


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
    elif manifest_line == "openspec/config.yaml":
        scaffold_text = src.read_text(encoding="utf-8")
        target_text = dst.read_text(encoding="utf-8") if dst.exists() else ""
        merged = sync_config_yaml(scaffold_text, target_text)
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
        elif line == "openspec/config.yaml":
            scaffold_text = src.read_text(encoding="utf-8")
            target_text = dst.read_text(encoding="utf-8")
            scaffold_rules = _extract_rules_block(scaffold_text)
            target_rules = _extract_rules_block(target_text)
            if scaffold_rules == target_rules:
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


# ── Reference-integrity check (--check-refs) ────────────────────────────────
#
# `--check` verifies BYTE convergence (synced files match the scaffold). It does
# NOT verify that the citations *inside* those files resolve to targets that
# exist in the target repo — a synced rule that cites a per-repo state file
# passes IDENTICAL while the cited file is absent downstream. `--check-refs`
# closes that gap. It is a SEPARATE subcommand (own 0/1 exit) so `--check`'s
# contract is untouched.

# Frozen / historical record dirs whose markdown is out of scope for the scan.
# knowledge/research/ holds period-correct historical analyses; its citations must
# NOT be ref-checked (they may cite pre-restructure paths that no longer exist).
_REF_SCAN_EXCLUDE = ("openspec/changes/", "knowledge/research/")
# `knowledge/....md` path citations (e.g. in synced rules).
_KNOWLEDGE_PATH_RE = re.compile(r"knowledge/[\w./-]+\.md")
# `<file>.md § "Section"` citations (any file; we only resolve canonical docs).
# The `§ "..."` form is the project's standard citation format; the loose
# `AGENTS.md (...)` parenthetical form is deliberately NOT matched (it fires on
# explanatory prose) — the one historical parenthetical ref is normalised to the
# `§` form during the repoint, and the standard form is enforced going forward.
_SECTION_RE = re.compile(r"`?([\w./-]+\.md)`?\s*§\s*\"([^\"]+)\"")
# Fenced code blocks — stripped before scanning to avoid illustrative-example
# false positives (inline-backtick citations stay in scope).
_FENCED_RE = re.compile(r"```.*?```", re.S)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def _tracked_markdown(repo: Path) -> list[str]:
    """Repo-relative markdown to scan: git-tracked if available, else a walk.

    Excludes frozen/historical record directories (`_REF_SCAN_EXCLUDE`).
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "ls-files", "*.md"],
            capture_output=True, text=True, check=True,
        ).stdout
        rels = [ln for ln in out.splitlines() if ln]
    except (FileNotFoundError, subprocess.CalledProcessError):
        rels = [str(p.relative_to(repo)) for p in sorted(repo.rglob("*.md"))]
    return [r for r in rels if not any(x in r for x in _REF_SCAN_EXCLUDE)]


_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")


def _section_anchors(path: Path) -> list[str]:
    """Normalised AGENTS.md section anchors: `#` headings AND bold inline labels.

    Many AGENTS.md rules are cited by a bold label (e.g. ``**STATUS.md cap rule:**``)
    rather than a heading, so both are valid citation targets.
    """
    if not path.exists():
        return []
    anchors: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            anchors.append(_norm(line.lstrip("#").strip()))
    anchors.extend(_norm(m.group(1)) for m in _BOLD_RE.finditer(text))
    return anchors


def _synced_files() -> list[str]:
    """Manifest entries that carry inline citations: AGENTS.md + synced knowledge/*.md."""
    return [
        line for line in _read_manifest()
        if line == "AGENTS.md" or (line.startswith("knowledge/") and line.endswith(".md"))
    ]


def check_references(target_path_str: str, md_files: list[str] | None = None) -> int:
    """Verify cited files/sections resolve in the target repo. 0 = clean, 1 = dangling.

    - ``knowledge/*.md`` path citations in the SYNCED files (AGENTS.md + synced knowledge/)
      must point at files that exist in the target.
    - ``AGENTS.md``/``knowledge/*`` section citations (``§ "..."``) anywhere in tracked
      markdown must point at a file that exists; AGENTS.md citations must also
      resolve to a heading or bold label (substring match). Section *titles* in
      ``knowledge/*`` are NOT resolved — their headings carry drifting qualifiers
      (dates, ``…`` ellipses), so only file existence is policed there.
    """
    target = Path(target_path_str).resolve()
    rels = md_files if md_files is not None else _tracked_markdown(target)
    agents_anchors = _section_anchors(target / "AGENTS.md")
    dangling = 0

    # (a) knowledge/*.md path citations in the synced files must exist.
    for rel in _synced_files():
        p = target / rel
        if not p.exists():
            continue
        text = _FENCED_RE.sub("", p.read_text(encoding="utf-8", errors="replace"))
        for m in _KNOWLEDGE_PATH_RE.finditer(text):
            cited = m.group(0)
            if not (target / cited).exists():
                print(f"DANGLING  {rel}: missing file '{cited}'")
                dangling += 1

    # (b) section citations to canonical docs anywhere: file must exist; for
    #     AGENTS.md the section must also resolve (other docs' titles drift).
    for rel in rels:
        p = target / rel
        if not p.exists():
            continue
        text = _FENCED_RE.sub("", p.read_text(encoding="utf-8", errors="replace"))
        for m in _SECTION_RE.finditer(text):
            cited_file, section = m.group(1), m.group(2)
            if cited_file != "AGENTS.md" and not cited_file.startswith("knowledge/"):
                continue
            if not (target / cited_file).exists():
                print(f"DANGLING  {rel}: missing file '{cited_file}' (§ '{section}')")
                dangling += 1
            elif cited_file == "AGENTS.md":
                # Citation must be contained in a real anchor (anchor may carry a
                # trailing ':' or qualifier). NOT the reverse — a short bold
                # emphasis span must not mask a longer dangling citation.
                n = _norm(section)
                if not any(n in a for a in agents_anchors):
                    print(f"DANGLING  {rel}: AGENTS.md has no section '{n}'")
                    dangling += 1

    if dangling:
        print(f"FAIL  {dangling} dangling reference(s)")
        return 1
    print(f"OK  no dangling references ({len(rels)} markdown files scanned)")
    return 0


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
    parser.add_argument(
        "--check-refs",
        action="store_true",
        help="Reference-integrity mode: exit 1 if a cited file/section is missing",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.check_refs:
        return check_references(args.target)
    if args.check:
        return check(args.target)
    sync(args.target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
