# Improvement Roadmap

Durable roadmap of larger improvements not yet scoped into a specific OpenSpec change. Add an entry when a meaningful improvement idea surfaces during research, verify, or design but is not ready to become a change. Prune entries as they graduate into real changes.

---

<!-- Format:
## <Short title>
**Priority:** High / Medium / Low
**Gating condition:** What must be true before this is actionable (e.g., "needs N real production runs", "requires design doc first").
**Summary:** What the improvement is and why it matters.
**Dependencies / notes:** Related items, prior art, open tensions.
-->

## Scaffold consolidation — hardening + propagation (supersedes scaffold-sync) — ✅ DONE 2026-06-17 — COMPLETE
**Priority:** ~~High~~ — COMPLETE. All findings shipped.
**Resolution:** The full W0–W7 family shipped + archived (2026-06-16…2026-06-17): W0 hook-wiring smoke, W1 fix-sync-mechanism, W2 dedup-scaffold, W3 fix-convergence-guard, W4 lifecycle-gates, W5 cleanup-workflow-ergonomics, W6 propagate-baseline, W7 single-source-rules. The one-time propagation (W6) carried scaffold HEAD to `extrends` (`176d554`) and `psc-monitor` (`6541a9d`) via `scripts/sync_scaffold.py`; the superseded `scaffold-sync` change was deleted (its surviving parts shipped in W1 + W6). The final audit finding — C2 (within-scaffold rule-restatement dedup) — graduated as the `single-source-rules` change (C2/W7, 2026-06-17), closing the consolidation ledger. All three repos are now converged on one workflow source, with the commit-test gate + scaffold-managed guard wired (dormant) downstream, and all five rule-families single-sourced with canonical homes and cite-don't-restate convention. Per-change records in `STATUS.md` and the archive; design ledger in `ai-docs/consolidation-plan-2026-06-16.md` + `workflow-audit-2026-06-16.md`.
**Dependencies / notes:** Consolidation family fully complete.

## Cross-change spec-conflict detection at archive
**Priority:** Low
**Gating condition:** Parallel changes that edit the *same* capability spec become common (multiple in-flight changes touching one capability).
**Summary:** The single-change archive flow cannot detect when two or more changes both modify the same capability's spec — archiving them one at a time can silently apply deltas in the wrong order or let one overwrite another. A former `bulk-archive` skill detected these cross-change collisions (it built a `capability → [changes]` map and resolved sync order before applying). It was removed (commit `8e325ee`) because it archived multiple changes in one inline pass with no pre-handoff checkpoint or scoped recovery — the opposite of the hardened, serialized, one-change-at-a-time archive flow. The collision-detection was the one genuinely unique capability lost in that removal.
**Dependencies / notes:** If reintroduced, rebuild it on the current hardened model (per-change pre-handoff checkpoint + archive-executor delegation + scoped recovery), not as an inline batch pass. Until then, when archiving multiple changes that touch overlapping capabilities, manually check for spec collisions before syncing.
