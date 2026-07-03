## Why

Downstream agents hit avoidable confusion running the scaffold's audit / knowledge-lint tooling
— surfaced in extrends immediately after the 2026-07-03 propagation. Three causes: (1) the
deterministic linter `scripts/knowledge_lint.py` and the LLM skill `lint-knowledge` have
near-mirrored names (reversed word order), so "knowledge-lint" is ambiguous — an agent can't tell
which tool is meant; (2) the deterministic-audit cycle lives only as prose in AGENTS.md, so every
agent must reconstruct the procedure, and that prose describes a *wired* end-state (`just audit-*`
targets, an `audit-log.md`) that a freshly-synced repo does not yet have; (3) bare-`python`
invocations don't resolve in venv-based repos. The tooling is sound; its discoverability and
naming are not.

## What Changes

- **BREAKING (skill rename):** rename the `lint-knowledge` skill → **`knowledge-drift-review`**.
  This leaves the deterministic `*_lint.py` script family untouched, so the two tools become
  unmistakable: `knowledge_lint.py` = the deterministic linter, `knowledge-drift-review` = the LLM
  semantic pass. The old skill directory becomes a **downstream tombstone** (deleted on the next
  sync, exactly like `openspec-onboard` — the manifest has no delete verb).
- **New skill `run-audit`:** an on-demand skill that owns the deterministic-audit cycle end-to-end
  — detect the repo's interpreter, run `audit_bundle.py --list/--floor/--report`, guide triage,
  `audit_scope.py tag`, print + append the `knowledge/audit-log.md` log line — and, when the
  per-repo audit-layer wiring is absent (`audit.toml`, `checks/`, task-runner `audit-*` targets),
  detect that and guide the build-out rather than failing opaquely.
- **`scaffold_lint.py` generalization:** replace the hardcoded `lint-knowledge` special-case in
  `dangling-skill-refs` with detection that resolves *any* non-`openspec-` skill token against the
  actual skill directory names — so both `knowledge-drift-review` and `run-audit` validate without
  a second hardcoded token.
- **AGENTS.md doc fixes** (in "Deterministic audit tooling"): mark the interpreter and the
  `just audit-*` example as per-repo / illustrative (not a promise a fresh repo already has them),
  point at the two now-distinctly-named tools, and reference the `run-audit` skill as the entry
  point.

## Capabilities

### New Capabilities

<!-- None. The run-audit skill deliberately gets NO capability spec: the deterministic-audit
     layer's contract lives in code docstrings + AGENTS.md by design (deterministic-tooling-layer
     decision D1), and the skill's existence/manifest-listing/findings-only integrity is enforced
     by scaffold_lint (manifest-completeness + dangling-skill-refs), not a spec. Adding a spec
     would break that established precedent for no gain. -->

### Modified Capabilities

- `knowledge-lint`: the skill rename touches **all 6 `lint-knowledge` occurrences** in
  `openspec/specs/knowledge-lint/spec.md` — not just paths. The delta updates: the Purpose-line
  prose (line 6, which describes the two tools by their now-*distinct* names — reworded so it no
  longer leans on the near-mirrored naming), the `judgment-layer-skill-detects-semantic-drift`
  requirement body + its `deterministic-pass-runs-first` and `skill-ships-single-path-detect-only`
  scenarios, and the `knowledge-lint-tooling-is-scaffold-managed` requirement body +
  `manifest-lists-linter-tooling` scenario. Every SHALL about the skill's single path,
  manifest-listing, and findings-only behavior carries over unchanged except for the name/path;
  design.md enumerates each occurrence.

## Impact

- **Scaffold-managed instruction surface:** `AGENTS.md`, `scripts/scaffold_lint.py` +
  `scripts/test_scaffold_lint.py`, the renamed skill dir + the new `run-audit` skill dir, and
  `scripts/scaffold_manifest.txt` — three manifest deltas: remove
  `.claude/skills/lint-knowledge/SKILL.md`, add `.claude/skills/knowledge-drift-review/SKILL.md`,
  add `.claude/skills/run-audit/SKILL.md` (missing any one breaks the manifest-completeness SEAL).
- **Spec:** `openspec/specs/knowledge-lint/spec.md` (delta — skill name/path).
- **Prose refs (per-repo, hand-updated here):** `knowledge/STATUS.md`,
  `knowledge/reference/resync-verification.md`, `knowledge/questions/knowledge-lint-follow-ons.md`.
- **Propagation:** scaffold-managed → a NEW sync batch to extrends + psc-monitor after this ships
  (extrends took the pre-rename state on 2026-07-03); the rename adds a tombstone-deletion step
  downstream (`rm -rf .claude/skills/lint-knowledge/` in each repo during that propagation batch,
  since the manifest has no delete verb). Not part of this change — tracked as a follow-on.
- **Deliberately NOT touched:** the historical `knowledge/decisions/INDEX.md` registry line for the
  `2026-07-02-knowledge-lint` change keeps its `lint-knowledge` mention (immutable historical
  record); the archived change dirs are likewise untouched.
- **No behavioral change to the deterministic scripts themselves** (`knowledge_lint.py`,
  `audit_bundle.py`, `audit_scope.py` are unchanged) — this is a naming + discoverability change.
