# Notes — reconcile-parked-backlog (MEDIUM)

## Why this change

The parked backlog has decayed in two directions with one shared root cause:

- **Stale paper.** 27 tracked items describe work that already shipped. Three were filed
  stale *by their own change's archive commit* — `repo-lint-fetchall-docstring.md` was
  filed 10 minutes AFTER its own fix landed (`e90961a2` 22:25:43 → `6d8024c` 22:35:59,
  same change); `data-lint-sqlite-backend.md` was filed by commit `8ceb1cc`, whose own
  message says it "accompanies the **already-committed** data_lint SQLite backend
  (`e604990`)".
- **Unexecuted ready work.** A cluster of live mechanical gaps sits parked, two of which
  have now met their own recorded revisit triggers.

**Root cause (D3 below):** archive files follow-on questions from `notes.md` without
checking whether the change itself already resolved them. Sweeping the tracker without
fixing the filing step means it re-decays — so the fix ships with the sweep.

## Operator routing

- **Apply pre-routed to Sonnet-first**, per explicit operator instruction this session:
  *"For apply-executor and archive, use sonnet subagent instead of deepseek."* This is the
  AGENTS.md operator pre-route carve-out ("operator MAY pre-route a specific change's apply
  to Sonnet-first, recorded in that change's notes.md"). Justified independently by the work
  itself: evidence-gated prose surgery across 17 tracker files is judgment-adjacent, exactly
  the "judgment-heavy prose surgery" the carve-out names.
- **Autonomy:** operator granted autonomy through verify, halting before archive.
- **Model tier:** Opus, not Fable. Execution-heavy with well-evidenced judgment; per the
  operator's Fable-scarcity working style, execution routes to Opus. No handoff warranted.

## Design decisions

**D1 — `scaffold_lint` vocabulary is derived from tombstones, not hand-maintained.**
`_NON_OPENSPEC_SKILL_TOKENS` is a *scan vocabulary*, not a validity list: `valid_tokens`
is derived from disk (`_skill_dir_names`), so any token naming an existing skill dir
always resolves and can never produce a finding. Consequence: **merely adding the 4
missing current skill names would be a behavioral no-op.** The set only ever fires for a
name in the vocabulary that is absent from disk — i.e. a *retired* skill. D2's recorded
trade-off (drop the name at removal) is therefore precisely what makes removed-name
detection impossible.

Retired `openspec-*` names already get removed-name detection for free via `_TOKEN_RE`'s
pattern match. Non-openspec names have no shared prefix, so they got a hand-maintained
set instead — which drifted. **Fix: derive the vocabulary from
`scripts/scaffold_manifest_removed.txt`**, which already tombstones exactly these
(`lint-knowledge`, `outstanding-work-review`) because removing a scaffold-managed skill
already requires a tombstone for downstream deletion. This brings non-openspec names to
parity with `openspec-*` names, deletes the hand-maintained set that drifted, and makes
drift structurally impossible rather than merely detected.

*Blast radius verified:* `grep -rn` over the scanned surface (`AGENTS.md`,
`.claude/skills/`, `.claude/agents/`, `.opencode/agents/`) finds zero references to
either retired name — the new tokens flag nothing today. References in `openspec/changes/`
and `knowledge/` are outside the scanned surface and unaffected.

*Rejected:* adding the 4 names + a coverage SEAL asserting the set matches disk. It
mechanizes maintenance of a set whose current-skill entries do nothing, and leaves the
actual blind spot (removed names) open.

**D2 — The tracker sweep is apply work, not archive work.** AGENTS.md defers
`knowledge/questions/INDEX.md` edits to archive. That rule targets *incidental* status
writes during unrelated busy work in a bloated context. Here the tracker content **is the
change's deliverable**: it is evidence-gated against `verify-stale.md` and must pass
verify. Deferring it to archive would skip verify for the bulk of the change and overload
the archive-executor with work its fresh-context seeding cannot support. Archive still
reconciles normally afterward, adding this change's own follow-on entries.

**D3 — Root-cause fix scoped to an instruction, not a detector.** "Was this follow-on
already resolved by this very change?" is a judgment call, not a decidable predicate — no
deterministic check can settle it. So the fix is a targeted obligation in the archive
skill's reconciliation step. Recorded as a deliberate departure from mechanism-over-docs
preference, because the mechanism does not exist to be had here.

*Fresh evidence for D3, from this change's own review:* the round-1 pro reviewer caught
`tasks.md` doing exactly what D3 indicts — tasks 2 and 4.1 fix problems whose tracker files
(`scaffold-lint-removed-name-blindspot.md`, `audit-skill-metadata-cleanup.md`) were never
scheduled for closure, which would have left two freshly-stale entries behind. The error is
this easy to make even while writing the change *about* the error. That is the argument for
the obligation being written down at the point of filing rather than left to diligence.
Fixed in tasks 2.6 and 4.2.

## Assumptions

- The 27 STALE verdicts rest on an adversarial re-verification pass
  (`verify-stale.md`) that tried to refute each one and reversed none at code level, but
  downgraded 14 from DELETE to TRIM (live sibling items inside). **Trim lists are
  authoritative — never delete a TRIM-marked file wholesale.**
- `plans/outstanding-work-review-residual-sweep.md` is fully obsolete: T1-T3 shipped
  verbatim into `outstanding-work-deep-sweep`; T4/T5 are tracked more currently in
  `split-outstanding-work-skills-follow-ons.md` + `pending-downstream-propagation.md`.

## Defects found during apply (and by what)

- **Orphan-citation cascade from task 3.4, caught by the live-tree `knowledge_lint` gate.**
  Deleting `plans/plans-scope-alignment.md` orphaned citations in two files beyond the INDEX
  pointer the task anticipated (`outstanding-work-collector-follow-ons.md:13`,
  `knowledge-surface-bounding-2-follow-ons.md:24`). The adversarial pre-pass caught this exact
  class for the Group 6 deletions (task 6.8) but nobody ran the check against the Group 3
  deletion. Fixed by task 6.9.

  *Lesson:* when a task deletes a tracked file, the cascade sweep is
  `grep -rn "<basename>" knowledge/ openspec/specs/` — not just "remove its INDEX pointer".
  No new mechanism is warranted: `broken-prose-path-citation` already detects this and is what
  found it. The planning missed it; the gate held. That is the system working as designed.

- **The prior apply-executor died mid-run** (session limit) without reporting. Its checkboxes
  through Group 5 were verified against disk rather than trusted: `git status` matched the
  expected file set and `check.sh` showed 637 passed with the single failure above — which was
  caused by task 3.4's cascade, not by any Group 1-5 defect.

- **D1's no-op trap was verified empirically, not assumed.** `_removed_skill_names()` uses
  `re.fullmatch(r"\.claude/skills/([^/]+)")` against manifest entries that are written with a
  trailing `/` — had `_read_removed_manifest_entries` not stripped it, the vocabulary would be
  silently EMPTY and task 2.5's "zero findings" would still have passed (an empty vocabulary
  also yields zero findings). Confirmed non-empty: `{lint-knowledge, outstanding-work-review,
  openspec-onboard}`. Further confirmed the new retired-name test is not vacuous by reverting
  `scaffold_lint.py` and re-running it: it fails pre-change (`0 = len([])`), passes post-change.

