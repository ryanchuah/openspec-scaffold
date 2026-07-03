#!/usr/bin/env python3
"""index_coverage.py — static index-coverage leads (audit-time report, NEVER a gate).

Regex-based, tolerant parsing — deliberately NOT a SQL parser. From
``--schema`` (DDL text: concatenated migrations, or ``pg_dump
--schema-only`` output) it collects, per table, the set of columns that are
the LEADING column of some index (``CREATE INDEX``, a table-level or
named-constraint ``PRIMARY KEY (...)``/``UNIQUE (...)``, or an inline
single-column ``col TYPE ... PRIMARY KEY`` / ``... UNIQUE`` definition).
From ``--queries`` it collects, per table, the columns used in ``WHERE``,
``JOIN ... ON``, and ``ORDER BY``. A **lead** is a used column whose table
has no index with that column as its LEADING column.

Limitations (read before trusting a lead as ground truth)
-----------------------------------------------------------
* **Leading-column match only.** A composite index ``(a, b)`` covers ONLY
  ``a``; a filter/join/order-by on ``b`` alone is still reported as a lead,
  even though the index exists.
* **f-strings / dynamic SQL evade static extraction entirely** — a query
  built by string concatenation or an f-string is invisible to this
  regexpass. Every lead is therefore a **lead for LLM triage, never ground
  truth** (see the brief's D-index-coverage caveat).
* **WHERE-style joins are classified as "where", not "join"** — this tool
  only recognizes explicit ``JOIN ... ON`` syntax; an old-style
  ``WHERE a.id = b.a_id`` join condition is picked up as two WHERE-column
  usages, not a join usage. That still produces a (possibly duplicate) lead
  if either side is unindexed, just under the "where" label.
* The LEFT-hand comparison target immediately preceding a comparison
  operator is captured per WHERE predicate (``col = value`` style), PLUS
  any QUALIFIED (``table.column``) reference found anywhere else in the
  WHERE clause (so an old-style join's right-hand side, e.g. ``b.a_id`` in
  ``WHERE o.id = b.a_id``, is also picked up). An UNQUALIFIED right-hand
  column, value literals, and function-wrapped columns (``LOWER(email) =
  ...``) are still not extracted.
* An **unparsed statement** is one from which this pass could attribute NO
  table/column usage at all (no WHERE/JOIN-ON/ORDER-BY column found) —
  counted in ``unparsed_statements`` so the report stays honest about its
  blind spots, rather than silently pretending full coverage.
* **Alias resolution is lightweight and per-statement only.** A simple
  ``FROM <table> [AS] <alias>`` or ``JOIN <table> [AS] <alias>`` is resolved
  so a qualified column like ``u.email`` attributes to the real table
  (``users.email``), not to a phantom table literally named ``u``. NOT
  resolved: subquery aliases and CTE names — a qualifier that isn't a
  recognized alias and isn't itself a table named in the DDL falls into
  ``unknown_table_usages`` rather than becoming a (guaranteed-noise) lead.
* **Expression/functional indexes are ignored.** ``CREATE INDEX idx ON t
  (lower(email))`` (or the same shape in a table-level/named-constraint
  ``PRIMARY KEY``/``UNIQUE``) records NO leading column for that index —
  never the function's own name (``lower``) — so a real column that
  happens to share a name with a SQL function is never falsely treated as
  covered.
* **UPDATE support.** ``primary_table`` is derived from ``FROM`` when
  present (``DELETE FROM`` already matches); absent a FROM, it falls back
  to ``UPDATE <table>`` — so a plain ``UPDATE t SET ... WHERE ...`` (no
  FROM clause) still yields WHERE-column usages. SET-clause columns are
  never mistaken for WHERE usages, since the WHERE-clause regex only
  matches text after the literal ``WHERE`` keyword.

CLI
---
``--schema <path-or-glob>`` (required) — DDL source(s), concatenated in
sorted-glob order.
``--queries <glob>`` (repeatable) — ``*.sql`` files are read verbatim;
``*.py`` files are scanned best-effort for SQL string literals (single-line
AND multi-line triple-quoted — the dominant real pattern in raw-psycopg2
code) containing a ``SELECT``/``UPDATE``/``DELETE``/``INSERT`` keyword.
``--json <path>`` (default ``index_coverage.json``) — output path.

Output
------
JSON::

    {
      "generated_by": "index_coverage.py",
      "confidence": "lead",
      "leads": [
        {"table": "...", "column": "...", "usage": ["where", ...],
         "evidence": ["<file>:<line>", ...]}
      ],
      "tables_seen": <int>,
      "unparsed_statements": <int>,
      "unknown_table_usages": <int>
    }

Stdout: one summary line, ``index_coverage: <n> leads across <m> tables ->
<json-path>``.

Exit codes
----------
0  — ran (leads are informational; this check NEVER gates, even with leads
     present).
3  — infra failure: ``--schema`` glob matched nothing, or an input file was
     unreadable.
"""

