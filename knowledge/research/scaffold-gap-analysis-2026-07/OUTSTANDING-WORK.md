# OUTSTANDING WORK — scaffold hardening from downstream audit evidence

**Source of truth for this backlog.** Wave 1 (OW-1..6, defect-prevention) derived from
`SYNTHESIS.md` (this dir); wave 2 (OW-7..14, workflow efficiency) derived from
`knowledge/research/workflow-audit-2026-07-11/AUDIT.md`. All items are **PARKED** (see
disposition at bottom) — none blocks the current session. Each is a candidate OpenSpec change
in *this* (scaffold) repo; landing it here propagates to `extrends` + `psc-monitor` via
`sync_scaffold.py`.

Legend — **Orch** = who should orchestrate: **Fable** (reserve for novel, high-blast-radius
design) vs **Opus** (well-specified design + all apply/verify orchestration; apply itself is
delegated to deepseek/sonnet regardless).

---

## OW-1 · Test-quality detector + verify lens  ·  Tier: MEDIUM  ·  Orch: **Opus** (end-to-end)
**Why:** GAP 3 — the cheapest, highest-yield fix; a known pattern (AST lint), no novel design.
**Scope:** new `checks.py` detector (enabled by default) flagging: tautological/forced-green
asserts (`or True`, empty test bodies), discarded return flags (`count, _ = …`), self-mocking
the module-under-test, unfrozen clocks in tests. Add a verify **lens** question: "would this
test fail if the behavior broke?" Ship as scaffold-managed; propagate.
**Evidence it would have paid off:** extrends TA-1/TQ-3 (13+), TA-3 (25+, caused ING-1 to ship
invisibly), TQ-2 (found by two audits); psc TQ-WEAK/TQ-FLAKY (23).
**Effort:** ~1–2 days. **Deps:** none. Do first.

## OW-2 · Lesson→check ratchet + per-repo invariant framework  ·  Tier: COMPLEX  ·  Orch: **Fable** (explore+propose) → Opus (apply/verify)
**STATUS 2026-07-10: PROPOSE COMPLETE — PAUSED AT APPLY (operator-mandated pause).**
Operator directed OW-2 be worked ahead of OW-1 (OW-1 is NOT a prerequisite). All 4 artifacts
frozen in `openspec/changes/lesson-check-ratchet/` (proposal, design, 2 spec deltas, tasks),
each through a deepseek-v4-pro review round: direction gate AGREE, proposal AGREE, design
PASS, specs PASS, tasks AGREE — zero 🔴 anywhere; every 🟡 fixed pre-freeze. Research inputs
checkpointed under the change dir's `research/`.
- **Park verdict: PARKED apply does NOT block OW-3.** OW-3's stated dependency is OW-1 or
  OW-4 (the freed verify pass needs a lens to point at), not OW-2. Nothing time-sensitive.
- **Apply/verify orchestrator: Opus** (Fable NOT needed). The frozen artifacts specify
  contracts, exit codes, config keys, insertion points, and literal ledger lines; apply is
  delegated to deepseek-flash regardless, and verifying a well-specified frozen change is
  within Opus's capability. **One caveat for the Opus session:** if verify surfaces a
  DESIGN-level defect (not an implementation bug), stop and escalate to the operator or a
  Fable session rather than redesigning mid-verify.
- Remaining Fable-worthy work in this backlog: OW-3's keep/drop call at propose, OW-5/OW-6
  design.
**Why:** GAP 1 — the compounding win. Today a found bug becomes prose in `lessons.md` and the
class stays open; sibling instances re-ship (proven in both repos).
**Scope (needs real design — hence Fable):** (a) a scaffold *rule* that a generalizable finding
is not "closed" until it has an enforcing check or a frozen regression test; (b) a low-friction
framework for a repo to register a domain-invariant detector (generalize the `data-lint`
backend); (c) how the archive/audit close-out routes findings into the ratchet without
bureaucracy. Get the ergonomics right or it will be ignored.
**Effort:** ~1 week design + build. **Deps:** none, but unlocks OW-5/OW-6's value.

