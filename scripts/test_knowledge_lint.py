#!/usr/bin/env python3
"""Tests for knowledge_lint.py — pytest style, `tmp_path`-fixture based.

No git and no real repo are required: every test builds a synthetic
``knowledge/`` tree under pytest's `tmp_path` fixture and runs the linter
against it directly.
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import knowledge_lint  # noqa: E402

# ===================================================================
# Helpers
# ===================================================================


def _write_tree(root: Path, files: dict[str, str]) -> None:
    """Write *files* (repo-relative path -> text content) under *root*,
    creating parent directories as needed. The `tmp_path`-based synthetic
    tree this builds needs no git and no real repo."""
    for relpath, content in files.items():
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _snapshot(root: Path) -> dict[str, bytes]:
    """Return {relpath: content-bytes} for every file under *root* — used to
    assert the tree is byte-identical before/after a lint run."""
    snap: dict[str, bytes] = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in filenames:
            full = Path(dirpath) / filename
            snap[str(full.relative_to(root))] = full.read_bytes()
    return snap


def _run_main(root: Path, extra_args: list[str] | None = None) -> tuple[int, str]:
    argv = ["--root", str(root)] + (extra_args or [])
    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = knowledge_lint.main(argv)
    return exit_code, buf.getvalue()


# ===================================================================
# 2.2 — one-instance-per-class drift fixture
# ===================================================================

_DRIFT_TREE = {
    # 1. orphan/duplicate canonical file — a root STATUS.md.
    "STATUS.md": "# Status (stray root copy)\n",
    # 2/3/4 — retired-path token, broken citation, dangling archive
    # pointer, each on its own isolated line so no check double-fires.
    "knowledge/reference/notes.md": (
        "# Reference Notes\n"
        "\n"
        "This runbook lives at ai-docs/old-notes.md for now.\n"
        "\n"
        "See `knowledge/missing.md` for details.\n"
        "\n"
        "Follow-up tracked in openspec/changes/archive/2026-01-01-ghost-change/design.md.\n"
    ),
    # 5. audit-log registry format — malformed entry line.
    "knowledge/audit-log.md": ("# Audit Log\n\n- **2026-01-01** · missing fields\n"),
}


def test_one_instance_per_class_drift_fixture_exact_findings(tmp_path):
    _write_tree(tmp_path, _DRIFT_TREE)

    findings = knowledge_lint.collect_findings(tmp_path)
    by_check = {f.check for f in findings}

    assert len(findings) == 5
    assert by_check == {
        "orphan-or-duplicate-canonical-file",
        "retired-path-token",
        "broken-prose-path-citation",
        "dangling-archive-pointer",
        "audit-log-registry-format",
    }

    paths = {f.path for f in findings}
    assert paths == {
        "STATUS.md",
        "knowledge/reference/notes.md",
        "knowledge/audit-log.md",
    }

    exit_code, stdout = _run_main(tmp_path)
    assert exit_code == 1
    assert "knowledge_lint: FAILED" in stdout


# ===================================================================
# 2.3 — drift-free fixture
# ===================================================================

_CLEAN_TREE = {
    "knowledge/STATUS.md": "# Status\nAll good.\n",
    "knowledge/lessons.md": "# Lessons\nNone yet.\n",
    "knowledge/roadmap.md": "# Roadmap\nNothing planned.\n",
    "knowledge/reference/notes.md": (
        "# Reference Notes\n\nEverything here resolves and cites nothing retired.\n"
    ),
    "knowledge/audit-log.md": (
        "# Audit Log\n\n- **2026-01-01** · audit/2026-01-01 · abc1234 · a clean audit\n"
    ),
}


def test_drift_free_fixture_zero_findings_exit_0(tmp_path):
    _write_tree(tmp_path, _CLEAN_TREE)

    findings = knowledge_lint.collect_findings(tmp_path)
    assert findings == []

    exit_code, stdout = _run_main(tmp_path)
    assert exit_code == 0
    assert "knowledge_lint: OK" in stdout


# ===================================================================
# 2.4 — detect-only: tree byte-identical before/after, drift and clean
# ===================================================================


def test_detect_only_tree_unchanged_drift_case(tmp_path):
    _write_tree(tmp_path, _DRIFT_TREE)
    before = _snapshot(tmp_path)
    exit_code, _stdout = _run_main(tmp_path)
    after = _snapshot(tmp_path)
    assert exit_code == 1
    assert before == after


def test_detect_only_tree_unchanged_clean_case(tmp_path):
    _write_tree(tmp_path, _CLEAN_TREE)
    before = _snapshot(tmp_path)
    exit_code, _stdout = _run_main(tmp_path)
    after = _snapshot(tmp_path)
    assert exit_code == 0
    assert before == after


# ===================================================================
# 2.5 — audit-log guard: absent (skip, no error) / malformed (flagged)
# ===================================================================


def test_audit_log_absent_is_skipped_silently(tmp_path):
    _write_tree(tmp_path, {"knowledge/reference/notes.md": "# Notes\n\nNothing wrong here.\n"})
    assert not (tmp_path / "knowledge" / "audit-log.md").exists()

    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "audit-log-registry-format" for f in findings)

    exit_code, _stdout = _run_main(tmp_path)
    assert exit_code == 0


def test_audit_log_present_and_malformed_flags_bad_line(tmp_path):
    _write_tree(
        tmp_path,
        {
            "knowledge/audit-log.md": (
                "# Audit Log\n"
                "\n"
                "- **2026-01-01** · audit/2026-01-01 · abc1234 · a valid entry\n"
                "- **2026-01-02** not even close to the format\n"
            )
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    audit_findings = [f for f in findings if f.check == "audit-log-registry-format"]
    assert len(audit_findings) == 1
    assert audit_findings[0].path == "knowledge/audit-log.md"
    assert audit_findings[0].line == 4


# ===================================================================
# 2.6 — per-repo config: checks.toml retired_paths merges with defaults
# ===================================================================


def test_no_audit_toml_only_default_tokens_flag(tmp_path):
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": (
                "Cites ai-docs/legacy.md (default token) and old-legacy/thing.md "
                "(custom token, not yet configured).\n"
            )
        },
    )
    assert not (tmp_path / "checks.toml").exists()

    findings = knowledge_lint.collect_findings(tmp_path)
    retired = [f for f in findings if f.check == "retired-path-token"]
    assert len(retired) == 1
    assert "ai-docs/" in retired[0].message


def test_audit_toml_retired_paths_extend_defaults(tmp_path):
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": (
                "Cites ai-docs/legacy.md (default token) and old-legacy/thing.md "
                "(custom token, now configured).\n"
            ),
            "checks.toml": '[knowledge_lint]\nretired_paths = ["old-legacy/"]\n',
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    retired = [f for f in findings if f.check == "retired-path-token"]
    assert len(retired) == 2
    messages = {f.message for f in retired}
    assert any("ai-docs/" in m for m in messages)
    assert any("old-legacy/" in m for m in messages)


# ===================================================================
# 2.7 — knowledge/research/ exclusion (retired-path + broken citation)
# ===================================================================


def test_research_dir_excluded_from_content_checks(tmp_path):
    drift_line = (
        "Historical note: cites ai-docs/legacy.md (retired token) "
        "and `knowledge/gone/file.md` (broken citation).\n"
    )
    _write_tree(
        tmp_path,
        {
            "knowledge/research/old-analysis.md": drift_line,
            "knowledge/reference/current.md": drift_line,
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)

    research_findings = [f for f in findings if f.path.startswith("knowledge/research/")]
    assert research_findings == []

    outside_findings = [f for f in findings if f.path == "knowledge/reference/current.md"]
    outside_checks = {f.check for f in outside_findings}
    assert outside_checks == {"retired-path-token", "broken-prose-path-citation"}


# ===================================================================
# 2.8 — orphan exclusions (INDEX.md/README.md) + duplicate sub-case
# ===================================================================


def test_orphan_exclusions_and_duplicate_subcase(tmp_path):
    _write_tree(
        tmp_path,
        {
            "INDEX.md": "# Index\n",
            "README.md": "# Readme\n",
            "STATUS.md": "# Status (stray root copy)\n",
            "knowledge/STATUS.md": "# Status (canonical)\n",
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    orphan_findings = [f for f in findings if f.check == "orphan-or-duplicate-canonical-file"]

    assert len(orphan_findings) == 1
    assert orphan_findings[0].path == "STATUS.md"


# ===================================================================
# 2.9 — negative citation cases (broken-prose-path-citation-flagged)
# ===================================================================


def test_negative_citation_cases_not_flagged(tmp_path):
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": (
                "Bare mention: docs/nowhere.md should not be flagged (no backticks).\n"
                "\n"
                "See `https://example.com/gone.md` for background "
                "(URL, backtick-wrapped, not flagged).\n"
                "\n"
                "Also `/home/nope/gone.md` is an absolute path "
                "(backtick-wrapped, not flagged).\n"
            )
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "broken-prose-path-citation" for f in findings)


def test_negative_citation_cases_extended_exclusions_not_flagged(tmp_path):
    """Live-verified refinements (found running against this scaffold's own
    knowledge/ tree): tilde-home paths, angle-bracket template placeholders,
    glob patterns, and whitespace-containing command/prose fragments are
    NOT real repo-relative path citations, even backtick-wrapped."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": (
                "Tilde home path: `~/.claude/gone.md` is absolute, not flagged.\n"
                "\n"
                "Placeholder: `openspec/changes/archive/<dir>/gone.md` is a format "
                "example, not flagged.\n"
                "\n"
                "Glob: `checks/*.sql` is a pattern, not flagged.\n"
                "\n"
                "Command fragment: `scripts/sync_scaffold.py --check <repo>` has "
                "embedded whitespace, not flagged.\n"
            )
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "broken-prose-path-citation" for f in findings)


