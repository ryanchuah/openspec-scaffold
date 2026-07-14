# tasks — verify-adversarial-fixtures (MEDIUM)

Apply-phase edits ONLY (prose/YAML — no code, no new tests). Design + scope + acceptance:
`notes.md`. Two files, three edits. **Re-grep each anchor before editing** (verify the exact
substring still matches). Do NOT re-author or add a spec delta — there is none (see notes.md
"placement"). Preserve exact surrounding whitespace/indentation.

## T1 — Extend the canonical verify rule (`openspec/config.yaml`)
In `openspec/config.yaml`, inside `rules:` → `verify:` step (2), extend the existing "green is
necessary but NOT sufficient" clause. This is the CANONICAL home for the rule.

- [x] **Edit.** Replace the exact substring:
  ```
  - green is necessary but NOT sufficient; (3) eyeball
  ```
  with (note the 6-space indentation on each continuation line — it matches the `>-` block scalar's
  indent; single newlines FOLD to spaces at parse time, so this is one logical clause, just not one
  giant physical line):
  ```
  - green is necessary but NOT sufficient: the executor's tests are a single blind
      source, so for any change whose diff carries decision logic (parser, state machine,
      detector, validator, branch-taking transform) the primary MUST also author its OWN
      adversarial/boundary fixtures — the boundary and should/should-not-trip inputs the
      executor's tests omit — and confirm behavior on them, since a green suite can hide a
      real defect at an untested boundary (the verify skill's "Adversarial / boundary
      fixtures" subsection carries the per-code-type how); (3) eyeball
  ```
  (Inside the `>-` folded block scalar — the continuation lines fold together into one clause.
  Change nothing else in the block. This states the rule + points to the skill for the detailed
  per-type breakdown — single-source: config owns the rule, skill owns the how.)

## T2 — Add the operational subsection to the verify skill
In `.claude/skills/openspec-verify-change/SKILL.md`, insert a NEW subsection immediately BEFORE the
line `### Multi-model passes (independent verification gates)`.

- [x] **Edit.** Replace the exact anchor line:
  ```
  ### Multi-model passes (independent verification gates)
  ```
  with the following (the new subsection, a blank line, then the original anchor line preserved):
  ```
  ### Adversarial / boundary fixtures (self-review core)

  **Canonical rule:** `openspec/config.yaml` `rules.verify` step (2) — *green is necessary but not sufficient; author your own adversarial/boundary fixtures for logic-bearing changes.* This subsection is the operational how; it cites that rule and does not restate it.

  The apply-executor's passing test suite is a **single blind source**: it covers the paths the executor considered and can pass green while a real defect hides at an input those tests never reach. This has already bitten the scaffold — a `spec-delta-structure` detector shipped with a false-negative on multi-section deltas while its executor-written tests (single-section only) all passed; only orchestrator-authored multi-section fixtures caught it (ratchet `detector-statemachine-boundary-flush`).

  So during the self-review (Step 5), when the change's diff carries **decision logic** — a parser, state machine, detector, validator, or any branch-taking transform — do NOT stop at re-running the executor's green suite. Independently construct the boundary and adversarial inputs the executor's tests omit, and confirm the change's behavior on them (from a freshly authored test or real output):
  - **State machine / doc-walking parser:** exercise EVERY transition and flush boundary — section headers, first/last item, EOF, empty input — not only the happy middle. (The canonical miss was a per-item flush that fired at two of three boundaries.)
  - **Detector / validator:** feed inputs that SHOULD trip each rule AND inputs that SHOULD NOT, including the empty, single, first, last, and multi-item cases.
  - **Any branch-taking transform:** cover each branch and the edges between them.

  This is **distinct from the test-quality lens**: that lens judges the quality of the tests the executor *already wrote*; this obligation has the orchestrator *author the boundary tests the executor never wrote*. A defect surfaced this way takes the existing defect path (Step 8: diagnose, re-delegate a fix-spec, re-verify). A change whose diff carries **no** decision logic — pure prose, docs, config, or data-free rewiring — does not trigger this; record that determination in `notes.md` and proceed.

  ### Multi-model passes (independent verification gates)
  ```

## T3 — Point Step 5 of the verify skill at the new subsection
In `.claude/skills/openspec-verify-change/SKILL.md`, augment Step 5 ("Re-run the FULL test suite
yourself") with a short pointer right after the "necessary but not sufficient" sentence.

- [x] **Edit.** Replace the exact substring:
  ```
   It must be green (pre-existing skips OK). A green exit is **necessary but not sufficient.**
  ```
  with:
  ```
   It must be green (pre-existing skips OK). A green exit is **necessary but not sufficient.**

   **When the diff carries decision logic** (a parser, state machine, detector, validator, or branch-taking transform), a green executor suite is not enough — author your OWN adversarial/boundary fixtures and confirm behavior on them before proceeding. See the **Adversarial / boundary fixtures (self-review core)** subsection for what to construct and why; a change with no decision logic in its diff records that determination in `notes.md` and skips this.
  ```
  (Preserve the leading 3-space indentation of the numbered-step body.)

## T4 — Green gate (report only; do NOT commit)
- [x] Run `bash scripts/check.sh` → must exit 0 (ruff + format + pytest). No `.py` changed, so no
  ruff autofix expected; run it to confirm the tree is green after the prose edits.
- [x] Run `/usr/bin/python3 scripts/scaffold_lint.py` (or via `check.sh` if it wraps it) and confirm
  no NEW findings from these edits (citation / model-id / budget checks). Report the exact result.
- [x] Report: the exact `check.sh` result and the `git diff --stat`. Do NOT commit — the orchestrator
  reviews and commits.
