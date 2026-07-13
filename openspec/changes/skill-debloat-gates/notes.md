# notes — mechanized-verify-propose-gates (OW-11, scoped)

**Tier:** MEDIUM. **Orchestrator:** Opus (design pre-made — AUDIT finding 5; recon `recon-ow11.md`).
**Apply:** delegated (deepseek-flash default — precise script + tests + surgical prose reorders).
Partially closes **OW-11** in `OUTSTANDING-WORK.md` and closes the ratchet item
`medium-change-spec-delta-unvalidated`.

## Scope decision (read first)
OW-11 as chartered bundles 8 sub-items of very different risk. To ship correctly, this change takes
the **high-value, low-risk mechanization** subset and **defers the fuzzy skill-de-bloat** to a tracked
follow-on. This preserves correctness over breadth (operator's "as much as you can without
compromising correctness").

**IN scope (this change):**
1. **spec-delta lint (#7 — the anchor).** `openspec validate` discovers changes via `proposal.md`, so
   MEDIUM (tasks.md-only) changes AND their spec deltas are **never CLI-validated** (recon reproduced
   live: `openspec validate` sees zero of the open changes). A new `spec-delta-structure` **detector
   in `scripts/checks.py`** (an in-process builtin — NO standalone script, NO new manifest entry;
   `checks.py` is already manifest-listed and propagates) discovers change dirs BY DIRECTORY
   (`openspec/changes/<name>/specs/**/spec.md`, excluding `archive` and dot-segments) and structurally
   validates each delta: a `## ADDED|MODIFIED|REMOVED Requirements` section header is present; every
   ADDED/MODIFIED `### Requirement:` has its normative SHALL/MUST on the FIRST physical line of its
   body; every such Requirement has ≥1 `#### Scenario:`. **Closes the ratchet item** — the exact class
   that made me hand-check SHALL-first-line for OW-7/OW-10's deltas. Findings are ADVISORY at the audit
   level (do NOT fail `check.sh`); T4's verify-skill wiring makes it ENFORCING at verify time (the
   orchestrator resolves any finding before archive). Propagates automatically via the checks.py
   manifest entry.
2. **model-id-agreement lint (#6).** `deepseek-v4-pro/flash` model ids are hardcoded ~59×/14 files
   with no guard (recon; the AUDIT's "44×/13" is already stale — it's actively growing). A new
   `model-id-agreement` check in `scaffold_lint.py` (parallel to the existing `budget-agreement`
   check) scans the same skill/agent/harness file set for `deepseek/deepseek-v4-<tier>` spellings and
   asserts each is in a canonical sanctioned set declared once (a `<!-- CANONICAL: model-ids -->`
   list). Golden-source-only (`scaffold_lint.py` is deliberately NOT manifest-listed).
3. **Concurrent COMPLEX verifier passes (#5).** The two COMPLEX passes (pro behavioral + flash lens)
   currently run **sequentially** by prose even though both are read-only on a frozen tree and the
   harness already supports background launch. Reorder the verify-skill prose to launch both
   concurrently; serialize only the NEEDS-REVISION re-run. Saves ~13 min wall-clock on COMPLEX. Pure
   prose, no plumbing.
4. **explore→propose slug-match warning (#4).** A slug mismatch between explore's `plans/<slug>/`
   brief and the propose change name silently orphans the brief + its premise review. Add a
   near-match warning to the propose skill (when the chosen change name has no exact `plans/<slug>/`
   but a close one exists, surface it) — trivial.

**DEFERRED (→ OW-11-residual follow-on, tracked in questions/ratchet):**
- #1 verify steps 12-16 de-bloat (fuzzy "search codebase / assess if implementation likely exists" →
  structural scan + coherence note) — needs a design call; `openspec status --json` only gives
  artifact-level done/blocked, not requirement-level, so the mechanization is non-trivial. Highest
  risk of the eight; defer.
- #2 notes_lint (the 5-field notes.md ritual → a lint) — marginal (the ritual is already skipped in
  2/3 recent MEDIUMs); pairs naturally with the #1 verify-skill de-bloat. Defer with #1.
- #3 freeze-check script — needs a companion prompt change (add a `FREEZE:` token). Defer.
- #8 explore gallery-prose trim — explicitly secondary per the AUDIT.

## Acceptance criteria
1. A `spec-delta-structure` **detector in `scripts/checks.py`** (an in-process builtin, registered
   exactly like `test-quality`/`data-scale` — `family="check"`, floor, always-available, enabled by
   default; NO new standalone script, NO new manifest entry — `checks.py` is already manifest-listed
   and propagates). It discovers change dirs by presence (`openspec/changes/*/`, excluding `archive`
   and dot-segments), globs `specs/**/spec.md`, and validates section-header + SHALL-on-first-physical-
   line + ≥1 scenario per ADDED/MODIFIED Requirement, emitting `{check,rule,path,line,message}`
   findings. Tests in `scripts/test_checks.py` (registry/list/autodetect + positive/negative fixtures).
   The findings are advisory at the audit level (do NOT fail `check.sh`); T4 makes it **enforcing at
   verify time** (the orchestrator runs it and resolves findings before archive).
2. `model-id-agreement` check in `scaffold_lint.py` + its test in `test_scaffold_lint.py`; a canonical
   sanctioned model-id list declared once; the live tree passes (all current spellings sanctioned).
3. Verify skill: the two COMPLEX verifier passes documented to launch concurrently (both backgrounded
   before waiting), NEEDS-REVISION re-run still serial. No change to MEDIUM (single pass).
4. Propose skill: explore→propose slug near-match warning added.
5. Green gate: `bash scripts/check.sh` exit 0 — this runs the new `spec-delta-structure` **tests**
   (T3 in `test_checks.py`, via `pytest -q`) and the `model-id-agreement` scaffold_lint test. (The
   detector's own *findings* are advisory and do NOT gate `check.sh`; it is the pytest tests that
   gate, plus verify-time enforcement per T4.)

## Spec deltas (authored under `specs/`)
- **ADDED `defect-prevention-detectors`** — a third universal in-process checks.py detector
  (`spec-delta-structure`), same shape as test-quality/data-scale. This is the durable home for #7.
- **MODIFIED `verify-multimodel-gate`** — the "hard gate" requirement clarified so the two COMPLEX
  verifier passes MAY be launched concurrently on the frozen tree, with the rerun-failed-and-after
  recovery unchanged (#5).
- **#6 model-id-agreement** needs NO spec delta (shared-lint-gate does not enumerate individual
  scaffold_lint checks; it's an implementation invariant like budget-agreement). **#4 slug-match** and
  **#7's ratchet closure** (recorded in `knowledge/ratchet-log.md`, `check` disposition) need no spec.

## Assumptions (batched)
- **A1 — spec-delta detector is ADVISORY at the audit level, ENFORCING at verify time.** As a
  checks.py builtin its findings surface in the audit report and do NOT fail `check.sh` (same contract
  as test-quality/data-scale). T4's verify-skill wiring makes it enforcing where it matters: the
  orchestrator SHALL run `checks.py --check spec-delta-structure` and resolve any finding before
  advancing to archive. This closes the ratchet via the `check` disposition (a deterministic detector
  now exists where none did) without the false-positive risk of a hard commit-gate on WIP deltas.
- **A2 — exclude `.claude/` (the locked `worktrees/analyze` worktree duplicates `openspec/changes/`)
  and `archive/`** from the delta scan, or the walk double-counts.
- **A3 — de-bloat deferred, not dropped** — recorded as an OW-11-residual follow-on so the AUDIT
  finding 5 items aren't lost.

## Out of scope
- The four DEFERRED items above. Consuming OW-7 telemetry. Removing the locked worktree (not ours).

## Traceability
Partially closes **OW-11** (mechanized-gates half); closes ratchet `medium-change-spec-delta-unvalidated`.
De-bloat half → OW-11-residual follow-on.
