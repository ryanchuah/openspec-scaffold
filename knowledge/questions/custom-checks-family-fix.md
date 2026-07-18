# `_custom_checks` `family=` fix — parked

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
