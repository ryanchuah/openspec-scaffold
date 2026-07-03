#!/usr/bin/env python3
"""data_lint.py — plain-SQL data-invariant runner (D4).

Convention
----------
Each check is a single ``*.sql`` file in ``--checks-dir`` (default
``checks/``, **flat directory only, no recursion** — matches the ~5-checks
D4 scale). Each file is exactly ONE ``SELECT`` returning the VIOLATING rows
for that invariant (orphans, dupes, nulls, referential integrity, sane
ranges, ...): zero rows returned = pass, any rows returned = fail. Checks
run in sorted filename order, one at a time, via::

    psql <db-url> -v ON_ERROR_STOP=1 --csv -f <file>

with ``PGOPTIONS="-c default_transaction_read_only=on"`` merged into the
subprocess environment on EVERY invocation — a hard, server-enforced D3
read-only guarantee (the check cannot write even if the SQL tried to), not
merely a convention. Each check also runs under a subprocess timeout
(default 120s, override with ``--timeout``); a timed-out check is treated
as an infrastructure failure so a hung connection can never hang a whole
bundle run.

Output
------
JSON written to ``--json`` (default ``data_lint.json``)::

    {
      "generated_by": "data_lint.py",
      "checks": [
        {"name": "<file-stem>", "status": "pass"|"fail", "rows": <int>, "sample": [...]}
      ]
    }

``sample`` holds up to ``--max-sample`` (default 5) violating rows, each as
a ``{column: value}`` dict from the CSV header.

Stdout: one summary line per check, ``data_lint/<name>: <pass|FAIL> — <n>
rows``, plus one final line ``data_lint: <clean|N check(s) failing> ->
<json-path>``.

Exit codes
----------
0  — no checks dir / no ``*.sql`` files (not adopted yet — not an error), or
     every check passed.
2  — one or more checks returned violating rows.
3  — infra failure: no ``--db-url``/``AUDIT_DB_URL``, a psql error (missing
     binary, connection refused, SQL error in a check file), or a check
     timing out. Stops immediately on the FIRST infra failure — a broken
     check must fail loudly, never be silently skipped, so no later check
     file runs.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import subprocess
import sys
from pathlib import Path

GENERATED_BY = "data_lint.py"
DEFAULT_TIMEOUT = 120
DEFAULT_MAX_SAMPLE = 5
DB_URL_ENV_VAR = "AUDIT_DB_URL"


def _write_json_atomic(path: Path, payload) -> None:
    """Write JSON to *path* atomically: full content to ``<path>.tmp``, then
    ``os.replace`` over the destination (matches checks.py's
    ``_write_manifest`` pattern)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _parse_csv_output(raw: str) -> tuple[list[str], list[list[str]]]:
    """Split psql --csv stdout into (header, data_rows)."""
    reader = csv.reader(io.StringIO(raw))
    rows = [row for row in reader if row]
    if not rows:
        return [], []
    return rows[0], rows[1:]


def _run_check(
    sql_file: Path, db_url: str, timeout: int
) -> tuple[bool, int, list[dict[str, str]] | None, str]:
    """Run one check. Returns (infra_ok, row_count, sample_rows, error_message)."""
    env = dict(os.environ)
    env["PGOPTIONS"] = "-c default_transaction_read_only=on"

    cmd = ["psql", db_url, "-v", "ON_ERROR_STOP=1", "--csv", "-f", str(sql_file)]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, env=env, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return False, 0, None, f"check timed out after {timeout}s"
    except OSError as exc:
        return False, 0, None, f"failed to invoke psql: {exc}"

    if result.returncode != 0:
        return False, 0, None, result.stderr.strip() or "psql exited nonzero"

    header, data_rows = _parse_csv_output(result.stdout)
    sample = [dict(zip(header, row)) for row in data_rows]
    return True, len(data_rows), sample, ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run plain-SQL data-invariant checks (D4)."
    )
    parser.add_argument("--checks-dir", default="checks", help="Directory of *.sql checks (flat, no recursion).")
    parser.add_argument("--db-url", default=None, help=f"Postgres connection URL (default: env {DB_URL_ENV_VAR}).")
    parser.add_argument("--json", default="data_lint.json", help="Output JSON path.")
    parser.add_argument("--max-sample", type=int, default=DEFAULT_MAX_SAMPLE, help="Max violating rows to sample per check.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Subprocess timeout per check, seconds.")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    checks_dir = Path(args.checks_dir)
    json_path = Path(args.json)

    sql_files = sorted(checks_dir.glob("*.sql")) if checks_dir.is_dir() else []

    if not sql_files:
        _write_json_atomic(json_path, {"generated_by": GENERATED_BY, "checks": []})
        print("data_lint: no checks configured")
        return 0

    db_url = args.db_url or os.environ.get(DB_URL_ENV_VAR)
    if not db_url:
        print(
            f"data_lint: INFRA-FAIL — no --db-url given and {DB_URL_ENV_VAR} is not set",
            file=sys.stderr,
        )
        return 3

    checks: list[dict] = []
    any_fail = False

    for sql_file in sql_files:
        name = sql_file.stem
        ok, rows, sample, err = _run_check(sql_file, db_url, args.timeout)
        if not ok:
            print(f"data_lint: INFRA-FAIL — check {name}: {err}", file=sys.stderr)
            return 3

        status = "pass" if rows == 0 else "fail"
        if status == "fail":
            any_fail = True
        checks.append(
            {
                "name": name,
                "status": status,
                "rows": rows,
                "sample": sample[: args.max_sample],
            }
        )
        print(f"data_lint/{name}: {'pass' if status == 'pass' else 'FAIL'} — {rows} rows")

    _write_json_atomic(json_path, {"generated_by": GENERATED_BY, "checks": checks})

    failing = [c for c in checks if c["status"] == "fail"]
    tail = "clean" if not failing else f"{len(failing)} check(s) failing"
    print(f"data_lint: {tail} -> {json_path}")

    return 2 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
