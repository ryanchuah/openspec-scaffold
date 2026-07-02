# Premise review — knowledge-lint (direction gate)

**Invocation:** `opencode run --agent openspec-reviewer --model deepseek/deepseek-v4-pro`,
2026-07-02, exit 0, no agent fallback, full (non-PARTIAL) output.

### Premise Verdict

```
PREMISE: AGREE
```

- **Root, not symptom:** ✅ The systematic gap (no mechanism re-checks per-repo prose against
  reality) is the root cause; the four drift classes are well-characterized symptoms; the
  coverage-gap table was independently verified accurate against the actual implementations.
- **Solution targets the root:** ✅ Deterministic + LLM two-layer approach covers all four
  observed drift classes from both angles.
- **Scope right-sized:** ✅ Mechanism only (scripts + skill + integration), not per-repo content
  fixes; out-of-scope clearly stated.
- **Blind spots:** three design-level 🟡 items, none direction-level.

### Findings (no 🔴) — carried into the propose phase

- 🟡 1 — Integration decision: does `knowledge_lint.py` subsume, coexist with, or replace
  `sync_scaffold.py --check-refs`'s path-citation scanning?
- 🟡 2 — Cadence split: the deterministic layer is cheap (CI/every-archive); the LLM judgment
  layer is not (periodic/operator-invoked) — the two layers need different cadences.
- 🟡 3 — Division of labor with `status_lint.py`'s existing archive-pointer check when
  broadening dangling-pointer detection beyond `decisions/INDEX.md`.
- 💡 test corpus of known-stale vs known-fresh claims to smoke-test the LLM layer; explicit
  "out of scope: non-markdown" note; per-repo config for retired-path tokens (recommended).

### Resolution

Verdict is `AGREE`; direction stands. The 🟡/💡 items were appended to the brief's open items
(§5) same-day so the propose session inherits them. Per operator decision 2026-07-02, propose
for this change runs in a **fresh session** — this session took it through the direction gate only.
