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

import hashlib
import io
import json
import os
import shutil
import sqlite3 as _stdlib_sqlite3
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
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
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                "postgres://fake/db",
                "--json",
                str(json_path),
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
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                "postgres://fake/db",
                "--json",
                str(json_path),
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
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                "postgres://fake/db",
                "--json",
                str(json_path),
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
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                "postgres://fake/db",
                "--json",
                str(json_path),
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
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                "postgres://fake/db",
                "--json",
                str(json_path),
                "--max-sample",
                "2",
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
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                "postgres://fake/db",
                "--json",
                str(json_path),
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
                "--checks-dir",
                str(self.checks_dir),
                "--json",
                str(json_path),
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
                    "--checks-dir",
                    str(self.checks_dir),
                    "--json",
                    str(json_path),
                ]
            )
        finally:
            os.environ.pop("AUDIT_DB_URL", None)
        self.assertEqual(rc, 0)

    def test_absent_checks_dir_exits_0_no_checks_configured(self):
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir",
                str(self.tmpdir / "does-not-exist"),
                "--db-url",
                "postgres://fake/db",
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("data_lint: no checks configured", out)

    def test_empty_checks_dir_exits_0_no_checks_configured(self):
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                "postgres://fake/db",
                "--json",
                str(json_path),
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
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                "postgres://fake/db",
                "--json",
                str(json_path),
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
        self.assertEqual([c["name"] for c in data["checks"]], ["001_a", "002_b", "003_c"])


# ------------------------------------------------------------------
# SQLite backend tests — use a real sqlite3 database, no psql stub
# ------------------------------------------------------------------


class DataLintSqliteTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.checks_dir = self.tmpdir / "checks"
        self.checks_dir.mkdir()

        # Create a small SQLite database with test data.
        self.db_path = self.tmpdir / "test.db"
        conn = _stdlib_sqlite3.connect(str(self.db_path))
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT, val INTEGER)")
        conn.execute("INSERT INTO items VALUES (1, 'alpha', 10)")
        conn.execute("INSERT INTO items VALUES (2, 'beta', -5)")
        conn.execute("INSERT INTO items VALUES (3, 'gamma', 10)")
        conn.execute("INSERT INTO items VALUES (4, 'delta', 0)")
        conn.commit()
        conn.close()

        self.db_url = f"sqlite://{self.db_path}"  # path already starts with /

        self._orig_db_url_env = os.environ.pop("AUDIT_DB_URL", None)

    def tearDown(self):
        if self._orig_db_url_env is not None:
            os.environ["AUDIT_DB_URL"] = self._orig_db_url_env
        else:
            os.environ.pop("AUDIT_DB_URL", None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_check(self, filename: str, sql: str) -> Path:
        p = self.checks_dir / filename
        p.write_text(sql + "\n")
        return p

    def _capture(self, argv: list[str]) -> tuple[int, str]:
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = data_lint.main(argv)
        return rc, out_buf.getvalue()

    def _db_sha256(self) -> str:
        return hashlib.sha256(self.db_path.read_bytes()).hexdigest()

    # ------------------------------------------------------------------

    def test_sqlite_pass_exit_0(self):
        """SELECT returning zero rows → pass, exit 0."""
        self._write_check("001_pass.sql", "SELECT * FROM items WHERE val > 999")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                self.db_url,
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())
        self.assertEqual(data["generated_by"], "data_lint.py")
        self.assertEqual(len(data["checks"]), 1)
        self.assertEqual(data["checks"][0]["status"], "pass")
        self.assertEqual(data["checks"][0]["rows"], 0)
        self.assertEqual(data["checks"][0]["sample"], [])
        self.assertIn("data_lint/001_pass: pass — 0 rows", out)
        self.assertIn("data_lint: clean ->", out)

    def test_sqlite_fail_exit_2_with_sample(self):
        """SELECT returning rows → fail, exit 2, sample in JSON."""
        self._write_check("001_fail.sql", "SELECT * FROM items WHERE val = 10")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                self.db_url,
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 2)
        data = json.loads(json_path.read_text())
        self.assertEqual(len(data["checks"]), 1)
        entry = data["checks"][0]
        self.assertEqual(entry["status"], "fail")
        self.assertEqual(entry["rows"], 2)  # alpha + gamma
        self.assertEqual(len(entry["sample"]), 2)
        # Verify sample is list of {column: value} dicts
        self.assertIsInstance(entry["sample"][0], dict)
        self.assertIn("name", entry["sample"][0])
        self.assertIn("data_lint/001_fail: FAIL — 2 rows", out)
        self.assertIn("data_lint: 1 check(s) failing ->", out)

    def test_sqlite_mixed_pass_fail_exit_2(self):
        """Two checks: one pass, one fail → exit 2, both in JSON."""
        self._write_check("001_pass.sql", "SELECT * FROM items WHERE val > 999")
        self._write_check("002_fail.sql", "SELECT * FROM items WHERE val < 0")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                self.db_url,
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 2)
        data = json.loads(json_path.read_text())
        self.assertEqual(len(data["checks"]), 2)
        self.assertEqual(data["checks"][0]["status"], "pass")
        self.assertEqual(data["checks"][1]["status"], "fail")
        self.assertEqual(data["checks"][1]["rows"], 1)  # beta
        self.assertIn("data_lint/001_pass: pass — 0 rows", out)
        self.assertIn("data_lint/002_fail: FAIL — 1 rows", out)
        self.assertIn("data_lint: 1 check(s) failing ->", out)

    def test_sqlite_max_sample_capped(self):
        """Sample capped at --max-sample, row count is full."""
        self._write_check("001.sql", "SELECT * FROM items")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                self.db_url,
                "--json",
                str(json_path),
                "--max-sample",
                "2",
            ]
        )
        self.assertEqual(rc, 2)  # 4 rows → fail because rows > 0
        data = json.loads(json_path.read_text())
        entry = data["checks"][0]
        self.assertEqual(entry["rows"], 4)
        self.assertEqual(len(entry["sample"]), 2)

    def test_sqlite_write_attempt_infra_failure_and_db_unchanged(self):
        """A check with INSERT fails as infra (read-only engine), db unchanged."""
        db_hash_before = self._db_sha256()

        self._write_check("001_write.sql", "INSERT INTO items VALUES (99, 'bad', 99)")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                self.db_url,
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 3)
        # INFRA-FAIL goes to stderr; rc==3 is sufficient proof of infra failure.
        # The SQLite error is engine-enforced read-only: the write was rejected.

        db_hash_after = self._db_sha256()
        self.assertEqual(db_hash_before, db_hash_after)

    def test_sqlite_no_checks_dir_exits_0(self):
        """Absent checks dir → exit 0, 'no checks configured'."""
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir",
                str(self.tmpdir / "does-not-exist"),
                "--db-url",
                self.db_url,
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("data_lint: no checks configured", out)

    def test_sqlite_empty_checks_dir_exits_0(self):
        """Empty checks dir → exit 0."""
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                self.db_url,
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("data_lint: no checks configured", out)

    def test_sqlite_db_url_from_env_var(self):
        """--db-url absent but AUDIT_DB_URL set → uses env var."""
        self._write_check("001_pass.sql", "SELECT * FROM items WHERE val > 999")
        json_path = self.tmpdir / "out.json"
        os.environ["AUDIT_DB_URL"] = self.db_url
        try:
            rc, out = self._capture(
                [
                    "--checks-dir",
                    str(self.checks_dir),
                    "--json",
                    str(json_path),
                ]
            )
        finally:
            os.environ.pop("AUDIT_DB_URL", None)
        self.assertEqual(rc, 0)

    def test_sqlite_non_existent_db_exits_3(self):
        """Non-existent database file → infra failure (exit 3)."""
        self._write_check("001.sql", "SELECT 1")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                "sqlite:////nonexistent/path/db.sqlite",
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 3)

    def test_sqlite_unsupported_scheme_exits_3(self):
        """Unsupported db-url scheme → infra failure (exit 3)."""
        self._write_check("001.sql", "SELECT 1")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                "mysql://user:pass@host/db",
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 3)

    def test_sqlite_bad_sql_in_check_exits_3(self):
        """Check with invalid SQL → infra failure (exit 3)."""
        self._write_check("001_bad.sql", "SELEC 1")  # typo
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                self.db_url,
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 3)

    def test_sqlite_checks_execute_in_sorted_filename_order(self):
        """Check results appear in sorted filename order."""
        self._write_check("002_b.sql", "SELECT * FROM items WHERE val = 10")
        self._write_check("001_a.sql", "SELECT * FROM items WHERE val > 999")
        self._write_check("003_c.sql", "SELECT * FROM items WHERE val < 0")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                self.db_url,
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 2)
        data = json.loads(json_path.read_text())
        self.assertEqual(
            [c["name"] for c in data["checks"]],
            ["001_a", "002_b", "003_c"],
        )

    def test_sqlite_timeout_returns_infra_failure_and_bundle_stops(self):
        """A slow query with --timeout 1 → infra-failure, bundle stops, <10s wall."""
        db_path = self.tmpdir / "slow.db"
        conn = _stdlib_sqlite3.connect(str(db_path))
        # Create 3 tables, 300 rows each → 27M-row cross join → reliably >1s
        n_rows = 300
        for col, tbl in [("x", "t1"), ("y", "t2"), ("z", "t3")]:
            conn.execute(f"CREATE TABLE {tbl}({col} INTEGER)")
            conn.executemany(
                f"INSERT INTO {tbl} VALUES (?)",
                [(i,) for i in range(n_rows)],
            )
        conn.commit()
        conn.close()

        db_url = f"sqlite://{db_path}"
        self._write_check(
            "001_slow.sql",
            "SELECT sum(t1.x + t2.y + t3.z) FROM t1, t2, t3",
        )
        # Second check that must NOT run (bundle stops on first infra-failure)
        self._write_check("002_fast.sql", "SELECT 1")

        t0 = time.monotonic()
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                db_url,
                "--json",
                str(json_path),
                "--timeout",
                "1",
            ]
        )
        elapsed = time.monotonic() - t0

        self.assertEqual(rc, 3)
        self.assertLess(elapsed, 10.0)
        # Bundle stopped on first check — JSON may not have been written
        # (main returns 3 before reaching _write_json_atomic).
        if json_path.exists():
            data = json.loads(json_path.read_text())
            self.assertLessEqual(len(data["checks"]), 1)

    def test_sqlite_large_result_capped_streaming(self):
        """Large result set: rows==true count, len(sample)==max_sample, fast."""
        db_path = self.tmpdir / "big.db"
        conn = _stdlib_sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE big (id INTEGER PRIMARY KEY, val TEXT)")
        n_rows = 50000
        conn.executemany(
            "INSERT INTO big (val) VALUES (?)",
            [(f"row_{i}",) for i in range(n_rows)],
        )
        conn.commit()
        conn.close()

        db_url = f"sqlite://{db_path}"
        self._write_check("001_big.sql", "SELECT * FROM big")

        max_sample = 5
        t0 = time.monotonic()
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--db-url",
                db_url,
                "--json",
                str(json_path),
                "--max-sample",
                str(max_sample),
            ]
        )
        elapsed = time.monotonic() - t0

        self.assertEqual(rc, 2)
        self.assertLess(elapsed, 5.0)

        data = json.loads(json_path.read_text())
        entry = data["checks"][0]
        self.assertEqual(entry["status"], "fail")
        self.assertEqual(entry["rows"], n_rows)
        self.assertEqual(len(entry["sample"]), max_sample)


if __name__ == "__main__":
    unittest.main()
