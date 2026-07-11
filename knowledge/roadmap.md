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

## Scaffold hardening from downstream audit evidence (6-item backlog) — 2026-07-10
**Priority:** High
**Gating condition:** None blocking — analysis complete; each item is a candidate OpenSpec change in this repo. Recommend landing order OW-1 → OW-6.
**Summary:** Correctness audits of both downstream repos (`extrends` 33 live classes across 4 waves; `psc-monitor` 1 wave + test-quality audit) converge on one systemic scaffold weakness: the scaffold pays for **multi-model breadth on each single diff** but pays **nothing** for (1) a **lesson→check ratchet** (found bugs become prose in `lessons.md`, never an enforced check, so identical shapes re-ship in sibling code — proven in both repos), (2) **test-quality gating** (tautological/forced-green asserts, discarded return flags, self-mocking shipped in bulk; both repos reconstructed behavioral oracles only post-hoc), (3) **accreted-composition review** (verify is single-diff-scoped; subsystems built from many approved changes are never reviewed whole), and (4) **data-scale enforcement** (prose rule, unbounded `fetchall()` recurred). The verify self→pro→flash stack runs the *same checklist* three times (model breadth, not lens diversity) and the bugs walked through all three — so the recommended token move is to **redirect the third pass to a lens the stack lacks**, not add passes. Six scoped items with tiers + Fable-vs-Opus routing.
**Dependencies / notes:** Full analysis + evidence + gate cost ledger: `knowledge/research/scaffold-gap-analysis-2026-07/` (`SYNTHESIS.md`, `OUTSTANDING-WORK.md`, per-repo issue catalogs). Highest-yield item (OW-1, test-quality detector) needs Fable not at all — Opus end-to-end. Reserve Fable for the novel/high-blast-radius designs (OW-2 ratchet, OW-3 verify redirect, OW-5/6 audit skills).

