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
