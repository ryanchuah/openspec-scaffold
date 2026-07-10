# SYNTHESIS — scaffold gaps & token-waste, from downstream audit evidence

**Author:** Fable (principal-engineer pass), 2026-07-10
**Inputs:** `psc-issues.md` (psc-monitor, 1 wave), `extrends-issues.md` (extrends, 4 waves +
test-audit, 33 live classes), `scaffold-procedures.md` (gate ledger). All in this dir.
**Verification:** load-bearing subagent claims re-checked against source
(`checks.py --list`, verify SKILL lines 43–46). Two independent repos converge on the same
signal — the strongest evidence available short of a controlled trial.

---

## The one-sentence finding

The scaffold spends heavily to review **each diff in isolation with multiple models running
the same checklist**, and spends almost nothing to (a) turn a discovered bug into a
**mechanical check that blocks its recurrence**, (b) review the **accreted composition** of
many past-approved changes, or (c) gate **test quality** — which is precisely why both
downstream repos had to run expensive, hand-built, post-hoc correctness audits that re-found
the *same shapes of bug* over and over.

The money is in the wrong place: **redundant model breadth, thin lens diversity, zero ratchet.**

---

## Evidence that the in-loop gates failed for the classes that mattered

- Both repos independently **reinvented a multi-wave correctness-audit program** (CHARTER →
  CENSUS → wave FINDINGS → remediation change) — machinery the scaffold does not provide.
  Teams don't build that when the standard verify gate is catching things.
- **Recurrence of identical bug shapes** despite every change passing verify:
  - psc-monitor: the B5 livelock (unbounded `fetchall()`) and F16 transaction-visibility bugs
    each produced a `lessons.md` paragraph; **a sibling instance of each survived and was
    re-found by hand months later** (CA-W2-05; the `autocommit=TRUE` fixture pattern).
  - extrends: ground-truth-silently-destroyed-on-load (wave 3 `labels_io.py` → wave 4
    `console/labels_io.py`), fail-soft-branch-invisible-to-health (found 3×), and
    wrong-boundary mocking (found by BOTH the correctness audit and the separate test-audit)
    all recurred **one wave apart, inside the same audit program.**
- The recurrences are the tell: a human/agent re-reading the whole corpus **still doesn't
  durably generalize a pattern into a guard** — only a committed deterministic check does.
  Prose lessons are write-only memory.

---

## The gaps, ranked by leverage (prevention-per-token)

### GAP 1 — No "lesson → check" ratchet *(highest leverage)*
Nothing converts a found bug or a `lessons.md` entry into an **enforced check on future
diffs.** `lessons.md` is prose; `checks.py` ships only generic detectors; the two never meet.
**Result:** every fix is a point fix; the *class* stays open and re-ships in sibling code.
**Fix direction:** make "a generalizable finding is not closed until it has an enforcing
check or a frozen regression test" a scaffold *rule*, and ship the *framework* to register
per-repo invariant detectors cheaply (the nascent `data-lint` backend is the seed to
generalize). The ratchet is what makes every future audit smaller than the last.

### GAP 2 — Verify is single-diff-scoped; nothing audits accreted composition
The verify SKILL is explicitly one-diff-scoped. Whole-repo/multi-commit views (`jscpd`,
`vulture`, `audit_scope.py scan`, `knowledge-drift-review`) exist but are **off-by-default
in the operator-pulled audit layer, wired to no cadence.** So a subsystem assembled from 15
individually-approved changes is never reviewed *as a whole* — which is exactly the seam the
downstream audits mined.
**Fix direction:** promote a **first-class, cadenced composition-audit** (the thing both
repos hand-built) into a scaffold skill, seeded by the whole-repo detectors, feeding GAP 1.

### GAP 3 — Test quality is ungated *(cheapest high-yield mechanization)*
The most-cited defect families are **mechanically detectable and shipped in bulk anyway:**
tautological/forced-green asserts (`or True`, empty bodies — extrends TA-1/TQ-3, 13+),
discarded return flags (`count, _ = …` dropping a collector's `complete` flag — extrends
TA-3, 25+, and the *direct cause* of the ING-1 truncation bug shipping invisibly),
self-mocking the module-under-test (extrends TQ-2, found by two independent audits),
weak assertions + unfrozen clocks (psc TQ-WEAK/TQ-FLAKY, 23). The scaffold has **no
test-quality detector and no rule requiring a behavioral oracle before code ships.** Both
repos reconstructed oracles *after* the fact.
**Fix direction:** ship an AST test-quality detector (tautologies, empty tests, self-mocking,
discarded returns) enabled by default, plus a verify **lens** that asks "would this test fail
if the behavior broke?" This is a weekend's work and would have caught a double-digit count in
each repo.

### GAP 4 — "Mind data scale" is prose, not a gate
The AGENTS.md rule exists; the unbounded-`fetchall()` bug recurred anyway (GAP 1 in miniature).
Verify mandates a *live smoke for external APIs* but does **not** mandate an *at-scale run for
data-path changes*.
**Fix direction:** an unbounded-query/`fetchall`-on-unbounded detector, plus a verify rule:
a change to data-path code requires either an at-scale run or an explicit bounded-domain
argument recorded in `notes.md`.

