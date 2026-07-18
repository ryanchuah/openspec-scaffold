#!/usr/bin/env python3
"""Tests for scripts/test-gate.sh's fail-safe defer branch (D3 / task 3.2).

Covers: with the git-native pre-commit hook present + executable at
core.hooksPath and a --no-verify-free genuine `git commit` classification,
test-gate.sh defers (exit 0, prints the defer notice, does NOT run
check.sh). With --no-verify (or a short -n flag) in the command, or the
hook absent/not executable, or an UNKNOWN classification, it runs check.sh
(verified via a marker-file sentinel a wired test-cmd writes only if it
actually ran, plus the BLOCKED exit code for a red test-cmd).

Reuses the workspace-builder pattern from test_gate_command_detection.py,
extended to a real git repo (the defer branch calls `git rev-parse` from
the workspace's cwd).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
TEST_GATE_SH = SCRIPTS_DIR / "test-gate.sh"
CHECK_SH = SCRIPTS_DIR / "check.sh"
PRE_COMMIT_SRC = SCRIPTS_DIR / "githooks" / "pre-commit"
RUFF_TOML = SCRIPTS_DIR.parent / "ruff.toml"

MARKER_NAME = "check_sh_ran.marker"


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=True)


def _build_workspace(tmp_path: Path, wire_hook: bool, red: bool = False) -> Path:
    """Real git repo with test-gate.sh + check.sh + a marker-writing
    test-cmd, so it's observable whether check.sh actually ran. Optionally
    wires the git-native pre-commit hook at core.hooksPath.

    The test-cmd is a standalone script (not an inline shell one-liner) —
    check.sh's test-cmd invocation is unquoted-word-split, so a single
    executable path avoids that quoting hazard entirely.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init", "-q"], repo)
    _run(["git", "config", "user.email", "test@example.com"], repo)
    _run(["git", "config", "user.name", "Test"], repo)

    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy2(str(TEST_GATE_SH), str(scripts_dir / "test-gate.sh"))
    (scripts_dir / "test-gate.sh").chmod(0o755)
    shutil.copy2(str(CHECK_SH), str(scripts_dir / "check.sh"))
    (scripts_dir / "check.sh").chmod(0o755)

    marker_path = repo / MARKER_NAME
    runner = scripts_dir / "test-runner.sh"
    runner.write_text(
        f"#!/usr/bin/env bash\ntouch {marker_path}\nexit {1 if red else 0}\n",
        encoding="utf-8",
    )
    runner.chmod(0o755)
    (scripts_dir / "test-cmd").write_text(f"{runner}\n", encoding="utf-8")

    if RUFF_TOML.exists():
        shutil.copy2(str(RUFF_TOML), str(repo / "ruff.toml"))
    (repo / "clean.py").write_text("x = 1\n", encoding="utf-8")

    if wire_hook:
        githooks_dir = scripts_dir / "githooks"
        githooks_dir.mkdir()
        shutil.copy2(str(PRE_COMMIT_SRC), str(githooks_dir / "pre-commit"))
        (githooks_dir / "pre-commit").chmod(0o755)
        _run(["git", "config", "--local", "core.hooksPath", "scripts/githooks"], repo)

    return repo


def _feed_stdin(payload: dict, workspace: Path) -> subprocess.CompletedProcess:
    gate_path = workspace / "scripts" / "test-gate.sh"
    return subprocess.run(
        [str(gate_path)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(workspace),
    )


def _marker(workspace: Path) -> Path:
    return workspace / MARKER_NAME


# ===================================================================
# Defer branch: hook active + GIT_COMMIT (no --no-verify) => defer
# ===================================================================


def test_defers_when_hook_active_and_genuine_commit(tmp_path):
    workspace = _build_workspace(tmp_path, wire_hook=True)
    payload = {"tool_input": {"command": "git commit -m msg"}}
    proc = _feed_stdin(payload, workspace)
    assert proc.returncode == 0, f"stdout:{proc.stdout}\nstderr:{proc.stderr}"
    assert "deferring" in proc.stdout, proc.stdout
    assert not _marker(workspace).exists(), "check.sh ran despite an active git-native hook"


# ===================================================================
# --no-verify (long flag or short -n cluster) => must NOT defer
# ===================================================================


def test_runs_check_sh_when_no_verify_present(tmp_path):
    workspace = _build_workspace(tmp_path, wire_hook=True)
    payload = {"tool_input": {"command": "git commit -m msg --no-verify"}}
    proc = _feed_stdin(payload, workspace)
    assert "deferring" not in proc.stdout, proc.stdout
    assert proc.returncode == 0, f"stdout:{proc.stdout}\nstderr:{proc.stderr}"
    assert _marker(workspace).exists(), "check.sh did not run despite --no-verify"


def test_runs_check_sh_when_no_verify_short_flag(tmp_path):
    """A short-flag cluster containing 'n' (e.g. -nm) also must NOT defer."""
    workspace = _build_workspace(tmp_path, wire_hook=True)
    payload = {"tool_input": {"command": "git commit -nm msg"}}
    proc = _feed_stdin(payload, workspace)
    assert "deferring" not in proc.stdout, proc.stdout
    assert _marker(workspace).exists(), "check.sh did not run despite a -n short flag"


def test_no_verify_blocks_on_red_test_cmd(tmp_path):
    """When it (correctly) does NOT defer, a red test-cmd still BLOCKS."""
    workspace = _build_workspace(tmp_path, wire_hook=True, red=True)
    payload = {"tool_input": {"command": "git commit -m msg --no-verify"}}
    proc = _feed_stdin(payload, workspace)
    assert "deferring" not in proc.stdout, proc.stdout
    assert proc.returncode == 2, f"stdout:{proc.stdout}\nstderr:{proc.stderr}"
    assert _marker(workspace).exists()


# ===================================================================
# Hook absent / not executable => must NOT defer (fail-safe fallback)
# ===================================================================


def test_runs_check_sh_when_hook_not_wired(tmp_path):
    workspace = _build_workspace(tmp_path, wire_hook=False)
    payload = {"tool_input": {"command": "git commit -m msg"}}
    proc = _feed_stdin(payload, workspace)
    assert "deferring" not in proc.stdout, proc.stdout
    assert proc.returncode == 0, f"stdout:{proc.stdout}\nstderr:{proc.stderr}"
    assert _marker(workspace).exists(), "check.sh did not run despite the hook being unwired"


def test_runs_check_sh_when_hook_not_executable(tmp_path):
    workspace = _build_workspace(tmp_path, wire_hook=True)
    (workspace / "scripts" / "githooks" / "pre-commit").chmod(0o644)
    payload = {"tool_input": {"command": "git commit -m msg"}}
    proc = _feed_stdin(payload, workspace)
    assert "deferring" not in proc.stdout, proc.stdout
    assert _marker(workspace).exists(), "check.sh did not run despite a non-executable hook"


# ===================================================================
# UNKNOWN classification (no stdin) => must NOT defer (fail-safe)
# ===================================================================


def test_runs_check_sh_when_unknown_classification(tmp_path):
    workspace = _build_workspace(tmp_path, wire_hook=True)
    gate_path = workspace / "scripts" / "test-gate.sh"
    proc = subprocess.run(
        [str(gate_path)],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(workspace),
    )
    assert "deferring" not in proc.stdout, proc.stdout
    assert _marker(workspace).exists(), "check.sh did not run under UNKNOWN classification"
