# Change C (shared lint layer) — banked research for the propose session

Collected 2026-07-03 during the checks-facts-split session; verified against the live
repos then. Re-verify anything load-bearing before freezing tasks.

## Scaffold repo facts (change C must land green HERE too)

- **Ruff baseline (indicative):** dominated by line-length errors with import-sort a
  distant second; `ruff format` has never been applied (nearly every scripts/ file would
  reformat). A line-length decision is therefore the first design choice: most of the
  backlog dissolves under the formatter, the rest needs either a raised `line-length` or
  a one-time manual pass. Repo has **no pyproject.toml at all** — a standalone
  `ruff.toml` works without one (ruff prefers `ruff.toml` over `pyproject.toml` when
  both exist, which also keeps downstream pyprojects lint-config-free).
- **Ruff is declared nowhere** (any repo): not in scaffold `dev-requirements.txt`
  (only requests/trafilatura/beautifulsoup4/lxml), not in downstream dev extras.
  Everyone currently uses a user-global `~/.local/bin/ruff`.
- **Gate wiring today:** `.claude/settings.json` PreToolUse hook (matcher `Bash`,
  `if: "Bash(git commit*)"`, timeout 600) → `scripts/test-gate.sh` → per-repo
  `scripts/test-cmd` (content: `pytest -q`). `test-gate.sh` IS scaffold-managed
  (manifest-listed); `test-cmd` is per-repo by design.
- **Executor autofix line must be added to BOTH agent files** —
  `.claude/agents/apply-executor.md` AND `.opencode/agents/apply-executor.md` — because
  `scripts/test_executor_body_agreement.py` byte-compares the bodies and fails on drift.
  Neither file has any lint/format instruction today (their loop is tests-only).
- **Doc-lints are shipped but not gated:** `knowledge_lint.py`/`status_lint.py` are
  manifest-listed and their tests are tmp_path-fixture-only; nothing runs them against
  the live tree at commit time. `scaffold_lint.py` is the model to copy: its test runs
  `collect_findings` against the real repo, so the commit gate enforces it.
- **knowledge/reference/ docs to update when C lands:** `exit-codes.md` (add check.sh
  exit convention), `new-repo-bootstrap.md` (install-tools step).

## Hook-matcher bug (fix owed in C — full evidence in
openspec/changes/checks-facts-split/notes.md §Discoveries)

The commit-test-gate hook fires on some complex non-commit Bash commands (reproduced
with a harmless `true` + file redirections + sentinel echo; plain probes pass). While a
suite is red mid-change, this intermittently blocks orchestration commands. Workaround
in use: put long commands in a script file and invoke `bash <file>`. C should tighten
the matcher (or wrap the gate so it only fires on genuine `git commit` argv) and add a
regression probe to the smoke fixture.

## Operator decisions already made (recorded in explore-brief.md)

- Ruleset: **E, F, I, B + enforced format** (ratchet later).
- Security scanners (gitleaks/osv-scanner): **CI blocking on pushes AND PRs**.
- `checks.toml` is per-repo glue (seed convention ships in A — SHIPPED; see the
  archived change once archived).
- extrends handoff-file hygiene: list per-file for operator approval before deletion (D1).

## Change-C scope reminder (from explore-brief.md, post-A adjustments)

Scaffold-managed: `ruff.toml`, `scripts/check.sh` (ruff check + format --check +
delegate to `scripts/test-cmd`), `scripts/install-tools.sh` (pinned gitleaks/osv-scanner;
deptry via dev extras), live-tree doc-lint test file, root `HANDOFF*`/`HANDOVER*` glob
check (mechanizes the knowledge-handoff-file decision), apply-skill + both executor-agent
autofix lines, `test-gate.sh` → `check.sh` rewire, hook-matcher fix, scaffold's own
baseline autofix commit. Note: A renamed the engine — any C reference to audit tooling
uses `checks.py`/`facts.py`/`checks.toml`.
