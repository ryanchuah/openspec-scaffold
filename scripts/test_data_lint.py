#!/usr/bin/env python3
"""Tests for data_lint.py — stdlib unittest, no pytest.

A stub `psql` shell script is prepended to PATH. Since data_lint invokes
`psql <db-url> ... -f <file>`, the stub inspects the SQL file's first line
for a directive comment (`-- STUB: zero|fail|violations:N`) to decide its
canned CSV output / exit code, and records its argv + PGOPTIONS to a
recording file (`$STUB_RECORD_FILE`) so tests can verify invocation order
and the read-only environment guarantee.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import data_lint  # noqa: E402


_PSQL_STUB = """\
#!/bin/sh
# args: <db-url> -v ON_ERROR_STOP=1 --csv -f <file>
prev=""
FILE=""
for arg in "$@"; do
  if [ "$prev" = "-f" ]; then
    FILE="$arg"
  fi
  prev="$arg"
done

{
  echo "ARGV: $@"
  echo "PGOPTIONS: $PGOPTIONS"
} >> "$STUB_RECORD_FILE"

mode=$(head -n 1 "$FILE" | sed -n 's/^-- STUB: //p')

case "$mode" in
  zero)
    printf 'col1\\n'
    exit 0
    ;;
  violations:*)
    n="${mode#violations:}"
    printf 'col1,col2\\n'
    i=1
    while [ "$i" -le "$n" ]; do
      printf 'v%s,w%s\\n' "$i" "$i"
      i=$((i+1))
    done
    exit 0
    ;;
  fail)
    echo "simulated sql error" >&2
    exit 1
    ;;
  *)
    echo "no STUB marker found in $FILE" >&2
    exit 1
    ;;
