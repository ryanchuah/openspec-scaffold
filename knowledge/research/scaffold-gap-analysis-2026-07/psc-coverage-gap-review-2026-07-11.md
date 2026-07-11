# psc-monitor coverage-gap review (2026-07-11) — deltas for the correctness-audit skill (OW-15 evidence)

**Provenance.** psc-monitor ran a departing-principal coverage-gap review of its correctness-audit
program (`plans/audit-correctness-quality/coverage-gaps-2026-07-11.md` in that repo, Fable
session). Method: a 45-dimension "what would a full correctness audit cover" taxonomy was written
**blind** (before reading the audit charter or any prior-review record — bias control), then four
read-only subagent surveys mapped actual coverage, then the two were diffed. This doc extracts the
scaffold-generalizable results as evidence for **OW-15**; psc-specific remediation stays in
psc-monitor's own queue.

**Why this lands here even though OW-5 already extracted psc's method:** OW-5's
`research/psc-audit-method.md` distilled how psc *ran* its audit (charter/census/wave shape).
This review found how that method **failed at the program level** — two failure modes the frozen
OW-5 design does not cover, plus scope-dimension content the charter template could seed with.
Checked against the frozen `specs/correctness-audit/spec.md` before writing this: no overlap.

---

## 1. Observed failure mode A — silent wave-drop (audit liveness)

psc-monitor's governing brief planned five discovery waves (0–4). Waves 0–2 ran and produced 23
verified findings + ~30 graduated LEADs; then the **remediation** program took over the "wave"
namespace (remediation waves A–G), and discovery Waves 3–4 — fully specified: time/clock,
billing/entitlement census, ops floor, env silent-no-op census, tests/tooling, frontend —
disappeared from every tracker (STATUS, questions INDEX, decisions INDEX, the remediation plan)
with **no recorded descope decision**. The audit was incomplete by its own done-criterion and
nothing surfaced that.

**What the frozen OW-5 design already covers:** the dossier carries per-wave status; the census
is the stopping rule ("audit complete only when no census row is undispositioned"); the skill
resumes from dossier state *when invoked*.

**What it doesn't:** the skill is pull-only and operator-invoked — if the operator stops invoking
it (because a successor program grabbed attention, as happened here), the incomplete dossier is
invisible. Dossier-internal state cannot defend against the dossier not being read.

**Delta 1 (OW-15): audit-liveness visibility.**
- An audit with unfinished waves SHALL be represented by an Active item in
  `knowledge/questions/INDEX.md` from Wave 0 until close-out (close-out removes it).
- Extend OW-5's dossier lint (knowledge-lint delta): dossier present with wave status ≠ complete
  AND no Active questions item referencing the dossier path → drift finding.