def test_ephemeral_handoff_citation_not_flagged(tmp_path):
    """`knowledge/HANDOFF.md` is a known-ephemeral path (written mid-change,
    deleted on absorption) — citing it is NOT a broken citation even when the
    file is absent. A citation to a genuinely-missing, non-ephemeral path
    must still be flagged (guards against over-broad suppression)."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": (
                "See `knowledge/HANDOFF.md` for the in-flight session handoff.\n"
                "\n"
                "See `knowledge/does-not-exist.md` for details.\n"
            )
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    citation_findings = [f for f in findings if f.check == "broken-prose-path-citation"]
    assert not any("HANDOFF.md" in f.message for f in citation_findings)
    assert any("does-not-exist.md" in f.message for f in citation_findings)


def test_dangling_archive_pointer_placeholder_not_flagged(tmp_path):
    """A literal format-doc example (`openspec/changes/archive/<dir>/`) is
    NOT a real dangling pointer — only a genuine, non-placeholder `<dir>/`
    segment that fails to resolve is flagged."""
    _write_tree(
        tmp_path,
        {
            "knowledge/decisions/INDEX.md": (
                "Format: `- **YYYY-MM-DD** · <slug> · <essence> → "
                "`openspec/changes/archive/<dir>/``\n"
                "\n"
                "Real dangling pointer: openspec/changes/archive/2026-01-01-ghost/design.md.\n"
            )
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    dangling = [f for f in findings if f.check == "dangling-archive-pointer"]
    assert len(dangling) == 1
    assert "2026-01-01-ghost" in dangling[0].message


# ===================================================================
# 2.2c — citation first-segment gate (citation-first-segment-must-be-
# real-top-level-dir): only a token rooted under a real top-level dir is
# a candidate citation; bare filenames, cross-repo names, GitHub shorthand,
# and non-path slashy tokens are not.
# ===================================================================


def test_citation_first_segment_gate(tmp_path):
    _write_tree(
        tmp_path,
        {
            # Establishes `plans/` as a real top-level dir at tmp_path root.
            "plans/keep.md": "# Kept plan\n",
            "knowledge/reference/notes.md": (
                "Real top-level dir, unresolved: `plans/gone/` should be flagged.\n"
                "\n"
                "Bare filename: `tasks.md` should not be flagged.\n"
                "\n"
                "Cross-repo name: `extrends/AGENTS.md` should not be flagged.\n"
                "\n"
                "GitHub shorthand: `sst/opencode` should not be flagged.\n"
                "\n"
                "Non-path slashy token: `WHEN/THEN/AND` should not be flagged.\n"
            ),
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    citation_findings = [f for f in findings if f.check == "broken-prose-path-citation"]

    assert len(citation_findings) == 1
    assert citation_findings[0].message.startswith("citation `plans/gone/`")


# ===================================================================
# 2.2d — git-ignore skip (git-ignored-paths-skipped): a path git-ignores
# is not scanned/flagged; the same content outside the ignored dir is.
# Guarded — skipped when git is unavailable in the sandbox, per the
# design's git-optional walk (nothing is skipped without git, so the
# skip behavior itself is untestable, not a failure).
# ===================================================================


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available in this environment")
def test_git_ignored_paths_skipped(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    _write_tree(
        tmp_path,
        {
            ".gitignore": "knowledge/vendored/\n",
            # Orphan STATUS.md inside the git-ignored vendored dir — the
            # directory is pruned from the walk, so this must NOT be
            # flagged even though its basename+location would otherwise
            # be an orphan/duplicate finding.
            "knowledge/vendored/STATUS.md": "# Status (git-ignored vendored copy)\n",
            # Broken citation inside the git-ignored vendored dir — the
            # file is skipped, so this must NOT be flagged.
            "knowledge/vendored/notes.md": (
                "See `knowledge/gone-elsewhere.md` for details (git-ignored).\n"
            ),
            # The same citation outside the ignored dir — must be flagged.
            "knowledge/reference/notes.md": (
                "See `knowledge/gone-elsewhere.md` for details (not ignored).\n"
            ),
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)

    ignored_findings = [f for f in findings if f.path.startswith("knowledge/vendored/")]
    assert ignored_findings == []

    outside_citation = [
        f
        for f in findings
        if f.path == "knowledge/reference/notes.md" and f.check == "broken-prose-path-citation"
    ]
    assert len(outside_citation) == 1
    assert "knowledge/gone-elsewhere.md" in outside_citation[0].message


def test_git_unavailable_or_no_repo_skips_nothing(tmp_path):
    """No `.git` present (the ordinary tmp_path fixture case for every
    other test in this file) -> the git-ignore checker always returns
    False, so nothing is skipped. This is the git-optional fallback
    exercised implicitly by every other test; asserted explicitly here."""
    assert not (tmp_path / ".git").exists()
    is_ignored = knowledge_lint.make_git_ignore_checker(tmp_path)
    assert is_ignored("knowledge/anything.md") is False
    assert is_ignored("anywhere/at/all") is False


# ===================================================================
# 6.1 — Citation skip-ladder hardening: brace, placeholder, ::symbol,
# :N-M, output/ prefix — each skips cleanly, and genuinely-missing
# files still flag.
# ===================================================================


def test_brace_pattern_not_flagged(tmp_path):
    """Brace-expansion ``{a,b}`` and ``{a..b}`` are deliberate notation,
    not broken paths."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": (
                "See `plans/labels/2026-W2{3,4,5}.yaml` for weekly variants.\n"
                "Also see `plans/notability-eval.{md,json}`.\n"
            ),
            "plans/keep.md": "# Kept plan\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "broken-prose-path-citation" for f in findings)


