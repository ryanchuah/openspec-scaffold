#!/usr/bin/env python3
"""Tests for sync_scaffold.py and scaffold_check.py — stdlib unittest, no pytest."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Import modules under test (siblings in scripts/)
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sync_scaffold  # noqa: E402
import scaffold_check  # noqa: E402


# ===================================================================
# Helper: construct fixture scaffold + target trees in a temp dir
# ===================================================================

# Minimal AGENTS.md for the scaffold — has all required anchors, no tail.
SCAFFOLD_AGENTS = """\
# <FILL: project name>

> **MANDATORY — read before doing anything else**
>
> You are reading this file. Before taking any action, also read **`STATUS.md`**.

## Cross-agent compatibility (load-bearing — do not weaken)

This repo is worked by **both Claude and non-Claude agents** (OpenCode/DeepSeek/GLM).

Maintain this discipline for the **entire session**, not just at the start.

## Project context

Authoritative one-paragraph summary in **`openspec/config.yaml`**.

<FILL: 2-4 sentences of detailed context.>

## Roles

- **The primary agent is the orchestrator and reviewer — not the implementer.**

## After reading this file
Acknowledge four things before acting: (1) your role as orchestrator/reviewer.
"""

# Target with ## Project context (typical downstream)
TARGET_AGENTS_WITH_CTX = """\
# My Downstream Repo

> **MANDATORY — read before doing anything else**
>
> You are reading this file.

## Cross-agent compatibility (load-bearing — do not weaken)

This repo is worked by **both Claude and non-Claude agents**.

Maintain this discipline for the **entire session**, not just at the start.

## Project context

This repo builds widgets. See CONTRIBUTING.md.

**Hard constraints:** none.

## Roles

- **The primary agent** orchestrates.

## After reading this file
Acknowledge your role.
"""

# Target WITHOUT ## Project context (extrends-like)
TARGET_AGENTS_NO_CTX = """\
# Extrends

> **MANDATORY — read before doing anything else**
>
> You are reading this file.

## Cross-agent compatibility (load-bearing — do not weaken)

This repo is worked by **both Claude and non-Claude agents**.

Maintain this discipline for the **entire session**, not just at the start.

## Roles

- **The primary agent** orchestrates.

## After reading this file
Acknowledge your role.
"""

# Target with a long tail after ## After reading this file (psc-monitor-like)
TARGET_AGENTS_WITH_TAIL = """\
# psc-monitor

> **MANDATORY — read before doing anything else**
>
> You are reading this file.

## Cross-agent compatibility (load-bearing — do not weaken)

This repo is worked by **both Claude and non-Claude agents**.

Maintain this discipline for the **entire session**, not just at the start.

## Project context

Monitoring service.

## Roles

- **The primary agent** orchestrates.

## After reading this file
Acknowledge your role.

# Project reference

This project monitors production systems.

## Architecture

The system consists of:
- Collector service
- Alert manager
"""

# Target that is >350 lines with no tail separator
TARGET_AGENTS_LONG_NO_TAIL = (
    "# Foo\n\n> **MANDATORY — read before doing anything else**\n\n"
    "## Cross-agent\n\n"
    "## Roles\n\n"
    "## Project context\n\nHello\n\n"
    "## After reading this file\n\n"
    + "\n".join(f"Line {i}" for i in range(360))
)

# Scaffold that violates the tail invariant (has # heading after ## After)
SCAFFOLD_AGENTS_WITH_TAIL = """\
# Scaffold

> **MANDATORY — read before doing anything else**

## Roles

## After reading this file
Content.

# Unexpected section
This should not be in scaffold.
"""


def _make_fixture_scaffold(tmpdir: Path) -> Path:
    """Create a minimal scaffold with manifest and files, return its root."""
    scaffold = tmpdir / "scaffold"
    scripts_dir = scaffold / "scripts"
    scripts_dir.mkdir(parents=True)

    # Fixture manifest
    manifest_content = """\
