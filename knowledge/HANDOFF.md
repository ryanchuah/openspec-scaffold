# HANDOFF — resume the frozen batch at OW-3 (verify-stack-redirect)

**Written 2026-07-13, after OW-2 (`lesson-check-ratchet`) shipped and archived.** This is the
sanctioned ephemeral mid-session handoff (`knowledge/HANDOFF.md`, per `knowledge/decisions/INDEX.md`
`knowledge-handoff-file`) — **absorb it, do the next chunk below, then rewrite it for the chunk
after (or delete it when the batch is done).** Its normal state is absent.

The operator granted autonomy for this batch and set a **working pattern**: do **one change per
session** (apply → verify → archive), **delegate the archive to a Sonnet `archive-executor`
subagent** (skip the deepseek-first ladder — operator's explicit choice), then **STOP after the
archive and rewrite this handoff for the next chunk**. Follow that pattern.

## What you're doing

Applying, verifying, and archiving the **three remaining already-frozen OpenSpec changes**, in this
**hard order**: **OW-3 → OW-5 → OW-6**. All three are propose-complete (proposal/design/tasks + spec
deltas written, pro-reviewed to zero 🔴, frozen). **Nothing needs (re-)designing.** Your job is
apply → verify → archive per the standard lifecycle skills (`openspec-apply-change`,
`openspec-verify-change`, `openspec-archive-change`).

**Orchestrator: Opus (you), not Fable.** The design judgment is frozen; apply is delegated to
deepseek-flash; verifying a well-specified frozen change is within your capability.

**Standard escalation caveat (all three):** implementation bugs found at verify are normal
defect-path work — diagnose, scope, re-delegate the fix, continue. A **DESIGN-level** defect (a
frozen contract doesn't fit reality, an interface disagrees with the codebase, a
census/stopping-rule/lens contract is wrong) → **STOP and escalate to the operator** rather than
redesigning mid-verify.

## Why this order (dependency graph)

- **OW-3 first:** it rewrites the verify stack, so OW-5 and OW-6 should verify under OW-3's *new*
  lens-diversity shape rather than the old three-same-lens shape.
- **OW-5 before OW-6:** OW-6's ESCALATE path cites the correctness-audit skill OW-5 ships, and both
  route close-out findings into **OW-2's ratchet ledger** (now shipped — `knowledge/ratchet-log.md`).
- OW-7/9/11/14 (a separate, NOT-in-scope wave-2 backlog) edit the same skill files OW-3 rewrites —
  do not touch them until this batch is fully archived.

## The three changes

### 1. OW-3 — `verify-stack-redirect` (apply NEXT)
**Dir:** `openspec/changes/verify-stack-redirect/` — tasks.md + 2 spec deltas + notes.md acceptance
criteria, frozen, direction gate + artifact review both AGREE/PASS, zero 🔴. **MEDIUM tier** (propose
emitted only tasks.md; acceptance criteria in its `notes.md`). Read `design.md`/`tasks.md` closely —
this change governs every downstream verify from here on.

**Scope:** redirects the verify stack from breadth (three same-lens model passes) to lens diversity.
New shape: **MEDIUM** = self→pro; **COMPLEX** = self→pro→**lens pass** (a *prompt*, not a new
detector — test-quality lens by default, data-scale lens for data-path changes); **SMALL** unchanged.
Touches the verify skill + AGENTS.md roles + the delegation harness; budgets (780s / `-k 15`) are
pinned and guarded by a budget-agreement lint.

**Verify note (IMPORTANT self-reference):** OW-3 verifies **itself** under the **pre-change**
(current) semantics — **self + pro only** (see its `notes.md`), because the new lens semantics don't
exist until this change ships. Do NOT try to run the new lens pass on OW-3 itself.

### 2. OW-5 — `correctness-audit-skill` (apply after OW-3)
**Dir:** `openspec/changes/correctness-audit-skill/` — proposal, design, 2 spec deltas (new
`correctness-audit` capability + a `knowledge-lint` dossier-lint delta), tasks. 2 pro-review rounds,
zero 🔴 outstanding, `openspec validate --strict` clean at freeze. **COMPLEX.**

**Scope:** standardizes the audit PROTOCOL (single charter `format: correctness-audit/v1`,
census-as-stopping-rule, FINDINGS contract with a `Prior:` dedup field + `Class:` slugs shared with
OW-2's ratchet, refuter-overrule graduation, marker-gated dossier lint, ratchet-routed close-out).
Severity taxonomy and wave decomposition stay per-repo. Read `design.md` before delegating apply.

**Verify note:** since OW-3 lands first, OW-5 verifies under OW-3's *new* lens-pass shape (see its
`notes.md`). **Known follow-on (do NOT do now):** OW-15 amends the capability OW-5 ships and applies
strictly AFTER it — out of scope for this batch (detail in the roadmap OW-15 entry + `OUTSTANDING-WORK.md`).

### 3. OW-6 — `composition-audit-cadence` (apply last)
**Dir:** `openspec/changes/composition-audit-cadence/` — proposal, design, 3 spec deltas (new
`composition-audit` capability + `outstanding-work-view` + `knowledge-lint` deltas), tasks. Every
round PASS zero 🔴, `openspec validate --strict` clean, cross-change collision check vs OW-2/OW-5
deltas confirmed clean. **COMPLEX.**

**Scope:** (1) a deterministic count-based due-signal (archived-changes-since-anchor ≥10 OR commits
≥100) in the `outstanding` fact + `inventory` sibling anchor; (2) an operator-invoked
`composition-audit` skill (one-shot `checks.py --report --include jscpd/vulture/radon` + baseline
delta + bounded top-K=5 judgment pass) emitting `COMPOSITION: CLEAN|FINDINGS-ROUTED|ESCALATE`;
(3) close-out routes into OW-2's ratchet and lays a `audit/<date>-composition` anchor. Read
`design.md`/`tasks.md` for exact anchors/formats.

**Verify note:** runs under OW-3's new stack with lens = test-quality (see its `notes.md`).

## Lessons carried forward from the OW-2 session (so you don't re-derive / re-learn)

1. **`openspec validate --strict` parses a requirement's `text` as ONLY its first physical line.**
   If the normative SHALL/MUST is wrapped onto line 2, validate fails with "must contain SHALL or
   MUST" even though the word is present. Fix by reordering so the verb is on line 1. **Run
   `openspec validate <change> --strict` before delegating apply** — the freeze step does not
   guarantee it. (This class is already enforced by validate, so it is deliberately NOT in the
   ratchet ledger — see OW-2 archive notes triage.)

2. **Delegation flow that worked cleanly (reuse it):** apply via
   `timeout -k 30 600 opencode run --dir <repoRoot> --agent apply-executor --model
   deepseek/deepseek-v4-flash --format json "<brief>" > /tmp/apply-out.jsonl 2>/tmp/apply-err.log
   < /dev/null; echo "EXIT=$?" > /tmp/apply-out.exit` (background, EXIT-sentinel). Verify passes:
   two concurrent `opencode run --agent openspec-verifier` calls (pro then flash), budget
   `-k 15 780`, read-only. All ran with no fallback. Harness contract:
   `.claude/skills/_shared/delegation-harness.md`. Canonical verifier prompt:
   verify-multimodel-gate design D5 (`openspec/changes/archive/2026-06-16-verify-multimodel-gate/design.md`).

3. **False-positive alarm to ignore:** grepping executor output for `### NON-CONVERGENCE BLOCKER`
   can MATCH the executor echoing the apply-SKILL.md failure-mode docs. Confirm from the actual
   completion report + `tasks.md` checkboxes, not the raw grep count.

4. **The apply-executor can mangle markdown list indentation.** In OW-2 it shifted skill-file
   sub-bullets from 3→4 spaces, mis-nesting peer steps. When apply edits a `.claude/skills/*.md`
   file, eyeball the list nesting in `git diff` — no test catches skill-md indentation.

5. **After an archive `git mv`, any doc citing the moved change dir breaks `knowledge_lint`
   (`broken-prose-path-citation`, exit 1), which runs in the live-tree pytest gate → the
   commit-test-gate will BLOCK your archive commit.** In OW-2 the culprit was this HANDOFF.md
   itself. Fix all citations to the moved dir (repoint to the archive path, or rewrite this file)
   BEFORE committing the archive, then re-run `scripts/check.sh` green.

6. **Simplicity gate on frozen spec-driven code:** the 4 cleanup agents surface real dead-code
   nits, but do NOT churn frozen-spec validation mid-verify (regression risk on message-asserting
   tests; deviating from a frozen design decision). Fix only the zero-risk one-liners inline; park
   the rest. OW-2's parked cleanups → `knowledge/questions/ratchet-lint-cleanup.md`.

7. **Ratchet self-application:** OW-2 added a ratchet-triage step to the archive skill Step 6, so
   every archive from here runs the 3-question triage over the change's own found-and-fixed defects
   (real? → generalizable class? → detectable/test-freezable?). One-off implementation slips are
   Q2=no → no entry. Add a `knowledge/ratchet-log.md` line only for a genuinely generalizable class
   lacking existing enforcement.

## Process reminders (standard)

- Tests green before any commit; you (orchestrator) commit in small reviewed checkpoints — executors
  never commit. Apply didn't auto-commit in OW-2, so the pre-archive checkpoint commit (Step 5.0)
  doubled as the implementation commit (`git add` the new files + `git commit -a`).
- Write each change's own `tasks.md`/`notes.md`/`review-log.md` continuously (change-local scratch).
  Do NOT touch `knowledge/STATUS.md` / `knowledge/decisions/INDEX.md` / `knowledge/questions/INDEX.md`
  mid-work — reconciled once per change at archive by the delegated Sonnet archive-executor, then you
  review + commit.
- Archive each change before starting the next (keeps the STATUS ≤3-cap meaningful and each
  reconciliation cheap). Downstream propagation of all shipped scaffold changes is **operator-gated
  and deferred** — do not sync without a fresh authorization.

## What's after this batch (do not start without fresh confirmation)

Per `OUTSTANDING-WORK.md` Disposition: once OW-3/5/6 are archived → OW-9 → OW-14 → OW-1 → OW-4 →
OW-7 → OW-10 → OW-11 → OW-8 → OW-13 → OW-12 (wave-2, all Opus-tier, none proposed — each needs its
own tier+plan confirmation). OW-15/OW-16 slot in independently (OW-15 after OW-5). Flag this to the
operator when the batch is done rather than auto-continuing.

## Full source-of-truth if anything here is unclear

`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` sections OW-3, OW-5, OW-6 have
the complete original scoping/evidence/park-verdict reasoning. OW-2's shipped record (the reference
for "the ratchet"): `openspec/changes/archive/2026-07-13-lesson-check-ratchet/`.
