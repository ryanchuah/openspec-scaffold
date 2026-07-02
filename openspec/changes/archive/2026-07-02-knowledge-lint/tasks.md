## 1. Deterministic linter — `scripts/knowledge_lint.py`

- [x] 1.1 Scaffold the script (stdlib-only): `--root <path>` arg (default = repo root discovered from the script location), filesystem-walk of `<root>/knowledge/**/*.md` for content checks, a `main()` returning an exit code wired via `sys.exit(main())`. Collect findings as `(check, path, line|None, message)`, print one stdout line per finding, exit `0` when clean and `1` on any finding (per design D2; `1` keeps "found drift" distinct from argparse's exit-`2`).
- [x] 1.2 Check — orphan/duplicate canonical file: fixed single-home map `{STATUS.md→knowledge/STATUS.md, lessons.md→knowledge/lessons.md, roadmap.md→knowledge/roadmap.md, audit-log.md→knowledge/audit-log.md}`; flag a canonical basename living outside its home or a second copy. Do NOT include `INDEX.md`/`README.md` (multi-home → false-positive).
- [x] 1.3 Check — retired-path token: per-line substring scan of in-scope knowledge markdown; built-in defaults `ai-docs/`, `plans/open-issues.md`, `docs/reviews/`, `/home/me/`; **skip `knowledge/research/`** (period-correct history).
- [x] 1.4 Check — broken prose path citation: extract backtick-wrapped, repo-relative path-like tokens (contain `/` or end in `.md`; NOT a URL, NOT an absolute system path), flag any that do not resolve under `<root>`; **skip `knowledge/research/`**.
- [x] 1.5 Check — dangling archive pointer: flag any `openspec/changes/archive/<dir>/` reference whose `<dir>` does not exist under `<root>`.
- [x] 1.6 Check — audit-log registry format (guarded): if `<root>/knowledge/audit-log.md` exists, validate each registry line against `- **YYYY-MM-DD** · audit/<date> · <short-sha> · <essence>`; if the file is absent, skip silently (no error).
- [x] 1.7 Per-repo config: if a repo-root `audit.toml` exists, read `[knowledge_lint].retired_paths` (array) via `tomllib` and **merge** those tokens with the built-in defaults; absent file/table/key → defaults only.
- [x] 1.8 Enforce detect-only: the script performs NO filesystem writes (no open-for-write, `mkdir`, `unlink`, or move) under any flag or input — outputs are stdout + exit code only.

## 2. Linter tests — `scripts/test_knowledge_lint.py`

- [x] 2.1 Add a `tmp_path` helper that builds a synthetic `knowledge/` tree, so tests need no git and no real repo.
- [x] 2.2 One-instance-per-class drift fixture (orphan root `STATUS.md`; a retired-path token; a broken `` `dir/gone.md` `` citation; a dangling `archive/<dir>/` pointer; a malformed `audit-log.md` line) → assert exactly the expected findings and exit `1`.
- [x] 2.3 Drift-free fixture → zero findings, exit `0`.
- [x] 2.4 Detect-only: assert the fixture tree is byte-identical (contents + file set) before and after a run, for both the drift and clean cases.
- [x] 2.5 audit-log guard: absent file → check skipped, no error; present-but-malformed → the bad line is flagged.
- [x] 2.6 Per-repo config: no `audit.toml` → only default tokens flag; `audit.toml` with `[knowledge_lint].retired_paths` → the extra tokens also flag (defaults still active).
- [x] 2.7 research exclusion: a retired-path token and a broken citation placed inside `knowledge/research/` yield NO finding; the same placed outside research ARE flagged.
- [x] 2.8 orphan exclusions + duplicate: an `INDEX.md` and a `README.md` outside `knowledge/` are NOT flagged; a root `STATUS.md` IS flagged; and a legitimate `knowledge/STATUS.md` plus a second stray copy of a canonical file elsewhere IS flagged (the duplicate sub-case).
- [x] 2.9 negative-citation cases (spec `broken-prose-path-citation-flagged`): a bare non-backtick mention, a URL, and an absolute system path — each pointing at a non-existent target in prose — are NOT flagged (only backtick-wrapped, repo-relative, non-URL, non-absolute tokens are).

## 3. Judgment skill — `.claude/skills/lint-knowledge/SKILL.md`

- [x] 3.1 Author `SKILL.md` at `.claude/skills/lint-knowledge/` **only** (no `.opencode/` copy). Frontmatter (name/description); body directs the agent to: (1) FIRST run `scripts/knowledge_lint.py` and clear its deterministic findings; then the judgment sweeps — (a) Class B stale "not yet built"/planned claims vs a shipped `openspec/changes/archive/` entry or `knowledge/STATUS.md`; (b) Class D intra-doc contradictions; (c) buried operator/pre-prod items in a README/runbook missing from `knowledge/questions/INDEX.md` Active. State detect-only (report, never rewrite) and the operator-invoked/periodic cadence (NOT every archive).

## 4. Archive-cadence integration (the `knowledge-organization` delta)

- [x] 4.1 Edit `AGENTS.md` — in the "State, write discipline, and the archive-as-handoff rule" span, add one flag-only sentence: at archive the archive-executor also runs `scripts/knowledge_lint.py` and re-checks `knowledge/reference/`, `knowledge/roadmap.md`, and the individual `knowledge/questions/<item>.md` Parked bodies for now-stale claims about the just-shipped change; findings are surfaced but do NOT block archive; the three-tracker reconciliation is unchanged. (This span is scaffold-managed and propagates.)
- [x] 4.2 Edit `.claude/skills/openspec-archive-change/SKILL.md` — add the matching flag-only wider-sweep instruction to the archive-executor payload in **both** platform branches so it actually reaches the executor on each platform: (a) the "If you are Claude Code" branch's `opencode run` prompt string, and (b) the "If you are OpenCode" branch's `@archive-executor` Task-tool "Pass:" list. Editing narrative prose alone is insufficient — the instruction must be inside both delegation payloads.

## 5. Manifest registration — `scripts/scaffold_manifest.txt`

- [x] 5.1 Add to the Scripts section: `scripts/knowledge_lint.py` and `scripts/test_knowledge_lint.py`.
- [x] 5.2 Add to the Skills section: `.claude/skills/lint-knowledge/SKILL.md`. Do NOT add `audit.toml` (per-repo config, not scaffold-managed).
