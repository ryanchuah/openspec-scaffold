# tasks — clarify-audit-tooling-surface (apply phase)

Implement top-to-bottom; check off as each lands. Do NOT commit (orchestrator reviews + commits).
Do NOT edit `openspec/specs/` — the requirement deltas merge at archive; the Purpose-line rename is
an archive instruction (see `notes.md`).

## Rename lint-knowledge → knowledge-drift-review

- [x] 1. `git mv .claude/skills/lint-knowledge .claude/skills/knowledge-drift-review`; in the moved
      `SKILL.md`, set frontmatter `name: knowledge-drift-review`. Body prose unchanged EXCEPT its
      `python scripts/knowledge_lint.py` line: add the same per-repo interpreter note the run-audit
      skill uses (design D3 try-order: task-runner `audit-*` → `.venv/bin/python` → `python3` →
      `python`) — one short note, so the skill stops implying a bare-`python` PATH assumption.
- [x] 2. `scripts/scaffold_manifest.txt`: three deltas — remove
      `.claude/skills/lint-knowledge/SKILL.md`, add `.claude/skills/knowledge-drift-review/SKILL.md`,
      add `.claude/skills/run-audit/SKILL.md`. Keep the file's section ordering/comments intact.
      (This lists `run-audit` before task 5 authors it — harmless: the live-repo SEAL is only checked
      at task 8, and nothing is committed mid-way.)

## Generalize scaffold_lint (design D2)

- [x] 3. `scripts/scaffold_lint.py`: replace `_LINT_KNOWLEDGE_RE` with
      `_NON_OPENSPEC_SKILL_TOKENS: frozenset[str] = frozenset({"knowledge-drift-review", "run-audit"})`
      (with the "keep in step with actual non-openspec skill dirs" comment). In
      `check_dangling_skill_refs`, after the `_TOKEN_RE` matches, add each token in
      `_NON_OPENSPEC_SKILL_TOKENS` found via `re.search(rf"\b{re.escape(t)}\b", text)`. Update the
      `dangling-skill-refs` docstring block (~line 80) to describe the set, not the single literal.
- [x] 4. `scripts/test_scaffold_lint.py`: update the fixtures that reference `lint-knowledge` to the
      new name + mechanism — specifically: (i) the `_LINT_KNOWLEDGE_SKILL` fixture body (`name:` +
      prose); (ii) the fixture-tree dictionary KEY `.claude/skills/lint-knowledge/SKILL.md` in
      `_clean_tree()` (~line 134) → `.claude/skills/knowledge-drift-review/SKILL.md`; (iii) the
      manifest-content string line (~126); (iv) the `_SKILL_CLEAN` line (~96), full text
      `Demo skill body. See \`openspec-demo\` for details and \`lint-knowledge\` for` →
      `... and \`knowledge-drift-review\` for`. ADD a regression test with the design-D2 construction: a fixture tree where
      `knowledge-drift-review`'s skill dir EXISTS but `run-audit`'s does NOT, and a scanned doc
      references both → `knowledge-drift-review` yields no finding (dir present), `run-audit` IS
      flagged (in `_NON_OPENSPEC_SKILL_TOKENS` so detected, no dir so not in `valid_tokens`). Use the
      new names — do NOT leave `lint-knowledge` literals in the test.

## New run-audit skill (design D3)

- [x] 5. Author `.claude/skills/run-audit/SKILL.md` per design D3: frontmatter (`name: run-audit`,
      operator-invoked description); the interpreter try-order convention (task-runner `audit-*` →
      `.venv/bin/python` → `python3` → `python`, referenced as `<py>`); **step-0 pre-check** (confirm
      `audit_bundle.py` + `audit_scope.py` run under `<py>`, fail fast if not); the cycle steps
      (`audit_bundle.py --list` → `--floor`/`--report --date` → triage → `audit_scope.py tag --date`
      → `log-line` → append `knowledge/audit-log.md`), where **`tag` runs ONLY when the operator
      explicitly asks to "tag"/"anchor"** (else read-only report); **error handling** (stop on first
      non-zero script exit + report; if `output/audit/<date>/` exists, report + do not overwrite
      without operator direction); the wiring-detection branch (detect absent `audit.toml`/`checks/`/
      task targets, guide but do NOT auto-create); guardrails (reports-only; `tag` is the one
      repo-state mutation; audit-log append is the one tracked-file write; never fix code). Single
      path — no `.opencode/` copy (mirrors knowledge-drift-review).

## AGENTS.md surgical edits (design D4)

- [x] 6. In AGENTS.md "Deterministic audit tooling" (keep the 4-paragraph structure): (a) note the
      interpreter is per-repo (`python` illustrative; `run-audit` handles it); (b) reword the
      `just audit-floor` example to read as an if-defined per-repo convention; (c) add one sentence
      naming `run-audit` as the entry point and distinguishing `knowledge_lint.py` (deterministic)
      from `knowledge-drift-review` (LLM). No structural rewrite.

## Per-repo prose refs (openspec/specs/ excluded — see header)

- [x] 7. Update `lint-knowledge` → `knowledge-drift-review` in `knowledge/STATUS.md`,
      `knowledge/reference/resync-verification.md`, `knowledge/questions/knowledge-lint-follow-ons.md`.
      Do NOT touch `knowledge/decisions/INDEX.md` historical line or `openspec/changes/archive/**`.

## Verify (do not commit)

- [x] 8. `python3 scripts/scaffold_lint.py` → `scaffold-lint: clean` (incl. live-repo SEAL —
      validates dangling-skill-refs + manifest-completeness); `pytest -q` green;
      `python3 scripts/sync_scaffold.py --check-refs .` → exit 0 (validates knowledge-path reference
      integrity — a different invariant, both needed);
      `grep -rn 'lint-knowledge' --include='*.md' --include='*.py' --include='*.txt' .` (excluding
      `.git/`, `openspec/changes/`, and `openspec/specs/knowledge-lint/spec.md` [main-spec bodies
      merge at archive]) returns only the `knowledge/decisions/INDEX.md` historical line.
