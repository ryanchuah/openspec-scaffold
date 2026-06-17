# Notes — single-source-rules (C2 / "W7")

Tier: **MEDIUM** (tasks.md only), operator-confirmed 2026-06-17. Mirrors `dedup-scaffold` (W2/C1):
extraction-not-redesign single-sourcing, the canonical doc/site assembled from the **exact existing
text**, nothing paraphrased or invented. Source finding: `ai-docs/workflow-audit-2026-06-16.md` §C2;
roadmap entry "Single-source the restated rules within scaffold (audit C2)".

## Why this is two phases

Phase 1 (this change): the full MEDIUM lifecycle (propose → apply → verify → archive), editing
scaffold-managed instruction files in scaffold only. Phase 2 (separate runbook, **operator go-ahead
required** before any cross-repo write): re-sync the changed managed files to `extrends` +
`psc-monitor` via `scripts/sync_scaffold.py` (`--check` → apply → re-`--check` IDENTICAL → per-repo
AGENTS.md span-merge diff-review → commit per repo `--no-verify` → do **not** push). No new manifest
entry is created by this change (see below), so phase 2 is a pure re-sync of already-managed files.

## Canonical-home registry (the design decisions)

The five rule-families the audit flagged as restated 3–5×, each assigned ONE home; every other site
keeps its per-context specifics + a citation. Homes were chosen so that **any site cited by a
manifest-synced file resolves downstream** (the citation target is itself synced or intrinsic).

| # | Rule | Canonical home | Synced? | Other sites → |
|---|------|----------------|---------|---------------|
| 1 | tasks.md = apply-phase only | `openspec/config.yaml` `rules.tasks` | **NOT in manifest** (per-repo); but **prompt-injected** into the tasks/propose artifact prompt locally in every repo — verified: `extrends` + `psc-monitor` both carry the full `rules.tasks` verbatim | propose verbatim copy → cite (safe: the rule is injected locally, so the proposing agent receives it regardless of the skill body); verify/archive interpretive uses keep 1 line + cite; AGENTS.md "MEDIUM emits only tasks.md" is a tier rule (different facet) — untouched |
| 2 | model-assignment matrix | `AGENTS.md` `## Roles` | yes (manifest, span-replace) | AGENTS.md Change-tiers keeps tier-tied model names, cites Roles for the ladder; config.yaml keeps the prompt-injected name + cite; skill prose re-explanations → cite. **Operational `--model …` / `model:` config preserved verbatim** |
| 3 | never record test/doc/row counts | `AGENTS.md` ("Tests green before any commit" bullet) | yes (manifest) | already cited by verify + archive skills + both archive-executor bodies ("see AGENTS.md") — near-done; config.yaml `context:` keeps its prompt-injected short form |
| 4 | mock-encoded-idealized-API war-story | apply-executor body (`.claude` + `.opencode`, byte-identical) | yes (manifest, guard-enforced) | genuine duplication is apply-body ≈ **verify** (same mock-sort story) → verify keeps its live-test action + 1-line ref. **propose tells a DISTINCT companion story** (constructor-kwarg live-probe) → **left intact**, optional "see also" cross-ref only |
| 5 | web-research convention | `ai-docs/research-fetch-convention.md` | yes (manifest) | AGENTS.md keeps a tight 1–2 line summary incl. the load-bearing guardrail (d) + cite; config.yaml `context:` one-liner + cite |

