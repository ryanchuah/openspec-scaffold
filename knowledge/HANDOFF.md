# HANDOFF — wave-2 backlog; verify-adversarial-fixtures shipped (2026-07-14)

> **Read this right after `knowledge/STATUS.md`.** A session with an explicit operator autonomy grant
> shipped **`verify-adversarial-fixtures`** (MEDIUM) end-to-end — propose → apply → verify → archive,
> two commits on `main` (`6047c96` impl, `ba6ab15` archive), local & **unpushed** (push is
> operator-gated). Absorb this, pick up from **Remaining work**, and **delete this file once the
> wave-2 batch (OW-8/13/12) is done**. Its normal state is absent.
>
> **You have NO standing autonomy grant.** The prior grant was in-session only. Confirm tier+plan per
> change unless the operator re-grants autonomy.

## DONE this session — verify-adversarial-fixtures (NOT a numbered OW item)
This change answered the operator's carried-forward question — *does the "build adversarial boundary
fixtures at verify" lesson warrant updating the scaffold's verify step?* **Yes; done.** The lesson
lived only in the (ephemeral) prior HANDOFF + one instance-scoped ratchet entry
(`detector-statemachine-boundary-flush`); it is now durable in the verify surface:
- **`openspec/config.yaml` `rules.verify` step (2)** [CANONICAL, propagated]: extended the existing
  "green is necessary but NOT sufficient" clause — for any change whose diff carries **decision logic**
  (parser / state machine / detector / validator / branch-taking transform), the self-review MUST author
  its OWN adversarial/boundary fixtures rather than trust the executor's green suite (a single blind source).
- **`.claude/skills/openspec-verify-change/SKILL.md`**: new `### Adversarial / boundary fixtures
  (self-review core)` subsection (operational how + per-code-type heuristics + war-story + distinction
  from the test-quality lens + pure-prose exemption), citing the canonical rule; plus a Step 5 pointer.
- **No spec delta** — the self-review's content is governed by `config.yaml rules.verify` + the skill,
  NOT by `verify-multimodel-gate` (whose purpose is the multi-model passes). Adding it there would
  mismatch that spec + duplicate the canonical rule. See archived `notes.md` "placement".

## ⭐ USE this now — it governs YOUR verify
At verify, when the change's diff carries decision logic, **build your OWN adversarial/boundary fixtures
and confirm behavior on them** — do not stop at the executor's green suite (see the new verify-skill
subsection). A pure-prose/config/data-free-rewiring diff is exempt: record that determination in
`notes.md` and skip. (This change dogfooded its own exemption — its diff carried no decision logic.)

## HARD-WON LESSONS (carried forward — prior lessons in the archived OW-7/10/11 handoffs still hold)
1. **MEDIUM change with NO spec delta is legitimate** when the rule's canonical home is
   `config.yaml rules.*` (or an AGENTS.md span) + skill cite. Don't force a `specs/` delta if it would
   mismatch a capability's purpose or duplicate a canonical rule — check the `knowledge/lessons.md` §2
   single-source registry first. `applyRequires` for MEDIUM is just `["tasks"]`.
2. **Verifier verdict-block adherence hiccup (monitored):** the `openspec-verifier` occasionally emits a
   terse prose summary INSTEAD of the mandated `## Verify Pass / VERDICT:` block. The
   `opencode_delegate.py` marker assertion is the working backstop (reports `status=marker-missing`); a
   single re-run with an emphatic "your FINAL message MUST be EXACTLY this block" prompt cleared it. Parked
   → `knowledge/questions/verify-adversarial-fixtures-follow-ons.md`.
