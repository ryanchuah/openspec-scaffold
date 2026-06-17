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

## Scaffold consolidation — hardening + propagation (supersedes scaffold-sync) — ✅ DONE 2026-06-17 (1 finding deferred → see C2 entry below)
**Priority:** ~~High~~ — COMPLETE except audit C2.
**Resolution:** The full W0–W6 family shipped + archived (2026-06-16…2026-06-17): W0 hook-wiring smoke, W1 fix-sync-mechanism, W2 dedup-scaffold, W3 fix-convergence-guard, W4 lifecycle-gates, W5 cleanup-workflow-ergonomics, W6 propagate-baseline. The one-time propagation (W6) carried scaffold HEAD to `extrends` (`176d554`) and `psc-monitor` (`6541a9d`) via `scripts/sync_scaffold.py`; the superseded `scaffold-sync` change was deleted (its surviving parts shipped in W1 + W6). All three repos are now converged on one workflow source, with the commit-test gate + scaffold-managed guard wired (dormant) downstream. Per-change records in `STATUS.md` and the archive; design ledger in `ai-docs/consolidation-plan-2026-06-16.md` + `workflow-audit-2026-06-16.md`. **One finding from the ledger did not ship: audit C2** (within-scaffold rule-restatement dedup) — twice-deferred (W2→W6) and never re-scoped; see the dedicated entry below.
**Dependencies / notes:** Prune this entry on the next roadmap pass once C2 lands.

## Single-source the restated rules within scaffold (audit C2) — candidate "W7"
**Priority:** Medium
**Gating condition:** None — actionable now. The sync mechanism (W1) and the single-source-then-cite pattern (W2/C1, `ai-docs/delegation-harness.md`) already exist; this applies the same treatment to the restated *rules*. Manifest-changing → schedule its own one-time re-sync to extrends + psc-monitor afterward (cheap, one `sync_scaffold.py` per repo).
**Summary:** The audit's §C2 flagged the same *rules* restated 3–5× across the instruction surface, free to drift independently: "tasks.md = apply-phase only" (~4×), the model-assignment matrix (~5×: AGENTS.md Roles + Change tiers + config.yaml + apply/verify/archive + agent frontmatter), "never record test/doc/row counts" (~5×), the mock-encoded-idealized-API war-story (~3–4× *within scaffold* — W6's Option-Y relocation only moved extrends' *downstream* copies to a lessons doc), and the web-research convention (×2, AGENTS.md vs `ai-docs/research-fetch-convention.md` — earlier made to *agree*, not single-sourced). Dedup each into one authoritative location with the others citing it, the way C1 deduped the delegation harness. Now that the propagation pipe is live, this matters more: scaffold faithfully propagates these restatements (and any drift among them) to all three repos — the "don't pump duplicated content through the pipe" concern from the consolidation plan §1, applied to rules.
**Dependencies / notes:** Findings detail in `ai-docs/workflow-audit-2026-06-16.md` §C2; tracked follow-on in `ai-docs/open-questions.md` ("propagate-baseline (W6) follow-ons"). Each rule needs a chosen canonical home (some belong in AGENTS.md, some in config.yaml, some in a referenced ai-docs doc) — decide per-rule at propose time. Per `golden-source-edit-rules`, dedup must preserve the established rule text verbatim, not paraphrase.

## Cross-change spec-conflict detection at archive
**Priority:** Low
**Gating condition:** Parallel changes that edit the *same* capability spec become common (multiple in-flight changes touching one capability).
**Summary:** The single-change archive flow cannot detect when two or more changes both modify the same capability's spec — archiving them one at a time can silently apply deltas in the wrong order or let one overwrite another. A former `bulk-archive` skill detected these cross-change collisions (it built a `capability → [changes]` map and resolved sync order before applying). It was removed (commit `8e325ee`) because it archived multiple changes in one inline pass with no pre-handoff checkpoint or scoped recovery — the opposite of the hardened, serialized, one-change-at-a-time archive flow. The collision-detection was the one genuinely unique capability lost in that removal.
**Dependencies / notes:** If reintroduced, rebuild it on the current hardened model (per-change pre-handoff checkpoint + archive-executor delegation + scoped recovery), not as an inline batch pass. Until then, when archiving multiple changes that touch overlapping capabilities, manually check for spec collisions before syncing.
