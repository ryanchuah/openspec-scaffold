# HANDOFF — wave-2 backlog, mid-batch (2026-07-13)

> **Read this right after `knowledge/STATUS.md`.** A prior session (operator-granted autonomy)
> worked the wave-2 backlog and shipped 4 of 10 items, then split the rest to a new session by
> design (operator said "fold in as much as you can; if too much, split with a handoff"). Absorb
> this, continue from **Remaining work** below, and **delete this file once the whole wave-2 batch
> (OW-7/8/10/11/12/13) is done**. Its normal state is absent.
>
> **You still hold the autonomy grant's intent for this batch is NOT automatic** — a new session has
> no standing grant. Confirm the tier+plan with the operator per change unless they re-grant autonomy.
> (The 4 shipped items were done under an explicit in-session grant.)

## Single source of truth for the backlog
- `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` — OW numbering, routing, order.
- `knowledge/research/workflow-audit-2026-07-11/AUDIT.md` — the wave-2 design calls are **pre-made
  inline** (findings 1-7 + addendum). Everything remaining is **Opus end-to-end** (apply delegated).

## DONE this session (4 of 10) — all shipped + archived, all gates green, no Sonnet fallback
| OW | change (archive dir) | commits |
|----|----------------------|---------|
| OW-9 + OW-14 | instruction-surface-coherence | 47161da (impl) + dfe6f90 (archive) |
| OW-1 + OW-4 | defect-prevention-detectors | e90961a (impl) + 6d8024c (archive) |

Batching decision: two tightly-coupled pairs merged (design pairs them). Both OW numbers cited in
each change's notes.md for traceability. Spec deltas promoted: `tier-confirmation-gate` (+autonomy
phase-advance), NEW `defect-prevention-detectors`, MODIFIED `verify-multimodel-gate`.

## Remaining work (6 items) — recommended order: OW-7 → OW-10 → OW-11 → OW-8 → OW-13 → OW-12
Sequencing note from OUTSTANDING-WORK: OW-7/9/11/14 edit the verify/apply/archive/delegation-harness
skill files. OW-9 + OW-14 already landed there cleanly. **OW-11 edits the SAME verify skill** that
OW-1/OW-4 (lens wiring) and OW-9/OW-14 (phase gates, cues) touched — re-read the current skill before
planning OW-11; anchors have shifted.

- **OW-7 · Delegation wrapper + run-telemetry ledger · MEDIUM.** `scripts/opencode_delegate.py`
  mechanizing the hand-rolled `opencode run` post-processing (timeout, fallback-grep, jq extraction,
  marker assert, EXIT-sentinel, exit-code interpretation) now duplicated across 6 skills, + a one-line
  JSONL ledger per run to `output/delegation-log.jsonl` (agent, model, phase, change, duration, exit,
  fallback?, verdict, retry#). Telemetry feeds two scheduled decisions (premise-gate downgrade at ~50
  reviews; MEDIUM pro-pass downgrade at ~20 verifies — AUDIT.md §"how many verify reviewers"). Design
  in AUDIT.md finding 1 + §deterministic-script. This is the one that removes the most toil — do first.
- **OW-10 · Apply-executor throughput + resume contract · MEDIUM.** Green path = targeted tests per
  task + full suite once per slice (today: full suite after EVERY task → binds the 600s ceiling);
  retry/fresh-executor brief gains the explicit resume contract (skip `[x]`, resume at first `[ ]`,
  reconcile the half-edited in-flight task) + distilled-state carry-forward. Edits the apply skill.
  AUDIT.md finding 4.
- **OW-11 · Skill de-bloat + mechanized gates · MEDIUM.** Replace verify steps 12-16 with
  deterministic CLI coverage + a short coherence note; `freeze-check` script (parse review verdict →
  FREEZE-OK/BLOCKED); `notes_lint.py` five-field gate; explore→propose slug-match warning; run the two
  COMPLEX verifier passes concurrently; model-ID agreement lint (`deepseek-v4` hardcoded 44×/13 files,
  no guard). AUDIT.md finding 5. **Fold in the ratchet item `medium-change-spec-delta-unvalidated`**
  (in `knowledge/ratchet-log.md`, open:since 2026-07-13): a check that discovers changes by DIR and
  structurally validates their spec deltas — MEDIUM changes are invisible to `openspec validate`.
- **OW-8 · Delegated-context caching hygiene · SMALL.** Variable-paths-last in apply/archive/reviewer
  prompt templates; single-source the triplicated premise prompt (explore/propose/AGENTS.md SMALL
  bullet); test `OPENCODE_DISABLE_PROJECT_CONFIG=1` for executors (verify no agent.md depends on
  AGENTS.md); treat AGENTS.md edits as cache-invalidation events. AUDIT.md finding 2 + §caching.
- **OW-13 · Knowledge-surface bounding round 2 · SMALL.** `status_lint` word-budgets for currently-
  exempt sections; bound `knowledge/decisions/INDEX.md` (year-split); a deterministic `boot_surface`
  byte-budget check (warn ~80KB / fail ~100KB). AUDIT.md finding 7 + addendum. Self-contained — good
  low-risk warmup.
