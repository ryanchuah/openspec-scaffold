# research-industry-standards-2026-06 Tier-3 items — no closing verdict

Surfaced by the 2026-07-13 full-repo outstanding-work crawl.

`knowledge/research/research-industry-standards-2026-06/_SYNTHESIS.md` sorted its findings into
Tier 1 (adopt), Tier 2 (adopt with caveats), and Tier 3 ("optional / needs operator judgment").
Tier 1 and Tier 2 each got a dedicated follow-up (`EDIT-PLAN-tier1.md`, `EDIT-PLAN-tier2.md`) with
explicit APPLY/DROP verdicts per item, both applied (commits `85cd257`, `0aa1088`). **Tier 3 never
got that closing pass** — five items sit with no recorded decision, verified directly against the
live tree as still absent:

- T3-1 — commented `.claude/settings.json` permissions-template stub
- T3-2 — commented MCP stanza example in README
- T3-3 — optional external-review-hook placeholder in the verify skill
- T3-4 — a `/clarify` pre-design step
- T3-5 — a context-health field in `notes.md`

**Confidence this is a genuine dropped ball: medium-low.** The source doc itself already leaned
toward "drop" (T3-5) or "defer" (T3-4) for several of these, so the lack of adoption may reflect an
implicit editorial call rather than an oversight. Unlike Tier 1/2, nothing in `roadmap.md`,
`decisions/INDEX.md`, or `OUTSTANDING-WORK.md` references Tier 3 at all.

**Recommended handling:** not worth a dedicated OpenSpec change. At most, worth a short operator
skim to either explicitly close each item (DROP, most likely) or adopt the one or two with real
value (T3-3's external-review-hook placeholder is the most plausible candidate if MCP-based review
tools ever enter the workflow). Low priority; do not schedule ahead of the OW-1..16 backlog.
