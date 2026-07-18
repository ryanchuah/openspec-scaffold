## Purpose

Define the protocol contract for the `security-audit` skill — a scaffold-owned, operator-invoked,
pull-only, **lane-split adversarial security audit**, the missing counterpart to the per-change,
diff-scoped security pass in `openspec-verify-change`. That pass sees one diff; this ceremony reads
the whole security surface as an attacker would. It closes a real gap: a repo can pass every
chartered correctness audit and still ship an account-takeover misconfiguration, because no
correctness charter's universe contains the security surface (each excludes it as "separate audit").
The contract standardizes the sequence — charter (lane selection + adversarial persona +
secrets-exclusion from external models) → a front-loaded deterministic scanner floor treated as a
floor-not-a-finder → per-lane adversarial passes (empirical-probe-first; confirm-the-negatives as the
clean-lane deliverable; orchestrator-only severity finalization) → independent refuter verification
(delegated, with money/abuse tradeoffs surfaced not auto-fixed) → a cross-lane completeness critic →
a machine-discriminable `SECURITY: CLEAN|FINDINGS-ROUTED|ESCALATE` verdict → finding-closure-ratchet
close-out — plus multi-session liveness (an unfinished lane-split audit cannot silently drop) and
explicit deploy-time deferral for lanes that need the live edge. It reuses existing scaffold
instruments (the `checks.py` security check-family, the shared delegation harness, the finding-closure
ratchet) rather than inventing parallel machinery, and it is audit-then-fix: it produces findings
only and modifies no product code, remediation shipping later as ordinary changes citing finding IDs.

## Requirements

### Requirement: security-audit-is-a-scaffold-owned-operator-invoked-pull-only-lane-split-skill

The scaffold SHALL ship an operator-invoked `security-audit` skill implementing a lane-split
adversarial security audit (this spec is the single normative home for the sequence, disposition
set, verdict values, and liveness/deferral rules; the skill cites it and adds operational detail).
It SHALL be **pull-only** — never wired into session boot, `AGENTS.md`, archive, CI, or any auto-run
trigger, and SHALL never gate a commit / verify / CI / lifecycle step. It SHALL be **audit-then-fix**:
it produces findings only and modifies no product code; remediation ships later as ordinary OpenSpec
changes citing finding IDs. The sole admitted mid-audit code change is the fix-now criterion —
hardening an audit **instrument** (a detector, a probe fixture), never product code.

#### Scenario: invocation modifies no product code
- **WHEN** the skill runs a lane and finds a defect
- **THEN** it SHALL record the finding and SHALL NOT modify product code to fix it (remediation is a
  later OpenSpec change citing the finding ID)

#### Scenario: never wired into an automatic trigger
- **WHEN** a repo integrates the scaffold
- **THEN** the `security-audit` skill SHALL NOT be referenced by any boot read, hook, archive step,
  or CI gate, and SHALL NOT block any commit/verify/CI/lifecycle step

### Requirement: a-charter-selects-and-prunes-lanes-adopts-an-adversarial-persona-and-excludes-secrets-from-external-models

