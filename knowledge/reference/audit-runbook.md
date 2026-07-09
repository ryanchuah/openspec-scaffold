# Deterministic-audit runbook (for the Fable end-to-end audit)

The deterministic tooling to run **before and alongside** an LLM audit of a downstream
repo (extrends, psc-monitor). These surfaces produce the on-disk artifacts the Fable LLM
uses as its **index** — the LLM spends judgment reading findings, not re-deriving them.
All scripts are scaffold-managed and present in both repos. Exit-code semantics:
`knowledge/reference/exit-codes.md`. Scanner provisioning: `security-scanners.md`.

## 0. Preconditions (do these first or the run has silent holes)

1. **PATH must carry `$(go env GOPATH)/bin`** (`~/go/bin`) if any go-installed scanner
   (gitleaks/osv) is enabled. **Non-interactive shells do NOT get it** from `~/.bashrc`
   (interactivity guard returns before the export) — export it explicitly for cron/CI/
   `opencode run`, or `checks.py` preflight exits **3**. See
   `knowledge/questions/scanner-provisioning-gaps.md`.
   ```bash
   export PATH="$(go env GOPATH)/bin:$PATH"   # e.g. ~/go/bin
   ```
2. **Activate the repo venv** (or use the task-runner targets, which prepend `.venv/bin`).
3. **`AUDIT_DB_URL`** must point at a **read-only-safe** Postgres DSN if `data-lint` is
   enabled (psc-monitor). `data_lint.py` forces `default_transaction_read_only=on`, but
   still point it at a replica/read role.

## 1. Is it green right now? — `scripts/check.sh`
The single definition of green: `ruff check` + `ruff format --check` + the repo test
command. Run first; a red gate means findings downstream may be noise.
```bash
bash scripts/check.sh
```

## 2. Detector bundle — `scripts/checks.py` (the audit index)
Findings-capable detectors, gated by the repo's `checks.toml`. Preflight computes tool
availability for every *enabled* check and exits 3 with a self-explaining line per gap.
```bash
just audit-list      # extrends   (Makefile: `make audit-list` on psc)
just audit-report    # → output/checks/<date>/  ... this dated bundle is Fable's index
```
- extrends targets: `just audit-floor` / `just audit-report` (justfile).
- psc-monitor targets: `make audit-floor` / `make audit-report` (Makefile).
- Raw form (either repo): `.venv/bin/python scripts/checks.py --report`.

## 3. Orientation snapshots — `scripts/facts.py`
Undated, regenerate-on-use, never fails. Cheap lay-of-the-land for the LLM.
```bash
.venv/bin/python scripts/facts.py       # → output/facts/
```

## 4. Domain data invariants — `scripts/data_lint.py`
Runs each `checks/*.sql` as a violating-rows SELECT (zero rows = pass). Needs
`AUDIT_DB_URL`. **Postgres-only today.**
```bash
.venv/bin/python scripts/data_lint.py   # honored via checks.py when [checks.data-lint] enabled
```

## 5. Doc-tree integrity — `knowledge_lint.py` + `status_lint.py`
Deterministic structural lints (citations, stale refs, STATUS structure). Pair with the
**`knowledge-drift-review`** skill for the semantic layer they can't see (LLM, not deterministic).
```bash
.venv/bin/python scripts/knowledge_lint.py
.venv/bin/python scripts/status_lint.py
```

## 6. Scaffold-drift check — run FROM the scaffold repo, not downstream
Downstream repos don't carry `sync_scaffold.py`. From `openspec-scaffold/`:
```bash
python3 scripts/sync_scaffold.py --check <repo>        # exit 0 = converged
python3 scripts/sync_scaffold.py --check-refs <repo>
```

## Per-repo state (2026-07-04, after each repo wired its audit layer)

| Surface | extrends | psc-monitor |
|---|---|---|
| `check.sh` gate | ✅ | ✅ |
| `checks.py` / task targets | ✅ `just audit-*` | ✅ `make audit-*` |
| gitleaks | ✅ enabled (pinned **release** binary) | ✅ enabled |
| osv-scanner | idle — no lockfile (auto-enables when one appears) | idle — no root lockfile |
| deptry | enabled (pip dev-extra) | off (no dev-extra) |
| `data-lint` | ❌ off — repo DB is **SQLite** (blocked on upstream data_lint SQLite backend) | ✅ 4 Postgres invariants live |
| `knowledge_lint`/`status_lint` | ✅ | ✅ |

## Known gaps the deterministic layer will NOT cover
- **extrends domain-SQL data checks** — blocked until `data_lint.py` gets a SQLite
  backend (`knowledge/questions/data-lint-sqlite-backend.md`). The LLM must eyeball
  extrends data invariants by hand meanwhile.
- **gitleaks version pin** re-breaks if `install-tools.sh` is re-run over the release
  binary (`knowledge/questions/scanner-provisioning-gaps.md`, Gap 1).
- **Prior-art oneoffs** (`scripts/_audit_*_oneoff.py` in both repos: dup, flakiness,
  weak-assertions, mocks, coverage, history) are re-runnable test-quality probes the LLM
  can crib from — per-repo, not standardized.
