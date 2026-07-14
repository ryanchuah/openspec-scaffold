# HANDOFF — OW-12 (archive-mechanization) shipped; only OW-11 residual remains (2026-07-14)

> **Read this right after `knowledge/STATUS.md`.** A session shipped **`archive-mechanization` (OW-12,
> COMPLEX)** end-to-end — explore(+direction gate) → propose → apply → verify → archive, committed on
> `main`, local & **unpushed** (push is operator-gated). Downstream propagation is **DEFERRED +
> operator-gated**. Absorb this, pick up from **Remaining work**, and **delete this file once absorbed**
> (its normal state is absent).
>
> **You have NO standing autonomy grant.** Confirm tier+plan per change unless the operator re-grants
> autonomy. (This session HAD an explicit grant; it does not carry over.)

## DONE this session — archive-mechanization (OW-12)
The last item on the scaffold-hardening backlog. The archive phase's mechanical work is now
deterministic scripts instead of LLM prose: **`scripts/apply_delta_spec.py`** promotes
ADDED/REMOVED/RENAMED spec-delta operations into canonical main specs (plan-all-in-memory,
write-all-or-nothing — any anomaly halts and writes nothing; MODIFIED always deferred to the LLM;
a per-op skip/anomaly/apply truth table where an already-achieved end-state is a *skip* and a
would-write-wrong/ambiguous op is an *anomaly*), and **`scripts/archive_move.py`** does the
conflict-guarded dir move. The archive/sync-specs skills + BOTH `archive-executor.md` bodies were
rewired to **promote-then-move**, reserving the LLM for MODIFIED merges + doc reconciliation. New
`archive-mechanization` capability spec (all ADDED). **BREAKING (safety):** an ADDED name-collision
is no longer a silent overwrite — byte-equal → skip, differing → anomaly. **Dogfooded on its own
archive** — the promoter created `openspec/specs/archive-mechanization/spec.md` from this change's own
delta, zero anomalies. Full record: decisions → `knowledge/decisions/INDEX.md` (`archive-mechanization`);
follow-ons → `knowledge/questions/archive-mechanization-follow-ons.md`; archive →
`openspec/changes/archive/2026-07-14-archive-mechanization/`.

Verify: premise AGREE at both altitudes (direction gate + proposal); **self-review's 16 orchestrator
adversarial fixtures caught 3 real product defects** (see lesson 2); pro behavioral pass READY, flash
test-quality lens READY, simplicity gate PASS; `check.sh` + `scaffold_lint` + `validate --strict`
clean; **zero Sonnet fallback on apply**.

## Hard-won lessons (process — carried forward)
1. **Apply-split worked a 3rd time (re-confirmed).** Orchestrator authored the fence-heavy
   skill/executor prose (byte-identical executor bodies) and checked those boxes `[x]` BEFORE
   delegating; flash did the deterministic Python (scripts + tests + manifest). Zero flash fallback.
   Keep splitting mixed prose+code applies this way.
2. **Orchestrator adversarial fixtures at verify EARNED their keep — hard.** On a parse→transform→
   rewrite tool, the flash executor's green op-level tests ("did it apply the op?") missed **3 real
   defects**: a planning branch missed a case (new-capability ADDED self-collision → duplicate
   requirement), and reconstruction corrupted the doc (blank-line drift → `\n\n\n`; a trailing `## `
   section reordered ahead of the requirements — silent canonical-spec corruption). My property/
   invariant fixtures (no-triple-blank, trailing-section-order, promote-twice-idempotency,
   all-or-nothing-atomicity) caught all 3; re-delegated the fix TDD-style (make the fixtures green),
   zero Sonnet fallback. **Lesson for any doc-rewrite/parser tool: write reconstruction-fidelity +
   ordering + idempotency + branch-parity property tests, not just "did it apply" unit tests.** Routed
   to `knowledge/ratchet-log.md` (`doc-rewrite-tool-reconstruction-fidelity`).
3. **The flash test-quality lens caught 2 weaknesses in MY OWN fixtures** (two tests discarded
   `_run()`'s exit code → a spurious anomaly-exit could pass by accident). The lens works even on
   orchestrator-authored fixtures. **Capture BOTH the exit code AND the file/report state in every
   fixture.**
4. **The pro-verifier emitted normal output this session** — the prior HANDOFF's zero-output pro-verifier
   was NOT a persistent degradation. Don't preemptively skip or down-tier the pro pass.
5. **`checks.py --check <name>` STILL litters cwd** (the lens run dropped `test-quality.json` at the
   repo root; I cleaned it before commit). Same wart as the prior HANDOFF's lesson #3 — still unfixed.
   Candidate tiny follow-on: default `--check` output under `output/`, or gitignore root `/*.json`.

## Remaining work — OW-11 residual ONLY (the entire scaffold tail)
- **OW-11 residual (fuzzy de-bloat half)** → `knowledge/questions/skill-debloat-gates-follow-ons.md`:
  replace verify steps 12–16 with deterministic CLI coverage + a coherence note (highest-risk — needs
  a design call, since `openspec status --json` is artifact-level not requirement-level); a
  `notes_lint.py` five-field gate; a `freeze-check` script (needs a companion `FREEZE:` token added to
  the review prompt first); trim explore's gallery prose. Independent; nothing blocks on them.
- **After OW-11 residual, the scaffold-hardening backlog is EMPTY.** The 2026-07-11 workflow-audit
  verdict stands (`knowledge/research/workflow-audit-2026-07-11/AUDIT.md`): scaffold optimization is at
  diminishing returns — future sessions should **spend downstream** (extrends' ~33 open
  correctness-audit defect classes, ZERO remediation shipped) rather than new scaffold mechanism.

## Downstream propagation — DEFERRED + operator-gated
OW-12 edited scaffold-managed surfaces: 2 new scripts (`apply_delta_spec.py`, `archive_move.py`) + 3
new test files, `scaffold_manifest.txt`, both skills (`openspec-sync-specs`, `openspec-archive-change`),
both `archive-executor.md` bodies. The `archive-mechanization` capability spec is golden-source-only
(never synced). **Coupling note:** the rewired skills/executors reference the new scripts, and those
scripts are in the manifest, so a sync delivers both together — no broken reference. Stdlib-only, no
new downstream lint/test failures expected on first sync. NOT synced to extrends/psc-monitor without
fresh operator authorization. Running ledger: `knowledge/reference/pending-downstream-propagation.md`.

## Pointers
- Backlog + per-item STATUS: `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`
  (OW-12 now SHIPPED; only OW-11 residual left).
- OW-11 residual: `knowledge/questions/skill-debloat-gates-follow-ons.md`.
- This change (full record): `openspec/changes/archive/2026-07-14-archive-mechanization/`.
- OW-12 follow-ons: `knowledge/questions/archive-mechanization-follow-ons.md`.
