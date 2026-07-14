## Context

The OW-11 residual is four independent de-bloat items across three scaffold-managed OpenSpec workflow
skills (verify, propose, explore) plus the `openspec-reviewer` agent and `scripts/checks.py`. The
mechanized-gates half of OW-11 already shipped (`spec-delta-structure` detector, `model-id-agreement`
lint, concurrent COMPLEX passes, slug-match warning). This change removes the *fuzzy prose rituals*
that half deliberately left behind, plus dead gallery prose, and folds in two generalizable HANDOFF
lessons and the checks.py cwd-litter fix (L5). Direction gate + proposal review both `PREMISE: AGREE`.

Current-state anchors (read before implementing):
- Verify skill artifact/spec-mapping checklist = `openspec-verify-change/SKILL.md` steps 12–18. The
  fuzzy clauses are step 13 "Spec Coverage" ("Search codebase for keywords… Assess if implementation
  likely exists") and step 14 "Requirement Implementation Mapping" ("Search codebase for implementation
  evidence"). Step 17 = the 5-field notes checkpoint; step 18 = the verbal-echo ritual.
- Reviewer output contract = `.opencode/agents/openspec-reviewer.md` "Output Format" (`### Verdict`
  emits `PASS`/`NEEDS REVISION`; `### Premise Verdict` emits `PREMISE: AGREE|DISSENT`).
- Propose freeze ladder = `openspec-propose/SKILL.md` step 4c (keys on 🔴 count today).
- Detector precedent = `scripts/checks.py` `_run_spec_delta_structure` (registration shape, change-dir
  discovery, `archive`/dot-segment exclusion, normalized `{check,rule,path,line,message}` findings).
- Explore gallery = `openspec-explore/SKILL.md` — the "Visualize" ASCII block (~lines 104–120) and the
  "Handling Different Entry Points" section (~lines 196–297).

## Goals / Non-Goals

**Goals:**
- Replace verify's fuzzy keyword-coverage with a deterministic structural check + a behavioral-evidence
  coherence note.
- Mechanize the notes-checkpoint obligation with a detector that catches a missing/incomplete checkpoint.
- Mechanize the propose freeze determination with a strict reviewer `VERDICT` token + `freeze_check.py`.
- Trim dead explore prose.
- Fold in L2/L3 verify-fixture guidance and the L5 cwd-litter fix.

**Non-Goals:**
- Requirement-level `openspec status` (the CLI is artifact-level only — not building it here).
- Changing the multi-model verify gate mechanism (`verify-multimodel-gate` unchanged).
- Changing the reviewer's *judgment* — only its verdict *format* is tightened.
- Downstream propagation / push (operator-gated, deferred).
- The unrelated low-priority follow-ons (`_validate_delta` merge; shared `_parse_harness_table`).

## Decisions

### D1 — Verify coverage de-bloat: structural check + coherence note (skill prose only)

The mandatory behavioral review (steps 4–8) is the real correctness proof — it exercises real output.
Steps 12–16 today *re-derive* coverage weakly via keyword search, a false-positive generator. New shape:

- **Step 12 (report structure):** keep, but collapse the three-dimension ceremony framing to a lean
  report (Completeness / Correctness / Coherence remain as report groupings; CRITICAL/WARNING/SUGGESTION
  severities remain — only the fuzzy per-dimension re-derivation is removed).
- **Step 13 Completeness:** keep the deterministic parts verbatim — **Task Completion** (checkbox parse;
  incomplete task ⇒ CRITICAL) and **Structural spec-delta validation** (`spec-delta-structure` detector).
  **Remove** the "Spec Coverage" fuzzy sub-block ("search codebase for keywords / assess if
  implementation likely exists / add CRITICAL if requirements appear unimplemented").
- **Step 14 Correctness → "Requirement coverage note":** replace the "search codebase for implementation
  evidence" prose with: (1) DETERMINISTIC — enumerate every `### Requirement:` and `#### Scenario:` in
  the delta specs (grep/parse); (2) JUDGMENT — write a short **coherence note** mapping each enumerated
  requirement to the behavioral evidence gathered in steps 4–8 (the real output eyeballed / smoke run),
  and flag any requirement whose behavior was **not exercised** as a CRITICAL coverage gap. The trigger
  for CRITICAL is "a requirement the behavioral review did not cover," NOT "keyword not found in code."
  Scenario Coverage folds into the same note (a scenario with no covering test/behavioral evidence ⇒
  WARNING). The coherence note is **MANDATORY, not optional** (verify prose uses MUST) — the whole point
  is to move the coverage judgment onto observed evidence, so it must not decay into a skipped step (the
  same failure mode the notes-checkpoint detector guards against). [addresses design review 💡-3]
- **Step 15 Coherence:** keep (design adherence + pattern consistency) — legitimate LLM residue, not a
  duplicate of anything deterministic. (Direction reviewer confirmed step 15 is not bloat.)
- **Step 16 report:** keep, leaner.

**Why not a mechanical requirement↔task string-match:** there is no reliable key between a delta
`### Requirement:` name and a free-text `tasks.md` checkbox (the highest-risk design call, per both
reviews). Keyword-overlap matching would reintroduce exactly the fragility being removed. So the
deterministic layer only *enumerates* requirements; the *mapping to evidence* is the coherence note,
grounded in observed behavior rather than inferred from a keyword hit. **No spec delta** — this is
verify-skill prose; `verify-multimodel-gate` is untouched.

### D2 — `notes-checkpoint-structure` detector (new checks.py builtin)

Registration identical to `spec-delta-structure`: `family="check"`, `tier="floor"`, always-available
(special-cased in availability like `test-quality`/`data-scale`/`spec-delta-structure`), enabled by
default, normalized `{check,rule,path,line,message}` findings, advisory at audit level (does NOT fail
`check.sh`), **enforcing at verify time** (orchestrator runs it before archive handoff).

**Discovery + trigger (avoids false positives — the key design call):**
- Discover change dirs by presence: glob `openspec/changes/*/` at repo root only (this naturally
  excludes `.claude/worktrees/…`); exclude any dir named `archive` or with a dot-prefixed segment
  (reuse the spec-delta-structure exclusion helper).
- For each change dir, read `tasks.md`:
  - absent, or zero checkbox lines ⇒ **skip** (SMALL / non-standard change — no verify-checkpoint
    obligation).
  - any `- [ ]` unchecked ⇒ **skip** (apply incomplete ⇒ verify not due ⇒ no false positive on WIP).
  - all checkboxes `- [x]` ⇒ **verify is due** ⇒ evaluate the checkpoint.
  - ("zero checkbox lines" = the file exists but contains no `- [ ]`/`- [x]` line — distinct from
    "file absent"; both skip.) [addresses design review 💡-2]
- **SMALL-change edge (design review 🟡-2):** a SMALL change that atypically wrote an all-`[x]` scaffolded
  `tasks.md` into `openspec/changes/<name>/` would trigger the detector though it owes no verify-skill
  checkpoint. This is handled by disposition, not a fragile proxy filter (a "no `proposal.md`" filter is
  wrong — MEDIUM changes are tasks.md-only and lack `proposal.md` yet DO owe the checkpoint): (a) findings
  are **advisory at audit level** (never fail `check.sh`), so a rare SMALL false-positive is a dismissable
  advisory; (b) **verify-time enforcement is tier-scoped by the orchestrator**, who runs the detector only
  for the MEDIUM/COMPLEX change it is verifying. SMALL changes typically use a lightweight plan, not a
  scaffolded `tasks.md`, so the case is rare in practice.
- For a verify-due change, read `notes.md`:
  - absent ⇒ finding `rule: notes-missing`.
  - present but no heading containing (case-insensitive) `verify checkpoint` ⇒ finding
    `rule: checkpoint-missing` (this catches the real failure mode — the whole block absent, seen in
    2/3 recent MEDIUMs).
  - checkpoint section present ⇒ within it, require all five fields by **number+keyword** (drift-tolerant):
    (1) `verdict`, (2) `live output` OR `eyeball`, (3) `defect`, (4) `as-built`, (5) `forward-looking`.
    Each missing keyword ⇒ finding `rule: checkpoint-field-missing` with the field number/name in the
    message. Presence-only (not completeness) — completeness of field 5 stays the orchestrator's
    verbal check (D3-adjacent, see D2-wiring).

**D2-wiring in the verify skill:**
- Step 17 (write checkpoint): keep, lightly slimmed (the detector now enforces field *presence*, so the
  prose need not over-belabor it; the "none + why" guidance stays because the detector is presence-only).
- Step 18 (verbal echo): **replace** the ~23-line fill-in-the-blanks template with a lean step: run
  `checks.py --check notes-checkpoint-structure`, resolve any finding, then confirm to the user the
  detector verdict AND enumerate **field 5 (forward-looking items)** — the one semantic field whose
  *completeness* the detector cannot judge. Rationale: the detector mechanizes presence-checking of all
  five fields (big de-bloat: the itemized echo of fields 1–4 is now redundant), while field-5
  enumeration retains its forcing function against the silent-omission failure mode. (Refinement over the
  recon's "delete step 18 entirely," which would have dropped the field-5 completeness guard.)

**Spec:** ADDED requirement in `defect-prevention-detectors` (parallel to `spec-delta-structure`).

### D3 — freeze-check: strict reviewer `VERDICT` token + `freeze_check.py`

**Reviewer contract change (`.opencode/agents/openspec-reviewer.md`):** tighten the existing
`### Verdict` output to also emit a strict machine-parseable line `VERDICT: PASS` or
`VERDICT: NEEDS REVISION` (mirroring the verifier's already-reliable `VERDICT: READY|NEEDS REVISION`).
This is a *format* tightening of the signal the reviewer already emits — not a new third signal, and not
a change to its judgment. The `### Premise Verdict` / `PREMISE:` line is unchanged.

**`scripts/freeze_check.py` (new, stdlib-only):**
- CLI: `freeze_check.py --artifact <proposal|design|tasks> --review <path>` where `<path>` is the
  extracted review text (e.g. `/tmp/review-out.jsonl.text.txt`).
- **Anchored parse (design review 🟡-3):** take the **last** line matching the anchored pattern
  `^\s*VERDICT: (PASS|NEEDS REVISION)\s*$` and, for a proposal, the last `^\s*PREMISE: (AGREE|DISSENT)\s*$`.
  Anchoring to whole-line (no surrounding prose/backticks) excludes an inline self-description like
  "emit `VERDICT: PASS`", so the reviewer's `### Verdict` line is the only match. (Same robustness the
  `PREMISE:` regex already relies on.)
- **Freeze policy (single source of truth):**
  - `proposal` ⇒ `FREEZE: READY` iff `VERDICT: PASS` AND `PREMISE: AGREE`; else `BLOCKED`.
  - `design` / `tasks` ⇒ `FREEZE: READY` iff `VERDICT: PASS`; else `BLOCKED`.
  - **Fail-closed:** a missing/unparseable `VERDICT` (or missing `PREMISE` for a proposal) ⇒ `BLOCKED`.
- **Machine-distinguishable BLOCKED reason codes (design review 🟡-1)** — so the propose ladder can branch
  without re-reading prose. Output exactly one of:
  - `FREEZE: READY`  (exit 0)
  - `FREEZE: BLOCKED — needs-revision`  (VERDICT: NEEDS REVISION)  (exit 1)
  - `FREEZE: BLOCKED — premise-dissent`  (proposal, VERDICT PASS but PREMISE DISSENT)  (exit 1)
  - `FREEZE: BLOCKED — missing-verdict`  (no parseable VERDICT, or proposal missing PREMISE)  (exit 1)
  - INFRA errors (bad args, unreadable file) ⇒ exit 3 + stderr.

**Propose-skill wiring (`openspec-propose/SKILL.md` step 4c):** after extracting the review text, the
orchestrator runs `freeze_check.py --artifact <a> --review <path>` and branches on the machine verdict —
this **replaces** the ladder's current human-read 🔴-count as the canonical freeze gate:
  - `FREEZE: READY` ⇒ freeze (for a proposal, a `READY` already implies PREMISE AGREE; no DISSENT branch).
  - `FREEZE: BLOCKED — needs-revision` ⇒ the existing 🔴 path: fix the artifact, **mandatory re-review**.
  - `FREEZE: BLOCKED — premise-dissent` ⇒ the existing DISSENT path: **AskUserQuestion**
    (re-frame / re-scope / override-to-proceed); do NOT collapse this into a plain re-review.
  - `FREEZE: BLOCKED — missing-verdict` ⇒ failed pass: **re-run the review** (do not freeze).
**Orchestrator overrule preserved:** a demonstrably-false `BLOCKED` may be overruled with a rationale
recorded in `review-log.md` (same authority as the existing "reviewer can be wrong" rule). Add
`--require-marker "VERDICT:"` to the propose reviewer's `opencode_delegate.py` post-processing call so a
review missing the token is caught. The reviewer-invocation **prompt** in the propose skill gains one
clause: "emit a strict `VERDICT: PASS|NEEDS REVISION` line as the last line of the `### Verdict` section."

**Spec:** MODIFIED the `premise-review-gate` "A proposal freezes only on zero blocking issues AND premise
agreement" requirement — the freeze determination is mechanized by the `VERDICT` token + `freeze_check.py`
while preserving the zero-🔴-and-AGREE semantics and orchestrator overrule.

**Why script-derives beats reviewer-emits-FREEZE:** keeps freeze *policy* (artifact-type-dependent) in
one deterministic, unit-tested place; the reviewer emits only judgments it owns (severity + premise); the
freeze DECISION stays the orchestrator's (a workflow act, not a review finding).

### D4 — Explore gallery trim (skill prose only)

In `openspec-explore/SKILL.md`, delete: (a) the standalone "Visualize" ASCII diagram block under "What
You Might Do" (~lines 104–120), and (b) the entire "Handling Different Entry Points" section (~lines
196–297, four worked dialogues each with its own ASCII diagram). Keep: the frontmatter, the mechanized
phase-gate flow (the direction-gate steps), "The Stance", a compressed "What You Might Do" bullet list
(without the giant diagram), the "OpenSpec Awareness" CLI section, and the "Guardrails". Preserve every
mechanized/phase-gate instruction verbatim; only illustrative gallery prose is removed. No spec.

### D5 — L2/L3 verify adversarial-fixture guidance (skill prose only)

Append two bullets to the verify skill's "Adversarial / boundary fixtures (self-review core)" subsection:
- **L2:** for a **doc-rewrite / transform tool** (a parser that re-emits a document — spec promoter,
  delta applier, doc rewriter), author **reconstruction-fidelity** fixtures (round-trip byte-identity on
  an unchanged input: no blank-line drift, no section reordering) and **idempotency** fixtures
  (apply-twice ≡ apply-once), not just "did it apply the op" unit tests. (Cite: OW-12's promoter shipped
  3 such defects past green op-level tests.)
- **L3:** every fixture asserts **both** the process exit code AND the resulting file/report state — a
  fixture that checks only one can pass on a spurious anomaly-exit or a silent wrong-write.

### D6 — L5 checks.py `--check` output dir (script + prose)

In `scripts/checks.py` `main()`, change the `--check` branch default from `out_dir = Path(".")` to
`out_dir = Path("output") / "checks"` (undated; `output/` is gitignored). `--floor` and `--report` are
untouched (`--report` already uses `output/checks/<date>/`; `--floor` is out of scope). Update the verify
skill's four `--check` prose references — two lens references (test-quality, data-scale) and two
enforcement references (spec-delta-structure, and the new notes-checkpoint) — to read findings from
`output/checks/<name>.json` rather than the implicit cwd path. [design review 💡-1: count corrected] `test_checks.py` already passes `--out` explicitly, so no test breaks;
add one test asserting the new default location.

## Risks / Trade-offs

- **[Coherence note is judgment, not mechanism]** → the requirement-coverage gap is now caught by the
  orchestrator's note rather than a script. Mitigation: it is grounded in the *already-mandatory*
  behavioral review (real output), which is strictly more reliable than the keyword search it replaces;
  the deterministic enumeration + `spec-delta-structure` still mechanize the structural layer.
- **[notes-checkpoint trigger on "all tasks [x]"]** → a change mid-verify (tasks done, checkpoint not yet
  written) flags transiently at an audit run. Mitigation: findings are advisory at audit level; at verify
  the orchestrator writes the checkpoint *before* running the detector, so it passes; SMALL/no-tasks
  changes are skipped.
- **[VERDICT token adoption]** → an older reviewer response lacking the strict token would fail-closed to
  `BLOCKED`. Mitigation: fail-closed is the safe direction (never auto-freezes a bad review); the reviewer
  contract + prompt both request the token; the wrapper asserts it.
- **[Bundled scope]** → four items + lessons + L5 in one COMPLEX change. Mitigation: items are mutually
  independent; apply is split (orchestrator authors prose, flash does Python); each item is independently
  verifiable; #3 and L5 are cleanly droppable if apply/verify surfaces a complication.
- **[Prose surgery on load-bearing gates]** → verify/propose govern every downstream change. Mitigation:
  full COMPLEX verify (self + pro + flash lens + simplicity); every mechanized instruction preserved
  verbatim; only fuzzy/illustrative prose removed.

## Migration Plan

Skill/agent/script edits land in this repo only. Downstream propagation via `sync_scaffold.py` is
operator-gated and DEFERRED (logged in `knowledge/reference/pending-downstream-propagation.md` at
archive). No rollback complexity — pure additive detector/script + prose edits; revert = `git revert`.

## Open Questions

None blocking. Field-5 completeness remains a human judgment by design (a detector cannot know an
open-question was omitted); the D2 step-18 refinement keeps that forcing function.

## Verification (change-specific acceptance criteria)

1. **verify de-bloat:** `openspec-verify-change/SKILL.md` contains NO "search codebase for keywords" /
   "assess if implementation likely exists" clause; step 13 keeps Task Completion + spec-delta-structure;
   step 14 is a requirement-coverage note grounded in the behavioral review; step 15 (Coherence) retained.
2. **notes-checkpoint detector:** `checks.py --list` shows `notes-checkpoint-structure` as enabled,
   floor, check-family, always-available. Run against adversarial fixtures: flags `checkpoint-missing`
   (all-tasks-done change, no checkpoint), `checkpoint-field-missing` (a field absent), `notes-missing`;
   stays silent on a well-formed checkpoint, on a WIP change (unchecked tasks), on a no-tasks/SMALL
   change, and does not scan `archive/`. Enforcing step wired into verify; step 18 replaced (not just
   deleted) with detector-run + field-5 enumeration.
3. **freeze-check:** `freeze_check.py` returns `FREEZE: READY` for (proposal, VERDICT PASS + PREMISE
   AGREE), (design, VERDICT PASS); `FREEZE: BLOCKED` for (proposal, PASS + DISSENT), (any, NEEDS
   REVISION), and fail-closed on a missing VERDICT / missing proposal PREMISE. Reviewer contract emits
   the strict `VERDICT:` token; propose skill wires the gate + overrule + `--require-marker "VERDICT:"`.
4. **explore trim:** the "Visualize" ASCII block and "Handling Different Entry Points" section are gone;
   all phase-gate/OpenSpec-awareness instructions preserved.
5. **L2/L3:** the two bullets are present in verify's adversarial-fixtures subsection.
6. **L5:** `checks.py --check <name>` (no `--out`) writes under `output/checks/`, not cwd; verify prose
   updated; a test asserts the new default.
7. **Green gate:** `bash scripts/check.sh` exit 0 (new detector tests + freeze_check tests run under
   pytest); live `scaffold_lint.py` clean; `openspec validate skill-debloat-residual --strict` exit 0;
   scaffold manifest lists `freeze_check.py` + its test.
8. **Dogfood:** this change's own `notes.md`, once its tasks are all `[x]`, passes
   `notes-checkpoint-structure`; the change froze its own artifacts with `freeze_check.py`.
