# Notes — correctness-audit-skill

## Acceptance criteria
Change-specific acceptance criteria live in `design.md` § Verification (authored and
reviewed at propose). Verify results will be recorded here at verify time.

## Sequencing (load-bearing)
- **Apply-order dependency on `lesson-check-ratchet` (OW-2):** do not apply this change
  until OW-2's apply lands `knowledge/ratchet-log.md`, its `_check_ratchet_log` lint,
  and the archive/run-audit triage text in the live tree. The skill text cites that
  interface as live behavior.
- **OW-2's apply session must first make its one-word normative fix** (its closure
  requirement fails `openspec validate --strict` SHALL-detection; gap-analysis
  OUTSTANDING-WORK.md finding 1). OW-5 cites OW-2 by requirement names and interface
  shapes (triage questions, ledger line format, disposition keywords), which that fix
  does not alter; if OW-2's apply changes anything beyond that word, re-check this
  change's citations before applying.
- **No dependency in either direction on `verify-stack-redirect` (OW-3).** If OW-3
  applies before this change (recommended batch order: OW-2 → OW-3 → OW-5), this
  change's verify runs under the post-OW-3 contract: COMPLEX = self → pro behavioral →
  flash lens pass (test-quality default). If OW-3 has not applied, verify runs under
  the pre-OW-3 contract (self → pro → flash same-checklist).

## Carried caveats (from review rounds — for verify/archive)
- **Graduation log is not lint-enforced.** The D8 dossier lint checks IDs, census
  dispositions, and `Prior:`/`Class:` presence; the graduation log (spec-required,
  append-only evidence trail) has no deterministic check — by design (D8 scopes to
  core format checks). The verify pass should eyeball the skill text's graduation-log
  template; a future audit that ships without one is a drift signal for
  knowledge-drift-review, not knowledge_lint.
- **First-real-audit manual check** (design § Verification, not unit-testable):
  confirm wave-gate triage-file appends keep graduated findings out of the
  `untriaged-finding-stale` bucket during a live audit.
- **Requirement-split suggestion declined** (specs round 2 💡2): the triage-file and
  ratchet-routing behaviors are one invariant ("no ID leaves untriaged, nothing closes
  silently") — recorded here so archive doesn't reopen it.

## Post-freeze input (2026-07-11, from psc-monitor — does NOT reopen the freeze)
A downstream coverage-gap review (psc-monitor
`plans/audit-correctness-quality/coverage-gaps-2026-07-11.md`) surfaced two audit-protocol
failure modes outside this change's frozen scope: **silent wave-drop** (chartered discovery
waves fell off every tracker when a remediation program took over the "wave" namespace —
pull-only invocation + dossier-internal state can't defend against the dossier not being read)
and **scope blind spots** (census-as-stopping-rule proves completeness within the chartered
surface list; it cannot row a dimension the charter never enumerated — psc had five such, one an
S4-class live gate). Queued as **OW-15** (apply strictly after this change), evidence at
`knowledge/research/scaffold-gap-analysis-2026-07/psc-coverage-gap-review-2026-07-11.md`.
Verify session: awareness only — do not fold into this change without operator direction.

**Second convergence (2026-07-12, extrends):** extrends independently executed the same blind
close-out review against its four-wave audit (method validated n=2; psc's backup blind-spot
class fired against extrends on first cross-repo use). OW-15 widened in place — notably
**Delta 4: post-close coverage-liveness ledger** (code shipped after a clean close-out is
unaudited by construction; ledger + mini-wave trigger, reference impl in extrends) and several
Delta-3 checklist widenings. Evidence:
`knowledge/research/scaffold-gap-analysis-2026-07/extrends-coverage-gap-review-2026-07-12.md`.
Same rule: awareness only — OW-15's apply consumes this, not this change's verify.

**Third input (2026-07-12, psc CG9 strategy pressure-test):** the blind-diff method validated a
third time, first in a NON-code domain (business thesis) — and found a launch-gate defect class
structurally invisible to this skill's object/oracle direction (pricing copy selling unbuilt or
unreachable features; code-as-object audits pass a dead-but-correct path by construction). OW-15
widened again in place (Delta-3 classes 9–12: copy↔capability claims ledger; entitlement-state
reachability; severity-taxonomy completeness prompt; source-class labeling for durable
web-sourced claims) plus a Delta-2 method note (evidence fan-out and blind list are BOTH
load-bearing — the top-severity findings came from evidence, not the blind list). The inverse
audit class itself is registered as **OW-16** (`product-audit` skill) — no interaction with this
change's frozen scope in either direction. Evidence:
`knowledge/research/scaffold-gap-analysis-2026-07/psc-strategy-pressure-test-2026-07-12.md`.
Same rule: awareness only.

## Orchestrator routing (operator-recorded verdicts, 2026-07-11)
- **Park verdict:** parked apply blocks nothing — OW-3 has no dependency on OW-5, and
  no backlog item waits on OW-5's apply. OW-5 itself waits on OW-2's apply.
- **Apply/verify orchestrator: Opus** (Fable not needed). Artifacts pin contracts,
  formats (verbatim ledger/triage/label sets), anchors, and budgets; apply is delegated
  to deepseek-flash regardless. **Escalation caveat:** implementation bugs and prose
  deviations from the frozen templates are normal defect-path work (fix-forward); a
  DESIGN-level defect (ratchet interface doesn't fit as frozen, lens/verify-chain
  interaction surprises, census/stopping-rule contract wrong) → stop and escalate to
  the operator or a Fable session rather than redesigning mid-verify.