## OW-3 · Verify-stack redirect (breadth → lens diversity)  ·  Tier: MEDIUM (high blast radius)  ·  Orch: **Fable** (propose) → Opus (apply/verify)
**STATUS 2026-07-10: PROPOSE COMPLETE — PAUSED AT APPLY (operator-mandated pause).**
All artifacts frozen in `openspec/changes/verify-stack-redirect/` (tasks.md, 2 spec deltas,
notes.md acceptance criteria): direction gate PREMISE: AGREE (round 1, zero 🔴, both 🟡
resolved into the brief); artifact review round 1 PASS + PREMISE: AGREE, zero 🔴, both 🟡
fixed pre-freeze. Design + evidence: change dir `explore-brief.md`, `premise-review.md`,
`research/` (touch-surface inventory; per-pass yield mining). Decisive evidence: across ~40
multi-model-verified changes in 3 repos, the flash same-lens pass **never uniquely caught a
non-trivial defect** (3 cosmetic nits total), while lens-diverse gates (security, simplicity)
caught critical defects both model passes rated clean. New shape: MEDIUM self→pro; COMPLEX
self→pro→flash **lens pass** (test-quality default / data-scale for data-path; prompts inline
in the verify skill); SMALL unchanged. Key design call: a lens is a *prompt*, not a detector —
**OW-3's previously-stated dependency on OW-1/OW-4 is dissolved**; their detectors later feed
the lens.
- **Park verdict: PARKED apply does NOT block anything.** No backlog item depends on OW-3's
  apply; the only cost of parking is that every MEDIUM/COMPLEX verify keeps paying the
  zero-yield third full-suite flash pass until it lands (waste, not risk). Recommend batching
  OW-3's apply into the same Opus session as OW-2's apply.
- **Apply/verify orchestrator: Opus** (Fable NOT needed). Tasks carry exact anchors/wording
  intents; budgets pinned (780/-k 15, budget-agreement lint guards them); apply is delegated
  to deepseek-flash regardless. Verify THIS change under current (pre-change) semantics =
  self + pro (see notes.md self-reference note). **Same escalation caveat as OW-2:** a
  DESIGN-level defect at verify (lens contract wrong, unforeseen chain interaction) → stop
  and escalate to operator/Fable; implementation bugs are normal defect-path work.
**Why:** GAP 5 / token-waste answer. self→pro→flash run the *same* checklist; the third pass
buys model weight, not a new question, and the bugs walked through all three.
**Scope:** keep self + ONE independent model pass as the diversity guard; reinvest the third
invocation into a lens the stack lacks (route it to OW-1's test-quality pass or OW-4's
data-scale pass). Drop the same-lens flash pass on MEDIUM; make the third pass lens-diverse on
COMPLEX. Touches verify SKILL + AGENTS.md roles + delegation harness — **governs every
downstream change's verify, so Fable makes the keep/drop call** to avoid weakening a
load-bearing gate.
**Effort:** ~1 day (mostly skill/AGENTS edits + careful review). **Deps:** best landed with OW-1
or OW-4 existing, so the freed pass has a lens to point at. **Net: cheaper AND better.**

## OW-4 · Data-scale detector + verify rule  ·  Tier: SMALL–MEDIUM  ·  Orch: **Opus** (end-to-end)
**Why:** GAP 4 — "mind data scale" is prose; unbounded `fetchall()` recurred anyway.
**Scope:** detector for unbounded-query / `fetchall()`-on-unbounded; verify rule that a
data-path change requires either an at-scale run or a recorded bounded-domain argument in
`notes.md`. **Effort:** ~1 day. **Deps:** none.

