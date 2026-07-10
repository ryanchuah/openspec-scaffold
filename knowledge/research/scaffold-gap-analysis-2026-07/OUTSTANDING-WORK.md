# OUTSTANDING WORK — scaffold hardening from downstream audit evidence

**Source of truth for this backlog.** Derived from `SYNTHESIS.md` (this dir). All items are
**PARKED** (see disposition at bottom) — none blocks the current session. Each is a candidate
OpenSpec change in *this* (scaffold) repo; landing it here propagates to `extrends` +
`psc-monitor` via `sync_scaffold.py`.

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
**Why:** GAP 6 — both repos hand-rolled the LLM correctness audit (CHARTER/CENSUS/waves/oracles)
differently; the scaffold owns only the deterministic `run-audit`.
**Scope:** a skill standardizing the wave/charter/census shape that **routes every generalizable
finding into OW-2's ratchet** on close. **Effort:** ~3–4 days. **Deps:** land after OW-2 so
findings have somewhere to go.

## OW-6 · Cadenced composition-audit  ·  Tier: MEDIUM–COMPLEX  ·  Orch: **Fable** (design) → Opus (apply/verify)
**Why:** GAP 2 — verify is single-diff-scoped; a subsystem built from many approved changes is
never reviewed as a whole. Whole-repo detectors exist but are off-by-default and cadence-less.
**Scope:** wire `jscpd`/`vulture`/`audit_scope.py scan`/`knowledge-drift-review` into a
first-class, triggered composition pass; feed OW-2. **Effort:** ~2–3 days. **Deps:** OW-2, OW-5.

---

## Orchestrator routing — summary
- **Reserve Fable** for the *design/propose* of the three conceptually-novel, high-blast-radius
  items: **OW-2** (ratchet), **OW-3** (verify redirect), **OW-5/OW-6** (audit skills). The
  expensive-to-get-right part is the design decision, not the mechanics.
- **Use Opus end-to-end** for the mechanical detectors — **OW-1, OW-4** — and for **all
  apply+verify orchestration** once any proposal is frozen. Apply is delegated to deepseek/
  sonnet regardless of orchestrator, and verifying a well-specified frozen change is squarely
  within Opus's capability.
- **Note the pleasant asymmetry:** the single highest-yield fix (OW-1) needs Fable *not at all*.

## Disposition
- **All PARKED.** Nothing here blocks this session; its deliverable (the gap analysis) is
  complete. These changes prevent *recurrence* of downstream bug classes — high value, not
  urgent. Recommended landing order: OW-1 → OW-2 → OW-3 → OW-4 → OW-5 → OW-6.
- **Out-of-scope flag for the operator (downstream, not scaffold):** extrends currently has
  **~33 correctness-audit defect classes with ZERO remediation shipped** (per its
  `decisions/INDEX.md § audit-first-remediation-deferred`) — every class is still live in that
  codebase. That is downstream execution work, but it is the more *urgent* pile than anything
  in this scaffold backlog.
