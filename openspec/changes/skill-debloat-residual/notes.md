# notes — skill-debloat-residual (OW-11 residual, de-bloat half)

**Tier:** COMPLEX. **Orchestrator:** Opus. **Apply:** split — orchestrator authored the fence-heavy
skill/agent prose (tasks 5–8) and checked them `[x]` before delegating; deepseek-flash implemented the
deterministic Python (tasks 1–4, 9). Zero Sonnet fallback anywhere.

Closes the entire **OW-11 residual** (`knowledge/questions/skill-debloat-gates-follow-ons.md`, item 1's
four DEFERRED de-bloat sub-items) + folds in HANDOFF lessons L2/L3 and the L5 checks.py cwd-litter fix.
After this, the wave-2 scaffold-hardening backlog is **empty**.

## What shipped
1. **verify coverage de-bloat** — removed the fuzzy "search codebase for keywords / assess if
   implementation likely exists" clauses (steps 13–14); step 14 is now a MANDATORY requirement-coverage
   note grounded in the behavioral review (steps 4–8), with a deterministic requirement/scenario
   enumeration. No spec delta (skill-prose; `verify-multimodel-gate` untouched).
2. **`notes-checkpoint-structure` detector** (checks.py builtin) — flags a verify-due change (all
   `tasks.md` boxes `[x]`) whose `notes.md` lacks a `## Verify checkpoint` section or any of the 5 fields.
   Enforcing at verify (step 18); step 18's verbal-echo template replaced by a detector run + field-5
   enumeration. ADDED requirement in `defect-prevention-detectors`.
3. **freeze-check** — reviewer emits a strict `VERDICT: PASS|NEEDS REVISION` token; `freeze_check.py`
   derives `FREEZE: READY|BLOCKED — <reason>` (reason codes: needs-revision / premise-dissent /
   missing-verdict) from VERDICT (+ PREMISE for proposals). Wired into the propose freeze ladder with
   reason-code branching + orchestrator overrule. MODIFIED requirement in `premise-review-gate`.
4. **explore trim** — removed ~116 lines of dead gallery prose (the "Visualize" ASCII block + the
   "Handling Different Entry Points" worked-dialogue section); phase-gate flow preserved.
5. **L2/L3** — added doc-rewrite reconstruction-fidelity + idempotency + exit-code-AND-state fixture
   guidance to verify's adversarial-fixtures subsection.
6. **L5** — `checks.py --check <name>` now writes under `output/checks/` (gitignored), not cwd; verify
   prose updated to read findings from there.

## Verify checkpoint (mandatory 5 fields + archive handoff) — 2026-07-14

**1. Verdict:** READY for archive. COMPLEX verify: self-review → pro behavioral pass (READY, zero
defects) → flash test-quality lens (READY) → simplicity/quality gate (5 behavior-preserving cleanups,
re-delegated + re-verified) → requirement-coverage note. `bash scripts/check.sh` green; live
`scaffold_lint.py` clean; `openspec validate --strict` clean. No security/data-path gate triggered (lint
tooling + skill prose; no auth/credential/persisted-data/external-API/data-path surface). Zero Sonnet
fallback on apply, fix, or any pass.

**2. Live output eyeballed (behavior, not counts):** I ran the REAL `notes-checkpoint-structure` detector
against 4 hand-built adversarial fixtures — it correctly flags a field-keyword that appears OUTSIDE the
checkpoint section as still-missing (section-scoping holds), correctly excludes a keyword in a trailing
same-level section, handles the EOF-boundary clean case, and is deterministic across two runs. Against
the real repo it correctly flagged THIS change `notes-missing` before this checkpoint was written. I ran
the REAL `freeze_check.py` — `FREEZE: READY` on (proposal PASS+AGREE) and (design PASS); `BLOCKED —
premise-dissent` on (proposal PASS+DISSENT); `BLOCKED — missing-verdict` on a trailing-prose or
inline-backtick VERDICT and on a proposal missing PREMISE; last-line-wins on multiple VERDICT lines. L5:
`--check` writes to `output/checks/` and leaves cwd clean. The detectors detect, the parser parses — not
forced-green.

