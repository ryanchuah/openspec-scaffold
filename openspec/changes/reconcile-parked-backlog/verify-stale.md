# Adversarial re-verification of STALE-marked tracker items

Method: for every item the 4 prior extracts marked STALE, re-checked against live
code/files (not the prior agent's prose) — file:line reads, git log/show/blame,
grep, and live downstream checkouts (`/home/pang/Projects/extrends`,
`/home/pang/Projects/psc-monitor`) where the claim concerned those repos.

**Headline: no STALE verdict was fully reversed — every claim's underlying code-level
assertion held up under direct inspection. BUT roughly half of them live inside a
multi-item tracker file where 1-2 sub-bullets resolved and the rest did not — for
those, the correct action is TRIM, not DELETE-ENTRY, or the deletion pass will
silently destroy live sibling items and orphan pointers. Also fixed: deleting
`parked-state-bounding.md`/`parked-sync-mechanism.md` will orphan two "see also"
bullets inside `lean-boot-context-follow-ons.md` — flagged below so the delete pass
doesn't leave dangling links.**

---

## The 3 flagged special-attention items

### 1. `data-lint-sqlite-backend.md` — id: `data-lint-sqlite`
- **my_verdict:** CONFIRMED-STALE
- **evidence:** `git log --follow` on the question file shows exactly one commit,
  `8ceb1cc` (2026-07-09), whose own commit message reads *"Knowledge-tree
  reconciliation that accompanies the **already-committed** data_lint SQLite backend
  (e604990)"* — i.e. the commit that filed this "still open" parked file explicitly
  says in its own message that the backend was already shipped 4 days earlier
  (`e604990`, 2026-07-05, "Add SQLite execution backend to data_lint.py"). Confirmed
  the backend is real: `scripts/data_lint.py`'s module docstring (lines 13-32)
  documents dual-backend dispatch by db-url scheme (`postgresql://` via `psql`,
  `sqlite:///` via stdlib `sqlite3` opened `file:...?mode=ro` read-only), and
  `scripts/test_data_lint.py` has 14 dedicated `test_sqlite_*` tests including
  `test_sqlite_write_attempt_infra_failure_and_db_unchanged` (proves the read-only
  guarantee) and a timeout test. The file's own "Open premise questions" (generalize
  vs Postgres-only? read-only enforcement design?) are answered by the shipped code;
  the one un-answered premise question ("which store does extrends target") is a
  downstream applicability question, not a scaffold blocker — the scaffold-side ask
  ("add SQLite support to data_lint.py upstream") is done regardless of the answer.
- **action:** DELETE-ENTRY (file is single-topic; also delete its `INDEX.md` pointer,
  line 36: `- data_lint.py SQLite backend (extrends ask...)`).

### 2. `run-audit-untested.md` — id: `run-audit-untested`
- **my_verdict:** CONFIRMED-STALE
- **evidence:** Scaffold itself still has **no** `knowledge/audit-log.md`, no
  `checks.toml`, no `checks/` (`ls` confirmed) — that part of the file's premise is
  still literally true today, but it was never presented as a gap to fix; the file's
  own text explicitly frames scaffold's absence of an audit layer as the *reason* an
  in-scaffold exercise is impossible, and states the resolution condition itself:
  *"When a downstream repo wires the audit layer, run a first end-to-end exercise
  there and feed any findings back here."* That condition has now been met precisely:
  `/home/pang/Projects/extrends/knowledge/audit-log.md` contains a real registry line
  (`2026-07-03 · audit/2026-07-03 · b9a96c2 · ruff hygiene only ... — no correctness
  bugs; gitleaks+deptry unavailable → no secret/dependency scan`), and
  `git tag --list "audit/*"` in that repo returns `audit/2026-07-03`. Cross-checked
  every step the SKILL.md names (list → floor/report → triage → tag(operator-gated,
  sole mutation) → log-line(sole tracked write)) against this evidence: the
  triage judgment is visible inline in the log line itself, the tag exists, the log
  line exists — a genuine full cycle, not a partial one. This is the only kind of
  evidence the file itself says would resolve it.
