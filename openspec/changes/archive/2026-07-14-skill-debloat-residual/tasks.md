## 1. notes-checkpoint-structure detector (checks.py)

- [x] 1.1 In `scripts/checks.py`, register a `notes-checkpoint-structure` builtin mirroring
  `spec-delta-structure`: add its `_CHECKS` registry entry (near line ~250, `family="check"`,
  `tier="floor"`); add `"notes-checkpoint-structure": True` to `_autodetect_defaults` (~line 344); add it
  to the always-available tuple in the availability special-case (~line 454, alongside `inventory`,
  `test-quality`, `data-scale`, `spec-delta-structure`); add a `_PARSERS` stub
  `"notes-checkpoint-structure": lambda _stdout: []` (~line 622); and add it to `_BUILTIN_RUNNERS`
  (~line 1395). (Line numbers are ~anchors — if `checks.py` has drifted, locate each site by content:
  the existing `spec-delta-structure` entry at each of the five registration points.)
- [x] 1.2 Implement `_run_notes_checkpoint_structure(check, config, out_path)` per design D2. Reuse the
  existing change-dir discovery + `archive`/dot-segment exclusion helper that `_run_spec_delta_structure`
  uses (glob `openspec/changes/*/` at repo root only). For each change dir: parse `tasks.md` checkboxes —
  skip if `tasks.md` absent OR has zero `- [ ]`/`- [x]` lines OR has any unchecked `- [ ]`; evaluate only
  when all boxes are `- [x]`. For a verify-due change emit normalized `{check, rule, path, line, message}`
  findings: `notes-missing` (no `notes.md`), `checkpoint-missing` (no heading containing case-insensitive
  `verify checkpoint`), and `checkpoint-field-missing` for each of the five fields absent from the
  checkpoint section, matched drift-tolerantly by keyword — (1) `verdict`, (2) `live output`/`eyeball`,
  (3) `defect`, (4) `as-built`, (5) `forward-looking`. Presence-only; write findings via `_write_json`.
- [x] 1.3 In `scripts/test_checks.py`, add tests: registry/`--list`/autodetect show it enabled+floor+
  always-available; plus adversarial fixtures (each asserts BOTH the exit code AND the findings/report
  state, per L3): `checkpoint-missing` (all-`[x]` tasks, notes without the heading), `notes-missing`
  (all-`[x]` tasks, no notes.md), `checkpoint-field-missing` (checkpoint present, one field removed),
  clean well-formed checkpoint (no finding), WIP skip (an unchecked `- [ ]` ⇒ no finding), no-checkbox
  `tasks.md` skip, absent-`tasks.md` skip, and archive-dir not scanned.

## 2. freeze_check.py (new script)

- [x] 2.1 Create `scripts/freeze_check.py` (stdlib only) per design D3: CLI
  `--artifact {proposal,design,tasks} --review <path>`. Parse the last whole-line-anchored
  `^\s*VERDICT: (PASS|NEEDS REVISION)\s*$` and, for a proposal, the last
  `^\s*PREMISE: (AGREE|DISSENT)\s*$`. Freeze policy: proposal ⇒ READY iff PASS+AGREE; design/tasks ⇒ READY
  iff PASS. Print exactly one of `FREEZE: READY` (exit 0), `FREEZE: BLOCKED — needs-revision`,
  `FREEZE: BLOCKED — premise-dissent`, `FREEZE: BLOCKED — missing-verdict` (exit 1 for BLOCKED); bad
  args/unreadable file ⇒ exit 3 + stderr. Fail closed on missing/unparseable tokens.
- [x] 2.2 Create `scripts/test_freeze_check.py`: cover every policy combination (proposal PASS+AGREE ⇒
  READY; proposal PASS+DISSENT ⇒ premise-dissent; proposal NEEDS REVISION ⇒ needs-revision; proposal
  missing VERDICT ⇒ missing-verdict; proposal PASS but no PREMISE ⇒ missing-verdict; design PASS ⇒ READY;
  design NEEDS REVISION ⇒ needs-revision), the anchored-parse test (an inline `` `VERDICT: PASS` `` in prose
  does NOT satisfy a NEEDS REVISION real verdict — real last-anchored-line wins), and the exit-3 INFRA
  path. Each test asserts BOTH exit code AND printed reason (L3).

## 3. L5 — checks.py --check output dir

- [x] 3.1 In `scripts/checks.py` `main()`, change the `--check` branch default from
  `out_dir = Path(".")` to `out_dir = Path("output") / "checks"` (leave `--floor` and `--report`
  unchanged). Add a `test_checks.py` test asserting that `--check <name>` with no `--out` writes
  `output/checks/<name>.json` (run in a temp cwd; assert file location + that cwd stays clean).

## 4. scaffold manifest

