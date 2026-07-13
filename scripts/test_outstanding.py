#!/usr/bin/env python3
"""Tests for outstanding.py — pytest style, `tmp_path`-fixture based.

Mirrors test_knowledge_lint.py's fixture style: every test builds a
synthetic tree under pytest's `tmp_path` fixture and runs the gather
against it directly (no git and no real repo required unless a test is
specifically exercising git-dependent behavior).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import outstanding  # noqa: E402

# ===================================================================
# Helpers
# ===================================================================


def _write_tree(root: Path, files: dict[str, str]) -> None:
    """Write *files* (repo-relative path -> text content) under *root*,
    creating parent directories as needed."""
    for relpath, content in files.items():
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _run(root: Path, out_json: Path | None = None) -> tuple[int, Path, Path]:
    """Run ``outstanding.main`` against *root*; return (exit_code, json_path, md_path)."""
    out_json = out_json or (root / "output" / "facts" / "outstanding.json")
    argv = ["--root", str(root), "--out", str(out_json)]
    rc = outstanding.main(argv)
    return rc, out_json, out_json.with_suffix(".md")


def _load(out_json: Path) -> dict:
    return json.loads(out_json.read_text(encoding="utf-8"))


# ===================================================================
# 5.1 — clean run: both artifacts, exit 0, source:line provenance
# ===================================================================


def test_clean_run_writes_both_artifacts_and_exits_0(tmp_path):
    _write_tree(
        tmp_path,
        {
            "knowledge/questions/INDEX.md": ("## Active\n\n- A clean, well-formed open item.\n"),
            "knowledge/roadmap.md": ("## An open roadmap idea\n**Priority:** Medium\n"),
        },
    )

    rc, out_json, out_md = _run(tmp_path)

    assert rc == 0
    assert out_json.is_file()
    assert out_md.is_file()


def test_every_open_work_item_carries_source_line_provenance(tmp_path):
    _write_tree(
        tmp_path,
        {
            "knowledge/questions/INDEX.md": ("## Active\n\n- Item one.\n- Item two.\n"),
            "knowledge/roadmap.md": ("## An open idea\n**Priority:** Low\n"),
            "openspec/changes/some-change/tasks.md": ("- [ ] an unchecked task\n"),
        },
    )

    rc, out_json, _out_md = _run(tmp_path)
    assert rc == 0

    payload = _load(out_json)
    assert payload["open_work"], "expected at least one open-work item"
    for item in payload["open_work"]:
        assert item.get("source"), f"item missing source: {item!r}"
        assert item.get("line") is not None, f"item missing line: {item!r}"


# ===================================================================
# 5.1 — malformed source degrades, never crashes
# ===================================================================


def test_malformed_source_yields_unparseable_and_still_exits_0(tmp_path):
    questions_dir = tmp_path / "knowledge" / "questions"
    questions_dir.mkdir(parents=True)
    # Invalid UTF-8 bytes — a genuinely unparseable structured source.
    (questions_dir / "INDEX.md").write_bytes(b"## Active\n- bad byte: \xff\xfe end\n")

    rc, out_json, _out_md = _run(tmp_path)
    assert rc == 0

    payload = _load(out_json)
    unparseable = [
        item for item in payload["open_work"] if "UNPARSEABLE" in item.get("content", "")
    ]
    assert unparseable, "expected an UNPARSEABLE entry for the malformed source"
    assert "read manually" in unparseable[0]["content"]
    assert unparseable[0]["source"].endswith("INDEX.md")


# ===================================================================
# 5.1 — structured extraction is format-plural: bullet form + table form
# ===================================================================


def test_active_items_extracted_from_bullet_form(tmp_path):
    _write_tree(
        tmp_path,
        {
            "knowledge/questions/INDEX.md": (
                "## Active\n\n- First active bullet item.\n* Second, star-bulleted.\n1. Third, numbered.\n"
            )
        },
    )

    items = outstanding._enumerate_questions_index(tmp_path)
    contents = {item["content"] for item in items}
    assert "First active bullet item." in contents
    assert "Second, star-bulleted." in contents
    assert "Third, numbered." in contents
    assert all(item["section"] == "Active" for item in items)


def test_active_items_extracted_from_table_form(tmp_path):
    _write_tree(
        tmp_path,
        {
            "knowledge/questions/INDEX.md": (
                "## Active\n\n"
                "| ID | Description |\n"
                "| --- | --- |\n"
                "| CA-1 | Something is outstanding |\n"
            )
        },
    )

    items = outstanding._enumerate_questions_index(tmp_path)
    # Only the data row is extracted — header and separator rows are not items.
    assert len(items) == 1
    assert "CA-1" in items[0]["content"]
    assert "Something is outstanding" in items[0]["content"]
    assert items[0]["section"] == "Active"


# ===================================================================
# 5.1 — prose-only source enumerated point-only, never fabricated
# ===================================================================


def test_prose_only_per_item_file_enumerated_point_only(tmp_path):
    _write_tree(
        tmp_path,
        {
            "knowledge/questions/some-idea.md": (
                "# Some Idea\n\nJust prose. No list items here at all — several\n"
                "paragraphs of narrative text, no bullets, no numbered points.\n"
            )
        },
    )

    items = outstanding._enumerate_prose_files(tmp_path)
    matches = [i for i in items if i["source"].endswith("some-idea.md")]
    # Exactly one point-only entry — no fabricated line-items from the prose body.
    assert len(matches) == 1
    assert matches[0]["line"] == 1
    assert matches[0]["content"].startswith("[untracked]") or matches[0]["content"].startswith(
        "[tracked]"
    )
    assert "Some Idea" in matches[0]["content"]


def test_prose_only_plan_file_enumerated_point_only(tmp_path):
    _write_tree(
        tmp_path,
        {"plans/some-plan.md": ("# Some Plan\n\nNarrative-only plan body, no structured items.\n")},
    )

    items = outstanding._enumerate_prose_files(tmp_path)
    matches = [i for i in items if i["source"].endswith("some-plan.md")]
    assert len(matches) == 1
    assert matches[0]["line"] == 1


# ===================================================================
# 5.2 — untriaged bucket: absent from questions/ -> untriaged; triaging
# moves it out on re-run
# ===================================================================


def test_untriaged_finding_absent_from_questions_lands_in_bucket(tmp_path):
    _write_tree(
        tmp_path,
        {
            "knowledge/research/some-audit/FINDINGS.md": ("Found issue CA-W1-1 in the wild.\n"),
        },
    )

    untriaged = outstanding.extract_untriaged(tmp_path, {})
    ids = {item["id"] for item in untriaged}
    assert "CA-W1-1" in ids


def test_triaging_moves_finding_out_of_untriaged_bucket_on_rerun(tmp_path):
    _write_tree(
        tmp_path,
        {
            "knowledge/research/some-audit/FINDINGS.md": ("Found issue CA-W1-1 in the wild.\n"),
        },
    )

    untriaged_before = outstanding.extract_untriaged(tmp_path, {})
    assert "CA-W1-1" in {item["id"] for item in untriaged_before}

    # Triage: reference the finding ID under knowledge/questions/.
    _write_tree(
        tmp_path,
        {
            "knowledge/questions/INDEX.md": ("## Active\n\n- Triaged: see CA-W1-1.\n"),
        },
    )

    untriaged_after = outstanding.extract_untriaged(tmp_path, {})
    assert "CA-W1-1" not in {item["id"] for item in untriaged_after}


def test_untriaged_finding_referenced_in_per_item_question_file_is_triaged(tmp_path):
    _write_tree(
        tmp_path,
        {
            "knowledge/research/some-audit/FINDINGS.md": ("Found issue CA-W9-9 in the wild.\n"),
            "knowledge/questions/some-item.md": ("# Some Item\n\nTracking CA-W9-9 here.\n"),
        },
    )

    untriaged = outstanding.extract_untriaged(tmp_path, {})
    assert "CA-W9-9" not in {item["id"] for item in untriaged}


# ===================================================================
# 5.2 — plans/archive/** excluded, top-level plans/*.md listed
# ===================================================================


def test_plans_archive_excluded_top_level_listed(tmp_path):
    _write_tree(
        tmp_path,
        {
            "plans/live-plan.md": "# Live Plan\n\nStill open.\n",
            "plans/archive/shipped-plan.md": "# Shipped Plan\n\nAlready archived.\n",
        },
    )

    items = outstanding._enumerate_prose_files(tmp_path)
    sources = {item["source"] for item in items}
    assert any(s.endswith("plans/live-plan.md") for s in sources)
    assert not any("plans/archive" in s for s in sources)


# ===================================================================
# 5.2 — absent-config defaults run cleanly
# ===================================================================


def test_absent_config_runs_cleanly_on_defaults(tmp_path):
    assert not (tmp_path / "checks.toml").exists()
    _write_tree(tmp_path, {"knowledge/roadmap.md": "## Some open idea\n**Priority:** Low\n"})

    rc, out_json, out_md = _run(tmp_path)
    assert rc == 0
    assert out_json.is_file()
    assert out_md.is_file()


# ===================================================================
# 5.2 — per-repo finding_id_pattern honored, scanned-vs-matched visible
# ===================================================================


def test_per_repo_finding_id_pattern_honored_with_scanned_matched_count(tmp_path):
    _write_tree(
        tmp_path,
        {
            "checks.toml": (
                "[facts.outstanding]\n"
                'findings_globs = ["custom_findings/**/*.md"]\n'
                'finding_id_pattern = "FOO-\\\\d+"\n'
            ),
            "custom_findings/area/REPORT.md": ("Custom-scheme finding FOO-42 needs triage.\n"),
        },
    )

    rc, out_json, out_md = _run(tmp_path)
    assert rc == 0

    payload = _load(out_json)
    assert payload["config"]["finding_id_pattern"] == "FOO-\\d+"
    untriaged_ids = {item["id"] for item in payload["untriaged"]}
    assert "FOO-42" in untriaged_ids

    # The default pattern would NOT have matched "FOO-42" the same way the
    # custom pattern's exact scheme is honored — and the scanned-vs-matched
    # count is visible in the rendered snapshot (non-empty file, non-zero
    # match count).
    md_text = out_md.read_text(encoding="utf-8")
    assert "Findings files scanned: 1" in md_text
    assert "Finding IDs matched: 1" in md_text


# ===================================================================
# 5.2 — open-work provenance is repo-relative, not absolute
# ===================================================================


def test_open_work_source_is_repo_relative_not_absolute(tmp_path):
    _write_tree(
        tmp_path,
        {
            "knowledge/questions/INDEX.md": "## Active\n\n- An open item.\n",
            "knowledge/roadmap.md": "## An open idea\n**Priority:** Low\n",
            "knowledge/questions/some-item.md": "# A per-item file\n",
        },
    )
    rc, out_json, _ = _run(tmp_path)
    assert rc == 0
    payload = _load(out_json)
    assert payload["open_work"]
    for item in payload["open_work"]:
        src = item["source"]
        assert not src.startswith("/"), f"source must be repo-relative, got absolute: {src!r}"
        assert not os.path.isabs(src), f"source must be repo-relative, got: {src!r}"
    # spot-check the concrete relative path is present
    sources = {item["source"] for item in payload["open_work"]}
    assert "knowledge/questions/INDEX.md" in sources


# ===================================================================
# 4.4 — composition-audit due-signal tests (AC1)
# ===================================================================


def _git(cmd: list[str], cwd: Path) -> str:
    """Run a git command in *cwd*, assert success, return stdout."""
    import subprocess as _sp

    result = _sp.run(["git", *cmd], cwd=str(cwd), capture_output=True, text=True)
    assert result.returncode == 0, f"git {' '.join(cmd)} failed: {result.stderr}"
    return result.stdout


def _git_init(tmp_path: Path) -> Path:
    """Create a minimal git repo under *tmp_path* and return its root."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init", "-b", "main"], repo)
    _git(["config", "user.email", "test@example.com"], repo)
    _git(["config", "user.name", "Test User"], repo)
    # Initial commit.
    (repo / "README.md").write_text("# repo\n")
    _git(["add", "README.md"], repo)
    _git(["commit", "-m", "initial"], repo)
    return repo


