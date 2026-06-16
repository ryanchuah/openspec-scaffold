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
import json
import os
import re
import sys
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STATE_DIR = "/tmp"
_SIGIL = "apply-convergence-"

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
        m = re.search(r'FAILED\s+(\S+(?:::\S+)?)\s*-\s', line)
        if m:
            return m.group(1)

        # pytest verbose short: "path::test_name FAILED"
        m = re.search(r'(\S+::\S+)\s+FAILED', line)
        if m:
            return m.group(1)

        # unittest: FAIL: test_name (module.ClassName)
        m = re.search(r'FAIL:\s+(\S+)', line)
        if m:
            return m.group(1)

        # Generic: "ERROR: test_name"
        m = re.search(r'ERROR(?:\s+collecting)?\s+(\S+)', line)
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

    # Strip absolute paths: /foo/bar/baz.py
    text = re.sub(r'/\S+', ' <PATH> ', text)

    # Strip ISO/epoch timestamps BEFORE line-number stripping because
    # timestamps contain ":digits" sequences that the line-number regex
    # would otherwise consume, leaving an unrecoverable partial stamp.
    text = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', '<ISO>', text)
    text = re.sub(r'(?<!\d)\d{4}-\d{2}-\d{2}(?!T)', '<DATE>', text)
    text = re.sub(r'\b\d{8,10}(?:\.\d+)?\b', '<EPOCH>', text)

    # Strip elapsed-time numbers: 2.34s, 0.50s, 1234ms
    text = re.sub(r'\b\d+\.\d+s\b', '<ELAPSED>', text)
    text = re.sub(r'\b\d+ms\b', '<ELAPSED>', text)

    # Strip line:col references: :42, :42:5, line 42, col 7
    text = re.sub(r'(?<!\w)(line\s+)\d+', r'\1<N>', text, flags=re.IGNORECASE)
    text = re.sub(r'(?<!\w)(col(?:umn)?\s+)\d+', r'\1<N>', text, flags=re.IGNORECASE)
    text = re.sub(r'(?<!\d):\d+(?::\d+)?\b', ':<N>', text)

    # Strip hex addresses: 0x[0-9a-f]+
    text = re.sub(r'0x[0-9a-fA-F]+', '0x<HEX>', text)

    # Strip "object at 0x..." phrases
    text = re.sub(r'object\s+at\s+0x[0-9a-fA-F]+', 'object at 0x<HEX>', text)

    # Normalize repeated whitespace within lines
    text = re.sub(r'[ \t]+', ' ', text)

    # Strip empty/whitespace-only lines, then strip each line
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return '\n'.join(lines)


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
# Core logic
# ---------------------------------------------------------------------------

def _verdict(
    test_id: str,
    signature: str,
    editing_file: Optional[str],
    change_slug: str,
    task_id: str,
) -> str:
    """Examine state and return a verdict string.

    Returns one of:
        "CONTINUE"
        "STOP:a:<detail>"
        "STOP:b:<detail>"
    """
    state = _load_state(change_slug)

    # Initialize per-change failure tracking if absent
    if "failures" not in state:
        state["failures"] = {}

    failure_key = test_id
    now = state["failures"].get(failure_key, {
        "attempts": 0,
        "last_signature": None,
        "files_edited": [],
    })

    attempts = now["attempts"] + 1
    last_sig = now["last_signature"]
    files_edited: list[str] = now.get("files_edited", [])

    # --- Rule (a): same signature after 2 consecutive attempts ---
    if last_sig is not None and last_sig == signature and attempts >= 2:
        state["failures"][failure_key] = {
            "attempts": attempts,
            "last_signature": signature,
            "files_edited": files_edited,
        }
        _save_state(change_slug, state)
        return f"STOP:a:Task {task_id} — test {test_id} failed with the same normalized error after {attempts} attempts"

    # --- Rule (b): about to edit file already edited 2+ times for this failure ---
    if editing_file is not None:
        # Count how many times this file has been edited for this failure
        edit_count = sum(1 for f in files_edited if f == editing_file)
        if edit_count >= 2:
            state["failures"][failure_key] = {
                "attempts": attempts,
                "last_signature": signature,
                "files_edited": files_edited,
            }
            _save_state(change_slug, state)
            return f"STOP:b:Task {task_id} — would edit {editing_file} a {edit_count + 1}th time for test {test_id}"

        # Record the pending edit
        files_edited.append(editing_file)

    # --- CONTINUE: update state and allow further attempts ---
    state["failures"][failure_key] = {
        "attempts": attempts,
        "last_signature": signature,
        "files_edited": files_edited,
    }
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
        help="File path about to be edited (load-bearing for rule b)",
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

    # Normalize the error signature
    signature = _normalize_signature(raw_output)

    # Determine verdict
    verdict = _verdict(
        test_id=test_id,
        signature=signature,
        editing_file=args.editing,
        change_slug=args.change,
        task_id=args.task,
    )
    print(verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
