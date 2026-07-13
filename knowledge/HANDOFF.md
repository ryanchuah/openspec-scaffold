# HANDOFF — resume the frozen batch at OW-6 (composition-audit-cadence)

**Written 2026-07-13, after OW-5 (`correctness-audit-skill`) shipped and archived.** This is the
sanctioned ephemeral mid-session handoff (`knowledge/HANDOFF.md`, per `knowledge/decisions/INDEX.md`
`knowledge-handoff-file`) — **absorb it, do the one change below, then rewrite it (or delete it
when the batch is done).** Its normal state is absent.

The operator granted autonomy for this batch and set a **working pattern**: do **one change per
session** (apply → verify → archive), **delegate the archive to a Sonnet `archive-executor`
subagent** (skip the deepseek-first ladder — operator's explicit choice), then **STOP after the
archive and rewrite this handoff** (or delete it — OW-6 is the LAST frozen item). Follow that
pattern. Present readiness and proceed under this recorded grant.

## What you're doing

Applying, verifying, and archiving the **last remaining already-frozen OpenSpec change**:
**OW-6 (`composition-audit-cadence`)**. It is propose-complete (proposal/design/tasks + 3 spec
deltas written, pro-reviewed to zero 🔴, `openspec validate --strict` clean at freeze, frozen).
**Nothing needs (re-)designing.** Your job is apply → verify → archive per the standard lifecycle
skills (`openspec-apply-change`, `openspec-verify-change`, `openspec-archive-change`).

**Orchestrator: Opus (you), not Fable.** The design judgment is frozen; apply is delegated to
deepseek-flash; verifying a well-specified frozen change is within your capability.

**Standard escalation caveat:** implementation bugs found at verify are normal defect-path work —
diagnose, scope, re-delegate the fix (or fix a truly-trivial one-liner inline), continue. A
**DESIGN-level** defect (a frozen contract doesn't fit reality — e.g. the count-based due-signal
threshold or the `COMPOSITION:` verdict contract is wrong, or the ratchet/anchor interface
disagrees with the codebase) → **STOP and escalate to the operator** rather than redesigning
mid-verify.

## OW-6 — `composition-audit-cadence`

**Dir:** `openspec/changes/composition-audit-cadence/` — proposal, design, **3 spec deltas**
(`composition-audit` new capability + `outstanding-work-view` + `knowledge-lint` deltas), tasks.
Every propose round PASS zero 🔴, `openspec validate --strict` clean, cross-change collision check
vs OW-2/OW-5 deltas confirmed clean at freeze. **COMPLEX.** **Read `design.md`/`tasks.md` before
delegating apply.**

**Scope:** (1) a deterministic count-based due-signal (archived-changes-since-anchor ≥10 OR commits
≥100) in the `outstanding` fact + an `inventory` sibling anchor; (2) an operator-invoked
`composition-audit` skill (one-shot `checks.py --report --include jscpd/vulture/radon` + baseline
delta + bounded top-K=5 judgment pass) emitting `COMPOSITION: CLEAN|FINDINGS-ROUTED|ESCALATE`;
(3) close-out routes into OW-2's ratchet and lays a `audit/<date>-composition` anchor. **OW-6's
ESCALATE path cites the `correctness-audit` skill OW-5 shipped — that dependency is now satisfied
(OW-5 is SHIPPED + archived + specs promoted).**

**Verify:** COMPLEX → **self-review → pro behavioral pass → flash LENS pass**. Select the lens and
record the selection + one-line rationale in `review-log.md`. OW-6 ships real Python (checks
anchors, `outstanding.py`/`inventory` due-signal, skill scaffolding) + new tests → the
**test-quality / adversarial-oracle lens** (the default) is almost certainly right (data-scale lens
is for data-path-dominant changes; OW-6 is not one). Judge from the actual diff.

## Lessons carried forward — do not re-derive

Concrete gotchas. The OW-2 lessons (validate/SHALL-detection) are guarded in the scaffold now; the
OW-5-session lessons below are the freshest.

1. **`openspec validate` needs `--type change` for these names.** `composition-audit-cadence`
   collides with the promoted **spec** name `composition-audit`, so bare
   `openspec validate composition-audit-cadence --strict` resolves against specs and errors. Use
   **`openspec validate composition-audit-cadence --type change --strict`**. Re-run it before
   delegating apply (OW-6 validated clean at freeze, but re-confirm). Spec-promotion validation at
   archive likewise needs `--type spec` (`openspec validate <cap> --type spec --strict`).

2. **Delegation shapes that ran cleanly this batch (reuse verbatim):**
   - **apply:** `timeout -k 30 600 opencode run --dir <repoRoot> --agent apply-executor --model
     deepseek/deepseek-v4-flash --format json "<brief>" > /tmp/apply-out.jsonl 2>/tmp/apply-err.log
     < /dev/null; echo "EXIT=$?" > /tmp/apply-out.exit` (background, EXIT-sentinel). OW-6 is COMPLEX
     with proposal.md + design.md → the standard brief applies. Tell the executor to source behavior
     from the frozen spec deltas + design decisions, preserve markdown list indentation on any
     skill file, and run `bash scripts/check.sh` at the gate task.
   - **verify pro pass:** one `opencode run --agent openspec-verifier --model deepseek/deepseek-v4-pro`,
     budget `-k 15 780`, read-only, background + EXIT-sentinel. **COMPLEX adds a flash LENS pass**
     (`--model deepseek/deepseek-v4-flash`, the selected lens prompt, diff-scoped — no full-suite
     rerun). Both pass prompts are inlined in the verify SKILL. Harness contract:
     `.claude/skills/_shared/delegation-harness.md`.
   - **archive:** Sonnet `archive-executor` subagent (`Agent` tool, `subagent_type:
     "archive-executor"`), per operator's choice. Give it a thorough brief (paths, sync=yes, the
     three docs, the notes.md field-5 items, ≤3-cap instruction, flag-only wider sweep). It does NOT
     commit and does NOT touch HANDOFF.md — you rewrite/delete the handoff, you commit.

