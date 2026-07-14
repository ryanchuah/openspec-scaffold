# Notes — archive-mechanization (OW-12)

## Acceptance criteria
See design.md `## Verification`. Change-specific acceptance = every D4 truth-table row behaves per
spec, atomicity holds (any anomaly → zero writes, exit 2), `archive_move.py` conflict guard, all guards
green (`check.sh`, `scaffold_lint`, `test_executor_body_agreement.py`).

## Assumptions (non-blocking; recorded per AGENTS.md)
- A1 · Exit-code convention: `apply_delta_spec.py` & `archive_move.py` use `0`=success, `2`=anomaly/
  refusal. Kept exit 2 (not exit 3) despite the argparse-2 overlap; callers disambiguate an anomaly
  from a usage error by report presence (review-log Round 2 💡).
- A2 · Move mechanism: plain `shutil.move` (git stays out of the script; primary stages at commit) — D11.
- A3 · Parser grammar: own copy of the three `checks.py` regexes + a frozen agreement test, NOT a
  shared module (avoids churning the load-bearing detector) — D2.

## Apply-split (disclosed per HANDOFF lesson #1)
Group 4 (skill/executor prose rewiring — fence-heavy, byte-identical-executor-bodies) is
**orchestrator-authored** and checked off BEFORE delegating; the flash apply-executor implements
groups 1–3 (deterministic Python + tests + manifest) only.

## Verify results — VERDICT: READY (2026-07-14)

- **Self behavioral review (the core):** read the full promoter source; authored **16 independent
  adversarial fixtures** (`test_apply_delta_spec_adversarial.py`, property/invariant style) covering
  the D4 table, atomicity, self-collision, RENAMED+MODIFIED combo, only-`## Purpose` spec, degenerate
  deltas, formatting invariants, idempotency, and trailing-section ordering. They caught **3 real
  product defects the green executor tests missed**:
  1. new-capability ADDED self-collision undetected (the `main_spec is None` branch appended blindly
     → duplicate requirements / missed anomaly);
  2. blank-line drift (`write_spec` emitted `\n\n\n` on every promotion);
  3. trailing `## ` section silently reordered ahead of the requirements (canonical-spec corruption).
  Diagnosed + scoped, **re-delegated the fix to a fresh flash executor** (TDD: make the fixtures green);
  **zero Sonnet fallback**. Re-probed real output: promoted ADDED/REMOVED/RENAMED specs are clean
  (single blanks, postamble preserved), atomicity holds (anomaly → nothing written, exit 2).
- **Pro behavioral verifier pass (deepseek-v4-pro):** VERDICT READY, zero defects, **no fallback**
  (the pro verifier emitted a normal verdict this session — contrast the prior HANDOFF's zero-output
  report; the degradation was not persistent).
- **Flash test-quality lens pass:** first run NEEDS-REVISION — caught **2 weaknesses in my own
  fixtures** (two tests discarded `_run()`'s exit code, risking a spurious-anomaly false pass). Fixed
  inline (verify fixtures, not product code); re-ran the lens (only the failed pass, per the ladder)
  → VERDICT READY, zero defects.
- **Simplicity/quality gate:** PASS. One low-priority note (below).
- **Security gate:** N/A — stdlib-only local file moves + text transforms; no auth/credentials/data/
  external-API/network surface.
- **Guards:** `check.sh` green (ruff + format + full suite), `scaffold_lint` clean (4+1 new files in
  manifest), `test_executor_body_agreement.py` passes (both executor bodies byte-identical),
  `openspec validate --strict` clean. Tests pass; the system ran clean.

## Candidate open-questions / follow-ons for archive
- **[low] Unify the `plan_spec` None-branch and else-branch ADDED-collision logic** (via an empty
  MainSpec) — ~15 lines duplicated; deferred to avoid churning just-fixed code, do it if the file is
  next touched.
- **[low, latent] Headerless-requirement parse** — a main spec with `### Requirement:` before any
  `## Requirements` header is parsed oddly; no repo spec triggers it (openspec always emits
  `## Requirements`). Monitor.
- **[monitored] RENAMED true debut** — RENAMED is now mechanized under a tested contract + fixtures,
  but the first REAL archive carrying a RENAMED delta remains the live debut.
- **[monitored] REMOVED-absent silent-skip** (design D4 decision) — flip to anomaly if a typo'd
  REMOVED ever silently no-ops in practice.
- **[info] pro-verifier no-output was not persistent** — worked normally this session; keep watching.
- **Dogfood at archive:** this change's own ADDED-only delta will be promoted by the new
  `apply_delta_spec.py` (via the rewired Sonnet archive-executor) → creates
  `openspec/specs/archive-mechanization/spec.md`. First real exercise of the tool.
