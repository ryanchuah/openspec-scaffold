"""Adversarial / boundary fixtures for apply_delta_spec.py — orchestrator-authored
at verify (an independent second source per config.yaml rules.verify + the change's
proposal.md). Deliberately does NOT reuse the executor-authored test helpers, so this
suite is an independent check rather than a mirror of the implementation's own tests.

Property/invariant style (not output-pinning): asserts semantics, atomicity, formatting
invariants (no triple-blank runs), idempotency, and structural ordering.
"""

from __future__ import annotations

import io
import json
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import apply_delta_spec  # noqa: E402


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run(change_dir: Path, specs_root: Path, *, dry_run: bool = False):
    """Run the promoter, returning (exit_code, json_report)."""
    argv = ["--change-dir", str(change_dir), "--specs-root", str(specs_root), "--json"]
    if dry_run:
        argv.append("--dry-run")
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = apply_delta_spec.main(argv)
    out = buf.getvalue()
    try:
        report = json.loads(out)
    except json.JSONDecodeError:
        report = None
    return code, report


def _spec_for(report, capability):
    for s in report["specs"]:
        if s["capability"] == capability:
            return s
    return None


MAIN_TWO_REQ = """\
## Purpose

Demo capability.

## Requirements

### Requirement: Keep me
The system SHALL keep this.

#### Scenario: keeps
- **WHEN** x
- **THEN** y

### Requirement: Drop me
The system SHALL drop this.

#### Scenario: drops
- **WHEN** a
- **THEN** b
"""


# ---------------------------------------------------------------------------
# Atomicity — a single anomaly blocks the whole change; nothing is written.
# ---------------------------------------------------------------------------


def test_atomicity_mixed_clean_and_anomaly_writes_nothing(tmp_path):
    specs = tmp_path / "specs"
    _write(specs / "demo" / "spec.md", MAIN_TWO_REQ)
    before = (specs / "demo" / "spec.md").read_text()
    change = tmp_path / "change"
    # One clean ADDED (new name) + one anomalous ADDED (existing name, different body).
    _write(
        change / "specs" / "demo" / "spec.md",
        "## ADDED Requirements\n\n"
        "### Requirement: Brand new\nThe system SHALL be new.\n\n"
        "#### Scenario: new\n- **WHEN** n\n- **THEN** m\n\n"
        "### Requirement: Keep me\nThe system SHALL keep this DIFFERENTLY.\n\n"
        "#### Scenario: keeps\n- **WHEN** x\n- **THEN** z\n",
    )
    code, report = _run(change, specs)
    assert code == 2
    assert report["status"] == "anomaly"
    # Nothing written — main spec byte-identical.
    assert (specs / "demo" / "spec.md").read_text() == before


# ---------------------------------------------------------------------------
# Intra-delta self-collision (D4 note).
# ---------------------------------------------------------------------------


def test_intra_delta_self_collision_differing_bodies_is_anomaly(tmp_path):
    specs = tmp_path / "specs"
    change = tmp_path / "change"
    _write(
        change / "specs" / "demo" / "spec.md",
        "## ADDED Requirements\n\n"
        "### Requirement: Twin\nThe system SHALL twin one way.\n\n"
        "#### Scenario: a\n- **WHEN** a\n- **THEN** b\n\n"
        "### Requirement: Twin\nThe system SHALL twin ANOTHER way.\n\n"
        "#### Scenario: c\n- **WHEN** c\n- **THEN** d\n",
    )
    code, report = _run(change, specs)
    assert code == 2
    assert not (specs / "demo" / "spec.md").exists()


def test_intra_delta_self_collision_identical_is_skip(tmp_path):
    specs = tmp_path / "specs"
    change = tmp_path / "change"
    block = (
        "### Requirement: Twin\nThe system SHALL twin.\n\n"
        "#### Scenario: a\n- **WHEN** a\n- **THEN** b\n"
    )
    _write(change / "specs" / "demo" / "spec.md", f"## ADDED Requirements\n\n{block}\n{block}")
    code, report = _run(change, specs)
    assert code == 0
    s = _spec_for(report, "demo")
    assert "Twin" in s["applied"]["added"]
    assert any(k["name"] == "Twin" for k in s["skipped"])


# ---------------------------------------------------------------------------
# RENAMED + MODIFIED on the same requirement in one delta (D8 ordering).
# ---------------------------------------------------------------------------


