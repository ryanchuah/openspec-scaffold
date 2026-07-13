# Proposal — correctness-audit-skill

## Why

The deep LLM correctness audit — the activity that found the downstream bug classes every
per-change verify gate missed — is not owned by the scaffold: `run-audit` covers only
deterministic detectors. Both downstream repos therefore hand-rolled the same multi-week
audit program independently (extrends wrote a playbook + charter + four waves; psc-monitor
then **ported that playbook and re-derived it by hand**), and their dossiers document the
same repeating, fixable failure modes: cross-wave duplicate findings (extrends W3-E3/W4-M2a,
psc CA-W1-20/CA-W2-30), no stopping rule (extrends had no census), unreliable adversarial
refuters (psc overruled ~4/9 refuter verdicts in one batch), closures with no enforcing
check (`intentional-by-design` / `doc-only`), defect classes never named as classes, and
outputs feeding no common closure mechanism. A protocol that already propagates by hand —
minus its bug fixes — is precisely what the scaffold exists to own (gap analysis GAP 6,
backlog OW-5).

## What Changes

- **New scaffold-managed skill `.claude/skills/correctness-audit/SKILL.md`** — operator-
  invoked, pull-only (sibling of `run-audit` / `knowledge-drift-review` /
  `outstanding-work-review`). It standardizes the audit **protocol** and leaves product
  judgment per-repo:
  - One **charter** artifact (scope, ground rules, per-repo severity taxonomy, wave plan,
    verification-method map, stopping rule, prior-knowledge register) — folding the
    charter/brief split both repos improvised into a single governing doc.
  - A **census** as completeness proof and stopping rule (one disposition per in-scope
    surface: `AUDITED-clean` / `AUDITED-finding` / `LEAD-deferred` / `N/A-<reason>`);
    a wave is complete when its census slice is fully dispositioned.
  - A **FINDINGS entry contract**: `CA-W<wave>-<seq>` IDs (matches the shipped
    `outstanding.py` default ID pattern); method-named evidence labels
    (`VERIFIED-BY-{repro|trace|test}` / `LEAD` / `REFUTED`); lead → adversarial
    refutation → graduation with an explicit refuter-overrule rule; a mandatory `Prior:`
    dedup field (dossier + register grep before write-up); a mandatory-to-fill `Class:`
    field — a kebab-slug shared with the ratchet ledger's class slugs for generalizable
    findings, or the literal sentinel `Class: none (one-off)` for findings that are not
    generalizable (consistent with OW-2's Q2=no → no ledger entry).
  - **Ground rules**: audit-then-fix, read-only + snapshot discipline, operator wave
    gates, orchestrator-only severity/evidence finalization, model routing (judgment →
    pro-tier, mechanical → flash; severities never set by the executor tier),
    never-record-counts with the coverage-percentage trap named.
  - **Wave execution model (decided here to bound the file surface):** delegated wave
    work uses the platform's existing delegation mechanics — `opencode run` under the
    shared delegation harness, or in-process subagents where the platform provides them
    (harness carve-out). Wave work is **sliced into bounded, checkpointed invocations
    that reuse the sanctioned budget pairs** (`-k 15 780` review-class for
    investigation/refutation; `-k 30 600` executor-class if a mechanical slice needs it)
    — granularity buys resumability, and no new harness budget row is introduced, so
    `.claude/skills/_shared/delegation-harness.md` is NOT modified by this change.
  - **Close-out routing into the finding-closure ratchet** (`lesson-check-ratchet`, OW-2):
    every graduated finding runs the frozen Q1/Q2/Q3 triage; qualifying classes land as
    `knowledge/ratchet-log.md` registry lines; `doc-only` / `intentional-by-design` closes
    carry a ledger disposition instead of closing silently. Remediation stays out of the
    audit: ordinary OpenSpec changes citing finding IDs.
  - **Output-location contract**: `knowledge/research/correctness-audit-<date>/` — findings
    become automatically visible to the existing `outstanding` fact and the 14-day
    untriaged-age `knowledge_lint` check (composition, zero new wiring).
- **New deterministic dossier lint** in `scripts/knowledge_lint.py` (absent-dossier lints
  clean, same shape as the ratchet-log check): duplicate finding IDs across a dossier's
  FINDINGS files, invalid census disposition values, missing `Prior:` / `Class:` fields on
  graduated findings.
- **Registration/propagation edits**: one `scaffold_manifest.txt` line for the new skill;
  `correctness-audit` added to `scaffold_lint.py`'s `_NON_OPENSPEC_SKILL_TOKENS` (the set's
  own comment says "keep in step with actual .claude/skills/ non-openspec dirs" — belt-and-
  suspenders over the dir-name fallback, which already resolves the token); a one-sentence
  disambiguation appended at the **end** of `AGENTS.md`'s audit-tooling section — naming the
  two audit families (deterministic detector ceremony vs. operator-invoked LLM
  correctness-audit program) rather than interleaving with the ceremony prose — and a
  cross-pointer in `run-audit/SKILL.md`.
- **Deliberate lifecycle simplification** (recorded as a rule in the skill): audit waves
  ship findings, not production code, so a wave does not run the multi-model verify stack —
  adversarial refutation IS the audit's verification. Remediation changes run the normal
  lifecycle at their tier.

## Capabilities

### New Capabilities
- `correctness-audit`: the protocol contract for deep LLM correctness audits — artifact
  shapes (charter / census / FINDINGS), evidence-and-graduation discipline, dedup and
  class-naming duties, wave mechanics and gates, and close-out routing into the
  finding-closure ratchet.

### Modified Capabilities
- `knowledge-lint`: gains one requirement — a detect-only dossier-format check (duplicate
  finding IDs, invalid census dispositions, missing `Prior:`/`Class:` fields), silent when
  no dossier exists.

## Impact

- **New files**: `.claude/skills/correctness-audit/SKILL.md`;
  `openspec/specs/correctness-audit/spec.md` (via delta).
- **Modified files**: `scripts/knowledge_lint.py` + `scripts/test_knowledge_lint.py`
  (dossier check); `scripts/scaffold_manifest.txt`; `scripts/scaffold_lint.py`
  (`_NON_OPENSPEC_SKILL_TOKENS`); `AGENTS.md` (one sentence, synced span);
  `.claude/skills/run-audit/SKILL.md` (one cross-pointer line).
- **Deliberately untouched**: `scripts/outstanding.py`, `scripts/checks.py`, `facts.py`
  surfaces (the skill composes their shipped behavior); `checks.toml` (per-repo, never
  synced); downstream repos' existing dossiers (no back-porting).
- **Sequencing**: apply-order dependency on `lesson-check-ratchet` (OW-2) — the close-out
  step routes into `knowledge/ratchet-log.md` and its lint, which must be live first.
  Propose proceeds now against OW-2's frozen contract text. No dependency in either
  direction on `verify-stack-redirect` (OW-3). **Known-risk note:** OW-2's frozen spec has
  a live one-word validator defect (its closure requirement fails `openspec validate
  --strict` SHALL-detection; recorded as finding 1 in the gap-analysis OUTSTANDING-WORK.md,
  to be fixed in OW-2's apply session). OW-5 cites OW-2 by requirement names and interface
  shapes (triage questions, ledger line format, disposition keywords), which that one-word
  normative fix does not alter — if OW-2's apply changes anything beyond that word, re-check
  OW-5's citations before its own apply.
- **Downstream**: propagates to extrends / psc-monitor via the normal operator-gated sync;
  their future audits adopt the standard shape (existing dossiers untouched).