3. **Judge every delegated run from disk, not the exit code or a raw grep.** Confirm success from
   the extracted completion report (`grep '"type":"text"' /tmp/<x>-out.jsonl | tail -1 | jq -r
   '.part.text'`) + `tasks.md` checkboxes + `git diff`. This batch a background fix-run was **KILLED
   with zero progress** (no exit sentinel written, no edits on disk) — for a TRULY trivial one-liner
   (helper substitution, collapsing an `or`) it was faster and rule-permitted to apply it inline
   than re-delegate again. **Caveat: after any inline Python edit, run `ruff format <file>` and
   re-check** — collapsing multi-line expressions can trigger a format reflow that reddens
   `check.sh`.

4. **Eyeball-real-output for a lint/anchor/skill-shipping change (verify step 6):** build a REAL
   artifact from the skill's LITERAL inlined templates/anchors and run the tool against it (a clean
   variant AND a deliberately-broken one). For OW-5 this meant building a dossier from the SKILL's
   template blocks and running `knowledge_lint --root <tmp>` — the strongest round-trip evidence and
   the thing that catches template↔parser drift. OW-6 ships a `composition-audit` skill + `outstanding`/
   `inventory` anchors + a `COMPOSITION:` verdict format → do the equivalent: exercise the due-signal
   at the threshold boundary and the anchor/verdict formats against a real (tmp) tree.

5. **After the archive `git mv`, re-run `python3 scripts/knowledge_lint.py` and repoint EVERY doc
   citing the moved dir before committing.** The delegated archive-executor reconciles STATUS/
   decisions/questions but does NOT fix the wider docs (it flags them). This session the move broke
   citations in `knowledge/roadmap.md` and `knowledge/HANDOFF.md` to the old OW-5 dir → the
   commit-test-gate (which runs knowledge_lint in the live-tree pytest gate) would BLOCK the commit.
   Repoint roadmap/STATUS/decisions citations by hand; rewriting THIS handoff for the next chunk
   clears the HANDOFF citation. (Interpreter note: this env has `python3` but not `python` on PATH.)

6. **Ratchet self-application (archive Step 6, PRIMARY's job — the executor can't judge
   generalizability).** Run the 3-question triage (real? → generalizable class? → detectable/
   test-freezable?) over each change's found-and-fixed defects. OW-5 yielded ONE `open:since` entry:
   `skill-template-parser-roundtrip` (template↔parser drift; enforcement = an extract-template lint
   test, not yet built). **OW-6 also ships templates/anchors/parsers → watch for the same class.**
   If OW-6's verify motivates building that extract-template test, it could CLOSE the OW-5 `open:`
   entry (flip `open:since` → `test:<path>`); otherwise leave it open and age-flagged. Most other
   slips are Q2=no one-offs (no entry). Preference: check > frozen test > waiver.

