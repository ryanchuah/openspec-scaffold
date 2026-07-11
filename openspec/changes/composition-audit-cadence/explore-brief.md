# Explore brief — composition-audit-cadence (OW-6)

**Date:** 2026-07-11 · **Author:** Fable orchestrator (explore phase)
**Proposed tier:** COMPLEX (new capability spec + skill + engine plumbing + two frozen-contract seams)
**Backlog source:** `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` OW-6 (GAP 2)
**Research digests (checkpointed):** `openspec/changes/composition-audit-cadence/research/`
(`composition-surface.md`, `gap2-evidence.md`, `ratchet-contracts.md`, `ow5-ow3-contracts.md`,
`prior-art-d5-d6.md`)

## Problem

Per-change verify is single-diff-scoped by design. A subsystem accreted from many approved
changes is never reviewed as a whole — and nothing in the scaffold ever *says it is time* to
review it. Concretely (see `research/gap2-evidence.md`):

- extrends accumulated ~45 archived feature changes with **zero** whole-repo review; when a
  hand-provoked audit finally ran, it found ~33 live defect classes that had each passed a
  green per-diff verify.
- The tightest recurrence data: the MEAS-1 ground-truth-destruction shape re-shipped in a
  *different module one wave apart* — days-to-weeks, not months. psc-monitor's B5 → CA-W2-05
  sibling recurrence gap was ~3–6 weeks.
- Both audits happened only because an operator got suspicious. The instruments already
  existed and were idle: jscpd/vulture/radon ship in `checks.py` but are `enabled: False`
  with no trigger heuristic (`research/composition-surface.md`); `audit_scope.py scan` is
  delta-aware but only ranks hotspots; `knowledge-drift-review` is pull-only; and the
  staleness signal (`audit_anchor.commits_since`) is computed in two places **and read by
  nothing** — the run-audit skill's only cadence policy is prose ("trigger when it grows
  large enough").

**Root cause:** the scaffold has whole-repo *instruments* but no whole-repo *occasions*. Cadence
exists nowhere as a mechanism, so composition review depends on operator heroics. (OW-5's
frozen artifacts confirm this is deliberately left open: "OW-6's cadence/trigger machinery"
is an explicit OW-5 non-goal — `research/ow5-ow3-contracts.md`.)

## What the evidence does NOT support (honest limits)

The counter-evidence (`research/gap2-evidence.md`) caps what a detector sweep can claim:
~30+ of ~36 catalogued composition-shaped classes required cross-module LLM judgment; jscpd
itself *undersold* a real three-way duplication when it did run (W4-T4(b)). So a cadenced
detector run is **not** a substitute for a chartered correctness audit (OW-5). The cheap
pass earns its keep three ways: (1) it fires at all (the trigger), (2) it catches the
narrow mechanical slice early (near-dup siblings, dead code, parallel-artifact drift), and
(3) it is the standing *escalation decision point* into an OW-5 audit.

## Proposed direction (v1)

Three pieces, smallest mechanism that closes the gap:

### 1. Deterministic cadence trigger — advisory, count-based, zero boot cost
A "composition-audit due" signal computed from repo state and surfaced where outstanding
work is already enumerated: the `outstanding` fact (pull-only, regenerates on use). Trigger
semantics: **archived-changes-since-last-composition-anchor ≥ N** (evidence favors counting
approved changes over calendar time; recurrence was provoked by change volume), with
commits-since as the fallback signal for repos where work lands without archives.

**Anchor = a composition-discriminable tag in the existing `audit/*` family** (e.g. a
composition-suffixed tag laid by the same operator-gated `audit_scope.py tag` surface, plus
the standard audit-log line). Machine-discriminable is the requirement: a plain `run-audit`
tag MUST NOT reset the composition clock — run-audit does not execute the composition
detectors, so letting its tag satisfy the trigger would silently mask composition debt
(premise-review 🟡1). Only a composition anchor resets the composition cadence; a
composition anchor may also count as a general audit anchor (it is a superset). Exact
tag/lint format extension is a design decision.

Threshold is a per-repo config key with a scaffold default. **Honest framing of
automaticity (premise-review 🟡2):** this is an advisory *staleness signal*, not a
self-firing timer — in v1 it becomes visible when the `outstanding` fact is regenerated
(outstanding-work-review, or any skill that pulls it). Whether it additionally gets a
**non-gating** notice on a recurring surface (e.g. a warning-level line in the
commit-time lint/test output) so it reaches operators who never pull, is carried to
design as an open question — the signal must never become a gate. The operator remains
the executor (no autonomy, consistent with house rules).

