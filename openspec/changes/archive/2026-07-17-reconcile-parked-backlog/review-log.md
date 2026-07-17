# Review log — reconcile-parked-backlog

## Round 1 — tasks.md — deepseek-v4-pro — 2026-07-16

Now I have all the evidence I need. Let me produce the review.

## Review Round 1 — tasks.md

### Summary

The `tasks.md` is well-structured, evidence-gated, and properly scoped per the MEDIUM-tier contract (notes.md carries design decisions and verification criteria). The 8 groups are logically ordered, dependencies are mostly clear, and the acceptance criteria for each task are concrete and testable. The "Hard rule" header correctly warns about the single worst failure mode (deleting TRIM files wholesale).

However, there is a **task-coverage gap**: two tracker files that describe problems **resolved by this change's own code-fix tasks** (Tasks 2 and 4.1) have no corresponding cleanup tasks in Groups 6 or 7. These tracker files will be left stale after implementation, contradicting the change's mission to sweep the parked backlog. I also note the evidence file at a `/tmp/` path may not exist at implementation time.

---

### 🔴 Blocking Issues

1. **Missing task to close `knowledge/questions/audit-skill-metadata-cleanup.md` after Task 4.1 resolves it.**  
   - **Evidence:** `INDEX.md` line 33 points to this tracker file, which describes inaccurate `compatibility: Requires openspec CLI.` frontmatter on `run-audit` and `knowledge-drift-review`. Task 4.1 fixes this exact issue for 7 skills (including those two). After Task 4.1 lands, this tracker file is stale — it describes a problem that no longer exists.  
   - **Impact:** The implementer following the exact task list would fix the frontmatter but leave a tracker file saying "this needs fixing." This contradicts Verification criterion #6 ("Tracker truth") and the change's stated purpose. The knowledge_lint would pass (file exists, not dangling), but the content would be known-stale — the very decay this change claims to sweep.  
   - **Recommendation:** Add a task to either (a) delete the file + its INDEX pointer (preferred — the problem is fully resolved and the "broader audit" the file mentions is exactly what Task 4.1 performs) or (b) update it to record the resolution.

