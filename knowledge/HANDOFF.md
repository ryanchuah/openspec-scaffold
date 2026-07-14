# HANDOFF — OW-8 (delegated-context-caching) shipped; wave-2 remaining OW-12 (+ OW-15/16) (2026-07-14)

> **Read this right after `knowledge/STATUS.md`.** A session with an explicit operator autonomy grant
> shipped **`delegated-context-caching` (OW-8, SMALL)** end-to-end — plan → premise → apply → verify →
> archive, three commits on `main` (impl, archive, handoff), local & **unpushed** (push is
> operator-gated). Absorb this, pick up from **Remaining work**, and **delete this file once absorbed**.
> Its normal state is absent.
>
> **You have NO standing autonomy grant.** The prior grant was in-session only. Confirm tier+plan per
> change unless the operator re-grants autonomy.

## DONE this session — delegated-context-caching (OW-8)
OW-8 was "Delegated-context caching hygiene" with four sub-parts. Shipped **A + D**; deferred **B**
(blocked); dropped **C** (over-engineering). SMALL, no spec delta, doc/prompt-only (no code).
- **A — variable-paths-LAST reshape** of the 4 delegated `opencode run` prompt strings (apply-executor,
  archive-executor, propose openspec-reviewer base, AGENTS.md SMALL-premise reviewer). Fixed
  instructions first, per-change variable paths bound at the tail → the byte-identical instruction body
  becomes a DeepSeek prefix-cache-eligible shared prefix. Behavior-preserving; all wrapper-asserted
  markers preserved. The verifier prompts were already the ideal shape (no inlined path) — the reference.
- **D — convention + durable finding.** (d1) New `delegation-harness.md` **§(g) "Prompt-template shape
  — variable content last"** codifies the rule so future prompt edits preserve it (prose-is-write-only-
  memory mitigation). (d2) AGENTS.md stability preamble gained a tight **batch-AGENTS.md-edits** note.
  (d3) B-finding recorded durably (archived `notes.md` + decisions entry + follow-on).

## ⭐ USE these now — they govern YOUR work
- **`delegation-harness.md` §(g) is a live convention.** Any new/edited delegated `opencode run` prompt
  MUST put per-change variables (paths/names/flags) at the TAIL and preserve its wrapper-asserted
  markers (`### Premise Verdict`/`PREMISE:`, `## Verify Pass`/`VERDICT:`/`### Defects`). Review-enforced
  (no lint — the variable-vs-illustrative-placeholder distinction is too fuzzy to detect reliably).
- **AGENTS.md is injected into every delegated executor and CANNOT be surgically stripped** (see below).
  So **batch AGENTS.md edits** — each one resets the DeepSeek prefix cache for all delegated agents.

## ⭐⭐ B-BLOCKED — do NOT re-attempt without a new opencode mechanism (reproducible proof)
The analysis's biggest lever — strip the ~7.2k-token, high-churn, orchestrator-voice AGENTS.md
injection from sub-executors via `OPENCODE_DISABLE_PROJECT_CONFIG=1` — is **blocked in opencode
v1.17.18**: that env var ALSO disables `.opencode/agents/` discovery. Proof (zero model cost):
`OPENCODE_DISABLE_PROJECT_CONFIG=1 opencode agent list` → **0** project agents (only built-ins);
plain `opencode agent list` → all 5 present. So setting it would silently swap `--agent apply-executor`
for a built-in default (right model, WRONG role) — the exact silent-fallback footgun. No per-agent
instruction-scoping opt-out exists in the schema. **Revisit only if** opencode adds a targeted
per-agent instruction-scoping mechanism, or AGENTS.md is deliberately split; re-test on any opencode
major-version bump. Full evidence: archived `notes.md`; trigger: `knowledge/questions/delegated-context-caching-follow-ons.md`.

## HARD-WON LESSONS (carried forward — prior lessons in archived handoffs still hold)
1. **"Fold as much as possible" = scope by coherence AND by what survives recon, not by count.** OW-8's
   4 sub-parts collapsed to 2 shippable (A+D) once recon proved B blocked and C over-engineering. The
   honest, correct scope was NOT padded to look bigger — the highest-value output was arguably the
   *recon finding* (B is definitively blocked), which saves every future agent from re-attempting it.
   Don't fold OW-12/OW-16 in — different surfaces, higher blast radius (handoff-lesson carried).
