## Why

OW-11 ("Skill de-bloat + mechanized gates") shipped its low-risk mechanized-gates subset and deferred
four fuzzy de-bloat sub-items to a tracked follow-on. They are the entire remaining scaffold-hardening
tail. All four share one root cause: three OpenSpec workflow skills (verify, propose, explore) still
carry **fuzzy prose rituals where a deterministic gate belongs, plus dead gallery prose** — and
prose-as-enforcement is demonstrably unreliable (the 5-field `notes.md` checkpoint ritual was skipped
in 2 of the last 3 MEDIUM changes). Because these skills are scaffold-managed and propagate to every
downstream repo, the weakness compounds across repos. The direction gate confirmed `PREMISE: AGREE`.

## What Changes

- **verify coverage de-bloat.** Replace the verify skill's step-13/14 fuzzy clauses ("search codebase
  for keywords related to the requirement / assess if implementation likely exists"; raise CRITICAL on
  a keyword miss) with (a) a **deterministic structural check** — enumerate the delta's
  `### Requirement:` / `#### Scenario:` headers, confirm all `tasks.md` checkboxes are `[x]`, and run
  the existing `spec-delta-structure` detector — and (b) a short **coherence note** in which the
  orchestrator maps each enumerated requirement to the behavioral evidence already gathered in the
  mandatory behavioral review (steps 4–8) and flags any unexercised requirement as a gap. The semantic
  "is this requirement satisfied" judgment stays LLM but is grounded in real behavioral evidence, not
  keyword search. Collapse the three-dimension CRITICAL/WARNING/SUGGESTION scorecard into a leaner report.
- **notes-checkpoint detector.** Add a `notes-checkpoint-structure` detector to `scripts/checks.py`
  (same registration shape as `spec-delta-structure`: `family="check"`, floor, always-available,
  enabled-by-default) that verifies a change's `notes.md` carries the five required verify-checkpoint
  fields. **Trigger:** it activates for a non-archived change whose `tasks.md` checkboxes are all `[x]`
  (⟺ apply complete, verify due) — so it catches the real failure mode (checkpoint missing *entirely*)
  without false-positiving on in-progress changes. **Tolerance:** it matches the five fields by
  number+keyword within the verify-checkpoint section (drift-tolerant; exact patterns in `design.md`),
  flagging any missing field. Wire it as the verify-time forcing-function and **delete** the redundant
  step-18 verbal-echo ritual (net prose reduction).
- **freeze-check + machine-readable review verdict.** The reviewer already emits two judgment signals:
  a `### Verdict` (`PASS`/`NEEDS REVISION`) and, for direction artifacts, a `PREMISE: AGREE|DISSENT`
  line. This change (a) **tightens** the reviewer's severity verdict to a strict machine-parseable
  `VERDICT: PASS|NEEDS REVISION` token (in the `openspec-reviewer` contract + the propose skill's
  reviewer-invocation prompt) — it does NOT add a third reviewer signal; and (b) adds
  `scripts/freeze_check.py` as the **single canonical freeze determination**, which DERIVES a
  `FREEZE: READY|BLOCKED` verdict from the reviewer's `VERDICT` (+ `PREMISE` for `proposal.md`) and the
  artifact type. Freeze *policy* thus lives in one deterministic, testable place; the reviewer stays
  decoupled from workflow policy. Wire it into the propose freeze ladder; the orchestrator retains
  overrule authority (recorded in `review-log.md`, per the existing "reviewer can be wrong" rule).
- **explore trim.** Delete the explore skill's redundant gallery prose (a standalone ASCII diagram
  block and the ~100-line "Handling Different Entry Points" worked-dialogue section), keeping the
  mechanized phase-gate flow, the OpenSpec-awareness section, and a compressed stance summary.
- **checks.py cwd-litter fix (L5).** Default `checks.py --check <name>` output to `output/checks/`
  (already gitignored) instead of the current working directory, and update the verify skill's
  detector-invocation prose to read findings from there. Eliminates the disposable `./<name>.json` every
  `--check` invocation drops at the repo root. **Pre-resolved as firm scope** (the explore brief framed
  it design-gated): it is low-risk, the verify-skill co-update is already planned for the other items,
  and safety is confirmed — the only callers that read `--check` findings from disk are the co-updated
  scaffold verify-skill prose, and `test_checks.py` always passes `--out` explicitly. Droppable at
  design only if it unexpectedly complicates the detector work.

