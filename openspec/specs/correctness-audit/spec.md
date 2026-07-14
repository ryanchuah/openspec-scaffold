## Purpose

Define the protocol contract for deep LLM correctness audits: artifact shapes (charter /
census / FINDINGS), evidence-and-graduation discipline, dedup and class-naming duties,
wave mechanics and operator gates, and close-out routing into the finding-closure
ratchet. The protocol is owned by the scaffold as a single operator-invoked, pull-only
skill that standardizes mechanism while leaving product judgment (severity taxonomy,
wave decomposition, verification-method map, census content) per-repo.

## Requirements

### Requirement: the-audit-protocol-is-a-scaffold-owned-operator-invoked-skill
The deep LLM correctness-audit protocol SHALL be owned by the scaffold as a single
skill (`.claude/skills/correctness-audit/SKILL.md`), operator-invoked and pull-only —
never wired into session boot, archive, or any automatic trigger. The skill SHALL
standardize the protocol (artifact shapes, evidence discipline, wave mechanics,
close-out routing) and SHALL leave product judgment per-repo: the severity taxonomy
(derived from the product's worst invisible failure mode), the wave decomposition, the
verification-method map, and all census content. The skill SHALL discover per-repo
wiring by detect-and-explain: it MUST NOT auto-provision per-repo files or config
without walking the operator through instantiating the inlined templates.

#### Scenario: invocation with no dossier present
- **WHEN** the operator invokes the skill in a repo with no in-progress audit dossier
- **THEN** the skill walks the operator through instantiating the charter and census
  from its inlined templates (severity taxonomy derived, wave plan assigned, census
  seeded from the inventory fact), creating nothing silently

#### Scenario: invocation with an in-progress dossier
- **WHEN** the operator invokes the skill and a dossier with unfinished waves exists
- **THEN** the skill resumes from the dossier state on disk (charter wave status +
  census dispositions), not from conversational memory

### Requirement: the-dossier-is-the-durable-record-and-checkpoint-state
An audit's durable state SHALL live entirely in a tracked dossier directory
`knowledge/research/correctness-audit-<YYYY-MM>/` containing `CHARTER.md` (the single
governing document: scope, ground rules, severity taxonomy, wave plan with per-wave
status, verification-method map, prior-knowledge register pointer, and the literal
format marker line `format: correctness-audit/v1`), `CENSUS.md`, and
`FINDINGS-wave<N>.md` files. The charter SHALL record the path to the repo's
prior-knowledge register (suggested default
`knowledge/reference/known-findings-ledger.md`, format per the template inlined in the
skill), making the register a deterministic grep target for the `Prior:` dedup field. Probe scripts, scan JSON, and snapshots SHALL go to
untracked locations (`tmp/`, `output/`) as regenerable evidence, not record. Audit
waves SHALL NOT be run as OpenSpec changes; the dossier is the checkpoint state.

#### Scenario: session interruption mid-wave
- **WHEN** an audit session is interrupted after any bounded work slice
- **THEN** a fresh session resumes by reading the charter's wave status and the census
  dispositions from disk, with no work lost beyond the in-flight slice

### Requirement: the-census-is-the-completeness-proof-and-stopping-rule
The census SHALL hold exactly one disposition per in-scope surface, drawn from the
fixed set `AUDITED-clean` / `AUDITED-finding` / `LEAD-deferred` / `N/A-<reason>`. A
wave SHALL be declared complete only when its census slice has no undispositioned
rows; the audit SHALL be declared complete only when no census row anywhere is
undispositioned. Census rows are enumerated, never tallied (never-record-counts).

#### Scenario: wave self-declares complete with undispositioned rows
- **WHEN** a wave's census slice still contains a row with no disposition
- **THEN** the wave is not complete and the wave gate is not presented

#### Scenario: open-ended discovery bounded
- **WHEN** discovery work beyond the known lead list is performed in a wave
- **THEN** each surface it touches is dispositioned in the census, so "how much
  discovery is enough" is answered by census coverage, not executor self-declaration

### Requirement: findings-follow-the-standard-entry-contract
Every finding SHALL be one FINDINGS-file entry with ID `CA-W<wave>-<seq>` (matching the
shipped outstanding-fact default ID pattern `\b[A-Z]{2,}(?:-[A-Z0-9]+)?-\d+\b`) and the
fields: Statement; Evidence with a
method-named label from the fixed set `VERIFIED-BY-{repro|trace|test}` / `LEAD` /
`REFUTED` / `UNVERIFIABLE-HERE(<missing resource>)` (a bare "confirmed" is not a valid
label; a `VERIFIED-BY-repro` label without a named snapshot/fixture path is
disqualified); Severity (per-repo taxonomy value, PROVISIONAL until graduation);
`Prior:` (mandatory — `none (grep clean)` or `<ID> — distinct because <reason>`,
produced by grepping the dossier and the prior-knowledge register for the finding's
file path, function name, and candidate class slug before write-up); `Class:`
(mandatory-to-fill — a kebab-slug shared with the ratchet ledger's class slugs, or the
literal sentinel `none (one-off)` declaring the triage outcome Q2=no); Fix sketch; and
Effort (S/M/L). `UNVERIFIABLE-HERE` findings SHALL default to `Class: none (one-off)`
— an unconfirmed mechanism must not seed a ratchet class.

#### Scenario: duplicate mechanism about to be re-filed
- **WHEN** an author writes up a lead whose file path or mechanism already appears in a
  prior wave's findings or the prior-knowledge register
- **THEN** the `Prior:` grep surfaces the earlier ID and the entry either cites it with
  a distinctness reason or is folded into the existing finding

#### Scenario: one-off defect graduated
- **WHEN** a finding graduates that could not recur in sibling code
- **THEN** its entry carries `Class: none (one-off)` and no ratchet ledger entry is
  created for it

### Requirement: findings-graduate-only-through-adversarial-refutation-with-orchestrator-re-check
Every finding SHALL start as `LEAD`, and no severity SHALL be finalized until an
adversarial refutation pass (fresh context, explicit brief to refute) has run AND the
orchestrator has re-checked the refuter's verdict against source — a refuter's verdict
is itself a claim to verify, and the orchestrator forms its own read of the finding's
crux before opening the refuter's verdict. False premise → `REFUTED`; real-but-milder
mechanism → `VERIFIED-BY-*` with severity overruled downward. Severity and evidence
labels SHALL be finalized only by the orchestrator, never by the executor tier that
produced the draft. Each FINDINGS file SHALL carry an append-only **graduation log** at
its top recording every refutation session (date, IDs adjudicated, verdicts, and any
orchestrator overrules) — the durable evidence trail, kept separate from the in-place
field updates it authorizes. Graduation SHALL write the finding's final disposition
back to its census row. If a refuter discovers a materially similar real defect during
refutation, it SHALL be filed as a new lead immediately.

#### Scenario: refuter verdict is wrong
- **WHEN** a refutation pass returns REFUTED but the orchestrator's independent
  re-check finds the mechanism real
- **THEN** the finding graduates `VERIFIED-BY-*` with the overrule recorded in the
  graduation log

#### Scenario: finding premise is false
- **WHEN** the refutation demonstrates the finding's premise does not hold
- **THEN** the finding is labeled `REFUTED` and retained in the FINDINGS file as a
  first-class outcome, never silently deleted

#### Scenario: finding cannot be verified with available resources
- **WHEN** a finding graduates with an `UNVERIFIABLE-HERE(<missing resource>)` label
- **THEN** its census row disposition is set to `LEAD-deferred` and the finding is
  dispositioned by the operator at close-out

### Requirement: wave-work-is-sliced-checkpointed-and-operator-gated
Wave 0 SHALL precede findings work and verify the audit's own instruments (snapshot
tooling proven, deterministic baseline captured, any invariant "ruler" verified against
known-good fixtures before it is cited); mid-audit code changes SHALL be admitted only
to harden audit instruments, never the product (audit-then-fix). Delegated
investigation and refutation slices SHALL run via `opencode run` under the shared
delegation harness, sliced into bounded invocations (one lead investigation, one census
slice sweep, or one refutation batch per invocation) reusing only sanctioned timeout
budget pairs; each slice SHALL checkpoint one-line dispositions to the dossier before
returning. Judgment slices route to a pro-tier model, mechanical slices to a
flash-tier model. Every wave SHALL end at an explicit operator gate; executors MUST
NOT proceed past a wave gate unattended (an actively-occurring critical finding may be
escalated to the operator immediately).