- Charter template note: discovery waves and remediation waves MUST use distinct namespaces
  (psc's collision — both called "waves" — is what let the tail fall off).

## 2. Observed failure mode B — scope blind spots (nothing audits the scope itself)

The census proves completeness **within** the chartered surface list. It structurally cannot
catch a dimension the charter never enumerated — no census row ever exists for it. In psc-monitor
five dimensions were never chartered in any wave, and one of them was an S4-class live gate in a
heavily-audited repo: **no implemented backup covered any non-reconstructible store** (user
accounts, alert history, the GDPR-erasure register, billing linkage — while trackers said backups
were "✅ satisfied" because the re-derivable bulk data was covered).

**Delta 2 (OW-15): chartered close-out coverage-gap review.** At audit close (or on demand for a
stalled audit), a reviewer writes the full-audit dimension taxonomy **blind — before reading the
charter or dossier** (reading them first anchors the reviewer to the charter's own blind spots),
then diffs it against chartered+executed coverage, classifying each dimension
✅ covered / 🟡 partial / 📋 planned-never-run / ⬜ never-planned. Cost in psc-monitor: one
session, four read-only subagent surveys. Yield: one new S4 gate, the wave-drop discovery, and a
ranked residual list.

**Delta 3 (OW-15): scope-seeding checklist.** The charter-instantiation walk (OW-5's "invocation
with no dossier" scenario) SHOULD consult a generic dimension checklist when drawing the scope
boundary — protocol-level content, distinct from the per-repo judgment (severity taxonomy, wave
decomposition) that OW-5 correctly leaves per-repo. Seed checklist in §4.

## 3. Named recurring blind-spot classes (checklist candidates with teeth)

Concrete classes the psc review caught that generalize to any repo this skill audits:

1. **Backup completeness of NON-reconstructible state.** Enumerate stores by
   reconstructible-vs-not; verify every non-reconstructible store has an implemented (not
   documented-as-planned) backup path; restore drills must exercise the non-reconstructible tier,
   not just the re-derivable bulk.
2. **Cutover/deploy-day as ONE sequence.** Each step individually verified ≠ the sequence
   verified; interactions between migrations, sweeps, first-load, and cron installation live
   between the checklist rows.
3. **Provider feedback channels, not just request paths.** Bounce/complaint handling,
   webhook-miss reconciliation (is external-service truth ever re-synced, or is state
   event-delivery-only?).
4. **Policy-without-mechanism.** Retention/erasure policies whose enforcement code doesn't exist;
   compliance docs that presuppose infrastructure (psc: "data ages out of backup rotation" argued
   about a backup that didn't exist).
5. **Phantom dev tooling.** Declared ≠ invoked (psc: pytest-cov in the dependency manifest,
   never run with `--cov` anywhere). Preflight should verify invocation sites, not declarations.
6. **Partial-✅ dispositions.** A "satisfied/complete" claim that covers a subset of the surface
   (backups "✅" = zips only). Dispositions should name what a ✅ excludes.
7. **Point-in-time audits with no durable convention.** A traceability/consistency property
   audited once (psc: spec↔test mapping, done well, then left to rot with no mechanical link)
   needs either a convention or an explicit re-audit cadence — otherwise it decays silently.
8. **At-rest invariant census at production scale.** The core data structure's defining
   invariants checked against the real accumulated store, not fixture-scale tests (psc: the SCD
   chain's no-overlap invariant was enforced nowhere and lint-checked nowhere over 15M rows).

## 4. The blind-taxonomy seed (genericized; 45 dimensions, 11 groups)

Written blind in psc-monitor, genericized here. Use as the charter-walk checklist (Delta 3) and
as the close-out reviewer's starting frame (Delta 2 — the reviewer still writes their own blind
first, then may union with this list).

- **A. Specification level:** spec↔intent (specs can be consistent and wrong) · spec↔impl
  conformance · spec↔test traceability with rot protection · delta-spec sync integrity
  (specs ≡ sum of applied deltas).
- **B. Data model & data-at-rest:** constraint completeness census (invariant → schema / app
  code / nowhere) · core-structure invariants at rest on the REAL store · cross-store orphan
  census (unFK'd logical keys) · migration-chain ≡ fresh-schema equivalence · NULL-semantics
  ledger per column · unicode/collation/type fidelity.
- **C. Domain semantics:** upstream-contract conformance + format-evolution canary · event/diff
  taxonomy completeness vs product promise ("every upstream transition → output or
  documented-none") · matching/resolution soundness vs ground truth · output-surface semantics
  (does the report answer what the reader thinks it answers; as-of semantics) · time/clock
  semantics (host vs DB clock, boundaries, timezones).
- **D. State machines, concurrency, idempotency:** lifecycle transition tables with no undefined
  holes · idempotency of every mutating job (re-run after crash at ANY point) · overlap/TOCTOU
  guards · transaction-boundary walk (what commits atomically; crash-between-commits state).
- **E. Failure modes & recovery:** silent-failure census (warn-and-continue,
  empty-looks-like-success, swallowed exceptions) · crash-recovery per pipeline stage ·
  partial-input handling · **backup completeness of non-reconstructible state + tested restore**.
- **F. Interface contracts:** API response-shape/error/pagination consistency · frontend
  correctness (edge values, empty states, validation parity) · outbound-content correctness
  (what the user actually sees vs what the system meant) · third-party contract fidelity
  including feedback channels (bounces, replays, reconciliation).
- **G. Money & entitlement:** entitlement matrix (account state × feature × surface, every cell
  enforced and tested) · external-truth reconciliation (missed-event drift repair) · quota/limit
  arithmetic (boundaries, off-by-one, concurrent consumption).
- **H. Test-suite quality:** mutation resistance / assertion strength · coverage dark spots
  (and coverage tooling actually running) · fixture realism (scale AND shape) · mock-fidelity
  ledger (which mocks were ever validated live) · order/isolation robustness.
- **I. Operational correctness:** cron/schedule audit vs intent (incl. committed-template vs
  live drift) · config/env census (silent behavior changes on absent/malformed values) ·
  deploy-day integrated dry-run · observability sufficiency map (failure class → which signal
  fires; "quiet because healthy" vs "quiet because dead").
- **J. Compliance-mechanism correctness (non-security):** suppression/redaction completeness
  across ALL output surfaces · retention/erasure enforcement mechanisms exist and run ·
  subject-access export completeness.
- **K. Meta/process:** audit-blind-spot review (this very step) · fix regression protection
  (every remediation carries a reintroduction-catching test) · knowledge/doc drift vs reality.

## 5. Routing

Queued as **OW-15** (OUTSTANDING-WORK.md, this dir): SMALL–MEDIUM amendment to the
`correctness-audit` capability, **apply strictly after OW-5 lands** (it amends what OW-5
creates); Opus end-to-end; standard escalation caveat. Alternative at operator discretion: fold
into OW-5's verify session as an immediate follow-on change. The OW-5 change dir's `notes.md`
carries a pointer so the apply/verify session sees this without reopening the freeze.
