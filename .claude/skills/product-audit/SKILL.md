---
name: product-audit
description: Run a single-session promise-surface / business-thesis audit — blind attack-list → five-lane evidence fan-out → per-attack disposition diff → operator ratification menu, with a machine-discriminable verdict. Operator-invoked, pull-only, never fixes product code.
license: MIT
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.4.1"
---

Run a bounded, single-session **product audit**: an adversarial review of the product's **promise
surface** (pricing / landing / marketing copy, README feature claims, public docs) and **business
thesis** (pricing / ICP / GTM / regulatory window / competitors). It is the one audit class whose
**object is the copy and the thesis** and whose **oracle is the code and the market** — the inverse of
every code-facing audit (correctness, test-quality, composition, …), which take code as object and a
spec as oracle. That inversion is why three chartered code audits can pass while a pricing page sells
features that do not exist: no code audit's universe contains the marketing surface.

**Pull-only.** This skill is NEVER wired into session boot, `AGENTS.md`, archive, or any auto-run
trigger, and it NEVER gates a commit / verify / CI / lifecycle step. Invoke it explicitly. **Cadence:**
a **pre-launch gate** for product repos, plus a re-run when a strategy-reference watch-list item
expires — NOT a recurring ceremony and NOT a count-based due-signal.

**Audit-then-fix.** The audit produces findings only and modifies **no product code**. Remediation
ships later as ordinary OpenSpec changes citing finding IDs.

**Single-session, not a dossier audit.** Unlike `correctness-audit` (multi-wave, resumable dossier,
in-progress liveness obligation), a product audit runs in one bounded session. It therefore carries
**no in-progress liveness obligation** and needs no liveness lint. The only durable artifact it leaves
— the **claims ledger** — is kept honest by a *staleness* check (`knowledge_lint`'s
`claims-ledger-staleness` detector), a different obligation from liveness.

**Normative protocol:** `openspec/specs/product-audit/spec.md`. This file adds operational detail; the
spec is normative for the protocol, the disposition set, the verdict values, and the ledger convention.

**Web-research convention.** Lanes 4 and 5 (regulatory, competitive) need live-web evidence. Route ALL
web research through **subagents** using `scripts/fetch_clean.py` (discover via a fetched search URL,
then fetch the chosen pages) — **never** call the built-in `WebSearch` from the main thread. This is
the repo-wide research guardrail (`openspec/config.yaml` `rules.research`); it keeps the orchestrator
context clean and lets the two web lanes run in parallel and checkpoint to disk.

**Operator dual-literacy.** A product audit needs both **business-thesis literacy** (what is sold, to
whom, against whom) and **code-surface literacy** (what is actually built). The five-lane structure is
itself the scaffold for this: the implementation-as-sold lane forces code-reading, the GTM / web lanes
force thesis-reading. An operator strong on one side leans on the fan-out to cover the other.

---

## Protocol

### 1. Blind attack list — committed BEFORE any evidence

Write the adversarial attack list first: every way the promise surface and the business thesis could be
false (sold-but-unbuilt; built-but-unsold; dead-but-correct differentiator; pricing/trial/entitlement
mismatch; ICP undefined; kill-criteria absent; window arithmetic; unknown competitor; mis-sourced
regulatory claim; …). **Commit it before any evidence returns** — this defends against anchoring the
attack list to what the evidence happens to surface. Enumerate the attacks; never tally them.

**Scope prompts consulted while writing the list** (both are load-bearing gaps a behavior audit misses):
- **Entitlement-state reachability** — for every *sold* state, is there a **user-reachable path to
  enter it**? A dead-but-correct differentiator (the code path works, but no route/UI/webhook ever puts
  a user into that state) passes every behavior audit by construction; only a reachability question
  catches it.