**3. Defect found + how fixed (attributed):** *Self-review* found **no product defect** — all 10
orchestrator adversarial fixtures passed on the first executor build (the section-scoping boundary, the
one most likely to hide a defect, was correctly implemented). *Simplicity gate* (4 parallel review
agents) surfaced five behavior-preserving cleanups — extract a shared `_iter_active_change_dirs` helper
(realizing D2's stated reuse intent, which the first build only half-did), collapse the 5 field-check
blocks into a `_CHECKPOINT_FIELDS` table, hoist local regexes to module scope, dedupe a double
`notes_md.exists()`, and drop a dead `title_kw` in a test helper — **re-delegated to a fresh flash
executor** and re-verified behavior-preserving (617-test suite + all 10 adversarial fixtures still pass).
*Pro behavioral pass* and *flash lens*: READY, no defects. Zero Sonnet fallback.

**4. As-built deltas (not already in artifacts):**
- The freeze-signal design settled at propose (reviewer emits `VERDICT`; `freeze_check.py` DERIVES
  `FREEZE`, rather than the reviewer emitting a `FREEZE` token) — recorded in design D3, not a surprise.
- The simplicity-gate refactor (shared discovery helper + field table) landed post-executor; it realizes
  design D2's "reuse the existing change-dir discovery" intent that the first build only partially met.
- `freeze_check.py` folds a proposal's missing-`PREMISE` case into the `missing-verdict` reason code
  (design D3 anticipated this).

**5. Forward-looking items (fold into knowledge/questions at archive):**
- **Reviewer `VERDICT:`-token compliance (monitor).** `freeze_check.py` matches a whole-line-anchored
  `VERDICT: PASS|NEEDS REVISION` and **fails closed** (→ `missing-verdict` → re-run) if the reviewer
  decorates the line with trailing prose/backticks. The reviewer contract forbids decoration, but this
  is the first change to ship the token — watch that downstream reviewers emit the bare token; if they
  habitually decorate it, consider a more lenient parse. (This change's OWN propose flow used the
  pre-token reviewer, so the token path is not yet exercised end-to-end in a real freeze.)
- **Uppercase `[X]` checkbox edge.** The detector's checkbox regexes match lowercase `[x]`/`[ ]` only;
  an uppercase `[X]` is invisible (treated as a non-checkbox → change may be seen as "no checkboxes" →
  skipped). Standard OpenSpec/markdown uses lowercase, so this is a monitored edge, not a live bug.
- **`--floor` still writes to cwd** (deliberately out of scope for L5, which fixed only `--check`); a
  future candidate if `--floor` litter becomes a concern.
- **notes-checkpoint field-5 completeness** stays a human judgment by design (a detector cannot know an
  open-question was omitted); step 18 keeps the field-5 enumeration as the forcing function.
- **premise-review-gate overrule scenario** is prose-only (workflow, not script-testable); its behavior
  lives in the propose skill edit, verified by reading, not by a fixture.

**Still owned by archive:** promote the two spec deltas into `openspec/specs/` (ADDED
`defect-prevention-detectors` notes-checkpoint requirement; MODIFIED `premise-review-gate` freeze
requirement) via the deterministic promoter + `openspec validate --strict`; move the change dir to
`openspec/changes/archive/2026-07-14-skill-debloat-residual/`; reconcile `knowledge/STATUS.md` (add this
change; 3-section cap drops the oldest), `knowledge/decisions/INDEX.md` (add the
`notes-checkpoint-detector` + `freeze-check-token` decision lines), `knowledge/questions/INDEX.md` (close
the OW-11-residual item — the four de-bloat sub-items are now shipped; park this change's follow-ons
above); update `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` OW-11 status
(residual shipped → backlog empty) and `knowledge/roadmap.md`; append this change's scaffold-managed
edits to `knowledge/reference/pending-downstream-propagation.md` (DEFERRED + operator-gated). Delete
`knowledge/HANDOFF.md` once absorbed. Downstream propagation + push are operator-gated.
