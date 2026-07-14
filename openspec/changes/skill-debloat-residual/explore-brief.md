# Explore brief — skill-debloat-residual (OW-11 residual, de-bloat half)

## Problem

OW-11 ("Skill de-bloat + mechanized gates") shipped its low-risk mechanized-gates subset
(`skill-debloat-gates`, archived 2026-07-14) and **deferred four fuzzy de-bloat sub-items** to a
tracked follow-on (`knowledge/questions/skill-debloat-gates-follow-ons.md`). These four are the entire
remaining scaffold-hardening tail; after them the wave-2 backlog is empty. They share one root
problem: **three OpenSpec workflow skills still carry fuzzy prose rituals where a deterministic gate
belongs, plus dead gallery prose** — and prose-as-enforcement has been demonstrably unreliable (the
5-field notes ritual is already skipped in 2 of the last 3 MEDIUM changes).

The four items (independent of each other; nothing blocks on them):

1. **verify steps 12–16 fuzzy coverage.** `openspec-verify-change/SKILL.md` step 13 (Spec Coverage)
   and step 14 (Requirement Mapping) instruct the orchestrator to *"search codebase for keywords
   related to the requirement / assess if implementation likely exists"* and raise CRITICAL when a
   keyword is not found. This is a low-value **re-derivation** of what the mandatory behavioral review
   (steps 4–8) already proved with real output — and a false-positive generator (a keyword miss is not
   a missing implementation). `openspec status --json` is confirmed **artifact-level** (`tasks: done`),
   not requirement-level, so there is no CLI oracle for "is requirement X implemented"; the fuzzy
   keyword-search is the stand-in.

2. **5-field notes.md checkpoint is prose-only.** Verify step 17 mandates 5 fields in `notes.md`
   (verdict / live-output-eyeballed / defect+fix / as-built deltas / forward-looking items) and step 18
   mandates a separate verbal-echo ritual. Evidence of unreliability: `lesson-check-ratchet` follows it;
   `defect-prevention-detectors` and `instruction-surface-coherence` (both same-day MEDIUMs) shipped
   with **no 5-field block at all**. A forcing-function that is skipped 2/3 of the time is not a gate.

3. **propose freeze is an un-mechanized read.** The freeze condition (zero 🔴 **and**, for `proposal.md`,
   `PREMISE: AGREE`) rests on a human read of free-text review prose: 🔴 counts appear as prose
   ("zero 🔴, zero 🟡"), not a machine-countable token. A load-bearing gate on every downstream change
   has no deterministic check.

4. **explore skill is ~63% dead gallery prose.** `openspec-explore/SKILL.md` (339 lines): the mechanized
   phase-gate flow is ~120 lines; the rest is stance/worked-dialogue prose — a standalone ASCII diagram
   block and a ~100-line "Handling Different Entry Points" section of four worked dialogues, each with
   its own diagram — with no mechanized effect. It bloats a scaffold-managed, propagated skill surface.

**Blast radius:** all three skills (verify, propose, explore) govern *every* downstream change in every
scaffolded repo and propagate via `sync_scaffold.py`. Getting a gate wrong here propagates the mistake.

## Proposed solution / direction

One **COMPLEX** change ("fold in as much as you can" — the four items are independent, mutually
non-conflicting, and #1+#2 share the verify file so must be one coordinated edit pass). Direction per item:

1. **verify de-bloat.** Replace the step-13/14 keyword-search clauses with (a) a **deterministic
   structural coverage check** — enumerate each delta `### Requirement:` / `#### Scenario:` and
   cross-reference against `tasks.md` checkbox completion (already CLI-backed); CRITICAL fires only on a
   *structural* gap (a requirement with no covering task), never "keyword not found in code"; and (b)
   fold the semantic "does the implementation satisfy this requirement" judgment into a **short coherence
   note** the orchestrator writes from its own steps 4–8 behavioral review, not a keyword re-derivation.
   The semantic judgment stays LLM (per the workflow-audit "correctly LLM — do not script" list); only
   the fuzzy *mechanism* is removed. Step 15 (Coherence) is legitimate residue and stays. The elaborate
   3-dimension CRITICAL/WARNING/SUGGESTION scorecard collapses to a leaner report.

2. **notes-checkpoint lint.** A `notes-checkpoint-structure` **checks.py builtin** (same registration
   shape as the shipped `spec-delta-structure`: `family="check"`, floor tier, always-available,
   enabled-by-default) that parses a change's `notes.md` for the 5 field markers (tolerant of wording
   drift, by heading/number), flagging any missing or empty-without-a-"none + why". Enforcing at verify
   time (the orchestrator runs it before the archive handoff, exactly as it already does for
   `spec-delta-structure`). Excludes `archive/` and `.claude/worktrees/`. Deleting step 18's verbal-echo
   ritual (the lint is now the forcing-function) — net prose reduction. Propagates via the existing
   `checks.py` manifest entry (no new manifest line).

