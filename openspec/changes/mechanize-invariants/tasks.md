# Tasks — mechanize-invariants

Context for every task: this is the golden-source repo. `scripts/scaffold_lint.py` is an
**authoring-side** linter (like `scripts/sync_scaffold.py`) — it is deliberately NOT added to
`scripts/scaffold_manifest.txt` and never syncs downstream. All paths are repo-relative.

## 1. scripts/scaffold_lint.py

- [ ] 1.1 Create `scripts/scaffold_lint.py`: stdlib-only CLI, `python3 scripts/scaffold_lint.py [--root PATH]`
      (default root = the script's grandparent dir, same convention as `scripts/scaffold_check.py`).
      Exit codes: `0` = clean, `1` = findings (matches `sync_scaffold.py --check` / `knowledge_lint.py`).
      Each finding is one stdout line: `scaffold-lint: <check-id>: <detail>`. Module docstring documents
      the contract, all check-ids, and the exclusion list. Runs all checks even after one finds findings
      (report everything, then exit 1).
- [ ] 1.2 Implement check `manifest-completeness`: (a) every existing file matching the managed globs
      `.claude/skills/*/SKILL.md`, `.claude/skills/_shared/*.md`, `.claude/agents/*.md`,
      `.opencode/agents/*.md`, `scripts/*` (plain files only — `scripts/` mixes files and dirs like
      `__pycache__/`; the skill/agent globs are inherently file-only) must be listed in
      `scripts/scaffold_manifest.txt` OR match the exclusion list:
      `scripts/sync_scaffold.py`, `scripts/test_sync_scaffold.py`, `scripts/scaffold_lint.py`,
      `scripts/test_scaffold_lint.py`, `scripts/test-cmd`, glob `scripts/_*_oneoff.py`;
      (b) reverse: every manifest entry must exist on disk. Missing either way = finding.
- [ ] 1.3 Implement check `agents-md-structure` as TWO sub-checks (the reused function only detects
      anchor *presence*, not *uniqueness* — do not conflate them):
      (a) **uniqueness** — implemented directly in scaffold_lint: for each of the three anchor
      strings (`> **MANDATORY`, `## Roles`, `## After reading this file`), count matching lines
      per-line via `line.startswith(anchor)` — the SAME method for all three (never `str.count()`,
      which would match inside fenced code blocks); a count other than exactly 1 = finding;
      (b) **presence + no-tail** — REUSE `scripts/sync_scaffold.py`'s span extraction by importing it
      (same import pattern `scripts/test_sync_scaffold.py` uses), run it against the scaffold's own
      `AGENTS.md` (as both source and target), and convert any `ValueError` into a finding. Do NOT
      duplicate the extraction regexes for sub-check (b).
- [ ] 1.4 Implement check `config-rules-last`: `openspec/config.yaml` must contain a `rules:` block and
      no non-comment top-level key after it. Two sub-checks: (a) missing block — REUSE
      `sync_scaffold.py`'s `_extract_rules_block` by import; no block found = finding; (b) trailing
      keys — REUSE `sync_scaffold.py`'s `sync_config_yaml` by import, calling it with the scaffold's
      own config as BOTH source and target and converting `ValueError` into a finding (note: when the
      block is missing, `sync_config_yaml` appends instead of raising — which is why (a) is a
      separate explicit sub-check).
- [ ] 1.5 Implement check `dangling-skill-refs`: scan `AGENTS.md` plus every `.md` under
      `.claude/skills/` (recursive — `_shared/*.md` is intentionally included and expected to stay
      clean), `.claude/agents/`, `.opencode/agents/` for tokens matching
      `\bopenspec-[a-z][a-z-]*[a-z]\b`, plus the literal token `lint-knowledge` (special-cased because
      it is the ONLY skill name that does not start with `openspec-`; no other literal tokens are
      needed — agent names like `apply-executor` are validated only when they appear as `openspec-*`
      tokens, which they don't). Every matched token must be one of: a skill dir name under
      `.claude/skills/`, an agent file stem under `.claude/agents/` or `.opencode/agents/`, or in the
      allowlist constant `{"openspec-scaffold"}`. Unknown token = finding naming file and token.
- [ ] 1.6 Implement check `budget-agreement`: extract every numeric `timeout -k <G> <B>` pair from the
      same file set as 1.5 (regex `timeout\s+-k\s+(\d+)\s+(\d+)` — the `timeout` prefix is deliberate:
      the check targets executable copy-paste command blocks, not descriptive prose like
      "the budget is `-k 15 780`"; do not broaden it). Sanctioned pairs come from
      `.claude/skills/_shared/delegation-harness.md` with this exact algorithm: iterate the file's
      lines; on each line that starts with `|` (a markdown table row), apply the regex
      ``\x60-k (\d+) (\d+)\x60`` (backtick-quoted flags cell) and collect all matches as (G, B)
      pairs — do NOT split on `|` (inline code spans elsewhere in the file contain pipes). Any
      embedded pair not in the sanctioned set = finding naming file, line, and pair. Two distinct
      infra findings: no line of the file contains `## (e)` → `budget-agreement: §e table not found`;
      table rows found but zero pairs extracted → `budget-agreement: could not parse §e table`.
      Self-referential note (no special exclusion needed): the harness file itself is in the 1.5 scan
      set, but its §e cells are backtick-quoted without a `timeout` prefix and its §c prose uses
      angle-bracket placeholders (`timeout -k <grace> <budget>`), so the embedded-pair regex matches
      nothing in it.

## 2. Tests for scaffold_lint

- [ ] 2.1 Create `scripts/test_scaffold_lint.py` (pytest style, `tmp_path` fixture repos, same
      conventions as `scripts/test_knowledge_lint.py`): for EACH of the five checks, at least one clean
      fixture (no finding) and one violating fixture (finding + exit 1). Include: anchor renamed,
      anchor duplicated, anchor line deleted entirely, tail present, extra top-level key after
      `rules:`, unlisted skill file, manifest entry missing on disk, unknown `openspec-*` token,
      embedded `timeout -k 15 999` not in table.
- [ ] 2.2 Fix the one known live violation so the repo lints clean: in
      `.claude/skills/openspec-apply-change/SKILL.md`, the line suggesting `openspec-continue-change`
      (currently line 67 — a skill that does not exist in this repo). Replace that suggestion with:
      suggest re-running the `openspec-propose` skill to create the missing artifacts. Keep the rest
      of the line's meaning intact.
- [ ] 2.3 Add a live-repo test to `scripts/test_scaffold_lint.py`: running the linter against THIS
      repo reports zero findings and exits 0. Its docstring must state it is a SEAL: once green, any
      instruction-file edit that introduces a violation fails the suite by design — that is the
      enforcement mechanism, not test fragility. If this test surfaces any pre-existing violation
      other than the one fixed in 2.2, do NOT edit further instruction files — STOP and report it as
      a blocker on TWO surfaces: append a `## NON-CONVERGENCE BLOCKER` section (with the exact
      finding lines) to `openspec/changes/mechanize-invariants/notes.md`, AND lead your final return
      message with the same `### NON-CONVERGENCE BLOCKER` heading per your agent instructions.

## 3. sync_scaffold.py hook-wiring warning

- [ ] 3.1 In `scripts/sync_scaffold.py`, in BOTH `check()` and `sync()`: after the existing manifest
      walk, read `<target>/.claude/settings.json`; if the file is missing OR its text does not contain
      the substring `scaffold_check.py`, print to stderr:
      `WARNING: <target>/.claude/settings.json does not wire scripts/scaffold_check.py (PreToolUse) — the downstream edit-guard is absent`.
      This is a warning only — exit codes and all existing stdout output are unchanged. (No existing
      `test_sync_scaffold.py` test asserts on stderr content as of this writing; if you find one,
      update only its assertion to tolerate the warning line — never the checked behavior.)
- [ ] 3.2 Add tests to `scripts/test_sync_scaffold.py`: target with a settings.json containing
      `scaffold_check.py` → no warning; target with no settings.json → warning; target with a
      settings.json lacking the substring → warning; in all three cases `--check` exit code is
      unchanged from current behavior.

## 4. Arm this repo's commit-test gate

- [ ] 4.1 Create `scripts/test-cmd` containing exactly one line: `pytest -q`
      (per the per-repo convention in `scripts/test-gate.sh`; NOT `python3 -m pytest` — on this
      machine pytest is installed only for the `~/.local/bin/pytest` interpreter). Then run
      `scripts/test-gate.sh` once and confirm it prints `tests passed` and exits 0 — this smokes the
      gate WIRING specifically.
- [ ] 4.2 Final convergence check across everything this change touched (groups 1–3): run
      `pytest -q` directly from the repo root and confirm green. This is distinct from
      4.1 (which validates the gate script picks up test-cmd); this validates the suite itself after
      all edits have landed.
