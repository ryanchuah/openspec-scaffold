# Semgrep needs config — monitored

Deferred follow-on from `graduate-sast-scanners` (shipped 2026-07-18).

## What
Semgrep ships with **no scaffold default ruleset** (by design — the scaffold doesn't bake one in).
A repo enabling `semgrep` via `[checks.semgrep] enabled = true` MUST supply a `--config <ruleset>`
via `[checks.semgrep] args`. Without it, semgrep's own error surfaces as an INFRA-FAIL (acceptable
misconfiguration signal, per the design).

## Risk
A downstream repo could enable semgrep without a ruleset and get a confusing INFRA-FAIL. The
error message points at the missing `--config`, but the UX could be more helpful (e.g. a preflight
hint from `checks.py`).

## Monitored
Watch for operator confusion during downstream propagation. If this trips more than once, add a
preflight guard that surfaces "semgrep enabled but no `--config` in args" as a clear WARNING
rather than letting it reach the tool's own opaque error.
