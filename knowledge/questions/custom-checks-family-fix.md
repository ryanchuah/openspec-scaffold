# `_custom_checks` `family=` fix — RESOLVED

**Status:** RESOLVED 2026-07-18 by `custom-checks-family-fix`
(`plans/archive/custom-checks-family-fix/`). `_custom_checks()` now honors a normalized,
gating-safe `family=` key so `[checks.custom.*]` entries can register fact-family
(preflight-exempt, graceful-degrade) checks; an invalid/typo value falls back to `check` (gated),
never silently `fact`. Decision: `knowledge/decisions/INDEX.md` (2026-07-18 · custom-checks-family).

Deferred follow-on from `graduate-sast-scanners` (shipped 2026-07-18).

## What
Let a `[checks.custom.<name>]` entry in `checks.toml` register a **fact**-family (preflight-exempt,
graceful-degrade) check by honoring `spec.get("family", "check")` — currently `_custom_checks` always
force `family="check"`.

## Why deferred
Orthogonal to the Semgrep/Bandit built-in check wiring (both are `check`-family). Touching
`_custom_checks` adds risk to the preflight/degradation logic; belongs to the separate
"facts-snapshot registration" concern. This would allow downstream repos to register app-specific
fact snapshots (e.g. psc-monitor's route-authz) without standalone scripts.

## When
Separate SMALL change when needed. Not blocking anything.