def test_date_placeholder_not_flagged(tmp_path):
    """``YYYY-Www`` style date/period placeholders are not real paths."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": ("See `plans/labels/YYYY-Www.yaml` for weekly data.\n"),
            "plans/keep.md": "# Kept plan\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "broken-prose-path-citation" for f in findings)


def test_symbol_node_id_on_existing_file_not_flagged(tmp_path):
    """``file.py::symbol`` strips the ``::symbol`` suffix and checks the
    file — if the file exists, no finding."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": (
                "See `plans/keep.md::_normalize_tokens` for the impl.\n"
            ),
            "plans/keep.md": "# Kept plan\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "broken-prose-path-citation" for f in findings)


def test_line_range_on_existing_file_not_flagged(tmp_path):
    """``file.py:N-M`` strips the ``:N-M`` range and checks the file —
    if the file exists, no finding."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": ("See `plans/keep.md:10-20` for the relevant lines.\n"),
            "plans/keep.md": "# Kept plan\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "broken-prose-path-citation" for f in findings)


def test_output_ephemeral_not_flagged(tmp_path):
    """``output/``-rooted paths are ephemeral (generated artifacts)."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": ("See `output/digest-2026-W25.md` for results.\n"),
            "output/dummy.md": "# output artifact\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "broken-prose-path-citation" for f in findings)