## OW-5 · `correctness-audit` scaffold skill  ·  Tier: COMPLEX  ·  Orch: **Fable** (design) → Opus (apply/verify)
**STATUS 2026-07-11: PROPOSE COMPLETE — PAUSED AT APPLY (operator-mandated pause).**
All 4 artifacts frozen in `openspec/changes/correctness-audit-skill/` (proposal, design, 2 spec
deltas — new `correctness-audit` capability + `knowledge-lint` dossier-lint delta — tasks), each
through deepseek-v4-pro review: direction gate AGREE (round 1), proposal AGREE (round 1), design
PASS (2 rounds — round 1 caught 2 🔴: REFUTED/one-off findings escaping the 14-day untriaged lint,
fixed via a per-wave-gate triage file; missing token-set edit), specs PASS (2 rounds — round 1
caught 1 🔴: graduation log undefined), tasks PASS (round 1). Zero 🔴 outstanding; every 🟡 fixed
pre-freeze; `openspec validate --strict` clean (validate-at-freeze run this time — finding 3 from
the OW-3 session applied procedurally). Research + explore artifacts in the change dir per D8.
Direction: standardize the audit PROTOCOL (single charter with `format: correctness-audit/v1`
marker, census-as-stopping-rule, FINDINGS contract with `Prior:` dedup field + `Class:` slugs
shared with the ratchet ledger, refuter-overrule graduation, marker-gated dossier lint,
ratchet-routed close-out); severity taxonomy and wave decomposition stay per-repo.
- **Park verdict: PARKED apply blocks NOTHING.** OW-3 has no dependency on OW-5 in either
  direction; no backlog item waits on OW-5's apply. OW-5's own apply is gated on OW-2's apply
  (ratchet must be live). Recommended batch for one Opus session: **apply OW-2 → OW-3 → OW-5**
  (OW-2 first for the ratchet; OW-3 before OW-5 preferred so OW-5's verify runs under the new
  lens contract — see change notes.md).
