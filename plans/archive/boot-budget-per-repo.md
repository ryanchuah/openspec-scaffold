# SMALL plan — boot-budget-per-repo

**Tier:** SMALL · **Date:** 2026-07-15 · **Origin:** psc-monitor propagation friction F4
(operator chose "make the boot budget per-repo configurable")

## Problem statement

`scripts/boot_surface_lint.py` hardcodes the mandatory-boot-read byte budget as module
constants `WARN_BYTES = 80_000` / `FAIL_BYTES = 100_000`. Unlike `knowledge_lint.py`
(which reads a per-repo `[knowledge_lint]` section from `checks.toml` with graceful
defaults), boot_surface_lint offers **no per-repo override**. A legitimately larger
downstream project — psc-monitor carries a 12GB pipeline + Stripe billing + GDPR
compliance + deploy runbooks, giving it 109,596 B of boot surface vs the scaffold's
78,876 B — therefore hard-FAILs the check on first sync (the live-tree test
`test_boot_surface_live_tree_not_fail` asserts `rc != 2`, so a FAIL breaks the pytest
suite and blocks the downstream commit gate). The check's one-size-fits-all constant
is mis-calibrated for repos with a richer-than-scaffold boot surface.

## Proposed approach / fix

Mirror the established `knowledge_lint` per-repo config pattern exactly:

1. **`scripts/boot_surface_lint.py`** — add `_load_config(root: Path) -> dict` that reads
   a `[boot_surface_lint]` table from the repo-root `checks.toml` (stdlib `tomllib`),
   with keys `warn_bytes` (default `WARN_BYTES`) and `fail_bytes` (default `FAIL_BYTES`).
   Absent file / absent section / absent key → the existing constants, so behaviour is
   byte-for-byte unchanged where no override exists (the scaffold itself stays at 80k/100k).
   In `main()`, resolve the two thresholds from config *after* resolving `repo_root`, and
   use the resolved values in the comparisons and in the WARN/FAIL messages (which already
   interpolate the threshold). Keep the module constants as the documented defaults.
   Validate: `fail_bytes >= warn_bytes` (if a repo misconfigures them inverted, fall back
   to defaults or clamp — decide in apply; simplest: if `warn > fail`, ignore overrides and
   use defaults, print a one-line notice). Non-negative ints only; malformed types → defaults.
2. **`scripts/test_boot_surface_lint.py`** — extend `_make_boot_repo` to optionally write a
   `checks.toml`, and add tests: (a) raised `fail_bytes` lets an over-100k surface pass;
   (b) lowered `fail_bytes`/`warn_bytes` fails a smaller surface; (c) absent/malformed config
   falls back to the 80k/100k defaults (regression-guards the unchanged-where-no-override
   contract); (d) inverted warn>fail falls back to defaults. Keep the live-tree
   `assertNotEqual(rc, 2)` test.
3. **Docstring** — update the module docstring's "Constants" / threshold description to
   note the per-repo `[boot_surface_lint]` override and its default fallback.

Then (downstream, separate from the scaffold commit): add `[boot_surface_lint]` with
`warn_bytes = 100000`, `fail_bytes = 120000` to **psc-monitor's** `checks.toml` (per-repo,
not scaffold-managed), re-sync the scaffold script, and confirm the downstream suite goes
green (109,596 B → WARN, exit 1, non-blocking).

## Out of scope

- **No change to psc-monitor's knowledge content** — the operator explicitly chose the
  threshold route over condensing live deploy-gate knowledge. The Active/Parked split-rule
  cleanup (parking the 3 big green items) is NOT done here; it can be a later, separate
  per-repo pass if desired.
- **No change to the default budget** (80k/100k stays the scaffold default and applies to
  any repo without an override).
- **No new config file** — reuse the existing per-repo `checks.toml` mechanism; do not add a
  YAML/other surface.
- **Not making WARN_BYTES/FAIL_BYTES themselves scaffold-synced** — `checks.toml` is per-repo
  and remains so.

## Execution & verify record (2026-07-15) — SHIPPED

- **Premise (flash):** `PREMISE: AGREE`, PASS (`plans/archive/boot-budget-per-repo-premise-review.md`).
- **Apply:** delegated to `apply-executor` @ `deepseek/deepseek-v4-flash` (status=ok, no fallback).
  Implemented `_load_config` mirroring `knowledge_lint`, threaded resolved thresholds through
  `main()`, added 5 override tests, updated docstring. Inverted `warn>fail` resolved as
  fallback-to-defaults + stderr notice.
- **Verify (flash `openspec-verifier`):** `VERDICT: READY`. One 🟡 (non-blocking): the
  malformed-config test was vacuous (float overrides equalled the defaults). Fixed inline
  (disclosed trivial exception) — overrides now `50000.0/60000.0` so removing the type-guard
  would flip rc 1→2, making the test non-vacuous.
- **Gates:** full scaffold suite green (`pytest -q`), `ruff check` + `ruff format --check` clean.
- **Downstream:** psc-monitor `checks.toml` gets `[boot_surface_lint] warn_bytes=100000,
  fail_bytes=120000` (per-repo, committed downstream, not in this scaffold commit).