def test_composition_no_anchor_archives_below_threshold(tmp_path):
    """No composition tag, fewer archives than threshold → not due."""
    repo = _git_init(tmp_path)
    # Create 1 archive dir (threshold default is 10).
    archive_dir = repo / "openspec" / "changes" / "archive" / "change-one"
    archive_dir.mkdir(parents=True)
    (archive_dir / "file.md").write_text("x")
    _git(["add", "-A"], repo)
    _git(["commit", "-m", "add archive"], repo)

    sig = outstanding._composition_signal(repo, {})
    assert sig["due"] is False
    assert sig["status"] == "ok"
    assert sig["anchor_tag"] is None
    assert sig["archived_changes_since"] == 1


def test_composition_no_anchor_archives_above_threshold_due(tmp_path):
    """No composition tag, ≥10 archives → due (extrends-shape)."""
    repo = _git_init(tmp_path)
    archive_root = repo / "openspec" / "changes" / "archive"
    for i in range(10):
        d = archive_root / f"change-{i}"
        d.mkdir(parents=True)
        (d / "file.md").write_text(f"content-{i}")
    _git(["add", "-A"], repo)
    _git(["commit", "-m", "add 10 archives"], repo)

    sig = outstanding._composition_signal(repo, {})
    assert sig["due"] is True
    assert sig["status"] == "ok"
    assert sig["archived_changes_since"] == 10
    assert "archived changes" in sig.get("reason", "")


