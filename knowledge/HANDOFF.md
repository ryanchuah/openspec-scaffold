# HANDOFF — OW-15 (correctness-audit-meta-hardening) shipped; wave-2 remaining OW-12/OW-16 + OW-11 residual (2026-07-14)

> **Read this right after `knowledge/STATUS.md`.** A session shipped **`correctness-audit-meta-hardening`
> (OW-15, MEDIUM)** end-to-end — plan → propose → apply → verify → archive, committed on `main`, local &
> **unpushed** (push is operator-gated). Downstream propagation is **DEFERRED + operator-gated**. Absorb
> this, pick up from **Remaining work**, and **delete this file once absorbed**. Its normal state is absent.
>
> **You have NO standing autonomy grant.** Confirm tier+plan per change unless the operator re-grants
> autonomy.

## DONE this session — correctness-audit-meta-hardening (OW-15)
Four deltas to the shipped `correctness-audit` capability: (1) liveness — an in-progress dossier stays
an Active `knowledge/questions/INDEX.md` item; charter `status:` marker `in-progress`→`closed`;
remediation programs use a namespace distinct from discovery `WAVE-N` rows; (2) a blind close-out
coverage-gap review (four-marker taxonomy diff; blind-taxonomy + evidence-fanout both load-bearing);
(3) a bounded scope-seeding checklist inlined in the skill (11-group dimension seed + 12 named
blind-spot classes; **classes 9-12 are awareness pointers only — the claims-ledger mechanism is OW-16,
not built here**); (4) a post-close `POST-CLOSE-LEDGER.md` requirement for persistence-touching changes.
Plus two new guarded `knowledge_lint` detectors (`audit-liveness`, `post-close-ledger-format`), both
gated on the existing `format: correctness-audit/v1` marker. Verify: premise AGREE, pro behavioral
verifier READY with zero defects, 9 orchestrator-authored adversarial fixtures held, `check.sh` green,
zero Sonnet fallback anywhere in the lifecycle. Full record: decisions —
`knowledge/decisions/INDEX.md` (`correctness-audit-meta-hardening`); follow-ons —
`knowledge/questions/correctness-audit-meta-hardening-follow-ons.md`; archive —
`openspec/changes/archive/2026-07-14-correctness-audit-meta-hardening/`.

## ⭐ Corrected stale-tracker finding — verify archive vs tracker STATUS lines before trusting them
This change's own premise was almost blocked by a stale line: `OUTSTANDING-WORK.md`'s OW-5 entry still
read "PROPOSE COMPLETE — PAUSED AT APPLY" even though OW-5 (`correctness-audit`) **shipped 2026-07-13**
(`openspec/changes/archive/2026-07-13-correctness-audit-skill/`). The prior HANDOFF and `STATUS.md` both
repeated the stale "OW-15 BLOCKED on OW-5" claim, inherited from the tracker without re-checking the
archive. **Both are now corrected** (OW-5's STATUS line → SHIPPED; OW-15 marked SHIPPED). Lesson: a
tracker's STATUS line is a snapshot, not a live fact — when a backlog item's actionability hinges on
another item's ship state, check `openspec/changes/archive/` directly, not just the tracker prose.

## Remaining work — OW-12, OW-16, OW-11 residual
- **OW-12 · Archive mechanization · SMALL–MEDIUM · lowest priority · no recon yet.** `archive_move.py`
  for the dir move; deterministic delta-applier for ADDED/REMOVED/RENAMED (LLM only for MODIFIED merge
  + reconciliation narrative). Keep the archive-executor on pro.
- **OW-16 · `product-audit` skill (promise-surface / business-thesis audit) · chain-independent
  greenfield.** Carries forward this change's classes 9-12 (copy↔capability conformance / claims ledger,
  entitlement-state reachability, severity-taxonomy completeness, source-class labeling) as the
  operationalization target, plus the claims-ledger convention itself. Slots anywhere; see
  `OUTSTANDING-WORK.md` OW-16 entry and `knowledge/roadmap.md`.
- **OW-11's fuzzy de-bloat half** remains parked (`knowledge/questions/skill-debloat-gates-follow-ons.md`).
- **OW-15 residual follow-ons** (monitored, none blocking) →
  `knowledge/questions/correctness-audit-meta-hardening-follow-ons.md`: liveness substring-match
  false-negative; Delta-4 ledger should-exist-after-close-out obligation (deferred, protocol-level not
  lint-level); ledger at-least-five cell tolerance.

## Downstream propagation — DEFERRED + operator-gated
This change edited scaffold-managed surfaces: `scripts/knowledge_lint.py` + `test_knowledge_lint.py`
(two new detectors), `.claude/skills/correctness-audit/SKILL.md`, and the `correctness-audit` +
`knowledge-lint` capability specs. NOT synced to extrends/psc-monitor without fresh operator
authorization. Both new lint checks are guarded on the existing format marker — no new downstream lint
failures expected on first sync. Migration note for whoever runs the propagation: a downstream dossier
that later adopts the marker while genuinely still in-progress needs a `status:` line added (a one-time
reconciliation the liveness check will otherwise correctly flag). Running ledger:
`knowledge/reference/pending-downstream-propagation.md`.

## Pointers
- Backlog + per-item STATUS: `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`.
- Evidence sources for OW-15: `psc-coverage-gap-review-2026-07-11.md`,
  `extrends-coverage-gap-review-2026-07-12.md`, `psc-strategy-pressure-test-2026-07-12.md` (same dir).
- This change (full record): `openspec/changes/archive/2026-07-14-correctness-audit-meta-hardening/`.
