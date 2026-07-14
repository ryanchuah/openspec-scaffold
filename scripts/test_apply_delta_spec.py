#!/usr/bin/env python3
"""Tests for apply_delta_spec.py — core contract suite.

Covers every D4 truth-table row, MODIFIED deferred-not-applied, --dry-run,
JSON report shape, new-main-spec creation, and the regex-agreement test.

The orchestrator adds independent adversarial/boundary fixtures at verify
(atomicity, intra-delta self-collision, RENAMED+MODIFIED combo ordering,
empty/degenerate deltas, only-##Purpose main spec, and RENAMED-debut edges).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import apply_delta_spec  # noqa: E402
import checks  # noqa: E402

# ===================================================================
# Helpers
# ===================================================================


def _main(
    root: Path, change_name: str = "my-change", extra: list[str] | None = None
) -> tuple[int, str]:
    """Run apply_delta_spec.main() against a fixture under *root*.

    Writes change-dir delta specs and main specs under *root* before calling.
    Returns (exit_code, captured_stdout).
    """
    import io
    from contextlib import redirect_stdout

    change_dir = root / "changes" / change_name
    specs_root = root / "specs"
    argv = [
        "--change-dir",
        str(change_dir),
        "--specs-root",
        str(specs_root),
    ]
    if extra:
        argv.extend(extra)

    out_buf = io.StringIO()
    with redirect_stdout(out_buf):
        rc = apply_delta_spec.main(argv)
    return rc, out_buf.getvalue()


def _main_json(
    root: Path, change_name: str = "my-change", extra: list[str] | None = None
) -> tuple[int, dict]:
    """Run with --json, return (exit_code, parsed_report_dict)."""
    extra = list(extra or []) + ["--json"]
    rc, out = _main(root, change_name, extra=extra)
    return rc, json.loads(out)


def _write_main_spec(specs_root: Path, capability: str, body: str) -> None:
    """Write a main spec file."""
    cap_dir = specs_root / capability
    cap_dir.mkdir(parents=True, exist_ok=True)
    (cap_dir / "spec.md").write_text(body)


def _write_delta(change_dir: Path, capability: str, body: str) -> None:
    """Write a delta spec file."""
    delta_dir = change_dir / "specs" / capability
    delta_dir.mkdir(parents=True, exist_ok=True)
    (delta_dir / "spec.md").write_text(body)


# ===================================================================
# Fixture helpers
# ===================================================================


SIMPLE_MAIN_SPEC = """\
## Purpose

Some purpose text.
## Requirements
### Requirement: existing-req

Some existing requirement body.

#### Scenario: existing-scenario
- **WHEN** something
- **THEN** something
"""


ADDED_DELTA = """\
## ADDED Requirements

### Requirement: new-requirement

A newly added requirement.

#### Scenario: new-scenario
- **WHEN** we add it
- **THEN** it appears
"""


# ===================================================================
# D4 — ADDED
# ===================================================================


class TestAdded:
    """ADDED: apply / skip (body-equal) / anomaly (body differs)."""

    def test_added_apply(self, tmp_path: Path) -> None:
        """ADDED absent → apply."""
        _write_main_spec(tmp_path / "specs", "my-cap", SIMPLE_MAIN_SPEC)
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", ADDED_DELTA)

        rc, out = _main(tmp_path)
        assert rc == 0
        assert "APPLIED" in out
        assert "added: new-requirement" in out

        # Verify the main spec was actually written
        spec_text = (tmp_path / "specs" / "my-cap" / "spec.md").read_text()
        assert "new-requirement" in spec_text

    def test_added_skip_body_equal(self, tmp_path: Path) -> None:
        """ADDED present with equal body → skip."""
        # Main spec already has the requirement with the same body
        main_body = (
            SIMPLE_MAIN_SPEC
            + """
### Requirement: new-requirement

A newly added requirement.

