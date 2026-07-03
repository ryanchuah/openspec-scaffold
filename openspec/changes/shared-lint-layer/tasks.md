# Tasks — shared-lint-layer (portfolio Change C, MEDIUM)

Context for the executor: acceptance criteria + all design decisions live in this change's
`notes.md` (there is no design.md at MEDIUM). Banked facts:
`plans/day-to-day-tooling/c-lint-layer-research.md`. Delta specs: `specs/shared-lint-gate/`,
`specs/commit-test-gate/`, `specs/knowledge-lint/`. Depends on shipped B (sync deletion manifest)
and A (checks-facts-split) — audit tooling is now `checks.py`/`facts.py`/`checks.toml`.

Key existing anchors (re-grep before editing — line numbers drift):
- `scripts/knowledge_lint.py`: `_check_broken_citations` (~363-399) with its skip-ladder
  (~373-389); helpers `_is_glob_pattern`, `_is_template_placeholder`, `_is_path_like`,
  `EPHEMERAL_PATHS`; `collect_findings(root)` (~459); `main(argv)` (~485).
- `scripts/status_lint.py`: `main(argv)` (~236) — NO `collect_findings`.
- `scripts/scaffold_lint.py`: `collect_findings(root)` (~471) — the live-tree test pattern to mirror
  is in `scripts/test_scaffold_lint.py` (`collect_findings(tmp_path)` / real-root asserts).
- `scripts/test-gate.sh`: current gate (reads `scripts/test-cmd`, exit 0 allow / 2 block, with an
  unresolvable-executable → warn+exit-0 branch to preserve).
- `scripts/scaffold_manifest.txt`: manifest of scaffold-managed files.
- `scripts/dev-requirements.txt`: currently requests/trafilatura/beautifulsoup4/lxml only.

Do not commit — the orchestrator reviews and commits. Work sequentially, checking off each task.

## 1. ruff config + scaffold baseline (land green before wiring the gate)

- [x] 1.1 Create root `ruff.toml` (standalone; the scaffold has no pyproject). Lint: `select = ["E",
      "F", "I", "B"]`, `ignore = ["E501"]` (the formatter owns width — see notes.md line-length
      decision). Formatter enabled with `line-length = 100`. Keep any per-file-ignores in this one
      file (none needed initially).
- [x] 1.2 Add `ruff` (pinned to a current stable version) to `scripts/dev-requirements.txt`, and
      install it into the repo `.venv` so `check.sh` and the baseline can run
      (`.venv/bin/python -m pip install ruff==<pin>`; if the repo uses user-global ruff, still add
      the pin to dev-requirements so envs converge).
- [x] 1.3 Run the one-time baseline over the whole scaffold: `ruff check --fix .` then
      `ruff format .`. This is a large but purely-mechanical diff (behavior-preserving). Do NOT
      hand-edit logic. After it, `ruff check .` and `ruff format --check .` MUST both exit 0.
- [x] 1.4 Re-run the full test suite (`scripts/test-cmd`) after the reformat and confirm it is still
      green (formatting must not change behavior). Fix any test that the reformat legitimately broke
      (should be none).

## 2. check.sh — the single definition of green

- [x] 2.1 Create `scripts/check.sh` (executable, `set -euo pipefail`, byte-identical-across-repos
      shape like `test-gate.sh`). Resolve `REPO_ROOT` the same way `test-gate.sh` does. Run in order:
      (a) `ruff check`, (b) `ruff format --check`, (c) the test stage sourced from `scripts/test-cmd`.
      Exit non-zero naming the failed stage; exit 0 only if all pass.
- [x] 2.2 Missing-tool degradation (mirror `test-gate.sh`): if `ruff` does not resolve
      (`command -v ruff`), warn on stderr, SKIP stages (a) and (b), and continue to the test stage —
      do NOT block on absent ruff. If `scripts/test-cmd` is absent/empty, the test stage is a no-op
      (as today). Only a present tool reporting a real violation, or a failing test, yields non-zero.
- [x] 2.3 Add a `scripts/test_check_sh.py` (or extend the gate smoke fixture) exercising check.sh
      branches: clean tree → 0; injected lint violation → non-zero; format drift → non-zero; failing
      test-cmd → non-zero; ruff absent (simulate via PATH) → warns, skips lint/format, still runs
      tests, does not hard-block. Use tmp fixtures; do not depend on the real repo state.

## 3. install-tools.sh — pinned security scanners

- [x] 3.1 Create `scripts/install-tools.sh` (executable, idempotent): install pinned `gitleaks` and
      `osv-scanner` to a resolvable location; note that `deptry` comes via dev extras (pip), not a
      binary install. Pin explicit current-stable versions (record the pins in the script header).
      Re-running with the pinned versions already present must be a no-op and exit 0.

## 4. test-gate.sh → check.sh rewire

- [x] 4.1 Rewire `scripts/test-gate.sh` to delegate to `scripts/check.sh` instead of running the
      test command directly: keep the hook contract (exit 0 allow / exit 2 block) — map any non-zero
      from check.sh to exit 2, exit 0 to exit 0. Preserve the existing no-op branches (no test-cmd,
      config error) by letting check.sh own them. Keep both scripts byte-identical-across-repos.
- [x] 4.2 Update the smoke fixture / any `scripts/test_*gate*` so the gate's five documented states
      still pass through the new check.sh delegation (absent test-cmd → 0; empty → 0; unresolvable →
      0+warn; failing → 2; passing → 0), plus a lint/format-failure → 2 case.

## 5. Hook-matcher fix (fixes the parked misfire) + regression probe

