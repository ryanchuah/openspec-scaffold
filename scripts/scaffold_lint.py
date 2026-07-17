#!/usr/bin/env python3
"""scaffold_lint.py — stdlib-only, detect-only linter over this repo's own
mechanized invariants.

This is an **authoring-side** tool, like ``scripts/sync_scaffold.py`` — it is
deliberately NOT listed in ``scripts/scaffold_manifest.txt`` and never syncs
downstream (see the exclusion list documented under ``manifest-completeness``
below, which encodes exactly this).

Usage
-----
    python3 scripts/scaffold_lint.py [--root PATH]

Default ``--root`` is this script's grandparent directory (the repo root),
mirroring the root-resolution convention used by ``scripts/knowledge_lint.py``
and ``scripts/scaffold_check.py``.

Exit codes
----------
0 — no findings.
1 — one or more findings (matches ``sync_scaffold.py --check`` /
    ``knowledge_lint.py``'s drift-diagnostic convention).

Each finding is printed as exactly one stdout line:

    scaffold-lint: <check-id>: <detail>

All seven checks run even after an earlier one has produced findings — this
script reports everything in one pass, then exits 1. If all checks are
clean, it prints ``scaffold-lint: clean`` and exits 0.

Checks
------

  manifest-completeness
    Every existing file matching the managed globs — ``.claude/skills/*/SKILL.md``,
    ``.claude/skills/_shared/*.md``, ``.claude/agents/*.md``,
    ``.opencode/agents/*.md``, and ``scripts/*`` — must be listed in
    ``scripts/scaffold_manifest.txt`` OR match the exclusion list below. All
    five globs are filtered to plain files only (``scripts/`` in particular
    mixes files and directories like ``__pycache__/``, so this filter
    matters there). Reverse direction is checked too: every manifest entry
    must exist on disk. Missing either way is a finding.

    Exclusion list (authoring-side tooling that is deliberately never
    manifest-listed / never synced downstream):
      ``scripts/scaffold_manifest_removed.txt``,
      ``scripts/sync_scaffold.py``, ``scripts/test_sync_scaffold.py``,
      ``scripts/scaffold_lint.py``, ``scripts/test_scaffold_lint.py``,
      ``scripts/test-cmd``, and the glob ``scripts/_*_oneoff.*``.

  manifest-no-conflict
    A path may not appear in both ``scripts/scaffold_manifest.txt`` AND
    ``scripts/scaffold_manifest_removed.txt`` (normalised by stripping
    trailing ``/``). If the same normalised path is in both files, that
    is a finding naming the path — the live manifest says "copy this"
    while the removed manifest says "delete this", which is contradictory
    and can never be resolved.

  agents-md-structure
    Two sub-checks over ``AGENTS.md`` (the reused ``sync_scaffold`` span
    function only detects anchor *presence*, not *uniqueness* — these are
    deliberately separate mechanisms, not conflated):
    (a) **uniqueness** — for each of the three anchor strings
        (``> **MANDATORY``, ``## Roles``, ``## After reading this file``),
        count matching lines via ``line.startswith(anchor)`` (never
        ``str.count()``, which would also match inside a fenced code
        block). A count other than exactly 1 is a finding.
    (b) **presence + no-tail** — reuses ``sync_scaffold.sync_agents_md``
        (imported) by running it against this repo's own ``AGENTS.md`` as
        BOTH source and target; any ``ValueError`` it raises becomes a
        finding.

  config-rules-last
    Two sub-checks over ``openspec/config.yaml``:
    (a) **missing block** — reuses ``sync_scaffold._extract_rules_block``
        (imported); ``None`` (no ``rules:`` block found) is a finding.
    (b) **trailing keys** — reuses ``sync_scaffold.sync_config_yaml``
        (imported), calling it with this repo's own config as BOTH source
        and target; any ``ValueError`` it raises becomes a finding. (When
        the block is entirely missing, ``sync_config_yaml`` appends rather
        than raising — which is why (a) is a separate, explicit sub-check.)

  dangling-skill-refs
    Scans ``AGENTS.md`` plus every ``.md`` file under ``.claude/skills/``
    (recursive — ``_shared/*.md`` is intentionally included and expected
    to stay clean), ``.claude/agents/``, and ``.opencode/agents/`` for
    tokens matching ``\\bopenspec-[a-z][a-z-]*[a-z]\\b``, plus any token in
    the non-``openspec-`` scan vocabulary derived from
    ``scripts/scaffold_manifest_removed.txt`` (every tombstoned
    ``.claude/skills/<name>/`` directory entry contributes its ``<name>``;
    non-skill entries and a missing/unreadable manifest contribute nothing).
    Every matched token must resolve to one of: a skill directory name under
    ``.claude/skills/``, an agent file stem under ``.claude/agents/`` or
    ``.opencode/agents/``, or the allowlist constant
    ``{"openspec-scaffold"}``. An unresolved token is a finding naming the
    file and the token.

  budget-agreement
    Extracts every numeric ``timeout -k <G> <B>`` pair (regex
    ``timeout\\s+-k\\s+(\\d+)\\s+(\\d+)`` — the literal ``timeout`` prefix is
    deliberate: this check targets executable copy-paste command blocks,
    not descriptive prose) from the same file set as ``dangling-skill-refs``.
    The set of sanctioned pairs is parsed from
    ``.claude/skills/_shared/delegation-harness.md``'s §e table: iterate
    the file's lines, and on each line starting with ``|`` (a markdown
    table row) apply `` `-k (\\d+) (\\d+)` `` (backtick-quoted flags cell)
    and collect all matches — never split on ``|`` (inline code spans
    elsewhere in the file legitimately contain pipes). Any embedded pair
    not in the sanctioned set is a finding naming the file, line, and pair.
    Two distinct infra findings: no line in the harness file starts with
    ``## (e)`` -> ``budget-agreement: §e table not found``; table rows were
    found but zero pairs were extracted from them ->
    ``budget-agreement: could not parse §e table``.

  model-id-agreement
    Extracts every ``deepseek[-/]v[0-9][-a-z_]*``-shaped token (regex
    ``\\bdeepseek[-/]v\\d[-\\w]*``) from the same file set as
    ``dangling-skill-refs``. Every matched token must be in the set of
    sanctioned model IDs parsed from ``.claude/skills/_shared/
    delegation-harness.md``'s §(f) table: iterate the file's lines, and on
    each line starting with ``|`` (a markdown table row) apply
    `` `(deepseek[-/][^`]+)` `` (backtick-quoted model ID cell) and
    collect all matches. Any token not in the sanctioned set is a finding
    naming the file, line, and token. Two distinct infra findings: no
    line in the harness file starts with ``## (f)`` ->
    ``model-id-agreement: §(f) table not found``; table rows were found
    but zero IDs were extracted from them ->
    ``model-id-agreement: could not parse §(f) table``.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys
from pathlib import Path

# Import sync_scaffold as a sibling module (same import pattern used by
# scripts/test_sync_scaffold.py) so agents-md-structure(b) and
# config-rules-last(b) reuse its span/rules-block logic rather than
# duplicating the extraction regexes.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sync_scaffold  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# manifest-completeness
_MANAGED_GLOBS: tuple[str, ...] = (
    ".claude/skills/*/SKILL.md",
    ".claude/skills/_shared/*.md",
    ".claude/agents/*.md",
    ".opencode/agents/*.md",
    "scripts/*",
)

_MANIFEST_EXCLUDE_EXACT: frozenset[str] = frozenset(
    {
        "scripts/scaffold_manifest_removed.txt",
        "scripts/sync_scaffold.py",
        "scripts/test_sync_scaffold.py",
        "scripts/scaffold_lint.py",
        "scripts/test_scaffold_lint.py",
        "scripts/test-cmd",
        # Scaffold-only: propagation is always run FROM the golden source, so the
        # propagate-scaffold skill is authoring-side (like sync_scaffold.py) and is
        # deliberately NOT synced downstream.
        ".claude/skills/propagate-scaffold/SKILL.md",
    }
)
_MANIFEST_EXCLUDE_GLOB = "scripts/_*_oneoff.*"

# dangling-skill-refs / budget-agreement shared scan surface
_SCAN_BASE_DIRS: tuple[str, ...] = (
    ".claude/skills",
    ".claude/agents",
    ".opencode/agents",
)

# dangling-skill-refs
_TOKEN_RE = re.compile(r"\bopenspec-[a-z][a-z-]*[a-z]\b")
# Non-openspec skills have no shared prefix to pattern-match, so they need an
# explicit scan vocabulary — unlike openspec-* names, which _TOKEN_RE matches
# for free. That vocabulary is tombstone-derived (see
# _removed_skill_names below) from scripts/scaffold_manifest_removed.txt
# rather than hand-maintained, so it cannot drift the way a hardcoded set did
# (D1 in this change's notes.md): every retired skill dir tombstoned there is
# in scope for removed-name detection, and a current skill dir can never
# false-positive because valid_tokens is disk-derived.
_DANGLING_ALLOWLIST: frozenset[str] = frozenset({"openspec-scaffold"})

# budget-agreement
_HARNESS_REL_PATH = ".claude/skills/_shared/delegation-harness.md"
_EMBEDDED_PAIR_RE = re.compile(r"timeout\s+-k\s+(\d+)\s+(\d+)")
_TABLE_CELL_PAIR_RE = re.compile(r"`-k (\d+) (\d+)`")

# model-id-agreement
_MODEL_ID_TOKEN_RE = re.compile(r"\bdeepseek[-/]v\d[-\w]*")
_TABLE_CELL_MODEL_ID_RE = re.compile(r"`(deepseek[-/][^`]+)`")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _scan_file_set(root: Path) -> list[Path]:
    """AGENTS.md + every .md (recursive) under the three scan base dirs.

    Shared by dangling-skill-refs, budget-agreement, and model-id-agreement.
    """
    files: list[Path] = []
    agents_md = root / "AGENTS.md"
    if agents_md.is_file():
        files.append(agents_md)
    for base in _SCAN_BASE_DIRS:
        base_dir = root / base
        if base_dir.is_dir():
            files.extend(sorted(base_dir.rglob("*.md")))
    return files


# ---------------------------------------------------------------------------
# Check: manifest-completeness
# ---------------------------------------------------------------------------


def _read_manifest_entries(root: Path) -> set[str]:
    manifest = root / "scripts" / "scaffold_manifest.txt"
    entries: set[str] = set()
    with manifest.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                entries.add(line)
    return entries


def _managed_files(root: Path) -> set[str]:
    found: set[str] = set()
    for pattern in _MANAGED_GLOBS:
        for p in root.glob(pattern):
            if p.is_file():
                found.add(p.relative_to(root).as_posix())
    return found


def _is_manifest_excluded(rel: str) -> bool:
    if rel in _MANIFEST_EXCLUDE_EXACT:
        return True
    return fnmatch.fnmatch(rel, _MANIFEST_EXCLUDE_GLOB)


def check_manifest_completeness(root: Path) -> list[str]:
    findings: list[str] = []
    manifest_path = root / "scripts" / "scaffold_manifest.txt"
    if not manifest_path.is_file():
        return ["manifest-completeness: scripts/scaffold_manifest.txt not found"]

    manifest_entries = _read_manifest_entries(root)
    managed = _managed_files(root)

    for rel in sorted(managed):
        if _is_manifest_excluded(rel):
            continue
        if rel not in manifest_entries:
            findings.append(
                f"manifest-completeness: {rel} exists but is not listed in "
                f"scripts/scaffold_manifest.txt"
            )

    for rel in sorted(manifest_entries):
        if not (root / rel).exists():
            findings.append(f"manifest-completeness: manifest entry {rel} does not exist on disk")

    return findings


# ---------------------------------------------------------------------------
# Check: manifest-no-conflict
# ---------------------------------------------------------------------------


def _read_removed_manifest_entries(root: Path) -> set[str]:
    """Return the normalised set of non-blank, non-comment lines from
    ``scaffold_manifest_removed.txt``, with trailing ``/`` stripped.
    Returns an empty set if the file does not exist."""
    path = root / "scripts" / "scaffold_manifest_removed.txt"
    if not path.is_file():
        return set()
    entries: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                entries.add(line.rstrip("/"))
    return entries


def check_manifest_no_conflict(root: Path) -> list[str]:
    """A path may not appear in both scaffold_manifest.txt and
    scaffold_manifest_removed.txt (normalised by stripping trailing /)."""
    findings: list[str] = []
    manifest_path = root / "scripts" / "scaffold_manifest.txt"
    if not manifest_path.is_file():
        return findings  # manifest absent → nothing to conflict with

    # Reuse the existing helper but normalise
    manifest_entries = {p.rstrip("/") for p in _read_manifest_entries(root)}
    removed_entries = _read_removed_manifest_entries(root)
    conflicts = manifest_entries & removed_entries
    for c in sorted(conflicts):
        findings.append(
            f"manifest-no-conflict: {c} appears in both "
            f"scripts/scaffold_manifest.txt and "
            f"scripts/scaffold_manifest_removed.txt"
        )
    return findings


# ---------------------------------------------------------------------------
# Check: agents-md-structure
# ---------------------------------------------------------------------------


def check_agents_md_structure(root: Path) -> list[str]:
    findings: list[str] = []
    agents_path = root / "AGENTS.md"
    if not agents_path.is_file():
        return ["agents-md-structure: AGENTS.md not found"]

    text = agents_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # (a) uniqueness — per-line startswith, the SAME method for all three.
    for anchor in sync_scaffold.AGENTS_ANCHORS:
        count = sum(1 for line in lines if line.startswith(anchor))
        if count != 1:
            findings.append(
                f"agents-md-structure: anchor {anchor!r} appears {count} time(s) "
                f"in AGENTS.md (expected exactly 1)"
            )

    # (b) presence + no-tail — reuse sync_scaffold.sync_agents_md, source ==
    # target == this repo's own AGENTS.md.
    try:
        sync_scaffold.sync_agents_md(text, text)
    except ValueError as exc:
        findings.append(f"agents-md-structure: {exc}")

    return findings


# ---------------------------------------------------------------------------
# Check: config-rules-last
# ---------------------------------------------------------------------------


def check_config_rules_last(root: Path) -> list[str]:
    findings: list[str] = []
    config_path = root / "openspec" / "config.yaml"
    if not config_path.is_file():
        return ["config-rules-last: openspec/config.yaml not found"]

    text = config_path.read_text(encoding="utf-8")

    # (a) missing block — reuse sync_scaffold._extract_rules_block.
    if sync_scaffold._extract_rules_block(text) is None:
        findings.append("config-rules-last: no rules: block found in openspec/config.yaml")

    # (b) trailing keys — reuse sync_scaffold.sync_config_yaml, source ==
    # target == this repo's own config.
    try:
        sync_scaffold.sync_config_yaml(text, text)
    except ValueError as exc:
        findings.append(f"config-rules-last: {exc}")

    return findings


# ---------------------------------------------------------------------------
# Check: dangling-skill-refs
# ---------------------------------------------------------------------------


def _skill_dir_names(root: Path) -> set[str]:
    skills_dir = root / ".claude" / "skills"
    if not skills_dir.is_dir():
        return set()
    return {p.name for p in skills_dir.iterdir() if p.is_dir()}


def _agent_file_stems(root: Path) -> set[str]:
    stems: set[str] = set()
    for base in (".claude/agents", ".opencode/agents"):
        base_dir = root / base
        if base_dir.is_dir():
            for p in base_dir.glob("*.md"):
                stems.add(p.stem)
    return stems


def _removed_skill_names(root: Path) -> set[str]:
    """Return the set of retired skill names — the ``<name>`` in each
    ``.claude/skills/<name>/`` directory entry tombstoned in
    ``scripts/scaffold_manifest_removed.txt`` (reusing
    ``_read_removed_manifest_entries``, which already ignores comments and
    blanks). Non-skill entries (e.g. ``scripts/audit_bundle.py``) contribute
    no token. A missing or unreadable manifest yields an empty set — this
    check is manifest-optional, same as manifest-no-conflict."""
    names: set[str] = set()
    for entry in _read_removed_manifest_entries(root):
        match = re.fullmatch(r"\.claude/skills/([^/]+)", entry)
        if match:
            names.add(match.group(1))
    return names


def check_dangling_skill_refs(root: Path, scanned: list[tuple[Path, str]]) -> list[str]:
    findings: list[str] = []
    valid_tokens = _skill_dir_names(root) | _agent_file_stems(root) | _DANGLING_ALLOWLIST
    non_openspec_vocab = _removed_skill_names(root)

    for path, text in scanned:
        rel = path.relative_to(root).as_posix()

        tokens: set[str] = set(_TOKEN_RE.findall(text))
        for t in non_openspec_vocab:
            if re.search(rf"\b{re.escape(t)}\b", text):
                tokens.add(t)

        for token in sorted(tokens):
            if token not in valid_tokens:
                findings.append(f"dangling-skill-refs: {rel}: unknown token {token!r}")

    return findings


# ---------------------------------------------------------------------------
# Check: budget-agreement
# ---------------------------------------------------------------------------


def _sanctioned_pairs(root: Path) -> tuple[set[tuple[str, str]], list[str]]:
    """Return (sanctioned pairs, infra findings) parsed from the §e table in
    .claude/skills/_shared/delegation-harness.md."""
    findings: list[str] = []
    harness_path = root / _HARNESS_REL_PATH

    if not harness_path.is_file():
        findings.append(f"budget-agreement: {_HARNESS_REL_PATH} not found")
        return set(), findings

    lines = harness_path.read_text(encoding="utf-8").splitlines()

    if not any(line.startswith("## (e)") for line in lines):
        findings.append("budget-agreement: §e table not found")
        return set(), findings

    table_row_found = False
    pairs: set[tuple[str, str]] = set()
    for line in lines:
        if line.startswith("|"):
            table_row_found = True
            for m in _TABLE_CELL_PAIR_RE.finditer(line):
                pairs.add((m.group(1), m.group(2)))

    if table_row_found and not pairs:
        findings.append("budget-agreement: could not parse §e table")

    return pairs, findings


def check_budget_agreement(root: Path, scanned: list[tuple[Path, str]]) -> list[str]:
    sanctioned, findings = _sanctioned_pairs(root)

    for path, text in scanned:
        rel = path.relative_to(root).as_posix()
        lines = text.splitlines()
        for lineno, line in enumerate(lines, start=1):
            for m in _EMBEDDED_PAIR_RE.finditer(line):
                pair = (m.group(1), m.group(2))
                if pair not in sanctioned:
                    findings.append(
                        f"budget-agreement: {rel}:{lineno}: pair "
                        f"(-k {pair[0]} {pair[1]}) not in the sanctioned "
                        f"§e budget set"
                    )

    return findings


# ---------------------------------------------------------------------------
# Check: model-id-agreement
# ---------------------------------------------------------------------------


def _sanctioned_model_ids(root: Path) -> tuple[set[str], list[str]]:
    """Return (sanctioned model IDs, infra findings) parsed from the §(f)
    table in .claude/skills/_shared/delegation-harness.md."""
    findings: list[str] = []
    harness_path = root / _HARNESS_REL_PATH

    if not harness_path.is_file():
        findings.append(f"model-id-agreement: {_HARNESS_REL_PATH} not found")
        return set(), findings

    lines = harness_path.read_text(encoding="utf-8").splitlines()

    if not any(line.startswith("## (f)") for line in lines):
        findings.append("model-id-agreement: §(f) table not found")
        return set(), findings

    table_row_found = False
    ids: set[str] = set()
    for line in lines:
        if line.startswith("|"):
            table_row_found = True
            for m in _TABLE_CELL_MODEL_ID_RE.finditer(line):
                ids.add(m.group(1))

    if table_row_found and not ids:
        findings.append("model-id-agreement: could not parse §(f) table")

    return ids, findings


def check_model_id_agreement(root: Path, scanned: list[tuple[Path, str]]) -> list[str]:
    sanctioned, findings = _sanctioned_model_ids(root)

    for path, text in scanned:
        rel = path.relative_to(root).as_posix()
        lines = text.splitlines()
        for lineno, line in enumerate(lines, start=1):
            for m in _MODEL_ID_TOKEN_RE.finditer(line):
                token = m.group(0)
                if token not in sanctioned:
                    findings.append(
                        f"model-id-agreement: {rel}:{lineno}: model ID "
                        f"{token!r} not in the sanctioned §(f) set"
                    )

    return findings


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def collect_findings(root: Path) -> list[str]:
    """Run every check and return the combined finding list (unprefixed —
    each string already begins with its own check-id)."""
    scanned = [(p, p.read_text(encoding="utf-8", errors="replace")) for p in _scan_file_set(root)]

    findings: list[str] = []
    findings.extend(check_manifest_completeness(root))
    findings.extend(check_manifest_no_conflict(root))
    findings.extend(check_agents_md_structure(root))
    findings.extend(check_config_rules_last(root))
    findings.extend(check_dangling_skill_refs(root, scanned))
    findings.extend(check_budget_agreement(root, scanned))
    findings.extend(check_model_id_agreement(root, scanned))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect-only linter over this repo's mechanized scaffold invariants."
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Repository root (default: this script's grandparent dir).",
    )
    args = parser.parse_args(argv)

    if args.root is not None:
        root = Path(args.root).resolve(strict=True)
    else:
        root = Path(__file__).resolve().parent.parent

    findings = collect_findings(root)
    for finding in findings:
        print(f"scaffold-lint: {finding}")

    if findings:
        return 1

    print("scaffold-lint: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
