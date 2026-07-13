# Explore brief — correctness-audit-skill (OW-5)

**Date:** 2026-07-11 · **Tier:** COMPLEX · **Origin:** scaffold gap analysis GAP 6
(`knowledge/research/scaffold-gap-analysis-2026-07/SYNTHESIS.md`), backlog item OW-5
(`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`).
**Research inputs (checkpointed):** `openspec/changes/correctness-audit-skill/research/`
— `psc-audit-method.md`, `extrends-audit-method.md`, `ratchet-and-verify-contracts.md`,
`scaffold-conventions.md`.

## Problem

The deep LLM correctness audit — the activity that actually found the downstream bug
classes the per-change verify gates missed — is not owned by the scaffold. `run-audit`
covers only deterministic detectors. Both downstream repos therefore hand-rolled the
same multi-week audit program independently: extrends wrote a methodology playbook
(PD1–PD13) plus a charter and four subsystem waves; psc-monitor then **ported that
playbook and re-derived everything by hand** (ground rules GR1–GR10, a product severity
taxonomy S1–S7, a census). Two hand-rolled implementations of one recurring pattern is
the definition of a scaffold gap.

Because the method lives only as per-repo prose, its known failure modes repeat and
never get fixed centrally. Documented in both repos' own dossiers:

1. **Cross-wave duplicate findings** — extrends W3-E3 / W4-M2a fully re-investigated the
   same `labels_io.py` data-loss mechanism one wave apart; psc CA-W1-20 / CA-W2-30. No
   step checks a new lead against prior waves' output.
2. **No stopping rule** — extrends had no census; each wave self-declared "COMPLETE"
   with nothing to measure open-ended discovery against. psc's census (one disposition
   per module) is the missing completeness proof.
3. **Unreliable adversarial refuters** — psc's refutation pass was itself wrong ~4/9 in
   one graduation batch, caught only by orchestrator re-check; the overrule discipline
   exists only as a lessons.md paragraph.
