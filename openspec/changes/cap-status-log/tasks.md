# Tasks — cap-status-log

> Scope: scaffold-only. All edits below are to scaffold files that propagate
> downstream via `scripts/sync_scaffold.py`. The one-time cleanup of extrends'
> already-bloated STATUS.md / open-questions.md is a SEPARATE effort in that
> repo and is NOT part of this change.

## 1. AGENTS.md — MANDATORY read block (span1, synced)

> Files affected: `AGENTS.md`

- [x] 1.1 In the `> **MANDATORY**` block, replace the single "read ... in full"
  directive with file-specific guidance: read **`STATUS.md`** and
  **`ai-docs/open-questions.md`** in full (both stay bounded); for
  **`ai-docs/decisions.md`** read the `## ` section headers (it is append-only
  and grows in a long-lived repo) and then read in full only the entries
  relevant to the current task. Keep the resume-time change-dir guidance and the
  "starting source of truth / override training data" framing unchanged.
- [x] 1.2 In the same block, amend the freshness sanity-check (the
  `git log --oneline -5` / "if it lags, reconcile it" sentence): add that
  **process/scaffold-maintenance commits that do not change project state**
  (e.g. tooling, scaffold-rule, or doc-formatting commits) do NOT obligate a
  `STATUS.md` "Latest change" entry — the lag-check targets feature/change-shipping
  commits, so their absence from `STATUS.md` is not a lag to reconcile.

## 2. AGENTS.md — write-discipline section (span2, synced)

> Files affected: `AGENTS.md`

- [x] 2.1 In `## State, write discipline, and the archive-as-handoff rule`, under
  the "Project-tracked docs" bullet, add the STATUS.md **cap rule**: `STATUS.md`
  holds only the current-state preamble, `## Immediate next action`, and at most
  the **3** most recent `## Latest change` / `## Prior change` paragraphs; at archive the
  reconciliation moves any older `## Prior change` paragraphs verbatim into
  `ai-docs/archive/status-log.md` (append-only, newest-first). State the rationale
  in one clause (bounds the read-in-full onboarding cost; the archive log keeps the
  full history). Note that `open-questions.md` already prunes resolved items to
  `ai-docs/archive/retired-notes.md` and `decisions.md` is intentionally append-only.

## 3. archive-executor body — cap mechanic (.claude + .opencode, BYTE-ALIGNED)

- [x] 3.1 In `.claude/agents/archive-executor.md` step `#### 3a. Reconcile STATUS.md`,
  after the "Demote the previous `## Latest change`" bullet, add a new bullet: after
  adding the new `## Latest change` and demoting the prior one, **prune** — if more
  than **3** `## Latest change`/`## Prior change` paragraphs now exist, move the
  oldest ones (verbatim, headers included) into `ai-docs/archive/status-log.md`
  (create it if absent; prepend so newest-first), leaving the 3 most recent in
  `STATUS.md`. Do not edit the moved content; do not touch the preamble or
  `## Immediate next action`.
- [x] 3.2 Apply the **identical** edit (same wording, same position) to
  `.opencode/agents/archive-executor.md` step 3a. (Step 3a is already byte-identical
  between the two files; the only sanctioned divergence is the intro clause, which is
  outside 3a — do not touch it.)
- [x] 3.3 Run `python3 scripts/test_executor_body_agreement.py` — both archive-executor
  bodies must remain byte-identical (modulo the sanctioned intro clause). Must pass.

## 4. archive skill — verify checklist (synced)

- [x] 4.1 In `.claude/skills/openspec-archive-change/SKILL.md`, in the
  `**Quality check — verify each doc contains real, artifact-backed content:**` block,
  after its `open-questions.md` sub-bullet, add one assertion: `STATUS.md` retains at most
  3 change paragraphs and any overflow was moved to `ai-docs/archive/status-log.md`.

## 5. Validation

- [x] 5.1 Run `python3 scripts/test_sync_scaffold.py` — confirms the `sync_agents_md`
  span-replace algorithm and its tail/anchor invariants still hold (the test runs against
  fixture strings, not the live AGENTS.md, so it validates the algorithm — NOT that this
  change's real edits preserved the anchors; that is task 5.3's job). Must pass.
- [x] 5.2 Run `openspec validate --all` (or `--strict`) — must pass with no new failures.
- [x] 5.3 **Authoritative anchor-preservation gate.** Confirm the AGENTS.md edits left the
  four regex-anchored span headings byte-unchanged — `> **MANDATORY`, `## Project context`,
  `## Roles`, `## After reading this file`. (These four are the ONLY headings
  `sync_scaffold.py` regex-matches; other headings inside the synced spans may be edited
  freely.) Also confirm no test/doc/row counts were introduced in any edited tracked doc.
