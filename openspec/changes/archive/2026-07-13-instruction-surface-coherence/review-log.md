# review-log — instruction-surface-coherence (OW-9 + OW-14)

## Round 1 — tasks.md — `@openspec-reviewer` (deepseek-v4-pro), 2026-07-13

**Verdict:** NEEDS REVISION (zero 🔴). **Premise:** `PREMISE: AGREE`.

Reviewer confirmed: tasks concrete + correctly anchored + implementable; spec delta minimal,
additive, non-conflicting with the existing tier-confirmation-gate requirement; MEDIUM-tier pattern
followed; direction sound (problem = live instruction-surface contradictions; root cause = rules
restated in many places drift independently; solution = canonical single-source + cite, the repo's
own pattern). Premise blind-spot noted (not a fault): the delegation cues T15/T16 are rule-only
until OW-7's wrapper lands — known sequencing tradeoff, disclosed.

### 🟡 (all three addressed pre-freeze — zero 🔴, so no re-review round required)
1. **T17 openspec-validate vacuous for MEDIUM.** CONFIRMED empirically: `openspec validate
   instruction-surface-coherence --strict` → "Unknown item", exit 0 (no proposal.md to discover
   from; OUTSTANDING finding 2). → T17 rewritten: dropped the vacuous validate as a "gate", added a
   manual delta-format inspection instruction; green gate is `check.sh` only.
2. **T12 under-specified must-preserve.** → Added the two Claude-branch invariants that must survive
   the freeze-branch de-dup: model-override clause (~L150-152) and prompt-variation-by-artifact
   (~L127-137).
3. **T15 delegation cue risks weakening the "do not delegate" gate.** → Narrowed the cue to Step 5
   (re-run suite) ONLY; cue must restate "behavioral judgment is NON-delegable" inline; no cues at
   Steps 6/7 (observation there is judgment); L203 left untouched.

### 💡 (folded)
- T1 insertion clarified to "after the full grant paragraph". T4 marker/one-liner placement pinned.
- T5 made its own adjacent bullet (not crammed into the short planning bullet).
- review-log.md bootstrapped (this file).

**Freeze decision:** zero 🔴 + `PREMISE: AGREE` → FROZEN after folding all 🟡/💡 above. Per the
propose skill, re-review is mandatory only after clearing a 🔴; none existed, so the artifact freezes
on this round. Full reviewer text retained in the session's ephemeral run artifact
(`/tmp/isc-review-out.jsonl`); the material findings + dispositions are captured above.

## Verify — 2026-07-13

- **Self-review (orchestrator, inline behavioral pass):** PASS. Reviewed the full diff (7 files):
  AGENTS.md T1-T6 all coherent; T12 freeze-ladder de-dup preserves both MUST-PRESERVE invariants;
  T11 self-review wording reconciled; all 4 phase gates cite `autonomy-phase-advance` with correct
  carve-outs; delegation cues correctly scoped (Step 5 only, judgment kept non-delegable). Green
  gate `bash scripts/check.sh` → 414 passed, lint/format clean. No defects.
- **Pro behavioral verifier pass (`openspec-verifier`, deepseek-v4-pro):** **VERIFY: READY**, zero
  defects. Evidence-by-claim confirmed all 6 acceptance areas + citations-resolve + green suite. No
  Sonnet fallback.
- **Simplicity/quality gate:** satisfied by construction — this change is itself a de-duplication
  (T12 collapses restated freeze branches; canonical markers replace repeated rule prose). No new
  code, abstractions, or dead paths introduced.
- **Security gate:** not triggered (no auth/credential/data/external-API surface).
- **Post-verify structural fix (disclosed):** the spec delta's normative SHALL was moved to the
  requirement's first physical line (was 3rd) so it validates clean when promoted at archive —
  purely structural, no semantic change, no re-review required.

**Verify verdict: READY → advance to archive (autonomy grant, no DISSENT/NEEDS-REVISION/operator gate).**
