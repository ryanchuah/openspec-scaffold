# Tasks — reconcile-parked-backlog

> **Evidence file (authoritative for Groups 6-7):** `verify-stale.md`, in this change dir.
> Read it before starting Group 6 — it carries the per-file survivor lists, and the task
> descriptions below are summaries of it, not a substitute. If it is missing, STOP and ask;
> do not reconstruct the survivor lists by guessing.
>
> **Hard rule for Groups 6-7:** files marked TRIM keep live sibling items — remove ONLY the
> named sub-bullets, never the whole file. Deleting a TRIM file wholesale destroys real
> outstanding work and is the single worst failure mode of this change. Only the 7 files
> named in Group 6 may be deleted outright; every file in Group 7 must survive.
>
> **Do NOT commit.** The orchestrator reviews and commits.

## 1. freeze_check bold-emphasis tolerance

- [x] 1.1 In `scripts/freeze_check.py`, make the `VERDICT:` anchor (line ~45) and the
      `PREMISE:` anchor (line ~55) tolerate optional `**` markdown emphasis around the
      token and/or the whole line. All four spellings must parse identically:
      `VERDICT: PASS`, `**VERDICT:** PASS`, `**VERDICT: PASS**`, `VERDICT: **PASS**`.
      Keep the anchors otherwise strict — leading/trailing whitespace only; do NOT relax
      to an unanchored search. Suggested shape (adapt as needed, but stay anchored):
      `r"^\s*\*{0,2}VERDICT:\*{0,2}\s*\*{0,2}(PASS|NEEDS REVISION)\*{0,2}\s*$"`.
      The `^...$` anchors are load-bearing: an unanchored search would match a verdict
      token quoted mid-prose and defeat the gate.
- [x] 1.2 Add unit tests to `scripts/test_freeze_check.py` covering, for BOTH `VERDICT:` and
      `PREMISE:`: (a) each of the 4 spellings in 1.1 parses to the same verdict;
      (b) `NEEDS REVISION` / `DISSENT` still parse when bolded;
      (c) **negative control** — text with no verdict line still returns
      `BLOCKED — missing-verdict`, and a verdict token appearing mid-prose (not on its
      own line) is still NOT accepted. A fix that accepts everything is not a fix.

## 2. scaffold_lint removed-name blind spot

Design rationale is in `notes.md` D1 — read it first. Adding the 4 missing current skill
names is a NO-OP (they resolve from disk); the vocabulary must instead carry *retired*
names.

- [x] 2.1 In `scripts/scaffold_lint.py`, add a helper that parses
      `scripts/scaffold_manifest_removed.txt` and returns the set of retired **skill
      names** — the directory entries under `.claude/skills/<name>/`. Ignore comments,
      blanks, and non-skill entries (e.g. `scripts/audit_bundle.py`). Missing or
      unreadable manifest → return empty set (do not crash; the linter is manifest-optional
      the same way it is git-optional).
- [x] 2.2 Replace the hand-maintained `_NON_OPENSPEC_SKILL_TOKENS` frozenset (lines
      ~187-189) with the derived vocabulary from 2.1. NOTE: it is currently a module-level
      constant but the derivation needs `root`, so it must become a function call inside
      `check_dangling_skill_refs` (line ~411) — which already receives `root`. Keep the
      comment explaining WHY non-openspec names need an explicit vocabulary while
      `openspec-*` names are matched by `_TOKEN_RE` — reword it to record that the
      vocabulary is now tombstone-derived so it cannot drift. Update the
      `dangling-skill-refs` docstring (lines ~84-95) to match.
- [x] 2.3 **Update the existing regression test**
      `test_dangling_skill_refs_non_openspec_skill_without_dir_flagged`
      (`scripts/test_scaffold_lint.py:462`). It currently removes `run-audit`'s dir and
      relies on the name still being in the hardcoded frozenset. Under the derived
      vocabulary it must also add `.claude/skills/run-audit/` to the fixture's
      `scripts/scaffold_manifest_removed.txt` — which is MORE faithful, since removing a
      scaffold-managed skill already requires a tombstone. Check whether the `_clean_tree()`
      fixture writes a `scaffold_manifest_removed.txt` at all; add one if absent.
