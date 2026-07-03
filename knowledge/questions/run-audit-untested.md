# run-audit never exercised end-to-end

The `run-audit` skill's full cycle (list → floor/report → triage → tag → log-line append) has
never been exercised against a real, wired audit layer. The scaffold repo itself has **no wired
audit layer** — no `checks.toml`, no `checks/` directory, no task-runner `audit-*` targets, no
seeded `knowledge/audit-log.md`. The skill's commands and error-handling are verified accurate
(manual review of the SKILL.md against the actual `checks.py`/`audit_scope.py` CLI), but
the first real end-to-end exercise happens when a downstream repo wires the audit layer and an
operator invokes the skill.

**Monitored, not blocking.** The skill is safe to ship because:
- It is operator-invoked only (on-demand, not wired into any automated lifecycle step).
- Its wiring-detection branch explicitly handles the missing-layer case (detects absent
  `checks.toml`/`checks/`/task targets and guides the build-out rather than failing opaquely).
- `audit_scope.py tag` is the sole repo-state mutation and is operator-gated (tagged only when
  operator explicitly asks to "tag"/"anchor this audit").

When a downstream repo wires the audit layer, run a first end-to-end exercise there and feed
any findings back here.