#### Scenario: new-scenario
- **WHEN** we add it
- **THEN** it appears
"""
        )
        _write_main_spec(tmp_path / "specs", "my-cap", main_body)
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", ADDED_DELTA)

        rc, out = _main(tmp_path)
        assert rc == 0
        assert "SKIPPED" in out
        assert "body-equal" in out

    def test_added_anomaly_body_differs(self, tmp_path: Path) -> None:
        """ADDED present with different body → anomaly."""
        # Main spec already has the requirement with a different body
        main_body = (
            SIMPLE_MAIN_SPEC
            + """
### Requirement: new-requirement

A different existing requirement body.
"""
        )
        _write_main_spec(tmp_path / "specs", "my-cap", main_body)
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", ADDED_DELTA)

        rc, out = _main(tmp_path)
        assert rc == 2
        assert "ANOMALY" in out
        assert "present with different body" in out


# ===================================================================
# D4 — REMOVED
# ===================================================================


class TestRemoved:
    """REMOVED: apply / skip (target-absent)."""

    REMOVED_DELTA = """\
## REMOVED Requirements

### Requirement: existing-req
"""

    def test_removed_apply(self, tmp_path: Path) -> None:
        """REMOVED present → apply."""
        _write_main_spec(tmp_path / "specs", "my-cap", SIMPLE_MAIN_SPEC)
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", self.REMOVED_DELTA)

        rc, out = _main(tmp_path)
        assert rc == 0
        assert "APPLIED" in out
        assert "removed: existing-req" in out

        spec_text = (tmp_path / "specs" / "my-cap" / "spec.md").read_text()
        assert "existing-req" not in spec_text

    def test_removed_skip_target_absent(self, tmp_path: Path) -> None:
        """REMOVED absent → skip."""
        _write_main_spec(tmp_path / "specs", "my-cap", SIMPLE_MAIN_SPEC)
        # Try to remove something that doesn't exist
        delta = """\
## REMOVED Requirements

### Requirement: nonexistent-req
"""
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", delta)

        rc, out = _main(tmp_path)
        assert rc == 0
        assert "SKIPPED" in out
        assert "target-absent" in out


# ===================================================================
# D4 — RENAMED
# ===================================================================


class TestRenamed:
    """RENAMED: apply / skip (already-renamed) / anomaly×2 (neither, both)."""

    RENAMED_DELTA = """\
## RENAMED Requirements
- FROM: `### Requirement: existing-req`
- TO: `### Requirement: renamed-req`
"""

    def test_renamed_apply(self, tmp_path: Path) -> None:
        """RENAMED from present, to absent → apply."""
        _write_main_spec(tmp_path / "specs", "my-cap", SIMPLE_MAIN_SPEC)
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", self.RENAMED_DELTA)

        rc, out = _main(tmp_path)
        assert rc == 0
        assert "APPLIED" in out
        assert "existing-req" in out
        assert "renamed-req" in out

        spec_text = (tmp_path / "specs" / "my-cap" / "spec.md").read_text()
        assert "### Requirement: renamed-req" in spec_text
        assert "### Requirement: existing-req" not in spec_text

    def test_renamed_skip_already(self, tmp_path: Path) -> None:
        """RENAMED from absent, to present → skip (already-renamed)."""
        # Main spec has renamed-req but NOT existing-req (FROM absent = already renamed)
        main_body = """\
## Purpose

Some purpose text.
## Requirements
### Requirement: renamed-req

Some renamed content.
"""
        _write_main_spec(tmp_path / "specs", "my-cap", main_body)
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", self.RENAMED_DELTA)

        rc, out = _main(tmp_path)
        assert rc == 0
        assert "SKIPPED" in out
        assert "already-renamed" in out

    def test_renamed_anomaly_neither(self, tmp_path: Path) -> None:
        """RENAMED both absent → anomaly."""
        _write_main_spec(tmp_path / "specs", "my-cap", SIMPLE_MAIN_SPEC)
        # Neither existing-req nor renamed-req exists — wait, existing-req does exist
        # in SIMPLE_MAIN_SPEC. Let me use names that don't exist.
        delta = """\
