# psc-monitor strategy pressure-test (2026-07-12) — the promise-surface audit class (OW-16 evidence; OW-15 widenings)

**Provenance.** psc-monitor ran a departing-principal adversarial review of its **business thesis**
— pricing, ICP, GTM, regulatory window, competitor set, cost structure — recorded as
`plans/strategy-pressure-test/pressure-test-2026-07-12.md` in that repo (Fable session; "CG9" in
its queue). Method: a 24-attack list written **blind** (committed before any evidence returned) →
five parallel evidence extractions (three internal: implementation-as-sold, cost/critical-path,
repo+git-history/GTM sweep; two live-web via the research convention: regulatory status,
competitor/TAM) → per-attack disposition diff (CONFIRMED / PARTIAL / SURVIVED-BY-THESIS / OPEN),
with attacks the thesis survives recorded rather than dropped. This doc extracts what
generalizes; psc-specific findings and ratifications stay in psc's own queue.

---

## 1. Headline: a launch-gate defect three chartered code audits could not have found

psc's pricing page sold three Pro-tier differentiators; verification against the code showed
**two did not exist and the third was misdescribed**: the "daily/immediate alerts" upgrade was
*unreachable* (the dispatcher handles all three cadences correctly, but no route, webhook, or UI
ever updates the user's cadence field — every user is permanently on the default), "start free
trial" charged the card immediately (no trial configured anywhere), and "priority support" had no
implementation. The mirror-image defect rode along: a genuinely built compliance-evidence feature
(per-alert review feedback log) was marketed nowhere.

Three structural reasons the (excellent, repeatedly-verified) correctness program missed it:

1. **Object/oracle inversion.** Every audit wave took *code* as the object and a spec/contract as
   the oracle. This defect needs the *copy* as the object and the *code* as the oracle — the
   marketing surface (`landing/`, a static site with no data path) was in no wave's universe, and
   no dimension taxonomy (including OW-15's 45-dim seed) contained copy↔capability conformance.
2. **Reachability vs behavior.** The dead-but-correct differentiator passes every behavior audit
   by construction: the code path works when entered; nobody asks whether a user can *enter* it.
   The entitlement-matrix dimension (group G) as worded — "every cell enforced and tested" —
   audits enforcement of reached states, not reachability of sold states.
3. **Severity-taxonomy hole.** The repo's S1–S7 scale graded data/money/compliance harm *inside
   the system*. "The pitch is false" is trust/legal/conversion harm with no severity slot — the
   class was invisible to triage, not just to discovery. (The repo had even recorded a
   "severity-taxonomy UX-class gap" as a tooling follow-on; the gap had teeth.)

Amusing corroborating detail: the billing webhook hardening deliberately handled the `trialing`
subscription state — the code was hardened for a state the product never offers, while the copy
promised a state that never occurs. Correctness-audit energy and promise-surface drift are
orthogonal.

## 2. Method validation (n=3) — and the first non-code domain

The blind-taxonomy/attack-list → evidence → diff method is now validated three times: psc
close-out review (45-dim, found the backup gate + wave-drop), extrends close-out (30-dim,
convergent), and now psc CG9 (24 attacks) — the first run in a **non-code domain** (business
thesis), where it performed identically: the blind list caught the anchoring-prone gaps (GTM
void, kill-criteria absence, window arithmetic), and the disposition table kept survived attacks
honest.

**New method note worth carrying into OW-15's Delta-2 skill text:** the two highest-severity CG9
findings came from the **evidence fan-out, not the blind list** — sold-but-unbuilt came from the
implementation extraction; a brand-new direct competitor came from the live-web scan. The blind
list defends against anchoring; the evidence fan-out finds what armchair reasoning cannot
predict. Both halves are load-bearing — a review that writes the blind taxonomy but skims the
evidence pass is half a method.

## 3. OW-15 Delta-3 checklist widenings (route into OW-15; no new OW number)

Continuing the numbered blind-spot class list (psc review classes 1–8, extrends widenings):

9. **Copy↔capability conformance (claims ledger).** Enumerate every externally visible promise
   (pricing table, landing/marketing copy, README feature claims, public docs) → map each to the
   delivering code surface + the check that proves it. Two failure directions, both observed:
   sold-but-unbuilt AND built-but-unsold. Cheap at product scale (psc's table: ~10 rows); the
   ledger is best born as the by-product of the first copy fix rather than a standalone ceremony.
10. **Entitlement-state reachability (liveness, not behavior).** Widen group G: for every
    sold/entitled state, verify a user-reachable path exists to *enter* it. A dead-but-correct
    differentiator passes every behavior audit; only a reachability question catches it.
11. **Severity-taxonomy completeness prompt.** The charter walk asks: does the severity scale
    have a slot for external-promise/trust/legal harm (false advertising, misleading CTA,
    ToS-vs-behavior drift) — or is that class explicitly ruled out-of-scope to a named sibling
    audit? Either answer is fine; silence is the defect.
12. **Source-class labeling for durable web-sourced claims.** A vendor blog post's speculation
    entered psc's durable strategy reference as a regulatory "tail risk" and survived a month as
    decision input (near-verbatim phrasing match to the promotional source = the circular-sourcing
    signature). Durable web-sourced claims carry a source class at write time (official /
    secondary / vendor-speculation); re-verification burden points at the non-official classes
    first.

One **OW-6 (composition-audit) lens candidate**, routed there rather than here: a
**revealed-vs-stated-priority diff** — psc's own strategy doc ruled "time-to-market and
distribution dominate every prioritisation trade-off"; the month of work after it ran ~7:1 the
other way with no recorded re-decision. A cadenced pass that reads the operator's standing
priority ruling and diffs it against the archive/commit distribution names that drift; nothing
does today.

## 4. The portfolio-level scope blind spot → OW-16

OW-15's Delta 2 fixed "nothing audits the scope" *within* the correctness audit. CG9 exposes the
same failure one level up: **the scaffold's whole audit portfolio is code-facing** (correctness,
test-quality, composition, workflow-efficiency, knowledge-drift, plus the per-repo security
sibling). A repo that is a *product* has audit classes whose object is not code:

- the **promise surface** (copy↔capability — §1);
- the **business thesis** (pricing/ICP/window/competitors — decision inputs that decay and can be
  mis-sourced, §3.12);
- **outcome quality** (does the product's output meet its accuracy claims on labeled ground
  truth — distinct from code correctness; for an alerting product, alert precision *is* the
  product);
- **operational rehearsal** (restore/DSAR/incident drills — operator-response liveness, not code).

None of these had a name or an owner, so "which audit classes have we run?" was unanswerable —
psc ran three code audits before anyone adversarially read its pricing page. The portfolio
should be a named list the coverage-gap review (OW-15 Delta 2) checks scope against, and the
promise-surface/thesis classes get a scaffold-owned protocol: **OW-16**.

## 5. Routing

- **OW-15 widened in place** (§2 method note + §3 classes 9–12); no new number, apply unchanged
  (strictly after OW-5).
- **OW-16 registered** (OUTSTANDING-WORK.md, this dir): `product-audit` skill — blind attack
  list → five-lane evidence fan-out → disposition diff → findings + operator ratification menu;
  ships the claims-ledger convention; reference impl = psc `plans/strategy-pressure-test/`
  (attack list, pressure-test doc, tracked web-evidence appendices).
- **OW-6 lens candidate** (revealed-vs-stated priority) recorded in §3 for OW-6's apply session.
- Roadmap mirrored; awareness pointer added to the OW-5 change dir's `notes.md` (freeze NOT
  reopened). psc-specific follow-ons (its own missing audit classes: full-depth security,
  outcome-quality) are psc's queue, not scaffold work.