- [x] 2.4 Add new unit tests: (a) a doc in the scanned surface referencing
      `outstanding-work-review` (retired, tombstoned) IS flagged — this is the blind spot
      being closed, and the test MUST fail against the pre-change code (verify that by
      running it before your 2.2 edit, or by reasoning it through and saying so);
      (b) a doc referencing a CURRENT non-openspec skill (e.g. `run-audit`) is NOT flagged;
      (c) a tombstoned non-skill entry (`scripts/audit_bundle.py`) contributes no token;
      (d) absent/unreadable manifest → no crash, no findings.
- [x] 2.5 Run `python3 scripts/scaffold_lint.py` on the live tree — MUST report zero
      findings. If it flags anything, STOP and report; the blast radius was verified clean
      (`AGENTS.md`, `.claude/skills/`, `.claude/agents/`, `.opencode/agents/` have no
      references to either retired name) and any finding means an assumption broke.
- [x] 2.6 Delete `knowledge/questions/scaffold-lint-removed-name-blindspot.md` + its
      `INDEX.md` pointer (line ~32). Task 2 resolves it: the file documents the D2
      trade-off where removed names are dropped from the hand-maintained set, and the
      tombstone-derived vocabulary closes exactly that, making its "revisit if" triggers
      moot. Applying this change's own D3 lesson to itself — do not fix a problem and leave
      its tracker saying it is unfixed. (The rationale is recorded as a decision at archive,
      per the `decisions-entry-format` rule; it is not lost by deleting the question file.)

## 3. plans/ scope alignment

- [x] 3.1 In `scripts/knowledge_lint.py` (~line 1121), change the `plans/` gather from
      `plans_dir.glob("*.md")` to `plans_dir.rglob("*.md")`, and add the same
      `plans/archive/` exclusion `scripts/outstanding.py` already has (see
      `outstanding.py` ~line 522: `rglob` + `if str(rel).startswith("plans/archive/"):
      continue`). **Keep** knowledge_lint's existing `README.md` skip — that is a
      legitimate per-check difference (README is not a plan), not drift to remove.
      Net effect: both gathers agree on recursion and on `plans/archive/`.
- [x] 3.2 Update the `outstanding-work-view` spec (~lines 88-91) which says "top-level
      `plans/*.md`" — reword to recursive-excluding-`archive/` so spec, gather, and lint
      all agree.
- [x] 3.3 Add a test fixture with a nested `plans/sub/item.md` asserting `knowledge_lint`
      now sees it (previously invisible), plus one asserting `plans/archive/old.md` is
      still NOT gathered.
- [x] 3.4 This task IS the work specified by `plans/plans-scope-alignment.md`. Once 3.1-3.3
      land, delete that plan file (executed) and remove its `knowledge/questions/INDEX.md`
      pointer (line ~41, "plans/ gather scope: keep recursive, align spec+lint").

## 4. Skill frontmatter accuracy

- [x] 4.1 Remove the false `compatibility: Requires openspec CLI.` frontmatter
      line (line 5 in each) on the 7 skills that do not touch the openspec CLI:
      `run-audit`, `knowledge-drift-review`, `composition-audit`, `correctness-audit`,
      `outstanding-work-scan`, `outstanding-work-deep-sweep`, `product-audit`.
      Verify the claim per skill before editing (grep its SKILL.md for `openspec `
      invocations); if any genuinely does shell out to the openspec CLI, leave it and
      report which.
      Do NOT touch the `openspec-*` lifecycle skills — the line is accurate there.
- [x] 4.2 Delete `knowledge/questions/audit-skill-metadata-cleanup.md` + its `INDEX.md`
      pointer (line ~33). Task 4.1 resolves it — the file asks for exactly this fix, and
      flags that the inaccuracy likely spans more than the two skills it names; 4.1 sweeps
      all 7. Applying this change's own D3 lesson to itself. If 4.1 found any skill whose
      `compatibility` line was actually accurate and left it, say so and KEEP the file
      instead, trimmed to that residue.