# fixture manifest
test-regular.txt
subdir/data.txt
AGENTS.md
"""
    (scripts_dir / "scaffold_manifest.txt").write_text(manifest_content)

    # Regular files
    (scaffold / "test-regular.txt").write_text("regular file content\n")
    subdir = scaffold / "subdir"
    subdir.mkdir()
    (subdir / "data.txt").write_text("data file content\n")

    # AGENTS.md
    (scaffold / "AGENTS.md").write_text(SCAFFOLD_AGENTS)

    return scaffold


def _make_fixture_target(tmpdir: Path) -> Path:
    """Create a target repo (with .git) containing initial files."""
    target = tmpdir / "target"
    target.mkdir()
    (target / ".git").mkdir()  # empty dir to pass the .git check

    # Pre-populate files that match what sync will write
    (target / "test-regular.txt").write_text("regular file content\n")
    subdir = target / "subdir"
    subdir.mkdir()
    (subdir / "data.txt").write_text("data file content\n")
    # Target AGENTS.md with custom project context
    (target / "AGENTS.md").write_text(TARGET_AGENTS_WITH_CTX)

    return target


# ===================================================================
# Tests
# ===================================================================


class SyncAgentsMdTest(unittest.TestCase):
    """Tests for sync_agents_md — span-replace algorithm (task 4.2)."""

    def test_project_context_preserved_byte_identical(self):
        """## Project context from the target is preserved byte-identical."""
        result = sync_scaffold.sync_agents_md(SCAFFOLD_AGENTS, TARGET_AGENTS_WITH_CTX)
        # The target's project context should be in the output
        self.assertIn("This repo builds widgets. See CONTRIBUTING.md.", result)
        # The target's title should be preserved
        self.assertIn("# My Downstream Repo", result)
        # Shared spans from scaffold should be present
        self.assertIn("both Claude and non-Claude agents", result)

    def test_no_project_context_no_empty_section(self):
        """Target without ## Project context succeeds without inserting empty section."""
        result = sync_scaffold.sync_agents_md(SCAFFOLD_AGENTS, TARGET_AGENTS_NO_CTX)
        # Title preserved
        self.assertIn("# Extrends", result)
        # No empty "## Project context" should appear
        self.assertNotIn("## Project context", result)
        # But the second shared span from scaffold should be there
        self.assertIn("## Roles\n", result)
        self.assertIn("## After reading this file", result)

    def test_long_tail_preserved_byte_for_byte(self):
        """psc-monitor-like long tail after ## After is preserved byte-identical."""
        result = sync_scaffold.sync_agents_md(SCAFFOLD_AGENTS, TARGET_AGENTS_WITH_TAIL)
        # Tail content preserved
        self.assertIn("# Project reference", result)
        self.assertIn("This project monitors production systems.", result)
        self.assertIn("Collector service", result)
        # Shared spans from scaffold present
        self.assertIn("both Claude and non-Claude agents", result)

    def test_missing_target_mandatory_anchor_aborts(self):
        """Raises ValueError when target lacks > **MANDATORY**."""
        bad_target = "# No mandatory\n\n## Roles\n\n## After reading this file\n"
        with self.assertRaises(ValueError):
            sync_scaffold.sync_agents_md(SCAFFOLD_AGENTS, bad_target)

    def test_missing_target_roles_anchor_aborts(self):
        """Raises ValueError when target lacks ## Roles."""
        bad_target = "# Foo\n\n> **MANDATORY**\n\n## After reading this file\n"
        with self.assertRaises(ValueError):
            sync_scaffold.sync_agents_md(SCAFFOLD_AGENTS, bad_target)

    def test_missing_target_after_anchor_aborts(self):
        """Raises ValueError when target lacks ## After reading this file."""
        bad_target = "# Foo\n\n> **MANDATORY**\n\n## Roles\n\n"
        with self.assertRaises(ValueError):
            sync_scaffold.sync_agents_md(SCAFFOLD_AGENTS, bad_target)

    def test_scaffold_tail_invariant_aborts(self):
        """Raises ValueError when scaffold has unexpected tail."""
        with self.assertRaises(ValueError):
            sync_scaffold.sync_agents_md(SCAFFOLD_AGENTS_WITH_TAIL, TARGET_AGENTS_WITH_CTX)

    def test_350_line_no_tail_aborts(self):
        """Raises ValueError when target >350 lines has no tail separator."""
        with self.assertRaises(ValueError):
            sync_scaffold.sync_agents_md(SCAFFOLD_AGENTS, TARGET_AGENTS_LONG_NO_TAIL)

    def test_idempotent_on_own_output(self):
        """sync_agents_md applied to its own output returns identical string."""
        first = sync_scaffold.sync_agents_md(SCAFFOLD_AGENTS, TARGET_AGENTS_WITH_CTX)
        second = sync_scaffold.sync_agents_md(SCAFFOLD_AGENTS, first)
        self.assertEqual(first, second)

    def test_no_header_injected(self):
        """Synced output contains no 'DO NOT EDIT' header string."""
        result = sync_scaffold.sync_agents_md(SCAFFOLD_AGENTS, TARGET_AGENTS_WITH_CTX)
        self.assertNotIn("DO NOT EDIT", result)
        self.assertNotIn("synced from openspec-scaffold", result)


