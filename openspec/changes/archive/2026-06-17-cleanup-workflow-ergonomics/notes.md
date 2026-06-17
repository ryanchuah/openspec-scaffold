# W5 — cleanup-workflow-ergonomics · notes

## Tier & process
- **MEDIUM** → propose emits `tasks.md` only; this `notes.md` carries the
  acceptance criteria; one deepseek-v4-pro review before freeze; phase-gated
  (do **not** auto-advance to apply). Per AGENTS.md `## Change tiers`.
  (The audit suggested SMALL→MEDIUM; operator set MEDIUM for this propose.)
- **NOT manifest-changing.** Every touched file is already shared/managed:
  the apply + verify + sync-specs skills, two promoted specs, AGENTS.md, and a
  new `docs/test/` smoke procedure (docs/test is not a synced-content path).
  Per the consolidation plan W5 is "before W6 (preferred)" — a snapshot-cleanliness
  preference, **not** a W6 hard prereq.
- **Scope = the four cleanup findings B1 / D-iii / E4 / E5** — the residue the
  audit explicitly parked as "cleanup" (`workflow-audit-2026-06-16.md` §"Suggested
  priority order": "8. The rest (B3/C2/C3/C4/D-iii/E3/E4/E5) as cleanup"). B3/C2/C3/C4
  went to W2; E3 (security gate) went to W4; what remains for W5 is B1, D-iii, E4, E5.

## Provenance (every claim re-confirmed against disk 2026-06-17)
- Findings: `ai-docs/workflow-audit-2026-06-16.md` §B1, §D-iii, §E4, §E5.
- Map: `ai-docs/consolidation-plan-2026-06-16.md` — work-item table row **W5**
  ("CLEANUP — B1 happy-path · D-iii header · E4 rollback · E5 smoke") and ledger
  rows B1→W5, D-iii→W5, E4→W5, E5→W0/W5.
- E5 was a **W0 carry-forward**: the commit-gate hook smoke (W0) landed, but the
  functional "does opencode enumerate the openspec skills" check was deferred to a
  next OpenCode-capable session. Recorded in `ai-docs/decisions.md` (audit-E5 line)
  and `ai-docs/open-questions.md` (W0 resolved entry, "E5 → W5 / next OpenCode session").
- Prereqs cleared: W0 hook smoke RESOLVED (exit-2 blocks, `$CLAUDE_PROJECT_DIR`
  expands). W1 (sync mechanism) + W2 (harness dedup) SHIPPED — so B1's two surfaces
  are in their post-W2 shape (harness prose already extracted to
  `ai-docs/delegation-harness.md`; what remains buried is the *orchestration* happy
  path, not the harness contract).

## Disk state confirmed before proposing
- **B1** — apply Step 6 (`.claude/skills/openspec-apply-change/SKILL.md:84–182`):
  the happy path (deepseek runs → all tasks `[x]` → proceed to Step 7) is still
  interleaved with the assert-ran / EXIT-sentinel / 4-rung failure-ladder prose.
  verify MANDATORY blockquote (`.claude/skills/openspec-verify-change/SKILL.md:14–34`):
  a ~20-line block where the 5 self-review steps are tangled with their don'ts.
- **D-iii** — `openspec/specs/verify-multimodel-gate/spec.md:1` and
  `openspec/specs/scaffold-sync-mechanism/spec.md:1` each open with a
  `# <name> Specification` H1 + blank line before `## Purpose`; the other five
  specs (apply-convergence-guard, commit-test-gate, noninteractive-delegation-safety,
  reviewer-budget, tier-confirmation-gate) start directly at `## Purpose`. The
  H1-less form is the de-facto canon (5 of 7) and validates today, so normalize
  toward it. Promotion path that should enforce it: `openspec-sync-specs/SKILL.md:77–80`
  (step 4.d "Create new main spec").
- **E4** — lifecycle in AGENTS.md ends at archive; `## State, write discipline,
  and the archive-as-handoff rule` (`:149`) and `## OpenSpec workflow` (`:103`) are
  the natural homes. No "shipped change was later found wrong" branch exists anywhere.
- **E5** — `opencode` is on PATH at **1.17.7** (`/home/pang/.opencode/bin/opencode`);
  cross-load rests on `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS` unset (`decisions.md:24`).
  Existing smoke home `docs/test/commit-gate-smoke/README.md` is the pattern to mirror.

## Execution sequencing — overlap with W4 (concurrent propose)
W3 (`fix-convergence-guard`) and W4 are being proposed concurrently. W5 has **no
file overlap with W3** (W3: `_convergence.py`, `test_convergence.py`, `test-gate.sh`,
`apply-convergence-guard/spec.md`, apply-executor *agents*). W5 **does** overlap W4
on shared files — these must be **serialized at apply, not applied simultaneously**:
- `openspec-verify-change/SKILL.md` — W5 B1 (happy-path restructure) vs W4 E1
  (simplify/code-review gate) + B2 (tier-scale the multi-model passes).
- `AGENTS.md` — W5 E4 (rollback branch, in the lifecycle/state sections) vs W4 D-ii
  (SMALL-tier gate semantics, in `## Change tiers`). Different sections, same file.
- `openspec/specs/verify-multimodel-gate/spec.md` — W5 D-iii (drop H1) vs a possible
  W4 B2 spec delta (tier-scaling requirement). Different lines; re-read before edit.
**Mitigation:** whichever of W4/W5 applies second re-reads these files from disk
before editing (no stale line numbers), and the orchestrator runs `openspec validate
--strict` after each. The recommended apply order is W3 → W4 → W5 (W5 is the lightest
and most isolated). This is a preference, not a hard gate — none of W5 depends on W4's
*output*.

## Acceptance criteria (verify against these before READY)
1. **B1 — apply & verify lead with the happy path.** apply Step 6 and the verify
   MANDATORY block each open with a ≤3-line happy-path statement, with the failure /
   don't-do-this material moved into a clearly separated "Failure modes" (or
   equivalent) subsection below it. **No instruction is deleted or weakened** — this
   is a *reordering + sectioning* edit only; every existing caveat (assert-ran,
   EXIT-sentinel, concurrent-writer warning, fix-redelegation, multi-model passes)
   survives verbatim in its new subsection. Diff-review confirms net-semantic-zero.