- [x] 4.3 Document the `<!-- lint:planned -->` marker for authors in `knowledge/README.md`
      (the knowledge-tree taxonomy doc — the natural home). One or two lines: a knowledge doc
      that deliberately cites a not-yet-created path SHALL put `<!-- lint:planned -->` on that
      line to suppress the broken-citation finding; suppression is line-scoped. The marker is
      already implemented (`scripts/knowledge_lint.py` ~line 436) and specified
      (`knowledge-lint` spec, "An inline lint:planned marker suppresses forward-reference
      citations") but is mentioned in NO author-facing doc. Closes the
      `sll-lint-planned-author-doc` item — see the amended task 7.2.

## 5. Archive filing step — the root cause

- [x] 5.1 In `.claude/skills/openspec-archive-change/SKILL.md`, add a short obligation to
      the reconciliation step: before filing a follow-on item into
      `knowledge/questions/`, verify the item was not already resolved *by this very
      change* (check the change's own diff/commits) — file it only if still open.
      Cite the concrete failure: three tracker files were filed stale by their own
      change's archive commit (`repo-lint-fetchall-docstring.md` 10 minutes after its own
      fix landed; `data-lint-sqlite-backend.md` by a commit whose message states the
      backend was already committed). Keep it to a few lines — this is a targeted
      obligation, not a new section.
- [x] 5.2 Mirror the same obligation into `.claude/agents/archive-executor.md` and
      `.opencode/agents/archive-executor.md`. These two bodies are byte-compared by
      `scripts/test_executor_body_agreement.py` — the edit MUST keep them byte-identical
      or that guard fails.
- [x] 5.3 Run `python3 -m pytest scripts/test_executor_body_agreement.py -q` immediately
      after 5.2 — catching body drift here is far cheaper than discovering it at 8.2.

## 6. Tracker truth — whole-file deletions

Per `verify-stale.md`, these 7 are single-topic and fully resolved. Delete the file AND
its `knowledge/questions/INDEX.md` pointer line.

- [x] 6.1 Delete `knowledge/questions/data-lint-sqlite-backend.md` + INDEX pointer.
- [x] 6.2 Delete `knowledge/questions/repo-lint-fetchall-docstring.md` + INDEX pointer.
- [x] 6.3 Delete `knowledge/questions/run-audit-untested.md` + INDEX pointer. (Its two
      narrower residuals already live in `composition-audit-cadence-follow-ons.md` and
      `deterministic-tooling-layer-follow-ons.md` — leave those untouched.)
- [x] 6.4 Delete `knowledge/questions/parked-instruction-surface.md` + INDEX pointer.
- [x] 6.5 Delete `knowledge/questions/parked-state-bounding.md` + INDEX pointer.
- [x] 6.6 Delete `knowledge/questions/parked-sync-mechanism.md` + INDEX pointer.
- [x] 6.7 Delete `plans/outstanding-work-review-residual-sweep.md` (obsolete; T1-T3 shipped
      verbatim into `outstanding-work-deep-sweep`, T4/T5 tracked elsewhere). It has no
      `INDEX.md` pointer of its own. (`plans/plans-scope-alignment.md` is handled by 3.4 —
      do not confuse the two plan files.)
- [x] 6.8 **Cascade:** in `knowledge/questions/lean-boot-context-follow-ons.md`, remove the
      two "see also" pointer bullets targeting `parked-state-bounding.md` and
      `parked-sync-mechanism.md` (deleted in 6.5/6.6) — otherwise they dangle. Also remove
      its "enforcement untested against a live archive" bullet (stale: 24+ archives
      observed since). KEEP its `parked-psc-monitor.md` pointer bullet — that stays open.

- [x] 6.9 **Cascade from task 3.4** (added mid-apply; the live-tree lint gate caught this —
      task 3.4 deleted `plans/plans-scope-alignment.md` but two OTHER files cite it, beyond the
      INDEX pointer 3.4 already handled). Both cite work task 3 just RESOLVED, so close them
      per this change's own D3 lesson:
      - `knowledge/questions/outstanding-work-collector-follow-ons.md` (~lines 10-14): the item
        ending "This leaves a follow-on: update the spec and the closed-unpruned scan to match.
        Handoff details at `plans/plans-scope-alignment.md`." — tasks 3.1-3.3 did exactly that
        (recursive gather + spec reworded + `_check_closed_unpruned` aligned). Remove the whole
        item including its heading. KEEP the file's other items (e.g. the `lint:dup-ok`
        placement item) — they are unrelated and live.
      - `knowledge/questions/knowledge-surface-bounding-2-follow-ons.md` (~lines 24-25): the
        trailing parenthetical "(OW-13(d) plans/-count lint is tracked separately in
        `plans/plans-scope-alignment.md` / `knowledge/questions/INDEX.md` Parked — not
        duplicated here.)" — its referent is gone. Remove the parenthetical. KEEP items 1-3 of
        that file, including the `boot_surface_lint` WARN item — still live.
      Then confirm no citation to the deleted plan remains anywhere:
      `grep -rn "plans-scope-alignment" knowledge/ openspec/specs/` must return nothing outside
      this change dir and `openspec/changes/archive/`.

## 7. Tracker truth — trims (live siblings must survive)