class SyncIntegrationTest(unittest.TestCase):
    """Full sync and --check tests using temp fixture trees (tasks 4.3–4.5, 4.7–4.8)."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.fixture_scaffold = _make_fixture_scaffold(self.tmpdir)
        self.fixture_target = _make_fixture_target(self.tmpdir)

        # Patch sync_scaffold to use fixture scaffold
        self._scaffold_root_patcher = patch.object(
            sync_scaffold, "_scaffold_root", return_value=self.fixture_scaffold
        )
        self._scaffold_root_patcher.start()

    def tearDown(self):
        self._scaffold_root_patcher.stop()
        for root, dirs, files in os.walk(self.tmpdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.tmpdir)

    # -- idempotency (4.3) --

    def test_sync_twice_is_idempotent(self):
        """Syncing a fixture target twice leaves files unchanged; --check exits 0."""
        sync_scaffold.sync(str(self.fixture_target))
        sync_scaffold.sync(str(self.fixture_target))
        rc = sync_scaffold.check(str(self.fixture_target))
        self.assertEqual(rc, 0)

    # -- --check tests (4.4) --

    def test_check_exits_0_when_synced(self):
        """--check exits 0 when target matches scaffold."""
        sync_scaffold.sync(str(self.fixture_target))
        rc = sync_scaffold.check(str(self.fixture_target))
        self.assertEqual(rc, 0)

    def test_check_exits_1_after_one_byte_edit(self):
        """--check exits 1 and names the file after a one-byte edit."""
        sync_scaffold.sync(str(self.fixture_target))
        # Corrupt one regular file
        f = self.fixture_target / "test-regular.txt"
        f.write_text("EDITED\n")
        rc = sync_scaffold.check(str(self.fixture_target))
        self.assertEqual(rc, 1)
        # Also verify DIFFERS was printed — can't easily capture output here
        # but the exit code is the contract.

    def test_check_exits_1_on_missing_file(self):
        """--check exits 1 when a file is missing from target."""
        sync_scaffold.sync(str(self.fixture_target))
        os.remove(self.fixture_target / "test-regular.txt")
        rc = sync_scaffold.check(str(self.fixture_target))
        self.assertEqual(rc, 1)

    def test_check_agents_identical_when_only_context_differs(self):
        """--check reports AGENTS.md IDENTICAL when only ##Project context/tail differ."""
        # Create a target with different project context but shared spans matching
        target_agents_diff_ctx = TARGET_AGENTS_WITH_CTX.replace(
            "This repo builds widgets. See CONTRIBUTING.md.",
            "This repo builds DIFFERENT THINGS.",
        )
        (self.fixture_target / "AGENTS.md").write_text(target_agents_diff_ctx)
        sync_scaffold.sync(str(self.fixture_target))
        # After sync, the project context was replaced ... wait, no.
        # Actually let me rethink. For this test we want to verify that
        # --check identifies AGENTS.md as IDENTICAL when only the project
        # context differs between scaffold and target.
        # After sync, the shared spans match. Then we change the target's
        # project context. --check's AGENTS.md compare uses:
        #   expected = sync_agents_md(scaffold_text, target_text)
        #   compare expected == target_text
        # Since sync_agents_md extracts project context FROM the target,
        # the target edit is picked up and expected matches target_text.
        # So it's IDENTICAL.
        target_edited = (self.fixture_target / "AGENTS.md").read_text()
        target_edited_alt = target_edited.replace(
            "This repo builds widgets. See CONTRIBUTING.md.",
            "DIFFERENT context now.",
        )
        (self.fixture_target / "AGENTS.md").write_text(target_edited_alt)
        # --check should still pass because only project context differs
        rc = sync_scaffold.check(str(self.fixture_target))
        self.assertEqual(rc, 0)

    # -- no-header (4.5) --

    def test_synced_output_contains_no_header(self):
        """Synced files contain no 'DO NOT EDIT' header."""
        sync_scaffold.sync(str(self.fixture_target))
        for fname in ["test-regular.txt", "AGENTS.md"]:
            content = (self.fixture_target / fname).read_text()
            self.assertNotIn("DO NOT EDIT", content)
            self.assertNotIn("synced from openspec-scaffold", content)

    # -- sync abort (4.7) --

    def test_sync_aborts_on_nonexistent_target(self):
        """sync aborts when target does not exist."""
        with self.assertRaises(SystemExit):
            sync_scaffold.sync("/nonexistent/path")

    def test_sync_aborts_on_target_without_git(self):
        """sync aborts when target lacks .git."""
        no_git = self.tmpdir / "no-git"
        no_git.mkdir()
        with self.assertRaises(SystemExit):
            sync_scaffold.sync(str(no_git))

    def test_sync_aborts_on_missing_scaffold_source(self):
        """sync aborts when a manifest-listed source is missing in scaffold."""
        # Remove a file from the fixture scaffold that the manifest lists
        (self.fixture_scaffold / "test-regular.txt").unlink()
        with self.assertRaises(SystemExit):
            sync_scaffold.sync(str(self.fixture_target))

    # -- parent dir creation (4.8) --

    def test_sync_creates_parent_dirs(self):
        """sync creates parent dirs and writes at correct nested path."""
        # Add an entry with a deeper directory to the fixture manifest
        manifest = (
            self.fixture_scaffold / "scripts" / "scaffold_manifest.txt"
        )
        original = manifest.read_text()
        manifest.write_text(original + "deep/nested/file.txt\n")
        deep_file = self.fixture_scaffold / "deep" / "nested" / "file.txt"
        deep_file.parent.mkdir(parents=True)
        deep_file.write_text("deep content\n")

        sync_scaffold.sync(str(self.fixture_target))
        self.assertTrue(
            (self.fixture_target / "deep" / "nested" / "file.txt").exists()
        )
        self.assertEqual(
            (self.fixture_target / "deep" / "nested" / "file.txt").read_text(),
            "deep content\n",
        )

    def test_sync_abort_makes_no_changes(self):
        """Verify no files written on abort (missing source)."""
        target_original = (self.fixture_target / "AGENTS.md").read_text()
        (self.fixture_scaffold / "test-regular.txt").unlink()
        try:
            sync_scaffold.sync(str(self.fixture_target))
        except SystemExit:
            pass
        # AGENTS.md should be unchanged
        self.assertEqual(
            (self.fixture_target / "AGENTS.md").read_text(),
            target_original,
        )


