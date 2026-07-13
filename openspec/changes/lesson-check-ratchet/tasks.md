# Tasks — lesson-check-ratchet

Apply-phase implementation work only. Work top to bottom; check off each task as it lands.
Acceptance criteria live in design.md § Verification; verify/archive steps are not listed
here.

## 1. Invariant runner

- [x] 1.1 Create `scripts/repo_lint.py` (stdlib-only): discover checks via flat sorted
      `checks/*.py` glob (no recursion); run each as `sys.executable <file> <repo-root>`
      in a subprocess with per-check timeout (default 120s, `--timeout`); parse stdout as
      a JSON array of `{"path","line","message"}` findings (empty = pass); treat nonzero
      exit, timeout, or unparseable stdout as INFRA-FAIL and stop at the FIRST such
      failure (no later file runs); write `repo_lint.json` atomically (`--json`, default
      `repo_lint.json`) with `generated_by` and per-check `{name, status, findings,
      sample}` where `sample` is capped at `--max-sample` (default 5) but `findings`
      holds the full count; CLI flags `--checks-dir` (default `checks`), `--json`,
      `--timeout`, `--max-sample`; exit 0 clean / 2 findings / 3 infra; no `*.py` files →
      print "repo_lint: no checks configured", write empty-checks JSON, exit 0. Module
      docstring documents: the check-file contract with a ~10-line example, the
      check-only caveat adapted from `checks.py`'s custom-checks docstring section
      ("the engine cannot prevent a custom command from writing to the repo — keeping a
      custom check check-only is the CONFIGURING repo's responsibility", ~lines 67–70 —
      NOT design.md's decision D3), the near-zero-false-positive + actionable-fix
      admission bar, the target scale (~5–15 invariants grown from incidents), and the
      graduation path (external engine such as ast-grep via `[checks.custom.*]`).
- [x] 1.2 Create `scripts/test_repo_lint.py` (fixture-based, tmp_path): clean check →
      exit 0; finding-emitting check → exit 2 with correct count and capped sample;
      non-JSON stdout → exit 3; nonzero-exit check → exit 3; `test_stops_on_first_infra_failure`
      (a later sorted check file is NOT executed after an earlier infra failure — assert
      via a sentinel side-effect file the later check would have written); hung check
      killed at `--timeout` → exit 3; absent/empty checks dir → exit 0 with
      "no checks configured"; sorted execution order; JSON artifact schema fields present.

## 2. Engine registration

- [x] 2.1 Register `repo-lint` in `scripts/checks.py`: registry entry (tier `floor`,
      kind `delegate`, family `check`) placed directly after `data-lint`; update
      `_autodetect_defaults()` (~line 279) to return True for `repo-lint` when any
      `checks/*.py` exists — same function, same shape as the existing `has_checks`
      `*.sql` gate at ~line 284 (a separate `*.py` glob, NOT reusing the sql boolean);
      add trigger/coverage_note strings; config `[checks.repo-lint]` honoring `enabled`
      and `paths` (FIRST entry = checks dir; a second entry = explicit INFRA-FAIL, the
      data-lint rule); invoke by importing `repo_lint` and calling `repo_lint.main()`
      in-process with `--json <out>/repo_lint.json` and `--checks-dir <dir>`, then read
      the JSON artifact for count/status (copy the `data-lint` delegate block's shape);
      findings NOT merged into aggregate `findings.json`; update the module docstring's
      registry/trigger documentation.
- [x] 2.2 Extend `scripts/test_checks.py` (note: this file uses `unittest` + fake shell
      stubs, not bare pytest style — follow its existing conventions): `--list` shows
      `repo-lint`; auto-enabled iff `checks/*.py` exists (and not when only `*.sql`
      exist); `[checks.repo-lint] enabled = false` respected; second `paths` entry
      INFRA-FAILs; delegate run surfaces exit-2 findings as FINDINGS status.

## 3. Ledger lint

- [x] 3.1 Add `_check_ratchet_log(root)` to `scripts/knowledge_lint.py`, guarded on
      `knowledge/ratchet-log.md` existence (absent → no findings, the `_check_audit_log`
      guard shape). Validate per entry line: registry-line format
      `- **YYYY-MM-DD** · <kebab-slug> · <disposition> — <essence>`; disposition is
      exactly one of `check:<pointer>` / `test:<path>[::<name>]` /
      `waiver:review-by YYYY-MM-DD` / `open:since YYYY-MM-DD` / `grandfathered`; all
      dates are real ISO calendar dates (reject `2026-13-01`); `check:`/`test:` pointer
      file exists and, when a `::<name>` suffix is present, `<name>` appears textually in
      the file (bare path = existence only); `waiver` has non-empty essence (reason) and
      review-by not past; `open` older than `ratchet_open_max_age_days` (read from
      `checks.toml` `[knowledge_lint]`, default 30, the `untriaged_max_age_days` config
      shape) flagged; `grandfathered` = format only, no liveness checks. Add
      `"ratchet_open_max_age_days"` (default 30) to `_load_knowledge_lint_config()`'s
      (~line 328) return dict alongside `untriaged_max_age_days`. Register the check in
      the run sequence directly after `_check_audit_log` (~line 944); add
      `knowledge/ratchet-log.md` to `CANONICAL_MAP` and to `EPHEMERAL_PATHS`; update the
      module docstring's check list.
- [x] 3.2 Extend `scripts/test_knowledge_lint.py` with fixture cases: absent ledger
      clean; valid entry of each disposition passes; each malformed case flagged (bad
      keyword, bad slug, invalid calendar date); dangling `check:` path; dangling
      `test:` `::name`; bare `test:` path with existing file passes; stale waiver;
      aged `open` at the default threshold; a distinct case with checks.toml
      `[knowledge_lint] ratchet_open_max_age_days = 7` proving the override is honored;
      `grandfathered` with dead path in essence NOT flagged.

## 4. Ledger bootstrap, docs, manifest

- [x] 4.1 Create `knowledge/ratchet-log.md` with a header comment (HTML comment or plain
      text, length as needed) stating the registry-line format, followed by the three
      literal bootstrap entries from design.md D5 (ledger-format check;
      budget-agreement grandfather exemplar as `check:`; runner-contract `test:` pointer
      naming `test_stops_on_first_infra_failure`).
- [x] 4.2 Add `knowledge/ratchet-log.md` to the Reference taxonomy row of
      `knowledge/README.md`, alongside `audit-log.md`, described as a second bounded
      one-line-per-entry registry ledger (no new taxonomy row).
- [x] 4.3 Add one bullet to `AGENTS.md` `## Working process` (inside the synced span):
      the closure rule — a generalizable finding is not closed until
      `knowledge/ratchet-log.md` records check / frozen-test / waiver (preference
      ordering check > test > waiver; `open:since` for deferral) — citing the
      `finding-closure-ratchet` capability spec as canonical.
- [x] 4.4 Add `scripts/repo_lint.py` and `scripts/test_repo_lint.py` to
      `scripts/scaffold_manifest.txt`, placed adjacent to the data-lint siblings
      (`repo_lint.py` next to `data_lint.py`, `test_repo_lint.py` next to
      `test_data_lint.py`) — the manifest groups related entries; do NOT reorder
      existing lines.

## 5. Close-out routing text

- [x] 5.1 `.claude/skills/openspec-archive-change/SKILL.md`, Step 6 (primary review):
      insert the ratchet-triage step as a new sub-bullet BETWEEN the "Quality check"
      block and the "Lint before committing" bullet (so `knowledge_lint` then catches
      any ledger-format error the triage just introduced) — scan the change's
      `notes.md`/`review-log.md` for found-and-fixed defects; apply the three questions
      (real? → generalizable? → detectable/test-freezable?); Q1/Q2 = no → no entry;
      otherwise append one `knowledge/ratchet-log.md` registry line (format + one
      example line shown inline). Performed by the primary, not the archive-executor.
- [x] 5.2 `.claude/skills/run-audit/SKILL.md`, Step 3 (Triage): insert the same
      three-question triage with ledger-line output for findings judged real and
      generalizable, alongside the existing audit-log line ceremony.
- [x] 5.3 `.claude/skills/knowledge-drift-review/SKILL.md`, Step 2 (the stale-claims
      class): add one bullet — spot-check `knowledge/ratchet-log.md` `check:`/`test:`
      entries whose enforcing artifact (file/symbol) still exists but no longer
      exercises the recorded defect class (the semantic-drift residue the deterministic
      liveness check cannot see).

## 6. Green gate

- [x] 6.1 Run `scripts/check.sh` (ruff + format + full pytest incl. live-tree lint gate
      over the new ledger and the scaffold_lint SEAL with the manifest additions); fix
      any fallout until green.
