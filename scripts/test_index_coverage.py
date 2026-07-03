#!/usr/bin/env python3
"""Tests for index_coverage.py — stdlib unittest, no pytest."""

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

import index_coverage  # noqa: E402

_SCHEMA_SQL = """\
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    status TEXT,
    notes TEXT,
    created_at TIMESTAMP,
    region TEXT
);

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE
);

CREATE INDEX idx_orders_customer_region ON orders (customer_id, region);
"""

_QUERIES_SQL = """\
-- indexed leading column filtered in WHERE -> no lead
SELECT * FROM orders WHERE customer_id = 5;

-- unindexed column in WHERE -> lead (where)
SELECT * FROM orders WHERE status = 'active';

-- unindexed column in JOIN ON -> lead (join)
SELECT * FROM orders JOIN customers ON orders.notes = customers.id;

-- unindexed column in ORDER BY -> lead (order_by)
SELECT * FROM orders ORDER BY created_at;

-- composite index's non-leading column used in WHERE -> still a lead
SELECT * FROM orders WHERE region = 'west';
"""

_QUERIES_PY = '''\
import psycopg2


def get_orders(conn, region):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, customer_id
        FROM orders
        WHERE region = %s
        ORDER BY created_at
        """,
        (region,),
    )
    return cur.fetchall()
'''


class IndexCoverageTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.schema_file = self.tmpdir / "schema.sql"
        self.schema_file.write_text(_SCHEMA_SQL)

        self.queries_dir = self.tmpdir / "queries"
        self.queries_dir.mkdir()
        self.sql_query_file = self.queries_dir / "q.sql"
        self.sql_query_file.write_text(_QUERIES_SQL)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _capture(self, argv: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = index_coverage.main(argv)
        return rc, buf.getvalue()

    def _leads_by_key(self, data: dict) -> dict[tuple[str, str], dict]:
        return {(lead["table"], lead["column"]): lead for lead in data["leads"]}

    # ------------------------------------------------------------------

    def test_indexed_leading_column_no_lead_and_unindexed_usages_are_leads(self):
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--schema",
                str(self.schema_file),
                "--queries",
                str(self.queries_dir / "*.sql"),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 0)  # leads present -> still exit 0
        data = json.loads(json_path.read_text())
        self.assertEqual(data["confidence"], "lead")
        by_key = self._leads_by_key(data)

        # Leading indexed column filtered in WHERE -> no lead.
        self.assertNotIn(("orders", "customer_id"), by_key)

        # Unindexed WHERE column -> one lead, usage where.
        self.assertEqual(by_key[("orders", "status")]["usage"], ["where"])

        # Unindexed JOIN ON column -> one lead, usage join. The other side
        # of the join (customers.id) IS a PK leading column -> not a lead.
        self.assertEqual(by_key[("orders", "notes")]["usage"], ["join"])
        self.assertNotIn(("customers", "id"), by_key)

        # Unindexed ORDER BY column -> one lead, usage order_by.
        self.assertEqual(by_key[("orders", "created_at")]["usage"], ["order_by"])

        # Composite index's non-leading column ("region") still a lead.
        self.assertEqual(by_key[("orders", "region")]["usage"], ["where"])

        self.assertGreaterEqual(data["tables_seen"], 2)

    def test_py_literal_extraction_multiline_triple_quoted(self):
        py_query_file = self.queries_dir / "q.py"
        py_query_file.write_text(_QUERIES_PY)
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--schema",
                str(self.schema_file),
                "--queries",
                str(self.queries_dir / "*.py"),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())
        by_key = self._leads_by_key(data)
        self.assertIn(("orders", "region"), by_key)
        self.assertIn(("orders", "created_at"), by_key)
        evidence = by_key[("orders", "region")]["evidence"]
        self.assertTrue(any("q.py" in e for e in evidence))

    def test_empty_query_set_zero_leads_exit_0(self):
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--schema",
                str(self.schema_file),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())
        self.assertEqual(data["leads"], [])
        self.assertIn("index_coverage: 0 leads across 0 tables", out)

    def test_schema_glob_matching_nothing_exits_3(self):
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--schema",
                str(self.tmpdir / "does-not-exist-*.sql"),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 3)

    def test_leads_present_still_exit_0(self):
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--schema",
                str(self.schema_file),
                "--queries",
                str(self.queries_dir / "*.sql"),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())
        self.assertGreater(len(data["leads"]), 0)