def test_renamed_plus_modified_combo(tmp_path):
    specs = tmp_path / "specs"
    _write(specs / "demo" / "spec.md", MAIN_TWO_REQ)
    change = tmp_path / "change"
    _write(
        change / "specs" / "demo" / "spec.md",
        "## RENAMED Requirements\n"
        "- FROM: `### Requirement: Keep me`\n"
        "- TO: `### Requirement: Kept me`\n\n"
        "## MODIFIED Requirements\n\n"
        "### Requirement: Kept me\nThe system SHALL keep this.\n\n"
        "#### Scenario: another\n- **WHEN** q\n- **THEN** r\n",
    )
    code, report = _run(change, specs)
    assert code == 0
    s = _spec_for(report, "demo")
    assert ["Keep me", "Kept me"] in s["applied"]["renamed"]
    assert "Kept me" in s["deferred_modified"]
    text = (specs / "demo" / "spec.md").read_text()
    assert "### Requirement: Kept me" in text
    assert "### Requirement: Keep me" not in text


# ---------------------------------------------------------------------------
# Main spec with only `## Purpose` (no `## Requirements`) — D9.
# ---------------------------------------------------------------------------

ONLY_PURPOSE = "## Purpose\n\nJust a purpose, no requirements yet.\n"


def test_only_purpose_removed_is_skip(tmp_path):
    specs = tmp_path / "specs"
    _write(specs / "demo" / "spec.md", ONLY_PURPOSE)
    change = tmp_path / "change"
    _write(
        change / "specs" / "demo" / "spec.md",
        "## REMOVED Requirements\n\n### Requirement: Ghost\n",
    )
    code, report = _run(change, specs)
    assert code == 0
    s = _spec_for(report, "demo")
    assert any(k["op"] == "REMOVED" and k["name"] == "Ghost" for k in s["skipped"])


def test_only_purpose_renamed_is_anomaly(tmp_path):
    specs = tmp_path / "specs"
    _write(specs / "demo" / "spec.md", ONLY_PURPOSE)
    change = tmp_path / "change"
    _write(
        change / "specs" / "demo" / "spec.md",
        "## RENAMED Requirements\n"
        "- FROM: `### Requirement: Ghost`\n"
        "- TO: `### Requirement: Spectre`\n",
    )
    code, _ = _run(change, specs)
    assert code == 2


def test_only_purpose_added_inserts_requirements_header(tmp_path):
    specs = tmp_path / "specs"
    _write(specs / "demo" / "spec.md", ONLY_PURPOSE)
    change = tmp_path / "change"
    _write(
        change / "specs" / "demo" / "spec.md",
        "## ADDED Requirements\n\n"
        "### Requirement: Fresh\nThe system SHALL be fresh.\n\n"
        "#### Scenario: f\n- **WHEN** f\n- **THEN** g\n",
    )
    code, _ = _run(change, specs)
    assert code == 0
    text = (specs / "demo" / "spec.md").read_text()
    assert "## Requirements" in text
    assert "### Requirement: Fresh" in text
    assert "## Purpose" in text


# ---------------------------------------------------------------------------
# Degenerate deltas — clean no-op, no crash.
# ---------------------------------------------------------------------------


def test_empty_section_delta_is_noop(tmp_path):
    specs = tmp_path / "specs"
    change = tmp_path / "change"
    _write(change / "specs" / "demo" / "spec.md", "## ADDED Requirements\n\n")
    code, report = _run(change, specs)
    assert code == 0
    assert not (specs / "demo" / "spec.md").exists()


def test_no_section_delta_is_noop(tmp_path):
    specs = tmp_path / "specs"
    change = tmp_path / "change"
    _write(
        change / "specs" / "demo" / "spec.md", "# Delta title\n\nSome intro prose, no sections.\n"
    )
    code, report = _run(change, specs)
    assert code == 0


# ---------------------------------------------------------------------------
# REMOVED / RENAMED targeting a capability with no main spec file — D9 anomaly.
# ---------------------------------------------------------------------------


def test_removed_on_nonexistent_spec_is_anomaly(tmp_path):
    specs = tmp_path / "specs"
    change = tmp_path / "change"
    _write(
        change / "specs" / "ghostcap" / "spec.md",
        "## REMOVED Requirements\n\n### Requirement: X\n",
    )
    code, _ = _run(change, specs)
    assert code == 2


