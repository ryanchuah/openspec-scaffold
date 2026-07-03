# scaffold_lint removed-name blind spot (D2 trade-off)

`scaffold_lint.py`'s `check_dangling_skill_refs` uses an explicit frozenset
`_NON_OPENSPEC_SKILL_TOKENS` to detect non-openspec skill references. When a non-openspec
skill is *removed*, its name is (deliberately) dropped from the frozenset — so `scaffold_lint`
no longer flags a lingering reference to the removed name.

This is a documented D2 trade-off: rename-completeness for a removed non-openspec skill is a
one-time migration check (enforced by a manual `grep` sweep during the migration), not a standing
invariant. The frozenset approach preserves detect-then-validate for the *current* skill set at
the cost of losing detection for removed names.

Current risk: **harmless with 2 non-openspec skills** (`knowledge-drift-review`, `run-audit`).
The `grep -rn lint-knowledge` post-migration sweep confirmed no stragglers outside historical
records.

**Revisit if:**
- The non-openspec skill set grows beyond a handful (manual grep becomes infeasible).
- A non-openspec skill rename recurs (the rename-step review should include a grep sweep, but
  process discipline is softer than a SEAL).
