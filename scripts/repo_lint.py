#!/usr/bin/env python3
"""repo_lint.py — per-repo code/repo-shape invariant runner (D4-scope sibling of data_lint.py).

Conventions (discoverable here — the first place an author reads):

Check contract
--------------
Each check is a single ``checks/*.py`` file in ``--checks-dir`` (default
``checks/``, **flat directory only, no recursion** — the ``data_lint.py``
convention, sharing the same directory with disjoint extension). Invoked as::

    <python> <file> <repo-root>

The check script prints a JSON array of findings to stdout and exits 0::

    [{"path": "src/foo.py", "line": 42, "message": "os.system() call at ..."}]

An empty array ``[]`` = pass (zero findings). Any nonzero exit, timeout, or
unparseable stdout is an **infrastructure failure** (INFRA-FAIL): the runner
stops at the FIRST such failure, no later check runs.

Minimal real check (``checks/no_fetchall.py``)::

    #!/usr/bin/env python3
    \"\"\"psc-monitor SCALE-1: unbounded ``.fetchall()`` calls.\"\"\"
    import sys, os, re
    root = sys.argv[1]
    findings = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            with open(path) as fh:
                for lineno, line in enumerate(fh, 1):
                    if ".fetchall()" in line and "LIMIT" not in line.upper():
                        findings.append({"path": os.path.relpath(path, root),
                                         "line": lineno,
                                         "message": "unbounded fetchall()"})
    print(json.dumps(findings))
    sys.exit(0)

**Check-only caveat (D3):** the runner cannot prevent a check script from
writing to the repo — keeping a check check-only is the CONFIGURING repo's
responsibility. This is the same contract as ``[checks.custom.*]`` commands
(see ``checks.py``'s D3 caveat).

**Admission bar:** a new invariant must be near-zero-false-positive and have
an obvious, actionable fix (the Tricorder criteria adapted). A noisy check
should be tuned or demoted to a ledger waiver. Target scale: ~5–15 deliberate
invariants per repo, grown from incidents — not a general lint suite.

**Graduation path:** when a repo outgrows ~15 bespoke checks, switch to an
external engine such as ast-grep (single pinned binary, YAML pattern rules)
via the existing ``[checks.custom.*]`` escape hatch.

Output
------
JSON written to ``--json`` (default ``repo_lint.json``)::

    {
      "generated_by": "repo_lint.py",
      "checks": [
        {"name": "<file-stem>", "status": "pass"|"fail", "findings": <n>, "sample": [...]}
      ]
    }

``sample`` holds up to ``--max-sample`` (default 5) findings, each as
``{"path","line","message"}`` dict. ``findings`` holds the FULL count.

Stdout: one summary line per check, ``repo_lint/<name>: <pass|FAIL> — <n>
findings``, plus one final line ``repo_lint: <clean|N check(s) failing> ->
<json-path>``.

Exit codes
----------
0  — no checks dir / no ``*.py`` files (not adopted yet — not an error), or
     every check passed.
2  — one or more checks emitted findings.
3  — infra failure: check exited nonzero, printed non-JSON, or timed out.
     Stops immediately on the FIRST infra failure — a broken check must fail
     loudly, never be silently skipped, so no later check file runs.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

GENERATED_BY = "repo_lint.py"
DEFAULT_TIMEOUT = 120
DEFAULT_MAX_SAMPLE = 5


def _write_json_atomic(path: Path, payload) -> None:
    """Write JSON to *path* atomically: full content to ``<path>.tmp``, then
    ``os.replace`` over the destination (matches checks.py's
    ``_write_manifest`` pattern and data_lint.py's ``_write_json_atomic``)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _run_check_file(
    py_file: Path, repo_root: Path, timeout: int
) -> tuple[bool, list[dict] | None, str]:
    """Run one check file as a subprocess.

    Returns ``(ok, findings, error)``:
    - ``ok`` is True on success (exit 0 + parseable JSON array), False on
      infra failure.
    - ``findings`` is the parsed list of finding dicts (empty list = pass),
      or None on infra failure.
    - ``error`` is a human-readable error message on failure, or empty string.
    """
    try:
        result = subprocess.run(
            [sys.executable, str(py_file), str(repo_root)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, None, f"check timed out after {timeout}s"
    except OSError as exc:
        return False, None, f"failed to invoke check: {exc}"

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        detail = stderr if stderr else f"exited with code {result.returncode}"
        return False, None, detail

    raw = (result.stdout or "").strip()
    if not raw:
        return False, None, "check printed empty stdout (expected JSON array)"
    try:
        findings = json.loads(raw)
    except json.JSONDecodeError as exc:
        return False, None, f"unparseable stdout: {exc}"

    if not isinstance(findings, list):
        return False, None, f"stdout is a {type(findings).__name__}, expected a JSON array"

    return True, findings, ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run per-repo code/repo-shape invariant checks (D4-scope sibling of data_lint.py)."
    )
    parser.add_argument(
        "--checks-dir", default="checks", help="Directory of *.py checks (flat, no recursion)."
    )
    parser.add_argument("--json", default="repo_lint.json", help="Output JSON path.")
    parser.add_argument(
        "--max-sample",
        type=int,
        default=DEFAULT_MAX_SAMPLE,
        help="Max findings to sample per check.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="Timeout per check subprocess, seconds.",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    checks_dir = Path(args.checks_dir)
    json_path = Path(args.json)

    py_files = sorted(checks_dir.glob("*.py")) if checks_dir.is_dir() else []

    if not py_files:
        _write_json_atomic(json_path, {"generated_by": GENERATED_BY, "checks": []})
        print("repo_lint: no checks configured")
        return 0

    # Resolve repo root from the checks dir's parent (or CWD).
    repo_root = checks_dir.resolve().parent

    checks: list[dict] = []
    any_fail = False

    for py_file in py_files:
        name = py_file.stem
        ok, findings, err = _run_check_file(py_file, repo_root, args.timeout)
        if not ok:
            print(f"repo_lint: INFRA-FAIL — check {name}: {err}", file=sys.stderr)
            return 3

        status = "pass" if len(findings) == 0 else "fail"
        if status == "fail":
            any_fail = True
        sample = findings[: args.max_sample]
        checks.append(
            {
                "name": name,
                "status": status,
                "findings": len(findings),
                "sample": sample,
            }
        )
        print(
            f"repo_lint/{name}: {'pass' if status == 'pass' else 'FAIL'} — {len(findings)} findings"
        )

    _write_json_atomic(json_path, {"generated_by": GENERATED_BY, "checks": checks})

    failing = [c for c in checks if c["status"] == "fail"]
    tail = "clean" if not failing else f"{len(failing)} check(s) failing"
    print(f"repo_lint: {tail} -> {json_path}")

    return 2 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
