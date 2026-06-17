# notes — split-open-questions (MEDIUM)

## What this change is

A scaffold instruction-surface change (sibling of `cap-status-log`). It makes
`ai-docs/open-questions.md` cheap to onboard from without losing blocking-item visibility, by
introducing a **horizon split**:

- `ai-docs/open-questions.md` — always-loaded scan list; **active items only** (open blockers,
  operator-decision items, in-flight backlogs that gate other work).
- `ai-docs/parked-follow-ons.md` — the deferred / monitored / low-priority long tail, grouped by
  `##` area, loaded on demand (NOT in the mandatory read).
- `ai-docs/archive/retired-notes.md` — resolved items (unchanged mechanic).

The always-loaded surface is then bounded by the number of *simultaneously-live blockers*, which is
self-limiting — unlike "every open follow-on ever," which accretes one dense cluster per shipped
change and blew past the Read tool's cap in extrends even after a resolved-items prune (the finding
that motivated this change; see `STATUS.md` § "Immediate next action" and the prior
`cap-status-log` follow-ons).

**Chosen approach: C2 (two physical files), MEDIUM tier** — operator-confirmed. The rejected
alternatives (header-scan-only directive; index-only-with-pointers) are recorded for the decisions.md
"why" at archive: header-scan can't reveal which change-named section hides a live blocker without
opening it (unsound for this file's purpose); index-only delays but does not *bound* (grows with
cumulative opens) and breaks for ad-hoc items with no archive to point to. Physical separation
*enforces* the bound rather than merely making it satisfiable — the same reasoning `cap-status-log`
used for the STATUS.md ↔ status-log.md split. The operator's "index + pointer" idea is expressed
*within* C2: AGENTS.md carries the pointer, and the parked file's own `##` headers are its index.

## Scope (mechanism only — migrations are separate, per precedent)

Like `cap-status-log`, this change ships the **rule/mechanism** and applies it prospectively. It does
NOT bulk-migrate any existing `open-questions.md`. Scaffold-managed files edited (these propagate
downstream via `scripts/sync_scaffold.py`): `AGENTS.md` (span-merge), both `archive-executor.md`
bodies, `.claude/skills/openspec-archive-change/SKILL.md`. Per-repo (NOT manifest-managed): the new
`ai-docs/parked-follow-ons.md` stub.

Steady-state routing is deliberately **light**: new follow-ons are *born in the correct file* by
horizon, resolved items prune to retired-notes, and a deprioritized active item *may* move to parked
— but the executor does NOT re-classify the whole legacy file on every archive (that would be
expensive and risks burying a blocker). De-rotting a pre-split file is a one-time migration (below).

## Verification — change-specific acceptance criteria

1. **C4 guard green.** `python3 scripts/test_executor_body_agreement.py` passes — both
   archive-executor bodies remain byte-identical after the §3c edits (sole sanctioned divergence: the
   `.claude` intro clause). This is the load-bearing automated check for this change.
2. **Convergence guard untouched/green.** `python3 scripts/test_convergence.py` passes.
3. **Specs unaffected.** `openspec validate --all` passes (no delta specs in this change).
4. **AGENTS.md internally consistent.** The top MANDATORY read block and the new horizon-split rule
   in the State/write-discipline section agree: open-questions.md is read-in-full + bounded;
   parked-follow-ons.md is on-demand and explicitly out of the mandatory read; the STATUS.md cap
   rule's closing note points to the new rule rather than the old "already prunes resolved" phrasing.
5. **No-blocker-burial is encoded, not just intended.** Both the archive-executor §3c and the archive
   skill verify-checklist state that a live blocker is never parked and that the reviewer must confirm
   no blocker was parked. Read both back and confirm the wording is present.
6. **parked-follow-ons.md home exists** with the documented preamble + format comment, and is NOT in
   `scripts/scaffold_manifest.txt` (it is per-repo state).
7. **Behavioral dogfood at this change's own archive.** When this change archives, the archive-executor
   runs under the new §3c rule and must route this change's own follow-ons by horizon
   (active → open-questions.md, parked → parked-follow-ons.md), creating/populating the parked file.
   The primary reviews that routing + runs the independent deepseek-v4-pro information-loss review
   (per the standing cross-repo/info-loss feedback rule) before committing.

Note: because this change does NOT migrate the legacy `open-questions.md`, scaffold's own file stays
large (legacy sections remain) until the one-time migration below runs — expected, not a rule failure
(same posture `cap-status-log` left for scaffold's own STATUS.md).

## Candidate open-questions / follow-ons for archive

- **[Propagation backlog — HIGH, BLOCKING downstream effect]** The mechanism is scaffold-only and
  inert in `extrends` + `psc-monitor` until propagated. After archive, run
  `scripts/sync_scaffold.py --check ../extrends` and `--check ../psc-monitor` (dry-run), confirm only
  this change's managed files DIFFER, then apply + re-check IDENTICAL + review each repo's AGENTS.md
  span-merge (title / `## Project context` / tail preserved) + commit per repo. Needs explicit
  operator in-session go-ahead for the cross-repo writes; do NOT push.
- **[One-time migration of extrends `open-questions.md`]** This is the real over-cap case. After the
  rule propagates, split extrends' file into active + parked via a byte-integrity-gated one-off (pure
  line-partition where each bullet lands in exactly one of {active, parked, retired}; recombine ==
  source byte-for-byte; idempotent). Reuse/adapt the `extrends/scripts/_open_questions_prune_oneoff.py`
  pattern. Classification (active vs parked) is judgment → author it, get the independent
  deepseek-v4-pro information-loss review, do NOT delegate the classification to flash. Re-measure
  extrends' `open-questions.md` against the Read cap afterward to confirm onboarding is satisfiable.
