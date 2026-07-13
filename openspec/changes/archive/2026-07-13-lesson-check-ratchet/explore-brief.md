# Explore brief — lesson-check-ratchet (OW-2)

**Date:** 2026-07-10 · **Author:** Fable (orchestrator) · **Tier proposal: COMPLEX**
**Source:** `knowledge/research/scaffold-gap-analysis-2026-07/` (SYNTHESIS.md GAP 1,
OUTSTANDING-WORK.md OW-2), grounded in the extrends + psc-monitor correctness-audit corpora.

## Problem

Discovered defect classes do not durably close. When a bug is found — by verify, by an
incident, or by a hand-built correctness audit — the fix is a point fix and the *class* is
recorded as prose (`knowledge/lessons.md`, change `notes.md`, audit FINDINGS dossiers). Prose
is write-only memory: nothing re-reads it on every future diff, so sibling instances of the
same shape re-ship and are only re-found by hand, later, at audit cost.

This is proven twice over, in two independent repos governed by this scaffold:

- **psc-monitor:** the B5 livelock post-mortem (unbounded `fetchall()`, 14.6M rows) wrote an
  explicit "grep for this" lesson; a sibling unbounded fetch in the *same module family*
  (CA-W2-05) survived until a full audit re-found it by hand months later. Same story for the
  F16 transaction-visibility lesson → CA-W2-02, in the same file/function family.
- **extrends:** ground-truth-silently-destroyed-on-load recurred one wave apart
  (`labels_io.py` W3-E3 → `console/labels_io.py` W4-M2a); the fail-soft-invisible-to-health
  shape was found 3× across waves (OPS-2); wrong-boundary mocking was independently
  rediscovered by two separate audit programs (TQ-2). All *within the same multi-week
  program* — recurrence outruns even an active, well-funded audit.

## Root cause

Two coupled gaps, both structural:

1. **No closure contract.** Nothing defines when a generalizable finding is "closed." Today
   closure de facto = "the instance was fixed and a paragraph was written." No tracker has
   the semantics "this defect *class* is now mechanically enforced," and no lint can flag a
   class left unenforced, so the open state is invisible.
2. **No cheap place to put an enforcing artifact.** The deterministic layer has generic
   detectors (ruff/gitleaks/jscpd/…) and exactly one domain-invariant mechanism —
   `data_lint.py`'s flat `checks/*.sql` convention (one file = one invariant, violating rows
   = fail, read-only, timeout-bounded). There is no equivalent slot for *code-shape* or
   *repo-shape* invariants ("no unbounded fetchall in pipeline/", "every fail-soft status key
   is read by run_health.py", "test fixtures must not set autocommit=TRUE"). `[checks.custom.*]`
   exists but is an unparsed escape hatch with no conventions, no findings schema, and no
   process step that ever asks for one. When registering a check costs a design session,
   nobody registers one; the lesson stays prose.

## Proposed solution direction (three legs, one change)

1. **Closure rule (the ratchet).** A scaffold rule: a generalizable finding is not closed
   until it has (a) an enforcing deterministic check, (b) a frozen regression test, or
   (c) an explicit recorded waiver (for domain-judgment-only classes — the honest non-gaps).
   Each ratchet entry carries a machine-checkable disposition; `knowledge_lint.py` (or a
   sibling) flags entries with no disposition and dispositions pointing at artifacts that
   don't exist. The rule is enforced by lint, not by asking agents to remember — mechanism
   over docs, applied to the mechanism-over-docs rule itself.
2. **Per-repo invariant framework.** Generalize the proven `data-lint` convention sideways:
   a flat per-repo directory where one file = one domain invariant, zero findings = pass,
   read-only, timeout-bounded, registered in `checks.py` as a delegating check and
   auto-enabled when the directory is non-empty. v1 artifact types: SQL data invariants
   (exists today), code/repo-shape detectors (new runner; implementation choice — bespoke
   per-file Python vs. semgrep/ast-grep rules — is a design.md decision backed by a
   battle-tested-options research pass), and frozen regression tests (pytest, exists today;
   the ratchet just records the linkage). Target scale is D4-scale: ~5–15 invariants per
   repo, flat files, no framework ceremony.
3. **Close-out routing.** The two existing finding close-out points get one cheap triage
   step each: **archive** (per-change: any bug found+fixed during the change) and
   **run-audit triage** (deterministic findings judged real). The step is a ≤1-minute
   classification: *generalizable class or one-off? if class → pattern-detectable or
   domain-judgment? → detector / frozen test / waiver.* Output: one ratchet ledger line +
   the enforcing artifact (or waiver rationale). The future `correctness-audit` skill (OW-5)
   and composition-audit (OW-6) will route their findings into this same interface — this
   change defines the interface; it does not build those skills.

## Scope framing

**In scope:** the closure rule + its lint enforcement; the invariant-framework runner +
`checks.py` registration + conventions doc-string; the ledger format/location; the two
close-out routing steps (archive skill, run-audit skill); scaffold's own tree passing the
new lint; propagation-readiness (scaffold-managed files only).

**Out of scope:** OW-1's generic test-quality detectors and OW-4's generic data-scale
detector (upstream scaffold detectors, separate changes — though they are natural first
tenants of the framework's conventions); OW-5/OW-6 audit skills (they consume this
interface later); any retroactive remediation of the extrends/psc finding backlogs
(downstream execution work); back-filling detectors for every existing lessons.md entry
(a follow-on sweep, not a gate on this change — existing lessons are grandfathered with an
explicit one-time triage parked as follow-up).

**Ergonomics constraint (load-bearing):** if the triage step or the framework costs more
than minutes per finding, it will be skipped under deadline pressure and the ratchet becomes
bureaucracy. The design must keep: classification ≤3 questions; detector = 1 dropped file;
waiver always available but explicit and lintable. Get this wrong and the change is net
negative.

**Blast radius:** scaffold-managed files (`checks.py`, new runner script, `knowledge_lint.py`,
AGENTS.md rule text, archive + run-audit skills) → propagates to extrends and psc-monitor
via `sync_scaffold.py`. High blast radius is why this is COMPLEX and why the design is done
now (Fable) with apply/verify delegated later.

## Prior-art constraints honored (from `openspec/changes/lesson-check-ratchet/research/prior-art-digest.md`)

- **Slot into the existing engine, don't build a parallel one.** The invariant runner
  registers as a *delegating check* in `checks.py`'s existing registry (the `data-lint`
  pattern), emitting its own JSON — upstream parser surface stays limited, per the
  deterministic-tooling-layer decision.