# ---------------------------------------------------------------------------
# Alias resolution + unknown-table honesty counter (Defect 2 fix)
# ---------------------------------------------------------------------------

_ALIAS_SCHEMA_SQL = """\
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT
);
"""

_ALIAS_SCHEMA_INDEXED_SQL = """\
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT
);

CREATE INDEX idx_users_email ON users (email);
"""


class AliasResolutionTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.queries_dir = self.tmpdir / "queries"
        self.queries_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _capture(self, argv: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = index_coverage.main(argv)
        return rc, buf.getvalue()

    def _leads_by_key(self, data: dict) -> dict[tuple[str, str], dict]:
        return {(lead["table"], lead["column"]): lead for lead in data["leads"]}

    def _run(self, schema_sql: str, query_sql: str) -> dict:
        schema_file = self.tmpdir / "schema.sql"
        schema_file.write_text(schema_sql)
        query_file = self.queries_dir / "q.sql"
        query_file.write_text(query_sql)
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--schema",
                str(schema_file),
                "--queries",
                str(self.queries_dir / "*.sql"),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        return json.loads(json_path.read_text())

    def test_aliased_unindexed_column_attributed_to_real_table_not_alias(self):
        data = self._run(
            _ALIAS_SCHEMA_SQL,
            "SELECT * FROM users u WHERE u.email = 'x';\n",
        )
        by_key = self._leads_by_key(data)
        # Attributed to the REAL table, not the phantom alias "u".
        self.assertIn(("users", "email"), by_key)
        self.assertNotIn(("u", "email"), by_key)

    def test_aliased_indexed_column_no_lead(self):
        data = self._run(
            _ALIAS_SCHEMA_INDEXED_SQL,
            "SELECT * FROM users u WHERE u.email = 'x';\n",
        )
        by_key = self._leads_by_key(data)
        self.assertNotIn(("users", "email"), by_key)
        self.assertNotIn(("u", "email"), by_key)

    def test_qualified_column_on_table_absent_from_ddl_no_lead_counts_unknown(self):
        data = self._run(
            _ALIAS_SCHEMA_SQL,
            "SELECT * FROM users u WHERE ghost.status = 'active';\n",
        )
        by_key = self._leads_by_key(data)
        self.assertNotIn(("ghost", "status"), by_key)
        self.assertEqual(data["unknown_table_usages"], 1)

    def test_join_alias_resolved_in_on_clause(self):
        schema = """\
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER
);

CREATE TABLE addresses (
    id SERIAL PRIMARY KEY,
    line1 TEXT
);
"""
        query = (
            "SELECT * FROM appointments a "
            "JOIN addresses ad ON a.address_id = ad.id "
            "WHERE ad.line1 = 'x';\n"
        )
        data = self._run(schema, query)
        by_key = self._leads_by_key(data)
        # address_id on "appointments" (aliased "a") is unindexed -> lead
        # attributed to the real table, not to "a".
        self.assertIn(("appointments", "address_id"), by_key)
        self.assertNotIn(("a", "address_id"), by_key)
        # "ad.line1" resolves to "addresses.line1", also unindexed -> lead.
        self.assertIn(("addresses", "line1"), by_key)
        self.assertNotIn(("ad", "line1"), by_key)
        # "ad.id" (join condition's other side) is the PK -> no lead.
        self.assertNotIn(("addresses", "id"), by_key)


# ---------------------------------------------------------------------------
# UPDATE support, right-hand qualified WHERE columns, expression indexes
# (Fixes 3, 4, 5)
# ---------------------------------------------------------------------------


class AnalyzeStatementUnitTest(unittest.TestCase):
    """Direct unit-level checks of `_analyze_statement` for the exact probe
    statements confirmed in the review — no schema/query files needed."""

    def test_update_where_yields_usage(self):
        touched, usages = index_coverage._analyze_statement(
            "UPDATE users SET email = 'x' WHERE user_id = 5;"
        )
        self.assertIn("users", touched)
        self.assertIn(("users", "user_id", "where"), usages)

    def test_update_set_clause_column_not_treated_as_where_usage(self):
        touched, usages = index_coverage._analyze_statement(
            "UPDATE users SET email = 'x' WHERE user_id = 5;"
        )
        self.assertNotIn(("users", "email", "where"), usages)

    def test_where_right_hand_qualified_column_also_captured(self):
        touched, usages = index_coverage._analyze_statement(
            "SELECT * FROM orders o WHERE o.id = b.a_id"
        )
        self.assertIn(("orders", "id", "where"), usages)
        self.assertIn(("b", "a_id", "where"), usages)

    def test_where_qualified_column_not_duplicated(self):
        # "o.id" is captured by BOTH the left-hand `_WHERE_COL_RE` pass and
        # the additional qualified-column pass — must appear only once.
        touched, usages = index_coverage._analyze_statement("SELECT * FROM orders o WHERE o.id = 5")
        self.assertEqual(usages.count(("orders", "id", "where")), 1)


class UpdateStatementEndToEndTest(unittest.TestCase):
    """Fix 3, full pipeline: an UPDATE ... WHERE statement (no FROM) yields
    a lead when the WHERE column is unindexed."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.queries_dir = self.tmpdir / "queries"
        self.queries_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _capture(self, argv: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = index_coverage.main(argv)
        return rc, buf.getvalue()

    def test_update_where_column_unindexed_produces_lead(self):
        schema_file = self.tmpdir / "schema.sql"
        schema_file.write_text(
            "CREATE TABLE users (\n    id SERIAL PRIMARY KEY,\n    email TEXT\n);\n"
        )
        query_file = self.queries_dir / "q.sql"
        query_file.write_text("UPDATE users SET email = 'x' WHERE user_id = 5;\n")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--schema",
                str(schema_file),
                "--queries",
                str(self.queries_dir / "*.sql"),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())
        by_key = {(lead["table"], lead["column"]): lead for lead in data["leads"]}
        self.assertIn(("users", "user_id"), by_key)
        self.assertEqual(by_key[("users", "user_id")]["usage"], ["where"])
        # SET-clause "email" is never treated as a WHERE usage.
        self.assertNotIn(("users", "email"), by_key)


class ExpressionIndexTest(unittest.TestCase):
    """Fix 5: an expression/functional index records NO leading column
    (never the function's own name), so a genuine same-named column still
    produces a lead."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.queries_dir = self.tmpdir / "queries"
        self.queries_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _capture(self, argv: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = index_coverage.main(argv)
        return rc, buf.getvalue()

    def test_functional_index_yields_no_lower_entry_and_real_lower_column_still_leads(self):
        schema_file = self.tmpdir / "schema.sql"
        schema_file.write_text(
            "CREATE TABLE users (\n"
            "    id SERIAL PRIMARY KEY,\n"
            "    email TEXT,\n"
            "    lower TEXT\n"
            ");\n"
            "\n"
            "CREATE INDEX idx_users_email_lower ON users (lower(email));\n"
        )
        leading, known_tables = index_coverage._parse_ddl(schema_file.read_text())
        self.assertNotIn("lower", leading.get("users", set()))

        query_file = self.queries_dir / "q.sql"
        query_file.write_text("SELECT * FROM users WHERE lower = 'x';\n")
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(
            [
                "--schema",
                str(schema_file),
                "--queries",
                str(self.queries_dir / "*.sql"),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())
        by_key = {(lead["table"], lead["column"]): lead for lead in data["leads"]}
        # The genuine "lower" column is NOT falsely suppressed by the
        # mis-parsed function name from the expression index.
        self.assertIn(("users", "lower"), by_key)


if __name__ == "__main__":
    unittest.main()
