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

- **`boot_surface_lint` is WARN right now** — 81438 bytes vs 80000 threshold;
  `decisions/INDEX.md` alone is 33023. This sweep shrinks `questions/INDEX.md` but will
  **not** clear the WARN. The year-split is a MEDIUM standalone with its own design.
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