def test_missing_file_still_flagged(tmp_path):
    """A genuinely-missing file under a real top-level dir still flags —
    hardening does not blind the check to real drift."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": ("See `src/x/gone.py` for the implementation.\n"),
            "src/exists.md": "# exists\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    citation_findings = [f for f in findings if f.check == "broken-prose-path-citation"]
    assert len(citation_findings) == 1
    assert "src/x/gone.py" in citation_findings[0].message


def test_all_caps_component_not_mistaken_as_placeholder(tmp_path):
    """An all-caps path component like ``API`` must NOT be treated as a date
    placeholder — ``src/API/gone.py`` (where ``src/`` is a real top-level dir
    but the file does not exist) must still flag as a broken citation."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": ("See `src/API/gone.py` for the API impl.\n"),
            "src/exists.md": "# exists\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    citation_findings = [f for f in findings if f.check == "broken-prose-path-citation"]
    assert len(citation_findings) == 1
    assert "src/API/gone.py" in citation_findings[0].message


def test_symbol_node_id_on_missing_file_still_flagged(tmp_path):
    """``file.py::symbol`` where the underlying file does NOT exist still
    flags — drift is not blinded by the ``::symbol`` strip."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": ("See `plans/nope.md::SomeMethod` for the impl.\n"),
            "plans/keep.md": "# Kept plan\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    citation_findings = [f for f in findings if f.check == "broken-prose-path-citation"]
    assert len(citation_findings) == 1
    assert "plans/nope.md" in citation_findings[0].message


def test_line_range_on_missing_file_still_flagged(tmp_path):
    """``file.py:N-M`` where the underlying file does NOT exist still flags
    — drift is not blinded by the ``:N-M`` strip."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": ("See `plans/nope.md:10-20` for the relevant lines.\n"),
            "plans/keep.md": "# Kept plan\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    citation_findings = [f for f in findings if f.check == "broken-prose-path-citation"]
    assert len(citation_findings) == 1
    assert "plans/nope.md" in citation_findings[0].message


