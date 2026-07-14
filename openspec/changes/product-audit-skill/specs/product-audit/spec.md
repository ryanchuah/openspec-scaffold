## ADDED Requirements

### Requirement: the-product-audit-protocol-is-a-scaffold-owned-operator-invoked-pull-only-single-session-skill
The promise-surface / business-thesis audit protocol SHALL be owned by the scaffold as a single skill (`.claude/skills/product-audit/SKILL.md`), operator-invoked and pull-only — never wired into session boot, `AGENTS.md`, archive, or any automatic trigger. Its object is the product's promise surface (pricing/landing/README/public-docs copy) and business thesis (pricing/ICP/GTM/regulatory-window/competitors), and its oracle is the code and the market — the inverse of every code-facing audit class. The audit SHALL produce findings only and MUST NOT modify product code (audit-then-fix). Unlike the multi-wave `correctness-audit`, `product-audit` SHALL run as a single bounded session (no durable resumable dossier), and therefore SHALL NOT carry an in-progress liveness obligation and needs no liveness lint; the only durable artifact it leaves — the claims ledger — is guarded by staleness, not liveness.

#### Scenario: invocation modifies no product code
- **WHEN** the operator invokes the skill and it surfaces a promise-surface defect
- **THEN** the skill records the finding and routes it, and makes no change to product code within the audit (remediation ships later as an ordinary OpenSpec change)

#### Scenario: never wired into an automatic trigger
- **WHEN** any session boot, archive, or lifecycle step runs
- **THEN** the product-audit skill SHALL NOT be invoked automatically — it fires only on explicit operator invocation

### Requirement: the-audit-commits-a-blind-attack-list-before-any-evidence
The audit SHALL begin by writing an adversarial attack list — the ways the promise surface and business thesis could be false — and committing it before any evidence is gathered, so the evidence pass cannot anchor the attack list to what was found. Attacks SHALL be enumerated, never tallied.

#### Scenario: attack list precedes evidence
- **WHEN** the audit starts
- **THEN** the blind attack list is written and committed before the evidence fan-out runs, defending against anchoring

### Requirement: evidence-is-gathered-through-a-five-lane-fan-out-both-halves-load-bearing
The audit SHALL gather evidence through five lanes: (1) implementation-as-sold (each promise mapped to its delivering code surface), (2) cost / critical-path, (3) repo + git-history + GTM-artifact sweep, (4) live-web regulatory status, (5) live-web competitive / TAM. The two web lanes SHALL ride the existing web-research convention — routed through subagents using `scripts/fetch_clean.py`, never the built-in `WebSearch` from the main thread. Both halves of the method are load-bearing: the blind attack list defends against anchoring, and the evidence fan-out surfaces what armchair reasoning cannot predict; a run that writes the blind list but skims the evidence pass is incomplete, because the highest-severity findings observed came from the evidence fan-out, not the blind list.

#### Scenario: web lanes use the research convention
- **WHEN** the regulatory or competitive lane needs live-web evidence
- **THEN** it is gathered through a subagent using `scripts/fetch_clean.py`, never via a main-thread `WebSearch` call

#### Scenario: evidence fan-out is not optional
- **WHEN** an audit writes the blind attack list but does not run the five-lane evidence fan-out
- **THEN** the audit is incomplete — both halves are required

### Requirement: each-attack-gets-one-recorded-disposition-and-the-audit-emits-a-machine-verdict
Every attack SHALL receive exactly one disposition from the fixed set `CONFIRMED` / `PARTIAL` / `SURVIVED-BY-THESIS` / `OPEN`, and attacks the thesis survives SHALL be recorded rather than dropped. The audit SHALL write a machine-discriminable verdict to disk: exactly one of `PRODUCT: CLEAN`, `PRODUCT: FINDINGS-ROUTED`, `PRODUCT: ESCALATE`. `ESCALATE` SHALL be a recommendation to charter a follow-up (a correctness-audit of a built-but-unsold feature, or an operator launch block) and SHALL NOT itself charter one.

#### Scenario: survived attack is retained
- **WHEN** an attack is dispositioned `SURVIVED-BY-THESIS`
- **THEN** it is recorded in the disposition table as a first-class outcome, never silently dropped

#### Scenario: verdict is machine-discriminable
- **WHEN** an audit session completes
- **THEN** exactly one `PRODUCT:` verdict line with one of the three values is written to disk