**Convention home (operator's explicit ask — make the rule clear to future agents):**
`ai-docs/workflow-lessons.md` §2 "Golden-source edit rules" gets a new rule ("single-source restated
rules — cite, never re-expand") + a Single-source registry table (the five rows above).
`workflow-lessons.md` is deliberately **NOT manifest-synced** (each repo has its own divergent copy),
which is correct: only scaffold editors edit these rules — downstream repos are blocked from editing
managed files by `scaffold_check.py`, so the "don't re-expand" discipline only needs to bind scaffold.

## Preserve-verbatim guardrails (golden-source rule)

- The rule text at each canonical home is the **existing** text, kept verbatim — no rewrite, no
  "improvement." (Per `ai-docs/workflow-lessons.md` §2 and the W2 golden-source rule.)
- **Operational config is not prose** and is never touched: `--model deepseek/deepseek-v4-flash|pro`
  lines inside skill code blocks; `model:` fields in `.opencode`/`.claude` agent frontmatter.
- The `.claude` + `.opencode` apply-executor bodies must stay byte-identical (the marker in task 5.1
  is added to **both**, identically) so `scripts/test_executor_body_agreement.py` stays green.
- `openspec/config.yaml` `context:` and `rules.tasks` are injected into every artifact prompt — markers
  go in `#` comments OUTSIDE the injected strings, and the load-bearing short forms stay inline.
- No new file is added to `scripts/scaffold_manifest.txt` (war-story home = existing managed agent
  body; convention home = intentionally-unsynced `workflow-lessons.md`; web-research home already in
  the manifest). Phase 2 therefore touches only already-managed files.
- **Rule 1 downstream delivery (resolves reviewer 🔴 #1):** `openspec/config.yaml` is **per-repo and
  NOT manifest-synced** (its `context:` block carries per-repo fills). The "tasks.md = apply-only" rule
  nonetheless reaches every repo's proposing agent because `rules.tasks` is **prompt-injected** into the
  `openspec instructions tasks` output locally — verified that `extrends` and `psc-monitor` both already
  carry the full `rules.tasks` verbatim. So collapsing `openspec-propose`'s duplicate paragraph to a
  citation does NOT strand downstream agents: the rule is delivered by local injection, and the cite
  resolves to a home present in every repo. **Pre-existing residual (parked, out of scope):** because
  the `config.yaml` `rules:` block is per-repo and unsynced, it *could* drift between repos over time; a
  future hardening could sync the `rules:` block via span-logic (like the AGENTS.md span). Record as a
  parked follow-on at archive — do not expand scope here.

## Archive-phase deliverable (NOT a tasks.md item — write-deferred doc)

During this change's archive reconciliation, the archive-executor ALSO drops the **redundant
per-section summary paragraphs** in `ai-docs/open-questions.md`: each legacy `## <change> follow-ons`
section currently opens with a paragraph restating decisions.md/STATUS.md; replace each with the
one-line decisions.md pointer the §3c archive rule already prescribes for new sections, **keeping every
bullet follow-on verbatim** (the bullets are the unique content; the opening paragraphs only restate
content that already lives in decisions.md). This is info-loss-sensitive → it gets an **independent
`deepseek-v4-pro` information-loss review** (operator standing instruction), on top of the orchestrator
review, before commit. Also prune the roadmap C2 entry as it graduates into this change.

## Verification (change-specific acceptance criteria — checked at verify)

1. Each of the five rules appears **in full at exactly one home**; every former duplicate site is
   either a citation or a legitimately per-context application carrying a citation. (Diff-review each
   site against the registry above.)
2. **No behavior change**: no `--model …` code-block line and no frontmatter `model:` field changed;
   `git diff -- .claude .opencode | grep -E '^[-+].*--model|^[-+]model:'` is empty. The fallback ladders,
   budgets, and invocation shapes are unchanged.
3. `python scripts/test_executor_body_agreement.py` passes (apply-executor pair still byte-identical).
4. `openspec validate --all` passes.
5. The single-source registry in `ai-docs/workflow-lessons.md` lists all five rules with correct homes,
   and each home carries its `CANONICAL:` marker; spot-check that a reader at any citation site is told
   where the rule lives and "do not restate."
6. The web-research load-bearing guardrail (d) is still stated (not merely cited) in `AGENTS.md` — the
   convention's full text may be cited, but the don't-call-WebSearch-from-main-thread guardrail stays
   visible at first-load.
7. Independent `deepseek-v4-pro` info-loss review of the `open-questions.md` per-section-summary
   cleanup returns no defect (no bullet follow-on lost; no live blocker dropped).
8. **Each canonical home still contains the full rule text verbatim** (the citation's target is real):
   confirm the full rule is present at each home after the edits (criterion overlaps task 7.4). For the
   per-repo `config.yaml` home, confirm all three repos carry `rules.tasks` (verified at propose for
   `extrends` + `psc-monitor`; re-confirm at Phase 2). For manifest-synced homes, the Phase-2 `--check`
   IDENTICAL gate confirms downstream paths resolve.
9. **Apply-phase info-loss backstop:** for each text block removed at a citation site, the substantive
   rule text appears verbatim at the canonical home (task 7.4) — no rule text was dropped, only relocated
   or pointed-to.