- **Severity-taxonomy completeness** — does the repo's severity scale have a slot for
  **external-promise / trust / legal harm** (false advertising, misleading CTA, ToS-vs-behavior drift),
  or is that class *explicitly* ruled out to a named sibling audit? Either answer is fine; **silence is
  the defect** — a "the pitch is false" finding with no severity slot is invisible to triage.

### 2. Five-lane evidence fan-out (the load-bearing half)

Both halves of the method are load-bearing: the blind list defends against anchoring, but the
**highest-severity findings come from the evidence pass, not the list** (validated n=3). A run that
writes the blind list and skims the evidence is half a method. Run all five lanes, checkpointing each
to disk:

1. **Implementation-as-sold** — map each externally visible promise to its delivering code surface;
   confirm the surface exists AND is reachable (step-1 reachability prompt).
2. **Cost / critical-path** — does the unit economics / critical path hold at the sold price and scale?
3. **Repo + git-history + GTM-artifact sweep** — pricing config, feature flags, entitlement tables,
   landing copy, strategy docs; what the history says was intended vs shipped.
4. **Live-web regulatory** (subagent + `fetch_clean.py`) — current regulatory status of any compliance
   claim; label each durable claim with a **source class** (see below).
5. **Live-web competitive / TAM** (subagent + `fetch_clean.py`) — the live competitor set and market
   the strategy assumes; a new direct competitor the strategy doc doesn't know about is a common
   high-severity find.

**Source-class labeling for durable web claims.** Any web-sourced claim you record into a *tracked*
reference carries a source class at write time: `official` / `secondary` / `vendor-speculation`.
Re-verification burden points at the non-official classes first. The circular-sourcing signature is a
**near-verbatim phrasing match to a promotional source** — a vendor blog's speculation that entered a
durable strategy reference as if it were fact.

### 3. Per-attack disposition diff

Diff each blind attack against the evidence and assign exactly one disposition:
`CONFIRMED` (the attack lands — a real defect) · `PARTIAL` (partly lands) · `SURVIVED-BY-THESIS` (the
thesis holds against the attack) · `OPEN` (unresolved at close). **Record survived attacks — never drop
them**; a survived attack is a first-class outcome (the analog of a `REFUTED` correctness finding). Keep
the disposition table as the audit's durable working record.

### 4. Claims ledger (build or reconcile)

Build (first run) or reconcile (later runs) the repo's **claims ledger** — the durable artifact this
audit owns. See `## Claims-ledger convention` for the exact format and the reconciliation command.

### 5. Verdict

Write exactly one machine-discriminable verdict to disk (e.g.
`output/product-audit/<date>/product-verdict.md`):

- **`PRODUCT: CLEAN`** — no confirmed promise-surface or thesis findings.
- **`PRODUCT: FINDINGS-ROUTED`** — findings exist and were routed into the ratchet (step 6).
- **`PRODUCT: ESCALATE`** — findings suggest a chartered follow-up is warranted: a `correctness-audit`
  of a *built-but-unsold* feature (is the undisclosed feature production-grade?), or an operator launch
  block. ESCALATE **recommends** the follow-up and takes **no** chartering action itself.

### 6. Close-out — ratification menu + ratchet routing

Surface findings as an **operator ratification menu**: decisions to ratify, not observations. The
business thesis is the operator's to own — the audit surfaces and routes, and **never auto-decides** a
thesis question. For each generalizable finding, run the finding-closure-ratchet 3-question triage
(real defect? → generalizable class? → detectable/freezable?) — orchestrator judgment, never delegated
— and append one `knowledge/ratchet-log.md` line in the frozen format, per the mapping below.

**Reciprocal awareness pointer.** A **built-but-unsold** finding (a real feature marketed nowhere) may
warrant a `correctness-audit` of that undisclosed feature to confirm it is production-grade before it is
put on the promise surface. This closes the bidirectional handoff `correctness-audit` opened (it names
`product-audit` as the owner of the promise-surface classes 9–12).

---

## Claims-ledger convention