4. **Closure without enforcement** — findings closed `intentional-by-design`/`doc-only`
   carry no check or test; nothing mechanically prevents regression. (psc names this
   openly; it is the exact gap OW-2's ratchet exists to close.)
5. **Defect classes never named as classes** — extrends found three instances of one
   pattern ("an internal success/failure signal never reaches the layer that acts on
   it") in three subsystems across waves and never connected them; unnamed classes
   cannot be triaged into a ratchet.
6. **Outputs feed no common mechanism** — each repo's FINDINGS format is a dialect; no
   link to finding-closure or outstanding-work visibility.

## Root cause

The audit **protocol** (artifact contract, evidence discipline, wave mechanics,
close-out routing) is repo-neutral and stable, but it has no scaffold home — so each
repo re-derives it, drifts, and inherits the method's unfixed weaknesses. The judgment
content (what to audit, how severe things are) genuinely is per-repo; the protocol is
not.

## Solution direction

A scaffold-managed, **operator-invoked** `correctness-audit` skill (sibling of
`run-audit` / `knowledge-drift-review` / `outstanding-work-review`; pull-only, never
auto-triggered) that standardizes the protocol and mechanizes its known failure modes,
while explicitly leaving product judgment per-repo.

**Scaffold-owned (the skill + templates + a small lint):**
- **One charter artifact** (folding psc's CHARTER/brief split into a single governing
  doc): scope, ground rules, per-repo severity taxonomy, wave plan, verification-method
  map, stopping rule, prior-knowledge register pointer.
- **Census as completeness proof and stopping rule**: one line per in-scope surface,
  exactly one disposition (`AUDITED-clean` / `AUDITED-finding` / `LEAD-deferred` /
  `N/A-<reason>`); a wave is complete when its census slice is fully dispositioned —
  fixes weakness 2. Skeleton seedable from the existing `facts.py` inventory fact.
- **FINDINGS entry contract**: IDs `CA-W<wave>-<seq>` (matches the shipped
  `outstanding.py` default pattern); method-named evidence labels
  (`VERIFIED-BY-{repro|trace|test}` / `LEAD` / `REFUTED`, never bare "confirmed");
  lead → adversarial refutation → graduation with the **refuter-overrule rule**
  (a refuter's verdict is itself a claim the orchestrator re-checks — fixes 3);
  a mandatory **`Prior:` field** (dossier+register grep before write-up: either
  `none (grep clean)` or `<ID> — distinct because …` — mechanizes dedup, fixes 1);
  a mandatory **`Class:` kebab-slug** shared with the ratchet ledger's class slugs
  (fixes 5).
- **Ground rules**: audit-then-fix (findings only; narrow fix-now for audit
  instruments), read-only + snapshot discipline, wave gates (operator checkpoint
  between waves), orchestrator-only severity/evidence finalization, model routing
  (judgment → pro-tier, mechanical → flash), never-record-counts with the
  coverage-percentage trap named.
- **Close-out routing into OW-2's ratchet** (fixes 4 and 6): every graduated finding
  runs the frozen Q1/Q2/Q3 triage; qualifying classes land as
  `knowledge/ratchet-log.md` registry lines with `check:`/`test:`/`waiver:`/`open:`
  dispositions — including `doc-only`/`intentional-by-design` closes, which must carry
  a ledger disposition instead of closing silently. Remediation itself stays out of the
  audit: ordinary OpenSpec changes citing finding IDs (both repos converged on this;
  both fix-promptly and defer-all postures are legal operator calls the skill surfaces
  at close-out).
- **Output location contract**: `knowledge/research/correctness-audit-<date>/` — makes
  every finding automatically visible to the shipped `outstanding` fact and the 14-day
  untriaged-age `knowledge_lint` check (zero new wiring; the accountability ratchet is
  already live).
- **A small deterministic dossier lint** (mechanism over docs): duplicate finding IDs
  across a dossier, invalid census dispositions, missing `Prior:`/`Class:` fields.

**Per-repo (deliberately not standardized):** severity taxonomy (product-derived by
rule — both repos insist on this), wave decomposition, verification-method map content,
census content, remediation sequencing posture.

**Deliberate lifecycle simplification:** audit waves ship findings, not production code
— so the skill does not require the multi-model verify stack per wave; the
adversarial-refutation graduation IS the audit's verification mechanism. (Evidence:
psc's per-wave OpenSpec-change-with-full-verify overhead is its own top-listed
weakness; extrends' final-verify spot-check re-derived only 2 of ~19 Wave-4 findings
anyway.) Remediation changes still run the normal lifecycle at their tier.

## Out of scope

- OW-6's cadenced composition-audit (different trigger and scale; shares only the
  ratchet close-out seam, which this skill establishes).
- OW-1/OW-4 detectors; retroactive remediation of downstream audit backlogs;
  back-porting existing downstream dossiers to the new format.
- Auto-provisioning per-repo config from inside the skill (detect-and-explain, per
  run-audit precedent).

## Dependencies / sequencing

- **Apply-order dependency on OW-2** (`lesson-check-ratchet`): the close-out step needs
  `knowledge/ratchet-log.md`, its lint, and the triage text live. Propose can proceed
  now against OW-2's frozen contract text; **OW-5 apply must land after OW-2 apply.**
- **No dependency in either direction with OW-3** (`verify-stack-redirect`).
- Nothing else in the backlog depends on OW-5.

## Success criteria

- A downstream repo can run a correctness audit by invoking one skill, producing
  charter/census/FINDINGS in the standard shape, with zero method re-derivation.
- Every graduated finding ends the audit either remediated-with-regression-test,
  ratcheted (`check:`/`test:`), or visibly waived/deferred — no silent prose closure.
- Untriaged findings surface automatically via the outstanding fact and go stale-loud
  via knowledge_lint within 14 days.
- The known hand-rolled failure modes (1–6 above) each map to a named mechanism in the
  skill, not a warning paragraph.