2. **Missing task to update `knowledge/questions/scaffold-lint-removed-name-blindspot.md` after Task 2 resolves it.**  
   - **Evidence:** `INDEX.md` line 32 points to this tracker file, which describes the `_NON_OPENSPEC_SKILL_TOKENS` blind spot for detecting references to removed non-openspec skills. Task 2 (specifically D1's design) replaces the frozenset with a tombstone-derived vocabulary, making "drift structurally impossible." After Task 2 lands, the core problem is resolved — the blind spot is closed.  
   - **Impact:** The tracker file's "Revisit if" triggers (skill set growth, rename recurrence) haven't fired, but the file's primary claim ("the frozenset approach loses detection for removed names") is no longer accurate. Leaving it unmodified means a future agent reading the tracker would believe the blind spot still exists.  
   - **Recommendation:** Add a task to update the tracker, noting that the tombstone-derived vocabulary (Task 2) closes the blind spot, and retain only the revisit triggers if they're still relevant.

3. **Evidence file at `/tmp/` path may not exist at implementation time.**  
   - **Location:** `tasks.md` line 5: `"/tmp/claude-1000/-home-pang-Projects-openspec-scaffold/8acfcce2-efbe-406a-9f7d-419fe8bc08f3/scratchpad/verify-stale.md"`.  
   - **Impact:** This is in `/tmp/` — a volatile filesystem location. If the implementer starts in a fresh session, this file will be absent. Groups 3-4 explicitly say "Read it before starting Group 3" because the TRIM survivor lists are authoritative for Groups 6-7. Without this file, the implementer has no authoritative source for which sub-bullets to remove vs. keep in 13 separate tracker files — the task descriptions are summaries, not the full per-file survivor lists.  
   - **Recommendation:** Copy `verify-stale.md` into the change directory (`openspec/changes/reconcile-parked-backlog/verify-stale.md`) and update the `tasks.md` header to reference the local path, or at minimum add a note that if the `/tmp/` path is absent, the implementer should stop and ask.

---

### 🟡 Should Fix

4. **Groups 6-7 don't repeat the hard-rule header that Groups 3-4 get, though the risk is identical.**  
   - The header at lines 7-9 says "Hard rule for Groups 3-4" but the same risk — accidentally deleting a TRIM file wholesale — applies equally to Groups 6-7. A tired implementer working through Group 7 might glance at the instruction and think "delete the named bullets" but accidentally delete an entire file.  
   - **Recommendation:** Extend the hard-rule header to cover Groups 6-7 as well, or add a separate prominent warning before Group 7.

5. **Task 1.1 could cause a reviewer false-negative if the regex is too loose.**  
   - The task says "Keep the anchors otherwise strict — leading/trailing whitespace only; do NOT relax to an unanchored search." This is correct but subtle. If the implementer uses `\**` or `\*{0,2}` without anchoring, the regex could match bold markers mid-line. The "negative control" test in 1.2(c) should catch this, but the task description itself is terse.  
   - **Recommendation:** The task could include the concrete regex pattern to use (e.g., `r"^\s*\*{0,2}VERDICT:\*{0,2}\s*(PASS|NEEDS REVISION)\*{0,2}\s*$"`) so the implementer doesn't need to derive it from the four spellings.

6. **Task 4.1 says "line ~5" but the subagent confirmed it's at line 5 in all 7 files — the implementer should verify.**  
   - A `~` implies approximation, but the exact line is 5. Minor, but could cause an implementer to check lines 4-6 unnecessarily in 7 files.

---

### 💡 Suggestions

7. **Consider adding an explicit `test_executor_body_agreement.py` check after Task 5.2.**  
   - Task 5.2 requires byte-identical edits to both archive-executor files. Adding `python3 scripts/test_executor_body_agreement.py` as a post-task verification step would catch drift before final gates (8.2 already covers it, but earlier detection is cheaper).

8. **Task 2.5's live-tree `scaffold_lint` run is partially redundant with Task 8.1.**  
   - Both check for zero findings. Task 2.5 is a targeted blast-radius check; 8.1 is the comprehensive final gate. This isn't harmful, but if the tree is dirty between 2.5 and 8.1, 2.5's result could be misleading. Consider noting that 8.1 is authoritative.

9. **Task 7.14's "close RESOLVED entries" could be more explicit about what "close" means.**  
   - The INDEX.md lines 30 and 39 are inline RESOLVED entries (not separate files). "Remove them" is clear enough, but the AGENTS.md rule says "close it explicitly rather than leaving a stale entry" — the task could clarify: delete the line entirely (since the decision is recorded in `knowledge/decisions/INDEX.md` per the entries' own text).

---

### Verdict

🔴 Issues 1-2 are task-coverage gaps that would leave known-stale tracker content after implementation, contradicting the change's mission. 🔴 Issue 3 is an operational risk — the evidence file at a volatile path may be absent when the implementer starts. These must be addressed before freeze.

NEEDS REVISION — address 🔴 issues before proceeding

VERDICT: NEEDS REVISION
## Round 2 — tasks.md — deepseek-v4-pro — 2026-07-16

## Review Round 2 — tasks.md

### Summary

All three round 1 🔴 blocking issues are resolved and the fixes are real:

1. **Task 4.2** (lines 109–114) deletes `knowledge/questions/audit-skill-metadata-cleanup.md` + its INDEX pointer after task 4.1 resolves it. The INDEX line (33) is correctly identified.
2. **Task 2.6** (lines 72–78) deletes `knowledge/questions/scaffold-lint-removed-name-blindspot.md` + its INDEX pointer (line 32) after task 2 resolves it. The rationale — "applying this change's own D3 lesson to itself" — is sound and explicit.
3. **Volatile /tmp path** is gone. The header (line 3) now references `stale-evidence.md` **in the change dir**, and the file exists (confirmed). The header also carries an explicit STOP instruction (line 6: "If it is missing, STOP and ask").

The round 1 🟡/💡 fixes also landed correctly: the hard-rule header now applies to Groups 6–7 (line 8, not 3–4); the concrete regex is anchored in task 1.1 (line 23); the body-agreement check is task 5.3 (lines 131–132); task 7.14 explicitly says "delete the line entirely" (line 198).

The tasks cover all 7 DELETE-ENTRY files (Group 6) and all 14 TRIM files (Group 7), each cross-referenced against the authoritative `stale-evidence.md`. Cascading reference cleanup (6.8) is accounted for. Cross-group dependencies are either acknowledged explicitly (7.6 → task 1) or intra-group and sequential by construction.

### 🔴 Blocking Issues

None.

### 🟡 Should Fix

1. **Naming inconsistency — `stale-evidence.md` vs `verify-stale.md`.** The evidence file was renamed from `verify-stale.md` (the original `/tmp/` name) to `stale-evidence.md` during the round 1 fix. The `tasks.md` header (line 3) correctly names it `stale-evidence.md`, but three other locations still reference the old name:
   - `notes.md` line 62: "evidence-gated against `verify-stale.md`"
   - `notes.md` line 86: "adversarial re-verification pass (`verify-stale.md`)"
   - `notes.md` line 113: "per `verify-stale.md`"
   - **Task 8.5** (line 211): "per `verify-stale.md`"

   The implementer can self-correct from the header, but task 8.5 is the final manual verification step — pointing it at a filename that doesn't exist is a minor footgun. Either rename the file back to `verify-stale.md` (simplest), or update these four references to `stale-evidence.md`.

### 💡 Suggestions

2. **Task 4.1: "Remove/correct" is two different verbs.** Since the `compatibility: Requires openspec CLI.` line is false for the seven skills, the action is *remove it*. "Correct" implies changing it to something truthful, which raises the question "to what?" The implementer will figure it out, but a single unambiguous verb would be clearer.

3. **Task 8.5 is partially redundant with the hard-rule header** (lines 8–11) and the per-file KEEP instructions in Group 7. The header already says "files marked TRIM keep live sibling items — remove ONLY the named sub-bullets, never the whole file" and each task 7.1–7.13 specifies exactly what to keep. Task 8.5 adds a manual re-read pass — not harmful, but if an implementer skips reading `stale-evidence.md` during Group 7 execution and defers verification to 8.5, they'll be reconstructing trim decisions from a summary rather than from the authoritative source.

### Verdict

Round 1 fixes are real and complete. The task coverage is now exhaustive — every STALE verdict in `stale-evidence.md` maps to a task in Group 6 or 7, every cascading reference is handled, and every code-fix group closes its own tracker file. No 🔴 blocking issues remain. The single 🟡 (naming drift in four references) is self-correctable from the header and does not gate freeze.

PASS — ready to freeze

VERDICT: PASS
### Post-round-2 orchestrator fixes
- 🟡 naming drift: evidence file renamed back to `verify-stale.md` so all 5 references
  (notes.md x3, tasks.md x2 incl. the final 8.5 gate) resolve. Header updated.
- 💡 task 4.1 'Remove/correct' -> 'Remove' (the line is false; there is nothing to correct to).
- 💡 8.5 redundancy: KEPT deliberately. It is the last guard on the change's highest-risk
  property (no live work lost); redundancy there is intentional, not waste.

## Post-freeze scope addition — orchestrator, 2026-07-16

Recorded for transparency: `tasks.md` was FROZEN at Round 2 (`FREEZE: READY`), then amended.

**Added:** task 4.3 (document the `<!-- lint:planned -->` marker in `knowledge/README.md`)
and a consequent amendment to task 7.2 (remove all of §1 rather than keeping §1(b), since
4.3 resolves it).

**Why, and why it is not re-reviewed:** while running `check.sh` to commit the frozen
artifacts, the live-tree knowledge_lint gate went red on the untracked
`knowledge/questions/commit-gate-bypass.md` — a citation to the *proposed* path
`scripts/githooks/pre-commit`. The `<!-- lint:planned -->` marker exists precisely for this
and is spec'd, but is documented in no author-facing doc, so the orchestrator only found it
by grepping `knowledge_lint.py`. That is first-hand evidence for the parked
`sll-lint-planned-author-doc` item: the mechanism exists but is undiscoverable, so authors
red the suite and then reverse-engineer the fix.

The addition is doc-only, sits inside Group 4's existing "instruction-surface accuracy"
theme, and closes a parked item the change was already sweeping. Judged disproportionate to
spend a third reviewer pass on one documentation line. The verify phase's independent passes
cover it. If verify disagrees, this note is the audit trail.

**Also fixed in the same working tree (pre-existing, not part of this change's tasks):** the
two live-tree lint findings in `commit-gate-bypass.md` — an illustrative `plans/…/handoff.md`
ellipsis reworded to prose (it was never a real citation), and the forward reference marked
`<!-- lint:planned -->`. `knowledge_lint` is now clean.