# ===================================================================
# 8.1 — Single-line number citations (`:N` suffix): existing file not
# flagged; missing file still flagged (FIX 1 for shared-lint-layer).
# ===================================================================


def test_single_line_number_on_existing_file_not_flagged(tmp_path):
    """``file.py:42`` (single line number, no range) on an existing file
    is NOT flagged — the ``:N`` suffix is stripped before the existence
    check, same as ``:N-M``."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": ("See `src/real.py:42` for the key line.\n"),
            "src/real.py": "# exists\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    citation_findings = [f for f in findings if f.check == "broken-prose-path-citation"]
    assert len(citation_findings) == 0


def test_single_line_number_on_missing_file_still_flagged(tmp_path):
    """``file.py:42`` where the underlying file does NOT exist still flags
    — the ``:N`` strip does not blind the check to real drift."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": ("See `src/gone.py:42` for the key line.\n"),
            "src/real.py": "# exists\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    citation_findings = [f for f in findings if f.check == "broken-prose-path-citation"]
    assert len(citation_findings) == 1
    assert "src/gone.py" in citation_findings[0].message


# ===================================================================
# 8.2 — Inline ``<!-- lint:planned -->`` suppression marker: a line
# bearing the marker skips broken-citation checks entirely (FIX 2 for
# shared-lint-layer). Author opt-out for forward-referenced files.
# ===================================================================


