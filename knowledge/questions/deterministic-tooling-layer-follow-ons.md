# deterministic-tooling-layer follow-ons

Parked from `openspec/changes/archive/2026-07-02-deterministic-tooling-layer/notes.md`
(field-5 "Forward-looking items" + "Follow-ons (NOT this change)"). None of these are active
blockers — all are deferred, monitored, or gated behind a later operator action.

## From the verify checkpoint (field 5)

- **First-downstream-run risk:** the gitleaks/osv-scanner/deptry/jscpd parsers are validated
  against web-verified schemas + stubs only — no live binary has run them yet. The first
  downstream `--report` run is the real integration test. Tool-version pins are recorded in
  `EXPECTED_TOOL_VERSIONS` and were current 2026-07-02; they will rot over time. Recovery loop:
  bump the pin, then re-run baseline triage (brief D9).
- **`data_lint.py` live-DB validation pending:** no Postgres exists in this repo; the first
  psc-monitor adoption run is what actually validates it. Downstream convention to set: check SQL
  should `LIMIT` its violating-row `SELECT` (the runner caps the recorded sample but still fetches
  the full result to count rows).
- **`data_lint.py` credential hygiene:** the db-url currently rides in `psql` argv (visible in the
  process list). Downstream convention should prefer PG env vars / pgpass over URL-embedded
  credentials.
- **`index_coverage.py` next increment:** CTE/subquery aliases remain unresolved and land in
  `unknown_table_usages` — still sizeable on real code. Resolve only if the leads prove valuable in
  the first audit; this session's real psc-monitor leads output could seed that first triage.
- **Deferred structure refactor (follow-on SMALL):** single-writer artifact refactor (kills a
  double/triple write), `_mode_multi` decomposition (radon rates it rank E — the layer's own
  finding), status-string constants, test-helper dedup. Details in the archived `review-log.md`.
- **Vulture whitelist campaign seeds (D5):** `conftest.py`'s `collect_ignore` (pytest magic) and
  one unused unpacked test variable — deliberately left as seed material for the future campaign.
- **`--floor` writes artifacts to CWD** (recorded apply deviation) — fine for agent use today, but
  a default scratch-dir convention may be nicer; revisit at downstream wiring time.
- **knowledge-lint tie-in:** `knowledge_lint.py` shipped (2026-07-02) and covers the audit-log
  registry check. A further, still-unbuilt idea — detecting count-recording patterns ("N tests
  pass"-style tallies) in tracked docs — is now tracked in
  `knowledge/questions/knowledge-lint-follow-ons.md`.
- **Cosmetic:** the uniform summary line labels scope's informational file count as "findings";
  harmless but mildly confusing — reconsider the wording in the follow-on refactor.

## Follow-ons (not this change), all frozen pending operator downstream-sync go-ahead

- **Downstream wiring (after operator sync go-ahead):** sync the scaffold, then per-repo SMALL
  changes wiring `audit.toml`, `checks/*.sql` (~5 deliberate invariants each, grown from incidents
  per D4), `audit-*` task-runner targets, dev-extras pins, and custom checks (eslint/tsc for
  psc-monitor, alembic-check for extrends, sqlfluff for psc-monitor migrations).
- **First audit cycle (operator-driven):** a full `--report` run, a first-run wall triage (once),
  tuned configs + a committed baseline downstream, then `audit_scope.py tag` + an audit-log line,
  followed by a Fable audit using the bundle as an index. Delta-scoping only pays off from cycle 2
  onward (brief D6).
- **Dead-code/duplication/complexity triage campaign** (brief D5): one-time cheap-model pre-digest
  → shortlist → operator/Fable rules → vulture whitelist.
- **knowledge-lint** shipped (2026-07-02, `openspec/changes/archive/2026-07-02-knowledge-lint/`): its
  deterministic linter now covers the `knowledge/audit-log.md` registry format this change introduces;
  see `knowledge/questions/knowledge-lint-follow-ons.md` for the still-open latent-check item (untested
  until a repo grows a real `audit-log.md`).
- Delete `../extrends/AUDIT-WORKFLOW-HANDOFF.md` (superseded by the brief) — deferred along with
  the extrends sync freeze.