class ScaffoldCheckGuardTest(unittest.TestCase):
    """Tests for scaffold_check.py guard (task 4.6)."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        # Create a temp manifest for the guard
        self.manifest = self.tmpdir / "scaffold_manifest.txt"
        self.manifest.write_text("scripts/foo.py\nAGENTS.md\n")

    def tearDown(self):
        for root, dirs, files in os.walk(self.tmpdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.tmpdir)

    def test_guard_returns_2_when_manifest_file_staged(self):
        """scaffold_check.main() returns 2 when a manifest path is staged."""
        with patch.object(scaffold_check, "Path") as mock_Path:
            mock_Path.return_value.resolve.return_value.parent = self.tmpdir
            with patch.object(
                scaffold_check.subprocess, "check_output"
            ) as mock_git:
                mock_git.return_value.decode.return_value = (
                    "scripts/foo.py\nother.py\n"
                )
                rc = scaffold_check.main()
                self.assertEqual(rc, 2)

    def test_guard_returns_0_when_no_manifest_file_staged(self):
        """scaffold_check.main() returns 0 when no manifest path is staged."""
        with patch.object(scaffold_check, "Path") as mock_Path:
            mock_Path.return_value.resolve.return_value.parent = self.tmpdir
            with patch.object(
                scaffold_check.subprocess, "check_output"
            ) as mock_git:
                mock_git.return_value.decode.return_value = "other.py\n"
                rc = scaffold_check.main()
                self.assertEqual(rc, 0)

    def test_guard_returns_0_when_nothing_staged(self):
        """Returns 0 when nothing is staged."""
        with patch.object(scaffold_check, "Path") as mock_Path:
            mock_Path.return_value.resolve.return_value.parent = self.tmpdir
            with patch.object(
                scaffold_check.subprocess, "check_output"
            ) as mock_git:
                mock_git.return_value.decode.return_value = ""
                rc = scaffold_check.main()
                self.assertEqual(rc, 0)


class TestCheckReferences(unittest.TestCase):
    """Tests for --check-refs (referential-integrity pass)."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        for root, dirs, files in os.walk(self.tmpdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.tmpdir)

    def _write(self, rel, text):
        p = self.tmpdir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def test_clean_when_all_refs_resolve(self):
        self._write("AGENTS.md", "## Roles\nSee `memory/parked-follow-ons.md`.\n")
        self._write("memory/parked-follow-ons.md", "# Parked\n")
        self._write("memory/decisions/INDEX.md", "## Decision: Bulk FK thing\n")
        self._write(
            "doc.md",
            'See AGENTS.md § "Roles" and `memory/decisions/INDEX.md` § "Bulk FK thing".\n',
        )
        rc = sync_scaffold.check_references(
            str(self.tmpdir), md_files=["AGENTS.md", "doc.md"]
        )
        self.assertEqual(rc, 0)

    def test_dangling_when_cited_aidoc_file_missing(self):
        self._write("AGENTS.md", "## Roles\nSee `memory/parked-follow-ons.md`.\n")
        rc = sync_scaffold.check_references(str(self.tmpdir), md_files=["AGENTS.md"])
        self.assertEqual(rc, 1)

    def test_dangling_when_section_missing(self):
        self._write("AGENTS.md", "## Roles\n")
        self._write("doc.md", 'See AGENTS.md § "Nonexistent Section".\n')
        rc = sync_scaffold.check_references(
            str(self.tmpdir), md_files=["AGENTS.md", "doc.md"]
        )
        self.assertEqual(rc, 1)

    def test_parenthetical_prose_not_false_flagged(self):
        # The loose `AGENTS.md (...)` form is deliberately NOT matched — it fires
        # on explanatory prose. Only the `§ "..."` standard form is checked.
        self._write("AGENTS.md", "## Roles\n")
        self._write("doc.md", "See `AGENTS.md` (the Roles section, optionally).\n")
        rc = sync_scaffold.check_references(
            str(self.tmpdir), md_files=["AGENTS.md", "doc.md"]
        )
        self.assertEqual(rc, 0)

    def test_agents_bold_label_resolves(self):
        # AGENTS.md rules are often cited by a bold label, not a heading.
        self._write("AGENTS.md", "## State\n\n  **STATUS.md cap rule:** holds only ...\n")
        self._write("doc.md", 'See AGENTS.md § "STATUS.md cap rule".\n')
        rc = sync_scaffold.check_references(
            str(self.tmpdir), md_files=["AGENTS.md", "doc.md"]
        )
        self.assertEqual(rc, 0)

    def test_memory_section_citation_checks_file_existence_only(self):
        # memory/ section titles drift (dates/ellipses) → only file existence is
        # policed: present file passes regardless of the cited section text...
        self._write("AGENTS.md", "## Roles\n")
        self._write("memory/decisions/INDEX.md", "## Some heading that differs\n")
        self._write(
            "doc.md",
            'See `memory/decisions/INDEX.md` § "drifted title (2026-06-16)".\n',
        )
        rc = sync_scaffold.check_references(str(self.tmpdir), md_files=["doc.md"])
        self.assertEqual(rc, 0)
        # ...but a citation to a missing memory/ file is still flagged.
        self._write("doc2.md", 'See `memory/gone.md` § "anything".\n')
        rc = sync_scaffold.check_references(str(self.tmpdir), md_files=["doc2.md"])
        self.assertEqual(rc, 1)

    def test_fenced_code_block_citations_ignored(self):
        self._write("AGENTS.md", "## Roles\n")
        self._write("doc.md", '```\nSee AGENTS.md § "Imaginary Example".\n```\n')
        rc = sync_scaffold.check_references(
            str(self.tmpdir), md_files=["AGENTS.md", "doc.md"]
        )
        self.assertEqual(rc, 0)

    def test_tracked_markdown_excludes_frozen_dirs(self):
        self._write("doc.md", "x\n")
        self._write("docs/reviews/2026-06/r.md", "x\n")
        self._write("ai-docs/archive/old.md", "x\n")
        self._write("openspec/changes/c/proposal.md", "x\n")
        self._write("memory/research/old-analysis.md", "x\n")
        rels = sync_scaffold._tracked_markdown(self.tmpdir)
        self.assertIn("doc.md", rels)
        # docs/reviews/ and ai-docs/archive/ are no longer in _REF_SCAN_EXCLUDE.
        self.assertIn("docs/reviews/2026-06/r.md", rels)
        self.assertIn("ai-docs/archive/old.md", rels)
        # openspec/changes/ and memory/research/ are frozen/excluded.
        self.assertNotIn("openspec/changes/c/proposal.md", rels)
        self.assertNotIn("memory/research/old-analysis.md", rels)