## RENAMED Requirements
- FROM: `### Requirement: never-existed-a`
- TO: `### Requirement: never-existed-b`
"""
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", delta)

        rc, out = _main(tmp_path)
        assert rc == 2
        assert "ANOMALY" in out
        assert "rename source does not exist" in out

    def test_renamed_anomaly_both_present(self, tmp_path: Path) -> None:
        """RENAMED both present → anomaly."""
        main_body = (
            SIMPLE_MAIN_SPEC
            + """
### Requirement: first-req

First requirement.

### Requirement: second-req

Second requirement.
"""
        )
        _write_main_spec(tmp_path / "specs", "my-cap", main_body)
        delta = """\
## RENAMED Requirements
- FROM: `### Requirement: first-req`
- TO: `### Requirement: second-req`
"""
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", delta)

        rc, out = _main(tmp_path)
        assert rc == 2
        assert "ANOMALY" in out
        assert "rename target already exists" in out


# ===================================================================
# D4 — MODIFIED deferred (never applied)
# ===================================================================


class TestModified:
    """MODIFIED is deferred, never applied deterministically."""

    MODIFIED_DELTA = """\
## MODIFIED Requirements

### Requirement: existing-req

Modified body.

#### Scenario: new-modified-scenario
- **WHEN** modified
- **THEN** unchanged in main
"""

    def test_modified_deferred(self, tmp_path: Path) -> None:
        """MODIFIED → reported as deferred, not written to main."""
        _write_main_spec(tmp_path / "specs", "my-cap", SIMPLE_MAIN_SPEC)
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", self.MODIFIED_DELTA)

        rc, out = _main(tmp_path)
        assert rc == 0
        assert "DEFERRED" in out
        assert "existing-req" in out

        # Main spec unchanged
        spec_text = (tmp_path / "specs" / "my-cap" / "spec.md").read_text()
        assert "Modified body" not in spec_text

    def test_modified_not_in_applied(self, tmp_path: Path) -> None:
        """MODIFIED blocks do not appear in applied or anomalies."""
        _write_main_spec(tmp_path / "specs", "my-cap", SIMPLE_MAIN_SPEC)
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", self.MODIFIED_DELTA)

        rc, report = _main_json(tmp_path)
        assert rc == 0
        assert report["status"] == "ok"
        spec_report = report["specs"][0]
        assert "existing-req" in spec_report["deferred_modified"]
        assert spec_report["applied"]["added"] == []
        assert spec_report["applied"]["removed"] == []
        assert spec_report["applied"]["renamed"] == []
        assert spec_report["anomalies"] == []


# ===================================================================
# --dry-run
# ===================================================================


class TestDryRun:
    """--dry-run plans and reports but writes nothing."""

    def test_dry_run_writes_nothing(self, tmp_path: Path) -> None:
        """--dry-run: reports plan, exits same code, but main spec unchanged."""
        _write_main_spec(tmp_path / "specs", "my-cap", SIMPLE_MAIN_SPEC)
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", ADDED_DELTA)

        # Capture original content
        orig = (tmp_path / "specs" / "my-cap" / "spec.md").read_text()

        rc, out = _main(tmp_path, extra=["--dry-run"])
        assert rc == 0
        assert "APPLIED" in out

        # Main spec unchanged
        assert (tmp_path / "specs" / "my-cap" / "spec.md").read_text() == orig


# ===================================================================
# JSON report shape
# ===================================================================


class TestJsonReport:
    """JSON report shape + status/exit-code agreement."""

    def test_json_clean_ok(self, tmp_path: Path) -> None:
        """Clean apply: status=ok, exit 0."""
        _write_main_spec(tmp_path / "specs", "my-cap", SIMPLE_MAIN_SPEC)
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", ADDED_DELTA)

        rc, report = _main_json(tmp_path)
        assert rc == 0
        assert report["status"] == "ok"
        assert len(report["specs"]) == 1
        s = report["specs"][0]
        assert s["capability"] == "my-cap"
        assert s["applied"]["added"] == ["new-requirement"]

    def test_json_anomaly_exit_2(self, tmp_path: Path) -> None:
        """Anomaly: status=anomaly, exit 2."""
        main_body = (
            SIMPLE_MAIN_SPEC
            + """
