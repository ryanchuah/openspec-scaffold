> **Design carrier:** this MEDIUM change has no `design.md`. The architecture decisions (D1–D9) live in
> `openspec/changes/deterministic-tooling-layer/explore-brief.md` (direction-gated `PREMISE: AGREE`, see
> `premise-review.md`) and are pulled forward into the task descriptions below. Where a task and the brief
> conflict, STOP and report — do not improvise. Load-bearing invariants: **check-only, detectors never
> write to code or repo state (D3)**; **JSON-to-disk + one-line stdout summary (D8b)**; **no standing
> generated prose (D1)**. All four scripts are **stdlib-only Python 3.12** (tomllib is stdlib), mirroring
> `scripts/status_lint.py` conventions: module docstring, `main(argv=None) -> int`,
> `if __name__ == "__main__": sys.exit(main())`. Shared exit-code contract (all four scripts):
> **0** = ran clean / no findings, **2** = ran, findings present, **3** = infrastructure failure (tool
> missing, version mismatch, connection/SQL/config error). Tests are **stdlib `unittest`, NOT pytest**,
> matching `scripts/test_status_lint.py` conventions (temp dirs in `setUp`/`tearDown`, import via
> `sys.path.insert`). External binaries are faked in tests with stub executables prepended to `PATH`.

## 1. `scripts/audit_scope.py` — audit bookkeeping, delta scope, hotspots

