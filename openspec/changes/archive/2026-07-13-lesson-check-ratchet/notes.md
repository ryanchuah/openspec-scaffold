# notes — lesson-check-ratchet

Change-local scratch log. Newest entries last.

## 2026-07-10 — session 1 (Fable orchestrating explore+propose; pause at apply per operator)

**Operator instructions of record:** work OW-2 assuming OW-1 is NOT a prerequisite; Fable
does the judgment-heavy explore/propose; PAUSE at apply and report (a) park vs proceed
relative to OW-3, (b) whether apply/verify orchestration should be Fable or Opus; keep
`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` updated at phase
boundaries.

**Explore:** brief written, direction gate ran clean (deepseek-v4-pro, no fallback,
`PREMISE: AGREE`, zero 🔴). Full text in `review-log.md` Round 1. Carried into design:
- 🟡 waiver staleness → dispositions get a re-review trigger; lint flags stale waivers.
- 🟡 frozen-test linkage must be VERIFIED (pointer→artifact existence cross-check, the
  `budget-agreement` shape), never declarative-only.
- 🟡 code-shape detectors have a different cost profile than SQL data-lint → own
  timeout/perf model.
- 💡 disposition preference ordering (check > frozen test > waiver) — otherwise
  cheapest-disposition wins by default.
- 💡 `grandfathered` disposition for legacy lessons (distinguish "reviewed+deferred" from
  "never triaged").
- 💡 self-referential bootstrap: the ledger format's own lint check is itself a ledger entry.
- 💡 state downstream-adoption risk explicitly (done in proposal Impact).

**Load-bearing constraint discovered at propose:** `openspec/config.yaml` context pins
scaffold scripts to **Python 3.13 stdlib-only, no third-party runtime deps** → the shipped
invariant runner must be bespoke stdlib (`ast`/regex per-file checks); semgrep/ast-grep can
only ever be optional per-repo `[checks.custom.*]` tenants, never a scaffold dependency.

**Prior-art digest (subagent, checkpointed at `research/prior-art-digest.md`):**
- mechanize-invariants (2026-07-02) = 4 one-off prose→lint conversions; no general closure
  policy existed. This change generalizes that move.
- Locked conventions to respect: D3 check-only; D4 flat-dir/one-file-one-invariant/
  zero-rows-pass/~5-per-repo-grown-from-incidents; D7 scaffold-ships-framework,
  per-repo wiring = downstream SMALL changes; upstream parser surface stays limited;
  `scaffold_lint.py` stays golden-source-only (so ratchet lint enforcement goes in
  `knowledge_lint.py`, which DOES propagate).
- Ledger home: `knowledge/` registry-file shape (like `audit-log.md`), lint-first format,
  per-repo content, NOT structured fields inside `lessons.md` (lessons stay narrative).
- YAGNI reconciliation framing: prior "deferred until the rake recurs" calls ARE
  waiver-with-trigger dispositions, formalized.

