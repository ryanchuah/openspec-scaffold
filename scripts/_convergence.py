#!/usr/bin/env python3
"""_convergence.py — Deterministic convergence helper for OpenSpec apply-executor.

Reads raw test output on stdin and emits a verdict: CONTINUE (keep fixing
the same failure) or STOP:<a|b|c>:<detail> (rule a/b/c triggered).

Maintains durable per-change state in /tmp/apply-convergence-<slug>.json.

Usage:
    cat test_output.txt | python _convergence.py --task T3.1 --change harden-delegation
    cat test_output.txt | python _convergence.py --task T3.1 --change harden-delegation --editing foo.py

Exit codes:
    0 — verdict printed to stdout (CONTINUE or STOP:...)
    1 — error (no parseable verdict); executor treats as rule-(c) gap
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STATE_DIR = "/tmp"
_SIGIL = "apply-convergence-"
_MAX_ATTEMPTS = 20  # Absolute backstop ceiling — never interrupt healthy iteration

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_failing_test(raw_output: str) -> Optional[str]:
    """Extract the failing test node id from raw test output.

    Supports pytest, unittest, and generic patterns:
      - "FAILED test_foo.py::test_bar - AssertionError: ..."
      - "FAIL: test_baz (test_module.TestClass)"
      - "test_bar (test_module.TestClass.test_bar) ... FAIL"
      - "ERROR collecting test_foo.py"
    Returns the test id string or None.
    """
    lines = raw_output.splitlines()
    for line in lines:
        # pytest short format: FAILED path::test_name - error
        m = re.search(r"FAILED\s+(\S+(?:::\S+)?)\s*-\s", line)
        if m:
            return m.group(1)

        # pytest verbose short: "path::test_name FAILED"
        m = re.search(r"(\S+::\S+)\s+FAILED", line)
        if m:
            return m.group(1)

        # unittest: FAIL: test_name (module.ClassName)
        m = re.search(r"FAIL:\s+(\S+)", line)
        if m:
            return m.group(1)

        # Generic: "ERROR: test_name"
        m = re.search(r"ERROR(?:\s+collecting)?\s+(\S+)", line)
        if m:
            return m.group(1)

    # Fallback: use the first non-empty line after "FAILURES" heading
    in_failures = False
    for line in lines:
        stripped = line.strip()
        if stripped == "FAILURES":
            in_failures = True
            continue
        if in_failures and stripped and not stripped.startswith("__"):
            # First content line under FAILURES: usually the test header
            return stripped

    return None


def _normalize_signature(raw_output: str) -> str:
    """Normalize an error output by removing volatile text.

    Strips:
      - Line/column numbers (e.g. ":42", "line 42", "col 7")
      - Absolute file paths (starting with /)
      - Temp paths (/tmp/...)
      - ISO-8601 timestamps and epoch timestamps
      - Hex addresses (0x..., object at 0x...)
      - Elapsed-time numbers (e.g. "2.34s", "0.50s")
      - Trailing/leading whitespace per line

    Returns a compact, normalized string.
    """
    text = raw_output

    # Strip real filesystem paths (A4): /foo/bar/baz.py — matches only
    # /-separated runs ending in name.ext, leaving non-path / content
    # (regex literals, URLs, math) intact.  Must run BEFORE line-number
    # stripping (ordering comment below is load-bearing).
    text = re.sub(r"(?:/[\w.\-]+)*/[\w.\-]+\.\w+", " <PATH> ", text)

    # Strip ISO/epoch timestamps BEFORE line-number stripping because
    # timestamps contain ":digits" sequences that the line-number regex
    # would otherwise consume, leaving an unrecoverable partial stamp.
    text = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", "<ISO>", text)
    text = re.sub(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!T)", "<DATE>", text)
    text = re.sub(r"\b\d{8,10}(?:\.\d+)?\b", "<EPOCH>", text)

    # Strip elapsed-time numbers: 2.34s, 0.50s, 1234ms
    text = re.sub(r"\b\d+\.\d+s\b", "<ELAPSED>", text)
    text = re.sub(r"\b\d+ms\b", "<ELAPSED>", text)

    # Strip line:col references: :42, :42:5, line 42, col 7
    text = re.sub(r"(?<!\w)(line\s+)\d+", r"\1<N>", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<!\w)(col(?:umn)?\s+)\d+", r"\1<N>", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<!\d):\d+(?::\d+)?\b", ":<N>", text)

    # Strip hex addresses: 0x[0-9a-f]+
    text = re.sub(r"0x[0-9a-fA-F]+", "0x<HEX>", text)

    # Strip "object at 0x..." phrases
    text = re.sub(r"object\s+at\s+0x[0-9a-fA-F]+", "object at 0x<HEX>", text)

    # Normalize repeated whitespace within lines
    text = re.sub(r"[ \t]+", " ", text)

    # Strip empty/whitespace-only lines, then strip each line
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


# ---- Section boundaries for A2 scoped signature ----

_BOUNDARY_PATTERNS = [
    # Another test header: pytest FAILED ...
    re.compile(r"FAILED\s+\S+(?:::\S+)?"),
    # Another test header: unittest FAIL: or ERROR
    re.compile(r"(?:FAIL|ERROR)(?:\s+collecting)?\s+\S+"),
    # pytest separator run: ===== ... ===== or _____ ... _____
    re.compile(r"^[=_]+\s.*[=_]+\s*$"),
    # Summary line: === ... passed/failed/error ... ===
    re.compile(r"^=+.*(?:passed|failed|error).*=+$", re.IGNORECASE),
]


def _extract_test_section(raw_output: str, test_id: str) -> str:
    """Slice raw_output to just the failing test's section.

    Starts at the line matching the failing *test_id*, ends at the next
    test header / separator / summary.  Falls back to whole output if the
    start line cannot be located (preserving legacy behavior).
    """
    lines = raw_output.splitlines()
    start_idx = None
    # Walk lines looking for the line containing the test_id
    for i, line in enumerate(lines):
        if test_id in line:
            start_idx = i
            break

    if start_idx is None:
        # Fallback: whole-output normalization
        return raw_output

    # End at the first boundary line *after* start_idx
    end_idx = None
    for i in range(start_idx + 1, len(lines)):
        stripped = lines[i].strip()
        if any(p.search(stripped) for p in _BOUNDARY_PATTERNS):
            end_idx = i
            break

    if end_idx is None:
        # No boundary found — take up to 40 lines after start
        end_idx = min(start_idx + 40, len(lines))

    return "\n".join(lines[start_idx:end_idx])


def _normalize_test_key(test_id: str) -> str:
    """Reduce a node id to a path-stable form for state keys.

    Splits on ``::``, replaces the file part with ``os.path.basename()``,
    so both absolute and relative paths map to the same key.
    """
    if "::" in test_id:
        parts = test_id.split("::", 1)
        file_part = os.path.basename(parts[0])
        return f"{file_part}::{parts[1]}"
    # No :: separator — return as-is (probably a non-pytest format)
    return test_id


def _load_state(change_slug: str) -> dict[str, Any]:
    """Load convergence state from disk. Returns empty dict if missing/corrupt."""
    path = os.path.join(_STATE_DIR, f"{_SIGIL}{change_slug}.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save_state(change_slug: str, state: dict[str, Any]) -> None:
    """Save convergence state to disk atomically."""
    path = os.path.join(_STATE_DIR, f"{_SIGIL}{change_slug}.json")
    tmp = path + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, path)
    except OSError:
        # Best-effort; executor should treat as rule-(c) if this fails
        pass


# ---------------------------------------------------------------------------
# Git-based file fingerprint helpers (A3)
# ---------------------------------------------------------------------------

# Top-level state key for the per-change fingerprint map
_FINGERPRINTS_KEY = "file_fingerprints"


def _try_git_delta(
    repo_root: str, old_fingerprints: dict[str, str]
) -> tuple[list[str], dict[str, str], bool]:
    """Try to determine which files were edited this attempt via git.

    Returns (delta_files, new_fingerprints, ok):
        delta_files — list of files whose content changed since last call
        new_fingerprints — updated {file: sha1_hex} map for next call
        ok — True if git succeeded, False if degraded
    """
    try:
        # Get list of changed (unstaged + staged) files vs HEAD
        result = subprocess.run(
            ["git", "-C", repo_root, "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return [], {}, False

        changed_files = [f for f in result.stdout.splitlines() if f.strip()]
        if not changed_files:
            # No changes at all
            return [], old_fingerprints, True

        # Compute SHA1 fingerprints for changed files
        new_fingerprints = dict(old_fingerprints)
        delta: list[str] = []

        for rel_path in changed_files:
            abs_path = os.path.join(repo_root, rel_path)
            try:
                with open(abs_path, "rb") as fh:
                    sha1 = hashlib.sha1(fh.read()).hexdigest()
            except (OSError, IOError):
                # File might have been deleted; skip it
                continue

            old_fp = new_fingerprints.get(rel_path)
            if old_fp is None or old_fp != sha1:
                delta.append(rel_path)
                new_fingerprints[rel_path] = sha1

        return delta, new_fingerprints, True

    except (subprocess.SubprocessError, OSError, ValueError):
        # Any failure — degrade gracefully (no crash)
        return [], {}, False


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def _verdict(
    test_id: str,
    signature: str,
    editing_file: Optional[str],
    change_slug: str,
    task_id: str,
    repo_root: Optional[str] = None,
) -> str:
    """Examine state and return a verdict string.

    Returns one of:
        "CONTINUE"
        "STOP:a:<detail>"
        "STOP:b:<detail>"

    Ordering (task 2.3): rule-(a) consecutive, rule-(b) repeated-touch,
    oscillation (A1), absolute backstop ceiling (A1).
    """
    state = _load_state(change_slug)

    # Initialize per-change failure tracking if absent
    if "failures" not in state:
        state["failures"] = {}

    failure_key = _normalize_test_key(test_id)
    now = state["failures"].get(
        failure_key,
        {
            "attempts": 0,
            "prev_signature": None,
            "last_signature": None,
            "files_edited": [],
        },
    )

    attempts = now["attempts"] + 1
    prev_sig = now.get("prev_signature")
    last_sig = now["last_signature"]
    files_edited: list[str] = now.get("files_edited", [])

    # Slide signatures for state update (used on all non-early-return paths)
    next_prev = last_sig
    next_last = signature

    # --- Rule (a): same signature after 2 consecutive attempts ---
    if last_sig is not None and last_sig == signature and attempts >= 2:
        # Save with current files_edited (no new edits recorded yet)
        state["failures"][failure_key] = {
            "attempts": attempts,
            "prev_signature": next_prev,
            "last_signature": next_last,
            "files_edited": files_edited,
        }
        _save_state(change_slug, state)
        return f"STOP:a:Task {task_id} — test {test_id} failed with the same normalized error after {attempts} attempts"

    # --- Determine files edited this attempt (A3) ---
    # Try git-based derivation first; fall back to --editing hint
    attempts_files: list[str] = []
    git_ok = False

    if repo_root:
        delta_files, new_fingerprints, git_ok = _try_git_delta(
            repo_root,
            state.get(_FINGERPRINTS_KEY, {}),
        )
        if git_ok:
            state[_FINGERPRINTS_KEY] = new_fingerprints
            attempts_files = delta_files

    if not git_ok:
        # Fall back to --editing hint
        if editing_file is not None:
            attempts_files = [editing_file]

    # Warn if git was attempted but failed and no --editing coverage
    if not attempts_files and editing_file is None and repo_root and not git_ok:
        print(
            "WARNING: git-diff failed and no --editing; rule (b) has zero coverage",
            file=sys.stderr,
        )

    # --- Rule (b): file already edited 2+ times for this failure ---
    for edit_file in attempts_files:
        edit_count = sum(1 for f in files_edited if f == edit_file)
        if edit_count >= 2:
            from_source = "git-diff" if git_ok else "--editing"
            state["failures"][failure_key] = {
                "attempts": attempts,
                "prev_signature": next_prev,
                "last_signature": next_last,
                "files_edited": files_edited,
            }
            _save_state(change_slug, state)
            return (
                f"STOP:b:Task {task_id} — {edit_file} has been edited "
                f"{edit_count + 1} times for test {test_id} ({from_source})"
            )

        # Record this edit for this failure
        files_edited.append(edit_file)

    # --- Oscillation detection (A1): S(n) == S(n-2) and attempts >= 3 ---
    if prev_sig is not None and prev_sig == signature and attempts >= 3:
        state["failures"][failure_key] = {
            "attempts": attempts,
            "prev_signature": next_prev,
            "last_signature": next_last,
            "files_edited": files_edited,
        }
        _save_state(change_slug, state)
        return f"STOP:a:Task {task_id} — test {test_id} oscillating between two error signatures after {attempts} attempts, not converging"

    # --- Absolute backstop ceiling (A1): attempts >= _MAX_ATTEMPTS ---
    if attempts >= _MAX_ATTEMPTS:
        state["failures"][failure_key] = {
            "attempts": attempts,
            "prev_signature": next_prev,
            "last_signature": next_last,
            "files_edited": files_edited,
        }
        _save_state(change_slug, state)
        return f"STOP:a:Task {task_id} — test {test_id} reached {_MAX_ATTEMPTS} attempts without converging"

    # --- CONTINUE: update state and allow further attempts ---
    state["failures"][failure_key] = {
        "attempts": attempts,
        "prev_signature": next_prev,
        "last_signature": next_last,
        "files_edited": files_edited,
    }
    if git_ok:
        state[_FINGERPRINTS_KEY] = new_fingerprints
    _save_state(change_slug, state)
    return "CONTINUE"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convergence helper for OpenSpec apply-executor",
    )
    parser.add_argument(
        "--task",
        required=True,
        help="Task identifier (e.g. T3.1)",
    )
    parser.add_argument(
        "--change",
        required=True,
        help="Change slug (e.g. harden-delegation)",
    )
    parser.add_argument(
        "--editing",
        default=None,
        help="File path about to be edited (optional hint; git-diff is primary for rule b)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    raw_output = sys.stdin.read()

    # Extract failing test id
    test_id = _extract_failing_test(raw_output)
    if test_id is None:
        # Could not find a test id — that's unusual. Emit STOP:c as a gap.
        print("STOP:c:Could not extract failing test id from test output")
        return 0

    # Normalize the error signature over the failing test's section (A2)
    section = _extract_test_section(raw_output, test_id)
    signature = _normalize_signature(section)

    # Determine verdict — pass cwd as repo_root for git-based derivation (A3)
    verdict = _verdict(
        test_id=test_id,
        signature=signature,
        editing_file=args.editing,
        change_slug=args.change,
        task_id=args.task,
        repo_root=os.getcwd(),
    )
    print(verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
