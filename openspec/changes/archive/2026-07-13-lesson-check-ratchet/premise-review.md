# Premise review — lesson-check-ratchet explore brief (direction gate)

**Reviewer:** openspec-reviewer · deepseek/deepseek-v4-pro via `opencode run` · 2026-07-10
**Fallback check:** clean (no `Falling back to default agent` in stderr; exit 0)
**Full review text:** `openspec/changes/lesson-check-ratchet/review-log.md` (Round 1 — direction gate)

### Premise Verdict

```
PREMISE: AGREE
```

- 🔴 blocking: none.
- 🟡 (design.md-level, carried into design): (1) waiver staleness — waivers need a re-review
  cadence/expiry or they become the new write-only memory; (2) frozen-test linkage must be
  *verified* (test exists / still exercises the class), not declarative — apply the
  budget-agreement cross-check shape; (3) code-shape detectors have a different cost profile
  than SQL checks — whole-tree scans need their own timeout/perf model.
- 💡 (carried into design): disposition preference ordering (check > frozen test > waiver);
  self-referential bootstrap (the ratchet ledger format gets its own lint check, like
  `_check_audit_log`); a `grandfathered` disposition for legacy lessons so the lint can tell
  "reviewed and deferred" from "never triaged"; state the downstream-adoption risk explicitly.
- Drift: none detected vs SYNTHESIS.md / OUTSTANDING-WORK.md; prior-art constraints honored;
  no existing spec conflicts.

**Gate result: direction sound — advanced to propose.**