- **D7 division of responsibility stands:** the scaffold ships the framework + conventions;
  each repo's actual invariants/config are follow-on SMALL changes downstream. This change
  does not auto-wire per-repo checks.
- **D3 stands:** everything in the ratchet is check-only; nothing auto-fixes.
- **The ledger is a new lint-first registry file in `knowledge/`** (registry-line discipline
  like `knowledge/audit-log.md` / `decisions/INDEX.md`; per-repo content, scaffold-managed
  format), NOT structured fields bolted into `lessons.md` — lessons stay narrative.
- **Precedent, not invention:** `scaffold_lint.py`'s `budget-agreement` check is the existing
  artifact-vs-artifact cross-check shape; `mechanize-invariants` (2026-07-02) already
  converted 4 specific prose invariants into lint — this change generalizes that move into a
  standing closure contract instead of a one-off.
- **YAGNI reconciliation:** two prior conscious deferrals ("count-recording check — YAGNI
  until the rake recurs") are *not* contradicted — they are exactly what the ratchet
  formalizes as an explicit waiver-with-trigger disposition. The ratchet does not mandate a
  check per finding; it mandates an explicit, lintable *decision* (check | frozen test |
  waiver+reason). The evidence base for the contract itself is systemic (two repos, dozens
  of recurrences), not a single incident.

## Why this over alternatives

- **"Just write better lessons"** — refuted by the evidence: both repos wrote excellent
  lessons and the classes still recurred; prose does not execute.
- **"Rely on the generic detector suite"** — generic detectors can't know that
  `run_health.py`'s signal list must cover every fail-soft site, or that this repo's
  fixtures must not use `autocommit=TRUE`; domain invariants need a domain slot.
- **"Full policy-as-code platform (e.g. adopt a heavyweight rules engine)"** — over-scale
  for 3 repos at ~5–15 invariants each; contradicts the D4-scale precedent that made
  data-lint actually get adopted.

## Success criteria (direction-level)

A year from now, a repeat of the extrends/psc audits should find that previously-named
classes either (a) cannot recur because a check blocks them at commit/audit time, or
(b) were consciously waived with a recorded reason — and the next audit is measurably
smaller because each one shrinks the open-class set instead of re-discovering it.