## Correctness-audit meta-hardening (OW-15) — 2026-07-11
**Priority:** Medium
**Gating condition:** OW-5 (`correctness-audit-skill`) must apply first — OW-15 amends the capability it creates.
**Summary:** psc-monitor's 2026-07-11 coverage-gap review exposed two audit-protocol failure modes the frozen OW-5 design doesn't defend against: **silent wave-drop** (an incomplete audit fell off every tracker when the remediation program took over the "wave" namespace — dossier-internal state can't defend against the dossier not being read) and **scope blind spots** (the census proves completeness *within* the chartered surface list; nothing checks the scope itself — five dimensions were never chartered, one an S4-class live gate: no implemented backup covered any non-reconstructible store). OW-15 adds: an audit-liveness Active-item requirement + dossier-lint check; a chartered blind-taxonomy coverage-gap review at close-out; a generic scope-seeding dimension checklist for the charter-instantiation walk.
**Dependencies / notes:** Evidence + genericized 45-dimension taxonomy: `knowledge/research/scaffold-gap-analysis-2026-07/psc-coverage-gap-review-2026-07-11.md`; OW-15 entry in `OUTSTANDING-WORK.md` same dir; pointer left in `openspec/changes/correctness-audit-skill/notes.md` (freeze not reopened).
**Update 2026-07-12 (extrends convergence):** extrends independently ran the same blind close-out review against its four-wave audit — second validation (n=2), first cross-repo checklist yield in both directions. OW-15 widened in place (no new OW number): **Delta 4** = post-close coverage-liveness ledger (unaudited-code ledger appended at verify/archive, mini-wave trigger; reference impl in extrends), plus Delta-3 checklist widenings (measurement-pipeline parity; run-vs-period-indexed re-run distortion; phantom capability claims; cross-stream boot-doc rule; verified-safety-claim tagging; config-census smell signature). Evidence: `knowledge/research/scaffold-gap-analysis-2026-07/extrends-coverage-gap-review-2026-07-12.md`.

## Workflow-efficiency wave (OW-7..13) — 2026-07-11
**Priority:** Medium (defect-prevention wave above outranks it)
**Gating condition:** Frozen batch OW-2→3→5→6 must apply first — OW-7/9/11 edit the same skill files OW-3 rewrites.
**Summary:** Second-wave audit traced the lifecycle step-by-step and mined 81 archived changes across
all 3 repos for operational friction. Eight Opus-tier items: delegation wrapper + run-telemetry ledger
(OW-7), delegated-context caching hygiene — AGENTS.md is auto-injected into every deepseek call and is
the highest-churn boot file (OW-8), instruction-surface contradiction sweep incl. autonomy-vs-phase-gate
(OW-9), apply-executor targeted-tests + resume contract (OW-10), skill de-bloat + mechanized
freeze/notes gates (OW-11), archive mechanization (OW-12), knowledge-surface bounding round 2 incl. a
boot-surface byte budget (OW-13), delegation-by-default mechanics — haiku tier in the model matrix +
point-of-action cues so run-and-extract work leaves the orchestrator (OW-14).
Also records the evidence-gated scheduled decisions (premise-gate downgrade; MEDIUM pro-pass downgrade)
and an explicit do-not-build list. **After this wave: scaffold optimization is at diminishing returns —
spend downstream.**
**Dependencies / notes:** Full analysis: `knowledge/research/workflow-audit-2026-07-11/AUDIT.md`;
backlog registry: `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` (single source
for OW numbering, routing, order). All wave-2 items Opus end-to-end; Fable-tier backlog closed.

## `openspec update` skill-clobber — NON-ISSUE (already handled) — closed 2026-06-18
<!-- lint:keep --> <!-- resolved investigation, no shipped change to graduate to; retained as the durable "already checked, not an issue" record. -->
**Priority:** ~~Medium-High~~ — CLOSED, no action.
**Resolution:** The clobber *mechanism* is real — `OpenSpec/src/core/update.ts` regenerates a hardcoded `SKILL_NAMES` set with a plain `writeFile` (no merge), and our 7 `.claude/skills/openspec-*/SKILL.md` carry `generatedBy: "1.4.1"` with heavily customized bodies. **But the workflow already neutralizes it:** new-repo bootstrap is `cp -r` + fill placeholders (no generation step); `sync_scaffold.py` propagates by file-copy and has no init/clone mode; downstream repos have no `package.json` (no npm postinstall); and `README.md` (L49-53 + L136-143) already bans `openspec init`/`update` twice with rationale + recovery (`git checkout .claude/skills`). The only CLI commands used are change-lifecycle (`new change`/`status`/`archive`/`validate`), which don't touch skills. Earlier framing as a "landmine needing a CI guard" was over-engineering. Full detail: `knowledge/research/explore-agent-context-infra-2026-06-18.md` §6.4 + §7.1.
**Dependencies / notes:** Optional marginal nicety — the ban is in README (human-facing) not AGENTS.md (agent-facing); a one-line mirror would cover an agent that skips the README, but not worth a change on its own. Only revisit if the workflow ever starts consuming upstream skill regeneration.

## Cross-repo agent-sync — keep + harden the bespoke span-merge (copier ruled out)
**Priority:** Medium
**Gating condition:** None blocking — the spike is done. Future work is incremental hardening only (a repo registry if scale grows past 3).
**Summary:** Cross-repo sync is already ~90% solved by the bespoke `sync_scaffold.py` span-merge. **Spike done (2026-06-18): `copier` is RULED OUT** — it has no intra-file region primitive, so our "replace 2 spans, preserve title/project-context/tail" need degrades into whole-file 3-way merges that emit conflict markers on nearly every update; strictly worse than the current span-merge. The OpenSpec audit also confirmed the sync is **legitimately bespoke** — OpenSpec's global-overrides/community-schemas carry only schema.yaml + artifact templates, never skill bodies, executor agents, AGENTS.md spans, or ai-docs (our actual payload). So: **harden the homegrown script, don't migrate.** Optionally add a truly-universal *TEXT* layer via the two global AGENTS files (`~/.claude/CLAUDE.md` + `~/.config/opencode/AGENTS.md`); the global OpenCode `instructions:` array is fragile (replace-not-concat). `@import` stays disqualified (no-op in OpenCode, confirmed). Scale fixed at **3 repos** (below the 5+ that would justify a heavy standard tool). Full options/ruled-out: `knowledge/research/explore-agent-context-infra-2026-06-18.md` §2 + §6.2/§6.3.
**Dependencies / notes:** Dual-harness (Claude Code + OpenCode) is the hard constraint. See also `knowledge/research/research-single-source-2026-06/`.

## Cross-change spec-conflict detection at archive
**Priority:** Low
**Gating condition:** Parallel changes that edit the *same* capability spec become common (multiple in-flight changes touching one capability).
**Summary:** The single-change archive flow cannot detect when two or more changes both modify the same capability's spec — archiving them one at a time can silently apply deltas in the wrong order or let one overwrite another. A former `bulk-archive` skill detected these cross-change collisions (it built a `capability → [changes]` map and resolved sync order before applying). It was removed (commit `8e325ee`) because it archived multiple changes in one inline pass with no pre-handoff checkpoint or scoped recovery — the opposite of the hardened, serialized, one-change-at-a-time archive flow. The collision-detection was the one genuinely unique capability lost in that removal.
**Dependencies / notes:** If reintroduced, rebuild it on the current hardened model (per-change pre-handoff checkpoint + archive-executor delegation + scoped recovery), not as an inline batch pass. Until then, when archiving multiple changes that touch overlapping capabilities, manually check for spec collisions before syncing.