- **[One-time migration of scaffold's own `open-questions.md`]** Same treatment when convenient
  (scaffold's file is borderline, not yet clearly over cap). De-rotting also clears the five stale
  "Propagation backlog (HIGH)" bullets that W6 resolved but were never pruned.
- **[Redundant per-section summary paragraphs (LOW, overlaps C2/W7)]** Each legacy `open-questions.md`
  section opens with a paragraph restating decisions.md/STATUS.md. The new §3c rule stops authoring
  these for new sections (one-line decisions.md pointer instead); dropping the existing ones is a
  cleanup that pairs with the migration and with the C2/W7 rule-restatement dedup.
- **[psc-monitor — no migration needed]** Still small; inherits the corrected rule on the next sync.

---

## Verify checkpoint (2026-06-17)

1. **Verdict:** READY FOR ARCHIVE. Two independent gates agree — primary self-review (behavioral) +
   deepseek-v4-pro verifier pass (VERDICT: READY, zero defects, real verifier confirmed). The flash
   pass was skipped by explicit operator instruction this session. Simplicity/quality gate: clean
   (no duplication / single-use abstraction / dead code / over-parameterization — the rule lives once
   in AGENTS.md as policy, with the executor §3c and skill checklist as its operational enforcement,
   mirroring the cap-status-log pattern). Security gate: not triggered (no auth/credentials/data/
   external-API surface).

2. **Live output eyeballed (behavior, not counts):** Ran `sync_scaffold.py --check` read-only against
   BOTH downstream repos — the edited AGENTS.md span-merged cleanly (no parse error/exception) and the
   drift set was exactly this change's four managed files (AGENTS.md + both archive-executor bodies +
   the archive SKILL.md), every other managed file IDENTICAL, the manifest IDENTICAL. Eyeballed the
   rendered AGENTS.md MANDATORY-read block: the inserted parked-follow-ons sentence reads coherently in
   place after the archive/changes skip directive. Confirmed the two archive-executor §3c bodies render
   byte-identical (guard + direct comparison). Confirmed `ai-docs/parked-follow-ons.md` exists with the
   intended preamble + format comment and is absent from the manifest.

3. **Defects found and how fixed:** No defects from the pro pass (zero). The primary's own self-review
   (diff read) caught two trivial whitespace drifts the flash apply-executor introduced — a 3-space
   (vs 2) paragraph-continuation indent in AGENTS.md and a 6-space (vs 5) list-bullet indent in the
   archive SKILL.md quality-check list (the latter would have misrendered the bullet as nested under
   the decisions.md item). Both fixed inline by the primary under the sanctioned trivial-typo
   exception; content untouched; guards re-confirmed green.

4. **As-built deltas:** None beyond what tasks.md specifies. The only deviations from a verbatim
   transcription were the two whitespace fixes in field 3. (Worth flagging for the decisions.md "why"
   at archive: the new §3c deliberately replaces the prior per-section "one-paragraph summary" with a
   one-line decisions.md pointer — this is intended scope, already stated in tasks.md/notes, not a
   hidden delta.)

5. **Forward-looking items for the project docs:** Nothing NEW surfaced during verify — the behavioral
   review confirmed the design as-intended. All forward-looking items remain those already enumerated
   in the "Candidate open-questions / follow-ons for archive" section above, which archive must fold
   into `ai-docs/open-questions.md` (and the rejected-alternatives "why" into `ai-docs/decisions.md`):
   (a) **[HIGH / BLOCKING downstream]** propagate the 4 managed files to extrends + psc-monitor
   (operator go-ahead required; no push); (b) one-time migration of **extrends** `open-questions.md`
   (the real over-cap case) — byte-integrity-gated, judgment-classified, independent pro info-loss
   review; (c) one-time migration of **scaffold's own** `open-questions.md` (de-rots the five stale
   resolved "Propagation backlog (HIGH)" bullets); (d) **[LOW, overlaps C2/W7]** drop the redundant
   per-section summary paragraphs from legacy `open-questions.md`; (e) psc-monitor needs no migration
   (inherits the rule on next sync).

**Still owned by archive (do NOT reconcile here):**
- `STATUS.md` — new `## Latest change` paragraph (apply the 3-paragraph cap; overflow → status-log.md).
- `ai-docs/decisions.md` — append the decision with the rejected alternatives ((a) header-scan-only,
  (c) index-only) and the "why C2/physical-split" rationale.
- `ai-docs/open-questions.md` + `ai-docs/parked-follow-ons.md` — **first live dogfood**: route THIS
  change's own follow-ons under the new §3c rule (active → open-questions.md, parked →
  parked-follow-ons.md); primary reviews the routing + runs the independent deepseek-v4-pro
  information-loss review before committing.
- Spec promotion: none (no delta specs in this MEDIUM change).
- Cleanup: delete `tmp_handover_prompt.md` (untracked, safe) when convenient.