from __future__ import annotations

import argparse
import glob as glob_module
import json
import os
import re
import sys
from pathlib import Path

GENERATED_BY = "index_coverage.py"


def _write_json_atomic(path: Path, payload) -> None:
    """Write JSON to *path* atomically: full content to ``<path>.tmp``, then
    ``os.replace`` over the destination (matches checks.py's
    ``_write_manifest`` pattern)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)

# ---------------------------------------------------------------------------
# DDL parsing — leading indexed columns per table
# ---------------------------------------------------------------------------

_CREATE_INDEX_RE = re.compile(
    r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?\S+\s+ON\s+(\w+)\s*\(([^)]+)\)",
    re.IGNORECASE,
)

_CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\((.*?)\n\s*\)\s*;",
    re.IGNORECASE | re.DOTALL,
)

_CONSTRAINT_COLS_RE = re.compile(
    r"(?:PRIMARY\s+KEY|UNIQUE)\s*\(([^)]*)\)", re.IGNORECASE
)


_EXPR_INDEX_RE = re.compile(r"^\(?\s*\w+\s*\(")


def _leading_column(col_list: str) -> str | None:
    """First identifier in a comma-separated column list — or ``None`` if
    the first item is an EXPRESSION (an identifier immediately followed by
    ``(``, e.g. the functional/expression index ``lower(email)``).

    An expression index records NO leading column at all, rather than
    misattributing the FUNCTION's own name (``lower``) as though it were a
    real indexed column — that could falsely suppress a genuine lead on a
    column that happens to share a name with a SQL function (see the
    module docstring's expression-index limitations bullet).
    """
    first = col_list.split(",")[0].strip()
    if _EXPR_INDEX_RE.match(first):
        return None
    m = re.match(r"\(?\s*(\w+)", first)
    return m.group(1) if m else first


def _split_top_level_commas(s: str) -> list[str]:
    """Split on commas at paren-depth 0 (so nested `varchar(255)` etc. survive)."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in s:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def _parse_ddl(ddl_text: str) -> tuple[dict[str, set[str]], set[str]]:
    """Return (``{table: {leading_indexed_column, ...}}``, ``{known_table,
    ...}``) from DDL text. ``known_tables`` is every table NAMED in the DDL —
    a CREATE TABLE name or a CREATE INDEX target — even one with zero
    indexed leading columns (which would otherwise be invisible to callers
    relying on ``leading`` alone, since a table absent from `leading` is
    indistinguishable from a table absent from the DDL entirely)."""
    leading: dict[str, set[str]] = {}
    known_tables: set[str] = set()

    for m in _CREATE_INDEX_RE.finditer(ddl_text):
        table, cols = m.group(1), m.group(2)
        col = _leading_column(cols)
        if col is not None:
            leading.setdefault(table, set()).add(col)
        known_tables.add(table)

    for m in _CREATE_TABLE_RE.finditer(ddl_text):
        table, body = m.group(1), m.group(2)
        known_tables.add(table)
        for chunk in _split_top_level_commas(body):
            chunk = chunk.strip()
            if not chunk:
                continue
            cm = _CONSTRAINT_COLS_RE.search(chunk)
            if cm:
                # Table-level or named-constraint PRIMARY KEY(...)/UNIQUE(...).
                col = _leading_column(cm.group(1))
                if col is not None:
                    leading.setdefault(table, set()).add(col)
                continue
            # Plain column definition — check for an inline PRIMARY KEY/UNIQUE.
            tokens = chunk.split(None, 1)
            if not tokens:
                continue
            col_name = tokens[0]
            if re.search(r"\bPRIMARY\s+KEY\b", chunk, re.IGNORECASE) or re.search(
                r"\bUNIQUE\b", chunk, re.IGNORECASE
            ):
                leading.setdefault(table, set()).add(col_name)

    return leading, known_tables


# ---------------------------------------------------------------------------
# Query extraction — *.sql verbatim, *.py best-effort string-literal scan
# ---------------------------------------------------------------------------

_SQL_KEYWORD_RE = re.compile(r"\b(SELECT|UPDATE|DELETE|INSERT)\b", re.IGNORECASE)
_TRIPLE_STR_RE = re.compile(r'("""|\'\'\')(.*?)\1', re.DOTALL)
_SINGLE_STR_RE = re.compile(r'"([^"\n]{1,4000})"|\'([^\'\n]{1,4000})\'')


def _split_sql_statements(text: str) -> list[tuple[str, int]]:
    """Naive `;`-delimited statement split; returns (statement, line_number)."""
    statements: list[tuple[str, int]] = []
    start = 0
    for m in re.finditer(r";", text):
        stmt = text[start : m.start() + 1]
        if stmt.strip():
            line_no = text.count("\n", 0, start) + 1
            statements.append((stmt, line_no))
        start = m.end()
    tail = text[start:]
    if tail.strip():
        line_no = text.count("\n", 0, start) + 1
        statements.append((tail, line_no))
    return statements


def _extract_py_sql_statements(text: str) -> list[tuple[str, int]]:
    """Best-effort extraction of SQL string literals from Python source.

    Handles BOTH multi-line triple-quoted strings (the dominant real
    pattern in raw-psycopg2 code) and single-line quoted strings.
    """
    statements: list[tuple[str, int]] = []
    consumed_spans: list[tuple[int, int]] = []

    for m in _TRIPLE_STR_RE.finditer(text):
        content = m.group(2)
        if _SQL_KEYWORD_RE.search(content):
            line_no = text.count("\n", 0, m.start()) + 1
            statements.append((content, line_no))
        consumed_spans.append(m.span())

    # Blank out triple-quoted spans (preserving newlines, for accurate line
    # numbers) so the single-line scan below can't re-match inside them.
    chars = list(text)
    for start, end in consumed_spans:
        for i in range(start, end):
            if chars[i] != "\n":
                chars[i] = " "
    blanked = "".join(chars)

    for m in _SINGLE_STR_RE.finditer(blanked):
        content = m.group(1) if m.group(1) is not None else m.group(2)
        if content and _SQL_KEYWORD_RE.search(content):
            line_no = blanked.count("\n", 0, m.start()) + 1
            statements.append((content, line_no))

    return statements


# ---------------------------------------------------------------------------
# Statement analysis — table/column usage extraction (WHERE / JOIN ON / ORDER BY)
# ---------------------------------------------------------------------------

# Reserved words that must never be mistaken for an alias token. Needed
# because, unlike `_JOIN_RE` (where a mandatory literal `ON` immediately
# follows the alias slot and forces correct backtracking), `_FROM_RE` has no
# such anchor — without this guard `FROM orders WHERE ...` would capture
# "WHERE" itself as an alias.
_ALIAS_STOPWORDS = (
    r"WHERE|GROUP|ORDER|LIMIT|JOIN|INNER|LEFT|RIGHT|FULL|CROSS|ON|UNION|"
    r"HAVING|SET|VALUES|RETURNING|USING"
)
_FROM_RE = re.compile(
    r"\bFROM\s+(\w+)(?:\s+(?:AS\s+)?(?!(?:" + _ALIAS_STOPWORDS + r")\b)(\w+))?",
    re.IGNORECASE,
)
# ``DELETE FROM`` already matches `_FROM_RE`; `UPDATE <table> SET ...` has no
# `FROM` at all (no alias support needed — an `UPDATE ... AS alias` form is
# rare enough this pass doesn't bother resolving it).
_UPDATE_RE = re.compile(r"\bUPDATE\s+(\w+)", re.IGNORECASE)
_JOIN_RE = re.compile(
    r"\bJOIN\s+(\w+)(?:\s+(?:AS\s+)?(\w+))?\s+ON\s+(.+?)"
    r"(?=\bJOIN\b|\bWHERE\b|\bGROUP\s+BY\b|\bORDER\s+BY\b|\bLIMIT\b|;|$)",
    re.IGNORECASE | re.DOTALL,
)
_WHERE_RE = re.compile(
    r"\bWHERE\s+(.+?)(?=\bGROUP\s+BY\b|\bORDER\s+BY\b|\bLIMIT\b|;|$)",
    re.IGNORECASE | re.DOTALL,
)
_ORDER_BY_RE = re.compile(
    r"\bORDER\s+BY\s+(.+?)(?=\bLIMIT\b|;|$)", re.IGNORECASE | re.DOTALL
)
_QUALIFIED_COL_RE = re.compile(r"(\w+)\.(\w+)")
_WHERE_COL_RE = re.compile(
    r"(?:(\w+)\.)?(\w+)\s*(?:=|<>|!=|<=|>=|<|>|\bLIKE\b|\bIN\b|\bIS\b)",
    re.IGNORECASE,
)


def _parse_order_by(text: str) -> list[tuple[str | None, str]]:
    cols: list[tuple[str | None, str]] = []
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        item = re.sub(r"\b(ASC|DESC)\b", "", item, flags=re.IGNORECASE).strip()
        item = re.sub(r"\bNULLS\s+(FIRST|LAST)\b", "", item, flags=re.IGNORECASE).strip()
        m = re.match(r"(?:(\w+)\.)?(\w+)", item)
        if m:
            cols.append((m.group(1), m.group(2)))
    return cols


def _strip_sql_line_comments(text: str) -> str:
    """Strip `-- ...` line comments so keyword text inside them (e.g. a
    comment literally containing the words "ORDER BY") can't be
    misattributed as real clause content by the tolerant regex pass below.
    """
    return re.sub(r"--[^\n]*", "", text)


def _analyze_statement(stmt: str) -> tuple[set[str], list[tuple[str, str, str]]]:
    """Return ``(tables_touched, [(table, column, usage), ...])`` for one
    statement. Qualified-column qualifiers are resolved through a
    single-statement-scoped alias map (built from ``FROM <table> [AS]
    <alias>`` / ``JOIN <table> [AS] <alias>``) BEFORE being attributed as
    table usage — so ``u.email`` under ``FROM users u`` attributes to
    ``users``, not to a phantom table literally named ``u``. A qualifier not
    in the alias map passes through unchanged (it may already be the real
    table name, or it may be genuinely unknown — the caller decides that via
    the DDL-derived known-tables set)."""
    stmt = _strip_sql_line_comments(stmt)
    usages: list[tuple[str, str, str]] = []
    tables_touched: set[str] = set()
    alias_map: dict[str, str] = {}

    from_m = _FROM_RE.search(stmt)
    primary_table = from_m.group(1) if from_m else None
    if primary_table:
        tables_touched.add(primary_table)
        if from_m.group(2):
            alias_map[from_m.group(2)] = primary_table
    else:
        # No FROM (``DELETE FROM`` already matches `_FROM_RE` above) — an
        # `UPDATE <table> SET ... [WHERE ...]` statement has no FROM at all,
        # so derive the primary table from UPDATE instead.
        update_m = _UPDATE_RE.search(stmt)
        if update_m:
            primary_table = update_m.group(1)
            tables_touched.add(primary_table)

    for jm in _JOIN_RE.finditer(stmt):
        join_table = jm.group(1)
        join_alias = jm.group(2)
        on_text = jm.group(3)
        tables_touched.add(join_table)
        if join_alias:
            alias_map[join_alias] = join_table
        for qm in _QUALIFIED_COL_RE.finditer(on_text):
            resolved = alias_map.get(qm.group(1), qm.group(1))
            usages.append((resolved, qm.group(2), "join"))
            tables_touched.add(resolved)

    where_m = _WHERE_RE.search(stmt)
    if where_m:
        where_text = where_m.group(1)
        seen_where_pairs: set[tuple[str, str]] = set()
        for wm in _WHERE_COL_RE.finditer(where_text):
            qualifier = wm.group(1)
            table = alias_map.get(qualifier, qualifier) if qualifier else primary_table
            if table:
                usages.append((table, wm.group(2), "where"))
                tables_touched.add(table)
                seen_where_pairs.add((table, wm.group(2)))
        # `_WHERE_COL_RE` only captures the LEFT-hand side of a comparison
        # (the identifier immediately before an operator) — an old-style
        # join condition's RIGHT-hand side (``... WHERE o.id = b.a_id``,
        # the ``b.a_id`` half) is otherwise dropped entirely. Additionally
        # scan the whole WHERE text for ANY qualified column (like the
        # JOIN-ON handling above), alias-resolved and deduplicated against
        # what `_WHERE_COL_RE` already captured.
        for qm in _QUALIFIED_COL_RE.finditer(where_text):
            resolved = alias_map.get(qm.group(1), qm.group(1))
            pair = (resolved, qm.group(2))
            if pair in seen_where_pairs:
                continue
            usages.append((resolved, qm.group(2), "where"))
            tables_touched.add(resolved)
            seen_where_pairs.add(pair)

    ob_m = _ORDER_BY_RE.search(stmt)
    if ob_m:
        for qualifier, col in _parse_order_by(ob_m.group(1)):
            table = alias_map.get(qualifier, qualifier) if qualifier else primary_table
            if table:
                usages.append((table, col, "order_by"))
                tables_touched.add(table)

    return tables_touched, usages


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Static index-coverage leads (audit-time report, never a gate)."
    )
    parser.add_argument(
        "--schema", required=True, help="DDL path or glob (concatenated, sorted)."
    )
    parser.add_argument(
        "--queries",
        action="append",
        default=[],
        help="Query glob (*.sql verbatim, *.py best-effort). Repeatable.",
    )
    parser.add_argument("--json", default="index_coverage.json", help="Output JSON path.")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    schema_files = sorted(glob_module.glob(args.schema, recursive=True))
    if not schema_files:
        print(
            f"index_coverage: INFRA-FAIL — --schema glob matched no files: {args.schema}",
            file=sys.stderr,
        )
        return 3

    try:
        ddl_text = "\n".join(Path(p).read_text(encoding="utf-8") for p in schema_files)
    except OSError as exc:
        print(f"index_coverage: INFRA-FAIL — could not read schema input: {exc}", file=sys.stderr)
        return 3

    ddl_leading, known_tables = _parse_ddl(ddl_text)

    query_files: list[str] = []
    for pattern in args.queries:
        query_files.extend(sorted(glob_module.glob(pattern, recursive=True)))

    all_statements: list[tuple[str, str, int]] = []  # (file, statement_text, line_no)
    try:
        for qf in query_files:
            suffix = Path(qf).suffix.lower()
            text = Path(qf).read_text(encoding="utf-8")
            if suffix == ".sql":
                for stmt, line_no in _split_sql_statements(text):
                    all_statements.append((qf, stmt, line_no))
            elif suffix == ".py":
                for stmt, line_no in _extract_py_sql_statements(text):
                    all_statements.append((qf, stmt, line_no))
    except OSError as exc:
        print(f"index_coverage: INFRA-FAIL — could not read query input: {exc}", file=sys.stderr)
        return 3

    tables_seen: set[str] = set()
    lead_usage: dict[tuple[str, str], set[str]] = {}
    lead_evidence: dict[tuple[str, str], list[str]] = {}
    unparsed_statements = 0
    unknown_table_usages = 0

    for file_path, stmt, line_no in all_statements:
        touched, usages = _analyze_statement(stmt)
        tables_seen |= touched
        if not usages:
            unparsed_statements += 1
            continue
        for table, column, usage in usages:
            if table not in known_tables:
                # Not a CREATE TABLE name or CREATE INDEX target anywhere in
                # the DDL — a subquery alias, CTE name, or genuinely unknown
                # table. Never a lead (a phantom table can't match any real
                # index); counted instead so the report stays honest about
                # schema-glob gaps rather than flooding leads with noise.
                unknown_table_usages += 1
                continue
            if column in ddl_leading.get(table, set()):
                continue  # covered by an index's leading column
            key = (table, column)
            lead_usage.setdefault(key, set()).add(usage)
            lead_evidence.setdefault(key, []).append(f"{file_path}:{line_no}")

    leads = [
        {
            "table": table,
            "column": column,
            "usage": sorted(lead_usage[(table, column)]),
            "evidence": lead_evidence[(table, column)],
        }
        for table, column in sorted(lead_usage)
    ]

    payload = {
        "generated_by": GENERATED_BY,
        "confidence": "lead",
        "leads": leads,
        "tables_seen": len(tables_seen),
        "unparsed_statements": unparsed_statements,
        "unknown_table_usages": unknown_table_usages,
    }

    json_path = Path(args.json)
    _write_json_atomic(json_path, payload)

    print(
        f"index_coverage: {len(leads)} leads across {len(tables_seen)} tables -> {json_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
