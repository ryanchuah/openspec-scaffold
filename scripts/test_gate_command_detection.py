#!/usr/bin/env python3
"""Tests for scripts/test-gate.sh hook-command detection (task 5.2, 5.3).

These tests probe the PreToolUse stdin-JSON parsing gate that determines
whether the current Bash command is a genuine `git commit` invocation.

Each test feeds test-gate.sh a synthetic JSON payload via stdin and checks
the exit code / stdout for the expected guard behavior.  Tests that verify
the guard proceeds to check.sh use a temp workspace with a trivial test-cmd
to avoid recursive test execution.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

TEST_GATE_SH = Path(__file__).resolve().parent / "test-gate.sh"
CHECK_SH = Path(__file__).resolve().parent / "check.sh"
RUFF_TOML = Path(__file__).resolve().parent.parent / "ruff.toml"

# The reproduction command from task 5.1: a non-commit Bash command that
# contains "git commit" only as a substring in an echo argument.
REPRODUCTION_CMD = 'echo "use git commit to save changes" && true'


def _build_gate_workspace(tmp_path: Path) -> Path:
    """Set up a temp workspace with test-gate.sh, check.sh, and trivial
    test-cmd so the gate can proceed without recursion."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    # Copy both gate scripts
    shutil.copy2(str(TEST_GATE_SH), str(scripts_dir / "test-gate.sh"))
    (scripts_dir / "test-gate.sh").chmod(0o755)
    shutil.copy2(str(CHECK_SH), str(scripts_dir / "check.sh"))
    (scripts_dir / "check.sh").chmod(0o755)
    # Trivial test command (avoids recursive pytest execution)
    (scripts_dir / "test-cmd").write_text("true\n")
    # Copy ruff.toml so check.sh's lint/format stages work
    if RUFF_TOML.exists():
        shutil.copy2(str(RUFF_TOML), tmp_path / "ruff.toml")
    # Create an empty Python file so ruff format --check doesn't error
    (tmp_path / "__init__.py").write_text("# workspace\n")
    return tmp_path


def _feed_stdin(payload: dict, workspace: Path | None = None) -> subprocess.CompletedProcess:
    """Run test-gate.sh with *payload* as stdin JSON.

    If *workspace* is None, run the real repo's test-gate.sh (only safe for
    tests where the guard exits early).  Otherwise use the workspace copy.
    """
    gate_path = workspace / "scripts" / "test-gate.sh" if workspace else TEST_GATE_SH
    return subprocess.run(
        [str(gate_path)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(workspace) if workspace else None,
    )


# ===================================================================
# Guard: NOT_GIT_COMMIT — must exit 0 and skip the gate entirely
# ===================================================================


def test_non_commit_substring_exits_0():
    """A non-commit command containing 'git commit' as substring => exit 0."""
    payload = {"tool_input": {"command": REPRODUCTION_CMD}}
    proc = _feed_stdin(payload)
    # Must exit 0 (no-op) without running checks
    assert proc.returncode == 0, (
        f"Expected 0, got {proc.returncode}\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert "not a genuine 'git commit'" in proc.stdout, proc.stdout
    assert "skipping gate" in proc.stdout, proc.stdout


def test_git_log_not_gated():
    """A non-commit git command (e.g. 'git log') does NOT trigger the gate."""
    payload = {"tool_input": {"command": "git log --oneline"}}
    proc = _feed_stdin(payload)
    assert proc.returncode == 0, (
        f"Expected 0, got {proc.returncode}\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert "not a genuine 'git commit'" in proc.stdout, proc.stdout


def test_git_cherry_pick_not_gated():
    """'git cherry-pick' (contains 'pick' not 'commit') does NOT trigger."""
    payload = {"tool_input": {"command": "git cherry-pick abc123"}}
    proc = _feed_stdin(payload)
    assert proc.returncode == 0
    assert "not a genuine 'git commit'" in proc.stdout, proc.stdout


# ===================================================================
# Guard: GIT_COMMIT — must proceed to check.sh delegation
# ===================================================================


def test_genuine_git_commit_proceeds_to_gate(tmp_path):
    """A genuine 'git commit' invocation proceeds past the guard to check.sh."""
    workspace = _build_gate_workspace(tmp_path)
    payload = {"tool_input": {"command": 'git commit -m "test message"'}}
    proc = _feed_stdin(payload, workspace)
    # Guard must not block
    assert "not a genuine 'git commit'" not in proc.stdout, proc.stdout
    # Must proceed to check.sh and pass (trivial test-cmd is "true")
    assert "all checks passed" in proc.stdout, (
        f"Expected checks to pass\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert proc.returncode == 0


def test_git_commit_amend_detected(tmp_path):
    """'git commit --amend' IS a genuine git commit and passes the guard."""
    workspace = _build_gate_workspace(tmp_path)
    payload = {"tool_input": {"command": "git commit --amend"}}
    proc = _feed_stdin(payload, workspace)
    assert "not a genuine 'git commit'" not in proc.stdout, proc.stdout
    assert "all checks passed" in proc.stdout


def test_git_commit_with_env_var_detected(tmp_path):
    """'VAR=val git commit -m' IS genuine and passes the guard."""
    workspace = _build_gate_workspace(tmp_path)
    payload = {"tool_input": {"command": "GIT_AUTHOR_DATE='2020-01-01' git commit -m 'msg'"}}
    proc = _feed_stdin(payload, workspace)
    assert "not a genuine 'git commit'" not in proc.stdout, proc.stdout
    assert "all checks passed" in proc.stdout


def test_git_with_global_opts_commit_detected(tmp_path):
    """'git -c key=val commit -m msg' IS genuine."""
    workspace = _build_gate_workspace(tmp_path)
    payload = {"tool_input": {"command": "git -c user.name='X' commit -m 'msg'"}}
    proc = _feed_stdin(payload, workspace)
    assert "not a genuine 'git commit'" not in proc.stdout, proc.stdout
    assert "all checks passed" in proc.stdout


# ===================================================================
# Guard: UNKNOWN (fail-safe) — proceeds if no stdin / unparseable
# ===================================================================


def test_no_stdin_fallback_runs_gate(tmp_path):
    """No stdin (direct invocation) => UNKNOWN => proceeds to check.sh."""
    workspace = _build_gate_workspace(tmp_path)
    gate_copy = workspace / "scripts" / "test-gate.sh"

    # Run without any stdin — the select timeout will produce UNKNOWN
    proc = subprocess.run(
        [str(gate_copy)],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(workspace),
    )
    # The guard should NOT block (UNKNOWN fallback)
    assert "not a genuine 'git commit'" not in proc.stdout, proc.stdout
    # Should proceed to check.sh and pass
    assert "all checks passed" in proc.stdout, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    assert proc.returncode == 0
