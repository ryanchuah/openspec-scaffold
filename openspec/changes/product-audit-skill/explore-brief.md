# Explore brief — `product-audit` skill (OW-16): promise-surface & business-thesis audit

**Tier (self-classified, autonomy grant):** COMPLEX — greenfield capability + new scaffold-managed
skill + a new durable cross-repo convention (claims ledger) + optional guarded lint. Parity with its
sibling OW-5 (`correctness-audit`, shipped COMPLEX).

## Problem
Every audit class the scaffold owns is **code-facing**: object = code, oracle = spec/contract
(correctness-audit, test-quality, composition-audit, workflow-efficiency, knowledge-drift, the per-repo
security sibling). For a repo that ships a **product**, an entire class of defect is structurally
invisible to that portfolio: defects where the object is the **promise surface** (pricing page,
landing/marketing copy, README feature claims, public docs) or the **business thesis**
(pricing/ICP/GTM/regulatory-window/competitor assumptions), and the oracle is the code or the market.

Concrete evidence (psc-monitor CG9, `knowledge/research/scaffold-gap-analysis-2026-07/psc-strategy-pressure-test-2026-07-12.md`):
a pricing page sold three Pro-tier differentiators; verification against code showed **two did not exist
and the third was unreachable** (dispatcher handled all cadences, but no route/UI ever mutated the
user's cadence field — every user permanently on default; "free trial" charged immediately; "priority
support" had no implementation). The mirror-image defect rode along: a genuinely built compliance
feature was marketed nowhere. This launch-gate defect **survived three chartered code audits** in a
heavily-audited repo. Separately, the business thesis (pricing/ICP/regulatory window/competitors) had
**zero adversarial review** while the code had three; when finally pressure-tested (24 blind attacks)
it yielded a new launch gate, a live competitor the strategy doc didn't know existed, a mis-sourced
regulatory claim sitting in a durable reference, and six ratified operator decisions — the highest
single-session decision yield of any audit run in either downstream repo.

## Root cause (three structural, not effort, failures)
1. **Object/oracle inversion.** Every wave took code as object, spec as oracle. This class needs *copy*
   as object, *code* as oracle — the marketing surface was in no wave's universe, and no dimension
   taxonomy (incl. OW-15's 45-dim seed) contained copy↔capability conformance.
2. **Reachability vs behavior.** A dead-but-correct differentiator passes every behavior audit by
   construction (the path works when entered; nobody asks whether a user can *enter* it). The
   entitlement-matrix dimension audits enforcement of reached states, not reachability of sold states.
3. **Severity-taxonomy hole.** "The pitch is false" is trust/legal/conversion harm with no severity
   slot in a scale built for in-system data/money/compliance harm — invisible to triage, not just to
   discovery.

Portfolio-level: because none of these classes had a name or an owner, "which audit classes have we
run?" was unanswerable. OW-15 Delta-2 fixed "nothing audits the scope" *within* a code audit; this is
the same failure one level up — the whole portfolio is code-facing.

## Solution direction
A new **operator-invoked, pull-only, never-fixes-product-code** `product-audit` skill — the promise-
surface/business-thesis sibling of `correctness-audit` — standardizing a protocol that is already
**proven and cheap** (one session; the blind-diff core is validated n=3, incl. this first non-code
domain). Shape:

1. **Blind attack-list first** — write the adversarial attack list and commit it *before* any evidence
   returns (defends against anchoring; the same blind-taxonomy discipline OW-15 Delta-2 uses).
2. **Five-lane evidence fan-out** (the load-bearing half — n=3 shows the top-severity findings come
   from the evidence pass, not the blind list): (a) implementation-as-sold (copy→delivering code
   surface); (b) cost / critical-path; (c) repo + git-history + GTM-artifact sweep; (d) live-web
   regulatory; (e) live-web competitive/TAM. Web lanes (d,e) ride the **existing research convention**
   (subagent-only, `scripts/fetch_clean.py`; never `WebSearch` from the main thread).
3. **Per-attack disposition diff** — CONFIRMED / PARTIAL / SURVIVED-BY-THESIS / OPEN; **survived attacks
   recorded, not dropped** (honest-survival, same as the disposition table).
4. **Findings + operator ratification menu** — findings ranked and surfaced as *decisions to ratify*,
   not observations (the business thesis is the operator's to own; the audit surfaces, never decides).
5. **Machine-discriminable verdict** — `PRODUCT: CLEAN | FINDINGS-ROUTED | ESCALATE` (parity with
   composition-audit's verdict line), read by the orchestrator from disk.
6. **Claims-ledger convention** (the durable cross-repo artifact this change owns): every externally
   visible promise → delivering code surface → the check that proves it. Cheap at product scale
   (~10 rows). Born as a by-product of the first copy fix, not a standalone ceremony.
7. **Findings route into the existing finding-closure ratchet** (`knowledge/ratchet-log.md`) on close,
   same three-question triage the sibling audits use — no new close-out machinery.

**Cadence:** pre-launch gate for product repos + on strategy-reference watch-list expiry. **NOT a
recurring ceremony** and **never wired into boot/AGENTS.md/any auto-run** (pull-only, like both siblings).

This change also **operationalizes** OW-15's carried-forward classes 9–12, which `correctness-audit`
explicitly hands off (its SKILL.md names these as awareness-pointers whose "full mechanism belongs to
the sibling `product-audit` skill"): copy↔capability conformance / claims ledger; entitlement-state
**reachability** (not behavior); severity-taxonomy completeness (a slot for external-promise/trust/legal
harm, or a named exclusion — silence is the defect); source-class labeling for durable web-sourced
claims (official / secondary / vendor-speculation; the near-verbatim-phrasing-to-a-promotional-source
circular-sourcing signature).

## Scope framing
**In scope:**
- New `.claude/skills/product-audit/SKILL.md` (scaffold-managed; +1 line to `scaffold_manifest.txt`).
- New `openspec/specs/product-audit/spec.md` capability (specs are golden-source-only, not synced).
- The claims-ledger convention (format inlined in the skill as a template).
- **Optional, decided at design:** one guarded `knowledge_lint` detector (promise-surface files newer
  than the claims ledger → staleness finding), marker-gated on `format: product-audit/v1` so this repo
  and un-adopted downstream repos lint clean (mandatory idiom — mirrors the three existing audit
  detectors; live-tree gate `test_doc_lint_gate.py` requires it).

**Out of scope (explicit):**
- OW-12 (archive mechanization) and OW-11-residual (skill de-bloat) — separate concerns, not folded
  (per HANDOFF lesson: maximal *coherent* unit, not maximal count). Handed off.
- The OW-6 lens candidate (**revealed-vs-stated-priority diff**) — routed to composition-audit's queue,
  not built here.
- Outcome-quality and operational-rehearsal audit classes (§4 of the evidence doc) — named as future
  portfolio gaps, not this change.
- No product code, no downstream propagation (operator-gated), no push (operator-gated).

## Key design decisions deferred to propose/design
- **Deterministic vs LLM split.** Which lanes/steps (if any) warrant a helper script vs pure skill
  prose. Prior: correctness-audit is prose-only; composition-audit shells deterministic tools. Lean
  prose-only + guarded lint; decide at design.
- **Claims-ledger location & marker.** Where the ledger lives (per-repo `knowledge/reference/`?) and
  what `format:` marker it carries so a lint can find it without false-flagging non-product repos.
- **Spec requirement decomposition.** ~5–8 requirements (parity: composition-audit=5, correctness-
  audit=11), each with WHEN/THEN scenarios; SHALL/MUST on each requirement's first line.

### Carried from the direction gate (pro premise review, PREMISE: AGREE — two 🟡 to resolve at design)
- **🟡-1 Ratchet-disposition fit for non-code findings.** Ratchet Q3 ("mechanically detectable /
  test-freezable?") was designed for code defects. A promise-surface finding ("copy claims X, code
  lacks X") may not map onto the five dispositions cleanly — what is a `check:`/`test:` for a marketing
  claim? **Open design question:** do the existing dispositions cover promise-surface classes (the
  claims-ledger *proving check* row may itself be the `check:` disposition), or is a small leaf
  carve-out needed? Resolve in design; do not assert compatibility.
- **🟡-2 Claims-ledger staleness lint is NOT default-optional.** The ledger suffers the same copy↔code
  drift the skill detects; its maintenance mechanism shouldn't stay optional indefinitely. **Reframed
  as a tension:** ship the guarded staleness lint now, or explicitly defer it with a recorded re-audit
  trigger — not silently optional. (Leaning: ship it — mechanism-over-docs; the marker-guard idiom
  keeps un-adopted repos clean.)
- **💡 Reciprocal awareness pointer** — product-audit SKILL points back at correctness-audit (a
  built-but-unsold finding may warrant a correctness-audit of the undisclosed feature), closing the
  bidirectional handoff correctness-audit already opened.
- **💡 Operator dual-literacy** — a light scaffold acknowledging the operator needs both business-thesis
  and code-surface literacy (parity with the correctness-audit charter walk).

## Evidence & reference
- Primary: `knowledge/research/scaffold-gap-analysis-2026-07/psc-strategy-pressure-test-2026-07-12.md`.
- Backlog entry: `.../OUTSTANDING-WORK.md` OW-16; roadmap: `knowledge/roadmap.md` "Product-audit skill".
- Conventions map (this session): sibling skills' frontmatter/section/verdict/ratchet/marker idioms +
  the guarded-lint test triad + live-tree gate.
- Reference impl (downstream, not edited): psc-monitor `plans/strategy-pressure-test/`.
