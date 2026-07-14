# HANDOFF — OW-13 shipped; wave-2 remaining OW-8 → OW-12 (+ OW-15/16) (2026-07-14)

> **Read this right after `knowledge/STATUS.md`.** A session with an explicit operator autonomy grant
> shipped **`knowledge-surface-bounding-2` (OW-13, MEDIUM)** end-to-end — propose → apply → verify →
> archive, two commits on `main` (`1943929` impl, `f1dc873` archive), local & **unpushed** (push is
> operator-gated). Absorb this, pick up from **Remaining work**, and **delete this file once absorbed**.
> Its normal state is absent.
>
> **You have NO standing autonomy grant.** The prior grant was in-session only. Confirm tier+plan per
> change unless the operator re-grants autonomy.

## DONE this session — knowledge-surface-bounding-2 (OW-13, live-impactful core)
Mechanized two boot-surface bounds that AGENTS.md prose states but nothing enforced:
- **`status_lint.py` C3:** replaced the `EXEMPT_HEADINGS` frozenset with `EXEMPT_HEADING_BUDGETS`
  (dict → per-heading word budget) and added a C3 check bounding each cap-exempt STATUS section
  (current state 500 / immediate next action 550 / done 300 / pointers 200). C1/C2 unchanged.
- **`scripts/boot_surface_lint.py` (new):** sums the four mandatory boot-read files
  (`AGENTS.md` + `knowledge/STATUS.md` + `knowledge/questions/INDEX.md` + `knowledge/decisions/INDEX.md`)
  vs WARN 80KB / FAIL 100KB. Exit 0/1/2. Live-tree pytest gate asserts only `!= 2` (WARN is advisory).
- **Companion STATUS prune (orchestrator, lossless):** the `## Immediate next action` accretion
  (985→~100 words) was cut by **relocating** the shipped-but-unpropagated ledger to the NEW on-demand
  `knowledge/reference/pending-downstream-propagation.md` — moving accretion off the boot surface
  (total 80.4KB → 73.5KB, clean). **This reference doc is now the canonical home for "what scaffold
  changes shipped locally but aren't yet propagated downstream" — do NOT re-accrete it into STATUS.**
- **No spec delta** (D1) — the checks mechanize existing canonical AGENTS.md prose; round-1
  `add-status-lint` precedent + `knowledge-organization` defers numeric bounds to tooling.

## ⭐ USE these now — they govern YOUR work
- **`boot_surface_lint` is a live gate.** If your change grows the boot-read set past 80KB it WARNs
  (advisory), past 100KB it FAILs (blocks). `decisions/INDEX.md` (~27KB) is the largest single
  contributor — the OW-13(b) year-split (deferred) is its eventual pressure-relief.
- **`status_lint` C3 now word-budgets STATUS's cap-exempt sections.** At archive, keep
  `## Immediate next action` ≤550 and `## Current state` ≤500 words or the commit gate blocks.
