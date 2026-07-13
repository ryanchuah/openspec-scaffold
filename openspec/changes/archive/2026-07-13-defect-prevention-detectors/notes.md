# notes — defect-prevention-detectors (OW-1 + OW-4)

**Tier:** MEDIUM. **Orchestrator:** Opus (design pre-made — OW-1/OW-4 in
`OUTSTANDING-WORK.md`; the checks.py architecture fork resolved this session, see
`recon-digest.md`). **Apply:** delegated (deepseek-flash default; may fall back to Sonnet for the
AST logic).

Merges the two wave-1 defect-prevention detector items (both add a universal `checks.py` detector +
a verify hook; coherent single change). Both OW numbers close together.

## Architecture (decided — see recon-digest.md for the deciding facts)
Both detectors ship as **first-class in-process AST builtins in `scripts/checks.py`**
(scaffold-managed → propagate to every repo), special-cased like `inventory` (always-available, no
external-tool preflight), `family="check"`, **enabled by default**. checks.py findings surface in the
audit report and do NOT fail `check.sh`/pytest → enabling by default is FP-safe (advisory surface,
operator-triaged). The per-repo `checks/*.py`/`repo-lint` framework is NOT touched (it is for
repo-specific invariants; these are universal).

## Acceptance criteria

### OW-1 — test-quality detector + verify lens wiring
1. **New `test-quality` detector** in `checks.py`, scoped to **test files only** (`test_*.py` /
   `*_test.py`, pytest discovery), emitting `{check:"test-quality", rule, path, line, message}`. v1
   rules (each pinned by a positive+negative test fixture):
   - `assert-true` — a bare `assert True` (tautological).
   - `assert-or-true` — `assert <expr> or True` / `assert True or <expr>` (forced-green).
   - `empty-test` — a `def test_*` whose body is only `pass` and/or a docstring (no assertions).
   - `unfrozen-clock` — a call to `datetime.now`/`datetime.utcnow`/`time.time`/`time.monotonic`
     inside a `test_*` function body (non-deterministic clock in a test).
   - `self-mock` — `patch("<m>…")`/`patch.object(<m>, …)`/`mock.patch("<m>…")` whose target's root
     module equals the module-under-test derived from the filename (`test_<m>.py`→`<m>`);
     conservative — skip when no clear module-under-test.
   - `discarded-return-flag` — a tuple-unpack assignment `<name>, _ [,…] = <call>()` inside a
     `test_*` function (a returned status dropped into `_`). **Documented FP tradeoff:** legit
     idioms (`x, _ = divmod(...)`) can trip it; acceptable because findings are advisory
     (audit-triaged, not a CI gate) and the evidence value is high (extrends TA-3).
2. **Verify lens wired to the detector.** The verify skill's test-quality lens prompt
   (`SKILL.md:97`) + the `verify-multimodel-gate` spec forward-compat clause (`spec.md:100`) become
   concrete: the lens SHALL direct the verifier to run `checks.py --check test-quality` and confirm
   its findings rather than rediscover them. (The lens QUESTION "would this test fail if the
   behavior broke?" stays as the judgment layer.)

### OW-4 — data-scale detector + verify rule
3. **New `data-scale` detector** in `checks.py`, scoped to **non-test source** (exclude the test
   globs + fixture dirs), v1 rule:
   - `unbounded-fetchall` — a `.fetchall()` call. Message directs: record an at-scale run or a
     bounded-domain argument in `notes.md`, or add a LIMIT/pagination.
4. **Verify RULE hardened** (from the current lens *question*): a **data-path change** SHALL record
   in `notes.md` EITHER an at-scale run OR a bounded-domain argument. Home: a conditional block in
   the verify skill modeled on the security-review gate; cite the canonical `AGENTS.md` "Mind data
   scale" span + `openspec/config.yaml rules.verify` (do NOT restate). The data-scale lens prompt
   also wired to run `checks.py --check data-scale`.

### Both
5. **Registry + config wiring:** both added to `_REGISTRY` (tier=floor, kind=builtin, family=check),
   `_autodetect_defaults` (enabled), and registered in `_BUILTIN_RUNNERS` + `_PARSERS` so the normal
   builtin dispatch path (the `else` branch that normalizes paths + builds the record + merges the
   aggregate) handles them uniformly. The ONLY inventory-style special-case is in
   `_availability_for_check` (always-available, no external binary) — do NOT special-case
   `_execute_check` (that path skips path normalization). Their `_run_*` runners do AST in-process
   and return an outcome dict WITH a `findings` list. `checks.toml` `[checks.<name>].enabled`
   override works. (See T4 for the exact dispatch contract.)
6. **Tests:** `test_checks.py` `ListModeTest.expected_names` + `AutodetectTest` updated for the 2
   entries; per-rule finding-shape + scoping tests (write real source into the temp repo, assert the
   `{check,rule,path,line,message}` finding + `rc==2` FINDINGS contract; assert test-quality does NOT
   scan non-test files and data-scale does NOT scan test files).
7. **Green gate:** `bash scripts/check.sh` exits 0. Confirm no existing test asserts a global
   "checks.py --floor/--report finds zero" on the scaffold (which the new default-on detectors could
   break); if the scaffold's own test files legitimately trip a rule, that's an advisory finding —
   ensure it does not red the suite (and note any self-findings for follow-up triage).

## Spec deltas
- **NEW `defect-prevention-detectors`** capability (the two universal builtins + their contract).
- **MODIFIED `verify-multimodel-gate`** (forward-compat clause → concrete; OW-4 data-path rule).

## Assumptions (batched)
- **A1 — `discarded-return-flag` FP tradeoff accepted** (advisory surface; see criterion 1). Reverse
  to a stricter heuristic or defer if the operator prefers near-zero-FP over coverage.
- **A2 — OPTIONAL: update `repo_lint.py`'s `no_fetchall.py` docstring example** so it doesn't imply
  repos should re-implement the now-universal `data-scale` check. Low priority; in-scope only if
  cheap — else park.
- **A3 — per-rule enable/disable toggle is a v2 follow-on** (surfaced by the pro review). v1 ships
  all 6 test-quality rules enabled, with the two noisiest (`unfrozen-clock`, `discarded-return-flag`)
  advisory-labeled; a repo drowning in them disables the whole detector via
  `[checks.test-quality] enabled = false`. A per-rule `disabled_rules` config (so the high-signal
  rules stay on while noisy ones are silenced) is the real long-term fix — deferred to v2, observed
  from downstream adoption noise first. Park as a follow-on question at archive.

## Out of scope
- The per-repo `checks/*.py`/`repo-lint` framework (untouched). Downstream adoption/propagation
  (operator-gated). ast-grep graduation.

## Traceability
Closes **OW-1** and **OW-4** (wave-1 defect-prevention) in `OUTSTANDING-WORK.md`; the wave-1
roadmap entry closes when these land (per roadmap.md 2026-07-13 update).
