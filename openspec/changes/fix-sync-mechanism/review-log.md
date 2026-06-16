# Review log — fix-sync-mechanism

Reviewer: `@openspec-reviewer` via `opencode run --model deepseek/deepseek-v4-pro`. Each round audits one
artifact; re-review is mandatory after any 🔴 fix.

---

## Round 1 — proposal.md (2026-06-16) — PASS

**Verdict: PASS** — no 🔴. Frozen after applying both 🟡 precision fixes below.

### 🔴 Blocking
None.

### 🟡 Should Fix (both applied)
1. `--check` exit code underspecified ("non-zero") → **applied**: now states "exits **1** on drift (a
   diagnostic CLI, not a blocking hook)", keeping it distinct from the guard's exit 2.
2. Guard detection mechanism left implicit → **applied**: now states the guard detects scaffold-managed
   files "by intersecting the manifest with `git diff --cached --name-only`".

### 💡 Suggestions (not applied — judgment)
1. Add an explicit `## Scope` section — declined: scope is already distributed across Why / What Changes /
   Impact and the template makes it optional; design.md's Verification section will carry the testable line.
2. "REMOVED is a delta against the prior plan, not the codebase" — reviewer confirmed the existing
   parenthetical already handles this; no change needed.
3. Note W0 must be *completed* before W1 apply — already covered by the "Depends on W0" Impact bullet;
   the apply-phase prereq is tracked in the consolidation plan.

---

## Round 2 attempt 1 — design.md (2026-06-16) — ABORTED (no review emitted)

Reviewer hard-errored (~115s, exit 1) when deepseek tried to call the `bash` tool to verify the design's
"every manifest path exists in scaffold" claim. The reviewer agent is `bash: deny` (read-only by design),
so opencode rejected the tool call and terminated the run. Only narration ("let me read X") was emitted —
zero findings. **Not a timeout; not escalated** (root cause is clear). Re-running with explicit steering:
read-only / no bash / use read+glob+grep / treat the primary's disk-verification as given. (Lesson: prepend
this steering to all subsequent review prompts.)

---

## Round 2 attempt 2 — design.md (2026-06-17) — PASS

Re-ran with read-only/no-bash steering + pre-stated disk verification. Clean (exit 0, no error events,
proper format). **Verdict: PASS** — no 🔴. Frozen after applying all three 🟡 + two 💡.

### 🔴 Blocking
None.

### 🟡 Should Fix (all applied)
1. D6 overstated that a differing tail "does not count as drift" → **applied**: qualified to shared-span
   *content*; added the span2/tail join-boundary caveat (one-time `DIFFERS` on first `--check`, cosmetic,
   normalized by one `sync_scaffold.py` run).
2. D5 prose still cited `$CLAUDE_PROJECT_DIR`/cwd after the code switched to `Path(__file__)` → **applied**:
   dropped the parenthetical; now states the guard makes no cwd assumption.
3. "A5" referenced but undefined in W1's artifacts (it's a workflow-audit ID) → **applied**: replaced the
   code comment with a self-contained description of the cwd-fragility bug class.

### 💡 Suggestions
1. Document the one-time `--check` DIFFERS → **applied** (folded into the D6 caveat above).
2. Bootstrap ordering: manifest lists `scaffold_check.py` + `scaffold_manifest.txt`, neither of which exists
   until W1 creates them → **carried into tasks.md**: create the files before the manifest self-verification
   step. (Tracked for the tasks artifact.)
3. `## Roles` literal inside a downstream `## Project context` could mis-slice → **applied**: added as a
   known low-risk accepted trade-off in R1.

---

## Round 3 — specs/scaffold-sync-mechanism/spec.md (2026-06-17) — NEEDS REVISION → fixed, re-review pending

Clean run (exit 0). Confirmed the four cuts from the prior spec are absent and the new requirements present.
**Verdict: NEEDS REVISION** — one 🔴. Fixes applied; `openspec validate --strict` passes; **re-review
mandatory** (cannot freeze on own fix).

### 🔴 Blocking (applied)
1. `sync-script-copies-files` header claimed "byte-identical" universally, contradicting the AGENTS.md
   span-replace scenario → **applied**: header now distinguishes regular files (byte-identical) from
   `AGENTS.md` (span-replace), cross-referencing the preservation requirement.

### 🟡 Should Fix (applied)
2. Missing D7 abort scenario "manifest source missing in scaffold" → **applied**: added
   `sync-aborts-on-missing-scaffold-source`.

