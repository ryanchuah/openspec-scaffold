## ADDED Requirements

### Requirement: an-in-progress-audit-remains-visible-and-uses-distinct-wave-namespaces
An in-progress audit SHALL remain visible as an Active item in `knowledge/questions/INDEX.md` referencing the dossier directory, from Wave 0 until close-out. The charter SHALL carry a `status:` line alongside its `format: correctness-audit/v1` marker, set to `in-progress` at Wave 0 and to `closed` only at close-out; an audit whose charter `status:` is anything other than `closed` is in-progress, and its dossier directory MUST be referenced by an Active questions item for the whole of that window. When a remediation program follows the discovery audit in the same dossier, it SHALL occupy a namespace distinct from the discovery `WAVE-N` rows (e.g. `REMEDIATION-N`), never a second run of the `WAVE-N` labels, so the discovery scope cannot be silently overwritten and its tail dropped. This closes the failure mode where a remediation program takes over the "wave" namespace and the discovery tail falls off with no descope decision, invisible because nothing external tracked the unfinished audit.

#### Scenario: in-progress audit is surfaced as an Active question
- **WHEN** a dossier's `CHARTER.md` carries `format: correctness-audit/v1` and a `status:` other than `closed`
- **THEN** an Active item in `knowledge/questions/INDEX.md` SHALL reference the dossier directory until close-out

#### Scenario: close-out removes the visibility obligation
- **WHEN** the audit closes and the charter `status:` is set to `closed`
- **THEN** the Active questions item MAY be removed and the audit no longer needs to be surfaced as active

#### Scenario: remediation does not reuse the discovery wave namespace
- **WHEN** a remediation program follows a discovery audit in the same dossier
- **THEN** it SHALL occupy a namespace distinct from the discovery `WAVE-N` rows, so no discovery wave is silently absorbed or dropped

### Requirement: close-out-includes-a-blind-coverage-gap-review
Audit close-out SHALL include a coverage-gap review that writes the full-audit dimension taxonomy blind — before reading the charter or dossier — and then diffs it against the chartered-and-executed coverage. Each dimension SHALL be classified as exactly one of `✅ covered`, `🟡 partial`, `📋 planned-never-run`, or `⬜ never-planned`; a `📋` or `⬜` classification names a scope gap the census cannot detect, because the census proves completeness only *within* the chartered scope and nothing else checks the scope itself. The review SHALL run both halves — the blind taxonomy, which defends against inheriting the charter's own blind spots, and an evidence fan-out over the real implementation, which surfaces gaps armchair reasoning cannot predict; a review that writes the blind taxonomy but skims the evidence pass is incomplete, because the highest-severity gaps observed came from the evidence fan-out, not the blind list. This review MAY also be run on demand for a stalled audit, not only at close-out.

#### Scenario: coverage-gap review runs at close-out
- **WHEN** an audit reaches close-out
- **THEN** a reviewer writes the dimension taxonomy blind, then classifies every dimension against chartered-and-executed coverage using the four markers

#### Scenario: a never-planned dimension is surfaced
- **WHEN** the blind taxonomy contains a dimension the charter never enumerated
- **THEN** it is classified `⬜ never-planned` and recorded as a scope gap rather than passing unseen because the census proved only within-scope completeness

#### Scenario: evidence fan-out is load-bearing
- **WHEN** the reviewer writes the blind taxonomy but does not run the evidence fan-out over the real implementation
- **THEN** the review is incomplete — both halves are required, because the highest-severity gaps come from the evidence pass, not the blind list

### Requirement: charter-scope-is-seeded-from-a-generic-dimension-checklist
Charter instantiation with no prior dossier SHALL consult a generic, protocol-level dimension checklist inlined in the skill when drawing the scope boundary. The checklist SHALL provide a grouped dimension seed, the named recurring blind-spot classes, and their widenings, as coverage-awareness prompts — distinct from the per-repo judgment (severity taxonomy, wave decomposition, verification-method map) the protocol deliberately leaves per-repo. Consulting the checklist is mandatory; the per-dimension outcome is judgment — a dimension deliberately ruled out of scope SHALL be recorded as such in the charter rather than silently omitted. The checklist SHALL remain a bounded reference list, not an execution handbook: blind-spot classes whose full audit mechanism belongs to a sibling product-surface audit (the promise-surface / business-thesis audit) SHALL be carried only as awareness pointers, never operationalized here.

#### Scenario: charter walk consults the checklist
- **WHEN** the operator instantiates a charter with no prior dossier
- **THEN** the charter-instantiation walk consults the inlined dimension checklist to draw the scope boundary

#### Scenario: an out-of-scope dimension is recorded, not dropped
- **WHEN** a checklist dimension is deliberately excluded from the audit scope
- **THEN** the charter records the exclusion explicitly rather than omitting the dimension silently

### Requirement: coverage-liveness-continues-after-close-out-via-a-post-close-ledger
After an audit closes, coverage SHALL be kept live by a post-close ledger seeded in the dossier directory at close-out. Any subsequent change whose diff touches a persistence path, a publish path, or writes evaluation ground truth SHALL append one ledger line at verify or archive time carrying the fields `commit`, `subsystem`, `wave-owner`, `spec?`, and `review-tier`. When the ledger's open set accumulates several persistence-touching entries, a mini-wave SHALL be cut from the ledger rather than relying on per-change verify passes alone, because every wave audits a point-in-time snapshot and code shipped afterward is unaudited by construction and wave-level scrutiny never re-fires. This ledger is the mirror image of the in-progress-visibility obligation: one defends the unfinished dossier, the other defends the finished one.

#### Scenario: a post-close persistence change is ledgered
- **WHEN** a change whose diff touches a persistence or publish path (or writes eval ground truth) ships after an audit has closed
- **THEN** one well-formed line carrying `commit`, `subsystem`, `wave-owner`, `spec?`, and `review-tier` is appended to the post-close ledger at verify/archive time

#### Scenario: the ledger open set triggers a mini-wave
- **WHEN** the post-close ledger accumulates several persistence-touching entries
- **THEN** a mini-wave is cut from the ledger rather than trusting per-change verify passes alone
