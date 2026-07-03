## ADDED Requirements

### Requirement: The broken-citation check skips legitimate citation notation
The broken-prose-path-citation check SHALL NOT false-positive on legitimate citation notation (this
becomes load-bearing because C promotes `knowledge_lint.py` to a live commit gate). Extending the
existing skip-ladder (which
already skips URLs, absolute paths, globs, `{…}` placeholders, non-path tokens, first-segment-not-a-
real-dir, and `EPHEMERAL_PATHS`), the check SHALL additionally treat the following as non-findings:
(a) brace-expansion patterns `{a,b}` and `{a..b}`; (b) literal date/period placeholders such as
`YYYY-Www`; (c) a trailing `::symbol` node-id (pytest/symbol reference) — resolved by stripping the
`::` suffix and existence-checking the file; (d) a trailing `:N-M` line range — resolved by stripping
the range and existence-checking the file; and (e) any citation rooted under the `output/` ephemeral
prefix. Each skip SHALL remain narrow enough that a genuinely-missing file still flags.

#### Scenario: brace-expansion patterns are not flagged
- **WHEN** a knowledge doc cites `` `eval/labels/2026-W2{3,4,5}.yaml` `` or `` `output/notability-eval.{md,json}` ``
- **THEN** the linter SHALL NOT flag it (a brace pattern is a deliberate notation, not a broken path)

#### Scenario: period placeholders are not flagged
- **WHEN** a doc cites `` `eval/labels/YYYY-Www.yaml` `` or `` `output/digest-{label}.md` ``
- **THEN** the linter SHALL NOT flag it

#### Scenario: symbol node-ids resolve against the file
- **WHEN** a doc cites `` `src/trendscope/extract.py::_normalize_tokens` `` and `src/trendscope/extract.py` exists
- **THEN** the linter SHALL NOT flag it (the `::symbol` suffix is stripped before the existence check)
- **AND WHEN** the underlying file does not exist, it SHALL still flag as genuine drift

#### Scenario: line ranges resolve against the file
- **WHEN** a doc cites `` `src/trendscope/scoring.py:490-524` `` and `src/trendscope/scoring.py` exists
- **THEN** the linter SHALL NOT flag it (the `:N-M` range is stripped before the existence check)

#### Scenario: output artifacts are ephemeral
- **WHEN** a doc cites a concrete path under `output/` (e.g. `` `output/digest-2026-W25.md` ``)
- **THEN** the linter SHALL NOT flag it (`output/` is treated as an ephemeral prefix)

#### Scenario: genuinely missing files still flag
- **WHEN** a doc cites `` `src/trendscope/gone.py` `` under a real top-level dir and the file does not exist and matches none of the skip forms
- **THEN** the linter SHALL still flag the unresolved citation (hardening does not blind the check to real drift)

### Requirement: Root-level handoff files are flagged
`knowledge_lint.py` SHALL flag any `HANDOFF*` or `HANDOVER*` file at the repository root, mechanizing
the knowledge-handoff-file decision (durable handoffs belong in the knowledge tree, not as tracked
root files). The sanctioned ephemeral `knowledge/HANDOFF.md` SHALL be exempt (it is inside the
knowledge tree, not at the root). This check rides the same live-tree gate as the other doc-lints.

#### Scenario: a root handoff file is flagged
- **WHEN** a file matching `HANDOFF*` or `HANDOVER*` exists at the repository root
- **THEN** the linter SHALL flag it as a finding

#### Scenario: the sanctioned in-tree handoff is exempt
- **WHEN** `knowledge/HANDOFF.md` exists (the sanctioned mid-session handoff location)
- **THEN** the linter SHALL NOT flag it
