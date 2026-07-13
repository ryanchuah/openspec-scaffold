# HANDOFF — resume the frozen batch at OW-5 (correctness-audit-skill)

**Written 2026-07-13, after OW-3 (`verify-stack-redirect`) shipped and archived.** This is the
sanctioned ephemeral mid-session handoff (`knowledge/HANDOFF.md`, per `knowledge/decisions/INDEX.md`
`knowledge-handoff-file`) — **absorb it, do the next chunk below, then rewrite it for the chunk
after (or delete it when the batch is done).** Its normal state is absent.

The operator granted autonomy for this batch and set a **working pattern**: do **one change per
session** (apply → verify → archive), **delegate the archive to a Sonnet `archive-executor`
subagent** (skip the deepseek-first ladder — operator's explicit choice), then **STOP after the
archive and rewrite this handoff for the next chunk**. Follow that pattern. (The operator has been
present each session to reconfirm; present readiness and proceed under this recorded grant.)

## What you're doing

Applying, verifying, and archiving the **two remaining already-frozen OpenSpec changes**, in this
**hard order**: **OW-5 → OW-6**. Both are propose-complete (proposal/design/tasks + spec deltas
written, pro-reviewed to zero 🔴, `openspec validate --strict` clean at freeze, frozen). **Nothing
needs (re-)designing.** Your job is apply → verify → archive per the standard lifecycle skills
(`openspec-apply-change`, `openspec-verify-change`, `openspec-archive-change`).

**Orchestrator: Opus (you), not Fable.** The design judgment is frozen; apply is delegated to
deepseek-flash; verifying a well-specified frozen change is within your capability.

**Standard escalation caveat (both):** implementation bugs found at verify are normal defect-path
work — diagnose, scope, re-delegate the fix, continue. A **DESIGN-level** defect (a frozen contract
doesn't fit reality, an interface disagrees with the codebase, a census/stopping-rule/lens contract
is wrong) → **STOP and escalate to the operator** rather than redesigning mid-verify.

## The two changes

### 1. OW-5 — `correctness-audit-skill` (apply NEXT)
**Dir:** `openspec/changes/correctness-audit-skill/` — proposal, design, 2 spec deltas (new
`correctness-audit` capability + a `knowledge-lint` dossier-lint delta), tasks. 2 pro-review
rounds, zero 🔴 outstanding, `openspec validate --strict` clean at freeze. **COMPLEX.**

**Scope:** standardizes the audit PROTOCOL (single charter `format: correctness-audit/v1`,
census-as-stopping-rule, FINDINGS contract with a `Prior:` dedup field + `Class:` slugs shared with
OW-2's ratchet, refuter-overrule graduation, marker-gated dossier lint, ratchet-routed close-out).
Severity taxonomy and wave decomposition stay per-repo. **Read `design.md` before delegating apply.**

**Verify note (IMPORTANT — the new stack is now live):** OW-3 shipped, so OW-5 verifies under
OW-3's **new** shape. OW-5 is **COMPLEX** → the verify chain is **self-review → pro behavioral pass
→ flash LENS pass**. Select the lens and record the selection + one-line rationale in
`review-log.md` (the verify skill's "Lens pass (COMPLEX)" subsection has the two canonical prompts).
OW-5 ships an audit skill + `knowledge_lint` dossier-lint check with new tests → the **test-quality /
adversarial-oracle lens** (the default) is almost certainly the right pick (data-scale lens is for
data-path-dominant changes; OW-5 is not one) — but judge from the actual diff.

**Known follow-on (do NOT do now):** OW-15 amends the capability OW-5 ships and applies strictly
AFTER it — out of scope for this batch (detail in the roadmap OW-15 entry +
`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`).

### 2. OW-6 — `composition-audit-cadence` (apply last)
**Dir:** `openspec/changes/composition-audit-cadence/` — proposal, design, 3 spec deltas (new
`composition-audit` capability + `outstanding-work-view` + `knowledge-lint` deltas), tasks. Every
round PASS zero 🔴, `openspec validate --strict` clean, cross-change collision check vs OW-2/OW-5
deltas confirmed clean. **COMPLEX.**

**Scope:** (1) a deterministic count-based due-signal (archived-changes-since-anchor ≥10 OR commits
≥100) in the `outstanding` fact + `inventory` sibling anchor; (2) an operator-invoked
`composition-audit` skill (one-shot `checks.py --report --include jscpd/vulture/radon` + baseline
delta + bounded top-K=5 judgment pass) emitting `COMPOSITION: CLEAN|FINDINGS-ROUTED|ESCALATE`;
(3) close-out routes into OW-2's ratchet and lays a `audit/<date>-composition` anchor. Read
`design.md`/`tasks.md` for exact anchors/formats. OW-6's ESCALATE path cites the correctness-audit
skill OW-5 ships — that's why OW-5 lands first. **Verify:** COMPLEX → same new self→pro→lens shape;
test-quality lens is the likely pick.

## Lessons carried forward — do not re-derive

These are the concrete gotchas from the OW-2 and OW-3 sessions. The OW-2 lessons (#1/#3/#5 below)
are now **guarded in the scaffold** by `lifecycle-skill-hardening`
(`openspec/changes/archive/2026-07-13-lifecycle-skill-hardening/`); kept for context and the one
place manual action still matters.

1. **`openspec validate` needs `--type change` for these change names.** The change name collides
   with a promoted **spec** name (e.g. `verify-multimodel-gate`), so bare
   `openspec validate <change> --strict` resolves against specs and errors "Unknown item". Use
   **`openspec validate <change> --type change --strict`**. Run it before delegating each apply —
   these changes were frozen before the validate-at-freeze gate existed. (OW-5/OW-6 validated clean
   at freeze, but re-confirm.)

2. **`openspec validate --strict` parses a requirement's `text` as ONLY its first physical line.**
   A SHALL/MUST wrapped onto line 2 fails "must contain SHALL or MUST". NOW GUARDED at propose
   freeze; re-run `--type change --strict` anyway before each apply. (Enforced by validate → NOT a
   ratchet entry.)

3. **Delegation shapes that ran cleanly this batch (reuse verbatim):**
   - **apply:** `timeout -k 30 600 opencode run --dir <repoRoot> --agent apply-executor --model
     deepseek/deepseek-v4-flash --format json "<brief>" > /tmp/apply-out.jsonl 2>/tmp/apply-err.log
     < /dev/null; echo "EXIT=$?" > /tmp/apply-out.exit` (background, EXIT-sentinel). For a MEDIUM
     change with no proposal.md/design.md, point the brief at `notes.md` + the spec deltas +
     `explore-brief.md`; OW-5/OW-6 are COMPLEX and DO have proposal.md + design.md, so the standard
     brief applies.
   - **verify pro pass:** one `opencode run --agent openspec-verifier --model deepseek/deepseek-v4-pro`,
     budget `-k 15 780`, read-only, background + EXIT-sentinel. **COMPLEX adds a flash LENS pass**
     (`--model deepseek/deepseek-v4-flash`, the selected lens prompt, diff-scoped — no full-suite
     rerun). Harness contract: `.claude/skills/_shared/delegation-harness.md`. Both pass prompts are
     now inlined in the verify SKILL (no more "design D5" pointer — OW-3 removed it).
   - **archive:** Sonnet `archive-executor` subagent (`Agent` tool, `subagent_type:
     "archive-executor"`), per operator's choice. Give it a thorough brief (paths, sync=yes/no, the
     three docs, the notes.md field-5 items, ≤3-cap instruction, flag-only wider sweep). It does NOT
     commit and does NOT touch HANDOFF.md — you rewrite the handoff, you commit.

4. **Extract the completion report, don't trust raw grep.** Confirm success from
   `grep '"type":"text"' /tmp/<x>-out.jsonl | tail -1 | jq -r '.part.text'` + `tasks.md` checkboxes +
   `git diff`, not a raw-stream grep (the raw jsonl contains the executor's tool-reads of skill
   headings and false-positives — e.g. `### NON-CONVERGENCE BLOCKER`). NOW GUARDED in the apply
   skill.

5. **The apply-executor can mangle markdown list indentation.** When apply edits a `.claude/skills/*.md`
   or `.opencode/agents/*.md` file, eyeball list nesting in `git diff` (3-space vs 4-space drift) —
   no test catches it. (OW-3 apply was clean on this, but stay alert for OW-5/OW-6's skill files.)

6. **After the archive `git mv`, repoint/rewrite any doc citing the moved dir before committing** —
   `knowledge_lint`'s `broken-prose-path-citation` runs in the live-tree pytest gate and the
   commit-test-gate will BLOCK the archive commit. This HANDOFF.md is the usual culprit; rewriting
   it for the next chunk (as now) clears it. NOW GUARDED (archive skill Step 6 runs knowledge_lint),
   but confirm `bash scripts/check.sh` is green before the archive commit.

7. **NEW this session (OW-3) — touch-surface research can omit human-facing docs.** OW-3's
   edit-site inventory scanned skills/agents/AGENTS.md/specs but **missed root `README.md`**, which
   duplicates agent-facing role/chain descriptions in prose; the pro verifier caught it stale at
   verify and the primary reconciled it directly (README is NOT scaffold-managed → no downstream
   sweep). Recorded as a **waiver** in `knowledge/ratchet-log.md` (`touch-surface-omits-readme`,
   review-by 2026-07-31). **For OW-5/OW-6:** if the change touches any role/chain/skill-name
   description, grep root `README.md` for the same terms and reconcile it in the same change. Root
   README is a **primary-direct quick doc edit** (not implementation code → not re-delegated).

8. **Ratchet self-application (archive Step 6, primary's job — the executor can't judge
   generalizability).** Run the 3-question triage over each change's found-and-fixed defects
   (real? → generalizable class? → detectable/test-freezable?). One-off slips are Q2=no → no entry.
   Preference check > frozen test > waiver. Add a `knowledge/ratchet-log.md` line only for a
   genuinely generalizable class lacking existing enforcement.

9. **Simplicity gate on frozen spec-driven changes:** do NOT run an auto-fixing `simplify`/`/code-review`
   skill on frozen-spec-driven skill prose mid-verify (regression risk; it targets code, not the
   frozen markdown). Self-review the diff against the gate's checklist (duplication / single-use
   abstraction / dead code / over-parameterization), fix only zero-risk one-liners inline, park the
   rest. OW-5/OW-6 ship real Python (checks, skill scaffolding) so the simplicity gate has actual
   code surface there — run it properly on the code, judiciously on the prose.

## Process reminders (standard)

- Tests green before any commit; you (orchestrator) commit in small reviewed checkpoints — executors
  never commit. Apply did not auto-commit this batch, so the pre-archive checkpoint commit (archive
  Step 5.0) doubles as the implementation commit (`git commit -am`, NOT `-A` — concurrent propose
  work is untracked and must be excluded). Commit-message convention: repo style
  `<Verb> <thing> (<id>): <essence>` + the `Co-Authored-By` / `Claude-Session` trailers (see recent
  `git log`).
- Write each change's own `tasks.md`/`notes.md`/`review-log.md` continuously (change-local scratch).
  Do NOT touch `knowledge/STATUS.md` / `knowledge/decisions/INDEX.md` / `knowledge/questions/INDEX.md`
  mid-work — reconciled once per change at archive by the delegated Sonnet archive-executor, then you
  review + commit.
- Archive each change before starting the next (keeps the STATUS ≤3-cap meaningful and each
  reconciliation cheap). Downstream propagation of all shipped scaffold changes is **operator-gated
  and deferred** — do not sync without a fresh authorization.

## What's after this batch (do not start without fresh confirmation)

Once OW-5 → OW-6 are archived, the frozen batch is DONE. Per
`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` Disposition: next is the
wave-2 backlog (OW-9 → OW-14 → OW-1 → OW-4 → OW-7 → OW-10 → OW-11 → OW-8 → OW-13 → OW-12, all
Opus-tier, **none proposed** — each needs its own tier+plan confirmation). OW-15 slots in after OW-5
(amends OW-5's capability); OW-16 is independent. Flag completion to the operator rather than
auto-continuing.

## Full source-of-truth if anything here is unclear

`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` sections OW-5, OW-6 (and
OW-15) have the complete original scoping/evidence/park-verdict reasoning. OW-3's shipped record
(the reference for the new verify stack): `openspec/changes/archive/2026-07-13-verify-stack-redirect/`.
OW-2's ratchet (the close-out routing OW-5/OW-6 depend on):
`openspec/changes/archive/2026-07-13-lesson-check-ratchet/` + `knowledge/ratchet-log.md`.