def test_lint_planned_marker_suppresses_broken_citation(tmp_path):
    """A broken citation on a line CONTAINING ``<!-- lint:planned -->``
    is NOT flagged — the entire line is suppressed."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": (
                "See `src/gone.py` for the upcoming change. <!-- lint:planned -->\n"
            ),
            "src/exists.md": "# exists\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    citation_findings = [f for f in findings if f.check == "broken-prose-path-citation"]
    assert len(citation_findings) == 0


def test_lint_planned_marker_only_affects_marked_line(tmp_path):
    """The SAME broken citation on a line WITHOUT the marker IS still
    flagged — suppression is line-scoped and does not leak."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": (
                "See `src/gone.py` for the upcoming change. <!-- lint:planned -->\n"
                "\n"
                "See `src/gone.py` for the actual file (no marker).\n"
            ),
            "src/exists.md": "# exists\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    citation_findings = [f for f in findings if f.check == "broken-prose-path-citation"]
    assert len(citation_findings) == 1
    assert "src/gone.py" in citation_findings[0].message


def test_lint_planned_marker_does_not_affect_other_lines(tmp_path):
    """A broken citation on an unmarked line is unaffected by a marker
    on a different line elsewhere in the same file."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": (
                "See `src/gone.py` for the actual file (no marker).\n"
                "\n"
                "See `src/other.py` for the follow-on change. <!-- lint:planned -->\n"
            ),
            "src/exists.md": "# exists\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    citation_findings = [f for f in findings if f.check == "broken-prose-path-citation"]
    assert len(citation_findings) == 1
    assert "src/gone.py" in citation_findings[0].message


# ===================================================================
# 7.1 — Root-handoff file check: files matching HANDOFF* / HANDOVER*
# at the repo root are flagged; knowledge/HANDOFF.md is exempt.
# ===================================================================


def test_root_handoff_file_flagged(tmp_path):
    """Root-level ``HANDOFF-x.md`` and ``HANDOVER.md`` are flagged."""
    _write_tree(
        tmp_path,
        {
            "HANDOFF-x.md": "# Temp handoff\n",
            "HANDOVER.md": "# Temp handover\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    handoff_findings = [f for f in findings if f.check == "root-handoff-file"]
    assert len(handoff_findings) == 2
    assert any("HANDOFF-x.md" in f.path for f in handoff_findings)
    assert any("HANDOVER.md" in f.path for f in handoff_findings)


def test_knowledge_handoff_not_flagged(tmp_path):
    """The sanctioned ``knowledge/HANDOFF.md`` (inside the knowledge tree,
    not at the root) is NOT flagged."""
    _write_tree(
        tmp_path,
        {
            "knowledge/HANDOFF.md": "# Session handoff\n",
            "knowledge/STATUS.md": "# Status\nAll good.\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "root-handoff-file" for f in findings)


def test_root_handoff_clean_tree_no_findings(tmp_path):
    """A clean tree with no handoff files produces no findings."""
    _write_tree(
        tmp_path,
        {
            "knowledge/STATUS.md": "# Status\nAll good.\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "root-handoff-file" for f in findings)


# ===================================================================
# Detect-only enforcement — no write-mode calls anywhere in the module
# ===================================================================


def test_module_source_has_no_write_calls():
    """Belt-and-suspenders static check (task 1.8): the module never opens
    a file for writing, and never calls mkdir/unlink/rename/move-style
    filesystem mutators."""
    source = Path(knowledge_lint.__file__).read_text(encoding="utf-8")
    forbidden = [
        '"w")',
        "'w')",
        '"wb")',
        "'wb')",
        "os.remove(",
        "os.unlink(",
        "os.mkdir(",
        "os.makedirs(",
        "shutil.move(",
        "shutil.rmtree(",
        "Path.mkdir(",
        ".unlink(",
        ".rmdir(",
    ]
    for token in forbidden:
        assert token not in source, f"potential write call found: {token!r}"