#### Scenario: wave boundary reached
- **WHEN** a wave's census slice is fully dispositioned and its findings graduated
- **THEN** the orchestrator appends the triage-file lines, presents the wave-gate
  report, and stops until the operator confirms the next wave

#### Scenario: instrument found broken during Wave 0
- **WHEN** Wave 0 finds the audit's snapshot tooling or ruler invariant defective
- **THEN** fixing that instrument is in-scope (fix-now) and no findings work starts
  until the instrument is proven

### Requirement: every-finding-id-is-triage-referenced-and-close-out-routes-into-the-ratchet
The audit SHALL maintain `knowledge/questions/correctness-audit-<YYYY-MM>-triage.md`,
created at Wave 0 and appended at every wave gate with one line per newly graduated
finding (`- <ID>: <disposition> — <one-line essence>`); at audit close, still-ungraduated
findings (`LEAD-deferred` census rows, including `UNVERIFIABLE-HERE`) SHALL have their
IDs appended the same way — no finding ID leaves the audit without a triage reference.
At audit close, every graduated finding SHALL run the finding-closure ratchet's
three-question triage (Q1: real defect? → Q2: generalizable class? → Q3: mechanically
detectable or test-freezable?); qualifying classes SHALL land as
`knowledge/ratchet-log.md` registry lines using the ratchet's exact line format —
`- **YYYY-MM-DD** · <kebab-class-slug> · <disposition> — <essence>` — and its five
disposition keywords verbatim: `check:<pointer>`, `test:<path>[::<name>]`,
`waiver:review-by YYYY-MM-DD`, `open:since YYYY-MM-DD`, `grandfathered`.
`intentional-by-design` / `doc-only` closes SHALL carry a ledger disposition (typically
`waiver:review-by` with the rationale) rather than closing as prose. `REFUTED` and
Q2=no one-offs get no ledger entry. Close-out SHALL produce a remediation queue ranked by
shared code surface; the operator chooses the remediation posture at the close-out
gate. Remediation SHALL ship as ordinary OpenSpec changes citing finding IDs — never
inside the audit. Audit waves themselves are exempt from the multi-model verify stack:
the refutation-graduation pipeline is the audit's verification mechanism.

#### Scenario: refuted finding at close-out
- **WHEN** the audit closes with a finding labeled `REFUTED`
- **THEN** its ID appears in the triage file (so the untriaged-age lint never fires on
  it) and no ratchet ledger entry is created

#### Scenario: generalizable class closed doc-only
- **WHEN** a graduated, generalizable finding is closed by a documentation correction
  with no enforcing check or test
- **THEN** the class gets a ratchet ledger line with a `waiver:review-by` disposition
  recording the rationale — never a silent prose close

#### Scenario: audit closes with verified findings
- **WHEN** the close-out gate is reached with verified findings present
- **THEN** the operator receives the ranked remediation queue and the recorded triage
  outcomes, and chooses fix-promptly or defer-all explicitly

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