The audit SHALL open with a charter that (a) enumerates the audit **lanes** applicable to the repo,
recording each inapplicable lane as **explicitly excluded** with a reason — never silently omitted;
(b) assigns each lane an **adversarial-researcher persona** framed as a concrete attack ("bypass this
control; show the exact payload"), not a posture question ("is this secure?"); and (c) records the
rule that `.env`, real secrets, private keys, and PII fixtures SHALL NOT be sent to any **external**
(delegated) model, because a delegated model is an external API. A known-safe placeholder/dev secret
MAY be discussed; a real production secret SHALL NOT enter any prompt.

#### Scenario: an inapplicable lane is recorded as excluded, not omitted
- **WHEN** a lane does not apply to the repo (e.g. no file-upload surface, no payment integration)
- **THEN** the charter SHALL record that lane as excluded with a reason, and SHALL NOT leave it
  silently absent

#### Scenario: delegated prompts exclude secrets
- **WHEN** a lane's finding is delegated to an external model for verification
- **THEN** the delegated prompt SHALL exclude `.env`, real secrets, private keys, and PII fixtures
  (a known-safe placeholder secret MAY be named)

### Requirement: a-deterministic-scanner-floor-is-front-loaded-and-treated-as-a-floor-not-a-finder

Before the LLM lanes, the audit SHALL run the repo's enabled deterministic security detectors (the
`checks.py` security check-family — gitleaks / osv-scanner / semgrep / bandit as wired) and dump
their output to an untracked report dir; the LLM lanes SHALL then **consume the reports** rather than
re-scanning. Scanner output SHALL be treated as a **floor, not a finder**: each scanner finding gets
true-positive / reachability triage before it is filed (a scanner's severity label is not a
finding), a scanner's silence is recorded as coverage, and a scanner **gap** (e.g. no JavaScript SAST
available) is recorded as a manual-coverage caveat so a re-review knows the clearance was manual.

#### Scenario: scanners run before the judgment lanes and dump to disk
- **WHEN** the audit begins
- **THEN** the enabled security detectors SHALL run first and write their output to the untracked
  report dir, and the LLM lanes SHALL consume that output rather than re-running the scan

#### Scenario: a scanner false-positive class is triaged, not filed
- **WHEN** a scanner emits findings that reachability/true-positive triage shows are safe (e.g. SAST
  flagging a parameterized query it cannot statically verify)
- **THEN** the audit SHALL record the triaged disposition and SHALL NOT file the scanner label as a
  finding

### Requirement: each-lane-is-an-adversarial-pass-that-prefers-empirical-probes-and-enumerates-confirm-the-negatives

Each lane SHALL be an adversarial pass over a scoped file-set. For any claim about
crypto/library/runtime behavior whose severity turns on version-specific behavior, the auditor SHALL
**run the one-liner probe** rather than reasoning from memory. Every **cleared** attack SHALL be
recorded together with the specific control that stops it — for a lane with no defect, the
enumerated attack list (each attack, each cleared, with its control) IS the deliverable a re-review
inherits. Finding severities SHALL be **provisional** until finalized by the orchestrator; an
executor/delegated model may draft a severity but SHALL NOT finalize it.

#### Scenario: a library-behavior severity call is grounded in an empirical probe
- **WHEN** a finding's severity depends on version-specific library behavior (e.g. whether a hash
  function truncates or raises on oversize input)
- **THEN** the auditor SHALL run the empirical probe and set severity from the observed behavior, not
  from remembered documentation

#### Scenario: a clean lane records the enumerated cleared attacks with their controls
- **WHEN** a lane surfaces no defect
- **THEN** the lane's recorded deliverable SHALL be the enumerated list of attempted attacks, each
  marked cleared with the control that stops it

### Requirement: findings-are-adversarially-verified-and-money-or-abuse-tradeoffs-are-surfaced-not-auto-fixed

Before a finding is recorded as real, it SHALL be **adversarially verified** by an independent pass
instructed to **refute** (not assess) it; when delegated, this uses the shared delegation harness
(a lane-scoped brief citing file:line, a machine-checkable verdict line, run in the background). The
orchestrator SHALL form its own read of the finding's crux **before** opening the refuter's verdict
— the refuter's verdict is itself a claim to verify. A finding that is a **monetization-integrity /
business-tradeoff / abuse-ceiling** decision (e.g. a free-tier quota race) SHALL be **surfaced to the
operator** with a concrete recommended fix for ratify-or-accept, rather than unilaterally changed;
data-exposure and authentication/authorization defects SHALL be fixed under the normal remediation
path.

#### Scenario: a finding is refuted-or-confirmed by an independent pass
- **WHEN** a candidate finding is drafted
- **THEN** an independent pass instructed to refute it SHALL run before the finding is recorded, and
  the orchestrator SHALL finalize the verdict and severity after forming its own read of the crux

