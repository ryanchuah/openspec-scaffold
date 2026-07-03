# SMALL premise review — fix-propagation-tooling-drift

Reviewer: `openspec-reviewer` @ `deepseek/deepseek-v4-flash` (via `opencode run`), 2026-07-03.

```
PREMISE: AGREE
```

No 🔴, no 🟡. Both bugs fact-verified against source (`sync_scaffold.py:361`,
`knowledge_lint.py:120`, `scaffold_lint.py:144`, `_MANIFEST_EXCLUDE_EXACT` at 135-143; the
`audit-log.md` citation confirmed at `AGENTS.md:352` and `knowledge/README.md:16`). Root cause,
solution-targets-root, and scope all sound. No autonomy override needed — verdict is AGREE.

## 💡 folded into apply instructions
- The new check-refs regression test is **two-case** (mirroring the existing HANDOFF test at
  `test_sync_scaffold.py:652`): (a) a citation to `knowledge/audit-log.md` with the file absent
  yields NO DANGLING; (b) a *second* genuinely-missing file still fires — proving the exemption
  does not mask real dangling refs.