### Folded-in verify guidance (generalizable HANDOFF lessons, apply downstream)
- **L2 — doc-rewrite/transform reconstruction fidelity.** Add to verify's "Adversarial / boundary
  fixtures" subsection an obligation: for any doc-rewrite/transform tool, author
  **reconstruction-fidelity** (round-trip byte-identity: no blank-line drift, no section reorder) +
  **idempotency** (apply-twice = apply-once) fixtures, not just "did it apply" unit tests. This class
  caught 3 real defects on OW-12's promoter.
- **L3 — fixtures assert exit code AND state.** Same subsection: every fixture asserts both the process
  exit code and the file/report state, so a spurious anomaly-exit cannot pass by accident.

## Capabilities

### New Capabilities
<!-- None — all durable requirements land in existing capabilities. -->

### Modified Capabilities
- `defect-prevention-detectors`: ADD a fourth universal `checks.py` builtin — `notes-checkpoint-structure`
  — that structurally validates a change's `notes.md` verify-checkpoint fields (parallel to the existing
  `spec-delta-structure` detector).
- `premise-review-gate`: MODIFY the proposal-freeze requirement so the freeze determination is mechanized
  by a strict machine-readable reviewer `VERDICT` token parsed (with `PREMISE`) by a deterministic
  `freeze_check.py`, with the orchestrator's overrule authority preserved.

> **No `verify-multimodel-gate` delta.** The verify coverage de-bloat modifies only the verify **skill
> prose** (the artifact/spec-mapping checklist, which was never spec-gated) and the notes-checkpoint
> wiring — not the multi-model gate mechanism. Confirmed with the direction reviewer: no requirement in
> `verify-multimodel-gate` changes.

## Impact

- **Skill prose (scaffold-managed, propagated):** `.claude/skills/openspec-verify-change/SKILL.md`
  (de-bloat coverage steps + adversarial-fixtures additions + detector-invocation paths + notes-checkpoint
  wiring + delete step 18), `.claude/skills/openspec-propose/SKILL.md` (freeze-check wiring + strict
  VERDICT token in reviewer prompt), `.claude/skills/openspec-explore/SKILL.md` (gallery trim).
- **Reviewer contract (scaffold-managed, propagated):** `.opencode/agents/openspec-reviewer.md` (emit
  the strict `VERDICT:` token).
- **Scripts (scaffold-managed, propagated):** `scripts/checks.py` (new `notes-checkpoint-structure`
  detector + `--check` output-dir default), `scripts/freeze_check.py` (new) + tests; `scripts/test_checks.py`
  (detector tests). New `scripts/scaffold_manifest.txt` entries for `freeze_check.py` and its test.
- **Specs:** delta files for `defect-prevention-detectors` (ADDED) and `premise-review-gate` (MODIFIED).
- **Out of scope:** downstream propagation (operator-gated, deferred); push to remote (operator-gated);
  the unrelated low-priority follow-ons (`_validate_delta` two-pass merge; shared `_parse_harness_table`
  helper); requirement-level `openspec status` (the CLI does not expose it — not this change's job).
- **No breaking changes to runtime behavior.** The `--check` output-dir default change is safe (see the
  L5 bullet's pre-resolution).

## Assumptions (design-phase validation checklist)
- **A1.** The orchestrator's coherence note (grounded in the mandatory behavioral review) is a more
  reliable requirement-coverage signal than keyword search — because steps 4–8 already exercise real
  behavior, so the note reports observed evidence rather than inferring from a keyword hit.
- **A2.** The reviewer's `VERDICT:` token will be emitted reliably enough for deterministic parsing
  (it is a single strict line, mirroring the verifier's already-reliable `VERDICT: READY|NEEDS REVISION`).
- **A3.** The `notes.md` 5-field verify-checkpoint convention is stable enough for structural detection
  via number+keyword matching (the convention is single-sourced in the verify skill and unchanged here
  except for deleting the separate verbal-echo).
- **A4.** Tying the notes-checkpoint trigger to "all `tasks.md` checkboxes `[x]`" is a sound proxy for
  "verify is due"; SMALL/no-standard-tasks changes are skipped rather than false-flagged.
