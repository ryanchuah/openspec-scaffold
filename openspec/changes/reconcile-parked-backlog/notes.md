# Notes — reconcile-parked-backlog (MEDIUM)

## Why this change

The parked backlog has decayed in two directions with one shared root cause:

- **Stale paper.** 27 tracked items describe work that already shipped. **Two** were filed
  stale *by their own change's archive commit* — `repo-lint-fetchall-docstring.md` was
  filed 10 minutes AFTER its own fix landed (`e90961a2` 22:25:43 → `6d8024c` 22:35:59,
  same change); `data-lint-sqlite-backend.md` was filed by commit `8ceb1cc`, whose own
  message says it "accompanies the **already-committed** data_lint SQLite backend
  (`e604990`)".
  *(Corrected at verify from "Three": `run-audit-untested.md` was also stale, but by a
  different mechanism — it named its own resolution condition and that condition was met
  later by extrends, so it was not filed-stale-by-its-own-change. The two-file count is the
  one that evidences D3; the commit messages for `9344a7a`/`aba963f` say "three" and are
  wrong on this point — history left unrewritten, corrected here.)*
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
- **Autonomy:** initially granted through verify (halt before archive); **extended to archive**
  by the operator in the follow-up session that resumed this change after the first apply
  executor hit a session limit. Archive also pre-routed to Sonnet by the same instruction.
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

## Verify checkpoint

**1. Verdict:** READY for archive. Self-review READY; `deepseek/deepseek-v4-pro` behavioral
pass `VERDICT: READY` (zero defects); simplicity/quality gate PASS.
Security review: **not triggered** — the change touches no auth, credentials/secrets, persisted
data, or external API/network surface. Data-path rule: **not triggered** — no data path modified,
so no at-scale run or bounded-domain argument is owed. Live smoke: **not applicable** — no
external-API surface exists to smoke (its absence is correct here, not a gap).

**2. What was confirmed by eyeballing live output** (behavior, not counts):
- **`plans/` recursion, real tree probe.** Planted `plans/probe-sub/closed-item.md` (nested, live)
  and `plans/archive/probe-nested/old.md` (nested, archived). `knowledge_lint` flagged the nested
  live plan as closed-but-unpruned — it was previously invisible to the top-level-only glob — and
  did NOT flag the archived one. The `outstanding` gather listed the nested live plan and excluded
  the archived one. Both gathers now agree; the three-way disagreement is gone. Probe removed, tree
  re-verified clean.
- **`scaffold_lint` vocabulary is genuinely non-empty**, derived live as
  `{lint-knowledge, outstanding-work-review, openspec-onboard}`. This was the D1 no-op trap: the
  parser fullmatches `.claude/skills/([^/]+)` against entries written with a trailing `/`, so had
  the reader not stripped it the vocabulary would be silently EMPTY — and task 2.5's "zero findings"
  would still have passed, because an empty vocabulary also yields zero findings. Checked directly
  rather than inferred.
- **The new retired-name test is not vacuous.** Reverted `scaffold_lint.py` to pre-change and re-ran
  it: fails (`0 = len([])`); restored: passes. The blind spot is really closed.
- **`freeze_check` emphasis tolerance did not become a blanket accept** — see field 3.
- Live linters on the real tree: `knowledge_lint` OK, `scaffold_lint` clean, `check.sh` green,
  `openspec validate --type change --strict` valid, `facts.py --check outstanding` regenerates.
- **Boot surface returned to OK** (was WARN before this change).

**Adversarial/boundary fixtures (orchestrator-authored, self-review core).** The diff carries
decision logic in three places (a verdict regex, a manifest parser, a recursive gather), so the
executor's green suite was treated as a single blind source and 27 independent fixtures were
authored at inputs its tests did not reach. All pass. The load-bearing ones:
- `freeze_check` **rejects** a verdict token mid-prose, blockquoted (`> VERDICT: PASS`), as a list
  item (`- VERDICT: PASS`), and in inline code — i.e. tolerance did not degrade the gate.
- `VERDICT: NEEDS REVISION` still **blocks** in all four emphasis spellings (a false READY there
  would be the catastrophic failure).
- last-anchored-wins semantics survive bolding in both directions.
- manifest parser: trailing-slash and no-slash dir entries both contribute; non-skill entries,
  nested paths, comments/blanks contribute nothing; absent manifest → empty set, no crash.

**3. Defects found and how they were fixed:**
- **(self-review, orchestrator)** Task 3.4's deletion of `plans/plans-scope-alignment.md` orphaned
  citations in two other files. Caught by the live-tree `knowledge_lint` gate, not by planning.
  Fixed by adding task 6.9. *Root cause: the cascade sweep was run for the Group 6 deletions but
  never for the Group 3 deletion.*
- **(apply-executor, Sonnet)** Three further orphan-citation cascades found by re-running
  `knowledge_lint` after the Group 6 deletions (`composition-audit-cadence-follow-ons.md`,
  `knowledge/reference/audit-runbook.md`, `pending-downstream-propagation.md`). Reworded to state
  the live fact. The underlying downstream fact was independently operator-verified.
