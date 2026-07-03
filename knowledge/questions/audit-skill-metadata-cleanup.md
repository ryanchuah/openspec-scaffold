# audit-skill metadata cleanup

Both `run-audit/SKILL.md` and `knowledge-drift-review/SKILL.md` carry a frontmatter
`compatibility: Requires openspec CLI` line — template boilerplate that is inaccurate for
both skills:

- `run-audit` does **not** require the openspec CLI. It drives `audit_bundle.py` and
  `audit_scope.py` — stdlib-only scripts with no openspec CLI dependency. The skill's
  interpreter-detection logic handles `.venv/bin/python`, `python3`, and `python`.
- `knowledge-drift-review` does **not** require the openspec CLI. It runs
  `scripts/knowledge_lint.py` (stdlib-only) and performs LLM judgment sweeps — no openspec
  CLI dependency.

This was noted as a cosmetic carryover during the `clarify-audit-tooling-surface` verify
checkpoint (2026-07-03): not fixed in that change because it matched the pre-existing
`knowledge-drift-review` boilerplate (carried forward from the original `lint-knowledge`).
A broader audit of skill frontmatter accuracy across all skills may be warranted.
