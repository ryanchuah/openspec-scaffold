#!/usr/bin/env python3
"""Tests for scripts/githooks/pre-commit — the git-native commit-test gate.

Deterministic, throwaway-git-repo pytest (no gated Claude session required).
Builds a real git repo under tmp_path, wires `core.hooksPath` to a copy of
the real `scripts/githooks/pre-commit` (which execs a copy of the real
`scripts/check.sh`), and drives real `git commit --allow-empty` attempts
across every evasion spelling probed in design.md's Live Probe. Reuses the
tmp_path/workspace patterns from test_check_sh.py and
test_gate_command_detection.py.
"""

from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path

# ===================================================================
# Fixtures
# ===================================================================

SCRIPTS_DIR = Path(__file__).resolve().parent
CHECK_SH_SRC = SCRIPTS_DIR / "check.sh"
PRE_COMMIT_SRC = SCRIPTS_DIR / "githooks" / "pre-commit"

RUFF_TOML_CLEAN = """\
line-length = 100

[lint]
select = ["E", "F", "I", "B"]
ignore = ["E501"]
"""


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=True)


def _build_repo(tmp_path: Path, test_cmd: str = "true\n") -> Path:
    """Build a throwaway git repo with the real check.sh + pre-commit hook
    wired via core.hooksPath, plus a seed --no-verify commit so the tree
    starts clean."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init", "-q"], repo)
    _run(["git", "config", "user.email", "test@example.com"], repo)
    _run(["git", "config", "user.name", "Test"], repo)

    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy2(str(CHECK_SH_SRC), str(scripts_dir / "check.sh"))
    (scripts_dir / "check.sh").chmod(0o755)

    githooks_dir = scripts_dir / "githooks"
    githooks_dir.mkdir()
    shutil.copy2(str(PRE_COMMIT_SRC), str(githooks_dir / "pre-commit"))
    (githooks_dir / "pre-commit").chmod(0o755)

    (repo / "ruff.toml").write_text(RUFF_TOML_CLEAN, encoding="utf-8")
    (repo / "clean.py").write_text("x = 1\n", encoding="utf-8")
    (scripts_dir / "test-cmd").write_text(test_cmd, encoding="utf-8")

    _run(["git", "config", "--local", "core.hooksPath", "scripts/githooks"], repo)

    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "--no-verify", "-m", "seed"], repo)
    return repo


def _spellings(repo: Path) -> list[tuple[str, Path, str]]:
    """Every evasion spelling probed in design.md's Live Probe: (label, cwd,
    shell command)."""
    repo_s = str(repo)
    parent = repo.parent
    return [
        ("git commit", repo, "git commit --allow-empty -m attempt"),
        (
            "cd <repo> && git commit",
            parent,
            f"cd {shlex.quote(repo_s)} && git commit --allow-empty -m attempt",
        ),
        (
            "git -C <repo> commit",
            parent,
            f"git -C {shlex.quote(repo_s)} commit --allow-empty -m attempt",
        ),
        ("env FOO=bar git commit", repo, "env FOO=bar git commit --allow-empty -m attempt"),
    ]


def _attempt(cwd: Path, cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, cwd=str(cwd), capture_output=True, text=True)


def _commit_count(repo: Path) -> int:
    proc = _run(["git", "rev-list", "--count", "HEAD"], repo)
    return int(proc.stdout.strip())


# ===================================================================
# Real pre-commit hook: exec bit
# ===================================================================


def test_real_pre_commit_hook_is_executable():
    """Guards against a lost exec bit on the tracked hook (load-bearing —
    git silently skips a non-executable hook)."""
    assert PRE_COMMIT_SRC.exists(), "scripts/githooks/pre-commit is missing"
    mode = PRE_COMMIT_SRC.stat().st_mode
    assert mode & 0o111, "scripts/githooks/pre-commit is not executable"


# ===================================================================
# Red test-cmd => blocked, across every evasion spelling
# ===================================================================


def test_red_test_cmd_blocks_every_spelling(tmp_path):
    repo = _build_repo(tmp_path, test_cmd="false\n")
    before = _commit_count(repo)
    for label, cwd, cmd in _spellings(repo):
        proc = _attempt(cwd, cmd)
        assert proc.returncode != 0, (
            f"{label}: expected commit to be BLOCKED, got exit 0\n"
            f"stdout:{proc.stdout}\nstderr:{proc.stderr}"
        )
    after = _commit_count(repo)
    assert after == before, "a blocked spelling still advanced HEAD"


# ===================================================================
# Green test-cmd => allowed
# ===================================================================


def test_green_test_cmd_allows_commit(tmp_path):
    repo = _build_repo(tmp_path, test_cmd="true\n")
    before = _commit_count(repo)
    proc = _attempt(repo, "git commit --allow-empty -m attempt")
    assert proc.returncode == 0, f"stdout:{proc.stdout}\nstderr:{proc.stderr}"
    assert _commit_count(repo) == before + 1


# ===================================================================
# --no-verify => allowed even when red (visible opt-out)
# ===================================================================


def test_no_verify_allowed_even_when_red(tmp_path):
    repo = _build_repo(tmp_path, test_cmd="false\n")
    before = _commit_count(repo)
    proc = _attempt(repo, "git commit --allow-empty --no-verify -m attempt")
    assert proc.returncode == 0, f"stdout:{proc.stdout}\nstderr:{proc.stderr}"
    assert _commit_count(repo) == before + 1