### 2. A `composition-audit` skill — the cheap recurring ceremony
Operator-invoked, ~an afternoon not ~a week, positioned explicitly below OW-5:
- **Preconditions:** wired audit layer (reuse run-audit's wiring-detection branch), clean tree.
- **Deterministic sweep:** one-shot run of the heavy-tier composition detectors
  (jscpd, vulture, radon) *without* permanently enabling them per-repo, plus
  `audit_scope.py scan` for delta-since-anchor hotspot ranking, plus `checks.py --baseline`
  diff against the previous composition run (D6's "delta pays from cycle 2" — needs a small
  standing-baseline pointer, a known gap: today `--baseline` must be passed by hand).
- **Judgment layer (bounded):** cheap-model pre-digest of the detector wall → shortlist
  (the archived D5 campaign shape, graduated from one-time to recurring), then ONE
  orchestrator composition-lens pass over the **top-K ranked hotspots only** — cross-module
  sibling drift, accreted duplication, invariant coherence. Not a whole-repo LLM crawl.
- **Machine-discriminable outcome:** `COMPOSITION: CLEAN | FINDINGS-ROUTED |
  ESCALATE` — where `ESCALATE` is a recommendation to charter an OW-5 correctness audit
  (recommendation only; chartering stays operator-gated).
- **Close-out:** the OW-2 triage-then-append pattern — 3-question triage per finding →
  `knowledge/ratchet-log.md` lines + one audit-log line + the operator-gated
  **composition-anchor tag** (the only thing that resets the composition cadence clock). OW-2 names OW-6 as a consumer of exactly this seam but pins no hook;
  the skill defines its own close-out step mirroring run-audit's Step-3 shape
  (`research/ratchet-contracts.md`).

### 3. Nothing else
Not a gate (never blocks commits/verify), not autonomous, not wired into archive or boot,
does not flip heavy detectors on permanently, does not touch the per-change verify chain
(OW-3's tier-keyed lens contract is untouched — composition is explicitly out of verify's
scope in OW-3's frozen brief).

## Scope

- New capability spec `composition-audit` (trigger semantics + ceremony contract + verdict
  + close-out routing).
- New `.claude/skills/composition-audit/SKILL.md` (scaffold-managed, manifest entry).
- `outstanding` fact delta: surface the due-signal (spec delta to `outstanding-work-view`).
- Small engine plumbing in `scripts/checks.py`/`facts.py`: archived-changes-since-anchor
  computation; a one-shot include mechanism for disabled heavy checks; a standing
  composition-baseline pointer. Exact shape is a design decision.
- Per-repo config key(s) for the threshold (schema note in the `checks.py` docstring).

## Out of scope

- OW-5's charter/census/wave machinery (different instrument; shared vocabulary only —
  `Class:` slugs and ratchet routing).
- Any change to the verify multi-model chain (OW-3 owns it).
- Auto-remediation, auto-tagging, cron/CI wiring, or any autonomous invocation.
- Enabling jscpd/vulture by default in downstream repos.
- The cross-change spec-conflict-detection roadmap item (noted as a future absorber:
  a later composition pass could host it — long-term path, not v1).

## Open questions carried to design

1. One-shot heavy-check mechanism: a `checks.py --include <check>` override flag vs a
   documented temporary-config pattern (flag preferred: deterministic, no config churn;
   must not subject the run to preflight-abort for unrelated missing tools).
2. Standing-baseline pointer: file convention under `output/checks/` (untracked) vs a
   tracked pointer; interaction with D6 fingerprint diffing.
3. Threshold default and per-repo key placement (`checks.toml` vs the fact's own config) —
   plus exact fallback semantics when a repo has no archive dirs, AND the mixed-signal
   case where archives exist but are sparse relative to commit volume (e.g. 3 archives
   across 50 commits — should the commits-since fallback co-fire?).
4. Whether `knowledge-drift-review` is invoked inside the ceremony or merely recommended
   by it (leaning: recommended step, keep the ceremony's mandatory core deterministic).
5. Whether the staleness signal also gets a **non-gating** notice on a recurring surface —
   e.g. a warning-level `knowledge_lint`/lint-output line parallel to `_check_untriaged_age`
   but never failing the run — so it reaches operators who never pull the `outstanding`
   fact. Constraint: must not gate commits/CI (composition review is never a gate).
6. Composition-anchor tag format + the `knowledge_lint` audit-log line check extension
   (the existing check pins `audit/<date>`; the composition variant must stay lintable).

## Dependencies & sequencing

- **Propose now against frozen contracts** (same pattern OW-5 used against OW-2): the
  ratchet ledger format, disposition taxonomy, and triage questions are frozen in
  `lesson-check-ratchet`; the escalation target's protocol marker is frozen in
  `correctness-audit-skill`.
- **Apply gated on OW-2's apply** (ratchet must be live) and **ordered after OW-5's apply**
  (the ESCALATE verdict references the correctness-audit skill by name). Recommended batch:
  OW-2 → OW-3 → OW-5 → OW-6 in one Opus apply session.
- Parking OW-6's apply blocks nothing in the backlog.

## Risks

- **run-audit ceremony itself is only downstream-proven piecemeal** (`knowledge/questions/
  run-audit-untested.md`): OW-6 reuses its surfaces (tag, audit-log, wiring detection)
  rather than inventing parallel ones — that reuse is the mitigation, and the first
  composition run doubles as the end-to-end exercise of the shared ceremony surface.
- **Detector-wall noise on first run:** mitigated by D5's pre-digest + top-K bounding +
  D6's baseline from cycle 2; first run triages the wall once (that cost is real and
  stated, not hidden).
- **Trigger nagging / threshold miscalibration:** advisory-only placement in a pull-only
  fact bounds the annoyance; threshold is per-repo tunable.
- **Signal unseen if pulls lapse:** the inverse risk — a pull-only signal depends on
  operator attention (the very failure mode this change addresses). Mitigation: open
  question 5 (non-gating recurring-surface notice); if design rejects it, the residual
  dependence is stated in the skill, not hidden.
- **Chain-shape prose drift** (OW-3 session finding 5 pattern): the ceremony sequence is
  stated once in the spec and cited elsewhere — no restatements.