#### Scenario: a money-adjacent race is surfaced for operator ratification, not auto-fixed
- **WHEN** a confirmed finding is a monetization-integrity / abuse-ceiling tradeoff rather than a
  data or auth breach
- **THEN** the audit SHALL surface it to the operator with a recommended fix for ratify-or-accept and
  SHALL NOT unilaterally change the behavior

### Requirement: a-cross-lane-completeness-critic-runs-before-the-verdict

Before the verdict, the audit SHALL run a **completeness-critic** pass over themes that per-lane
scoping can miss — checked as **themes, not files**: middleware/CSRF/CORS that touch every route;
revenue/entitlement integrity spanning billing and quota; info/PII leakage spanning handlers, email,
and logging; supply-chain touching the whole app; and outbound/SSRF surfaces. Any theme-level defect
this pass surfaces SHALL be recorded as a finding like any lane finding.

#### Scenario: a cross-lane theme is checked independent of the per-lane passes
- **WHEN** the per-lane passes are complete
- **THEN** the audit SHALL explicitly check the cross-lane themes as themes, and record any
  theme-level defect as a finding

### Requirement: the-audit-emits-a-machine-discriminable-verdict-and-routes-findings-into-the-finding-closure-ratchet

The audit SHALL write exactly one machine-discriminable verdict to disk: one of
`SECURITY: CLEAN`, `SECURITY: FINDINGS-ROUTED`, or `SECURITY: ESCALATE`. `ESCALATE` SHALL **recommend**
a follow-up (e.g. a dynamic pen-test drill, or chartering a deeper audit) and SHALL take **no**
chartering action itself. At close-out, for each **generalizable** finding the audit SHALL run the
finding-closure-ratchet three-question triage (real defect? → generalizable class? →
detectable/freezable?) as **orchestrator judgment, never delegated**, and append one
`knowledge/ratchet-log.md` line per qualifying class in the frozen format (`check:` > `test:` >
`waiver:` > `open:` > `grandfathered`). A `doc-only` / accepted-by-design close SHALL still carry a
ledger disposition (a `waiver:` with rationale), never a silent prose close.

#### Scenario: verdict is machine-discriminable
- **WHEN** an audit completes
- **THEN** the report dir SHALL contain exactly one `SECURITY:` verdict line with one of the three
  values

#### Scenario: close-out routes generalizable findings into the ratchet
- **WHEN** an audit ends `FINDINGS-ROUTED` with at least one generalizable finding
- **THEN** close-out SHALL append one conforming `knowledge/ratchet-log.md` line per qualifying class,
  with the ratchet triage performed by the orchestrator and never delegated

### Requirement: multi-session-audits-are-liveness-tracked-and-deploy-time-edge-lanes-are-deferred-not-dropped

Because a full audit is lane-split and MAY span sessions, an **unfinished** audit SHALL be referenced
by an Active `knowledge/questions/INDEX.md` item (naming the audit and its outstanding lanes) so it
cannot silently drop off every tracker; that item closes at close-out. Lanes that require the **live
deployed edge** (rate-limit efficacy through the real proxy/tunnel, TLS/HSTS, CORS/CSP as actually
served, open-port surface) SHALL be recorded as **deferred to deploy-time** with a pointer to where
they run — never marked `CLEAN` from code inspection alone.

#### Scenario: an unfinished audit is referenced by an Active liveness item
- **WHEN** an audit has run some but not all of its chartered lanes
- **THEN** an Active `knowledge/questions/INDEX.md` item SHALL reference the audit and its
  outstanding lanes until close-out

#### Scenario: a deploy-time lane is recorded deferred, not clean
- **WHEN** a lane's evaluation requires the live deployed edge that is not available at audit time
- **THEN** that lane SHALL be recorded as deferred to deploy-time with a pointer, and SHALL NOT be
  marked `CLEAN`