2. **Test the "just try X" backlog hypotheses cheaply before building on them.** `opencode agent list`
   with/without the env var settled B in two commands — no model spend, no guesswork. When a backlog
   item says "test env var Y", the binary + a dry CLI subcommand often answer it for free.
3. **Doc/prompt-only SMALL changes: the primary applies directly** (disclosed deviation from the
   flash-delegate default). AGENTS.md's "quick doc edits done by the primary; do not over-delegate
   trivia" governs when there's no implementation code and exact target strings are pre-authored — more
   reliable for load-bearing prose, and avoids the `.claude/worktrees/analyze/` stale-copy footgun.
4. **`scripts/opencode_delegate.py` is NOT executable in a fresh checkout** — invoke `python3
   scripts/opencode_delegate.py …`, not `scripts/opencode_delegate.py …` (the latter → "Permission
   denied", exit 126). The AGENTS.md/skill examples show the bare form; prefix `python3`.
5. **Zero Sonnet fallback again.** deepseek-flash cleanly handled both the SMALL premise pass (AGREE,
   validated the B-defer/C-drop judgment calls independently) and the verify behavioral pass (READY,
   zero defects, produced a real side-by-side semantic-equivalence table — not a rubber stamp).
   **Archive via a Sonnet subagent** (operator-directed) worked cleanly: held the ≤3 STATUS cap,
   respected C3 budgets + boot_surface, created the follow-on body, and even caught a pre-existing
   OW-13 self-consistency gap in OUTSTANDING-WORK (flagged + fixed).
6. **Two `knowledge/reference` reconciliations the archive brief must name** (I had to add them post-
   archive): the **pending-propagation ledger** (`knowledge/reference/pending-downstream-propagation.md`)
   needs an entry for any scaffold-managed edit, and the **roadmap** wave-status line goes stale. Put
   both in the archive-executor brief next time.

## Remaining work — OW-12 (+ OW-15 / OW-16)
- **OW-12 · Archive mechanization · SMALL–MEDIUM · lowest priority · NO recon yet.** `archive_move.py`
  for the dir move; deterministic delta-applier for ADDED/REMOVED/RENAMED (LLM only for MODIFIED merge
  + reconciliation narrative). Keep the archive-executor on pro. AUDIT finding 6.
- **OW-15** (correctness-audit meta-hardening) — **BLOCKED**: amends OW-5's capability, and **OW-5 is
  still parked-at-apply**. **OW-16** (`product-audit` skill) — chain-independent greenfield, slot
  anywhere. See `OUTSTANDING-WORK.md` lines ~268/330.
- **OW-11's fuzzy de-bloat half** remains parked (`knowledge/questions/skill-debloat-gates-follow-ons.md`).
- **OW-8 residual follow-ons** → `knowledge/questions/delegated-context-caching-follow-ons.md` (B revisit
  trigger; the C-drop premise-marker lint idea). None blocking.

## Downstream propagation — DEFERRED + operator-gated
This change edited scaffold-managed surfaces: AGENTS.md shared span (stability note + SMALL-premise
prompt reshape), the 3 delegating skills (apply/archive/propose prompt reshapes), and
`_shared/delegation-harness.md` (new §(g)). NOT synced to extrends/psc-monitor without fresh operator
authorization. Unlike knowledge-surface-bounding-2, these are behavior-preserving prompt reshapes + doc
conventions — **no new lint failures expected downstream**. Running ledger:
`knowledge/reference/pending-downstream-propagation.md`.

## Pointers
- Backlog + per-item STATUS: `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`.
- Wave-2 design calls + caching analysis: `knowledge/research/workflow-audit-2026-07-11/` (`AUDIT.md`,
  `caching-analysis.md` — the latter is the OW-8 source; its items #1 (var-last) and #3-batch shipped
  here, #2/#3-boot shipped in OW-13, #4 (AGENTS.md scoping) = the blocked B).
- This change (full record incl. B-evidence): `openspec/changes/archive/2026-07-14-delegated-context-caching/`.