- [x] 4.1 Add `scripts/freeze_check.py` and `scripts/test_freeze_check.py` to
  `scripts/scaffold_manifest.txt` (Scripts section), so both propagate downstream.

## 5. Reviewer contract — strict VERDICT token

- [x] 5.1 In `.opencode/agents/openspec-reviewer.md` "Output Format", tighten the `### Verdict` contract:
  the reviewer MUST emit, as the last line of the `### Verdict` section, a strict machine-parseable line
  `VERDICT: PASS` or `VERDICT: NEEDS REVISION` (in addition to any human-readable summary). `VERDICT: PASS`
  denotes zero 🔴. Its judgment and the 🔴/🟡/💡 severities are unchanged; only the verdict line is
  formalized. Keep the `### Premise Verdict` / `PREMISE:` contract unchanged.

## 6. Verify skill — de-bloat + wiring (prose)

- [x] 6.1 In `.claude/skills/openspec-verify-change/SKILL.md` steps 12–16, remove the fuzzy clauses per
  design D1: delete step 13's "Spec Coverage" keyword-search sub-block (keep Task Completion + Structural
  spec-delta validation); replace step 14's "search codebase for implementation evidence" with the
  MANDATORY (MUST) requirement-coverage note — deterministically enumerate every `### Requirement:` /
  `#### Scenario:` in the delta, then map each to the behavioral evidence gathered in steps 4–8, flagging
  any requirement the behavioral review did NOT exercise as CRITICAL (a scenario with no covering
  test/evidence ⇒ WARNING). Keep step 15 (Coherence) as-is. Collapse the three-dimension scorecard framing
  in steps 12/16 to a lean report (retain CRITICAL/WARNING/SUGGESTION severities).
- [x] 6.2 Rewire the notes-checkpoint steps (D2-wiring): slim step 17 (the detector now enforces field
  presence — keep the "none + why" guidance); replace step 18's fill-in-the-blanks verbal-echo template
  with a lean step — run `checks.py --check notes-checkpoint-structure`, resolve any finding, then confirm
  to the user the detector verdict AND enumerate field 5 (forward-looking items), the one field whose
  completeness the detector cannot judge.
- [x] 6.3 Add L2/L3 bullets to the "Adversarial / boundary fixtures (self-review core)" subsection: L2 —
  for a doc-rewrite/transform tool, author reconstruction-fidelity (round-trip byte-identity: no blank-line
  drift, no section reorder) + idempotency (apply-twice ≡ apply-once) fixtures, not just "did it apply";
  L3 — every fixture asserts both the process exit code and the resulting file/report state.
- [x] 6.4 L5 prose: update the four `--check` references in this skill (test-quality lens ~line 128,
  data-scale lens ~line 144, spec-delta-structure enforcement ~line 347, and the new notes-checkpoint
  enforcement) to read findings from `output/checks/<name>.json` instead of the implicit cwd path.

## 7. Propose skill — freeze-check wiring (prose)

- [x] 7.1 In `.claude/skills/openspec-propose/SKILL.md` step 4c: add to the reviewer-invocation prompt the
  clause "emit a strict `VERDICT: PASS|NEEDS REVISION` line as the last line of the `### Verdict` section";
  add `--require-marker "VERDICT:"` to the propose reviewer's `opencode_delegate.py` post-processing call.
- [x] 7.2 In the shared freeze ladder, replace the human-read 🔴-count gate with a `freeze_check.py` call
  (`--artifact <a> --review /tmp/review-out.jsonl.text.txt`) and branch on its reason codes:
  `FREEZE: READY` ⇒ freeze; `needs-revision` ⇒ fix + mandatory re-review; `premise-dissent` ⇒ operator
  AskUserQuestion (re-frame/re-scope/override); `missing-verdict` ⇒ re-run review. Preserve the
  orchestrator-overrule rule (record rationale in `review-log.md`).

## 8. Explore skill — gallery trim (prose)

- [x] 8.1 In `.claude/skills/openspec-explore/SKILL.md`, delete the standalone "Visualize" ASCII diagram
  block under "What You Might Do" (~lines 104–120) and the entire "Handling Different Entry Points" section
  (~lines 196–297). Keep frontmatter, the phase-gate/direction-gate flow, "The Stance", a compressed "What
  You Might Do" bullet list, "OpenSpec Awareness", and "Guardrails". Preserve every mechanized instruction
  verbatim — remove only illustrative gallery prose.

## 9. Green gate

- [x] 9.1 Run `bash scripts/check.sh` and ensure exit 0 (new detector + freeze_check tests run under
  pytest); ensure live `python3 scripts/scaffold_lint.py` is clean and `openspec validate
  skill-debloat-residual --strict` exits 0. Do not commit (the orchestrator commits after verify).
