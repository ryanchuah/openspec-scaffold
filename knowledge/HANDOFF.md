# HANDOFF — resume the frozen OW-2→3→5→6 apply batch

**Written 2026-07-13.** Operator authorized resuming this batch in the session that wrote this
handoff (a full-repo outstanding-work crawl; see that session's `knowledge/questions/INDEX.md`
additions for what else it found — not relevant to this batch). This file is the sanctioned
ephemeral mid-session handoff (`knowledge/HANDOFF.md`, per `knowledge/decisions/INDEX.md`
`knowledge-handoff-file`) — **absorb it, continue the work below, then delete it.**

## What you're doing

Applying, verifying, and archiving **four already-frozen OpenSpec changes**, in this **hard
order**: **OW-2 → OW-3 → OW-5 → OW-6**. All four are propose-complete — proposal/design/tasks (and
spec deltas where applicable) are written, pro-reviewed to zero 🔴, and frozen. **Nothing needs
(re-)designing.** Your job is apply → verify → archive, per the standard OpenSpec lifecycle
(`.claude/skills/openspec-apply-change/SKILL.md`, `openspec-verify-change/SKILL.md`,
`openspec-archive-change/SKILL.md`).

**Orchestrator for all four: Opus (you), not Fable.** The design judgment is already made and
frozen; apply is delegated to deepseek-flash regardless of who orchestrates, and verifying a
well-specified frozen change is within your capability.

**Standard escalation caveat, all four changes:** implementation bugs found at verify are normal
defect-path work — diagnose, scope, re-delegate the fix to a fresh executor, continue. A
**DESIGN-level** defect (a frozen contract doesn't fit, an interface disagrees with reality, a
census/stopping-rule/lens contract is wrong) → **STOP and escalate to the operator or a Fable
session** rather than redesigning mid-verify.

## Why this order (dependency graph)

- OW-5's apply is gated on OW-2's apply (the correctness-audit skill routes findings into OW-2's
  ratchet — the ratchet must exist first).
- OW-6's apply is gated on **both** OW-2 (ratchet ledger must exist) and OW-5 (OW-6's ESCALATE
  path cites the correctness-audit skill).
- OW-3 has no hard dependency on the others, but land it **before** OW-5 so OW-5's own verify runs
  under OW-3's *new* verify-stack shape (see OW-3 below) rather than the old one.
- OW-7/9/11/14 (a separate, NOT-in-scope-here wave-2 backlog) edit the same skill files OW-3
  rewrites — do not touch those until this batch is fully archived.

## The four changes

### 1. OW-2 — `lesson-check-ratchet` (apply first)
**Dir:** `openspec/changes/lesson-check-ratchet/` — proposal, design, 2 spec deltas, tasks, all
pro-reviewed AGREE/PASS, zero 🔴. Research checkpointed under the change dir's `research/`.

**Scope:** a deterministic invariant runner <!-- lint:planned --> (`scripts/repo_lint.py`, not yet built — this apply creates it) plus the ratchet framework — turns "a generalizable finding is
closed" into "closed only with an enforcing check or a frozen regression test." Full scope is in
the change's own `design.md`/`tasks.md` — read those, not this summary, before delegating apply.

**⚠️ Known pre-apply fix — do this FIRST, before delegating apply:** the frozen delta
`specs/finding-closure-ratchet/spec.md` has an ADDED requirement
`generalizable-findings-close-only-with-a-recorded-disposition` that **lacks a SHALL/MUST verb**,
which fails `openspec validate`. Make the one-word normative fix yourself (mechanical, no
re-review round needed), disclose it in the change's `review-log.md`, then re-run
`openspec validate --strict` to confirm clean before delegating apply. (Source: OUTSTANDING-WORK.md
"New findings — 2026-07-10 OW-3 session", item 1.)

### 2. OW-3 — `verify-stack-redirect` (apply second)
**Dir:** `openspec/changes/verify-stack-redirect/` — tasks.md + 2 spec deltas + notes.md
acceptance criteria, frozen, direction gate + artifact review both AGREE/PASS, zero 🔴.

**Scope:** redirects the verify stack from breadth (three same-lens model passes) to lens
diversity. New shape: **MEDIUM** = self→pro; **COMPLEX** = self→pro→**lens pass** (a *prompt*, not
a new detector — test-quality lens by default, data-scale lens for data-path changes); **SMALL**
unchanged. Touches the verify skill + AGENTS.md roles + the delegation harness — this is the
change that governs every downstream verify from here on, so read `design.md`/`tasks.md` closely;
budgets (780s/-k15) are pinned and guarded by a budget-agreement lint.