### Requirement: new-requirement

A different body.
"""
        )
        _write_main_spec(tmp_path / "specs", "my-cap", main_body)
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", ADDED_DELTA)

        rc, report = _main_json(tmp_path)
        assert rc == 2
        assert report["status"] == "anomaly"
        assert len(report["specs"][0]["anomalies"]) > 0

    def test_json_skip_records_skipped(self, tmp_path: Path) -> None:
        """Clean skip includes skipped entry."""
        main_body = (
            SIMPLE_MAIN_SPEC
            + """
### Requirement: new-requirement

A newly added requirement.

#### Scenario: new-scenario
- **WHEN** we add it
- **THEN** it appears
"""
        )
        _write_main_spec(tmp_path / "specs", "my-cap", main_body)
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", ADDED_DELTA)

        rc, report = _main_json(tmp_path)
        assert rc == 0
        assert len(report["specs"][0]["skipped"]) > 0
        assert report["specs"][0]["skipped"][0]["reason"] == "body-equal"


# ===================================================================
# New-main-spec creation (D9)
# ===================================================================


class TestNewMainSpec:
    """ADDED requirement on a capability with no main spec → created."""

    def test_new_main_spec_created(self, tmp_path: Path) -> None:
        """ADDED-only delta for a new capability creates the main spec."""
        _write_delta(tmp_path / "changes" / "my-change", "new-cap", ADDED_DELTA)

        rc, out = _main(tmp_path)
        assert rc == 0
        assert "APPLIED" in out

        spec_text = (tmp_path / "specs" / "new-cap" / "spec.md").read_text()
        assert "## Purpose" in spec_text
        assert "## Requirements" in spec_text
        assert "new-requirement" in spec_text


# ===================================================================
# Regex agreement test (D2)
# ===================================================================


class TestRegexAgreement:
    """Pattern strings match the checks.py originals verbatim."""

    def test_section_header_re(self) -> None:
        assert apply_delta_spec._SECTION_HEADER_RE.pattern == checks._SECTION_HEADER_RE.pattern

    def test_requirement_header_re(self) -> None:
        assert (
            apply_delta_spec._REQUIREMENT_HEADER_RE.pattern == checks._REQUIREMENT_HEADER_RE.pattern
        )

    def test_scenario_header_re(self) -> None:
        assert apply_delta_spec._SCENARIO_HEADER_RE.pattern == checks._SCENARIO_HEADER_RE.pattern


# ===================================================================
# No-op / degenerate deltas (basic — orchestrator adds deeper at verify)
# ===================================================================


class TestDegenerate:
    """Empty / degenerate deltas are clean no-ops."""

    def test_no_delta_specs(self, tmp_path: Path) -> None:
        """No specs dir → clean no-op, exit 0."""
        change_dir = tmp_path / "changes" / "my-change"
        change_dir.mkdir(parents=True, exist_ok=True)

        rc, out = _main(tmp_path)
        assert rc == 0
        assert "no operations" in out

    def test_empty_specs_dir(self, tmp_path: Path) -> None:
        """Empty specs dir → clean no-op, exit 0."""
        delta_dir = tmp_path / "changes" / "my-change" / "specs"
        delta_dir.mkdir(parents=True, exist_ok=True)

        rc, out = _main(tmp_path)
        assert rc == 0

    def test_empty_delta_section(self, tmp_path: Path) -> None:
        """A section header with no blocks is a clean no-op."""
        _write_main_spec(tmp_path / "specs", "my-cap", SIMPLE_MAIN_SPEC)
        _write_delta(tmp_path / "changes" / "my-change", "my-cap", "## ADDED Requirements\n")

        rc, out = _main(tmp_path)
        assert rc == 0
        assert "no operations" in out
