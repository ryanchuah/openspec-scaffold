# Notes — cap-status-log

## Problem (from the extrends-agent feedback, 2026-06-17)

The scaffold's archive-executor step 3a appends a `## Latest change` paragraph and
demotes the prior to `## Prior change` at every archive, but **nothing prunes** —
STATUS.md grows by one dense paragraph per change forever. In the scaffold itself
this is at 9 paragraphs (tolerable). In **extrends** (a real working repo that
inherited the rule via sync) STATUS.md is 449 lines / ~27k tokens with 38 change
headers — it exceeds the Read 25k-token cap, so AGENTS.md's "read in full" directive
is literally unsatisfiable. decisions.md (1,322 lines) and open-questions.md (794) are
similarly large. psc-monitor is still small (119/311/106) and needs no cleanup.

Root cause is scaffold-authored, so the durable fix lives here and propagates via
`sync_scaffold.py`. Both the MANDATORY block (span1) and the write-discipline
section (span2) are inside the synced AGENTS.md spans, so a scaffold edit reaches
extrends and psc-monitor on the next sync.

## Design decisions

- **Fix by bounding the files, not by weakening the read directive wholesale.**
  Keep "read in full" for STATUS.md (capped) and open-questions.md (pruned via the
  existing retired-notes.md mechanic). Only decisions.md — which legitimately grows
  append-only — switches to "read `##` headers, then read relevant entries."
- **Cap STATUS.md at ~3 change paragraphs**; overflow moves verbatim to
  `ai-docs/archive/status-log.md` (new append-only log, newest-first). The cap runs
  inside the existing archive-executor reconciliation pass — no new gate, no new run.
- **Freshness carve-out:** process/scaffold-maintenance commits don't obligate a
  STATUS.md entry, so the resume-time lag-check won't drive spurious edits (this is
  live right now in the scaffold repo — recent commits are all process commits).
- extrends cleanup and psc-monitor are explicitly OUT of scope for this change.

## Verification — change-specific acceptance criteria

1. AGENTS.md MANDATORY block: decisions.md read directive is header-scan + relevant
   entries; STATUS.md + open-questions.md still "in full". Freshness carve-out present.
2. AGENTS.md write-discipline: STATUS.md cap rule (~3 paragraphs, overflow →
   `ai-docs/archive/status-log.md`) stated, with rationale.
3. archive-executor `.claude` and `.opencode` both carry the prune bullet in 3a and
   are byte-identical: `python3 scripts/test_executor_body_agreement.py` passes.
4. `python3 scripts/test_sync_scaffold.py` passes — AGENTS.md span anchors intact,
   span-replace round-trips, tail preserved.
5. `openspec validate --all` passes with no new failures.
6. No test/doc/row counts introduced; synced-span anchor headings unchanged.
7. Live sync smoke (verify-time, not a task): after edits land, run
   `python3 scripts/sync_scaffold.py --check ../psc-monitor` — the AGENTS.md span-merge
   must still produce a clean/IDENTICAL result against a real downstream target,
   confirming the edited content interacts correctly with a downstream structure (the
   unit test only exercises fixtures). [reviewer 💡 S2]

## Verify outcome (2026-06-17)

1. **Verdict:** READY FOR ARCHIVE.
2. **Live output eyeballed:** ran `scripts/sync_scaffold.py --check ../psc-monitor` against
   the edited scaffold — the AGENTS.md span-merge completed cleanly (no anchor/ValueError),
   and the only files reported DIFFERS were `AGENTS.md` and `.opencode/agents/archive-executor.md`,
   i.e. exactly the two synced files this change edits (psc-monitor is simply behind by the new
   rule and picks it up on the next real sync). All other manifest files IDENTICAL. Also re-ran
   the guard suites: executor-body-agreement OK (bodies byte-identical), sync-scaffold tests OK,
   and confirmed the four AGENTS.md span anchors are byte-unchanged vs HEAD. `openspec validate
   --all` = 7 passed / 0 failed.
3. **Defects found / fixed:** none. Self-review, deepseek-v4-pro pass, and deepseek-v4-flash pass
   all returned VERDICT: READY with zero defects (real agents confirmed — no fallback warning).
4. **As-built deltas:** none — the diff matches the frozen tasks.md exactly.
5. **Forward-looking items:** none new from verify. Two pre-existing items remain (already in
   this notes.md below): the **extrends one-time cleanup** (next, separate; per-repo state, cannot
   sync) and **psc-monitor** (no action; inherits the rule on next sync). One standing observation
   worth the archive reconciler's awareness: the cap rule is now stated in three surfaces
   (AGENTS.md principle / archive-executor mechanic / archive-skill check) — intentional layering,
   but it touches the same within-scaffold rule-restatement theme tracked as the deferred **C2/W7**
   dedup candidate; no action here.

**Still owned by archive:** reconcile `STATUS.md` (add Latest-change, demote prior — and this is
the FIRST archive that should exercise the new cap/prune if >3 paragraphs result), `ai-docs/decisions.md`
(new decision entry for the cap rule + freshness carve-out + decisions.md read-directive change),
`ai-docs/open-questions.md` (carry the extrends-cleanup follow-on), spec promotion (none — no delta
specs), and any cleanup.

## Candidate open-questions / follow-ons for archive

- **extrends one-time cleanup** (next, separate): cap its STATUS.md to last 3, move
  ~35 old paragraphs to `ai-docs/archive/status-log.md`, sweep resolved open-questions
  to retired-notes.md. Cannot be synced — it is per-repo state.
- psc-monitor: no action; inherits the corrected rule on next `sync_scaffold.py`.