- **Pending-propagation ledger lives in `knowledge/reference/pending-downstream-propagation.md`**, not
  STATUS. Update it (not STATUS's next-action) when a scaffold change ships-but-defers-propagation.

## HARD-WON LESSONS (carried forward — prior lessons in archived handoffs still hold)
1. **MEDIUM with NO spec delta is legitimate** when the checks mechanize existing canonical prose
   (AGENTS.md / config.yaml) rather than create a new rule — forcing a `specs/` delta would duplicate
   the canonical rule (lesson from the verify-adversarial-fixtures handoff, reconfirmed). Check the
   governing capability's intent first: `knowledge-organization` *deliberately* says bounds are
   "enforced by the project's bounds tooling … not by this spec."
2. **The "fold as much as possible" call → scope by coherence, not count.** OW-13's live-impactful
   core is (a) status_lint C3 + (c) boot_surface_lint. The no-op-on-scaffold convention parts —
   OW-13(b) decisions year-split, (d) plans-count lint — were DEFERRED (b is a from-scratch
   convention nothing exercises; d is coupled to the unexecuted `plans/plans-scope-alignment.md`).
   **OW-8 (delegation prompt-caching) and OW-12 (archive mechanization) were NOT folded** — they are
   distinct surfaces with higher blast radius / no recon; bundling them would mix unrelated
   capabilities and raise verification risk. One coherent change ships cleaner than three stapled
   together.
3. **STATUS pruning is orchestrator work, not flash-delegable, and must precede apply.** Editing
   load-bearing state is judgment-heavy (what is safely relocatable?), so the orchestrator does the
   prune + reference-doc relocation BEFORE delegating the code apply — otherwise the executor's
   `check.sh` completion gate reds on the new C3 budget. Relocate accretion to on-demand
   `knowledge/reference/` (off the boot surface) — that is the correct direction and is lossless.
4. **`checks.py --check <name>` writes `<name>.json` to CWD and it is NOT gitignored** — a
   `git add -A` trap. It slipped into the impl commit; caught and amended. Run checks from a scratch
   dir, or stage explicitly, or `git rm --cached` after.
5. **Zero Sonnet fallback again.** deepseek-pro cleanly handled propose-review (PASS/AGREE) + the
   verify pro behavioral pass (READY); deepseek-flash cleanly handled the (precise-spec) apply.
   **Archive via a Sonnet subagent** (operator-directed override of the deepseek-pro default) again
   worked cleanly when given an explicit brief: it held the ≤3 STATUS cap, respected the NEW C3
   budgets, created the follow-ons file, and correctly did NOT re-accrete the propagation ledger.
6. **boot_surface WARN is pytest-advisory-only** (live gate asserts `!= 2`), so a WARN is invisible
   under `pytest` — only a standalone run surfaces it. Follow-on: wire `boot_surface_lint` into
   `run-audit`'s reported surface (parked → `knowledge/questions/knowledge-surface-bounding-2-follow-ons.md`).
7. **`openspec validate <medium>` still errors "Unknown item"** (proposal.md-gated) on a proposal-less
   MEDIUM — expected, not a failure. Green gate = `bash scripts/check.sh` only.

## Remaining work — recommended order OW-8 → OW-12 (+ OW-15/OW-16)
- **OW-8 · Delegated-context caching hygiene · SMALL–MEDIUM. NO recon yet — do one first.** Variable-
  paths-LAST in apply/archive/reviewer prompt templates; single-source the triplicated premise prompt;
  test `OPENCODE_DISABLE_PROJECT_CONFIG=1` for executors. AUDIT finding 2. (Note: OW-13 edited no
  prompt templates, so no new cache-invalidation beyond what the prior handoff flagged.)
- **OW-12 · Archive mechanization · SMALL–MEDIUM · lowest priority · NO recon yet.** `archive_move.py`
  for the dir move; deterministic delta-applier for ADDED/REMOVED/RENAMED (LLM only for MODIFIED merge
  + reconciliation narrative). Keep the archive-executor on pro. AUDIT finding 6. NB: OW-13's archive
  again had no delta to promote, so the delta-applier half stays unexercised.
- **OW-15** (correctness-audit meta-hardening) — **BLOCKED**: amends OW-5's capability, and **OW-5 is
  still parked-at-apply**. **OW-16** (`product-audit` skill) — chain-independent greenfield, slot
  anywhere. See `OUTSTANDING-WORK.md` lines 268/330.
- **OW-13 residual follow-ons** (b year-split, budget tuning, boot_surface WARN visibility) →
  `knowledge/questions/knowledge-surface-bounding-2-follow-ons.md`; (d plans-count lint) →
  `plans/plans-scope-alignment.md`. None blocking.

## Downstream propagation — DEFERRED + operator-gated
This change edited scaffold-managed surfaces (`scripts/status_lint.py`, new
`scripts/boot_surface_lint.py`, `scripts/scaffold_manifest.txt`, `knowledge/reference/exit-codes.md`).
NOT synced to extrends/psc-monitor without fresh operator authorization. **On first sync,
extrends/psc will FAIL `boot_surface_lint`** (both are over ~100KB boot surface today — extrends
~122KB) — that is the intended signal; downstream cleanup is separate work. The running
shipped-but-unpropagated ledger is now `knowledge/reference/pending-downstream-propagation.md`.

## Low-priority wider-drift flag left for a future sweep (NOT fixed this session)
`knowledge/questions/restructure-growth-trigger.md` describes the `status_lint.py` bounds as
"≤3 STATUS sections, ≤150 words" without mentioning the new C3 per-section budgets — not wrong, just
incomplete. Low priority.

## Pointers
- Backlog + per-item STATUS: `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`.
- Wave-2 design calls: `knowledge/research/workflow-audit-2026-07-11/AUDIT.md`.
- This change (full record): `openspec/changes/archive/2026-07-14-knowledge-surface-bounding-2/`.
- The scaffold's own `checks.py --check test-quality` reports advisory self-findings on its own
  tests — EXPECTED, not a defect.