- **Three further orphan-citation cascades** beyond task 6.9, found by the executor re-running
  `knowledge_lint` after the Group 6 deletions: `composition-audit-cadence-follow-ons.md:40`
  (cited deleted `run-audit-untested.md`), plus `knowledge/reference/audit-runbook.md:86` and
  `pending-downstream-propagation.md:22` (both cited deleted `data-lint-sqlite-backend.md`).
  Reworded to state the live fact rather than point at dead files. The underlying fact was
  operator-verified against the live downstream checkout: extrends' `checks.toml` still disables
  `data-lint` with a "Postgres-only … blocked on an upstream scaffold change" comment, though the
  upstream SQLite backend shipped in `e604990` with 14 dedicated tests. That downstream re-wiring
  is now recorded in the propagation ledger, which is its correct home.

- **`resync-verification.md` §7 was actively misleading** (found via the executor's flag, fixed by
  the orchestrator). It claimed "the manifest has no delete mechanism, so a file the scaffold
  removed still lives downstream until deleted by hand" and named `openspec-onboard` as "currently
  owed". Both false: `_read_removed_manifest`/`_delete_removed_entries` are wired
  (`sync_scaffold.py:63/317/326`), and `openspec-onboard` is already gone from both downstreams.
  This is worse than a stale tracker entry — it is a runbook instructing future agents to do
  manual work the mechanism already does. Rewritten to describe the tombstone contract.