**Verify note:** this change verifies itself under the **pre-change** (current) semantics —
self + pro only (see the change's own `notes.md` self-reference note) — since the new semantics
don't exist until this change ships.

### 3. OW-5 — `correctness-audit-skill` (apply third)
**Dir:** `openspec/changes/correctness-audit-skill/` — proposal, design, 2 spec deltas (new
`correctness-audit` capability + a `knowledge-lint` dossier-lint delta), tasks — 2 pro-review
rounds on design/specs (round 1 caught 2 🔴, both fixed pre-freeze), zero 🔴 outstanding,
`openspec validate --strict` clean.

**Scope:** standardizes the audit PROTOCOL other repos hand-rolled independently — single charter
(`format: correctness-audit/v1` marker), census-as-stopping-rule, FINDINGS contract with a
`Prior:` dedup field + `Class:` slugs shared with OW-2's ratchet, refuter-overrule graduation,
marker-gated dossier lint, ratchet-routed close-out. Severity taxonomy and wave decomposition stay
per-repo. Read `design.md` for the full contract before delegating apply.

**Reminder:** since OW-3 lands before this, OW-5's own verify runs under OW-3's *new* lens-pass
verify shape — see this change's `notes.md` for the verify-semantics note.

**Known follow-on (do NOT do now, just be aware):** **OW-15** amends the capability this change
ships (meta-hardening deltas — liveness visibility, chartered close-out coverage-gap review,
scope-seeding checklist). OW-15 applies strictly AFTER this change lands; it is **out of scope for
this batch** — full detail in
`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` if a later session picks it
up.

### 4. OW-6 — `composition-audit-cadence` (apply fourth/last)
**Dir:** `openspec/changes/composition-audit-cadence/` — proposal, design, 3 spec deltas (new
`composition-audit` capability + `outstanding-work-view` + `knowledge-lint` deltas), tasks — every
review round PASS with zero 🔴 on round 1, `openspec validate --strict` clean, cross-change
collision check vs OW-2/OW-5 deltas explicitly confirmed clean.

**Scope:** (1) a deterministic count-based due-signal (archived-changes-since-anchor ≥10 OR
commits ≥100) in the `outstanding` fact + `inventory` sibling anchor; (2) an operator-invoked
`composition-audit` skill (one-shot `checks.py --report --include jscpd/vulture/radon` + baseline
delta + bounded top-K=5 judgment pass) emitting `COMPOSITION: CLEAN|FINDINGS-ROUTED|ESCALATE`;
(3) close-out routes into OW-2's ratchet and lays a `audit/<date>-composition` anchor. Read
`design.md`/`tasks.md` for exact anchors/formats — all pinned and reviewer-verified.

**Verify note:** if the batch order holds, this change's verify runs under OW-3's new stack with
lens = test-quality (see this change's `notes.md`).

## Process reminders (standard, not batch-specific)

- Tests green before any commit; you (the orchestrator) commit in small reviewed checkpoints —
  the apply-executor never commits.
- Write each change's own `tasks.md`/`notes.md`/`review-log.md` continuously as you go (change-local
  scratch, cheap). Do **NOT** touch `knowledge/STATUS.md` / `knowledge/decisions/INDEX.md` /
  `knowledge/questions/INDEX.md` mid-batch — those are reconciled **once per change, at archive**,
  by the delegated archive-executor (deepseek-v4-pro, Sonnet fallback), then you review and commit.
- Archive each change before starting the next (don't batch all four applies then all four
  archives) — this keeps `knowledge/STATUS.md`'s ≤3-entry cap meaningful and each archive's
  reconciliation cheap (fresh context seeded from that change dir only).
- After OW-2 archives, `knowledge/decisions/INDEX.md` should gain a ratchet-related entry (and any
  later change that references "the ratchet" will mean this one).

## What's next after this batch (do not start without a fresh confirmation)

Per `OUTSTANDING-WORK.md`'s Disposition section, once this batch is archived: OW-9 → OW-14 → OW-1
→ OW-4 → OW-7 → OW-10 → OW-11 → OW-8 → OW-13 → OW-12 (wave-2 workflow-efficiency items, all
Opus-tier, none yet proposed — each needs its own tier+plan confirmation). OW-15 and OW-16 slot in
independently. None of that is in scope for *this* handoff — flag it to the operator when this
batch is done rather than auto-continuing.

## Full source-of-truth if anything here is unclear

`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` sections "OW-2" through
"OW-6" (lines ~26-168) have the complete original scoping, evidence, and park-verdict reasoning
this handoff distilled from. Read it if you need more than what's inlined above.
