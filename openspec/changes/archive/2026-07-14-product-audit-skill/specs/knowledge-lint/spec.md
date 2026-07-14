## ADDED Requirements

### Requirement: linter-detects-claims-ledger-staleness
The deterministic knowledge linter (`scripts/knowledge_lint.py`) SHALL detect staleness of a `product-audit/v1`-marked claims ledger by comparing the recorded content hash of each covered promise-surface file against the file's current content. The detector SHALL glob `knowledge/reference/*.md` and, for each file containing the literal marker `format: product-audit/v1`, parse its `## Covered promise-surface files` manifest (entries of the form `- <path> — sha256:<64-hex>`); for each parseable entry it SHALL flag a finding when the covered file is missing, or when the file's current `sha256` (of its raw bytes) differs from the recorded hash. The detector SHALL be marker-gated so a repo with no `product-audit/v1` ledger produces zero findings, keeping this repo and un-adopted downstream repos lint-clean under the live-tree gate. A manifest line that does not parse to a path plus a 64-hex sha256 SHALL be silently skipped (the detector guards staleness, not manifest format), and a validly-marked ledger with no manifest section or an empty manifest SHALL produce zero findings. The detector SHALL check staleness of *listed* files only — manifest completeness (a promise-surface file present on disk but absent from the manifest) is a coverage concern outside its scope. Like every knowledge-lint detector, it is detect-only, never rewrites tracked content, and SHALL be wired into `collect_findings()`.

#### Scenario: covered file drifted since reconciliation
- **WHEN** a `product-audit/v1`-marked claims ledger lists a covered file whose current content sha256 differs from the recorded hash
- **THEN** the linter emits a `claims-ledger-staleness` finding naming the drifted file

#### Scenario: listed covered file is missing
- **WHEN** the manifest lists a covered file that no longer exists on disk
- **THEN** the linter emits a `claims-ledger-staleness` finding naming the missing file

#### Scenario: no marked ledger keeps the tree clean
- **WHEN** a repo has no file under `knowledge/reference/` carrying `format: product-audit/v1`
- **THEN** the detector emits zero findings

#### Scenario: malformed and vacuous manifests are tolerated
- **WHEN** a marked ledger has a manifest line that is not `- <path> — sha256:<64-hex>`, or has no manifest section, or an empty manifest section
- **THEN** the detector silently skips the unparseable line(s) and emits zero findings for a vacuous manifest