def test_renamed_on_nonexistent_spec_is_anomaly(tmp_path):
    specs = tmp_path / "specs"
    change = tmp_path / "change"
    _write(
        change / "specs" / "ghostcap" / "spec.md",
        "## RENAMED Requirements\n- FROM: `### Requirement: X`\n- TO: `### Requirement: Y`\n",
    )
    code, _ = _run(change, specs)
    assert code == 2


# ---------------------------------------------------------------------------
# Dry-run never writes.
# ---------------------------------------------------------------------------


def test_dry_run_clean_writes_nothing(tmp_path):
    specs = tmp_path / "specs"
    _write(specs / "demo" / "spec.md", MAIN_TWO_REQ)
    before = (specs / "demo" / "spec.md").read_text()
    change = tmp_path / "change"
    _write(
        change / "specs" / "demo" / "spec.md",
        "## ADDED Requirements\n\n### Requirement: New\nThe system SHALL add.\n\n"
        "#### Scenario: n\n- **WHEN** n\n- **THEN** m\n",
    )
    code, report = _run(change, specs, dry_run=True)
    assert code == 0
    assert "New" in _spec_for(report, "demo")["applied"]["added"]
    assert (specs / "demo" / "spec.md").read_text() == before  # unchanged


# ---------------------------------------------------------------------------
# Formatting invariants — the deterministic promoter must produce CLEAN specs.
# ---------------------------------------------------------------------------


def test_no_triple_blank_run_after_promotion(tmp_path):
    """Promoting must not introduce >1 consecutive blank line."""
    specs = tmp_path / "specs"
    _write(specs / "demo" / "spec.md", MAIN_TWO_REQ)
    change = tmp_path / "change"
    _write(
        change / "specs" / "demo" / "spec.md",
        "## REMOVED Requirements\n\n### Requirement: Drop me\n",
    )
    code, _ = _run(change, specs)
    assert code == 0
    text = (specs / "demo" / "spec.md").read_text()
    assert "\n\n\n" not in text, f"triple blank introduced:\n{text!r}"


def test_surviving_requirement_body_preserved(tmp_path):
    specs = tmp_path / "specs"
    _write(specs / "demo" / "spec.md", MAIN_TWO_REQ)
    change = tmp_path / "change"
    _write(
        change / "specs" / "demo" / "spec.md",
        "## REMOVED Requirements\n\n### Requirement: Drop me\n",
    )
    code, _ = _run(change, specs)
    assert code == 0
    text = (specs / "demo" / "spec.md").read_text()
    assert "### Requirement: Keep me" in text
    assert "The system SHALL keep this." in text
    assert "#### Scenario: keeps" in text
    assert "### Requirement: Drop me" not in text


def test_promote_twice_is_idempotent(tmp_path):
    """A second promotion (now all-skips) leaves the file byte-identical."""
    specs = tmp_path / "specs"
    _write(specs / "demo" / "spec.md", MAIN_TWO_REQ)
    change = tmp_path / "change"
    _write(
        change / "specs" / "demo" / "spec.md",
        "## REMOVED Requirements\n\n### Requirement: Drop me\n",
    )
    code1, _ = _run(change, specs)
    assert code1 == 0
    after_first = (specs / "demo" / "spec.md").read_text()
    # The first promotion must actually have done the work (not a spurious no-op).
    assert "### Requirement: Drop me" not in after_first
    code2, _ = _run(change, specs)
    assert code2 == 0
    after_second = (specs / "demo" / "spec.md").read_text()
    assert after_first == after_second


def test_trailing_section_preserved_after_requirements(tmp_path):
    """A `## ` section that follows the requirements must NOT be reordered ahead of them."""
    main = MAIN_TWO_REQ + "\n## Notes\n\nA trailing note that must stay last.\n"
    specs = tmp_path / "specs"
    _write(specs / "demo" / "spec.md", main)
    change = tmp_path / "change"
    _write(
        change / "specs" / "demo" / "spec.md",
        "## REMOVED Requirements\n\n### Requirement: Drop me\n",
    )
    code, _ = _run(change, specs)
    assert code == 0
    text = (specs / "demo" / "spec.md").read_text()
    assert "## Notes" in text and "A trailing note that must stay last." in text
    # The Notes section must appear AFTER the surviving requirement, not before it.
    assert text.index("### Requirement: Keep me") < text.index("## Notes")