A single per-repo markdown file, canonical home **`knowledge/reference/claims-ledger.md`**, carrying the
literal marker `format: product-audit/v1`. It has a covered-file manifest (each covered promise-surface
file + the sha256 of its content at last reconciliation) and a claims table. The
`claims-ledger-staleness` `knowledge_lint` detector reads the manifest and flags any covered file whose
content changed since the ledger was reconciled — that is the mechanism that keeps the ledger from
silently rotting into the same copy↔code drift this skill detects.

```markdown
<!-- format: product-audit/v1 -->
last-reconciled: 2026-07-14

## Covered promise-surface files
- landing/pricing.html — sha256:<64-hex>
- README.md — sha256:<64-hex>

## Claims
| Promise (as sold) | Delivering surface | Proving check | Disposition |
|---|---|---|---|
| Daily/immediate alerts on Pro | dispatcher cadence field + the settings route that sets it | test:tests/test_cadence.py::test_pro_daily_reachable | CONFIRMED |
| Priority support | (none) | — | CONFIRMED (copy-only; removed) |
```

**Reconciliation.** After any covered promise-surface file changes (or when the staleness lint fires),
re-hash it and paste the digest into its manifest row, then bump `last-reconciled`:

```bash
sha256sum landing/pricing.html
# → <64-hex>  landing/pricing.html   ← paste the hex into the row's `sha256:` field
```

The `Proving check` cell records a **resolvable** `test:<path>::<name>` or `check:<pointer>` (a real test
or detector that fails if the promise regresses) — this is the pointer that lands in the ratchet for a
detectable finding. Coverage of the *full* promise surface (which files belong in the manifest) is the
operator's judgment at audit time; the staleness detector checks only that *listed* files have not
drifted, and never adjudicates completeness.

## Disposition → ratchet mapping (no new close-out machinery)

The five existing ratchet dispositions cover every product-audit finding — **no new keyword, no ratchet
spec change**:

| Finding shape | Ratchet disposition |
|---|---|
| Copy↔code claim closed with a real proving check (test/detector) | `test:<path>::<name>` or `check:<pointer>` — the claim's ledger proving-check cell |
| Copy↔code claim closed by correcting the copy, no enforcing check possible | `waiver:review-by <date>` + rationale (doc-only-close rule) |
| Pure business-thesis decision (accepted pricing / regulatory / competitor risk) | `waiver:review-by <date>` — re-review date = the strategy-reference watch-list expiry |
| `OPEN` attack (unresolved at close) | `open:since <date>` |
| `SURVIVED-BY-THESIS` attack | no ledger entry (recorded in the disposition table only) |

---

## Honest limits

The only mechanized surface here is the claims-ledger staleness lint; everything else is judgment
(copy↔code reasoning, live-web scans, thesis attack) — there is no deterministic detector for "is this
pricing claim true." The value is the **occasion** (nothing else names the moment to adversarially read
the pricing page and the business thesis) plus the **blind-list + evidence-fan-out** discipline. Two
adjacent product-audit classes named by the evidence but NOT built here — **outcome quality** (does the
product's output meet its accuracy claims on labeled ground truth) and **operational rehearsal**
(restore / DSAR / incident drills) — are future portfolio gaps, not this skill.

## Guardrails

- **Pull-only / never auto-run.** Do NOT wire this skill into session boot, `AGENTS.md`, or any hook,
  and do NOT let it gate any commit / verify / CI / lifecycle step.
- **Audit-then-fix.** Modify no product code from this skill; remediation is a later OpenSpec change.
- **Ratification, not decision.** Surface thesis findings as operator decisions; never auto-decide one.
- **Web research via subagents only** (`scripts/fetch_clean.py`); never `WebSearch` from the main thread.
- **Do not edit** `scripts/knowledge_lint.py` or any detector from this skill — it is detect-only.
- **Ratchet triage is orchestrator judgment**, never delegated to a mechanical executor.