- **OW-12 · Archive mechanization · SMALL-MEDIUM · lowest priority.** `archive_move.py` for the dir
  move; deterministic delta-applier for ADDED/REMOVED/RENAMED (LLM only for MODIFIED merge +
  reconciliation narrative). Keep the executor on pro. AUDIT.md finding 6.

Late additions (chain-independent, slot anywhere): **OW-15** (correctness-audit meta-hardening — amends
OW-5, now shipped) and **OW-16** (product-audit skill) — see roadmap.md + OUTSTANDING-WORK.md.

## HARD-WON PROCESS LESSONS (make the next session faster — these cost real time to learn)
1. **opencode delegations MUST run `run_in_background: true`.** The Bash tool's default timeout is
   120s but opencode budgets are 600-780s → a foreground call gets SIGTERM'd mid-run at 120s. Always:
   background + append `; echo "EXIT=$?" > /tmp/<phase>-out.exit` + wait for the completion
   notification, then extract with `grep '"type":"text"' out.jsonl | tail -1 | jq -r '.part.text'`.
2. **`openspec validate <medium-change> --strict` is VACUOUS** — prints "Unknown item", exits 0 (it
   discovers changes via proposal.md; MEDIUM has none). Green gate = `bash scripts/check.sh` ONLY.
   BUT spec deltas DO get validated after promotion at archive (the main spec is validator-visible) —
   so ensure each requirement's normative **SHALL is on its FIRST physical line** BEFORE archive, or
   the archive-executor's `openspec validate <capability> --strict` fails. (Now tracked as ratchet
   `medium-change-spec-delta-unvalidated`, → OW-11.)
3. **Interpreter:** `python`/`python3 -m pytest` is NOT available bare (no pytest in system python).
   `bash scripts/check.sh` resolves it (test-cmd = `pytest -q`). For a one-off detector run use
   `/usr/bin/python3 scripts/checks.py ...` (works; just no pytest).
4. **The pro review earns its cost on code-heavy changes** — it caught 2 real silent-bug dispatch-
   contract issues in Change 2 (wrong `checks.py` builtin-dispatch path; missing `findings` key) that
   green tests would have hidden. Budget for 2-3 review rounds; a 🔴 mandates a re-review round (max 3).
5. **At verify, independently EXERCISE code changes** — build your own fixtures and run the real code;
   do NOT trust the executor's green tests (self-consistent-but-wrong is the classic trap; maximally
   ironic for the test-quality detector, which is why it got hand-fixtures). This caught a real
   hidden-dir scoping defect the tests missed.
6. **Apply routing:** deepseek-flash (default) worked cleanly on a *precise* tasks.md (Change 2's AST
   detectors). Sonnet-first is worth pre-routing for prose-surgery (Change 1) — record the pre-route in
   notes.md (the `sonnet-first-pre-route` decision, now canonical). A precise spec is what makes
   deepseek-flash viable.
7. **checks.py detector architecture** (for OW-7/OW-11 if they touch it): registry = dicts in
   `_REGISTRY`; in-process builtins register in `_BUILTIN_RUNNERS` + `_PARSERS` (value must be
   CALLABLE — `lambda _stdout: []`) + special-case `_availability_for_check` (always-available). Adding
   a registry entry REQUIRES updating `test_checks.py` `ListModeTest.expected_names` + `AutodetectTest`
   + `SummaryLineFormatTest`. checks.py findings are ADVISORY (don't fail check.sh).
8. **Archive-executor (deepseek-pro) is reliable** — handled a single ADDED delta and a
   NEW-capability+MODIFIED two-delta sync cleanly. It uses plain `mv` (not `git mv`), so stage the
   move with `git add -A <old-dir> <new-archive-dir>`. Its wider-drift sweep is flag-only (it flagged
   roadmap/OUTSTANDING staleness — reconcile those yourself; see below).
9. **Commit rhythm:** two commits per change — "Implement …" then "Archive … and reconcile project
   docs". Commit to `main` directly (project convention). Push stays operator-gated (NOT done).
10. **Downstream propagation of ALL 4 shipped changes is DEFERRED + operator-gated** (scaffold-managed
    files edited: AGENTS.md spans, 6 skills, delegation-harness, checks.py, test_checks.py,
    repo_lint.py). Arrives INERT-ish downstream (the detectors are new advisory checks; per-repo
    checks.toml can disable). Not synced without fresh operator authorization.

## Session-end reconciliation status
- The 3 core trackers (STATUS / decisions / questions) were reconciled by each archive. STATUS holds
  the 2 latest changes; 3-section cap maintained.
- roadmap.md + OUTSTANDING-WORK.md + lesson-check-ratchet-follow-ons.md batch-reconciled for OW-9/14/1/4
  at session end (marking them SHIPPED) — see the "reconcile project docs" state at HEAD.
- ratchet-log.md +2 this session: `medium-change-spec-delta-unvalidated` (→OW-11),
  `detector-filewalker-scans-hidden-dirs` (frozen test).

## Pointers
- Design sources: AUDIT.md (wave-2), OUTSTANDING-WORK.md (backlog), SYNTHESIS.md (wave-1 evidence).
- The scaffold's own `checks.py --check test-quality` reports 13 advisory self-findings (7
  discarded-return, 6 unfrozen-clock) — EXPECTED (advisory rules on the scaffold's own tests), not a
  defect; audit-triage material, not a blocker.
