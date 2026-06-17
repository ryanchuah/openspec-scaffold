# W5 — cleanup-workflow-ergonomics · tasks

**Tier:** MEDIUM (tasks.md-only propose; acceptance criteria in `notes.md`).
**Scope:** the four audit "cleanup" residue findings
(`ai-docs/workflow-audit-2026-06-16.md` §B1, §D-iii, §E4, §E5) — make the two
most-executed skills lead with the happy path, normalize spec headers, document the
rollback lifecycle branch, and close the deferred opencode skill-enumeration smoke.
Reorder/normalize/document only — **no guarantee is deleted or weakened.**

**Files touched (all already shared/managed — NOT manifest-changing):**
- `.claude/skills/openspec-apply-change/SKILL.md` (B1)
- `.claude/skills/openspec-verify-change/SKILL.md` (B1)
- `.claude/skills/openspec-sync-specs/SKILL.md` (D-iii promotion convention)
- `openspec/specs/verify-multimodel-gate/spec.md` (D-iii)
- `openspec/specs/scaffold-sync-mechanism/spec.md` (D-iii)
- `AGENTS.md` (E4 rollback branch)
- `docs/test/skill-enumeration-smoke/README.md` (E5 — new procedure)
- `ai-docs/decisions.md` + `ai-docs/open-questions.md` (E5 closure; B1/E4 record)

> ⚠ **Execution sequencing:** W4 (concurrent) also edits `openspec-verify-change/SKILL.md`,
> `AGENTS.md`, and possibly `verify-multimodel-gate/spec.md`. Apply W5 **after** W4
> (recommended W3→W4→W5), and **re-read each shared file from disk before editing** —
> the line numbers below are propose-time references, not apply-time anchors. See
> `notes.md` "Execution sequencing" for the full overlap map.

---

## B1 — apply & verify lead with the happy path

- [x] **1.1** In `openspec-apply-change/SKILL.md` Step 6 "If you are Claude Code"
      (currently `:84–182`): open the section with a ≤3-line **happy path** — e.g.
      "Drive the deepseek `apply-executor` via `opencode run` (harness contract:
      `ai-docs/delegation-harness.md`); on a clean run every `tasks.md` item is `[x]`
      and you proceed to Step 7. Everything below handles the ways that can fail."
- [x] **1.2** Move the existing assert-ran (step 2), success/crash/non-crash triage
      (step 3), and the 4-rung failure ladder (step 4) **verbatim** under a clearly
      labelled `#### Failure modes` (or "When it doesn't go cleanly") subsection that
      follows the happy path. Keep the EXIT-sentinel / concurrent-writer / slice-large-
      changes caveats intact — relocated, not edited.
- [x] **1.3** In `openspec-verify-change/SKILL.md` MANDATORY blockquote (currently
      `:14–34`): restate the 5 self-review steps as a tight happy-path list (read diffs;
      re-run full suite green; eyeball real output; live smoke if external API; on a
      defect, re-delegate) and pull the embedded don'ts / fix-redelegation mechanics /
      escalation rungs into a separated "On a defect / failure modes" block beneath it.
      The multi-model passes section (`:36+`) is unchanged.
- [x] **1.4** Diff-review gate: confirm the B1 edits are **net-semantic-zero** —
      every caveat that existed before still exists (grep the pre-edit phrases:
      "Falling back to default agent", "EXIT=", "NON-CONVERGENCE BLOCKER",
      "concurrent writers", "re-delegate", "Mandatory disclosure"). Also grep one
      distinctive phrase from the verify multi-model-passes block (`:36+`, declared
      "unchanged" in 1.3) — e.g. "independent verification" / "verifier pass" — to confirm
      that section did not drift during the 1.3 rewrite. If any phrase is gone, it was
      wrongly deleted — restore it.

## D-iii — normalize promoted-spec headers

- [x] **2.1** `openspec/specs/verify-multimodel-gate/spec.md`: delete the leading
      `# verify-multimodel-gate Specification` H1 line **and** its trailing blank so
      the file starts at `## Purpose` (match the 5 conformant specs).
