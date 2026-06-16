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

## Scaffold consolidation — hardening + propagation (supersedes scaffold-sync)
**Priority:** High
**Gating condition:** Holistic map is done (`ai-docs/consolidation-plan-2026-06-16.md`). Actionable now — propose W0/W1 first. W0 (hook-wiring smoke) needs a gated Claude session.
**Summary:** Consolidates the `scaffold-sync` review (`principal-review.md`) and the full workflow audit (`workflow-audit-2026-06-16.md`) into ONE design → an ordered family of small changes (W0…W6): fix the sync mechanism (de-gold-plated), dedup the within-scaffold delegation harness, close `_convergence.py` holes, add the missing simplicity/security gates, then do the one-time propagation last (clean snapshot). `scaffold-sync` is superseded — delete it once W1+W6 carry its surviving parts.
**Dependencies / notes:** Full map, ordering, supersession table, and per-finding ledger in `ai-docs/consolidation-plan-2026-06-16.md`. Scope cut (which W's ship now vs. defer) decided per-change at propose time.

## Cross-change spec-conflict detection at archive
**Priority:** Low
**Gating condition:** Parallel changes that edit the *same* capability spec become common (multiple in-flight changes touching one capability).
**Summary:** The single-change archive flow cannot detect when two or more changes both modify the same capability's spec — archiving them one at a time can silently apply deltas in the wrong order or let one overwrite another. A former `bulk-archive` skill detected these cross-change collisions (it built a `capability → [changes]` map and resolved sync order before applying). It was removed (commit `8e325ee`) because it archived multiple changes in one inline pass with no pre-handoff checkpoint or scoped recovery — the opposite of the hardened, serialized, one-change-at-a-time archive flow. The collision-detection was the one genuinely unique capability lost in that removal.
**Dependencies / notes:** If reintroduced, rebuild it on the current hardened model (per-change pre-handoff checkpoint + archive-executor delegation + scoped recovery), not as an inline batch pass. Until then, when archiving multiple changes that touch overlapping capabilities, manually check for spec collisions before syncing.
