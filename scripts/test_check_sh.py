#!/usr/bin/env python3
"""Tests for scripts/check.sh — pytest style, tmp-workspace fixtures.

Each test creates a synthetic repo-like tree under pytest's tmp_path,
copies the real check.sh into it, and invokes it via subprocess.
No dependency on the real repo tree (beyond the check.sh source itself).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

# ===================================================================
# Fixtures
# ===================================================================

CHECK_SH_SRC = Path(__file__).resolve().parent / "check.sh"
RUFF_TOML_CLEAN = """\
line-length = 100

[lint]
select = ["E", "F", "I", "B"]
ignore = ["E501"]
"""


def _write_tree(root: Path, files: dict[str, str]) -> None:
    for relpath, content in files.items():
        full = root / relpath
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")


def _build_workspace(
    tmp_path: Path,
    test_cmd: str = "true\n",
    extra_files: dict[str, str] | None = None,
    ruff_toml: str = RUFF_TOML_CLEAN,
) -> Path:
    """Create a minimal workspace with check.sh, ruff.toml, and test-cmd."""
    files: dict[str, str] = {
        "ruff.toml": ruff_toml,
        "scripts/test-cmd": test_cmd,
    }
    if extra_files:
        files.update(extra_files)
    _write_tree(tmp_path, files)

    # Copy check.sh into scripts/
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(CHECK_SH_SRC), str(scripts_dir / "check.sh"))
    (scripts_dir / "check.sh").chmod(0o755)

    return tmp_path


def _run_check(workspace: Path, extra_env: dict[str, str] | None = None):
    """Run check.sh from *workspace* and return (returncode, stdout, stderr)."""
    check_sh = workspace / "scripts" / "check.sh"
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        [str(check_sh)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(workspace),
    )
    return result.returncode, result.stdout, result.stderr


def _env_without_ruff() -> dict[str, str]:
    """Return env dict with ruff removed from PATH (if present).

    Drops EVERY PATH entry that carries a ruff executable, not just the first
    `shutil.which` hit: a machine can have ruff in several dirs at once (e.g. a
    project `.venv/bin` AND a user `~/.local/bin`), and scrubbing only one leaves
    check.sh able to find the other — defeating the 'ruff absent' simulation.
    """
    old_path = os.environ.get("PATH", "")
    entries = [p for p in old_path.split(":") if p]
    kept = [p for p in entries if not shutil.which("ruff", path=p)]
    if len(kept) == len(entries):
        return {}  # ruff not on PATH anywhere → nothing to scrub
    return {"PATH": ":".join(kept)}


# ===================================================================
# Branch: clean tree => exit 0
# ===================================================================


def test_clean_tree_exit_0(tmp_path):
    """A tree with no lint/format violations and a passing test-cmd => 0."""
    workspace = _build_workspace(
        tmp_path,
        extra_files={
            "foo.py": "x = 1\n",
        },
    )
    rc, stdout, stderr = _run_check(workspace)
    assert rc == 0, f"Expected 0, got {rc}\nstdout:{stdout}\nstderr:{stderr}"
    assert "all checks passed" in stdout, stdout


# ===================================================================
# Branch: lint violation => non-zero
# ===================================================================


def test_lint_violation_exit_nonzero(tmp_path):
    """An unused import (F401) causes check.sh to exit non-zero."""
    workspace = _build_workspace(
        tmp_path,
        extra_files={
            "foo.py": "import os\nx = 1\n",
        },
    )
    rc, stdout, stderr = _run_check(workspace)
    assert rc != 0, f"Expected non-zero, got {rc}\nstdout:{stdout}\nstderr:{stderr}"
    assert "ruff check failed" in stderr, stderr


# ===================================================================
# Branch: format drift => non-zero
# ===================================================================


def test_format_drift_exit_nonzero(tmp_path):
    """A file that passes ruff check but ruff format would change => non-zero."""
    # This expression is syntactically fine and triggers no E/F/I/B lint,
    # but ruff format will reflow it (removing the unnecessary parentheses).
    workspace = _build_workspace(
        tmp_path,
        extra_files={
            "foo.py": "x = (1\n     + 2)\n",
        },
    )
    rc, stdout, stderr = _run_check(workspace)
    assert rc != 0, f"Expected non-zero, got {rc}\nstdout:{stdout}\nstderr:{stderr}"
    assert "ruff format --check failed" in stderr, stderr


# ===================================================================
# Branch: failing test-cmd => non-zero
# ===================================================================


def test_failing_test_cmd_exit_nonzero(tmp_path):
    """A test-cmd that fails (e.g. 'false') causes check.sh to exit non-zero."""
    workspace = _build_workspace(
        tmp_path,
        test_cmd="false\n",
        extra_files={
            "foo.py": "x = 1\n",
        },
    )
    rc, stdout, stderr = _run_check(workspace)
    assert rc != 0, f"Expected non-zero, got {rc}\nstdout:{stdout}\nstderr:{stderr}"
    assert "tests failed" in stderr, stderr


# ===================================================================
# Branch: ruff absent => warns, skips lint/format, runs tests
# ===================================================================


def test_ruff_absent_warns_and_skips_lint(tmp_path):
    """When ruff is not on PATH, check.sh warns, skips lint/format, runs tests."""
    workspace = _build_workspace(
        tmp_path,
        extra_files={
            "foo.py": "import os\nx = 1\n",
        },
    )
    no_ruff_env = _env_without_ruff()
    rc, stdout, stderr = _run_check(workspace, extra_env=no_ruff_env)
    assert rc == 0, f"Expected 0, got {rc}\nstdout:{stdout}\nstderr:{stderr}"
    assert "ruff not found" in stderr, stderr
    assert "all checks passed" in stdout, stdout


def test_ruff_absent_still_runs_tests(tmp_path):
    """When ruff is absent, tests still run and their exit reflects."""
    workspace = _build_workspace(
        tmp_path,
        test_cmd="false\n",
        extra_files={
            "foo.py": "x = 1\n",
        },
    )
    no_ruff_env = _env_without_ruff()
    rc, stdout, stderr = _run_check(workspace, extra_env=no_ruff_env)
    assert rc != 0, f"Expected non-zero, got {rc}\nstdout:{stdout}\nstderr:{stderr}"
    assert "ruff not found" in stderr, stderr
    assert "tests failed" in stderr, stderr


# ===================================================================
# Branch: absent / empty test-cmd => exit 0 (no-op)
# ===================================================================


def test_no_test_cmd_file_exit_0(tmp_path):
    """No scripts/test-cmd file => check.sh exits 0 (no-op for test stage)."""
    workspace = _build_workspace(
        tmp_path,
        extra_files={
            "foo.py": "x = 1\n",
        },
    )
    # Remove test-cmd
    (workspace / "scripts" / "test-cmd").unlink()
    rc, stdout, stderr = _run_check(workspace)
    assert rc == 0, f"Expected 0, got {rc}\nstdout:{stdout}\nstderr:{stderr}"
    assert "no scripts/test-cmd" in stdout, stdout


def test_empty_test_cmd_exit_0(tmp_path):
    """Empty scripts/test-cmd file => check.sh exits 0 (no-op)."""
    workspace = _build_workspace(
        tmp_path,
        test_cmd="",
        extra_files={
            "foo.py": "x = 1\n",
        },
    )
    rc, stdout, stderr = _run_check(workspace)
    assert rc == 0, f"Expected 0, got {rc}\nstdout:{stdout}\nstderr:{stderr}"
    assert "empty/whitespace-only" in stdout, stdout


def test_unresolvable_test_executable_exit_0(tmp_path):
    """A test-cmd whose executable is not resolvable => exit 0 with warning."""
    workspace = _build_workspace(
        tmp_path, test_cmd="nonexistent-binary --flag\n", extra_files={"foo.py": "x = 1\n"}
    )
    rc, stdout, stderr = _run_check(workspace)
    assert rc == 0, f"Expected 0, got {rc}\nstdout:{stdout}\nstderr:{stderr}"
    assert "cannot run" in stderr, stderr
    assert "NOT blocking" in stderr, stderr