### Requirement: findings-are-surfaced-as-an-operator-ratification-menu-with-source-classed-web-claims
Findings SHALL be surfaced as an operator ratification menu — decisions to ratify, not observations — because the business thesis is the operator's to own; the audit surfaces and routes, and MUST NOT auto-decide a thesis question. Durable web-sourced claims recorded by the audit SHALL carry a source class at write time — `official` / `secondary` / `vendor-speculation` — and re-verification burden SHALL point at the non-official classes first; near-verbatim phrasing match to a promotional source is the circular-sourcing signature.

#### Scenario: thesis finding is ratified, not decided
- **WHEN** the audit surfaces a business-thesis finding (e.g. an accepted pricing risk)
- **THEN** it is presented to the operator as a decision to ratify, and the audit takes no auto-decision

#### Scenario: durable web claim carries a source class
- **WHEN** the audit records a durable web-sourced claim (e.g. a regulatory status) into a tracked reference
- **THEN** the claim is labeled `official` / `secondary` / `vendor-speculation` at write time

### Requirement: the-skill-ships-a-claims-ledger-convention-with-a-content-hashed-covered-file-manifest
The skill SHALL define and inline the claims-ledger convention: a per-repo file (canonical home `knowledge/reference/claims-ledger.md`) carrying the literal marker `format: product-audit/v1`, a `## Covered promise-surface files` manifest listing each covered file as `- <path> — sha256:<64-hex>` (the sha256 of that file's content at last reconciliation), and a `## Claims` table mapping every externally visible promise to its delivering code surface and the proving check that closes it. The skill SHALL inline the exact reconciliation command (`sha256sum <path>`) and procedure so an operator who sees the staleness lint fire has the fix in front of them. The audit protocol SHALL consult the entitlement-state reachability prompt (for every sold state, a user-reachable path to enter it must exist) and the severity-taxonomy-completeness prompt (a slot for external-promise/trust/legal harm, or a named exclusion — silence is the defect).

#### Scenario: ledger row maps promise to proving check
- **WHEN** the operator records a Pro-tier promise in the ledger
- **THEN** the row names the delivering code surface and the proving check (a `test:`/`check:` pointer, or a dated manual verification)

#### Scenario: reachability prompt catches a dead-but-correct differentiator
- **WHEN** a sold entitlement state's code path works but no user-reachable route enters it
- **THEN** the reachability prompt surfaces it as a finding that a behavior-only audit would pass

### Requirement: close-out-routes-findings-into-the-finding-closure-ratchet-with-no-new-machinery
At close, every generalizable finding SHALL run the finding-closure ratchet's three-question triage and land as a `knowledge/ratchet-log.md` registry line using the ratchet's existing five dispositions verbatim — no new close-out machinery and no new disposition keyword. The mapping SHALL be: a copy↔code claim closed with a real proving check → `test:<path>` / `check:<pointer>` where the pointer is the claim's ledger proving-check cell (a resolvable test/detector path, per the ratchet's live-pointer requirement); a copy↔code claim closed by correcting the copy with no enforcing check → `waiver:review-by <date>`; a pure business-thesis decision → `waiver:review-by <date>` (re-review date = the strategy-reference watch-list expiry); an `OPEN` attack → `open:since <date>`; a `SURVIVED-BY-THESIS` attack → no ledger entry. The skill SHALL carry a reciprocal awareness pointer back to `correctness-audit` (a built-but-unsold finding may warrant a correctness-audit of the undisclosed feature), closing the bidirectional handoff.

#### Scenario: copy-only fix takes a waiver disposition
- **WHEN** a copy↔code finding is closed by correcting the marketing copy with no enforcing test possible
- **THEN** its ratchet line carries `waiver:review-by <date>` with the rationale — never a silent prose close

#### Scenario: survived attack gets no ledger entry
- **WHEN** the audit closes with an attack dispositioned `SURVIVED-BY-THESIS`
- **THEN** no ratchet ledger entry is created for it

### Requirement: cadence-is-operator-driven-pre-launch-and-watch-list-not-recurring
The skill's cadence guidance SHALL be a pre-launch gate for product repos plus re-runs on strategy-reference watch-list expiry, and SHALL NOT be a recurring ceremony, a count-based due-signal, or any auto-run trigger. The skill SHALL never gate any commit, verify, CI, or lifecycle step.

#### Scenario: no automatic due-signal
- **WHEN** a repo accrues changes or commits over time
- **THEN** no automatic product-audit due-signal fires — the audit is run only when the operator chooses (pre-launch or on watch-list expiry)
