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
import time
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
# 2.6 — composition audit-log line accepted
# ===================================================================


def test_audit_log_composition_line_accepted(tmp_path):
    """Composition audit-log line is accepted by the linter."""
    _write_tree(
        tmp_path,
        {
            "knowledge/audit-log.md": (
                "# Audit Log\n"
                "\n"
                "- **2026-07-11** · audit/2026-07-11-composition · abc1234 · first composition pass\n"
            )
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    audit_findings = [f for f in findings if f.check == "audit-log-registry-format"]
    assert len(audit_findings) == 0, f"composition line should be accepted, got: {audit_findings}"


def test_audit_log_foreign_suffix_rejected(tmp_path):
    """A suffix other than -composition after the anchor date is flagged."""
    _write_tree(
        tmp_path,
        {
            "knowledge/audit-log.md": (
                "# Audit Log\n"
                "\n"
                "- **2026-07-11** · audit/2026-07-11-security · abc1234 · security pass\n"
            )
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    audit_findings = [f for f in findings if f.check == "audit-log-registry-format"]
    assert len(audit_findings) == 1, "foreign suffix should be flagged"
    assert audit_findings[0].line == 3


# ===================================================================
# 2.7 — per-repo config: checks.toml retired_paths merges with defaults
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


def test_gitignored_citation_target_not_flagged(tmp_path):
    """A citation to a gitignored (generated/rendered/ephemeral) target is NOT a
    broken citation even when the file is absent — generalizes the `output/`
    exemption to any path git ignores (e.g. a downstream repo's deploy-time
    rendered `deploy/rendered/…` install artifact). A citation to a genuinely
    missing, NON-ignored path must still flag (guards against over-broad
    suppression). Requires a real git repo so `make_git_ignore_checker` is live."""
    _write_tree(
        tmp_path,
        {
            ".gitignore": "deploy/rendered/\n",
            "deploy/install.sh": "#!/usr/bin/env bash\necho install\n",
            "knowledge/reference/notes.md": (
                "Install the rendered artifact: `deploy/rendered/crontab.txt` "
                "(gitignored, absent on a clean tree, not flagged).\n"
                "\n"
                "See `deploy/does-not-exist.md` for a genuinely missing, "
                "non-ignored path (must still flag).\n"
            ),
        },
    )
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)

    findings = knowledge_lint.collect_findings(tmp_path)
    citation_findings = [f for f in findings if f.check == "broken-prose-path-citation"]
    assert not any("deploy/rendered/crontab.txt" in f.message for f in citation_findings)
    assert any("deploy/does-not-exist.md" in f.message for f in citation_findings)


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
# 7.1 — Handoff-file check: any non-gitignored file whose name contains
# handoff/handover (case-insensitive) anywhere in the repo is flagged;
# knowledge/HANDOFF.md is exempt; gitignored paths are not scanned.
# ===================================================================


def test_root_handoff_file_flagged(tmp_path):
    """Root-level ``HANDOFF-x.md`` and ``HANDOVER.md`` are flagged (repo-wide)."""
    _write_tree(
        tmp_path,
        {
            "HANDOFF-x.md": "# Temp handoff\n",
            "HANDOVER.md": "# Temp handover\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    handoff_findings = [f for f in findings if f.check == "handoff-file"]
    assert len(handoff_findings) == 2
    assert any("HANDOFF-x.md" in f.path for f in handoff_findings)
    assert any("HANDOVER.md" in f.path for f in handoff_findings)


def test_knowledge_handoff_not_flagged(tmp_path):
    """The sanctioned ``knowledge/HANDOFF.md`` (sole exemption) is NOT flagged."""
    _write_tree(
        tmp_path,
        {
            "knowledge/HANDOFF.md": "# Session handoff\n",
            "knowledge/STATUS.md": "# Status\nAll good.\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "handoff-file" for f in findings)


def test_root_handoff_clean_tree_no_findings(tmp_path):
    """A clean tree with no handoff files produces no findings."""
    _write_tree(
        tmp_path,
        {
            "knowledge/STATUS.md": "# Status\nAll good.\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "handoff-file" for f in findings)


def test_nested_handoff_file_flagged(tmp_path):
    """A nested ``plans/foo-handoff.md`` is flagged (repo-wide scope)."""
    _write_tree(
        tmp_path,
        {
            "plans/foo-handoff.md": "# Handoff plan\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    handoff_findings = [f for f in findings if f.check == "handoff-file"]
    assert len(handoff_findings) == 1
    assert "plans/foo-handoff.md" in handoff_findings[0].path


def test_nested_handover_case_insensitive_flagged(tmp_path):
    """A nested ``docs/HANDOVER.md`` (uppercase) is flagged
    (case-insensitive substring match)."""
    _write_tree(
        tmp_path,
        {
            "docs/HANDOVER.md": "# Handover doc\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    handoff_findings = [f for f in findings if f.check == "handoff-file"]
    assert len(handoff_findings) == 1
    assert "docs/HANDOVER.md" in handoff_findings[0].path


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available in this environment")
def test_gitignored_handoff_file_not_flagged(tmp_path):
    """A handoff-named file under a gitignored directory is NOT flagged."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=tmp_path)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path)
    _write_tree(
        tmp_path,
        {
            ".gitignore": "output/\n",
            "output/x-handoff.md": "# Ignored handoff\n",
            # A non-gitignored handoff elsewhere still flags.
            "plans/session-handoff.md": "# Real handoff\n",
        },
    )
    # Must stage .gitignore for git to recognize the ignore rules.
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)

    findings = knowledge_lint.collect_findings(tmp_path)
    handoff_findings = [f for f in findings if f.check == "handoff-file"]

    # output/x-handoff.md is gitignored -> not flagged.
    ignored = [f for f in handoff_findings if "output/x-handoff.md" in f.path]
    assert ignored == []

    # plans/session-handoff.md is not gitignored -> flagged.
    non_ignored = [f for f in handoff_findings if "plans/session-handoff.md" in f.path]
    assert len(non_ignored) == 1


# ===================================================================
# 5.3 — duplicate-content-block (D7): flagged / not-flagged cases,
# overlapping-window merge, research/specs exclusion, dup-ok marker.
# ===================================================================

_DUP_BLOCK_10_LINES = "\n".join(
    f"Duplicated line number {n} of the shared block." for n in range(1, 11)
)


def test_duplicate_block_flagged_across_two_files_one_finding_per_file(tmp_path):
    """A >=8-line verbatim block across two in-scope files is flagged — and
    the overlapping 1-line-shifted sliding windows across the whole span
    collapse into exactly ONE finding per file, not one per window offset
    (the merge-overlapping-windows fix)."""
    _write_tree(
        tmp_path,
        {
            "AGENTS.md": f"# Agents\n\n{_DUP_BLOCK_10_LINES}\n\nTail content unique to AGENTS.md.\n",
            "knowledge/reference/other.md": (
                f"# Other\n\n{_DUP_BLOCK_10_LINES}\n\nTail content unique to other.md.\n"
            ),
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    dup_findings = [f for f in findings if f.check == "duplicate-content-block"]

    assert len(dup_findings) == 2  # exactly one per file, not one per window offset
    paths = {f.path for f in dup_findings}
    assert paths == {"AGENTS.md", "knowledge/reference/other.md"}
    for f in dup_findings:
        assert "appears in 2 files" in f.message

    exit_code, stdout = _run_main(tmp_path)
    assert exit_code == 1
    assert "duplicate-content-block" in stdout


def test_duplicate_block_under_8_lines_not_flagged(tmp_path):
    short_block = "\n".join(f"Short shared line {n}." for n in range(1, 7))  # 6 lines, < 8
    _write_tree(
        tmp_path,
        {
            "AGENTS.md": f"# Agents\n\n{short_block}\n",
            "knowledge/reference/other.md": f"# Other\n\n{short_block}\n",
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "duplicate-content-block" for f in findings)


def test_duplicate_block_in_research_dir_not_flagged(tmp_path):
    """The duplicated block sitting DIRECTLY inside knowledge/research/ (not
    nested in a subdirectory) must be excluded — regression test for the
    exact-match exclusion bug (a bare prefix-with-slash check misses the
    directory itself)."""
    _write_tree(
        tmp_path,
        {
            "AGENTS.md": f"# Agents\n\n{_DUP_BLOCK_10_LINES}\n",
            "knowledge/research/old-plan.md": f"# Old Plan\n\n{_DUP_BLOCK_10_LINES}\n",
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "duplicate-content-block" for f in findings)


def test_duplicate_block_openspec_specs_excluded_via_configured_scan_dir(tmp_path):
    """openspec/specs/ is excluded even when a configured
    ``duplicate_scan_dirs`` entry would otherwise bring it into scope; a
    sibling dir under the same configured root is NOT exempt."""
    _write_tree(
        tmp_path,
        {
            "checks.toml": '[knowledge_lint]\nduplicate_scan_dirs = ["openspec"]\n',
            "AGENTS.md": f"# Agents\n\n{_DUP_BLOCK_10_LINES}\n",
            "openspec/specs/some-cap/spec.md": f"# Spec\n\n{_DUP_BLOCK_10_LINES}\n",
            "openspec/other/notes.md": f"# Notes\n\n{_DUP_BLOCK_10_LINES}\n",
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    dup_findings = [f for f in findings if f.check == "duplicate-content-block"]
    dup_paths = {f.path for f in dup_findings}

    assert "openspec/specs/some-cap/spec.md" not in dup_paths
    assert "openspec/other/notes.md" in dup_paths
    assert "AGENTS.md" in dup_paths


def test_duplicate_block_dup_ok_marker_suppresses(tmp_path):
    """The marker must sit INSIDE the detected duplicate window. Embedding
    it at the same position in both files keeps the block a single
    contiguous verbatim match (still >=8 lines, still identical across
    both files) while placing the marker within each occurrence's own
    reported line range."""
    block_with_marker = (
        "\n".join(f"Duplicated line number {n} of the shared block." for n in range(1, 6))
        + "\n<!-- lint:dup-ok -->\n"
        + "\n".join(f"Duplicated line number {n} of the shared block." for n in range(6, 11))
    )
    _write_tree(
        tmp_path,
        {
            "AGENTS.md": f"# Agents\n\n{block_with_marker}\n",
            "knowledge/reference/other.md": f"# Other\n\n{block_with_marker}\n",
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "duplicate-content-block" for f in findings)


# ===================================================================
# 5.3 — closed-but-unpruned (D7): roadmap + top-level plan flagged;
# lint:keep opts out.
# ===================================================================


def test_closed_unpruned_roadmap_entry_flagged(tmp_path):
    _write_tree(
        tmp_path,
        {
            "knowledge/roadmap.md": (
                "# Roadmap\n\n## Some shipped idea\n**Status:** DONE\n**Priority:** ~~Medium~~\n"
            )
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    closed = [f for f in findings if f.check == "closed-but-unpruned"]
    assert len(closed) == 1
    assert closed[0].path == "knowledge/roadmap.md"


def test_closed_unpruned_top_level_plan_flagged(tmp_path):
    _write_tree(
        tmp_path,
        {"plans/shipped-plan.md": "# Shipped Plan\n\n**Status:** COMPLETE\n"},
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    closed = [f for f in findings if f.check == "closed-but-unpruned"]
    assert len(closed) == 1
    assert closed[0].path == "plans/shipped-plan.md"


def test_closed_unpruned_nested_plan_flagged(tmp_path):
    """A plan file nested inside a non-archive subdirectory of plans/ is
    gathered the same as a top-level plans/*.md file (recursive gather,
    agreeing with scripts/outstanding.py)."""
    _write_tree(
        tmp_path,
        {"plans/sub/item.md": "# Nested Shipped Plan\n\n**Status:** COMPLETE\n"},
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    closed = [f for f in findings if f.check == "closed-but-unpruned"]
    assert len(closed) == 1
    assert closed[0].path == "plans/sub/item.md"


def test_closed_unpruned_archive_plan_not_gathered(tmp_path):
    """plans/archive/**, regardless of nesting depth, is excluded from the
    gather — a closed-token marker there is never flagged."""
    _write_tree(
        tmp_path,
        {
            "plans/archive/old.md": "# Old Plan\n\n**Status:** COMPLETE\n",
            "plans/archive/sub/older.md": "# Older Plan\n\n**Status:** DONE\n",
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "closed-but-unpruned" for f in findings)


def test_closed_unpruned_lint_keep_opts_out(tmp_path):
    _write_tree(
        tmp_path,
        {
            "knowledge/roadmap.md": (
                "# Roadmap\n\n## Some shipped idea\n**Status:** DONE\n<!-- lint:keep -->\n"
            ),
            "plans/shipped-plan.md": (
                "# Shipped Plan\n\n**Status:** COMPLETE\n<!-- lint:keep -->\n"
            ),
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "closed-but-unpruned" for f in findings)


# ===================================================================
# 5.3 — untriaged-finding-stale (D8): past window flagged, within window
# not flagged, mtime fallback when git is absent (no .git in these fixtures).
# ===================================================================


def _backdate(path: Path, days: int) -> None:
    ts = time.time() - days * 86400
    os.utime(path, (ts, ts))


def test_untriaged_age_flagged_past_window(tmp_path):
    findings_path = tmp_path / "knowledge" / "research" / "audit" / "FINDINGS.md"
    _write_tree(tmp_path, {"checks.toml": "[knowledge_lint]\nuntriaged_max_age_days = 5\n"})
    _write_tree(tmp_path, {str(findings_path.relative_to(tmp_path)): "Found CA-W5-5 issue.\n"})
    _backdate(findings_path, days=10)  # older than the 5-day window

    findings = knowledge_lint.collect_findings(tmp_path)
    stale = [f for f in findings if f.check == "untriaged-finding-stale"]
    assert len(stale) == 1
    assert "CA-W5-5" in stale[0].message


def test_untriaged_age_not_flagged_within_window(tmp_path):
    findings_path = tmp_path / "knowledge" / "research" / "audit" / "FINDINGS.md"
    _write_tree(tmp_path, {"checks.toml": "[knowledge_lint]\nuntriaged_max_age_days = 14\n"})
    _write_tree(tmp_path, {str(findings_path.relative_to(tmp_path)): "Found CA-W6-6 issue.\n"})
    # Freshly written -> mtime is "now", well within the 14-day window.

    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "untriaged-finding-stale" for f in findings)


def test_untriaged_age_uses_mtime_fallback_without_git(tmp_path):
    """No .git anywhere in this fixture — age must come from filesystem
    mtime, not crash for lack of git, and reflect the backdated age."""
    assert not (tmp_path / ".git").exists()
    findings_path = tmp_path / "knowledge" / "research" / "audit" / "FINDINGS.md"
    _write_tree(tmp_path, {str(findings_path.relative_to(tmp_path)): "Found CA-W7-7 issue.\n"})
    _backdate(findings_path, days=20)

    untriaged = knowledge_lint.outstanding.extract_untriaged(tmp_path, {})
    match = next(item for item in untriaged if item["id"] == "CA-W7-7")
    assert 19 <= match["age_days"] <= 21


# ===================================================================
# 6.1 — ratchet-log registry format check (guarded)
# ===================================================================


def test_ratchet_log_absent_is_skipped_silently(tmp_path):
    """No ratchet-log.md -> no ratchet findings."""
    _write_tree(tmp_path, {"knowledge/reference/notes.md": "# Notes\n"})
    assert not (tmp_path / "knowledge" / "ratchet-log.md").exists()
    findings = knowledge_lint.collect_findings(tmp_path)
    assert not any(f.check == "ratchet-log-registry-format" for f in findings)
    exit_code, _stdout = _run_main(tmp_path)
    assert exit_code == 0


def test_ratchet_valid_check_disposition_passes(tmp_path):
    """A valid check: pointer with existing file passes."""
    _write_tree(
        tmp_path,
        {
            "knowledge/ratchet-log.md": (
                "# Ratchet Log\n"
                "\n"
                "- **2026-07-10** · my-class · check:scripts/knowledge_lint.py::_check_ratchet_log — test check\n"
            ),
            "scripts/knowledge_lint.py": (
                "#!/usr/bin/env python3\ndef _check_ratchet_log():\n    pass\n"
            ),
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ratchet_findings = [f for f in findings if f.check == "ratchet-log-registry-format"]
    assert len(ratchet_findings) == 0


def test_ratchet_valid_test_disposition_passes(tmp_path):
    """A valid test: pointer with existing file passes."""
    _write_tree(
        tmp_path,
        {
            "knowledge/ratchet-log.md": (
                "# Ratchet Log\n"
                "\n"
                "- **2026-07-10** · my-test-class · test:test_ratchet_valid_test_disposition_passes.py — test pin\n"
            ),
            "test_ratchet_valid_test_disposition_passes.py": ("def test_something(): pass\n"),
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ratchet_findings = [f for f in findings if f.check == "ratchet-log-registry-format"]
    assert len(ratchet_findings) == 0


def test_ratchet_bare_test_path_with_existing_file_passes(tmp_path):
    """A test: pointer with bare file path (no ::name) passes if file exists."""
    _write_tree(
        tmp_path,
        {
            "knowledge/ratchet-log.md": (
                "# Ratchet Log\n"
                "\n"
                "- **2026-07-10** · bare-test-class · test:scripts/knowledge_lint.py — bare file path\n"
            ),
            "scripts/knowledge_lint.py": "content\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ratchet_findings = [f for f in findings if f.check == "ratchet-log-registry-format"]
    assert len(ratchet_findings) == 0


def test_ratchet_valid_waiver_disposition_passes(tmp_path):
    """A valid waiver: reason present, review-by in the future."""
    _write_tree(
        tmp_path,
        {
            "knowledge/ratchet-log.md": (
                "# Ratchet Log\n"
                "\n"
                "- **2026-07-10** · waived-class · waiver:review-by 2099-12-31 — domain judgment only, no detector possible\n"
            ),
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ratchet_findings = [f for f in findings if f.check == "ratchet-log-registry-format"]
    assert len(ratchet_findings) == 0


def test_ratchet_valid_open_disposition_passes(tmp_path):
    """A valid open:since with young age passes."""
    _write_tree(
        tmp_path,
        {
            "knowledge/ratchet-log.md": (
                "# Ratchet Log\n"
                "\n"
                "- **2026-07-10** · open-class · open:since 2026-07-10 — enforcement deferred\n"
            ),
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ratchet_findings = [f for f in findings if f.check == "ratchet-log-registry-format"]
    assert len(ratchet_findings) == 0


def test_ratchet_valid_grandfathered_passes(tmp_path):
    """grandfathered disposition with dead path in essence is NOT flagged."""
    _write_tree(
        tmp_path,
        {
            "knowledge/ratchet-log.md": (
                "# Ratchet Log\n"
                "\n"
                "- **2026-07-10** · legacy-class · grandfathered — pre-ratchet lesson; see `knowledge/gone/lesson.md`\n"
            ),
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ratchet_findings = [f for f in findings if f.check == "ratchet-log-registry-format"]
    assert len(ratchet_findings) == 0


def test_ratchet_bad_keyword_flagged(tmp_path):
    """Unknown disposition keyword is flagged."""
    _write_tree(
        tmp_path,
        {
            "knowledge/ratchet-log.md": (
                "# Ratchet Log\n\n- **2026-07-10** · unknown-class · nope:what — unknown keyword\n"
            ),
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ratchet_findings = [f for f in findings if f.check == "ratchet-log-registry-format"]
    assert len(ratchet_findings) == 1
    assert "unknown disposition" in ratchet_findings[0].message


def test_ratchet_bad_slug_flagged(tmp_path):
    """Non-kebab slug is flagged."""
    _write_tree(
        tmp_path,
        {
            "knowledge/ratchet-log.md": (
                "# Ratchet Log\n\n- **2026-07-10** · Bad_Slug · grandfathered — bad slug\n"
            ),
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ratchet_findings = [f for f in findings if f.check == "ratchet-log-registry-format"]
    assert len(ratchet_findings) == 1
    assert "malformed" in ratchet_findings[0].message


def test_ratchet_invalid_calendar_date_flagged(tmp_path):
    """Invalid calendar date (2026-13-01) is flagged."""
    _write_tree(
        tmp_path,
        {
            "knowledge/ratchet-log.md": (
                "# Ratchet Log\n"
                "\n"
                "- **2026-13-01** · bad-date-class · grandfathered — invalid date\n"
            ),
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ratchet_findings = [f for f in findings if f.check == "ratchet-log-registry-format"]
    assert len(ratchet_findings) == 1
    assert "invalid" in ratchet_findings[0].message


def test_ratchet_dangling_check_pointer_flagged(tmp_path):
    """Dangling check: path is flagged."""
    _write_tree(
        tmp_path,
        {
            "knowledge/ratchet-log.md": (
                "# Ratchet Log\n"
                "\n"
                "- **2026-07-10** · dangling-check · check:checks/nonexistent.py — missing check\n"
            ),
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ratchet_findings = [f for f in findings if f.check == "ratchet-log-registry-format"]
    assert len(ratchet_findings) == 1
    assert "does not exist" in ratchet_findings[0].message


def test_ratchet_dangling_test_symbol_flagged(tmp_path):
    """Dangling test::name where symbol not in file is flagged."""
    _write_tree(
        tmp_path,
        {
            "knowledge/ratchet-log.md": (
                "# Ratchet Log\n"
                "\n"
                "- **2026-07-10** · dangling-symbol · test:scripts/test_checks.py::_no_such_test — missing symbol\n"
            ),
            "scripts/test_checks.py": ("class DoesExist: pass\n"),
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ratchet_findings = [f for f in findings if f.check == "ratchet-log-registry-format"]
    assert len(ratchet_findings) == 1
    assert "not found" in ratchet_findings[0].message
    assert "_no_such_test" in ratchet_findings[0].message


def test_ratchet_stale_waiver_flagged(tmp_path):
    """Waiver with review-by in the past is flagged."""
    _write_tree(
        tmp_path,
        {
            "knowledge/ratchet-log.md": (
                "# Ratchet Log\n"
                "\n"
                "- **2026-07-10** · stale-waiver · waiver:review-by 2020-01-01 — old waiver\n"
            ),
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ratchet_findings = [f for f in findings if f.check == "ratchet-log-registry-format"]
    assert len(ratchet_findings) == 1
    assert "past" in ratchet_findings[0].message


def test_ratchet_aged_open_flagged_default_threshold(tmp_path):
    """Open:since older than default 30 days is flagged."""
    _write_tree(
        tmp_path,
        {
            "knowledge/ratchet-log.md": (
                "# Ratchet Log\n"
                "\n"
                "- **2020-01-01** · aged-open · open:since 2020-01-01 — very old open\n"
            ),
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ratchet_findings = [f for f in findings if f.check == "ratchet-log-registry-format"]
    assert len(ratchet_findings) == 1
    assert "days old" in ratchet_findings[0].message
    assert "max 30 days" in ratchet_findings[0].message


def test_ratchet_open_honors_configured_threshold(tmp_path):
    """Open:since age check honors checks.toml ratchet_open_max_age_days = 7."""
    _write_tree(
        tmp_path,
        {
            "knowledge/ratchet-log.md": (
                "# Ratchet Log\n"
                "\n"
                "- **2026-07-01** · config-open · open:since 2026-07-01 — deferred\n"
            ),
            "checks.toml": "[knowledge_lint]\nratchet_open_max_age_days = 7\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ratchet_findings = [f for f in findings if f.check == "ratchet-log-registry-format"]
    # 2026-07-01 is 12 days before 2026-07-13, so it exceeds 7 days
    assert len(ratchet_findings) == 1
    assert "max 7 days" in ratchet_findings[0].message


def test_ratchet_open_within_threshold_not_flagged(tmp_path):
    """Open:since within the default 30-day threshold is NOT flagged."""
    from datetime import date as _date

    today = _date.today()
    since_str = today.isoformat()
    _write_tree(
        tmp_path,
        {
            "knowledge/ratchet-log.md": (
                "# Ratchet Log\n"
                "\n"
                f"- **{since_str}** · recent-open · open:since {since_str} — fresh deferral\n"
            ),
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ratchet_findings = [f for f in findings if f.check == "ratchet-log-registry-format"]
    assert len(ratchet_findings) == 0


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


# ===================================================================
# 2.2 — correctness-audit dossier lint (_check_audit_dossier)
# ===================================================================

_CHARTER_WITH_MARKER = (
    "# Correctness Audit Charter\n"
    "\n"
    "## Scope\n"
    "scripts/ingestion.py, scripts/validation.py\n"
    "\n"
    "---\n"
    "format: correctness-audit/v1\n"
)

_CENSUS_VALID = (
    "# Census\n"
    "\n"
    "scripts/ingestion.py | AUDITED-clean    | — | No issues\n"
    "scripts/validation.py | AUDITED-finding | CA-W1-1 | Silent truncation\n"
    "vendor/old-lib/ | N/A-no-source | — | No source\n"
)

_FINDINGS_W1_VALID = (
    "## CA-W1-1 — Silent data truncation\n"
    "\n"
    "**Statement**\n"
    "Truncation without warning.\n"
    "\n"
    "**Evidence**\n"
    "VERIFIED-BY-repro\n"
    "Repro snapshot exists.\n"
    "\n"
    "**Severity**\n"
    "HIGH\n"
    "\n"
    "**Prior:**\n"
    "none (grep clean)\n"
    "\n"
    "**Class:**\n"
    "silent-truncation\n"
    "\n"
    "**Fix sketch**\n"
    "Add length check.\n"
    "\n"
    "**Effort:** S\n"
)

_FINDINGS_W2_VALID = (
    "### Graduation log\n"
    "\n"
    "- **2026-07-10** — Refutation session\n"
    "  - Adjudicated: CA-W2-1\n"
    "  - Verdicts: CA-W2-1 -> REFUTED\n"
    "\n"
    "## CA-W2-1 — Retry loop without backoff\n"
    "\n"
    "**Statement**\n"
    "Retries without exponential backoff.\n"
    "\n"
    "**Evidence**\n"
    "REFUTED\n"
    "Premise false — outer layer has backoff.\n"
    "\n"
    "**Severity**\n"
    "LOW\n"
    "\n"
    "**Prior:**\n"
    "none (grep clean)\n"
    "\n"
    "**Class:**\n"
    "none (one-off)\n"
    "\n"
    "**Fix sketch**\n"
    "No fix needed.\n"
    "\n"
    "**Effort:** S\n"
)


def _build_dossier(
    root: Path, subdir: str, charter: str, census: str, findings: list[tuple[str, str]]
) -> Path:
    """Build a correctness-audit dossier under *root*/*subdir*."""
    dd = root / "knowledge" / "research" / subdir
    dd.mkdir(parents=True, exist_ok=True)
    (dd / "CHARTER.md").write_text(charter, encoding="utf-8")
    if census is not None:
        (dd / "CENSUS.md").write_text(census, encoding="utf-8")
    for fname, content in findings:
        (dd / fname).write_text(content, encoding="utf-8")
    return dd


def test_audit_dossier_conforming_clean(tmp_path):
    """A conforming marked dossier with unique IDs, valid dispositions, and
    Prior:/Class: on all graduated findings lints clean."""
    _build_dossier(
        tmp_path,
        "correctness-audit-2026-07",
        _CHARTER_WITH_MARKER,
        _CENSUS_VALID,
        [("FINDINGS-wave1.md", _FINDINGS_W1_VALID), ("FINDINGS-wave2.md", _FINDINGS_W2_VALID)],
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    dossier_findings = [f for f in findings if f.check == "audit-dossier-format"]
    assert dossier_findings == []


def test_audit_dossier_duplicate_id_flagged(tmp_path):
    """A duplicate finding ID across two wave files is flagged with both
    locations."""
    _build_dossier(
        tmp_path,
        "correctness-audit-2026-07",
        _CHARTER_WITH_MARKER,
        _CENSUS_VALID,
        [
            ("FINDINGS-wave1.md", "## CA-W1-1 — First\n\n**Evidence**\nLEAD\n"),
            ("FINDINGS-wave2.md", "## CA-W1-1 — Duplicate\n\n**Evidence**\nLEAD\n"),
        ],
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    dossier_findings = [f for f in findings if f.check == "audit-dossier-format"]
    assert len(dossier_findings) == 1
    assert "duplicate finding ID" in dossier_findings[0].message
    assert "CA-W1-1" in dossier_findings[0].message
    assert "FINDINGS-wave1.md" in dossier_findings[0].message
    assert "FINDINGS-wave2.md" in dossier_findings[0].message


def test_audit_dossier_invalid_census_disposition_flagged(tmp_path):
    """A census row with an invalid disposition is flagged."""
    bad_census = "# Census\n\nscripts/ingestion.py | UNKNOWN-VALUE | — | Bad\n"
    _build_dossier(
        tmp_path,
        "correctness-audit-2026-07",
        _CHARTER_WITH_MARKER,
        bad_census,
        [("FINDINGS-wave1.md", "# No findings yet\n")],
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    dossier_findings = [f for f in findings if f.check == "audit-dossier-format"]
    assert len(dossier_findings) == 1
    assert "invalid census disposition" in dossier_findings[0].message
    assert "UNKNOWN-VALUE" in dossier_findings[0].message


def test_audit_dossier_graduated_missing_prior_class_flagged(tmp_path):
    """A graduated finding (non-LEAD evidence) missing Prior: or Class: is
    flagged."""
    bad_findings = (
        "## CA-W1-1 — Silent truncation\n"
        "\n"
        "**Statement**\n"
        "Truncation.\n"
        "\n"
        "**Evidence**\n"
        "VERIFIED-BY-repro\n"
        "\n"
        "**Severity**\n"
        "HIGH\n"
        "\n"
        "**Fix sketch**\n"
        "Fix it.\n"
        "\n"
        "**Effort:** S\n"
    )
    census = "# Census\n\nscripts/ingestion.py | AUDITED-finding | CA-W1-1 | Truncation\n"
    _build_dossier(
        tmp_path,
        "correctness-audit-2026-07",
        _CHARTER_WITH_MARKER,
        census,
        [("FINDINGS-wave1.md", bad_findings)],
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    dossier_findings = [f for f in findings if f.check == "audit-dossier-format"]
    assert len(dossier_findings) == 1
    assert "CA-W1-1" in dossier_findings[0].message
    assert "Prior:" in dossier_findings[0].message or "Class:" in dossier_findings[0].message


def test_audit_dossier_lead_not_flagged_for_missing_prior_class(tmp_path):
    """A finding still labeled LEAD is NOT flagged for missing Prior:/Class: —
    it is still in the draft phase."""
    lead_findings = (
        "## CA-W1-2 — Potential issue\n"
        "\n"
        "**Statement**\n"
        "Something might be wrong.\n"
        "\n"
        "**Evidence**\n"
        "LEAD\n"
        "\n"
        "**Severity**\n"
        "MEDIUM\n"
        "\n"
        "**Fix sketch**\n"
        "TBD.\n"
        "\n"
        "**Effort:** M\n"
    )
    census = "# Census\n\nscripts/ingestion.py | LEAD-deferred | CA-W1-2 | Lead deferred\n"
    _build_dossier(
        tmp_path,
        "correctness-audit-2026-07",
        _CHARTER_WITH_MARKER,
        census,
        [("FINDINGS-wave1.md", lead_findings)],
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    dossier_findings = [f for f in findings if f.check == "audit-dossier-format"]
    assert dossier_findings == []


def test_audit_dossier_markerless_skipped(tmp_path):
    """A dossier whose CHARTER.md lacks the format marker is skipped entirely
    — no findings from it."""
    _build_dossier(
        tmp_path,
        "correctness-audit-2026-07",
        "# Charter without marker\n",
        "# Census\n\nscripts/ingestion.py | INVALID-DISP | — | Bad\n",
        [("FINDINGS-wave1.md", "## CA-W1-1 — Duplicate\n")],
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    dossier_findings = [f for f in findings if f.check == "audit-dossier-format"]
    assert dossier_findings == []


def test_audit_dossier_no_charter_skipped(tmp_path):
    """A dossier dir with no CHARTER.md is skipped entirely."""
    dd = tmp_path / "knowledge" / "research" / "correctness-audit-2026-07"
    dd.mkdir(parents=True, exist_ok=True)
    (dd / "CENSUS.md").write_text("scripts/ingestion.py | INVALID | — | Bad\n", encoding="utf-8")
    findings = knowledge_lint.collect_findings(tmp_path)
    dossier_findings = [f for f in findings if f.check == "audit-dossier-format"]
    assert dossier_findings == []


def test_audit_dossier_no_dossier_dir_clean(tmp_path):
    """No correctness-audit-* directory at all → clean."""
    findings = knowledge_lint.collect_findings(tmp_path)
    dossier_findings = [f for f in findings if f.check == "audit-dossier-format"]
    assert dossier_findings == []


# ===================================================================
# 3.1 — audit-liveness drift check (_check_audit_liveness)
# ===================================================================

_CHARTER_IN_PROGRESS = (
    "# Correctness Audit Charter\n"
    "\n"
    "## Scope\n"
    "scripts/ingestion.py\n"
    "\n"
    "---\n"
    "format: correctness-audit/v1\n"
    "status: in-progress\n"
)

_CHARTER_CLOSED = (
    "# Correctness Audit Charter\n"
    "\n"
    "## Scope\n"
    "scripts/ingestion.py\n"
    "\n"
    "---\n"
    "format: correctness-audit/v1\n"
    "status: closed\n"
)


def test_liveness_no_dossier_dir_clean(tmp_path):
    """(a) no dossier dir → no audit-liveness findings."""
    findings = knowledge_lint.collect_findings(tmp_path)
    liveness = [f for f in findings if f.check == "audit-liveness"]
    assert liveness == []


def test_liveness_markerless_charter_clean(tmp_path):
    """(b) markerless charter → clean."""
    _build_dossier(
        tmp_path,
        "correctness-audit-2026-07",
        "# Charter without marker\n",
        None,
        [],
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    liveness = [f for f in findings if f.check == "audit-liveness"]
    assert liveness == []


def test_liveness_closed_charter_clean_even_without_active_item(tmp_path):
    """(c) charter containing 'status: closed' → clean even with no
    Active item."""
    _build_dossier(
        tmp_path,
        "correctness-audit-2026-07",
        _CHARTER_CLOSED,
        None,
        [],
    )
    # No Active questions item at all.
    findings = knowledge_lint.collect_findings(tmp_path)
    liveness = [f for f in findings if f.check == "audit-liveness"]
    assert liveness == []


def test_liveness_in_progress_missing_from_active_flagged(tmp_path):
    """(d) in-progress dossier (marked, no 'status: closed') whose dir
    name is absent from the INDEX Active section → exactly one
    audit-liveness finding."""
    _build_dossier(
        tmp_path,
        "correctness-audit-2026-07",
        _CHARTER_IN_PROGRESS,
        None,
        [],
    )
    # INDEX.md with empty ## Active (no reference to the dossier).
    _write_tree(
        tmp_path,
        {
            "knowledge/questions/INDEX.md": (
                "# Open Questions\n"
                "\n"
                "## Active\n"
                "\n"
                "<!-- nothing here -->\n"
                "\n"
                "## Parked\n"
                "\n"
                "- Some parked item\n"
            )
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    liveness = [f for f in findings if f.check == "audit-liveness"]
    assert len(liveness) == 1
    assert "correctness-audit-2026-07" in liveness[0].path


def test_liveness_in_progress_present_in_active_clean(tmp_path):
    """(e) in-progress dossier whose dir name appears in the ## Active
    section → clean."""
    _build_dossier(
        tmp_path,
        "correctness-audit-2026-07",
        _CHARTER_IN_PROGRESS,
        None,
        [],
    )
    _write_tree(
        tmp_path,
        {
            "knowledge/questions/INDEX.md": (
                "# Open Questions\n"
                "\n"
                "## Active\n"
                "\n"
                "- correctness-audit-2026-07 → `knowledge/questions/correctness-audit-2026-07.md`\n"
                "\n"
                "## Parked\n"
                "\n"
                "- Some parked item\n"
            )
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    liveness = [f for f in findings if f.check == "audit-liveness"]
    assert liveness == []


def test_liveness_in_progress_only_in_parked_flagged(tmp_path):
    """(f) in-progress dossier whose dir name appears only under
    ## Parked (not ## Active) → flagged."""
    _build_dossier(
        tmp_path,
        "correctness-audit-2026-07",
        _CHARTER_IN_PROGRESS,
        None,
        [],
    )
    _write_tree(
        tmp_path,
        {
            "knowledge/questions/INDEX.md": (
                "# Open Questions\n"
                "\n"
                "## Active\n"
                "\n"
                "<!-- nothing relevant -->\n"
                "\n"
                "## Parked\n"
                "\n"
                "- correctness-audit-2026-07 → `knowledge/questions/correctness-audit-2026-07.md`\n"
            )
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    liveness = [f for f in findings if f.check == "audit-liveness"]
    assert len(liveness) == 1
    assert "correctness-audit-2026-07" in liveness[0].path


# ===================================================================
# 3.2 — post-close ledger format check (_check_post_close_ledger)
# ===================================================================


def test_ledger_absent_no_findings(tmp_path):
    """(a) marked dossier with no POST-CLOSE-LEDGER.md → no
    post-close-ledger-format findings."""
    _build_dossier(
        tmp_path,
        "correctness-audit-2026-07",
        _CHARTER_CLOSED,
        None,
        [],
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ledger_findings = [f for f in findings if f.check == "post-close-ledger-format"]
    assert ledger_findings == []


def test_ledger_valid_lines_clean(tmp_path):
    """(b) ledger with valid entry lines — both bare form
    (a | b | c | d | e) and pipe-delimited table form
    (| a | b | c | d | e |) → clean."""
    _build_dossier(
        tmp_path,
        "correctness-audit-2026-07",
        _CHARTER_CLOSED,
        None,
        [],
    )
    ledger_content = "# Post-Close Ledger\n\na1 | b1 | c1 | d1 | e1\n| a2 | b2 | c2 | d2 | e2 |\n"
    _write_tree(
        tmp_path,
        {
            "knowledge/research/correctness-audit-2026-07/POST-CLOSE-LEDGER.md": ledger_content,
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ledger_findings = [f for f in findings if f.check == "post-close-ledger-format"]
    assert ledger_findings == []


def test_ledger_malformed_lines_flagged(tmp_path):
    """(c) entry line with fewer than five cells, and one with an empty
    cell → each flagged with its line number."""
    _build_dossier(
        tmp_path,
        "correctness-audit-2026-07",
        _CHARTER_CLOSED,
        None,
        [],
    )
    ledger_content = (
        "# Post-Close Ledger\n"
        "\n"
        "a1 | b1 | c1 | d1 | e1\n"
        "a2 | b2 | c2 | d2\n"  # only 4 cells -> flagged
        "\n"
        "a4 | b4 | c4 | d4 | \n"  # last cell empty -> flagged
    )
    _write_tree(
        tmp_path,
        {
            "knowledge/research/correctness-audit-2026-07/POST-CLOSE-LEDGER.md": ledger_content,
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ledger_findings = [f for f in findings if f.check == "post-close-ledger-format"]
    assert len(ledger_findings) == 2
    lines = {f.line for f in ledger_findings}
    assert 4 in lines  # line 4: only 4 cells
    assert 6 in lines  # line 6: last cell empty


def test_ledger_non_entry_lines_skipped(tmp_path):
    """(d) heading / table-separator / HTML-comment / blank lines
    alongside valid entries → not treated as entries, clean."""
    _build_dossier(
        tmp_path,
        "correctness-audit-2026-07",
        _CHARTER_CLOSED,
        None,
        [],
    )
    ledger_content = (
        "# Post-Close Ledger\n"
        "\n"
        "a1 | b1 | c1 | d1 | e1\n"
        "|---|---|---|\n"
        "<!-- a comment -->\n"
        "\n"
        "| a2 | b2 | c2 | d2 | e2 |\n"
    )
    _write_tree(
        tmp_path,
        {
            "knowledge/research/correctness-audit-2026-07/POST-CLOSE-LEDGER.md": ledger_content,
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    ledger_findings = [f for f in findings if f.check == "post-close-ledger-format"]
    assert ledger_findings == []


# ===================================================================
# 4.1 — claims-ledger staleness checks (_check_claims_ledger_staleness)
# ===================================================================


def _write_ledger_covered_file(tmp_path: Path, rel_path: str, content: bytes) -> tuple[Path, str]:
    """Write a covered file under *tmp_path*, returning (path, sha256 hex)."""
    target = tmp_path / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    import hashlib

    h = hashlib.sha256(content).hexdigest()
    return target, h


def test_claims_ledger_conforming_clean(tmp_path):
    """(a) conforming — marked ledger with matching sha256 → zero findings."""
    covered_path, actual_hash = _write_ledger_covered_file(tmp_path, "some/file.md", b"content")
    ledger = (
        "<!-- format: product-audit/v1 -->\n"
        "\n"
        "## Covered promise-surface files\n"
        f"- some/file.md — sha256:{actual_hash}\n"
        "\n"
        "## Claims\n"
        "| Promise | Delivering surface | Proving check | Disposition |\n"
    )
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/claims-ledger.md": ledger,
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    claims_findings = [f for f in findings if f.check == "claims-ledger-staleness"]
    assert claims_findings == []


def test_claims_ledger_conforming_uppercase_hash_clean(tmp_path):
    """(a2) conforming — recorded hash in UPPERCASE (case-insensitive match)."""
    covered_path, actual_hash = _write_ledger_covered_file(
        tmp_path, "docs/landing.html", b"landing content"
    )
    uppercase_hash = actual_hash.upper()
    ledger = (
        "<!-- format: product-audit/v1 -->\n"
        "\n"
        "## Covered promise-surface files\n"
        f"- docs/landing.html — sha256:{uppercase_hash}\n"
        "\n"
        "## Claims\n"
        "| Promise | ...\n"
    )
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/claims-ledger.md": ledger,
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    claims_findings = [f for f in findings if f.check == "claims-ledger-staleness"]
    assert claims_findings == []


def test_claims_ledger_drift_flagged(tmp_path):
    """(b) drift — recorded hash present but covered file content changed
    → exactly one finding naming the file."""
    covered_path, original_hash = _write_ledger_covered_file(
        tmp_path, "pricing/page.md", b"original content"
    )
    ledger = (
        "<!-- format: product-audit/v1 -->\n"
        "\n"
        "## Covered promise-surface files\n"
        f"- pricing/page.md — sha256:{original_hash}\n"
        "\n"
        "## Claims\n"
        "| Promise | ...\n"
    )
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/claims-ledger.md": ledger,
        },
    )
    # Now change the covered file's content (drift).
    covered_path.write_bytes(b"changed content")

    findings = knowledge_lint.collect_findings(tmp_path)
    claims_findings = [f for f in findings if f.check == "claims-ledger-staleness"]
    assert len(claims_findings) == 1
    assert "pricing/page.md" in claims_findings[0].message


def test_claims_ledger_missing_file_flagged(tmp_path):
    """(c) missing — a listed covered file does not exist on disk
    → one finding naming it."""
    actual_hash = "ab" * 32  # valid 64-char hex, but file doesn't exist
    ledger = (
        "<!-- format: product-audit/v1 -->\n"
        "\n"
        "## Covered promise-surface files\n"
        f"- pricing/gone.md — sha256:{actual_hash}\n"
        "\n"
        "## Claims\n"
        "| Promise | ...\n"
    )
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/claims-ledger.md": ledger,
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    claims_findings = [f for f in findings if f.check == "claims-ledger-staleness"]
    assert len(claims_findings) == 1
    assert "missing promise-surface file" in claims_findings[0].message
    assert "pricing/gone.md" in claims_findings[0].message


def test_claims_ledger_no_marker_skipped(tmp_path):
    """(d1) guard-skip — ledger without the format: product-audit/v1 marker
    → zero findings."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/claims-ledger.md": (
                "# Claims Ledger\n"
                "\n"
                "## Covered promise-surface files\n"
                "- missing/file.md — sha256:aa" + "bb" * 31 + "\n"
            ),
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    claims_findings = [f for f in findings if f.check == "claims-ledger-staleness"]
    assert claims_findings == []


def test_claims_ledger_no_ledger_file_skipped(tmp_path):
    """(d2) guard-skip — no knowledge/reference/*.md at all → zero findings."""
    _write_tree(
        tmp_path,
        {
            "knowledge/other.md": "# No reference dir\n",
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    claims_findings = [f for f in findings if f.check == "claims-ledger-staleness"]
    assert claims_findings == []


def test_claims_ledger_malformed_lines_skipped(tmp_path):
    """(d3) guard-skip — marked ledger with malformed manifest lines:
    one short/garbage hash (sha256:zzzz), one no-sha256 line, and one
    wrong-delimiter line (colon instead of em-dash).  All silently skipped.
    Also includes one conforming line with a real tracked file that
    matches — to avoid the false positive of 'no findings because no
    lines parsed at all'."""
    covered_path, actual_hash = _write_ledger_covered_file(
        tmp_path, "real/file.md", b"real content"
    )
    ledger = (
        "<!-- format: product-audit/v1 -->\n"
        "\n"
        "## Covered promise-surface files\n"
        "- short/hash.md — sha256:zzzz\n"
        "- no-hash-line.md — some text without sha256\n"
        "- wrong/delim.md : sha256:" + "aa" * 32 + "\n"
        f"- real/file.md — sha256:{actual_hash}\n"
        "\n"
        "## Claims\n"
        "| Promise | ...\n"
    )
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/claims-ledger.md": ledger,
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    claims_findings = [f for f in findings if f.check == "claims-ledger-staleness"]
    assert claims_findings == []


def test_claims_ledger_no_manifest_section_skipped(tmp_path):
    """(d4) guard-skip — marked ledger with NO ``## Covered promise-surface
    files`` section → zero findings."""
    covered_path, actual_hash = _write_ledger_covered_file(
        tmp_path, "real/file.md", b"real content"
    )
    ledger = (
        "<!-- format: product-audit/v1 -->\n"
        "\n"
        "## Other section\n"
        f"- real/file.md — sha256:{actual_hash}\n"
        "\n"
        "## Claims\n"
        "| Promise | ...\n"
    )
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/claims-ledger.md": ledger,
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    claims_findings = [f for f in findings if f.check == "claims-ledger-staleness"]
    assert claims_findings == []


def test_claims_ledger_empty_manifest_section_skipped(tmp_path):
    """(d5) guard-skip — marked ledger whose ``## Covered promise-surface
    files`` heading exists but has no entries before the next ``## `` heading
    → zero findings."""
    ledger = (
        "<!-- format: product-audit/v1 -->\n"
        "\n"
        "## Covered promise-surface files\n"
        "\n"
        "## Claims\n"
        "| Promise | ...\n"
    )
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/claims-ledger.md": ledger,
        },
    )
    findings = knowledge_lint.collect_findings(tmp_path)
    claims_findings = [f for f in findings if f.check == "claims-ledger-staleness"]
    assert claims_findings == []


# ===================================================================
# handoff-lint-exempt — the sanctioned `knowledge/HANDOFF.md` is exempt
# from the four prose-hygiene checks (retired-path-token,
# broken-prose-path-citation, dangling-archive-pointer,
# duplicate-content-block), keyed on EXACT path equality only.
# ===================================================================

# A quoted block, >=8 non-blank lines, identical (whitespace-normalized)
# across two files — trips duplicate-content-block.
_HANDOFF_QUOTED_BLOCK = "\n".join(
    f"Handoff quoted line {n} carried forward verbatim." for n in range(1, 10)
)


def _handoff_four_trips_content() -> str:
    """Prose that simultaneously trips all four prose-hygiene checks:
    a forward citation to a not-yet-created file (first path segment
    `knowledge` must already exist under the tree for the first-segment
    gate to treat it as a citation at all), a retired-path token, a
    planned archive pointer, and a quoted >=8-line block."""
    return (
        "# Session Handoff\n"
        "\n"
        "## Forward reference\n"
        "\n"
        "See `knowledge/reference/not-built-yet.md` for the module this "
        "session was building.\n"
        "\n"
        "## Retired-path note\n"
        "\n"
        "The old `ai-docs/` layout is gone; do not resurrect it.\n"
        "\n"
        "## Planned archive landing\n"
        "\n"
        "Follow-up tracked in "
        "openspec/changes/archive/2026-01-01-not-yet-landed/design.md.\n"
        "\n"
        "## Quoted context carried forward\n"
        "\n"
        f"{_HANDOFF_QUOTED_BLOCK}\n"
        "\n"
        "Tail content unique to the handoff.\n"
    )


def test_sanctioned_handoff_exempt_from_all_four_prose_hygiene_checks(tmp_path):
    """(4.1/4.2) `knowledge/HANDOFF.md` simultaneously trips all four
    prose-hygiene checks — a forward citation, a retired-path token, a
    planned archive pointer, and a quoted >=8-line block copied verbatim
    from `knowledge/README.md`. Assert ZERO findings against the handoff,
    AND zero collateral duplicate-content-block findings against the
    quoted file — proving the collateral finding is gone too, not just the
    handoff-side one."""
    _write_tree(
        tmp_path,
        {
            "knowledge/HANDOFF.md": _handoff_four_trips_content(),
            "knowledge/README.md": (
                "# Knowledge README\n"
                "\n"
                f"{_HANDOFF_QUOTED_BLOCK}\n"
                "\n"
                "Tail content unique to the README.\n"
            ),
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)

    handoff_findings = [f for f in findings if f.path == "knowledge/HANDOFF.md"]
    assert handoff_findings == []

    dup_findings_on_quoted_file = [
        f
        for f in findings
        if f.check == "duplicate-content-block" and f.path == "knowledge/README.md"
    ]
    assert dup_findings_on_quoted_file == []


def test_over_broad_suppression_guard_non_handoff_file_still_flagged(tmp_path):
    """(4.3, load-bearing) The IDENTICAL four constructs, placed in a
    NON-handoff knowledge file, are still flagged by all four checks.
    Without this guard the exemption could be widened to `knowledge/*`
    (or any substring match) and the rest of this suite would stay green
    while the linter went blind generally."""
    _write_tree(
        tmp_path,
        {
            "knowledge/reference/notes.md": _handoff_four_trips_content(),
            "knowledge/README.md": (
                "# Knowledge README\n"
                "\n"
                f"{_HANDOFF_QUOTED_BLOCK}\n"
                "\n"
                "Tail content unique to the README.\n"
            ),
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)
    notes_findings = [f for f in findings if f.path == "knowledge/reference/notes.md"]

    assert any(f.check == "broken-prose-path-citation" for f in notes_findings)
    assert any(f.check == "retired-path-token" for f in notes_findings)
    assert any(f.check == "dangling-archive-pointer" for f in notes_findings)
    assert any(f.check == "duplicate-content-block" for f in notes_findings)


def test_handoff_named_file_at_other_path_still_flagged_both_checks(tmp_path):
    """(4.4) A handoff-NAMED file at a path OTHER than the exact sanctioned
    `knowledge/HANDOFF.md` is still flagged by both the handoff-named-file
    check AND the broken-prose-path-citation check — proving the exemption
    keys on the exact path and does not leak to other handoff-named files.

    Placed under `knowledge/` (rather than e.g. `plans/session-handoff.md`,
    which the handoff-named check alone already covers at line ~845 above)
    because `broken-prose-path-citation` only ever scans
    `knowledge/**/*.md` by design (unrelated to this change) — a file
    outside `knowledge/` could never exercise that check regardless of the
    exemption, so it would not be a load-bearing guard for it.
    """
    _write_tree(
        tmp_path,
        {
            "knowledge/session-handoff.md": (
                "# Old handoff (not the sanctioned one)\n"
                "\n"
                "See `knowledge/does-not-exist.md` for details.\n"
            ),
        },
    )

    findings = knowledge_lint.collect_findings(tmp_path)

    handoff_named_findings = [
        f
        for f in findings
        if f.check == "handoff-file" and f.path == "knowledge/session-handoff.md"
    ]
    assert len(handoff_named_findings) == 1

    citation_findings = [
        f
        for f in findings
        if f.check == "broken-prose-path-citation" and f.path == "knowledge/session-handoff.md"
    ]
    assert len(citation_findings) == 1