**Tooling research (subagent, checkpointed at `research/tooling-research.md`):**
- ruff custom rules: verified NO (astral-sh/ruff#283 still open, FAQ confirms, 2026-05).
- semgrep CE: heavyweight (~100-200MB class), enterprise adopters, rules-registry license
  churn 2024 (engine LGPL unaffected); opengrep = consortium fork, binary, young.
- ast-grep: single Rust binary, lightest, YAML rules, thinner enterprise trail.
- Industry precedent for the ratchet process itself: Google Error Prone ("eliminate classes
  of serious bugs"), Tricorder ICSE'15 admission criteria (near-zero FP, actionable),
  SWE-at-Google ch.20. Use in design.md rationale.
- Verbatim "worth fixing → worth checking forever" quote: UNVERIFIED, do not cite as quote.

**Propose:** proposal.md written; pro review round dispatched (premise verdict + D10 drift
vs explore-brief). Capabilities: NEW `finding-closure-ratchet`, NEW `repo-invariant-checks`;
no modified capabilities (precedent: outstanding-work-view owns its own knowledge_lint
checks in its own spec).

**Propose COMPLETE (2026-07-10, same session):** 4/4 artifacts frozen. Five pro review
rounds total (direction gate, proposal+premise, design, specs, tasks) — zero 🔴 in any; all
🟡 fixed pre-freeze (see review-log.md dispositions). Notable frozen decisions: five
dispositions (check/test/waiver/open/grandfathered) with preference ordering and
configurable open-age flag; ledger at `knowledge/ratchet-log.md` (CANONICAL_MAP +
EPHEMERAL_PATHS); subprocess-per-check stdlib runner `scripts/repo_lint.py` over
`checks/*.py`; data-lint-pattern registration in checks.py incl. `_autodetect_defaults()`;
triage step placement pinned in both skills. PAUSED AT APPLY per operator instruction —
park/orchestrator verdicts recorded in
`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` (park; Opus, with
design-defect escalation caveat). Next session: `apply lesson-check-ratchet` under an Opus
orchestrator (deepseek-flash executor per the apply skill), then verify (COMPLEX: self →
pro → flash multi-model chain + simplicity gate; security gate n/a — no auth/credential/
external-API surface), then archive.

## 2026-07-13 — session 2 (Opus orchestrating apply→verify→archive)

**Pre-apply fix (disclosed in review-log.md):** `openspec validate --strict` failed on the
`generalizable-findings-close-only-with-a-recorded-disposition` requirement — root cause is
openspec's parser reading only a requirement's FIRST physical line as its `text`; SHALL sat on
line 2. Reordered so SHALL leads line 1, meaning preserved. Now validates clean.

**Apply:** deepseek-v4-flash executor via `opencode run`, one clean pass, no fallback, 14/14
tasks checked. Completion report clean; the "### NON-CONVERGENCE BLOCKER" jsonl grep match was
a false positive (executor echoing the apply-SKILL.md failure-mode docs, not a real blocker).

**Verify — orchestrator self-review (COMPLEX, pre-OW-3 semantics: self→pro→flash + simplicity):**
- Green gate (`scripts/check.sh`): ruff + format + full pytest all pass (incl. live-tree lint
  gate over the real bootstrapped `knowledge/ratchet-log.md` and scaffold_lint SEAL with manifest
  additions). Bootstrap pointer liveness thereby proven against the real tree.
- Read `repo_lint.py` (faithful: subprocess-per-check, exit 0/2/3, first-infra-fail stop, atomic
  JSON, D3/D4 docstring), `_check_ratchet_log`/`_validate_pointer`/`_validate_date` (digit-date
  anchor skips the `YYYY-MM-DD` header example; `::name` conditional; `calendar.monthrange`
  rejects `2026-13-01`), `checks.py` `_run_delegate` (mirrors data-lint, >1-paths INFRA-FAIL,
  rc→status map). `checks.py --list` shows `repo-lint … available`.
- Live smoke (design Verification item 6): toy `os.system(` invariant + synthetic offender in an
  isolated scratch tree → `repo_lint.py` exit 2, 1 finding, correct path/line/message, JSON
  schema matches design.
- **Self-review defect fixed inline (trivial formatting, disclosed here):** the executor
  re-indented the archive-skill Step 6 "Fix trivial issues"/"Lint before committing" sub-steps
  from 3→4 spaces and added "Ratchet triage" at 4 spaces, mis-nesting three peer sub-steps one
  level deep (peer level is 3 spaces, per "Read back"/"Quality check"/"Commit once satisfied").
  Normalized all three back to 3-space markers / 5-space continuations. Cosmetic-only; no test
  asserts on skill-md list indentation, but it is a propagated, agent-read file.

### Verify checkpoint (mandatory 5 fields + archive handoff)

**1. Verdict:** READY for archive. COMPLEX change, verified under pre-OW-3 semantics
(self → pro → flash + simplicity gate; security gate n/a). Both delegated verifier passes
returned `VERDICT: READY` with `- None` defects (no fallback; real agents ran). `openspec
validate --strict` clean; 14/14 tasks; all 8 spec requirements (4 finding-closure-ratchet +
4 repo-invariant-checks) mapped to implementation.

**2. Live output eyeballed (behavior, not counts):** Ran `repo_lint.py` against an isolated
scratch tree holding a toy `os.system(`-detector `checks/*.py` + a synthetic offender →
runner exited findings-status and emitted one finding naming the offender's path/line/message,
with the JSON artifact carrying `generated_by` + per-check `{name,status,findings,sample}`.
`checks.py --list` surfaced `repo-lint` as an available floor/delegate/check. `knowledge_lint`
ran clean over the real bootstrapped `knowledge/ratchet-log.md` — the three bootstrap pointers
(`_check_ratchet_log`, `scaffold_lint.py::budget-agreement`,
`test_repo_lint.py::test_stops_on_first_infra_failure`) all resolved live via the pytest
live-tree gate. No external-API surface, so no live smoke (not a skipped smoke — none exists).

**3. Defects found + how fixed (attributed):** All fixed inline by the primary (Opus); NO
deepseek/Sonnet fix re-delegation was needed anywhere in this change.
  - *Pre-apply (validation):* `openspec validate --strict` failed the
    `generalizable-findings-close-only-...` requirement — root cause is openspec parsing a
    requirement's `text` as only its FIRST physical line; SHALL sat on line 2. Reordered so SHALL
    leads line 1, meaning preserved. Disclosed in review-log.md.
  - *Self-review:* archive-skill Step 6 mis-indentation (executor shifted "Fix trivial"/"Lint"
    sub-steps 3→4 spaces, mis-nesting 3 peer sub-steps). Normalized to 3-space markers.
  - *Simplicity gate (4 cleanup agents converged):* removed the unused/misleading dead constant
    `_RATCHET_POINTER_RE` (knowledge_lint.py). Re-ran green gate after — still green.

**4. As-built deltas not already in the artifacts:**
  - The ledger's spec-citation line in `knowledge/ratchet-log.md` carries a `<!-- lint:planned -->`
    marker because the delta specs are not yet promoted into `openspec/specs/`. Once archive
    promotes them, that citation resolves — the marker should be REMOVED at/after archive (else it
    hides a now-valid citation). Flagged under "Still owned by archive".
  - No other behavioral as-built delta; implementation matches design D1–D6.

**5. Forward-looking items recorded nowhere else (fold into knowledge/questions at archive):**
  a. **Design deferral (design.md Open Questions):** whether `outstanding.py` should also surface
     `open:` ratchet entries in the outstanding-work snapshot — wait for real usage; the 30-day
     lint age-flag covers rot meanwhile.
  b. **Design deferral (design.md Open Questions):** whether OW-1's test-quality detector ships as
     `checks/*.py` tenants or a built-in — to be decided in OW-1, not here.
  c. **Code-quality follow-on (NEW, from the simplicity gate — behavior-preserving, non-blocking):**
     inside `knowledge_lint.py`, four cleanups were surfaced by 3–4 agents and deliberately parked
     (not done mid-verify to avoid deviating from the frozen design / regressing message-asserting
     tests): (i) `_validate_date` re-implements calendar validity with `_ISO_DATE_RE` +
     `calendar.monthrange` and the waiver/open branches re-parse the same string in an unreachable
     try/except — collapsible to a single `datetime.date.fromisoformat()` that returns the date
     object (NOTE: the frozen design deliberately chose the explicit-message form, so this needs
     design-aware review + test-message updates, not a blind swap); (ii) the slug re-check at
     `_check_ratchet_log` (~:625) is unreachable — FULL_RE/DISP_RE already enforce the kebab slug and
     a bad slug is caught as "malformed" first; (iii) `_RATCHET_LOG_FULL_RE` duplicates
     `_RATCHET_DISP_RE`, leaving a dead `if not m: continue` guard; (iv) `any_fail` in `repo_lint.py`
     is derivable from the post-loop `failing` list. Suggested park: a "ratchet-lint-cleanup"
     code-quality follow-on in knowledge/questions (low priority).
  d. **Downstream propagation (operator-gated, NOT this batch):** this change adds scaffold-managed
     files (`repo_lint.py`, `test_repo_lint.py` → manifest), an AGENTS.md synced-span bullet, and
     `knowledge_lint.py` enforcement — all propagate on the next `sync_scaffold.py` run, arriving
     INERT downstream (no `checks/*.py` + no ledger → auto-disabled, lint-guarded). Per-repo adoption
     (naming first invariants, bootstrapping a downstream `ratchet-log.md`) is a downstream SMALL
     change per D7. Named adoption seeds (D6, documentation only): psc-monitor SCALE-1 (unbounded
     fetch) / TXN-1 (autocommit fixture); extrends OPS-2 (fail-soft status key unread) / MEAS-1
     (load-failure→empty overwrite).
  e. **Ratchet self-application at archive:** this change ADDS the ratchet-triage step to the archive
     skill, so THIS change's own archive should run the 3-question triage over the defects above.
     Candidate class to weigh: the "openspec requirement text = first physical line only" gotcha
     (§field 3) is generalizable but ALREADY caught by `openspec validate --strict` in the lifecycle
     — likely a `grandfathered`/no-entry or a `check:` pointer to the validate gate; leave the
     verdict to the archive triage, don't pre-decide.

**Still owned by archive (do NOT reconcile here — write-discipline defers these to the delegated
archive-executor, then primary review):**
  - `knowledge/STATUS.md` — new `## Latest change` section (ratchet), enforce the ≤3-section cap.
  - `knowledge/decisions/INDEX.md` — add the ratchet decision entry (per HANDOFF: later refs to "the
    ratchet" mean this change).
  - `knowledge/questions/INDEX.md` — park items (a)–(e) above.
  - Spec promotion — promote both delta specs (`finding-closure-ratchet`, `repo-invariant-checks`)
    into `openspec/specs/`, then remove the `<!-- lint:planned -->` marker on the ledger citation.
  - Cleanup — run the new archive ratchet-triage on this change's own defects (item e).