- [x] 5.1 Reproduce the parked misfire first (evidence: `plans/day-to-day-tooling/c-lint-layer-research.md`
      §hook-matcher-bug and `knowledge/questions/commit-test-gate-hook-misfire.md`): a non-commit Bash
      command containing `git commit` only as a substring (harmless `true` payload + file
      redirections + EXIT-sentinel echo) currently trips the gate.
- [x] 5.2 Fix so the gate fires only on a genuine `git commit` argv. Prefer the robust layer: have
      `test-gate.sh` read the PreToolUse tool-input command (the hook provides `tool_input.command`
      on stdin JSON) and no-op (exit 0) unless the command is actually a `git commit` invocation;
      then proceed to the check.sh delegation. (If reading stdin is not viable, tighten the
      `.claude/settings.json` PreToolUse matcher instead — but the script-layer guard is preferred so
      it travels with the scaffold-managed script.) A genuine `git commit -am`/`--amend` must still gate.
- [x] 5.3 Add the reproduction command to the commit-test-gate smoke fixture as a must-not-gate
      regression probe (asserts the gate no-ops on the substring-only command).

## 6. knowledge_lint citation-matcher hardening

- [ ] 6.1 In `scripts/knowledge_lint.py` `_check_broken_citations`, extend the skip-ladder so these
      resolve as non-findings (keep each narrow so genuinely-missing files still flag): (a)
      brace-expansion `{a,b}` and `{a..b}` — add detection (extend `_is_glob_pattern` or a new
      `_is_brace_pattern`); (b) `YYYY-Www`-style literal period placeholders — extend
      `_is_template_placeholder`; (c) trailing `::symbol` node-id — strip the `::…` suffix, then do
      the existing `(root / token).exists()` check on the file; (d) trailing `:N-M` line range —
      strip the `:N-M` suffix, then existence-check the file; (e) `output/` ephemeral prefix — treat
      any citation whose first segment is `output/` as ephemeral (like `EPHEMERAL_PATHS`).
- [ ] 6.2 Add unit tests to `scripts/test_knowledge_lint.py` for each skip class (brace, placeholder,
      `::symbol` on an existing file, `:N-M` on an existing file, `output/` path) asserting NO
      finding, AND a companion test that a genuinely-missing `src/…/gone.py` (real top-level dir,
      matches no skip form) STILL flags. Also assert `::symbol`/`:N-M` on a NON-existent file still
      flags (drift not blinded).

## 7. knowledge_lint root-handoff check

- [ ] 7.1 Add a new finding to `scripts/knowledge_lint.py`: flag any `HANDOFF*` / `HANDOVER*` file at
      the repository ROOT (glob the root only), exempting `knowledge/HANDOFF.md`. Wire it into
      `collect_findings` so it rides the same exit/report path as the other checks.
- [ ] 7.2 Add unit tests: a root `HANDOFF-x.md` fixture → flagged; a root `HANDOVER.md` → flagged;
      `knowledge/HANDOFF.md` present → NOT flagged; clean tree → no finding.

## 8. Doc-lints enforced on the live tree

- [ ] 8.1 Add a live-tree test (new `scripts/test_doc_lint_gate.py` or into an existing suite file)
      that asserts the REAL repo is clean: `knowledge_lint.collect_findings(REPO_ROOT) == []` and
      `status_lint.main([...]) == 0` (status_lint has no `collect_findings`; optionally add one for
      symmetry per notes.md, else assert its `main` exit code). Mirror the real-root pattern from
      `scripts/test_scaffold_lint.py`.
- [ ] 8.2 Confirm the scaffold's own tree passes both after tasks 6–7 (it currently passes
      knowledge_lint; the hardening only relaxes false-positives and the root-handoff check finds no
      root handoff files). Resolve any genuine finding the new checks surface in the scaffold's own
      `knowledge/` before proceeding.

## 9. Executor autofix habit (byte-identical bodies) + apply skill

- [ ] 9.1 Add an autofix instruction to BOTH `.claude/agents/apply-executor.md` and
      `.opencode/agents/apply-executor.md`, byte-identical bodies: before reporting a task done, run
      `ruff check --fix` + `ruff format` on the files touched. `scripts/test_executor_body_agreement.py`
      MUST stay green (byte-compare passes).
- [ ] 9.2 Add the matching autofix-before-done line to the apply SKILL
      (`.claude/skills/openspec-apply-change/SKILL.md`).

## 10. Manifest + propagation

- [ ] 10.1 Add `ruff.toml`, `scripts/check.sh`, `scripts/install-tools.sh` to
      `scripts/scaffold_manifest.txt`. Do NOT add `checks.toml` (per-repo). Ensure any new test files
      that are scaffold-managed by convention are handled per the manifest's existing rules.
- [ ] 10.2 Run `scripts/scaffold_lint.py` (manifest completeness + no-conflict) and
      `python scripts/sync_scaffold.py --check-refs` against this repo — both must exit 0.

## 11. Reference docs

- [ ] 11.1 Update `knowledge/reference/exit-codes.md` with the `check.sh` exit convention (0 green /
      non-zero = failed stage; test-gate maps to allow/block 0/2).
- [ ] 11.2 Update `knowledge/reference/new-repo-bootstrap.md` with the `scripts/install-tools.sh`
      step (and the ruff dev-dependency).

## 12. Final green self-check (executor, before reporting done)

- [ ] 12.1 Run and confirm all green: full suite via `scripts/test-cmd`; `scripts/check.sh` (exit 0);
      `scripts/scaffold_lint.py`; live-tree `knowledge_lint.py` (self) and `status_lint.py`;
      `sync_scaffold.py --check-refs`. Report any non-green stage with its output rather than
      continuing.