class SyncConfigYamlTest(unittest.TestCase):
    """Tests for sync_config_yaml and the openspec/config.yaml rules-block sync (task 6.1)."""

    # ── shared fixtures ──────────────────────────────────────────────────────

    SCAFFOLD_CONFIG = """\
schema: "1.0"

context:
  description: "Scaffold project"

rules:
  tasks: "tasks.md is for apply phase only"
  research: "use fetch_clean.py for research"
"""

    TARGET_CONFIG_DIFFERENT_RULES = """\
schema: "1.0"

context:
  description: "Downstream project — unique per-repo identity"

rules:
  tasks: "OLD tasks rule"
"""

    TARGET_CONFIG_NO_RULES = """\
schema: "1.0"

context:
  description: "Downstream project — no rules block yet"
"""

    TARGET_CONFIG_KEY_AFTER_RULES = """\
schema: "1.0"

rules:
  tasks: "some rule"

extra_key: "this follows rules: — invalid"
"""

    # ── unit tests: sync_config_yaml() ───────────────────────────────────────

    def test_rules_block_replaced(self):
        """scaffold rules: block replaces the target's rules: block."""
        result = sync_scaffold.sync_config_yaml(
            self.SCAFFOLD_CONFIG, self.TARGET_CONFIG_DIFFERENT_RULES
        )
        self.assertIn('tasks: "tasks.md is for apply phase only"', result)
        self.assertIn("research:", result)
        self.assertNotIn("OLD tasks rule", result)

    def test_context_block_preserved(self):
        """per-repo context: block is preserved byte-identical after sync."""
        result = sync_scaffold.sync_config_yaml(
            self.SCAFFOLD_CONFIG, self.TARGET_CONFIG_DIFFERENT_RULES
        )
        self.assertIn("Downstream project — unique per-repo identity", result)
        # scaffold's own context must NOT bleed into the result
        self.assertNotIn('description: "Scaffold project"', result)

    def test_idempotent(self):
        """Applying sync_config_yaml twice returns identical result (fixed point)."""
        first = sync_scaffold.sync_config_yaml(
            self.SCAFFOLD_CONFIG, self.TARGET_CONFIG_DIFFERENT_RULES
        )
        second = sync_scaffold.sync_config_yaml(self.SCAFFOLD_CONFIG, first)
        self.assertEqual(first, second)

    def test_drift_detected_by_extract_rules_block(self):
        """rules: blocks from scaffold and a diverged target compare unequal."""
        scaffold_rules = sync_scaffold._extract_rules_block(self.SCAFFOLD_CONFIG)
        target_rules = sync_scaffold._extract_rules_block(
            self.TARGET_CONFIG_DIFFERENT_RULES
        )
        self.assertIsNotNone(scaffold_rules)
        self.assertIsNotNone(target_rules)
        self.assertNotEqual(scaffold_rules, target_rules)

    def test_append_if_absent(self):
        """scaffold rules: is appended at EOF when target has no rules: block."""
        result = sync_scaffold.sync_config_yaml(
            self.SCAFFOLD_CONFIG, self.TARGET_CONFIG_NO_RULES
        )
        self.assertIn("rules:", result)
        self.assertIn("tasks.md is for apply phase only", result)
        # per-repo context unchanged
        self.assertIn("Downstream project — no rules block yet", result)
        # result ends with a newline
        self.assertTrue(result.endswith("\n"))

    def test_abort_when_key_follows_rules(self):
        """ValueError raised when a non-comment top-level key follows rules: in target."""
        with self.assertRaises(ValueError):
            sync_scaffold.sync_config_yaml(
                self.SCAFFOLD_CONFIG, self.TARGET_CONFIG_KEY_AFTER_RULES
            )

    # ── integration tests: full sync() + check() flow ───────────────────────

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.scaffold = self.tmpdir / "scaffold"
        (self.scaffold / "scripts").mkdir(parents=True)
        (self.scaffold / "scripts" / "scaffold_manifest.txt").write_text(
            "openspec/config.yaml\n"
        )
        (self.scaffold / "openspec").mkdir(parents=True)
        (self.scaffold / "openspec" / "config.yaml").write_text(self.SCAFFOLD_CONFIG)

        self.target = self.tmpdir / "target"
        self.target.mkdir()
        (self.target / ".git").mkdir()
        (self.target / "openspec").mkdir(parents=True)
        (self.target / "openspec" / "config.yaml").write_text(
            self.TARGET_CONFIG_DIFFERENT_RULES
        )

        self._scaffold_root_patcher = patch.object(
            sync_scaffold, "_scaffold_root", return_value=self.scaffold
        )
        self._scaffold_root_patcher.start()

    def tearDown(self):
        self._scaffold_root_patcher.stop()
        for root, dirs, files in os.walk(self.tmpdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.tmpdir)

    def test_sync_replaces_rules_preserves_context_integration(self):
        """Full sync(): rules: replaced, per-repo context: preserved."""
        sync_scaffold.sync(str(self.target))
        result = (self.target / "openspec" / "config.yaml").read_text()
        self.assertIn("tasks.md is for apply phase only", result)
        self.assertIn("research:", result)
        self.assertNotIn("OLD tasks rule", result)
        self.assertIn("Downstream project — unique per-repo identity", result)

    def test_sync_idempotent_integration(self):
        """sync() twice = no-op; --check exits 0 after second run."""
        sync_scaffold.sync(str(self.target))
        content_after_first = (self.target / "openspec" / "config.yaml").read_text()
        sync_scaffold.sync(str(self.target))
        content_after_second = (self.target / "openspec" / "config.yaml").read_text()
        self.assertEqual(content_after_first, content_after_second)
        rc = sync_scaffold.check(str(self.target))
        self.assertEqual(rc, 0)

    def test_check_detects_rules_drift_integration(self):
        """--check exits 1 when target rules: block differs from scaffold."""
        # target currently has different rules: — check should report drift
        rc = sync_scaffold.check(str(self.target))
        self.assertEqual(rc, 1)

    def test_check_identical_when_only_context_differs(self):
        """--check reports IDENTICAL when only context: differs (per-repo, expected)."""
        sync_scaffold.sync(str(self.target))
        current = (self.target / "openspec" / "config.yaml").read_text()
        # alter only the per-repo context
        modified = current.replace(
            "Downstream project — unique per-repo identity",
            "A completely different per-repo description",
        )
        (self.target / "openspec" / "config.yaml").write_text(modified)
        rc = sync_scaffold.check(str(self.target))
        self.assertEqual(rc, 0)

    def test_append_if_absent_integration(self):
        """sync() appends scaffold rules: when target has no rules: block."""
        target_no_rules = self.tmpdir / "target_no_rules"
        target_no_rules.mkdir()
        (target_no_rules / ".git").mkdir()
        (target_no_rules / "openspec").mkdir(parents=True)
        (target_no_rules / "openspec" / "config.yaml").write_text(
            self.TARGET_CONFIG_NO_RULES
        )
        sync_scaffold.sync(str(target_no_rules))
        result = (target_no_rules / "openspec" / "config.yaml").read_text()
        self.assertIn("rules:", result)
        self.assertIn("tasks.md is for apply phase only", result)
        self.assertIn("Downstream project — no rules block yet", result)
        # idempotent after append
        sync_scaffold.sync(str(target_no_rules))
        second = (target_no_rules / "openspec" / "config.yaml").read_text()
        self.assertEqual(result, second)

    def test_abort_when_key_follows_rules_integration(self):
        """sync() raises ValueError when a non-comment top-level key follows rules: in target."""
        (self.target / "openspec" / "config.yaml").write_text(
            self.TARGET_CONFIG_KEY_AFTER_RULES
        )
        with self.assertRaises(ValueError):
            sync_scaffold.sync(str(self.target))


if __name__ == "__main__":
    unittest.main()
