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

## Verify outcome — 2026-07-13 (orchestrator: Opus)

**Tier/shape:** MEDIUM, verified under CURRENT (pre-change) semantics = **self-review + one pro
behavioral pass**, no flash/lens pass — as pre-decided at freeze (review-log.md lens-selection
note) and per the self-reference note above. The new lens shape does not exist until this change
ships, so it is correctly NOT run on this change itself.

1. **Verdict: READY for archive.** All 14 tasks `[x]`; full gate green from disk
   (`bash scripts/check.sh`: ruff + format + pytest incl. the `scaffold_lint` SEAL and its
   budget-agreement check). Multi-model passes: **self-review → READY**; **pro pass
   (`deepseek/deepseek-v4-pro`) → READY, Defects: None** (real agent asserted ran, fallback-count 0,
   verdict block extracted from disk). Simplicity gate (MEDIUM): docs-only diff, self-reviewed
   against the checklist — the change *reduces* duplication (two invocation subsections collapsed
   into one); no findings. Security gate: not triggered (no auth/credential/data/external-API
   surface).

2. **Live output eyeballed (behavior, not counts):** the new tier-keyed chain renders consistently
   across all edited files; `scaffold_lint` budget-agreement parses the renamed §e verifier rows
   cleanly (`-k 15 780` unchanged, only labels changed); the two verify-skill invocation blocks
   target `/tmp/verify-pro-out.*` and `/tmp/verify-lens-out.*` (no stale `verify-flash-out`); the
   cited harness anchors §a/§d/§e all resolve; residual old-chain vocabulary
   ("self→pro→flash", "pro + flash", "flash-only", "Three independent views", "two invocations",
   "design D5") is **zero** across the edited files.

3. **Defects found and fixed:**
   - *Trivial (self-review, primary inline):* the newly-inlined behavioral prompt read
     "a always-present" → fixed to "an always-present" (SKILL.md). Trivial-typo inline exception.
   - *Real drift (pro pass, primary direct doc-edit):* root **`README.md`** described the verify
     chain in the OLD shape and cited the retired OpenCode `subagent_type` verifier-spawn path
     (L23, L180, L195, L205–206). Root `README.md` was **not** in the frozen touch-surface
     inventory, so the apply left it stale — exactly the drift this change exists to remove.
     Reconciled directly by the primary to the new tier-keyed platform-uniform chain + `opencode
     run --agent openspec-verifier` invocation (per AGENTS.md "quick doc edits done by the primary
     directly; do not over-delegate trivia" — this is human-facing documentation, not
     implementation code). Re-verified from disk: zero residual old-chain terms, gate still green.

4. **As-built delta (archive-executor MUST know):** this change's diff now touches **six** files,
   not the five in the frozen `tasks.md` — root `README.md` was added at verify (see defect above).
   `README.md` is **NOT scaffold-managed** (absent from `scripts/scaffold_manifest.txt`; only
   `knowledge/README.md` is listed) → it does **NOT** propagate downstream, so no per-repo README
   sweep is owed. No other scope change; the two delta specs and the five originally-planned files
   are byte-faithful to the frozen contract.

5. **Forward-looking items (fold into `knowledge/questions/INDEX.md` / `decisions` at archive):**
   - *(Carried from propose — still live)* Prune the 2-of-5 stale/superseded items in
     `knowledge/questions/verify-multimodel-gate-follow-ons.md` (the OpenCode Task-tool path and
     the "denylist deferred" line — both now resolved by this change + `tier-review-tightening`).
   - *(Carried from propose)* Close/update the `knowledge/roadmap.md` OW-3 pointer entry.
   - *(Carried from propose)* OW-1 / OW-4 detectors now have a defined consumer: when they ship,
     their tasks must update the corresponding lens prompt's **detector-handoff sentence** in the
     verify SKILL from "when a detector ships" to the concrete `scripts/checks.py` invocation.
   - *(Carried from propose)* The RENAMED spec-promotion path is still unexercised repo-wide —
     exercise it on a LOW-stakes change before it is needed in anger.
   - **NEW (verify) — generalizable process gap for the archive ratchet triage:** the chain-shape
     touch-surface research inventoried skills/agents/AGENTS.md/specs but **omitted root
     `README.md`**, which duplicates agent-facing rules in human-facing prose. Class:
     "a vocabulary/chain-shape change leaves stale duplicated descriptions in un-inventoried
     human-facing docs (esp. root `README.md`)." A deterministic detector is hard (semantic
     cross-prose consistency), so this is most likely a **waiver-with-re-review-trigger** or a
     lessons entry, not a check — route through the archive Step 6 3-question ratchet triage and
     record the disposition in `knowledge/ratchet-log.md`.

**Still owned by archive (do NOT do at verify — reconciled by the delegated archive-executor,
then primary-reviewed):**
- `git mv` the change dir → `openspec/changes/archive/2026-07-13-verify-stack-redirect/`.
- Promote the two delta specs into `openspec/specs/verify-multimodel-gate/spec.md` and
  `openspec/specs/noninteractive-delegation-safety/spec.md` (both are MODIFIED/ADDED, no RENAMED).
  These promoted specs are currently STALE vs. the new chain — that is expected; promotion is what
  reconciles them.
- Reconcile `knowledge/STATUS.md` (add the shipped section, honor the ≤3-cap; its historical
  "self-review + pro + flash … READY" vocabulary in prior sections is a shipped record, left as-is),
  `knowledge/decisions/INDEX.md` (new registry line for this change; the `tier-review-tightening`
  L35 line carries old chain vocabulary as historical record — leave it), and
  `knowledge/questions/INDEX.md` (fold in the field-5 items above).
- Run the archive Step 6 ratchet triage over this change's found-and-fixed defects (the NEW
  process-gap item above is the ratchet candidate; the two doc-edit fixes are one-off slips → no
  entry).
- Downstream propagation of the five scaffold-managed edited files is **operator-gated and
  deferred** — do not sync without fresh authorization. (`README.md` is not scaffold-managed.)