def test_plain_audit_tag_does_not_reset_composition(tmp_path):
    """Plain audit/<date> tag after a composition anchor does NOT reset the clock."""
    repo = _git_init(tmp_path)
    # Create a composition anchor.
    _git(["tag", "-a", "audit/2026-07-01-composition", "-m", "comp", "HEAD"], repo)
    # Add an archive dir.
    archive_dir = repo / "openspec" / "changes" / "archive" / "change-a"
    archive_dir.mkdir(parents=True)
    (archive_dir / "f.md").write_text("a")
    _git(["add", "-A"], repo)
    _git(["commit", "-m", "add archive"], repo)
    # Then a plain audit tag.
    import time

    time.sleep(1.1)
    _git(["tag", "-a", "audit/2026-07-02", "-m", "plain", "HEAD"], repo)

    sig = outstanding._composition_signal(repo, {})
    # composition_anchor should still be the composition tag (plain tag does
    # NOT reset the clock), archived_changes_since still counts from it.
    assert sig["anchor_tag"] == "audit/2026-07-01-composition"
    assert sig["archived_changes_since"] >= 1


def test_composition_anchor_at_head_resets_clock(tmp_path):
    """Composition anchor at HEAD → counts reset to zero."""
    repo = _git_init(tmp_path)
    # Create an archive dir.
    archive_dir = repo / "openspec" / "changes" / "archive" / "change-a"
    archive_dir.mkdir(parents=True)
    (archive_dir / "f.md").write_text("a")
    _git(["add", "-A"], repo)
    _git(["commit", "-m", "add archive"], repo)
    # Create composition anchor at HEAD.
    _git(["tag", "-a", "audit/2026-07-11-composition", "-m", "comp", "HEAD"], repo)

    sig = outstanding._composition_signal(repo, {})
    assert sig["anchor_tag"] == "audit/2026-07-11-composition"
    assert sig["archived_changes_since"] == 0
    assert sig["commits_since"] == 0
    assert sig["due"] is False


