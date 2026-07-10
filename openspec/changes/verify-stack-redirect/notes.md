# Notes — verify-stack-redirect

**Tier: MEDIUM** (high blast radius — edits the verify gate that governs every downstream
change). Per the AGENTS.md MEDIUM override, propose emits `tasks.md` (+ this notes.md for
acceptance criteria); no proposal.md/design.md. The design rationale and evidence live in
`explore-brief.md` (direction-gated: `PREMISE: AGREE`, `premise-review.md`) and `research/`
(`touch-surface.md` — complete edit-site inventory; `pass-yield-evidence.md` — empirical
per-pass defect yield across all 3 repos).

**Disclosed tier deviation:** this MEDIUM change carries two spec deltas
(`specs/verify-multimodel-gate/`, `specs/noninteractive-delegation-safety/`) because the
promoted `verify-multimodel-gate` capability pins the pass chain (leaving it stale would
recreate the drift this change removes) and `noninteractive-delegation-safety` still
describes the abandoned OpenCode Task-tool verifier path. Precedent: archived MEDIUM changes
`lifecycle-gates`, `checks-facts-split`, `delegated-agent-safety` all shipped `specs/` +
`tasks.md` without proposal/design. The pro review round covers tasks.md AND both deltas.

## Acceptance criteria (verified behaviorally at verify)

1. **Chain shape:** the verify SKILL, delegation harness, AGENTS.md, and verifier agent all
   describe the same tier-keyed, platform-uniform chain — MEDIUM: self → pro behavioral;
   COMPLEX: self → pro behavioral → flash lens; SMALL: unchanged single flash pass. Zero
   residual occurrences of the old "self → pro → flash same-checklist" description or of the
   stale "OpenCode runs flash-only" claim anywhere in the five edited files.
2. **Lens prompts canonical + inline:** both lens prompts (test-quality default, data-scale)
   live in the verify SKILL as fenced blocks; the "design D5" archive pointer for the
   verifier prompt is gone; the behavioral prompt is inlined.
3. **Lens contract:** lens pass is COMPLEX-mandatory / MEDIUM-opt-in, diff-scoped (no
   mandatory full-suite rerun), same verdict block, hard gate with the existing
   re-run-failed-and-after + 3-cycle-bound recovery; lens selection + one-line rationale
   recorded in `review-log.md`; attribution vocabulary is "self-review, pro pass, or lens
   pass" in report/notes steps.
4. **No budget drift:** delegation-harness §e verifier rows keep `780`/`-k 15`;
   `scaffold_lint` (incl. budget-agreement) and the full suite are green via
   `bash scripts/check.sh`.
5. **Verifier agent:** single agent file serves both pass types; `permission:` block
   byte-unchanged; body defaults to the behavioral review when no lens is specified.
6. **Specs:** delta specs match the as-built skill text (chain, lens menu, recording rules);
   the `noninteractive-delegation-safety` delta removes the Task-tool exemption and the
   stale scenario, and touches nothing about permission posture.

## For the apply/verify orchestrator (expected: Opus)

- Apply is delegated to deepseek-flash per the apply skill; these are precise markdown edits
  to five files — mechanical given tasks.md's anchors.
- **Escalation caveat (same as OW-2):** if verify surfaces a DESIGN-level defect (e.g. the
  lens contract itself is wrong, or a chain interaction nobody anticipated) — stop and
  escalate to the operator or a Fable session; do not redesign mid-verify. Implementation
  bugs (missed sweep site, wording drift between files) are normal defect-path work.
- Note the self-reference: this change EDITS the verify machinery it will itself be verified
  by. Verify this change under the CURRENT (pre-change) skill semantics — the new chain
  takes effect for changes verified after this one ships. In practice both chains agree for
  a MEDIUM change except the dropped flash pass; running self + pro (new shape) is
  acceptable and cheaper, and the operator has already endorsed the direction.
- Downstream propagation (operator-gated, at archive or later): the five edited
  manifest-tracked files auto-propagate via `sync_scaffold.py`; the promoted spec changes and
  any `knowledge/` mentions in downstream repos need the manual per-repo sweep —
  `research/touch-surface.md` §"manifest propagation" has the split.

## Forward-looking items already known at propose (for archive reconciliation)

- `knowledge/questions/verify-multimodel-gate-follow-ons.md`: 2 of 5 parked items are
  stale/superseded by this change — prune at archive.
- `knowledge/roadmap.md` OW-3 pointer entry: close/update at archive.
- OW-1/OW-4 (test-quality and data-scale detectors) now have a defined consumer: when they
  ship, their tasks should include updating the corresponding lens prompt's detector-handoff
  sentence from "when a detector ships" to the concrete invocation.
- The RENAMED spec-promotion path (hardened into the archive-executor by `lifecycle-gates`)
  remains unexercised repo-wide. This change deliberately avoided debuting it (kept original
  requirement headers, modified bodies only). Someone should exercise RENAMED on a LOW-stakes
  change before it is ever needed in anger.