7. **Spec promotion (archive, sync=yes):** OW-6 has 3 delta specs. `composition-audit` and
   `outstanding-work-view` — confirm which already exist in `openspec/specs/` (new → create;
   existing → merge the ADDED/MODIFIED requirements). `knowledge-lint` now has 12 requirements
   (OW-5 added `linter-validates-audit-dossier-format`) → OW-6's knowledge-lint delta merges on top.
   Brief the executor to promote a NEW-capability spec as `## Purpose` + `## Requirements` (NOT a
   bare `# title`) — `openspec validate --type spec` hard-requires a Purpose section (learned this
   session).

8. **The apply-executor can mangle markdown list indentation** — when apply edits a
   `.claude/skills/*.md` file, eyeball list nesting in `git diff` (3-space vs 4-space drift); no test
   catches it. OW-6 ships a `composition-audit` skill file → stay alert.

9. **Simplicity gate on frozen spec-driven changes:** do NOT run an auto-fixing `simplify` on frozen
   skill prose mid-verify. Self-review the prose against the gate checklist; run `/code-review`
   (read-only) or focused finder subagents on the CODE (OW-6 ships real Python → the gate has real
   surface there). Fold confirmed simplification/reuse/dead-code findings via the defect path; park
   larger restructures. OW-5's gate found 3 nits — folded 2 one-liners, parked 1 (single-pass merge)
   to `ratchet-lint-cleanup`.

## Process reminders (standard)

- Tests green before any commit; you (orchestrator) commit in small reviewed checkpoints — executors
  never commit. Apply did not auto-commit this batch, so the pre-archive checkpoint commit (archive
  Step 5.0) doubles as the implementation commit. The new skill file is **untracked** → `git add`
  it explicitly, then `git commit -a -F <msgfile>` (NOT `-A` — concurrent propose work must be
  excluded; and `-am -F` is a syntax error, use `-a -F`). Commit-message convention: repo style
  `<Verb> <thing> (<id>): <essence>` + the `Co-Authored-By` / `Claude-Session` trailers (see recent
  `git log`). Two commits per change: `Implement composition-audit-cadence (OW-6): …` then
  `Archive composition-audit-cadence and reconcile project docs`.
- Write each change's own `tasks.md`/`notes.md`/`review-log.md` continuously (change-local scratch).
  Do NOT touch `knowledge/STATUS.md` / `knowledge/decisions/INDEX.md` / `knowledge/questions/INDEX.md`
  mid-work — reconciled once at archive by the delegated Sonnet archive-executor, then you review +
  commit.
- Downstream propagation of all shipped scaffold changes is **operator-gated and deferred** — do not
  sync without a fresh authorization.

## What's after this change (do NOT start without fresh confirmation)

Once OW-6 is archived, **the frozen batch is DONE** — flag completion to the operator; do not
auto-continue. Per `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`
Disposition, next is the wave-2 backlog (OW-9 → OW-14 → OW-1 → OW-4 → OW-7 → OW-10 → OW-11 → OW-8 →
OW-13 → OW-12, all Opus-tier, **none proposed** — each needs its own tier+plan confirmation).
**OW-15** slots in after OW-5 (amends OW-5's capability; its gate is now clear — actionable) and
**OW-16** is independent. Delete this handoff (or rewrite it for OW-15/wave-2) once OW-6 archives.

## Full source-of-truth if anything here is unclear

`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` section OW-6 (and OW-15/OW-16)
has the complete original scoping/evidence/park-verdict reasoning. OW-5's shipped record (the
reference for the new audit-skill + dossier-lint shape, and the verify/archive walkthrough this
batch used): `openspec/changes/archive/2026-07-13-correctness-audit-skill/`. OW-3's shipped record
(the verify-stack reference): `openspec/changes/archive/2026-07-13-verify-stack-redirect/`. OW-2's
ratchet (the close-out routing OW-6 depends on):
`openspec/changes/archive/2026-07-13-lesson-check-ratchet/` + `knowledge/ratchet-log.md`.