def test_composition_thresholds_honored_from_config(tmp_path):
    """Custom thresholds from config are honored."""
    repo = _git_init(tmp_path)
    # Create 1 archive dir. With custom threshold 1, it should be due.
    archive_dir = repo / "openspec" / "changes" / "archive" / "change-a"
    archive_dir.mkdir(parents=True)
    (archive_dir / "f.md").write_text("a")
    _git(["add", "-A"], repo)
    _git(["commit", "-m", "add archive"], repo)

    config_with_thresholds = {
        "facts": {
            "outstanding": {
                "composition_change_threshold": 1,
                "composition_commit_threshold": 9999,
            }
        }
    }
    sig = outstanding._composition_signal(repo, config_with_thresholds)
    assert sig["due"] is True
    assert sig["thresholds"]["changes"] == 1


def test_composition_or_cofire_commits_trip_with_sparse_archives(tmp_path):
    """Commits threshold can trip when archive count is low (OR co-fire)."""
    repo = _git_init(tmp_path)
    # Composition anchor at initial commit.
    _git(["tag", "-a", "audit/2026-07-01-composition", "-m", "comp", "HEAD"], repo)
    # Add many small commits (no archives).
    for i in range(5):
        (repo / f"file_{i}.py").write_text(f"x = {i}\n")
        _git(["add", "-A"], repo)
        _git(["commit", "-m", f"commit {i}"], repo)
    import time

    time.sleep(1.1)

    config_low_commits = {
        "facts": {
            "outstanding": {
                "composition_change_threshold": 9999,
                "composition_commit_threshold": 3,
            }
        }
    }
    sig = outstanding._composition_signal(repo, config_low_commits)
    assert sig["due"] is True
    assert "commits" in sig.get("reason", "")


def test_composition_post_archive_edit_does_not_inflate(tmp_path):
    """Post-archive edit to an existing archive dir does NOT inflate count."""
    repo = _git_init(tmp_path)
    archive_root = repo / "openspec" / "changes" / "archive"
    change_dir = archive_root / "change-a"
    change_dir.mkdir(parents=True)
    (change_dir / "f.md").write_text("original\n")
    _git(["add", "-A"], repo)
    _git(["commit", "-m", "add archive"], repo)
    # Create composition anchor.
    _git(["tag", "-a", "audit/2026-07-01-composition", "-m", "comp", "HEAD"], repo)
    # Now edit f.md (modification, not add).
    (change_dir / "f.md").write_text("edited\n")
    _git(["add", "-A"], repo)
    _git(["commit", "-m", "edit archive file"], repo)

    sig = outstanding._composition_signal(repo, {})
    # Git diff --diff-filter=A sees NO added files — the file was modified but not added.
    assert sig["archived_changes_since"] == 0


def test_composition_no_git_degradation(tmp_path):
    """No-git scenario → status: no-git, due: false, fact still renders."""
    repo = tmp_path / "no-git-repo"
    repo.mkdir()
    (repo / "README.md").write_text("# no git here\n")
    sig = outstanding._composition_signal(repo, {})
    assert sig["status"] == "no-git"
    assert sig["due"] is False