- **A dangling reference the linter structurally cannot see.**
  `lean-boot-context-follow-ons.md:5` pointed at `parked-follow-ons.md` — a pre-restructure
  `ai-docs/` filename that has not existed since the knowledge-tree migration. It survived
  undetected because `broken-prose-path-citation` only inspects **backtick-wrapped** tokens, and
  this reference was bare prose. Repointed to `knowledge/questions/parked-psc-monitor.md`.
  *Follow-on worth parking:* un-backticked filename references dangle invisibly. Widening the
  check to bare tokens would be noisy (the backtick-only scope is a deliberate false-positive
  guard), so the realistic mitigation is authoring discipline — always backtick a citation. Low
  priority; recorded rather than fixed here.

## Verification (change-specific acceptance criteria)

MEDIUM tier: acceptance criteria live here, not in a design.md (AGENTS.md).

1. `scripts/check.sh` green (ruff check + format + full pytest, incl. `scaffold_lint`
   invariant SEAL and the live-tree `test_doc_lint_gate`).
2. `openspec validate --strict` exits 0.
3. **freeze_check:** `**VERDICT:** PASS` and `**PREMISE:** AGREE` parse identically to
   their unbolded forms; a genuinely missing verdict still returns
   `BLOCKED — missing-verdict`. Both directions must be tested — a fix that accepts
   everything is not a fix.
4. **scaffold_lint:** `python3 scripts/scaffold_lint.py` reports zero findings on the
   current tree (blast radius verified clean). A synthetic doc referencing
   `outstanding-work-review` in the scanned surface IS flagged — proving the blind spot
   is actually closed and the test is not vacuous.
5. **plans/ scope:** `knowledge_lint.py` and `outstanding.py` agree on recursive `plans/`
   gathering; a nested `plans/sub/x.md` fixture is seen by both.
6. **Tracker truth:** `python3 scripts/knowledge_lint.py` clean — specifically no dangling
   citation to any deleted file. Every `INDEX.md` pointer resolves.
7. **No live work lost:** each TRIM-marked file retains its live sibling items per
   `verify-stale.md`. This is the single highest-risk property of the change.
8. `python3 scripts/facts.py --check outstanding` regenerates without error and the open
   count drops (stale entries retired).

## Deferred / surfaced to operator (NOT in scope)

- **`boot_surface_lint` WARN — CLEARED by this change, but only just.** It was WARN at 81438
  bytes (threshold 80000) when this change was scoped, and this note originally predicted the
  sweep would *not* clear it. That prediction was wrong: the tracker sweep shaved ~1.8KB and the
  surface is now **79607 bytes — OK**. Recorded as a correction rather than quietly fixed.
  The margin is thin (393 bytes) and `decisions/INDEX.md` alone is still ~33KB, so the
  `decisions/INDEX.md` year-split (parked: `knowledge-surface-bounding-2-follow-ons.md`) stays
  live and will be needed again shortly — this change bought headroom, it did not solve it.
- **Composition audit is DUE** — 46 archived changes (≥10), 211 commits (≥100). An
  operator ceremony, not a change.
- **`commit-gate-bypass`** — the `if: Bash(git commit*)` matcher is prefix-anchored and
  Claude-only; a git-native `core.hooksPath` hook is the recommended direction. Real, but a
  cross-agent design decision deserving its own change. Newly parked; stays parked.
- **`knowledge-lint-gitignored-citation-exempt/`** — verified and landed (`7f23eda`),
  needs only an archive-move. Operator gate.
- Higher-risk parked items left untouched: verifier literal-spelling bypass, OpenCode
  gate-plugin gap, E501 ratchet, data_lint credential hygiene, dead-code campaign, and the
  two evidence-gated model-downgrade decisions (ledgers not yet full).