esac
"""


class DataLintTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.checks_dir = self.tmpdir / "checks"
        self.checks_dir.mkdir()

        self.stub_bin = self.tmpdir / "stub_bin"
        self.stub_bin.mkdir()
        psql = self.stub_bin / "psql"
        psql.write_text(_PSQL_STUB)
        psql.chmod(0o755)

        self.record_file = self.tmpdir / "record.txt"
        self.record_file.write_text("")

        self._orig_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{self.stub_bin}{os.pathsep}{self._orig_path}"
        self._orig_record = os.environ.get("STUB_RECORD_FILE")
        os.environ["STUB_RECORD_FILE"] = str(self.record_file)
        self._orig_db_url_env = os.environ.pop("AUDIT_DB_URL", None)

    def tearDown(self):
        os.environ["PATH"] = self._orig_path
        if self._orig_record is None:
            os.environ.pop("STUB_RECORD_FILE", None)
        else:
            os.environ["STUB_RECORD_FILE"] = self._orig_record
        if self._orig_db_url_env is not None:
            os.environ["AUDIT_DB_URL"] = self._orig_db_url_env
        else:
            os.environ.pop("AUDIT_DB_URL", None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_check(self, filename: str, directive: str) -> Path:
        p = self.checks_dir / filename
        p.write_text(f"-- STUB: {directive}\nSELECT 1;\n")
        return p

    def _capture(self, argv: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = data_lint.main(argv)
        return rc, buf.getvalue()

    def _record_lines(self) -> list[str]:
        return self.record_file.read_text().splitlines()

    # ------------------------------------------------------------------

    def test_pgoptions_readonly_present_every_invocation(self):
        self._write_check("001_a.sql", "zero")
        self._write_check("002_b.sql", "zero")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir", str(self.checks_dir),
                "--db-url", "postgres://fake/db",
                "--json", str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        pgoptions_lines = [line for line in self._record_lines() if line.startswith("PGOPTIONS:")]
        self.assertEqual(len(pgoptions_lines), 2)
        for line in pgoptions_lines:
            self.assertIn("default_transaction_read_only=on", line)

    def test_on_error_stop_and_csv_present_in_argv(self):
        self._write_check("001_a.sql", "zero")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir", str(self.checks_dir),
                "--db-url", "postgres://fake/db",
                "--json", str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        argv_lines = [line for line in self._record_lines() if line.startswith("ARGV:")]
        self.assertEqual(len(argv_lines), 1)
        self.assertIn("ON_ERROR_STOP=1", argv_lines[0])
        self.assertIn("--csv", argv_lines[0])

    def test_zero_rows_exit_0(self):
        self._write_check("001_a.sql", "zero")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir", str(self.checks_dir),
                "--db-url", "postgres://fake/db",
                "--json", str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())
        self.assertEqual(data["checks"][0]["status"], "pass")
        self.assertEqual(data["checks"][0]["rows"], 0)
        self.assertIn("data_lint/001_a: pass — 0 rows", out)
        self.assertIn("data_lint: clean ->", out)

    def test_violating_rows_exit_2_with_row_count_and_sample(self):
        self._write_check("001_a.sql", "violations:3")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir", str(self.checks_dir),
                "--db-url", "postgres://fake/db",
                "--json", str(json_path),
            ]
        )
        self.assertEqual(rc, 2)
        data = json.loads(json_path.read_text())
        entry = data["checks"][0]
        self.assertEqual(entry["status"], "fail")
        self.assertEqual(entry["rows"], 3)
        self.assertEqual(len(entry["sample"]), 3)
        self.assertEqual(entry["sample"][0], {"col1": "v1", "col2": "w1"})
        self.assertIn("data_lint/001_a: FAIL — 3 rows", out)
        self.assertIn("data_lint: 1 check(s) failing ->", out)

    def test_sample_capped_at_max_sample(self):
        self._write_check("001_a.sql", "violations:10")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir", str(self.checks_dir),
                "--db-url", "postgres://fake/db",
                "--json", str(json_path),
                "--max-sample", "2",
            ]
        )
        self.assertEqual(rc, 2)
        data = json.loads(json_path.read_text())
        entry = data["checks"][0]
        self.assertEqual(entry["rows"], 10)
        self.assertEqual(len(entry["sample"]), 2)

    def test_stub_nonzero_exit_3_and_no_later_check_runs(self):
        self._write_check("001_a.sql", "zero")
        self._write_check("002_b.sql", "fail")
        self._write_check("003_c.sql", "violations:1")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir", str(self.checks_dir),
                "--db-url", "postgres://fake/db",
                "--json", str(json_path),
            ]
        )
        self.assertEqual(rc, 3)
        argv_lines = [line for line in self._record_lines() if line.startswith("ARGV:")]
        # Only 001_a (passed) and 002_b (failed) ran — 003_c never executed.
        self.assertEqual(len(argv_lines), 2)
        self.assertTrue(any("001_a.sql" in line for line in argv_lines))
        self.assertTrue(any("002_b.sql" in line for line in argv_lines))
        self.assertFalse(any("003_c.sql" in line for line in argv_lines))

    def test_no_db_url_and_no_env_exits_3(self):
        self._write_check("001_a.sql", "zero")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir", str(self.checks_dir),
                "--json", str(json_path),
            ]
        )
        self.assertEqual(rc, 3)

    def test_db_url_from_env_var(self):
        self._write_check("001_a.sql", "zero")
        json_path = self.tmpdir / "out.json"
        os.environ["AUDIT_DB_URL"] = "postgres://fromenv/db"
        try:
            rc, out = self._capture(
                [
                    "--checks-dir", str(self.checks_dir),
                    "--json", str(json_path),
                ]
            )
        finally:
            os.environ.pop("AUDIT_DB_URL", None)
        self.assertEqual(rc, 0)

    def test_absent_checks_dir_exits_0_no_checks_configured(self):
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir", str(self.tmpdir / "does-not-exist"),
                "--db-url", "postgres://fake/db",
                "--json", str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("data_lint: no checks configured", out)

    def test_empty_checks_dir_exits_0_no_checks_configured(self):
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir", str(self.checks_dir),
                "--db-url", "postgres://fake/db",
                "--json", str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("data_lint: no checks configured", out)

    def test_checks_execute_in_sorted_filename_order(self):
        # Deliberately create out of alphabetical order.
        self._write_check("002_b.sql", "zero")
        self._write_check("001_a.sql", "zero")
        self._write_check("003_c.sql", "zero")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir", str(self.checks_dir),
                "--db-url", "postgres://fake/db",
                "--json", str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        argv_lines = [line for line in self._record_lines() if line.startswith("ARGV:")]
        order = []
        for line in argv_lines:
            for name in ("001_a.sql", "002_b.sql", "003_c.sql"):
                if name in line:
                    order.append(name)
        self.assertEqual(order, ["001_a.sql", "002_b.sql", "003_c.sql"])
        data = json.loads(json_path.read_text())
        self.assertEqual(
            [c["name"] for c in data["checks"]], ["001_a", "002_b", "003_c"]
        )


if __name__ == "__main__":
    unittest.main()
