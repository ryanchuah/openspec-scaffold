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

## As-built deviations (apply, 2026-07-02 — Sonnet executor per the override above; scrutinize at verify)
Executor web-verified (2026-07-02, via fetch) the real output schemas/flags of every parsed tool
(ruff JSON diagnostics, gitleaks Finding + required `--report-path`, osv-scanner results schema,
deptry `-o` reporter, radon `cc_to_dict`, jscpd JSON reporter path, vulture text-line format) and the
three binary pins (gitleaks 8.30.1, osv-scanner 2.4.0, jscpd 5.0.11) — invocation argv includes flags
the tasks' illustrative commands omitted. Gap-filling decisions, all documented in module docstrings:
1. Heavy-tier checks default DISABLED absent `audit.toml` (D8e on-demand; index-coverage has no sane
   default `--schema`); `scope`/`inventory` unconditionally enabled (no external dependency).
2. The non-empty-`--out` refusal applies to `--report` only (task wording scopes it there); `--floor`
   writes to CWD like the individual scripts.
3. radon findings threshold: blocks ranked D/E/F flagged (tasks gave no numeric threshold).
4. Run-manifest = single JSON array whose first element is `{"meta": true, config, date}`, and builtin
   check records carry a `"version"` field (reconciles 4.1's config-recording with 4.4's array contract
   and 4.3's record-only Python-tool probes).
5. `--resume` RETRIES a prior `INFRA-FAIL` record rather than skipping it (the skip reading would
   defeat resume's purpose).
Verify should scrutinize: the built argv for gitleaks/osv-scanner/deptry/radon/jscpd/vulture vs brief
§4; `index_coverage.py`'s tolerant regex extraction (misses under-represented by fixtures); inline
single-column PRIMARY KEY/UNIQUE parsing is handled but only exercised via the composite-index test.

## Verify checkpoint (2026-07-02)

**1. Verdict: READY FOR ARCHIVE.** Pass chain: self-review (Fable orchestrator; full read of all four
scripts + live probes) → deepseek-v4-pro verifier READY → deepseek-v4-flash verifier READY →
simplicity/quality gate (8-angle code-review harness) → flash re-run over the post-gate tree READY.
Full suite green on every re-verification. Security (recommended pass for MEDIUM): focused review
clean — every subprocess is list-argv (no shell=True, no eval), data_lint's read-only guarantee is
server-enforced per invocation, custom-check execution is repo-trusted config by documented design.

**2. Live output eyeballed (behavior, not counts):** real ruff findings flowed through `--report` into
normalized repo-relative JSON and a correct baseline delta (a removed unused-import came back
resolved; line-shifted findings counted unchanged; exit followed new-findings-only). Real
radon/vulture runs on this repo's own code surfaced the bundle orchestrator function as a
complexity hotspot (honest dogfood) and a pytest-magic false positive (whitelist-campaign
material). `index_coverage` against real psc-monitor migrations+code produced plausible per-table
leads with honest unparsed/unknown counters after the alias fix. Full-scope scan with real radon
completes in well under a second after batching (was ~17s per-file).

**3. Defects found and fixed (all fixes by fresh Sonnet fix-executors per the operator override;
every fix re-verified by re-running the probe that exposed it):**
- Self-review pass: findings paths stored absolute (breaking the repo-relative fingerprint contract
  and baseline portability); index_coverage alias phantom-table noise. Both fixed + tests.
- Simplicity/quality gate: git-rename numstat mishandling; per-file radon subprocess spawn
  (floor-contract violation); UPDATE-statement extraction gap; dropped RHS join columns;
  expression-index misparse; TOML scalar/list config footguns; missing delegate error capture in
  run-manifest; repo-root/CWD divergence from a subdirectory. All fixed + tests. Doc fixes by the
  orchestrator directly: AGENTS.md check-only wording precision; count-tally scrub in review-log.
- Pro and both flash verifier passes: zero defects.

**4. As-built deltas beyond the apply-phase section above:** `index_coverage` gained alias
resolution + an `unknown_table_usages` JSON field (contract extension) and UPDATE/RHS-join/
expression-index handling; `audit_scope` parses rename syntax and batch-invokes radon;
`audit_bundle` resolves repo_root via git toplevel (CWD fallback), coerces scalar TOML values,
errors on multi-entry data-lint `paths`, and records delegate stderr in INFRA-FAIL manifest
records; JSON artifact writes are atomic in all three delegate scripts.

**5. Forward-looking items (recorded nowhere else — fold into knowledge/questions at archive):**
- **First-downstream-run risk:** gitleaks/osv-scanner/deptry/jscpd parsers are validated against
  web-verified schemas + stubs only — no live binary has run them. The first downstream `--report`
  is the real integration test; pins (recorded in `EXPECTED_TOOL_VERSIONS`) were current 2026-07-02
  and will rot — recovery loop is bump-pin → re-baseline (brief D9).
- **data_lint live-DB validation pending:** no Postgres exists here; first psc-monitor adoption run
  validates it. Convention to set downstream: check SQL should `LIMIT` its violating-row SELECT
  (the runner caps the recorded sample but must fetch the full result to count rows).
- **data_lint credential hygiene:** the db-url rides in psql argv (visible in the process list);
  downstream convention should prefer PG env vars / pgpass over URL-embedded credentials.
- **index_coverage next increment:** CTE/subquery aliases remain unresolved (land in
  `unknown_table_usages`, still sizeable on real code); resolve only if leads prove valuable in the
  first audit. This session's real psc-monitor leads output could seed that first triage.
- **Deferred structure refactor (follow-on SMALL):** single-writer artifact refactor (kills a
  double/triple write), `_mode_multi` decomposition (radon rates it rank E — the layer's own
  finding), status-string constants, test-helper dedup. Details in review-log.
- **Vulture whitelist campaign seeds (D5):** `conftest.py collect_ignore` (pytest magic) and one
  unused unpacked test variable — deliberately left.
- **`--floor` writes artifacts to CWD** (recorded apply deviation) — fine for agents, but a default
  scratch-dir convention may be nicer; revisit at downstream wiring.
- **knowledge-lint tie-in (new):** beyond the audit-log registry check already in its brief, the
  future `knowledge_lint.py` should detect count-recording patterns ("N tests pass"-style tallies)
  in tracked docs — this session hit that exact rake via verbatim-appended verifier evidence.
- **Cosmetic:** the uniform summary line labels scope's informational file count as "findings";
  harmless but mildly confusing — reconsider wording in the follow-on refactor.

**Still owned by archive:** reconcile `knowledge/STATUS.md` (new change section, cap rule),
`knowledge/decisions/INDEX.md` (registry line → archive dir), `knowledge/questions/INDEX.md`
(fold field-5 items above into Active/Parked as appropriate); no delta specs exist to promote
(MEDIUM, tasks-only — decide at archive whether the audit-tooling conventions warrant a capability
spec); cleanup: none in this repo (downstream sync + `../extrends/AUDIT-WORKFLOW-HANDOFF.md`
deletion stay frozen pending operator go-ahead; the root `knowledge-doc-drift-analysis.md` copy is
the knowledge-lint change's cleanup, not this one's).

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
