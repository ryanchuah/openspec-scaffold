# Review log — delegated-agent-safety

## Round 1 — `@openspec-reviewer` (deepseek-v4-pro), 2026-07-03

**Verdict:** NEEDS REVISION. **Premise:** `PREMISE: AGREE` (direction validated; mechanism confirmed
a REAL permission control, residual-risk framing confirmed honest, (c) confirmed to preserve both the
`check-mode-reports-drift` and `sync-is-idempotent` contracts; no D10 drift vs the portfolio brief).
Severity tally: 3 🔴 / 3 🟡 / 3 💡. Full review text: `scratchpad/review-tasks.txt`.

### Dispositions

- **🔴 1 & 2 (task 3.4 fixture-git mismatch — the one real blocker; 🔴 2 is a latent false-pass of the
  same root):** FIXED. Rewrote task 3.4 to split tests by dependency: (a) real-SHA validated by a
  standalone test that calls `_scaffold_version()` UNPATCHED against the real repo; (b) beacon
  content + idempotence via a monkeypatched STABLE FAKE (removes the accidental-`"unknown"`
  false-pass); (c) check-unaffected (no git dependency); (d) unknown/best-effort via monkeypatch.
  (I had independently flagged this fixture caveat before the review — see the pre-review de-risking.)
- **🟡 1 (AGENTS.md insertion ambiguity):** FIXED. Task 2.1 now pins the exact insertion anchor
  (after "…scan the entries relevant to the current task.", before the "resuming an in-progress"
  sentence) and adds an anchor-safety caution.
- **🟡 2 (grep scope):** FIXED. Task 1.4 broadened to a repo-wide grep with explicit handling of
  archive (immutable) vs in-flight change dirs.
- **🟡 3 (`_scaffold_version` "unknown" content explicitness):** FIXED. Task 3.1 now states the exact
  argv, the single `--format=…` element, and that an unresolvable HEAD yields exactly
  `scaffold-sync: unknown\n`.
- **🟡 4 (scaffold_lint anchor caution):** FIXED. Folded into task 2.1's anchor-safety note.
- **🟡 5 (no scenario for denylist-independence):** NO CHANGE NEEDED — already scenario-encoded: the
  ADDED requirement's "Destructive data-store command is denied even in-tree" scenario carries an AND
  bullet asserting the deny holds "because it is enforced by the `bash` permission, not by
  `external_directory`". Recorded as considered-and-covered.
- **💡 1 (tee zero-arg):** NO CHANGE — reviewer agrees harmless (passthrough tee writes nothing).
- **💡 2 (deny `python -c` / `node -e`):** ADOPTED as an improvement. Added `python -c`, `python3 -c`,
  `node -e`/`--eval`, `ruby -e`, `perl -e`, plus the already-present `bash -c`/`sh -c`, to the
  denylist (task 1.1). This moves interpreter-eval wrapping from the residual list into the covered
  set; notes.md and the delta spec residual-risk are revised accordingly (primary residual is now
  writes-inside-an-allowed-command). Trade-off (fail-loud, recoverable) documented.
- **💡 3 (taxonomy row ordering):** NO CHANGE — task 2.2 placement (under State) is correct and clear.
- **💡 4 / premise blind-spot (stale `bash: allow` at AGENTS.md:127, a boot-read authority):** ADOPTED
  as a must-fix coherence gap. Added task 1.3b to update the `## Roles` verifier parenthetical to the
  denylist wording so the boot-read file matches the actual agent definition.

All 🔴 fixes are in the artifacts, not self-certified — Round 2 re-review below is mandatory to freeze.

## Round 2 — `@openspec-reviewer` (deepseek-v4-pro), 2026-07-03

**Verdict:** NEEDS REVISION (one 🔴). **Premise:** `PREMISE: AGREE` (stands). Full text:
`scratchpad/review2.txt`. The reviewer confirmed the Round-1 🔴 (task 3.4 fixture) **RESOLVED**, and
✅'d tasks 1.3b, 2.1 anchor-safety, and the interpreter-eval denials.

**Single 🔴 found:** task 1.2's residual-vector prose still listed `python -c`/`node -e` as
*uncovered* while task 1.1 now *denies* them — a self-contradiction against 1.1 + the delta spec +
notes.md.

**Disposition:** ALREADY FIXED — I independently caught and corrected this during a pre-Round-2
coherence read of tasks.md (task 1.2 now lists the true residual set: writes-inside-an-allowed-command
[primary], output redirection, multi-step evasion — matching the delta spec and notes.md verbatim).
Round 2 reviewed the pre-fix version (a race), and prescribed the exact fix already applied. Because a
🔴-clearing fix may not be self-certified, Round 3 below is a targeted confirmation on the current state.

## Round 3 — `@openspec-reviewer` (deepseek-v4-pro), 2026-07-03 — targeted freeze confirmation

**Verdict:** PASS — zero 🔴, zero 🟡, zero 💡. **Premise:** `PREMISE: AGREE`. Full text:
`scratchpad/review3.txt`. Reviewer confirmed both targeted claims: task 1.2 residual vectors now
match the delta spec + notes.md verbatim (interpreter-eval forms stated as blocked, not uncovered),
and zero 🔴 anywhere in the change — all four sub-scopes coherent, tasks map cleanly to the three
delta specs, no scope creep.

**FROZEN 2026-07-03.** Freeze conditions met (zero 🔴 AND `PREMISE: AGREE`). Proceeding to apply under
the session autonomy grant (propose phase-gate STOP overridden by explicit operator autonomy).
Three reviewer passes used (max 3).