### 💡 Suggestions (all applied)
3. `scaffold-tail-guard` bundled two aborts with OR → **applied**: split into `scaffold-tail-invariant-aborts`
   and `long-target-no-tail-aborts`.
4. Guard scenarios framed as "Claude Code git commit attempted" (implies W6 live wiring) → **applied**:
   reframed `hook-blocks`/`hook-passes` to the script-level behavior W1 actually verifies (the requirement
   text keeps the full settings.json-hook contract).
5. Purpose overstated "byte-identical" → **applied**: qualified to "byte-identical for regular files,
   span-identical on shared sections for AGENTS.md".

---

## Round 4 — specs/scaffold-sync-mechanism/spec.md (re-review, 2026-06-17) — PASS

Clean run. **Verdict: PASS** — prior 🔴 confirmed resolved; no new 🔴. Frozen after applying the minor
polish below (no re-review needed — no 🔴).

### 🔴 Blocking
None (prior 🔴 resolved).

### 🟡 Should Fix (applied)
1. `scaffold-tail-invariant-aborts` said "unexpected content," vaguer than the design's `---`/`# ` detection
   → **applied**: tightened the WHEN to "a `---` rule or a `# ` heading."
2. `sync-script-copies-files` requirement text listed only the bad-target abort → **applied**: now also names
   the missing-scaffold-source abort.

### 💡 Suggestions (applied)
1. Implementation-advice parenthetical in the tail-invariant scenario → **applied**: removed (left pure
   observable behavior).
2. Cross-reference pointed at a scenario name → **applied**: now references the
   `agents-md-span-replace-preserves-per-repo-sections` requirement.

All four planning artifacts (proposal, design, specs) now frozen; proceeding to tasks.md.

---

## Round 1 — tasks.md (2026-06-17) — NEEDS REVISION → fixed, re-review pending

Clean run (exit 0). Confirmed all tasks map to design/spec, dependency order correct, apply-phase only.
**Verdict: NEEDS REVISION** — one 🔴. Fixes applied; `openspec validate --strict` passes; **re-review
mandatory** (cannot freeze on own fix).

### 🔴 Blocking (applied)
1. No test task for the `sync-aborts-on-bad-target` D7 abort (T4 covered the other four aborts but not this
   one) → **applied**: added T4.7 covering bad-target + missing-scaffold-source aborts (non-zero exit, no
   writes).

### 🟡 Should Fix (applied)
1. T1.1 target-anchor list omitted `> **MANDATORY` → **applied**: expanded to all three target anchors
   (also fixed an edit that briefly duplicated the clause).
2. No explicit parent-dir-creation test → **applied**: added T4.8 (`sync-creates-parent-dirs`).

### 💡 Suggestions
1. T4.6 bundled guard + missing-source → **applied**: split (guard = T4.6, aborts = T4.7).
2. T2.2 atomically small (docstring only) → kept separate (the M1 limitation is an explicit acceptance
   criterion; clarity over micro-efficiency).
3. T5.1 straddles apply/verify → noted, no action (running unit tests during apply is standard).

### NOTE — process correction (operator, 2026-06-17)
This change was confirmed **MEDIUM**, which per AGENTS.md `## Change tiers` means propose should emit **only
`tasks.md`** (one deepseek-pro review) + acceptance criteria in `notes.md`. The full proposal/design/specs
sequence above was COMPLEX-tier process — an over-run (the propose SKILL.md has no tier gate; the AGENTS.md
rule overrides it). Operator chose to **keep the (clean) artifacts and proceed** rather than trim. MEDIUM
will be honored strictly for W2–W6. See memory `medium-tier-propose-is-tasks-only`.

---

## Round 2 — tasks.md (re-review, 2026-06-17) — PASS

Clean run. **Verdict: PASS** — prior 🔴 resolved; reviewer cross-checked all 26 spec scenarios against the
task list (full coverage, no orphans); no new 🔴/🟡. Frozen.

### 🔴 / 🟡
None.

### 💡 (applied)
1. T4.6 test criterion only said "names it," vs the spec's "directs the editor to change scaffold" →
   **applied**: T4.6 criterion now matches the full spec wording.

**Propose phase COMPLETE** — all artifacts (proposal, design, specs, tasks) frozen; `openspec validate
--strict` passes. Held at the apply gate per operator ("stop whenever you can"); no apply started.
