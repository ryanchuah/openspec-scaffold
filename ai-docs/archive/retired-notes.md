# Retired Notes

Not loaded at session start — agents skip `ai-docs/archive/` per `AGENTS.md`. This holds content
**moved out of `ai-docs/open-questions.md` / `ai-docs/parked-follow-ons.md`** once it became
resolved or superseded, to keep the always-loaded orientation set lean. Durable rationale for
shipped work lives in `ai-docs/decisions.md`. Load a section here only if you are re-examining the
specific closed item it covers. Newest first.

---

## single-source-rules — Phase 2 propagation (resolved 2026-06-18)

`sync_scaffold.py` carried single-source-rules' 7 managed files (AGENTS.md span-merge + `research-fetch-convention.md` + the propose/verify/archive skills + both apply-executor bodies) to extrends (`8812533`) and psc-monitor (`92beaec`); `--check` then ALL IDENTICAL on both. Each AGENTS.md span-merge was diff-reviewed (title / `## Project context` / tail preserved). `config.yaml` and `ai-docs/workflow-lessons.md` are intentionally per-repo (not in the manifest) and did not propagate — by design. The `(registry: ai-docs/workflow-lessons.md §2)` pointer was stripped from all `CANONICAL:` markers so they are self-contained. Originating change: `single-source-rules`. Archive: `openspec/changes/archive/2026-06-17-single-source-rules`._