- **caveat:** the *composition*-specific variant of the ceremony (`audit/*-composition`
  tag) remains unexercised in both downstream repos — but that residual is already
  tracked as its own live item, `run-audit-closure-via-composition-ceremony`, inside
  `composition-audit-cadence-follow-ons.md` (left untouched, still LIVE). Also
  psc-monitor still has no audit-log.md at all — tracked separately under
  `dtl-first-audit-cycle` in `deterministic-tooling-layer-follow-ons.md` (also LIVE,
  untouched).
- **action:** DELETE-ENTRY (this specific file's claim — "never exercised end-to-end"
  — is answered; the two residuals above already have their own current homes, so
  nothing is lost). Also delete/reword the `INDEX.md` line (line 31, currently
  "monitored, not blocking").

### 3. `repo-lint-fetchall-docstring.md` — id: `rlfd-docstring-update`
- **my_verdict:** CONFIRMED-STALE
- **evidence:** `git blame -L 20,28 scripts/repo_lint.py` shows the current docstring
  text ("Minimal real check (`checks/no_fetchall.py` — note: the scaffold's own
  `checks.py` now ships a universal `data-scale` detector...; this example exists for
  repos on an older scaffold or for extra repo-specific logic)") was committed in
  `e90961a2` at **2026-07-13 22:25:43**, titled "Implement defect-prevention-detectors
  (OW-1+OW-4): test-quality + data-scale checks.py detectors" — i.e. the SAME commit
  that built the `data-scale` detector this ask is about. The parked-question file
  itself was created by the archive-reconcile commit `6d8024c` at **22:35:59** — 10
  minutes *after* the docstring fix, for the same change. This is a clean case of an
  archive-reconciliation step filing a "still to do" tracker entry for something the
  same change had already shipped minutes earlier — read the docstring text directly
  against the ask ("update docstring so it doesn't mislead repos into re-implementing
  the now-universal check") and it matches exactly, wording and all.
- **action:** DELETE-ENTRY (single-topic file; also delete its `INDEX.md` pointer,
  line 51).

---

## All other STALE-marked items

| id | source file | my_verdict | action |
|---|---|---|---|
| kl-audit-log-untested | knowledge-lint-follow-ons.md | CONFIRMED-STALE (for the bullet as literally worded) | TRIM — remove only the "Latent check, untested against real data" bullet; file's other 2 open bullets (`kl-count-recording-check`, `kl-redundant-predicates`) are unrelated and still LIVE, per non-STALE parts of the same extract — do not delete the file |
| sll-lint-planned-extrends-doc (part a: apply marker to extrends' 2 files) | shared-lint-layer-follow-ons.md, §1 | CONFIRMED-STALE | TRIM — remove the "D1 owes: apply marker to extrends' 2 forward-refs" sentence only |
| sll-lint-planned-extrends-doc (part b: document marker convention) | shared-lint-layer-follow-ons.md, §1 | STILL-LIVE (not claimed stale by prior agent either — confirming it stays) | KEEP — no author-facing doc mentions `<!-- lint:planned -->` anywhere (`grep -rn "lint:planned" .claude/skills/ knowledge/reference/` empty); only in-code comments |
| sll-output-gitignore-general-form | shared-lint-layer-follow-ons.md, §2 | CONFIRMED-STALE | TRIM — delete entire §2 ("`output/` ephemeral skip..."); `is_ignored()` (knowledge_lint.py, confirmed present) shipped via commit `7f23eda` (2026-07-16) |
| sll-commit-gate-smoke-doc | shared-lint-layer-follow-ons.md, §6 | CONFIRMED-STALE | TRIM — delete entire §6 ("Commit-test-gate wiring-smoke doc..."); `tests/commit-gate-smoke/README.md` steps 7-8 confirmed present with the exact described content |
| — (net effect on shared-lint-layer-follow-ons.md) | | | After trimming §1(a), §2, §6: file keeps §1(b, marker-doc), §3 (data_lint strict-zip), §4 (E501 ratchet), §5 (scanner CVE-bump) — all still LIVE, confirmed unchanged |
| dtl-first-downstream-run-risk | deterministic-tooling-layer-follow-ons.md | CONFIRMED-STALE | TRIM — remove this item only; file has ~9 other sub-items, most independently confirmed LIVE (e.g. `dtl-data-lint-live-db-pending`, `dtl-structure-refactor-cluster`, `dtl-vulture-whitelist-seeds`) — do not delete the file. Evidence: `/home/pang/Projects/extrends/output/checks/2026-07-04/` has real `gitleaks.json`, `deptry.json`, `ruff.json`, `run-manifest.json`, `findings.json`; `checks.toml` comments confirm "Enabled 2026-07-04" for gitleaks/osv-scanner with real pinned binaries |
| dtl-delete-extrends-handoff | deterministic-tooling-layer-follow-ons.md | CONFIRMED-STALE | TRIM — remove this item only (same file as above); `find /home/pang/Projects/extrends -iname AUDIT-WORKFLOW-HANDOFF.md` returns nothing |
| readme-onboard-stale-reference | correctness-audit-skill-follow-ons.md | CONFIRMED-STALE | TRIM — remove this item only; file's other items (`dossier-census-format-robustness`, `template-parser-round-trip-untested`, `finding-entry-parser-fragility`, `findings-dual-read-loop-merge`, `graduation-log-not-lint-enforced`, `first-real-audit-manual-check`) are independently LIVE/UNCLEAR, not touched. Confirmed: `README.md` line 19 already reads "The 6 workflow skills...", no `onboard` anywhere (`grep -n onboard README.md` empty), `.claude/skills/onboard` absent |
| OW-15-amendment-pointer | correctness-audit-skill-follow-ons.md | CONFIRMED-STALE | TRIM — remove this item only (same file as above); `openspec/changes/archive/2026-07-14-correctness-audit-meta-hardening/` exists, confirming ship |
| OW-16-next-change-pointer | correctness-audit-meta-hardening-follow-ons.md | CONFIRMED-STALE | TRIM — remove this item only; file's other 3 items (`audit-liveness-substring-false-negative`, `post-close-ledger-existence-not-enforced`, `post-close-ledger-cell-count-tolerance`) confirmed still LIVE, unchanged. `.claude/skills/product-audit/SKILL.md` exists, `openspec/changes/archive/2026-07-14-product-audit-skill/` exists |
| split-outstanding-work-skills-downstream-propagation | split-outstanding-work-skills-follow-ons.md | CONFIRMED-STALE | TRIM — remove this item only; file's sibling item `freeze-check-bold-tolerance-gap` is still LIVE (confirmed: `scripts/freeze_check.py`'s `_last_anchored` regexes at lines 45/55 still have no `\*\*`-tolerance) and `unarchived-plan-md-lingering` still LIVE too — keep both. Also **update `INDEX.md` line 61**, which currently advertises "downstream propagation pending" — that clause is now false per `knowledge/reference/pending-downstream-propagation.md`'s "both downstreams current as of 2026-07-16" frontier |
| bash-destructive-denylist-optional | harden-delegation-robustness-follow-ons.md | CONFIRMED-STALE | TRIM — remove this item only; file's other 2 items (`doom-loop-default-ask` LIVE, `question-deny-deferred` in the sibling file) untouched. `.opencode/agents/openspec-verifier.md` confirmed has ~30-entry bash denylist (`"rm *": deny`, `"git commit*": deny`, `"git reset*": deny`, `"git push*": deny`, etc.) |
| no-runnable-test-suite-claim | verify-multimodel-gate-follow-ons.md | CONFIRMED-STALE | TRIM — remove this item only; file's sibling items (`rerun-failed-and-after-risk`, `v6d-edit-denial-not-probed`) confirmed LIVE, untouched. `scripts/test-cmd` confirmed exists, contents = `pytest -q` |
| manifest-no-tombstone | delegated-agent-safety-follow-ons.md | CONFIRMED-STALE | TRIM — remove this item only; file's sibling items (`verifier-literal-spelling-bypass` LIVE, `handoff-md-trust-model-note` informational) untouched. `scripts/scaffold_manifest_removed.txt` confirmed exists (4 tombstoned entries incl. `outstanding-work-review` skill dir), wired via `_delete_removed_entries`/`_read_removed_manifest` in `sync_scaffold.py` |
| slug-relocation-warning | premise-review-gate-follow-ons.md | CONFIRMED-STALE | TRIM — remove this item only |
| premise-review-gate-downstream-propagation | premise-review-gate-follow-ons.md (same file as above) | CONFIRMED-STALE | TRIM — remove this item too (same file); after removing both, file keeps 3 still-LIVE items (`explore-altitude-dissent-calibration-d11`, `cosmetic-explore-skill-wording`, `cosmetic-propose-skill-indentation`) — confirmed unchanged. `.claude/skills/openspec-propose/SKILL.md` confirmed has the near-match slug-scan warning (`"shares at least one hyphen-delimited token"` / `"may be related to this change"`) |
| delegation-wrapper-downstream-propagation | delegation-wrapper-follow-ons.md | CONFIRMED-STALE | TRIM — remove this item only; file's other 3 items (`premise-gate-downgrade-decision`, `medium-propass-downgrade-decision`, `duration-s-best-effort`) confirmed LIVE via ledger counts, untouched |
| park-instr-surface | parked-instruction-surface.md | CONFIRMED-STALE (both bullets) | DELETE-ENTRY — file is single-topic with exactly 2 bullets, both confirmed resolved: no `open-questions.md` anywhere in repo (superseded by `INDEX.md` system by construction); `sync_config_yaml()` in `scripts/sync_scaffold.py` (confirmed present, §D-C span-replace for the `rules:` block) shipped via `single-source-rules`. Also remove `INDEX.md` pointer line 21 |
| park-state-bounding | parked-state-bounding.md | CONFIRMED-STALE | DELETE-ENTRY — single bullet, single-topic file. extrends has archived 3+ more changes since (`audit-correctness-wave4` 2026-07-10, `llm-gold-anchor` 2026-07-12, `gold-anchor-v1-1` 2026-07-16 — all 3 confirmed present as archive dirs); `status_lint.py` run live against extrends today reports OK. **BUT see cascading note below** — `INDEX.md` line 22 and `lean-boot-context-follow-ons.md`'s 2nd bullet both point here and must be updated/removed in the same pass, or they'll dangle |
| park-sync-mechanism | parked-sync-mechanism.md | CONFIRMED-STALE | DELETE-ENTRY — single-topic file (main bullet + one "Update" sub-note, both about the same 350-line magic number). Commit `93e4d58` (2026-06-26) replaced the absolute cap with a relative `t_after_lines > s_after_lines` comparison (confirmed present in `scripts/sync_scaffold.py`); today `extrends/AGENTS.md` is 471 lines, `psc-monitor/AGENTS.md` 499 lines (both far past the old 350/355), and `sync_scaffold.py --check extrends` runs clean. **Same cascading note** — `INDEX.md` line 23 and `lean-boot-context-follow-ons.md`'s 3rd bullet point here |
| lean-boot-context-fu (the "enforcement untested" bullet) | lean-boot-context-follow-ons.md | CONFIRMED-STALE (for that one bullet) | TRIM, not delete — the file has 4 bullets: (1) "enforcement untested against a live archive" — CONFIRMED-STALE, 24+ archives observed since 2026-06-18 including a 2026-07-16 archive whose commit message records "knowledge_lint, status_lint, openspec validate --specs --strict, check.sh all green"; `.claude/agents/archive-executor.md` §3a-3c + `status_lint.py` gate confirmed still mechanizing exactly the 3 rules — remove this bullet. (2) and (3) are "see also" pointers to `parked-state-bounding.md`/`parked-sync-mechanism.md`, which this report recommends deleting above — **these two pointer-bullets must be removed in the same pass, or they become dangling links to deleted files**. (4) is a live pointer to `parked-psc-monitor.md`, which stays open (per extract-misc.md, unrelated to this task) — keep bullet (4), or fold this whole file down to just that one line |
| dedup-scaffold-fu (a: EXIT-sentinel bug) | dedup-scaffold-follow-ons.md | CONFIRMED-STALE | TRIM — remove bullet (a) only. `.claude/skills/openspec-archive-change/SKILL.md` line 165 confirmed has `echo "EXIT=$?" > /tmp/archive-out.exit` |
| dedup-scaffold-fu (b: task-range-splitting guidance buried) | dedup-scaffold-follow-ons.md | CONFIRMED-STALE | TRIM — remove bullet (b) too (same file); `.claude/skills/openspec-apply-change/SKILL.md` lines 129-143 confirmed has bolded "**Bounded wait + EXIT-sentinel (§c-d)**" callout with "**Why split:**" explanation. Bullet (c) — tier-scaled timeout budgets, "a deliberate non-goal" — confirmed still absent/unbuilt, KEEP that one bullet, file is not fully resolved |
| propagate-baseline-fu (downstream commit-test gate "ships dormant") | propagate-baseline-follow-ons.md | CONFIRMED-STALE | TRIM — remove this bullet only; file's 2nd bullet (psc-monitor `## Purpose` spec-validation failures for 3 named specs) independently re-confirmed still LIVE (grepped all 3 specs in the live psc-monitor checkout — none have a `## Purpose` heading) — keep that bullet. Evidence for the stale bullet: both `extrends/scripts/test-cmd` and `psc-monitor/scripts/test-cmd` exist and run `pytest -q` (extrends via `.venv/bin/python -m pytest -q`; psc-monitor with env-var scrubbing), and both repos' `.claude/settings.json` wire `test-gate.sh` into the `PreToolUse` `git commit*` hook |
| plans/outstanding-work-review-residual-sweep.md | (plan file, not a `knowledge/questions/*` tracker, but same "shipped, tracker is stale paper" pattern) | CONFIRMED-OBSOLETE | DELETE — confirmed T1 (skill split), T2 (parent-ID-disposition sentence), T3 (version bumps 1.1 / 1.0) all present verbatim in `.claude/skills/outstanding-work-deep-sweep/SKILL.md` and `outstanding-work-scan/SKILL.md`; T4/T5 (downstream sync + verify) are separately and more-currently tracked in `split-outstanding-work-skills-follow-ons.md` + `pending-downstream-propagation.md` — nothing unique is lost by deleting this plan file |

---

## Non-actionable note (not a real "STALE" claim, flagged for completeness)

`kl-known-absent-residual` in `knowledge-lint-follow-ons.md` was labeled "STALE-as-a-gap"
by the prior extract, but on inspection this isn't the "fix shipped, tracker is outdated"
pattern at all — it documents a **deliberate won't-build decision** (a general
known-absent/allowlist mechanism was explicitly rejected as YAGNI). There's no code to
verify as shipped or not; it's a permanent design note. Recommend leaving it as-is
(it's accurate and non-actionable) rather than treating it as a delete candidate under
this sweep — don't let "STALE" in the prior label cause it to be swept up by a blind
grep-for-STALE deletion pass.

---

## Summary counts

- Items re-verified: 27 STALE-labeled items + 1 OBSOLETE-labeled plan file = 28
- CONFIRMED-STALE (code-level claim genuinely resolved): 27
- STILL-LIVE (prior verdict reversed): 0, but 1 sub-part (`sll-lint-planned-extrends-doc`
  part b) that the prior extract itself already correctly flagged as separately LIVE
  within the same STALE-labeled item is reconfirmed LIVE here — no double-delete
- Non-actionable / mislabeled as STALE: 1 (`kl-known-absent-residual` — design note, not a gap)
- Whole-file DELETE-ENTRY safe: `data-lint-sqlite-backend.md`, `run-audit-untested.md`,
  `repo-lint-fetchall-docstring.md`, `parked-instruction-surface.md`,
  `parked-state-bounding.md`, `parked-sync-mechanism.md`,
  `plans/outstanding-work-review-residual-sweep.md` (7 files)
- Files needing TRIM (partial deletion only — deleting the whole file would destroy
  live work): `knowledge-lint-follow-ons.md`, `shared-lint-layer-follow-ons.md`,
  `deterministic-tooling-layer-follow-ons.md`, `correctness-audit-skill-follow-ons.md`,
  `correctness-audit-meta-hardening-follow-ons.md`,
  `split-outstanding-work-skills-follow-ons.md`,
  `harden-delegation-robustness-follow-ons.md`, `verify-multimodel-gate-follow-ons.md`,
  `delegated-agent-safety-follow-ons.md`, `premise-review-gate-follow-ons.md`,
  `delegation-wrapper-follow-ons.md`, `lean-boot-context-follow-ons.md`,
  `dedup-scaffold-follow-ons.md`, `propagate-baseline-follow-ons.md` (14 files)
- Cascading fix required alongside deletion: `INDEX.md` needs 7+ pointer-line
  edits/removals to match; `lean-boot-context-follow-ons.md` needs its 2nd and 3rd
  bullets removed specifically *because* their targets (`parked-state-bounding.md`,
  `parked-sync-mechanism.md`) are being deleted in this same pass — otherwise they
  become dangling references.