3. **Bash-tool 600s ceiling < opencode's 780s review/verify budget.** Launch every delegated `opencode
   run` with `run_in_background: true` and detect completion via the EXIT-sentinel / task-completion
   notification — a foreground Bash call would be killed at 600s mid-review. (Apply's 600s budget fits,
   but backgrounding is the safe default for all of them.)
4. **`scripts/opencode_delegate.py` has no execute bit** — invoke as `/usr/bin/python3
   scripts/opencode_delegate.py …` (bare path → exit 126). Same for the other `scripts/*.py` you run.
5. **Zero Sonnet fallback again.** deepseek-flash handled the (prose) apply on a precise exact-string
   fix-spec; deepseek-pro handled propose-review + verify behavioral pass cleanly. Precise specs keep
   flash/pro viable (prior lesson holds). **Archive via a Sonnet subagent** (operator-directed override of
   the deepseek-pro default) again worked: it `mv`s the dir, reconciles all 3 trackers, applies the
   STATUS ≤3-cap, and correctly leaves the wider-drift bodies + HANDOFF for the primary.
6. **`openspec validate <medium>` is still vacuous** (proposal.md-gated) and errors "Unknown item" on a
   proposal-less MEDIUM change — expected, not a failure. Green gate = `bash scripts/check.sh` only.
   `openspec status --change <medium>` works (shows `[x] tasks`, others absent).

## Remaining work — recommended order OW-8 → OW-13 → OW-12 (+ OW-15/OW-16)
- **OW-8 · Delegated-context caching hygiene · SMALL–MEDIUM. NO recon yet — do one first** (OW-7/11
  reshaped the prompt templates, and this change edited `config.yaml rules.verify` — an AGENTS.md-adjacent
  cache-invalidation event). Variable-paths-LAST in apply/archive/reviewer templates; single-source the
  triplicated premise prompt; test `OPENCODE_DISABLE_PROJECT_CONFIG=1` for executors. AUDIT finding 2.
- **OW-13 · Knowledge-surface bounding round 2 · SMALL. RECON DONE →**
  `openspec/changes/archive/2026-07-14-knowledge-surface-bounding-2/recon-ow13.md` (tracked; now archived).
  New `boot_surface_lint.py` + test + manifest entry. Key: year-split + plans-count lints are NO-OPS on
  the scaffold — build/test via fixtures. **Re-measure STATUS "Immediate next action" word budget** (it was
  rewritten again this session). Self-contained, low-risk.
- **OW-12 · Archive mechanization · SMALL–MEDIUM · lowest priority · NO recon yet.** `archive_move.py` for
  the dir move; deterministic delta-applier for ADDED/REMOVED/RENAMED (LLM only for MODIFIED merge +
  reconciliation narrative). Keep the archive-executor on pro. AUDIT finding 6. NB: this session's archive
  had no delta to promote, so it exercised only the move+reconcile half by hand.
- **OW-15** (correctness-audit meta-hardening) — **BLOCKED**: it amends OW-5's capability, and **OW-5 is
  still parked-at-apply**. Cannot start until OW-5 ships. **OW-16** (`product-audit` skill) —
  chain-independent greenfield, slot anywhere. See `OUTSTANDING-WORK.md` lines 268/330.

## Downstream propagation — DEFERRED + operator-gated
This change edited scaffold-managed + propagated surfaces: the `rules:` block of `openspec/config.yaml`
and `.claude/skills/openspec-verify-change/SKILL.md`. NOT synced to extrends/psc-monitor without fresh
operator authorization (joins the standing deferred-propagation list in STATUS).

## Pointers
- Backlog + per-item STATUS: `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`.
- Wave-2 design calls: `knowledge/research/workflow-audit-2026-07-11/AUDIT.md`.
- This change (full record): `openspec/changes/archive/2026-07-14-verify-adversarial-fixtures/`.
- OW-11 (spec-delta-structure detector + model-id-agreement lint — USE these):
  `openspec/changes/archive/2026-07-14-skill-debloat-gates/`.
- The scaffold's own `checks.py --check test-quality` reports ~13 advisory self-findings on its own
  tests — EXPECTED, not a defect.
