# data_lint.py SQLite backend — parked

**Status:** Parked (not a blocker). Raised by the extrends agent 2026-07-04.

## The ask
"Add SQLite support to `scripts/data_lint.py` upstream to unblock per-repo
domain-SQL data checks." extrends wants to write domain data-invariant checks
(`checks/*.sql`) but `data_lint.py` currently speaks Postgres/`psql` only.

## Why it's not a bolt-on
`data_lint.py` is scaffold-managed (edited here, synced downstream), so the
location is correct — but the change is a **backend abstraction**, not an add:

- The load-bearing property is the **server-enforced read-only guarantee** —
  `PGOPTIONS="-c default_transaction_read_only=on"`, documented as "not merely a
  convention" (the D3 guarantee). A SQLite engine must reproduce this via a
  different mechanism (`file:…?mode=ro`, `PRAGMA query_only=ON`) or it's a safety
  regression.
- The runner shells out to `psql --csv -f`, takes Postgres URLs, and its
  timeout/infra-fail model is Postgres-shaped. SQLite needs `sqlite3` with its
  own CSV invocation.
- Cleanest shape: dispatch on the db-url scheme → pluggable engine, each engine
  supplying its own read-only enforcement + CSV invocation.

## Ground truth (checked 2026-07-04)
extrends' **app** DB is Postgres (`pyproject.toml`: `postgres = ["psycopg[binary]"]`),
so the SQLite premise is NOT self-evident — it likely refers to extrends' **SQLite
factstore** (`scripts/_factstore_*_oneoff.py`), a separate store from the Postgres app
DB. Confirm which store the wanted checks target before committing scaffold surface:
if the checks target the Postgres app DB, `data_lint.py` already works and there is no
blocker at all.

## Open premise questions (resolve at explore before building)
1. Which store do the wanted checks target — the SQLite factstore or the Postgres app
   DB? If Postgres, no change is needed. Only a factstore target justifies a SQLite backend.
2. Scaffold-generalize (every repo carries a dual-backend runner) vs. keep
   Postgres-only? Adding a second backend grows the maintained surface for **all**
   downstream repos to serve one — justify the cost.
3. If generalize: MEDIUM change, design-first, read-only enforcement as the hard
   constraint per engine.

## Note
Until resolved, `data_lint.py` is effectively **non-functional on any SQLite-backed
repo** — the audit's domain-SQL layer can't run there. Relevant to the Fable audit
of extrends if extrends is SQLite-backed.
