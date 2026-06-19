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

## `openspec update` skill-clobber — NON-ISSUE (already handled) — closed 2026-06-18
**Priority:** ~~Medium-High~~ — CLOSED, no action.
**Resolution:** The clobber *mechanism* is real — `OpenSpec/src/core/update.ts` regenerates a hardcoded `SKILL_NAMES` set with a plain `writeFile` (no merge), and our 7 `.claude/skills/openspec-*/SKILL.md` carry `generatedBy: "1.4.1"` with heavily customized bodies. **But the workflow already neutralizes it:** new-repo bootstrap is `cp -r` + fill placeholders (no generation step); `sync_scaffold.py` propagates by file-copy and has no init/clone mode; downstream repos have no `package.json` (no npm postinstall); and `README.md` (L49-53 + L136-143) already bans `openspec init`/`update` twice with rationale + recovery (`git checkout .claude/skills`). The only CLI commands used are change-lifecycle (`new change`/`status`/`archive`/`validate`), which don't touch skills. Earlier framing as a "landmine needing a CI guard" was over-engineering. Full detail: `memory/research/explore-agent-context-infra-2026-06-18.md` §6.4 + §7.1.
**Dependencies / notes:** Optional marginal nicety — the ban is in README (human-facing) not AGENTS.md (agent-facing); a one-line mirror would cover an agent that skips the README, but not worth a change on its own. Only revisit if the workflow ever starts consuming upstream skill regeneration.

## Cross-repo agent-sync — keep + harden the bespoke span-merge (copier ruled out)
**Priority:** Medium
**Gating condition:** None blocking — the spike is done. Future work is incremental hardening only (a repo registry if scale grows past 3).
**Summary:** Cross-repo sync is already ~90% solved by the bespoke `sync_scaffold.py` span-merge. **Spike done (2026-06-18): `copier` is RULED OUT** — it has no intra-file region primitive, so our "replace 2 spans, preserve title/project-context/tail" need degrades into whole-file 3-way merges that emit conflict markers on nearly every update; strictly worse than the current span-merge. The OpenSpec audit also confirmed the sync is **legitimately bespoke** — OpenSpec's global-overrides/community-schemas carry only schema.yaml + artifact templates, never skill bodies, executor agents, AGENTS.md spans, or ai-docs (our actual payload). So: **harden the homegrown script, don't migrate.** Optionally add a truly-universal *TEXT* layer via the two global AGENTS files (`~/.claude/CLAUDE.md` + `~/.config/opencode/AGENTS.md`); the global OpenCode `instructions:` array is fragile (replace-not-concat). `@import` stays disqualified (no-op in OpenCode, confirmed). Scale fixed at **3 repos** (below the 5+ that would justify a heavy standard tool). Full options/ruled-out: `memory/research/explore-agent-context-infra-2026-06-18.md` §2 + §6.2/§6.3.
**Dependencies / notes:** Dual-harness (Claude Code + OpenCode) is the hard constraint. See also `memory/research/research-single-source-2026-06/`.

## Context onboarding — lean AGENTS.md + bound the mutable state files
**Priority:** Medium
**Gating condition:** None blocking — boot cost measured (2026-06-18).
**Summary:** Boot cost measured: **neither repo is cheap** (psc-monitor ~16-22k, extrends ~20-72k always-loaded tokens). The surprise — **extrends is the worse per-session case, not psc-monitor**: psc-monitor's bulk is a *stable* 47KB AGENTS.md appendix that prompt-caching largely amortizes (~4k marginal), while extrends' bulk is *mutable* Layer-3 state (STATUS+open-questions ~14k, decisions.md up to ~52k) that changes every session and pays full reload. So the fix is two-pronged: (1A) still move psc-monitor's appendix to `ai-docs/`/`config.yaml` (cuts cold-cache + OpenCode cost, harmonizes repos), and — now the **primary** lever — (1B) **bound + lightly structure the mutable state files** (e.g. decisions.md headers-only at boot, rotate/archive resolved entries, cap STATUS/open-questions). The `bootstrap_context.py` compiler (1C) is **NOT** needed; simpler bounding + progressive disclosure suffices. Full analysis: `memory/research/explore-agent-context-infra-2026-06-18.md` §1 + §6.1.
**Dependencies / notes:** Token figures are bytes/4 estimates (direction, not exact). The cache argument assumes prompt caching active + weaker under OpenCode. "Context rot" is a session-length phenomenon; a boot-time compiler doesn't cure it.

## Scaffold consolidation — hardening + propagation (supersedes scaffold-sync) — ✅ DONE 2026-06-17 — COMPLETE
**Priority:** ~~High~~ — COMPLETE. All findings shipped.
**Resolution:** The full W0–W7 family shipped + archived (2026-06-16…2026-06-17): W0 hook-wiring smoke, W1 fix-sync-mechanism, W2 dedup-scaffold, W3 fix-convergence-guard, W4 lifecycle-gates, W5 cleanup-workflow-ergonomics, W6 propagate-baseline, W7 single-source-rules. The one-time propagation (W6) carried scaffold HEAD to `extrends` (`176d554`) and `psc-monitor` (`6541a9d`) via `scripts/sync_scaffold.py`; the superseded `scaffold-sync` change was deleted (its surviving parts shipped in W1 + W6). The final audit finding — C2 (within-scaffold rule-restatement dedup) — graduated as the `single-source-rules` change (C2/W7, 2026-06-17), closing the consolidation ledger. All three repos are now converged on one workflow source, with the commit-test gate + scaffold-managed guard wired (dormant) downstream, and all five rule-families single-sourced with canonical homes and cite-don't-restate convention. Per-change records in `memory/STATUS.md` and the archive; design ledger in `memory/research/consolidation-plan-2026-06-16.md` + `memory/research/workflow-audit-2026-06-16.md`.
**Dependencies / notes:** Consolidation family fully complete.

## Cross-change spec-conflict detection at archive
**Priority:** Low
**Gating condition:** Parallel changes that edit the *same* capability spec become common (multiple in-flight changes touching one capability).
**Summary:** The single-change archive flow cannot detect when two or more changes both modify the same capability's spec — archiving them one at a time can silently apply deltas in the wrong order or let one overwrite another. A former `bulk-archive` skill detected these cross-change collisions (it built a `capability → [changes]` map and resolved sync order before applying). It was removed (commit `8e325ee`) because it archived multiple changes in one inline pass with no pre-handoff checkpoint or scoped recovery — the opposite of the hardened, serialized, one-change-at-a-time archive flow. The collision-detection was the one genuinely unique capability lost in that removal.
**Dependencies / notes:** If reintroduced, rebuild it on the current hardened model (per-change pre-handoff checkpoint + archive-executor delegation + scoped recovery), not as an inline batch pass. Until then, when archiving multiple changes that touch overlapping capabilities, manually check for spec collisions before syncing.