- [x] **2.2** `openspec/specs/scaffold-sync-mechanism/spec.md`: same — delete the
      `# scaffold-sync-mechanism Specification` H1 + trailing blank.
- [x] **2.3** `openspec-sync-specs/SKILL.md` step 4.d ("Create new main spec",
      `:77–80`): add the convention so promotions don't reintroduce the H1 — e.g.
      "Start the file at `## Purpose`; do **not** add a `# <name> Specification` H1
      (the repo's 7 specs share this header shape)."
- [x] **2.4** Run `openspec validate --strict` and confirm both edited specs still
      validate with no H1 title. **Scope the gate to the specs** — this is a MEDIUM
      change with no `proposal.md`/`design.md`, so a change-dir completeness warning for
      `cleanup-workflow-ergonomics` is **expected and ignorable**; do not try to "fix" it
      by adding a proposal. The real gate is the per-spec validation.

## E4 — rollback / "shipped change was wrong" lifecycle branch

- [x] **3.1** In `AGENTS.md`, **`## State, write discipline, and the archive-as-handoff
      rule`** (`:149`) — this exact section, to match the notes.md acceptance criterion;
      do not place it under `## OpenSpec workflow`: add one concise paragraph documenting
      the branch the lifecycle currently omits — *"If an archived
      change is later found wrong: `git revert` its commit(s) and open a **new**
      corrective OpenSpec change that references the reverted one in its proposal. Do
      not edit or un-archive the original — the archive is an immutable handoff record."*
- [x] **3.2** Keep it to a few lines — this is a documented branch, not a new tool or
      skill. Ensure it doesn't contradict the existing botched-archive *recovery*
      (`openspec-archive-change/SKILL.md`), which is a different situation (a failed
      archive run vs. a correctly-archived-but-wrong change).

## E5 — opencode skill-enumeration smoke (W0 carry-forward)

- [x] **4.1** Create `docs/test/skill-enumeration-smoke/README.md`, mirroring
      `docs/test/commit-gate-smoke/README.md`: explain that the dual-harness design
      rests on opencode (≥1.16) auto-discovering `.claude/skills/**/SKILL.md` (gated by
      `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS`, default unset — `ai-docs/decisions.md`),
      and give a repeatable check that `opencode` enumerates the `openspec-*` skills
      from `.claude/skills/` (e.g. a non-interactive probe; find the supported
      list/enumerate invocation for the installed opencode and pin it in the doc).
- [x] **4.2** Run the live functional check once against the installed **opencode
      1.17.7** (`/home/pang/.opencode/bin/opencode`) from the scaffold root and confirm
      the openspec skills are enumerated. Capture the exact command + observed output
      in the README as the recorded evidence.
- [x] **4.3** Record the resolution in `ai-docs/decisions.md` (close the audit-E5
      carry-forward: "opencode skill-enumeration smoke — passed against 1.17.7") and
      annotate the E5 line in `ai-docs/open-questions.md` (the W0-resolved entry's
      "E5 → W5 / next OpenCode session" carry-forward) — e.g. append
      "→ RESOLVED by W5, live skill-enumeration smoke passed against opencode 1.17.7".
- [x] **4.4** If — and only if — the live run is not possible in the apply session,
      ship the README and log the single remaining live-run action in open-questions
      instead of silently skipping. (Expected: it IS runnable here.)

## Close-out

- [x] **5.1** `openspec validate --strict` clean for the whole change.
- [x] **5.2** Record the B1 reorder + E4 branch in `ai-docs/decisions.md` if either
      established a reusable convention (happy-path-first skill structure; rollback
      branch); otherwise a one-line follow-on note suffices. **Append — do not overwrite**
      the E5 entry written in task 4.3.
- [x] **5.3** Update `notes.md` field "what the primary should check at verify" with
      the B1 net-semantic-zero grep result and the E5 live-run evidence.

---

### Pre-freeze gate (MEDIUM)
One **deepseek-v4-pro** review of this `tasks.md` + `notes.md` before freeze
(`ai-docs/delegation-harness.md` for the invocation; read-only `openspec-reviewer`).
Phase-gated: **do not auto-advance to apply** — the operator confirms tier + plan
first, and W5 applies after W4 per the sequencing note above.