- [ ] 1.1 Create `scripts/audit_scope.py` with three subcommands. `scan` (default, read-only):
  find the latest `audit/*` git tag (`git tag --list 'audit/*' --sort=-creatordate`, first line); if
  none exists report `"scope": "full"` over all tracked source files; else compute commits-since-tag,
  per-file churn from `git diff --numstat <tag>..HEAD` (churn = insertions + deletions), and per-file
  cyclomatic complexity via a `radon cc -j <path>` subprocess **only if** `radon` is on PATH — when
  absent set `"complexity_available": false` and `complexity: null` per file (graceful degradation; radon
  is pinned in each repo's dev extras, not vendored here). Per-file complexity = the **maximum
  `complexity` value across all block entries** (functions/methods/classes) in radon's JSON output for
  that file (a file with no blocks scores 0). JSON types: `complexity` is a number (0 included) whenever
  radon is available and `null` ONLY when it is not. Hotspot score = churn × (1 + that maximum, or 1 when
  radon is unavailable), ranked descending. Write JSON `{generated_by, tag, anchor_commit,
  commits_since, scope, complexity_available, files: [{path, churn, complexity, hotspot_score}]}` to
  `--json <path>` (default `audit_scope.json` in CWD) and print exactly one stdout summary line:
  `audit_scope: <n> files changed since <tag|full-repo> -> <json-path>`. Exit 0 on success, 3 on git/radon
  subprocess failure.
- [ ] 1.2 `tag --date YYYY-MM-DD` (date required — no implicit "today", keeping runs reproducible):
  create **annotated** tag `audit/<date>` at HEAD (message `audit anchor <date>`); if the tag already
  exists, print an error naming it and exit 3 without touching anything. This is the ONLY mutating
  operation in the entire change and only fires on explicit invocation (D3-compatible bookkeeping).
- [ ] 1.3 `log-line --date YYYY-MM-DD --essence "<free text>"`: PRINT (never write) the audit-log
  registry line in the exact format
  `- **<date>** · audit/<date> · <short-HEAD-sha> · <essence>` — the orchestrator appends it to
  `knowledge/audit-log.md` deliberately; the script stays write-free.
- [ ] 1.4 Create `scripts/test_audit_scope.py` (stdlib unittest). Build a real temp git repo
  (`git init` + commits) in `setUp`. Cover: scan with no `audit/*` tag → `scope: full`, exit 0; scan
  after tagging + further commits → correct changed-file set and churn ordering; radon absent → 
  `complexity_available: false` and hotspot ranking still produced (stub PATH without radon); radon
  stubbed with canned `-j` JSON → complexity merged into hotspot score; `tag` creates an annotated tag
  and a second identical `tag` exits 3; `log-line` output matches the exact registry format; summary
  line format is stable (single line, contains the JSON path).

## 2. `scripts/data_lint.py` — plain-SQL data-invariant runner (D4)

- [ ] 2.1 Create `scripts/data_lint.py`. CLI: `--checks-dir <dir>` (default `checks/`), `--db-url`
  (default from env `AUDIT_DB_URL`; NEVER a baked-in default — missing both → exit 3 with a message
  naming the env var), `--json <path>` (default `data_lint.json`), `--max-sample N` (default 5).
  For each `*.sql` file in the checks dir (**flat directory only, no recursion** — matches the ~5-checks
  D4 scale; state this in the docstring), sorted by name: run
  `psql <db-url> -v ON_ERROR_STOP=1 --csv -f <file>` with `PGOPTIONS="-c default_transaction_read_only=on"`
  merged into the subprocess env — the hard, server-enforced D3 read-only guarantee, present on EVERY
  invocation — and a **subprocess timeout of 120s per check** (`--timeout N` flag to override); a
  timed-out check is an infra failure (exit 3), so a hung connection can never hang a bundle run. Convention (document in module docstring): each check is one SELECT returning violating
  rows; zero rows = pass. Capture per check: row count and the first `--max-sample` rows.
- [ ] 2.2 Output + exit contract: JSON `{generated_by, checks: [{name, status: pass|fail, rows,
  sample}]}`; one stdout summary line per check `data_lint/<name>: <pass|FAIL> — <n> rows` plus one final
  line `data_lint: <clean|N check(s) failing> -> <json-path>`. Missing or empty checks dir → exit 0 with
  summary `data_lint: no checks configured` (repo hasn't adopted yet — not an error). Any psql error
  (missing binary, connection refused, SQL error in a check file) → exit 3 **immediately**
  (stop-on-first-infra-failure; a broken check must fail loudly, never be skipped). All checks pass →
  exit 0; any check returns rows → exit 2.
- [ ] 2.3 Create `scripts/test_data_lint.py` (stdlib unittest, stub `psql` shell script on PATH that
  records its argv/env to a file and emits canned CSV). Cover: `PGOPTIONS` read-only setting present in
  the recorded env of every invocation; `ON_ERROR_STOP=1` and `--csv` present in argv; zero-row CSV → 
  exit 0; violating rows → exit 2 with row count and ≤ max-sample samples in JSON; sample capping at
  `--max-sample`; stub exiting nonzero → exit 3 and NO later check file is executed (order-proof via the
  recording file); no `AUDIT_DB_URL` and no `--db-url` → exit 3; absent checks dir → exit 0 "no checks
  configured"; checks execute in sorted filename order.

## 3. `scripts/index_coverage.py` — static index-coverage leads (audit-time report, never a gate)

- [ ] 3.1 Create `scripts/index_coverage.py`. Inputs: `--schema <path-or-glob>` (DDL text: concatenated
  migrations or `pg_dump --schema-only` output), `--queries <glob>` (repeatable; `*.sql` files taken
  verbatim, `*.py` files scanned best-effort for SQL string literals containing
  `SELECT|UPDATE|DELETE|INSERT`), `--json <path>` (default `index_coverage.json`). Regex-based,
  tolerant parsing (no SQL parser dependency): from DDL collect per-table indexed leading columns
  (CREATE INDEX / PRIMARY KEY / UNIQUE); from queries collect per-table columns appearing in `WHERE`,
  `JOIN ... ON`, and `ORDER BY`. A **lead** = a column used in filters/joins on a table where no index
  has it as the leading column. Leading-column match only — record this limitation in the module
  docstring. An **unparsed statement** = an extracted SQL statement from which the regex pass could
  attribute NO table/column usage at all; these are counted (`unparsed_statements`) so the report is
  honest about its blind spots.
- [ ] 3.2 Output contract: JSON `{generated_by, "confidence": "lead", leads: [{table, column, usage:
  [where|join|order_by], evidence: [<file:line or file>]}], tables_seen, unparsed_statements}` — every
  lead is explicitly a **lead for LLM triage, not ground truth** (f-string/dynamic SQL evades static
  extraction; the brief's §4 caveat). Stdout: one summary line `index_coverage: <n> leads across
  <m> tables -> <json-path>`. Exit 0 when it ran (leads are informational — this check NEVER gates),
  exit 3 only on infra failure (no schema files matched, unreadable input).
- [ ] 3.3 Create `scripts/test_index_coverage.py` (stdlib unittest, fixture DDL + query strings written
  to temp files). Cover: indexed leading column filtered in WHERE → no lead; unindexed column in WHERE /
  JOIN ON / ORDER BY → one lead each with correct usage label; composite index covers only its leading
  column (second column of a composite index still produces a lead); SQL literal extraction from a `.py`
  fixture including a **multi-line triple-quoted SQL string** (the dominant real pattern in raw-psycopg2
  code — the extractor must not pass only on single-line toys); empty query set → zero leads, exit 0; `--schema` glob matching nothing → exit 3; leads
  present → still exit 0.

## 4. `scripts/audit_bundle.py` — check-only orchestrator (D1, D2, D3, D6, D8)

- [ ] 4.1 Create `scripts/audit_bundle.py` skeleton + config loading. Config file: `audit.toml` at the
  repo root (per-repo, NOT scaffold-managed; parsed with stdlib `tomllib`). Absent file → built-in
  defaults with auto-detection (enable a floor check only when its trigger exists: `pyproject.toml` →
  ruff + deptry; `.git/` → gitleaks; any `requirements*.txt`/`poetry.lock`/`uv.lock`/`package-lock.json`
  → osv-scanner; `checks/` dir → data-lint) and `"config": "defaults"` recorded in the run manifest.
  Config schema — documented ONLY in the module docstring + `--help` (self-documenting; no standing doc
  file per D1/knowledge-recoverability rule): `[tools]` version-pin overrides; `[checks.<name>]` with
  `enabled`, `args`, `paths`; `[checks.custom.<name>]` with `command` (argv list), `tier`
  (`floor|heavy|snapshot`), `gate` (bool, **default `true`**: nonzero custom-command exit =
  findings/exit-2 class; `gate = false` = report-only, output captured and the run continues). The
  docstring schema section MUST note the D3 caveat: the bundle cannot prevent a custom `command` from
  writing — keeping custom checks check-only is the configuring repo's responsibility.
- [ ] 4.2 Check registry. Built-in parsed checks (native JSON output → normalized findings
  `{check, rule, path, line?, message}`): **ruff** (`ruff check --output-format json`), **gitleaks**
  (`gitleaks detect --report-format json --no-banner --exit-code 2`), **osv-scanner**
  (`osv-scanner --format json -r .`), **deptry** (`deptry . -o <tmp-json>`), **radon**
  (`radon cc -j`, tier heavy), **jscpd** (`jscpd --reporters json`, tier heavy), **vulture** (line-text
  output parsed by regex, tier heavy). Delegating checks (tier per brief): **data-lint** → runs
  `scripts/data_lint.py` (floor), **index-coverage** → runs `scripts/index_coverage.py` (heavy),
  **scope** → runs `scripts/audit_scope.py scan` (floor). Built-in snapshot check **inventory** (tier
  snapshot, zero-findings semantics): tree of tracked source files + detected entrypoints
  (pyproject scripts/console_scripts, `justfile`/`Makefile` target names, `package.json` scripts) +
  env-var names referenced in source (regex alternation `os\.environ` / `os\.getenv\s*\(` /
  `process\.env` — anchored forms only, so a `my_getenv_wrapper` identifier does not match), as JSON. Everything else
  (eslint, tsc, sqlfluff, alembic-check, pyan3, paracelsus, pg_dump, openapi fetch, schemathesis,
  testmon) is deliberately NOT parsed upstream — downstream repos wire them as `[checks.custom.*]`
  generic commands (stdout captured verbatim to `<check>.txt`, findings-count null) in their follow-on
  SMALL changes. Do not add dedicated parsers for them.
- [ ] 4.3 Availability probes + pinning. Module constant `EXPECTED_TOOL_VERSIONS` pins **binary** tools
  (initially `gitleaks`, `osv-scanner`, `jscpd`; overridable via `[tools]`): before running, probe with
  this exact protocol — run `<tool> --version`; if its exit code is nonzero, run `<tool> version`; if
  both exit nonzero (or the binary is absent), the tool is **unavailable**. From the successful probe's
  combined stdout+stderr, extract the FIRST match of `\d+\.\d+(\.\d+)?` and compare it **exact-string**
  to the pinned value (pins are stored bare, no leading `v`, e.g. `"8.30.1"`). A non-matching or
  unparseable version = **version-mismatch**, failed as infra (exit-3 class) with a message naming
  expected vs found — never run a drifted binary silently. Python-ecosystem tools (ruff, deptry,
  radon, vulture) are pinned in each repo's dev extras, NOT here; the bundle probes them the same way
  (`<tool> --version`, same fallback and regex) but ONLY records the result into the run manifest —
  it never fails on a Python-tool version, and an unprobeable one is recorded as `null`. A tool missing from PATH: in `--report` mode → infra failure
  (stop-on-first-failure); in `--list`/single `--check` mode → reported as `unavailable` without failing
  the listing.
- [ ] 4.4 Modes. `--list`: one line per registered check — `<name>  <tier>  <enabled|disabled>
  <available|unavailable|version-mismatch>` — THE agent discovery surface (D8a), always exit 0.
  `--check <name>`: run exactly one check (query shape, D1). `--floor`: all enabled floor checks; if
  config disables every floor check, exit 0 with summary `audit_bundle: no floor checks enabled`
  (mirrors data_lint's no-checks behavior). `--report --out <dir>` (default
  `output/audit/<YYYY-MM-DD>/`; `--date` optional and defaults to today, pinning the dir name when
  given; an explicit `--out` takes precedence over the date-templated default, in which case `--date`
  only pins the date recorded in the run manifest): floor + heavy + snapshot checks in registry order;
  if `--out` already exists and is non-empty
  and `--resume` was NOT given, refuse with exit 3 and a message suggesting `--resume` or a different
  `--out` (never silently overwrite a prior run's findings); after EACH check
  completes, checkpoint its record into `<out>/run-manifest.json` — kept a single JSON array, rewritten
  atomically each time (write temp file + `os.replace`), NOT streamed-appended (the resumability
  checkpoint per AGENTS.md "make work resumable"); `--resume` skips checks already recorded as completed in an existing
  run-manifest; first infra failure (exit-3 class) ABORTS the run (stop-on-first-failure) — findings
  (exit-2 class) never abort. The bundle NEVER passes `--fix`-style flags and writes only under `--out`
  / the `--json` targets (D3).
- [ ] 4.5 Output contract (D8b). Per check: `<out>/<check>.json` (or `.txt` for custom/unparsed) plus
  exactly one stdout summary line `<check>: <ok|FINDINGS|INFRA-FAIL|skipped> — <n or ?> findings ->
  <artifact-path>`. After a full/floor run: aggregate `findings.json` (all normalized findings) and
  final line `audit_bundle: <n> findings across <m> checks -> <out>`. Exit: 0 no findings, 2 findings
  present, 3 infra failure/abort.
- [ ] 4.6 Baseline diff (D6/D8d). `--baseline <prior-findings.json>` — valid ONLY with `--report`
  (with `--check`/`--floor` it is a usage error, exit 3; a floor-mode baseline is a possible follow-on,
  not v1): fingerprint each finding as
  `sha1("\0".join([check, rule, path, message]))` over the normalized-finding fields from 4.2 — `check` =
  registry check name (e.g. `ruff`), `rule` = the tool's rule/vuln identifier (ruff code, gitleaks rule
  id, osv vuln id; empty string `""` when the tool has none), `path` = repo-relative path, `message` =
  the finding message stripped and with internal whitespace runs collapsed to single spaces. Deliberately
  line-number-insensitive so pure moves don't churn. Write `<out>/delta.json`
  `{new: [...], resolved: [...], unchanged_count}`
  plus summary line `delta: <n> new, <m> resolved vs <baseline-path>`. Exit code is then governed by
  **new** findings only (0 when no new findings even if old ones persist).
- [ ] 4.7 Create `scripts/test_audit_bundle.py` (stdlib unittest; stub executables on PATH emitting
  canned native-format output for ruff/gitleaks/osv-scanner/deptry/vulture/jscpd/radon). Cover:
  `--list` includes every registered check with correct tier and availability (including
  `version-mismatch` when a stub reports a wrong pinned version); defaults auto-detection enables
  exactly the triggered checks in a fixture repo; `audit.toml` parsing incl. a `[checks.custom.x]`
  command captured to `.txt`; normalized-findings shape from each built-in parser fixture;
  version-mismatch → exit 3 in report mode with the expected/found message; missing binary → 
  `unavailable` in `--list` but abort in `--report`; run-manifest appended after each check and
  `--resume` skips completed ones (order-proof); infra failure aborts before later checks run, findings
  do not abort; summary-line and final-line formats; baseline diff: unchanged finding at a shifted line
  number is NOT new (fingerprint insensitivity), removed one is resolved, added one is new, and exit
  code follows new-findings-only; `--report` without `--date` uses today's dir name while `--date` pins
  it.

## 5. Convention docs + manifest (scaffold-local ONLY — downstream sync is deferred, see notes.md)

- [ ] 5.1 In `AGENTS.md` (golden copy, inside the scaffold-managed shared span — i.e. anywhere before
  the per-repo tail; place it between the `## Web research convention` section and the next `##`
  heading, `## Scaffold-managed files & propagation`), add a new
  section `## Deterministic audit tooling` of AT MOST 15 lines containing exactly: (1) the check-only
  rule — audit tooling detects and reports, never writes/fixes (one sentence; no archive citation —
  the archive dir does not exist until this change ships); (2) discovery — run
  `python scripts/audit_bundle.py --list` to enumerate checks;
  per-repo task-runner targets follow an `audit-*` namespace (per-repo, not scaffold-managed); (3) the
  output contract — full JSON to disk, one-line stdout summaries, `output/audit/<date>/` is untracked
  and disposable, regenerated per audit; (4) the audit cycle — bundle `--report` → triage → 
  `audit_scope.py tag` + append the `log-line` output to `knowledge/audit-log.md` → LLM audit uses the
  bundle as its index; (5) the audit-log registry-line format, in-lined verbatim:
  `- **YYYY-MM-DD** · audit/<date> · <short-sha> · <essence>`. After editing, run
  `python scripts/test_sync_scaffold.py` to confirm the span mechanics still pass.
- [ ] 5.2 In `knowledge/README.md` (scaffold-managed), add `knowledge/audit-log.md` to the taxonomy as
  **reference-type** knowledge: a bounded one-line-per-audit registry ledger (same registry-line
  discipline as `knowledge/decisions/INDEX.md`); full audit outputs live untracked under
  `output/audit/<date>/` and are disposable per-audit build artifacts.
- [ ] 5.3 In `scripts/scaffold_manifest.txt` under `# Scripts`, add eight lines — `scripts/audit_bundle.py`,
  `scripts/audit_scope.py`, `scripts/data_lint.py`, `scripts/index_coverage.py`, and their four
  `scripts/test_*.py` files — one repo-relative path per line, alphabetically ordered among the existing
  entries (tests propagate, consistent with `test_status_lint.py`).
- [ ] 5.4 Run the full scaffold suite from the repo root and confirm green: every `scripts/test_*.py`
  (the four new ones plus `test_sync_scaffold.py`, `test_convergence.py`, `test_status_lint.py`,
  `test_executor_body_agreement.py`).