All paths below are relative to `knowledge/questions/`. Remove ONLY the named sub-bullets.
Every one of these files keeps live work — none may be deleted wholesale.

- [x] 7.1 `knowledge-lint-follow-ons.md` — remove only the "Latent check, untested against
      real data" bullet. KEEP `kl-count-recording-check`, `kl-redundant-predicates`, and
      the `kl-known-absent-residual` design note (a deliberate won't-build decision, NOT a
      stale gap — do not sweep it).
- [x] 7.2 `shared-lint-layer-follow-ons.md` — remove **all of §1** (its "apply marker to
      extrends' 2 forward-refs" part is stale; its marker-convention-doc part is resolved by
      task 4.3 of this change — D3 applied to itself again), all of §2 (`output/` ephemeral
      skip — shipped in `7f23eda`), and all of §6 (commit-gate smoke doc — shipped).
      KEEP §3, §4, §5. NOTE: this supersedes `verify-stale.md`, which says to keep §1(b) —
      it was written before task 4.3 was added to this change.
- [x] 7.3 `deterministic-tooling-layer-follow-ons.md` — remove only
      `dtl-first-downstream-run-risk` and `dtl-delete-extrends-handoff`. ~9 sibling items
      stay.
- [x] 7.4 `correctness-audit-skill-follow-ons.md` — remove only
      `readme-onboard-stale-reference` and `OW-15-amendment-pointer`. 6 siblings stay.
- [x] 7.5 `correctness-audit-meta-hardening-follow-ons.md` — remove only
      `OW-16-next-change-pointer`. 3 siblings stay.
- [x] 7.6 `split-outstanding-work-skills-follow-ons.md` — remove the downstream-propagation
      bullet (both downstreams converged 2026-07-16) AND the freeze_check bold-tolerance
      bullet (resolved by task 1 of this change — applying this change's own D3 lesson to
      itself). KEEP the `unarchived-plan-md-lingering` bullet — still live. Also fix
      `INDEX.md` line 61, which still advertises "downstream propagation pending" — now false.
- [x] 7.7 `harden-delegation-robustness-follow-ons.md` — remove only
      `bash-destructive-denylist-optional`. Siblings stay.
- [x] 7.8 `verify-multimodel-gate-follow-ons.md` — remove only the "scaffold has no
      runnable test suite" claim (`scripts/test-cmd` exists). Siblings stay.
- [x] 7.9 `delegated-agent-safety-follow-ons.md` — remove only `manifest-no-tombstone`
      (`scaffold_manifest_removed.txt` exists and is wired). Siblings stay.
- [x] 7.10 `premise-review-gate-follow-ons.md` — remove `slug-relocation-warning` and
      `premise-review-gate-downstream-propagation`. 3 siblings stay.
- [x] 7.11 `delegation-wrapper-follow-ons.md` — remove only the downstream-propagation
      bullet. 3 siblings stay.
- [x] 7.12 `dedup-scaffold-follow-ons.md` — remove bullets (a) EXIT-sentinel and (b)
      task-range guidance. KEEP bullet (c) tier-scaled timeout budgets — still unbuilt.
- [x] 7.13 `propagate-baseline-follow-ons.md` — remove only the "commit-test gate ships
      dormant" bullet. KEEP the psc-monitor `## Purpose` bullet — re-confirmed live.
- [x] 7.14 Close the 2 RESOLVED-in-place `INDEX.md` entries (the `clarify-audit-tooling`
      line and the `handoff-file lint downstream cleanup` line). "Close" here means **delete
      the line entirely** — both already state their rationale is recorded in
      `knowledge/decisions/INDEX.md`, so nothing is lost, and the AGENTS.md
      one-canonical-file rule says to close explicitly rather than leave a stale entry.

## 8. Final gates

- [x] 8.1 `python3 scripts/knowledge_lint.py` — clean. Specifically: zero dangling
      citations to any file deleted in Group 6, and every `INDEX.md` pointer resolves.
- [x] 8.2 `scripts/check.sh` — green (ruff check + format + full pytest incl.
      `scaffold_lint` SEAL, `test_executor_body_agreement`, live-tree `test_doc_lint_gate`).
- [x] 8.3 `openspec validate --strict` — exits 0.
- [x] 8.4 `python3 scripts/facts.py --check outstanding` — regenerates without error.
- [x] 8.5 Re-read every file touched in Group 7 and confirm each retains its live sibling
      items per `verify-stale.md`. Report any file where you were unsure what to keep
      rather than guessing.