3. **freeze-check + FREEZE token.** Add a required `FREEZE: <artifact> — READY|BLOCKED` token to the
   reviewer's output (companion prompt-template edit in the propose skill's reviewer-invocation section +
   the reviewer agent contract), mirroring the verifier's already-strict `VERDICT:` line. A new
   `scripts/freeze_check.py` parses the extracted review text → machine FREEZE verdict (and, for
   `proposal.md`, cross-checks the `PREMISE:` line). Wire it into the propose freeze ladder as a
   deterministic gate; the **orchestrator retains overrule authority** (recorded in `review-log.md`,
   consistent with the existing "reviewer can be wrong" rule) — the token is the reviewer's
   recommendation, the script mechanizes the default, judgment stays with the orchestrator. New standalone
   script → new `scaffold_manifest.txt` entries (script + its test). Design call to settle in `design.md`:
   the reviewer *emits* the token (robust, recon-recommended) vs. regex-counting 🔴 (fragile, rejected).

4. **explore trim.** Delete the redundant gallery — the standalone ASCII diagram block and the ~100-line
   "Handling Different Entry Points" worked-dialogue section — keeping the mechanized phase-gate flow, the
   OpenSpec-awareness CLI section, and a compressed stance summary. Pure prose; no spec delta.

**Folded-in HANDOFF lessons (generalizable, apply downstream — cohere with the verify-skill edit):**
- **L2 — doc-rewrite/parser reconstruction fidelity.** Add a bullet to verify's "Adversarial / boundary
  fixtures" subsection: for any doc-rewrite/transform tool, author **reconstruction-fidelity** (round-trip
  byte-identity — no blank-line drift, no section reorder) + **idempotency** (apply-twice = apply-once)
  fixtures, not just "did it apply" unit tests. This class caught 3 real defects on OW-12's promoter.
- **L3 — fixtures capture exit code AND state.** Same subsection: every fixture asserts BOTH the process
  exit code AND the file/report state, so a spurious anomaly-exit cannot pass by accident.

**Candidate (design-gated, lean yes): L5 — `checks.py --check <name>` litters cwd.** Every `--check`
invocation drops `<name>.json` at the repo root (must be hand-deleted, never committed). Since this change
already touches `checks.py` for #2, default `--check` output under `output/checks/` (already gitignored) —
low-risk, improves every downstream detector. Settle in `design.md`; drop if it complicates the detector work.

## Scope framing

**In scope:** the four de-bloat items + L2/L3 verify additions + (design-gated) L5. Spec deltas: ADDED
requirement in `defect-prevention-detectors` (notes-checkpoint detector); MODIFIED requirement in
`premise-review-gate` (FREEZE token + freeze-check gate); verify de-bloat may add/modify a
`verify-multimodel-gate` requirement governing the artifact-mapping step's new shape. Skill-prose edits to
verify/propose/explore. New `freeze_check.py` + tests + manifest.

**Out of scope:** the three low-priority follow-ons unrelated to de-bloat (`_validate_delta` two-pass
merge, shared `_parse_harness_table` helper — both from the prior change's residue); downstream propagation
(operator-gated, deferred); push to remote (operator-gated). Consuming any telemetry. Requirement-level
CLI status (openspec doesn't expose it — not this change's job to add).

**Tier:** COMPLEX — load-bearing gate surgery across three propagated skill surfaces, two genuine design
calls (#1 coherence-note boundary, #3 FREEZE-token mechanism), new deterministic detector + script.
Warrants full proposal + design + tasks and the full verify gate.

## Success = 
Fuzzy keyword-search gone from verify's coverage step (structural check + coherence note in its place);
notes-checkpoint and freeze both have deterministic checks; explore trimmed; verify's adversarial-fixtures
guidance covers doc-rewrite reconstruction fidelity; `check.sh` green; live tree lint clean; each new
detector/script exercised on adversarial fixtures (not just happy path).
