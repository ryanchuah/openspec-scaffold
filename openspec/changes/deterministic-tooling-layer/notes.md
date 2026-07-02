# deterministic-tooling-layer — notes

**Tier:** MEDIUM (operator-confirmed 2026-07-02). Propose emits `tasks.md` + this `notes.md`;
reviewed by deepseek-v4-pro before freeze; verified (self → pro → flash).
**Apply-executor override (operator, 2026-07-02, this session only):** implementation is delegated to a
**Sonnet subagent** directly, skipping the default deepseek-v4-flash `opencode run` leg of the ladder.

## Context / why
The full background, evidence base, tool roster, and design decisions D1–D9 live in this change's
`explore-brief.md` (direction-gated `PREMISE: AGREE` 2026-07-02, `premise-review.md`) — it is the
**design carrier** for this MEDIUM change. One-paragraph version: both downstream repos have pytest
and nothing else; audit prep burned ~12 LLM sessions on mechanical work scripts can do; agents burn
tokens mid-session on questions static analysis answers for free. This change ships the scaffold-managed
deterministic layer: an audit/check orchestrator, git-archaeology scoping, a plain-SQL data-invariant
runner, and a static index-coverage reporter — check-only, JSON-to-disk, agent-neutral.

## Scope (this change)
- `scripts/audit_bundle.py`, `scripts/audit_scope.py`, `scripts/data_lint.py`,
  `scripts/index_coverage.py` + four stdlib-unittest test files.
- `scaffold_manifest.txt` additions (scripts + tests).
- `AGENTS.md` `## Deterministic audit tooling` section (≤15 lines) + `knowledge/README.md`
  taxonomy entry for `knowledge/audit-log.md` (reference-type registry ledger).

## Non-goals / deliberate exclusions
1. **No downstream propagation in this change.** Operator directive 2026-07-02: NO syncs to extrends
   **or psc-monitor** without explicit go-ahead (another agent was active in extrends). Sync +
   per-repo wiring happen later; nothing in tasks.md touches a downstream repo.
2. **No per-repo configs/wiring** — `audit.toml`, `checks/*.sql`, task-runner `audit-*` targets,
   CI jobs, dev-extras tool pins are follow-on SMALL changes in each downstream repo.
3. **No dedicated parsers for eslint/tsc/sqlfluff/alembic-check/pyan3/paracelsus/schemathesis/
   testmon** — downstream repos wire these as `[checks.custom.*]` generic commands. Parser surface
   upstream stays limited to tools with stable machine output the executor can fixture-test.
4. **No formatters, no `--fix`, nothing that writes to code** (D3). The only mutating operation in
   the whole change is the explicit `audit_scope.py tag` subcommand (annotated git tag).
5. **No LLM pre-digestion tooling** (D2's cheap-model layer is audit-execution procedure, not code)
   and **no standing generated prose/nav docs** (D1; evidence in brief §2).
6. **EXPLAIN-plan regression diffing stays killed** (operator); index coverage ships static-only as
   leads, never a gate.
7. **Running the actual Fable audit** is a later operator-driven session, not this change.

## Design decisions (beyond the brief's D1–D9)
- **Shared exit-code triple** across all four scripts: 0 = clean, 2 = findings, 3 = infra failure.
  Extends the repo's 0/2 lint convention with an explicit findings-vs-infrastructure distinction,
  because stop-on-first-failure (AGENTS.md resumability rule) must trigger on infra failures ONLY —
  findings are results, not failures.
- **`audit.toml` + stdlib `tomllib`** (not YAML) keeps the scripts stdlib-only — same constraint as
  `status_lint.py`. Config schema documented in module docstring + `--help` only (code-derivable →
  not tracked knowledge).
- **Version-pin split:** binary tools pinned in `EXPECTED_TOOL_VERSIONS` inside the bundle (probed
  before every run; mismatch = loud infra failure); Python tools pinned per-repo in dev extras and
  only *recorded* by the bundle. Tool rot therefore always surfaces as a failed run, never silent
  drift — with recovery = bump pin, re-run baseline triage (brief D9).
- **Baseline fingerprints are line-number-insensitive** (sha1 of check/rule/path/normalized message)
  so pure code moves don't churn the delta; exit code follows NEW findings only.
- **`data_lint.py` enforces read-only at the server** (`PGOPTIONS default_transaction_read_only=on`
  on every psql invocation) — D3 as a hard guarantee, not a convention.
- **`audit_scope.py tag` requires an explicit `--date`** — no implicit "today", so re-running a
  documented command is reproducible and can never silently mint a second anchor.

## Acceptance criteria (verify phase checks these; results recorded here at verify)
1. `python scripts/audit_bundle.py --list` in the scaffold repo enumerates every registered check
   with tier and availability, exit 0, without any external tool installed.
2. With stub tools on PATH (as in the test suite): a `--report` run produces `run-manifest.json`
   incrementally, per-check JSON artifacts, `findings.json`, one-line summaries, and the correct
   exit code; killing after check N and re-running `--resume` skips the first N checks; an infra
   failure aborts the run while findings do not.
3. Baseline diff on fixture findings classifies new/resolved/unchanged correctly with a
   line-shifted finding counted as unchanged, and exits 0 when only old findings persist.
4. Every `data_lint.py` psql invocation carries the read-only `PGOPTIONS` (proven by the recording
   stub), and a failing check file aborts before later checks run.
5. `index_coverage.py` on the fixture DDL+queries yields the expected leads with
   `"confidence": "lead"` and exits 0 despite leads being present.
6. `audit_scope.py`: scan/tag/log-line behaviors per tasks 1.1–1.3, including the duplicate-tag
   refusal and the exact registry-line format.
7. Full scaffold suite green (all `scripts/test_*.py`); `AGENTS.md` section ≤15 lines and
   `test_sync_scaffold.py` still green after the span edit; manifest lines present for all eight
   new files.

## Follow-ons (NOT this change)
- **Downstream (after operator sync go-ahead):** sync scaffold; per-repo SMALL changes wiring
  `audit.toml`, `checks/*.sql` (~5 deliberate invariants each, grown from incidents per D4),
  `audit-*` task-runner targets, dev-extras pins, custom checks (eslint/tsc for psc-monitor,
  alembic-check for extrends, sqlfluff for psc-monitor migrations).
- **First audit cycle (operator-driven):** full `--report` run → first-run wall triage ONCE →
  tuned configs + baseline committed downstream → `audit_scope.py tag` + audit-log line → Fable
  audit with the bundle as index. Delta-scoping pays from cycle 2 (brief D6).
- **Dead-code/duplication/complexity triage campaign** (brief D5): one-time cheap-model pre-digest →
  shortlist → operator/Fable rules → vulture whitelist.
- **knowledge-lint change** (`plans/knowledge-lint/`, direction-gated AGREE 2026-07-02): its
  deterministic linter will also cover the `knowledge/audit-log.md` registry format this change
  introduces.
- Delete `../extrends/AUDIT-WORKFLOW-HANDOFF.md` (superseded by the brief) — deferred with the
  extrends sync freeze.