- **(orchestrator, inline)** `knowledge/reference/resync-verification.md` §7 claimed "the manifest
  has no delete mechanism" and named `openspec-onboard` as owed downstream. Both false. Worse than
  a stale tracker entry — a runbook instructing agents to do manual work the mechanism already
  does. Rewritten.
- **(orchestrator, inline)** `lean-boot-context-follow-ons.md:5` pointed at `parked-follow-ons.md`,
  a pre-restructure filename that has not existed since the knowledge migration. Repointed.
- **(verify, orchestrator, inline)** notes.md over-claimed "Three" tracker files filed stale by
  their own change; the evidence supports **two**. Corrected in place.
- No defect required re-delegation to a fix executor. No Sonnet fallback was needed for a fix
  (Sonnet ran apply itself, by operator pre-route).

**4. As-built deltas vs the artifacts:**
- Task 5.1 landed the archive obligation in the **orchestrator's review checklist** of
  `openspec-archive-change/SKILL.md`, while 5.2 landed it in the two executor bodies as a
  **filing-time** obligation. That two-layer split (executor does it; orchestrator verifies it) is
  better than the single instruction the task specified. Both bodies remain byte-identical.
- Task 4.3 was added post-freeze (recorded with rationale in `review-log.md`), and task 7.2 was
  amended to remove all of §1 rather than keep §1(b), since 4.3 resolved it.
- Task 6.9 was added mid-apply for the cascade above.
- `verify-stale.md` was moved out of a volatile `/tmp` path into the change dir after the round-1
  reviewer flagged it.

**5. Forward-looking items for the project docs** (each is recorded NOWHERE else — fold into
`knowledge/questions/INDEX.md` at archive):
- **Un-backticked path references dangle invisibly.** `broken-prose-path-citation` only inspects
  backtick-wrapped tokens, so a bare-prose filename reference can rot undetected — one
  (`parked-follow-ons.md`) survived the entire `ai-docs/`→`knowledge/` restructure unseen and was
  found by hand this session. Widening the check to bare tokens would be noisy (the backtick-only
  scope is a deliberate false-positive guard), so the realistic mitigation is authoring discipline.
  **Park as monitored, low priority.**
- **extrends' `checks.toml` still disables `data-lint`** with a stale "Postgres-only … blocked on an
  upstream scaffold change" comment, though the upstream SQLite backend shipped in `e604990`.
  Operator-verified against the live checkout. Already recorded in the propagation ledger
  (`knowledge/reference/pending-downstream-propagation.md`) — **no new question item needed**;
  noted here so archive does not double-file it.
- **`decisions/INDEX.md` year-split is still needed.** This change cleared the `boot_surface_lint`
  WARN (81438 → 79607 bytes) but the margin is only ~400 bytes and `decisions/INDEX.md` alone is
  ~33KB. The existing parked item (`knowledge-surface-bounding-2-follow-ons.md`) stays live and
  will re-trigger soon. **Do not close it on the strength of this change.**
- **Composition audit is DUE** (46 archived changes ≥ 10; 211 commits ≥ 100). Operator ceremony,
  not a change. Surface to the operator.
- **`commit-gate-bypass` remains parked** (`knowledge/questions/commit-gate-bypass.md`, committed
  `af71194`) — prefix-anchored matcher + Claude-only. Deliberately excluded from this change as a
  cross-agent design decision deserving its own. **Leave parked; do not close.**
- **`knowledge-lint-gitignored-citation-exempt/` is still unarchived** — verified and landed
  (`7f23eda`), needs only an archive-move. Flag to the operator.
- **The verifier's terse verdict block** — the pro pass emitted a well-formed but evidence-free
  block despite genuinely doing the work (443KB transcript: ran `pytest -q`, all three linters, read
  all 5 delta specs). This is the already-parked `verify-adversarial-fixtures-follow-ons.md`
  "verifier verdict-block adherence, monitored" item — **another observation for it, not a new item.**

**Still owned by archive:**
- `knowledge/STATUS.md` — add this change's section (≤3 sections, ≤150 words; drop the oldest).
- `knowledge/decisions/INDEX.md` — registry lines for D1 (tombstone-derived scan vocabulary,
  superseding the old D2 removed-name trade-off), D2 (sweep is apply work), D3 (archive filing
  obligation).
- `knowledge/questions/INDEX.md` — fold in field 5 above.
- Promote the 5 delta specs into `openspec/specs/` (4 MODIFIED + 1 ADDED). **MODIFIED deltas replace
  the whole requirement** — they were diff-verified against their originals at propose; promote
  faithfully.
- Move the change dir to `openspec/changes/archive/2026-07-17-reconcile-parked-backlog/`.
- Delete `knowledge/HANDOFF.md` if present (already removed during apply).