2. **D-iii — spec headers normalized.** `verify-multimodel-gate/spec.md` and
   `scaffold-sync-mechanism/spec.md` start at `## Purpose` (H1 title + its trailing
   blank removed); all 7 specs now share one header shape. `openspec validate
   --strict` passes for both. The `openspec-sync-specs` skill step 4.d states the
   convention ("promoted specs start at `## Purpose`; do not add a `# <name>
   Specification` H1") so future promotions don't reintroduce it.
3. **E4 — rollback branch documented.** AGENTS.md gains a short, explicit
   "a shipped/archived change was later found wrong" lifecycle branch (the canonical
   move: `git revert` the change's commit + open a new corrective OpenSpec change that
   references the reverted one; do **not** mutate the archived change). One concise
   paragraph, placed in the lifecycle/state section — not a new subsystem.
4. **E5 — skill-enumeration smoke exists and passes.** A repeatable procedure under
   `docs/test/` (mirroring `commit-gate-smoke/README.md`) documents how to confirm
   `opencode` (≥1.16) still enumerates the `.claude/skills/openspec-*` skills, and
   the live functional check has been run once against opencode 1.17.7 with the
   result recorded in `ai-docs/decisions.md` (closing the audit-E5 carry-forward) and
   the open-questions entry cleared. If the live run cannot be done in the apply
   session, the procedure still ships and the live run is logged as the single
   remaining E5 action — but it is runnable here (opencode 1.17.7 is on PATH).
5. **No regression to the 4 already-shipped changes' guarantees**; `openspec validate
   --strict` clean for the whole change; scaffold has no runnable test suite, so
   verification leans on `--strict` + diff review + the E5 live smoke.

## Non-goals (explicit)
- Not touching `_convergence.py` / `test-gate.sh` (W3) or the W4 gates (E1/B2/D-i/D-ii/E3).
- Not the one-time propagation (W6) — W5 only cleans scaffold-managed files pre-snapshot.
- Not re-opening settled scaffold-sync micro-decisions (consolidation-plan §7 guard).
- B1 is **not** a rewrite of the failure logic — reorder only; the failure ladders,
  EXIT-sentinel contract, and multi-model passes keep their current behavior.

## Verify checkpoint (apply-executor handoff)

### B1 net-semantic-zero grep result

All pre-edit phrases confirmed present after restructuring:

**Apply skill** (`.claude/skills/openspec-apply-change/SKILL.md`):
- `Falling back to default agent` — 1 match (step 2 in Failure modes)
- `EXIT=` — 1 match (invocation bash block)
- `NON-CONVERGENCE BLOCKER` — 6 matches (step 3, step 4 in Failure modes)
- `concurrent writers` — 1 match (EXIT-sentinel caveat in Failure modes)
- `Mandatory disclosure` — 1 match (failure ladder step 4 in Failure modes)

**Verify skill** (`.claude/skills/openspec-verify-change/SKILL.md`):
- `re-delegate` — 4 matches (happy path step 5; failure modes "do not hand-fix"; gate semantics fix path; notes.md field 3)
- `independent verification` — 1 match (multi-model passes heading, unchanged section)
- `verifier pass` — 3 matches (multi-model passes section, unchanged)

Multi-model passes section (`:36+`) was confirmed unchanged — all three phrases present in their original locations.

### E5 status

- **Task 4.1 (documentation):** DONE. `docs/test/skill-enumeration-smoke/README.md` created, mirroring `commit-gate-smoke/README.md`.
- **Tasks 4.2 and 4.3 (live smoke run + evidence recording):** DEFERRED to orchestrator. The apply-executor created the procedure but did NOT run the live `opencode debug skill` smoke or record evidence in `ai-docs/decisions.md` / `ai-docs/open-questions.md`. The README contains the placeholder `RECORDED EVIDENCE: <to be filled by orchestrator live run>`.
- Task 4.4 (alternative path) does not apply — the live run is runnable, just deliberately deferred to the orchestrator's verify phase.

### Files awaiting orchestrator action at verify
1. Run `opencode debug skill` smoke per `docs/test/skill-enumeration-smoke/README.md`
2. Fill `RECORDED EVIDENCE` in the README with the exact command + observed output
3. Record the E5 resolution in `ai-docs/decisions.md` (close audit-E5 carry-forward)
4. Annotate/clear the E5 entry in `ai-docs/open-questions.md`
5. Confirm the verify skill multi-model passes section is still structurally unchanged

---

## Verify checkpoint (orchestrator, 2026-06-17)

**1. Verdict:** READY FOR ARCHIVE. Self-review + one independent `deepseek-v4-flash`
verifier pass both returned READY, 0 defects. (Pro verifier pass skipped per the
operator's established precedent for scaffold docs-only changes — W1/W2.)

**2. Live output eyeballed:** the E5 skill-enumeration smoke was RUN against opencode
1.17.7 — `opencode debug skill` enumerated all 7 `openspec-*` skills, every `"location"`
resolving to `.claude/skills/openspec-*/SKILL.md`, with `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS`
`<unset>`. Evidence recorded in `docs/test/skill-enumeration-smoke/README.md`. The B1
restructures were eyeballed by set-difference diff (removed-vs-added content) confirming
the only genuine changes are relocations + the happy-path opener/headers — net-semantic-zero.

**3. Defect found and how fixed (and who):** during self-review the orchestrator caught
two formatting regressions the first flash apply introduced — (a) the E4 insertion
de-indented the preceding bullet's two continuation lines in AGENTS.md, popping them out
of the list; (b) the sync-specs `d.` sub-bullets shifted 6→7-space indent. Both were
trivial whitespace fixes applied inline by the orchestrator (doc formatting, not impl
logic). NOTE: this entire change was subsequently RE-APPLIED by the orchestrator by hand
(see field 4) after a concurrent session wiped the working tree, so those fixes are moot —
the re-application is clean from the start. No flash/Sonnet fix-redelegation was needed.

**4. As-built delta (process, not artifact):** the first flash apply-executor completed
W5 correctly, but the concurrent **W4 (`lifecycle-gates`) apply reset the shared working
tree to HEAD**, wiping all of W5's uncommitted edits (and the `docs/test/` dir). W4 then
committed + archived (`fed9432`, `a62f223`). W5 was therefore RE-APPLIED by the orchestrator
directly on top of W4's committed base — appropriate since W5 is entirely doc/markdown edits
(AGENTS.md: "quick doc edits done by the primary directly"). B1's verify-skill restructure
targets the MANDATORY block (lines 14-34), which W4 did not touch (W4's E1/B2/E3 additions
live at L38 and L107+), so there was no real content conflict — only the wipe. The E5 README
was also rewritten to fix a real procedure bug: `opencode debug skill | grep` races the
~120 KB stream and returns a 3-4 skill subset; the README now mandates capture-to-file first.

**5. Forward-looking items for project docs (open-questions / follow-ons):**
- **Concurrent agents share one working tree → mutual clobbering.** Two sessions applying
  to `openspec-scaffold` simultaneously reset/overwrote each other's uncommitted work
  (W4's apply wiped W5; W5's first apply collided with W4). This cost a full flash apply
  round. **Recommendation to fold into `ai-docs/open-questions.md`:** when running
  concurrent apply agents, give each its own `git worktree`, or serialize applies. This is
  the concrete recurrence of the hazard already noted for W3. (Process item — no artifact
  records it.)
- **`/tmp/apply-out.*` path collision:** both W4's and W5's `opencode run` apply wrappers
  wrote the same `/tmp/apply-out.jsonl`/`.exit` paths — another reason concurrent applies
  interfere. Consider per-change tmp paths in the apply skill's harness if concurrent
  applies become normal. (Minor; folds with the worktree item.)
- No new tuning knobs/thresholds were introduced by W5 (pure cleanup); nothing else to carry.

**Still owned by archive:** `STATUS.md` (update to reflect W5 shipped), and the change-dir
move to `openspec/changes/archive/2026-06-17-cleanup-workflow-ergonomics/`. NOTE: `ai-docs/
decisions.md` (3 W5 entries: B1, E4, E5) and `ai-docs/open-questions.md` (E5 resolved
annotation) were ALREADY reconciled inline during the hand re-application — a deliberate
deviation from the defer-to-archive rule, justified because the E5 evidence had to be
captured live and the whole change was re-done by the primary in-context. No spec promotion
is needed (D-iii edits existing promoted specs directly; the change has no delta specs).
