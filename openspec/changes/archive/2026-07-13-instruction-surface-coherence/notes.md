# notes — instruction-surface-coherence (OW-9 + OW-14)

**Tier:** MEDIUM. **Orchestrator:** Opus (design calls pre-made in
`knowledge/research/workflow-audit-2026-07-11/AUDIT.md` findings 3 + §"Orchestrators keep doing
mechanical work inline" + §Addendum). **Apply:** delegated (deepseek-flash default).

This change merges two tightly-coupled wave-2 items the design explicitly pairs (OW-14 "pairs
with OW-9"): both edit `AGENTS.md` (model-assignment matrix + Working-process rules) and the
lifecycle skill prose. Kept as one change for coherence; both OW numbers close together.

## Why (evidence)
The instruction surface carries **live contradictions** that fire at every phase boundary, plus a
delegation rule that is "write-only memory" — recited and then under-applied (AUDIT.md §Addendum,
the wave-1 "prose lessons are write-only memory" pattern applied to the instruction surface
itself). Mechanism fixes, not more prose.

## Acceptance criteria

### OW-9 — instruction-surface contradiction sweep
1. **Autonomy-grant vs phase-gate contradiction resolved.** A single canonical statement (home:
   `AGENTS.md`, spec-governed by a new `tier-confirmation-gate` requirement) says an autonomy
   grant permits phase **auto-advance** EXCEPT across (a) a premise **DISSENT**, (b) a verify
   **NEEDS-REVISION** escalation, or (c) any **operator-named gate** (downstream propagation,
   push-to-remote). The four phase skills' PHASE-GATE sections **cite** this rule instead of each
   asserting an unconditional "never advance without explicit user request — hard rule."
2. **Self-review contradiction resolved.** verify's self-review pass is described **consistently**
   across the verify skill and `delegation-harness.md` as the **orchestrator's own review pass**
   (the pass whose independence the multi-model gate is defined against) — not an "independent"
   pass. Wording reconciled so the two sites agree.
3. **Propose duplicated freeze branches de-duplicated.** The propose skill's parallel
   Claude-vs-OpenCode freeze-logic branches collapse to one shared statement + a thin
   platform-specific delta (extraction, not redesign — behavior preserved).
4. **Archive EXIT-sentinel added.** The archive-executor `opencode run` invocation gains the
   `; echo "EXIT=$?" > /tmp/<phase>-out.exit` sentinel; `delegation-harness.md` §d's note that this
   was "a pre-existing drift, left as-is" is updated to reflect it is now present.
5. **Assumption-batching rule added** (canonical home: `AGENTS.md`; folds the operator-attention
   finding): a **non-blocking** ambiguity gets a recorded default in the change's `notes.md`
   `Assumptions` block and is batch-surfaced at the next operator gate; only a **blocking**
   ambiguity interrupts immediately.
6. **Sonnet-first pre-route line added** to the model-assignment matrix: the operator MAY pre-route
   a change's apply to **Sonnet-first**, recorded in `notes.md`; the deepseek-first default is
   unchanged (legitimizes existing practice; OW-7 telemetry later decides whether the default moves).
7. **Boot-read displacement rule added** (canonical home: `AGENTS.md`): adding a new mandatory boot
   read SHALL displace or shrink an existing one — the boot set is a fixed budget, not a growing
   list.

### OW-14 — delegation-by-default mechanics
8. **Haiku tier added** to the model-assignment matrix (today it names only Sonnet-for-extraction).
9. **Canonical delegation rule stated once** (home: `AGENTS.md`, the existing "Use subagents"
   bullet becomes/points to the canonical statement): **run-and-extract → subagent** (haiku
   mechanical / sonnet extraction); **read-and-judge → orchestrator**; plan the slices before
   delegating.
10. **Point-of-action cues** added inside the verify / apply / archive skill steps where the
    orchestrator runs builders / probes / test-suites / JSONL-parsing — a one-line "delegate the
    run+extract; read the distilled report" cue at the moment of action (the rule must fire where
    the mistake happens, not only in a global preamble), each citing the canonical rule.

## Apply routing decision
**This change's apply is pre-routed Sonnet-first** (dogfooding the very rule it adds, OW-9 item 6).
Rationale: the change is prose-coherence surgery — T11 (reconcile self-review wording across two
files) and T12 (collapse the propose freeze-branch duplication without altering behavior) are
judgment-heavy edits where deepseek-flash's error rate on nuanced prose is a real risk; the
remainder is mechanical but shares the working tree, so a single Sonnet executor beats splitting.
The deepseek-flash-first default is unchanged for other changes.

## Assumptions (batched — surface at next operator gate)
- **A1 — the optional Claude-only PostToolUse large-Bash-output nudge hook (OW-14 item c) is
  DEFERRED, not built here.** Rationale: it is Claude-only harness-private surface needing its own
  decision-record carve-out (like the commit-test-gate hook), and the agent-neutral instruction
  edits deliver the rule's substance. Parked as a follow-on. Reverse if the operator wants the hook
  in-scope.
- **A2 — the optional session-handoff content-checklist line (OW-9 "at most a content checklist
  line") is DEFERRED.** The write-side convention already lives in `knowledge/README.md`; a
  checklist line is low-yield. Parked.
- **A3 — spec footprint kept minimal:** exactly one spec delta (`tier-confirmation-gate`, the
  autonomy phase-advance carve-out). Every other fix is instruction-surface prose (AGENTS.md canon
  + skill edits) — no new capability spec, matching the prose-coherence nature of the sweep.

## Out of scope
- OW-8 (prompt-template reshaping / premise-prompt single-sourcing / AGENTS.md injection scope-down)
  — its own change. This change does NOT reshape delegated prompt templates.
- OW-11 (verify step-12–16 mechanization, freeze-check/notes_lint scripts) — its own change.
- Any change to the model-assignment-matrix's *routing decisions* beyond adding the haiku tier row
  and the Sonnet-first pre-route option (no re-tiering of existing agents).

## Traceability
Closes **OW-9** and **OW-14** in
`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`.