### GAP 5 — Verify over-buys model breadth, under-buys lens diversity *(the token-waste answer)*
On Claude Code, MEDIUM/COMPLEX verify runs **self (Claude) → pro (deepseek) → flash
(deepseek)**, each **re-running the full suite** and executing the **identical checklist**
(SKILL line 46). The SKILL's own justification is *model* diversity only (line 43), and it
concedes elsewhere that a redundant same-tier pass "adds little" (line 44). Meanwhile the
empirical record is that these triple-reviewed changes **still shipped the audit's defect
classes.** More models on the same lens is the definition of diminishing returns: if the
checklist never asks "is this assertion tautological?" or "does this run at production
volume?", one model and three models miss it equally.
**Fix direction (redirect, don't just delete):** keep self + **one** independent model pass
as the diversity guard; spend the **third** invocation on a *different lens* the stack lacks
today — a test-quality/adversarial pass (GAP 3) or a data-scale pass (GAP 4). Same token
budget, strictly more coverage. Concretely: drop the flash **same-lens** pass on MEDIUM;
on COMPLEX, replace it with a lens-diverse pass. (Full cost table in `scaffold-procedures.md`:
SMALL ≈4, MEDIUM ≈9, COMPLEX ≈14 full-model passes; the same-lens verify passes are the single
biggest lever because each re-runs the suite.)

### GAP 6 — The deep correctness-audit itself is unowned by the scaffold
`run-audit` is deterministic-detector-only. The **LLM correctness audit** — the thing that
actually found these bugs — is not a scaffold skill, so each repo hand-rolls CHARTER/CENSUS/
waves/oracles differently and their outputs don't feed a common ratchet.
**Fix direction:** a `correctness-audit` scaffold skill that standardizes the wave/charter/
census shape and **routes every generalizable finding into GAP 1's ratchet** on close.

---

## Honest non-gaps (do not force-fit a mechanism here)
Real bugs a general scaffold mechanism would **not** realistically catch — these need domain
judgment, not process:
- **Entity-resolution semantics** (extrends ENTITY-1/TA-2; psc name-normaliser) — correctness
  is domain-defined; the most a scaffold can add is an **eval-gate diffing against curated
  ground truth**, which is a per-repo asset, not a generic check.
- **NLP term-fragmentation / scoring-eval logic** (extrends EXT-1, DET-1's semantics) — the
  *nondeterminism* half of DET-1 IS mechanizable (unordered-iteration detector); the *is-this-
  the-right-score* half is not.
- **LLM-nondeterminism in product output** — mitigable (frozen seeds, eval deltas) but not
  fully gate-able.

Naming these keeps the recommendation credible: the scaffold cannot make domain bugs
impossible. What it *can* do — and today does not — is ensure that **once found, a class
never silently returns**, and that **tests meant to catch it aren't hollow.**

---

## What is working — preserve, do not over-correct
- **Tiered process + delegation harness + archive-as-handoff token economy** — sound; the
  reconciliation-at-archive rule is the load-bearing cost control. Leave it.
- **Premise/direction gates** — cheap relative to building the wrong thing; keep. (Minor:
  the explore direction-gate and the propose premise-verdict are near-duplicate pro reviews;
  acceptable, low cost.)
- **Simplicity + conditional security gates** — genuinely lens-diverse, diff-only, no suite
  rerun. Keep. The redundancy problem is *only* the self/pro/flash same-lens stack.

---

## Token-waste verdict (direct answer to the operator's question)
> "Do we really need self-review + deepseek-pro + deepseek-flash for verify of complex changes?"

**Not as three same-lens passes, no.** The third pass buys model weight, not a new question,
and the downstream record shows the bugs walked straight through all three. Keep **two**
independent views (self + one model) as the diversity guard; **reinvest the third pass into a
lens the stack is blind to today** (test-quality or data-scale). That is a net *upgrade* in
defect yield at equal-or-lower token cost — the rare win that is both cheaper and better. The
larger waste is not the verify stack at all; it is paying for breadth on the diff while paying
**nothing** for the ratchet (GAP 1) and test-quality gate (GAP 3) that would have actually
stopped these bugs.

---

## Sequencing (for the senior engineers)
1. **GAP 3 (test-quality detector)** — cheapest, highest immediate yield, unblocks nothing else.
2. **GAP 1 (ratchet rule + per-repo invariant framework)** — the compounding win; every later
   audit shrinks.
3. **GAP 5 (verify-stack redirect)** — pure process/skill edit, frees tokens to fund the above.
4. **GAP 4 (data-scale detector + verify rule)** — narrow, mechanical.
5. **GAP 6 + GAP 2 (correctness-audit + composition-audit skills)** — larger; land after the
   ratchet exists so their findings have somewhere to go.

Full actionable breakdown with tiers and Fable-vs-Opus routing → `OUTSTANDING-WORK.md`.
