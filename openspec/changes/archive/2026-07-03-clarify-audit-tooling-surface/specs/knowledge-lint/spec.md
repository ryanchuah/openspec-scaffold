## MODIFIED Requirements

### Requirement: judgment-layer-skill-detects-semantic-drift

A `knowledge-drift-review` skill SHALL exist at `.claude/skills/knowledge-drift-review/SKILL.md` (one path, discovered
by both the Claude and OpenCode harnesses; no `.opencode/` copy) defining an operator-invoked LLM
judgment pass that detects the drift a deterministic linter cannot see. It SHALL FIRST run
`scripts/knowledge_lint.py` to clear the cheap deterministic findings, and only THEN perform the LLM
judgment sweeps (so the expensive pass is not spent on drift the linter already catches). It SHALL be
**detect-only** (it produces findings and SHALL NOT rewrite prose) and SHALL be a periodic/on-demand
pass — NOT run on every archive. Its judgment sweeps SHALL cover: (a) stale "not yet built / planned /
designed-not-built" claims that contradict a shipped `openspec/changes/archive/` entry or
`knowledge/STATUS.md`; (b) intra-doc contradictions; (c) buried operator/pre-prod items present in a
README/runbook but absent from `knowledge/questions/INDEX.md` Active.

#### Scenario: deterministic-pass-runs-first
- **WHEN** the `knowledge-drift-review` skill is invoked
- **THEN** it SHALL run `scripts/knowledge_lint.py` before beginning its LLM judgment sweeps

#### Scenario: stale-not-built-claim-flagged
- **WHEN** a tracked doc describes a feature as "not yet built"/"planned" that a shipped archive entry or `knowledge/STATUS.md` records as shipped
- **THEN** the skill SHALL flag the contradiction

#### Scenario: intra-doc-contradiction-flagged
- **WHEN** two passages within one tracked doc assert contradictory facts (e.g. two lists of different length for the same set)
- **THEN** the skill SHALL flag the intra-doc contradiction

#### Scenario: buried-gate-item-flagged
- **WHEN** a README/runbook names a real operator or pre-production gate that is absent from `knowledge/questions/INDEX.md` Active
- **THEN** the skill SHALL flag the buried item

#### Scenario: skill-ships-single-path-detect-only
- **WHEN** the skill is added to the scaffold
- **THEN** it SHALL exist only at `.claude/skills/knowledge-drift-review/SKILL.md` (no `.opencode/` copy), and running it SHALL produce findings only, modifying no tracked file

### Requirement: knowledge-lint-tooling-is-scaffold-managed

The knowledge-lint tooling SHALL be scaffold-managed: `scripts/knowledge_lint.py`, its test file
`scripts/test_knowledge_lint.py`, and `.claude/skills/knowledge-drift-review/SKILL.md` SHALL be listed in
`scripts/scaffold_manifest.txt` so `scripts/sync_scaffold.py` propagates them byte-identical to every
downstream repo. The per-repo `audit.toml` SHALL NOT be added to the manifest (it is per-repo config,
not scaffold-managed).

#### Scenario: manifest-lists-linter-tooling
- **WHEN** `scripts/scaffold_manifest.txt` is read
- **THEN** it SHALL contain entries for `scripts/knowledge_lint.py`, `scripts/test_knowledge_lint.py`, and `.claude/skills/knowledge-drift-review/SKILL.md`

#### Scenario: per-repo-config-not-scaffold-managed
- **WHEN** the manifest is checked for `audit.toml`
- **THEN** `audit.toml` SHALL NOT be a manifest entry (per-repo config stays per-repo)