- **Apply/verify orchestrator: Opus** (Fable NOT needed). Contracts, verbatim formats, anchors,
  and budgets are pinned in the frozen artifacts; apply is delegated to deepseek-flash
  regardless. **Escalation caveat (same as OW-2/OW-3, plus one):** implementation bugs and prose
  deviations from the frozen templates are normal defect-path work; a DESIGN-level defect
  (ratchet interface doesn't fit as frozen, census/stopping-rule contract wrong) → stop and
  escalate to operator/Fable. Reminder: OW-2's apply session makes its one-word normative fix
  first (New findings item 1).
**Why:** GAP 6 — both repos hand-rolled the LLM correctness audit (CHARTER/CENSUS/waves/oracles)
differently; the scaffold owns only the deterministic `run-audit`. (psc-monitor literally ported
extrends' playbook and re-derived it by hand — the pattern already propagates, just without an owner.)
**Scope:** a skill standardizing the wave/charter/census shape that **routes every generalizable
finding into OW-2's ratchet** on close. **Effort:** ~3–4 days. **Deps:** apply-order dependency on
OW-2 only (propose can proceed against frozen contracts); no OW-3 interaction in either direction.

## OW-6 · Cadenced composition-audit  ·  Tier: COMPLEX (was MEDIUM–COMPLEX; classified at explore)  ·  Orch: **Fable** (design) → Opus (apply/verify)
**STATUS 2026-07-11: PROPOSE COMPLETE — PAUSED AT APPLY (operator-mandated pause).**
All 4 artifacts frozen in `openspec/changes/composition-audit-cadence/` (proposal, design,
3 spec deltas — new `composition-audit` capability + `outstanding-work-view` +
`knowledge-lint` — tasks), every review round PASS with **zero 🔴 on round 1** (proposal
AGREE; design 3🟡; specs 5🟡, cross-change collision check vs OW-2/OW-5 deltas explicitly
clean; tasks 2🟡 — every 🟡 fixed pre-freeze), `openspec validate --strict` clean at freeze
(validate-at-freeze applied), zero reviewer-invocation crashes. Direction gate at explore:
PREMISE: AGREE round 1 (two 🟡 resolved into the brief: composition-discriminable anchor so
run-audit tags never silently reset the cadence clock; honest pull-surfaced-signal framing).
Key design judgment: **the trigger is the product** — both repos had all instruments and
lessons; nothing ever named the occasion. Shape: (1) deterministic count-based due-signal
(archived-changes-since-composition-anchor ≥10 OR commits ≥100, per-repo keys) in the
`outstanding` fact + `inventory` sibling anchor; (2) operator-invoked `composition-audit`
skill (one-shot `checks.py --report --include jscpd/vulture/radon` + baseline delta +
D5-shape pre-digest + bounded top-K=5 judgment pass) with machine verdict
`COMPOSITION: CLEAN|FINDINGS-ROUTED|ESCALATE`; (3) close-out routes into OW-2's ratchet
(orchestrator-performed triage per OW-2's SHALL) and lays the `audit/<date>-composition`
anchor. Honest limit stated in-artifact: detectors catch only the narrow mechanical slice
(~30+/~36 evidence classes needed LLM judgment) — the pass's value is occasion + early
mechanical catch + standing escalation point into OW-5.
- **Park verdict: PARKED apply blocks NOTHING — including OW-3.** OW-3 has no dependency
  on OW-6 in either direction (its OW-1/OW-4 dependency was dissolved at its own propose;
  OW-6 depends on OW-2/OW-5, not OW-3). Cost of parking: downstream repos keep accruing
  unreviewed composition debt — waste/risk-accumulation, not a blocker.
- **Apply/verify orchestrator: Opus** (Fable NOT needed). Contracts, exact anchors
  (file:line, all 12 reviewer-verified), formats, defaults, and insertion points are
  pinned in the frozen artifacts; apply is delegated to deepseek-flash regardless.
  **Standard escalation caveat:** implementation bugs are normal defect-path work; a
  DESIGN-level defect at verify (trigger semantics wrong, ceremony contract doesn't fit,
  ratchet seam mismatch surfacing during OW-2's apply) → stop and escalate to
  operator/Fable. See change `notes.md` for the verify-semantics note (under OW-3's new
  chain if batch order holds: lens = test-quality).
- **Recommended single Opus batch: apply OW-2 → OW-3 → OW-5 → OW-6** (hard order: OW-2
  before OW-6 — ratchet ledger must exist; OW-5 before OW-6 — ESCALATE cites its skill).
  With OW-6 frozen, the batch closes the entire Fable-tier design backlog; OW-1/OW-4
  remain Opus end-to-end greenfield.
**Why:** GAP 2 — verify is single-diff-scoped; a subsystem built from many approved changes is
never reviewed as a whole. Whole-repo detectors exist but are off-by-default and cadence-less.
**Scope:** wire `jscpd`/`vulture`/`audit_scope.py scan`/`knowledge-drift-review` into a
first-class, triggered composition pass; feed OW-2. **Effort:** ~2–3 days. **Deps:** propose
proceeds now against OW-2/OW-5 frozen contracts (same pattern OW-5 used); apply gated on OW-2's
apply and ordered after OW-5's (ESCALATE references the correctness-audit skill).

---

## Wave 2 — workflow-efficiency items (2026-07-11 Fable session)

Full evidence, design calls, and non-findings: `knowledge/research/workflow-audit-2026-07-11/AUDIT.md`
(incl. the addendum answering the boot-read sanity check and the delegation-forgetting report).
**All wave-2 items: Orch Opus end-to-end** — the Fable-tier judgment each needed is already made and
recorded in that document. Standard escalation caveat applies to every item (DESIGN-level defect at
propose/apply/verify → stop, escalate to operator/Fable). **Sequencing constraint: OW-7/9/11/14 edit
the same skill files OW-3 rewrites — land the frozen OW-2→3→5→6 batch FIRST.**

## OW-7 · Delegation wrapper + run-telemetry ledger  ·  Tier: MEDIUM  ·  Orch: **Opus**
`scripts/opencode_delegate.py` mechanizing the harness post-processing hand-rolled in 6 skills
(timeout, fallback-grep, jq extraction, marker assert, EXIT-sentinel, exit-code interpretation) +
one JSONL ledger line per run (agent, model, phase, change, duration, exit, fallback?, verdict,
retry#) to untracked `output/delegation-log.jsonl`. Telemetry feeds the two scheduled decisions
(premise-gate downgrade at ~50 reviews / MEDIUM pro-pass downgrade at ~20 verifies — see AUDIT.md).
**Deps:** after frozen batch.

## OW-8 · Delegated-context caching hygiene  ·  Tier: SMALL–MEDIUM  ·  Orch: **Opus**
Variable-paths-last in apply/archive/reviewer prompt templates; scope down / stabilize the
AGENTS.md auto-injection into delegated deepseek calls (highest-churn file resets all 5 agents'
prefix cache; ~7.2k orchestrator-voice tokens sent to the implementer role); single-source the
triplicated premise prompt. **Deps:** none hard; prompt-template edits after frozen batch.

## OW-9 · Instruction-surface contradiction sweep  ·  Tier: SMALL–MEDIUM  ·  Orch: **Opus**
Fix autonomy-grant vs phase-gate hard-STOP contradiction (resolved semantics recorded in AUDIT.md:
grant auto-advances phases EXCEPT across DISSENT / NEEDS-REVISION / operator-named gates); fix
harness-vs-skill self-review contradiction (resolve to: orchestrator's own inline pass); de-dup
propose's Claude/OpenCode freeze branches; archive EXIT-sentinel line; add the assumption-batching
rule (non-blocking ambiguity → recorded default in notes.md `Assumptions`, batch-surfaced at next
gate); add the Sonnet-first pre-route line to the model-assignment matrix. **Deps:** after frozen
batch. Do first among wave 2 — these are live contradictions.

## OW-10 · Apply-executor throughput + resume contract  ·  Tier: MEDIUM  ·  Orch: **Opus**
Green path = targeted tests per task + full suite once per slice (today: full suite after EVERY
task, which is what makes the 600s ceiling bind); retry/fresh-executor brief gains the explicit
resume contract (skip `[x]`, resume at first `[ ]`, reconcile the half-edited in-flight task) +
distilled-state carry-forward. Attacks the measured ~15–19% crash/timeout→Sonnet escalation rate.
**Deps:** after frozen batch (apply skill file).

## OW-11 · Skill de-bloat + mechanized gates  ·  Tier: MEDIUM  ·  Orch: **Opus**
Replace verify steps 12–16 with deterministic CLI coverage + coherence note; trim explore's
gallery prose; `freeze-check` script (parse review verdict → FREEZE-OK/BLOCKED); `notes_lint.py`
five-field gate replacing the step-18 ritual; explore→propose slug-match warning; run COMPLEX's
two verifier passes concurrently (read-only frozen tree; ~13 min wall-clock saved); model-ID
agreement lint (deepseek-v4 hardcoded 44×/13 files, no guard). **Deps:** strictly after OW-3
applies (same file).

## OW-12 · Archive mechanization  ·  Tier: SMALL–MEDIUM  ·  Orch: **Opus**  ·  lowest priority
`archive_move.py` for the dir move; deterministic delta-applier for ADDED/REMOVED/RENAMED (LLM
only for MODIFIED merge + reconciliation narrative). Keep the executor on pro — what remains IS
the judgment. **Deps:** after frozen batch.

## OW-13 · Knowledge-surface bounding, round 2  ·  Tier: SMALL  ·  Orch: **Opus**
`status_lint` word-budgets for the currently-exempt sections (evidence: extrends "Immediate next
action" at 1,645 words); bound `knowledge/decisions/INDEX.md` (extrends 52KB ≈ 13k boot-scan
tokens; year-split); optional plans/-count lint (extrends 68-file shadow workflow); a
deterministic `boot_surface` budget check summing the boot-read set's bytes (warn ~80KB / fail
~100KB — extrends is at ~122KB today; see AUDIT.md addendum). **Deps:** none.

## OW-14 · Delegation-by-default mechanics  ·  Tier: SMALL–MEDIUM  ·  Orch: **Opus**
Operator-reported failure: expensive orchestrators (Opus/Fable) run greps/builders/probes/JSON
parsing inline instead of delegating — the AGENTS.md rule exists but never fires at the moment of
action (prose-is-write-only-memory, applied to the instruction surface). Canonical rule:
**run-and-extract → subagent (haiku mechanical / sonnet extraction); read-and-judge →
orchestrator**; plan slices before delegating. Scope: (a) add the missing **haiku tier** to the
model-assignment matrix; (b) point-of-action cues inside verify/apply/archive steps that run
builders/probes/suites ("delegate the run+extract; read the distilled report"); (c) optional
Claude-only PostToolUse large-Bash-output nudge hook — needs a decision-record carve-out like the
commit-test-gate hook. **Deps:** after frozen batch (touches same skills); pairs with OW-9.

---

## Late addition — 2026-07-11 (psc-monitor coverage-gap review; extrends convergence 2026-07-12)

Evidence docs: `psc-coverage-gap-review-2026-07-11.md` + `extrends-coverage-gap-review-2026-07-12.md`
(this dir); source reviews in psc-monitor `plans/audit-correctness-quality/coverage-gaps-2026-07-11.md`
and extrends `knowledge/research/correctness-audit-2026-07/gap-map-2026-07-11.md`.

## OW-15 · Correctness-audit meta-hardening (liveness + scope blind spots)  ·  Tier: SMALL–MEDIUM  ·  Orch: **Opus**
Three deltas to the `correctness-audit` capability OW-5 ships, from a downstream review that
found a heavily-audited repo (psc-monitor, waves 0–2 executed) had (a) **silently dropped its
chartered Waves 3–4 from every tracker** — the remediation program took over the "wave"
namespace and the discovery tail fell off with no descope decision — and (b) **never chartered
five whole dimensions**, one of which was an S4-class live gate (no implemented backup covered
any non-reconstructible store while trackers said backups were "✅ satisfied"). Deltas:
(1) **audit-liveness visibility** — an in-progress dossier SHALL be surfaced as an Active
questions item until close-out; extend OW-5's dossier lint (dossier with unfinished waves + no
Active item referencing it → drift finding); charter template requires discovery/remediation
namespace separation. (2) **Chartered close-out coverage-gap review** — reviewer writes the
full-audit dimension taxonomy BLIND (before reading charter/dossier), then diffs against
chartered+executed coverage (census-as-stopping-rule proves completeness WITHIN scope; nothing
else checks the scope itself). (3) **Scope-seeding checklist** — generic 45-dimension seed +
eight named recurring blind-spot classes (backups of non-reconstructible state, cutover-as-one-
sequence, provider feedback channels, policy-without-mechanism, phantom dev tooling, partial-✅
dispositions, point-in-time audits without conventions, at-rest invariants at scale) consulted
during the charter-instantiation walk.
**Why:** both observed failure modes sit outside the frozen OW-5 design's defenses — dossier-
internal state cannot defend against the dossier not being read, and the census cannot row a
dimension the charter never enumerated. Checked against the frozen spec before filing: no overlap.
**Extrends convergence + widenings (2026-07-12,** `extrends-coverage-gap-review-2026-07-12.md`**):**
extrends independently ran the Delta-2 method (blind 30-dim taxonomy → 3-subagent recon → diff)
against its FOUR-wave audit the same weekend — second success, n=2, plus first cross-repo yield in
both directions (psc's class #1 fired against extrends: backups of non-reconstructible state,
never chartered there either; routed in extrends' own queue). Adds to this entry: **Delta 4 —
coverage liveness AFTER close-out** (post-close unaudited-code ledger appended at verify/archive
for persistence/publish-path diffs, mini-wave trigger when the open set grows; reference impl
`extrends/.../POST-WAVE4-LEDGER.md` — Delta 1's mirror image: Delta 1 defends the unfinished
dossier, Delta 4 defends the finished one); **Delta-3 checklist widenings** — measurement-pipeline
parity (eval grades the identical artifact path prod publishes), run-indexed vs period-indexed
derived state under sequential same-period re-runs (survives idempotent storage), phantom
*capability* claims (class-#5 widened from dev tooling to declared-never-exercised
extras/backends — extrends `[postgres]`), cross-stream interference + the **boot-doc rule** (a
routed constraint on another stream isn't routed until it's in that stream's boot/handoff doc),
verified-safety-claim tagging (class-#6 widened: tracker claims authorizing state-mutating
operator actions carry VERIFIED-BY or UNVERIFIED), a named group-I config smell
(pydantic-settings `extra="ignore"` + no `env_prefix`), and grade-hazards-against-deployed-config
(not code defaults). Plus one small adjacent process candidate (committed-handoffs check —
pairs with OW-13's plans lint; placement at operator discretion, evidence doc §4).
**Scope:** spec delta to `correctness-audit` + skill-text additions + one knowledge-lint check
(now incl. the Delta-4 ledger requirement).
**Effort:** ~1–1.5 days. **Deps:** apply strictly AFTER OW-5 lands (amends its capability); zero
interaction with OW-2/3/6. Alternative at operator discretion: fold into OW-5's verify session
as an immediate follow-on. Standard escalation caveat.

---

## New findings — 2026-07-10 OW-3 session (Fable; untriaged, small, none block anything)

1. **OW-2's frozen delta fails `openspec validate`.** `lesson-check-ratchet`'s
   `specs/finding-closure-ratchet/spec.md` ADDED requirement
   `generalizable-findings-close-only-with-a-recorded-disposition` lacks SHALL/MUST →
   validator ERROR. **The Opus apply session for OW-2 should make the one-word normative fix
   before delegating apply**, disclosing the post-freeze edit in `review-log.md` (mechanical,
   no re-review round needed).
2. **Validator blind spot for MEDIUM changes.** `openspec validate` discovers changes via
   `proposal.md`, so MEDIUM (tasks.md-only) changes — including their spec deltas — are never
   CLI-validated; delta format discipline rests entirely on the pro review. Candidate fix:
   teach the validator (or a `scaffold_lint` check) to discover changes by dir presence.
3. **No validate-at-freeze step.** The propose skill never runs `openspec validate` before
   freezing artifacts — finding 1 slipped through a COMPLEX change that WAS validator-visible.
   Candidate fix: one line in the propose skill (validate before declaring frozen) — cheap,
   deterministic, mechanism-over-docs.
4. **RENAMED spec-promotion path unexercised.** Hardened into the archive-executor by
   `lifecycle-gates`, never used by any archived change. OW-3 deliberately avoided debuting it
   (kept original requirement headers). Exercise it once on a low-stakes change.
5. **Verify-skill internal drift found and absorbed into OW-3** (pass-sequence prose still
   claimed OpenCode=flash-only; promoted spec self-contradictory on the same point; SMALL-pass
   optional-vs-required contradiction; live skill citing an archived design.md "D5" for the
   verifier prompt) — all fixed by OW-3's frozen tasks/deltas, listed here only so the pattern
   is visible: **chain-shape prose is restated in ≥6 places and drifts independently**; the
   long-term fix is fewer restatements (cite the spec), same cite-don't-restate rule the repo
   already applies to rule-families.

## Orchestrator routing — summary
- **The Fable-tier backlog is CLOSED as of 2026-07-11.** OW-2/3/5/6 designs are frozen; every
  wave-2 item's design judgment is pre-made in `knowledge/research/workflow-audit-2026-07-11/AUDIT.md`.
- **Use Opus end-to-end** for everything remaining: applying+verifying the frozen batch, OW-1,
  OW-4, and all of OW-7..13. Apply is delegated to deepseek/sonnet regardless of orchestrator,
  and verifying a well-specified frozen change is squarely within Opus's capability.
- **Escalate to operator/Fable** only on DESIGN-level defects surfacing mid-apply/verify (the
  per-item caveats above), never for implementation bugs.

## Disposition
- **All PARKED.** Nothing here blocks anything; parking costs only the known waste OW-3/OW-7
  will remove (zero-yield flash passes; hand-rolled delegation) plus deferred telemetry.
  Recommended Opus session order: **frozen batch OW-2→3→5→6 first** (OW-7/9/11/14 edit files
  OW-3 rewrites), then OW-9 → OW-14 → OW-1 → OW-4 → OW-7 → OW-10 → OW-11 → OW-8 → OW-13 → OW-12.
  **OW-15** (late addition 2026-07-11) slots anywhere after the frozen batch — it amends OW-5's
  capability, so it pairs naturally with OW-5's verify session or the first real audit run.
- **Post-backlog verdict (2026-07-11):** after this backlog lands, scaffold process optimization
  is at diminishing returns — further sessions should spend downstream (extrends' ~33 open
  defect classes) rather than on new scaffold mechanisms. See AUDIT.md non-findings for the
  explicit do-not-build list.
- **Out-of-scope flag for the operator (downstream, not scaffold):** extrends currently has
  **~33 correctness-audit defect classes with ZERO remediation shipped** (per its
  `decisions/INDEX.md § audit-first-remediation-deferred`) — every class is still live in that
  codebase. That is downstream execution work, but it is the more *urgent* pile than anything
  in this scaffold backlog.
