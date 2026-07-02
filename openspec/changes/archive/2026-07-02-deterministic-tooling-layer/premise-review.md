# Premise review — deterministic-tooling-layer (direction gate)

**Invocation:** `opencode run --agent openspec-reviewer --model deepseek/deepseek-v4-pro`,
2026-07-02, exit 0, no agent fallback, full (non-PARTIAL) output.

### Premise Verdict

```
PREMISE: AGREE
```

- **Root, not symptom:** ✅ The three problems (Fable token cost, agent context waste, missing workflow categories) all trace correctly to the root cause: no deterministic tooling layer exists in either repo, so expensive LLM passes substitute.
- **Solution targets the root:** ✅ Building a scaffold-managed, check-only, JSON-output deterministic tooling layer with two delivery shapes (report + query) directly removes the need for LLMs to do what scripts do better.
- **Scope right-sized:** ✅ In-scope (scaffold scripts + manifest + convention) and out-of-scope (per-repo configs, formatters, audit execution) are clearly delineated. MEDIUM tier scope concern is a process-weight flag (🟡), not a direction defect.
- **Blind spots cited:** 🟡 Tool breakage recovery path implicit; invocation overhead for session-start use not analyzed; "SQL is greppable" claim may be optimistic; `audit-log.md` taxonomy placement undefined.

### Findings (no 🔴)

- 🟡 1 — MEDIUM tier emits `tasks.md` only, but the change's design decisions (D1–D9) live in the
  explore brief; risk of apply-executor design-on-the-fly. Reviewer's minimum fix: acknowledge in
  the brief that `tasks.md` must be dense with design-guidance pulled from the brief.
- 🟡 2 — Brief preamble still instructed the next session to confirm the already-resolved §6 items.
- 💡 1 — Session-start wall-clock cost: run the fast floor eagerly, heavy checks on-demand only.
- 💡 2 — "psc-monitor SQL is greppable" is optimistic (f-strings/concat); keep as best-effort
  audit-time report; reality-check in propose.
- 💡 3 — Make the pinned-tool breakage recovery cycle explicit (bump pin → re-run baseline triage).
- 💡 4 — `plans/knowledge-lint/` was a forward reference at review time (brief in progress);
  propose should in-line the audit-log format spec rather than depend on the unwritten linter.

### Resolution

Verdict is `AGREE`; the overall "NEEDS REVISION" note is process-level. All items above were
addressed by same-day edits to `explore-brief.md` (preamble/status updated; MEDIUM design-carrier
acknowledgment added to §5; audit-log taxonomy placement + recovery cycle added to D6/D9;
eager-vs-on-demand split added to D8; index-coverage greppability caveat added to §4).
Proceeding to `propose deterministic-tooling-layer` (tier MEDIUM, operator-confirmed).
