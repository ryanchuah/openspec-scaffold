# Retired Notes

Not loaded at session start — agents skip `ai-docs/archive/` per `AGENTS.md`. This holds content
**moved out of `ai-docs/open-questions.md` / `ai-docs/parked-follow-ons.md`** once it became
resolved or superseded, to keep the always-loaded orientation set lean. Durable rationale for
shipped work lives in `ai-docs/decisions.md`. Load a section here only if you are re-examining the
specific closed item it covers. Newest first.

---

## add-status-lint — Phase B STATUS/decisions cleanup (resolved 2026-06-18)

The linter-driven one-time cleanup the external review called for is DONE across all three repos, each gated by `status_lint.py` going green: **scaffold** — the over-budget `split-open-questions` STATUS entry was trimmed and moved verbatim to `status-log.md` during the add-status-lint archive (`86b2094`); **extrends** (`c3f076b`) — the 3 retained entries (324/280/289w) trimmed to ≤150-word headlines (full prose → `status-log.md`), the bloated `## Immediate next action` trimmed (completed-setup history → archive pointer), and `improvement-roadmap.md` relocated `ai-docs/` → `plans/` with all 5 references updated; **psc-monitor** (`05c5b36`) — the 2 entries (332/210w) trimmed (full prose → `status-log.md`), staged explicitly to avoid a concurrent agent's in-flight work. All three repos now pass `status_lint`. Originating change: `add-status-lint`. Archive: `openspec/changes/archive/2026-06-18-add-status-lint`._

## single-source-rules — Phase 2 propagation (resolved 2026-06-18)

`sync_scaffold.py` carried single-source-rules' 7 managed files (AGENTS.md span-merge + `research-fetch-convention.md` + the propose/verify/archive skills + both apply-executor bodies) to extrends (`8812533`) and psc-monitor (`92beaec`); `--check` then ALL IDENTICAL on both. Each AGENTS.md span-merge was diff-reviewed (title / `## Project context` / tail preserved). `config.yaml` and `ai-docs/workflow-lessons.md` are intentionally per-repo (not in the manifest) and did not propagate — by design. The `(registry: ai-docs/workflow-lessons.md §2)` pointer was stripped from all `CANONICAL:` markers so they are self-contained. Originating change: `single-source-rules`. Archive: `openspec/changes/archive/2026-06-17-single-source-rules`._
