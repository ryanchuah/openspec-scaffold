# Premise review — boot-budget-per-repo (SMALL)

Reviewer: `openspec-reviewer` @ `deepseek/deepseek-v4-flash` (SMALL premise pass) · 2026-07-15

### Premise Verdict

**PREMISE: AGREE**

- **Root, not symptom:** hardcoded module constants (`WARN_BYTES`/`FAIL_BYTES`) that cannot
  accommodate legitimate per-repo variation in boot-surface size, causing a downstream
  commit-gate failure. This is the root, not a surface symptom.
- **Solution targets the root:** making thresholds per-repo configurable via `checks.toml`
  (mirroring the established `knowledge_lint` pattern) directly addresses the root. Defaults
  remain unchanged, so the scaffold itself is byte-for-byte unaffected.
- **Scope right-sized:** the three implementation steps are focused and well-bounded; the
  out-of-scope items are explicit and appropriate (no content-condensing creep, no new config
  file, no scaffold-synced budgets).
- **No critical blind spots:** verified (a) `boot_surface_lint.py` + test are scaffold-managed
  (manifest lines 54, 70); (b) `checks.toml` absent at scaffold root → absent-file fallback
  exercised; (c) `tomllib` available (already used by `knowledge_lint.py`); (d) live-tree test
  stays intact. One 🟡: inverted-threshold handling ("decide in apply") — a cleanliness note,
  not a direction fault.

**VERDICT: PASS** — sound direction, fit for delegation to apply. The 🟡 (inverted warn>fail)
is already covered by the plan's fallback-to-defaults rule.

_Note: this premise pass is recorded despite the operator having already directed the change
(Option 2 in the propagation friction question) — the SMALL premise pass fires regardless of
operator confirmation per AGENTS.md._
