# clarify-audit-tooling propagation follow-on

Sync the `clarify-audit-tooling-surface` change (rename `lint-knowledge` → `knowledge-drift-review`,
new `run-audit` skill, `scaffold_lint` dangling-skill-ref generalization) to **extrends** and
**psc-monitor** in the next propagation batch.

The rename adds a downstream **tombstone step** per repo: `rm -rf .claude/skills/lint-knowledge/`
(since the manifest has no delete verb — same pattern as the `openspec-onboard` tombstone).

**extrends** took the pre-rename state on 2026-07-03 during the large pending-sync batch — it still
has the old `lint-knowledge` skill dir. On next sync, the scaffold sync will see
`.claude/skills/knowledge-drift-review/SKILL.md` ADDED and `lint-knowledge` as an untracked stale
dir — the tombstone step cleans that up.

**psc-monitor** is still frozen (has not received any of the pending-sync batch). On thaw, the
first sync will need the full batch including the `openspec-onboard` tombstone, this rename
tombstone, and all new scaffold-managed files.

Both repos will also receive: the `run-audit` skill (new manifest entry), the generalized
`scaffold_lint.py`, the AGENTS.md "Deterministic audit tooling" edits (shared span, auto-propagated),
and the updated `knowledge-lint` spec.

Blocked on: operator authorization to propagate to each repo.
