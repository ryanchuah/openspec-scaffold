# HANDOFF — wave-2 backlog, OW-11 shipped (2026-07-14)

> **Read this right after `knowledge/STATUS.md`.** A session with an explicit operator autonomy grant
> shipped **OW-11 (`skill-debloat-gates`, mechanized half)** end-to-end — apply → verify → archive,
> two commits on `main` (`c36f5db` impl, `c45ed4f` archive), local & **unpushed** (push is
> operator-gated). Absorb this, pick up from **Remaining work**, and **delete this file once the whole
> wave-2 batch (OW-8/12/13) is done**. Its normal state is absent.
>
> **You have NO standing autonomy grant.** The prior grant was in-session only. Confirm tier+plan per
> change unless the operator re-grants autonomy.

## DONE this session — OW-11 mechanized half
`skill-debloat-gates` shipped 4 of OW-11's 8 chartered items (the low-risk mechanized-gate subset):
- **`spec-delta-structure` detector** (`scripts/checks.py`, in-process builtin) — validates every open
  change's spec deltas by directory presence (section headers, SHALL-on-first-physical-line, ≥1
  scenario per ADDED/MODIFIED req). **Closes ratchet `medium-change-spec-delta-unvalidated`**.
- **`model-id-agreement` lint** (`scripts/scaffold_lint.py`, golden-source-only) — every `deepseek-v4`
  token in the instruction surface must match the sanctioned **§(f) table in
  `.claude/skills/_shared/delegation-harness.md`**.
- Concurrent COMPLEX verifier passes (verify-skill prose) + explore→propose slug near-match warning.

The **de-bloat half (4 items) is DEFERRED** → `knowledge/questions/skill-debloat-gates-follow-ons.md`
(OW-11-residual: #1 verify steps 12–16 de-bloat, #2 notes_lint, #3 freeze-check [needs a `FREEZE:`
token], #8 explore gallery-prose trim). Independent — nothing blocks on them.

## ⭐ New scaffold capabilities from OW-11 — USE these
- **At verify, when a change has spec deltas, run `/usr/bin/python3 scripts/checks.py --check
  spec-delta-structure`** and resolve findings before archive (the verify skill Step 13 now wires
  this). It catches the SHALL-not-on-first-line class deterministically — you no longer hand-check it.
- **⚠️ `checks.py --check <name>` writes `<name>.json` into the CWD** (out_dir defaults to `.`). A
  `--check` run from the repo root drops a disposable `spec-delta-structure.json` at the root that you
  MUST delete and never commit. (Pre-existing wart, all detectors; parked as a low-priority follow-on.)
- **Adding a new model tier?** Update the delegation-harness §(f) table or `model-id-agreement` reddens.

## HARD-WON LESSONS (this session; prior lessons in the archived OW-7/OW-10 handoff still hold)
1. **At verify, build ADVERSARIAL / boundary fixtures — do not trust the executor's own tests.** The
   executor's `spec-delta-structure` tests covered only single-section deltas and **passed green while
   the detector had a real false-negative** on multi-section (ADDED+MODIFIED) deltas — a
   `requirement-no-scenario` miss at the `## Section` boundary. My own multi-section fixtures caught
   it; re-delegated a fix (hoist the check into a helper fired at all three boundaries + a regression
   test). Now frozen: ratchet `detector-statemachine-boundary-flush`. **Lesson: for any state-machine/
   parser detector, test EVERY boundary, not just the happy middle.**
2. **`scripts/opencode_delegate.py` lost its execute bit** — invoke as `/usr/bin/python3
   scripts/opencode_delegate.py …`, NOT `scripts/opencode_delegate.py …` (that gives exit 126).
3. **Zero Sonnet fallback all session.** deepseek-flash handled apply + two scoped fix cycles cleanly
   on precise fix-specs. The pro behavioral verifier pass returned READY, zero defects. A precise
   spec is what makes flash viable (prior lesson holds).
4. **Simplicity gate earns its keep:** 4 parallel Sonnet review agents (reuse/simplification/
   efficiency/altitude) surfaced 4 real behavior-preserving cleanups (helper reuse, dead comment,
   dead-unreachable worktrees guard, stale module-docstring count) — re-delegated as one cleanup-spec.
   Two bigger refactors were deferred (two-pass→one-pass merge; shared `_parse_harness_table` helper).
5. **Archive via Sonnet subagent worked** (operator directed it this session, overriding the
   deepseek-pro default). It moved the dir, promoted both spec deltas (`--strict` clean), reconciled
   all 3 trackers, and correctly LEFT the wider-drift bodies (roadmap/OUTSTANDING) for the primary.
   It uses plain `mv`, so `git add -A` stages the rename; the primary owns ratchet triage + wider-drift
   + commit.
6. **`openspec status --change <medium>` DOES work** (returns artifactPaths/isComplete), but
   `openspec validate <medium>` is still vacuous (proposal.md-gated). Green gate = `bash
   scripts/check.sh` only. `openspec list --json` lists proposal-less changes fine.

## Remaining work — recommended order OW-8 → OW-13 → OW-12 (+ OW-15/OW-16 anytime)
- **OW-8 · Delegated-context caching hygiene · SMALL–MEDIUM. NO recon yet — do one first** (OW-7/11
  reshaped the prompt templates). Variable-paths-LAST in apply/archive/reviewer templates; single-source
  the triplicated premise prompt; test `OPENCODE_DISABLE_PROJECT_CONFIG=1` for executors; treat
  AGENTS.md edits as cache-invalidation events. AUDIT finding 2 + §caching.
- **OW-13 · Knowledge-surface bounding round 2 · SMALL. RECON DONE →**
  `openspec/changes/knowledge-surface-bounding-2/recon-ow13.md` (tracked). A new `boot_surface_lint.py`
  + test + manifest entry. Key finding: year-split + plans-count lints are NO-OPS on the scaffold
  (all-2026 decisions, few plans) — build+test via fixtures. **Re-measure STATUS "Immediate next
  action" word budget** before setting one (this session rewrote STATUS). Self-contained, low-risk.
- **OW-12 · Archive mechanization · SMALL–MEDIUM · lowest priority · NO recon yet.** `archive_move.py`
  for the dir move; deterministic delta-applier for ADDED/REMOVED/RENAMED (LLM only for MODIFIED merge
  + reconciliation narrative). Keep the archive-executor on pro. AUDIT finding 6.
- **OW-15** (correctness-audit meta-hardening) + **OW-16** (`product-audit` skill) — chain-independent,
  slot anywhere. See `OUTSTANDING-WORK.md` lines 260/322.

## Downstream propagation — DEFERRED + operator-gated
OW-11 edited scaffold-managed files: `scripts/checks.py`, `.claude/skills/_shared/delegation-harness.md`
(§(f) added), `.claude/skills/openspec-verify-change/SKILL.md`, `.claude/skills/openspec-propose/SKILL.md`.
NOT synced to extrends/psc-monitor without fresh operator authorization. `scripts/scaffold_lint.py`
(model-id-agreement) is golden-source-only — does NOT propagate, by design.

## Pointers
- Backlog + per-item STATUS: `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`.
- Wave-2 design calls: `knowledge/research/workflow-audit-2026-07-11/AUDIT.md`.
- OW-11 archive (full record): `openspec/changes/archive/2026-07-14-skill-debloat-gates/`.
- The scaffold's own `checks.py --check test-quality` reports ~13 advisory self-findings on its own
  tests — EXPECTED, not a defect.
