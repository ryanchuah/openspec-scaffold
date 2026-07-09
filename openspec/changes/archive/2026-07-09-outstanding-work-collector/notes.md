# Notes — outstanding-work-collector

## Verify checkpoint (2026-07-09)

### 1. Verdict
**READY for archive.** Zero CRITICAL. All 23 apply tasks complete; full suite green (ruff +
`ruff format --check` + pytest, including the `scaffold_lint` SEAL and the live-tree
`knowledge_lint` gate). Both independent multi-model verifier passes returned `VERDICT: READY`
with no defects, then were **re-run READY after a fix**. Of the two WARNINGs surfaced by the
orchestrator self-review: (1) absolute-path provenance was **FIXED during verify** (operator-requested;
re-delegated; fields 3–4); (2) the `plans/` recursive-vs-top-level scope is a **pending operator
decision** (field 5), non-blocking either way.

### 2. What was confirmed by eyeballing live output (behavior, not counts)
- `facts.py --check outstanding` runs on this repo, exits 0, and writes both
  `output/facts/outstanding.md` and `.json`. The snapshot enumerated every prose source —
  `knowledge/questions/INDEX.md` (Active + Parked, bullet form), the open `knowledge/roadmap.md`
  entries, every per-item `knowledge/questions/*.md` file (point-only, tracked/untracked tagged),
  and the live `plans/` tree — each item carrying `source:line` provenance. The untriaged bucket
  rendered empty, correct-by-design (this repo has no `FINDINGS*` files).
- On a synthetic fixture tree I independently confirmed the behavioral contracts:
  - **D2 (never-fails):** an invalid-UTF-8 / malformed source degrades to an `UNPARSEABLE — read
    manually` entry and the run still exits 0 — it does not crash.
  - **D3 (format-plural):** Active items were extracted from **both** a bullet-form and a table-row
    `INDEX.md`.
  - **D4 (untriaged↔triaged):** a finding ID absent from `knowledge/questions/` surfaced in the
    untriaged bucket, then moved to triaged once a `questions/` file referenced it; a per-repo
    `finding_id_pattern` override was honored.
  - **D6 (plans):** a top-level `plans/*.md` was listed; `plans/archive/**` was excluded.
  - **D7 (knowledge_lint):** a planted ≥8-line duplicate across two in-scope files flagged as exactly
    one finding per file (overlapping sliding windows correctly merged — no per-offset spam); the same
    block under `knowledge/research/` was not flagged; `<!-- lint:dup-ok -->` inside the window and
    `<!-- lint:keep -->` on a closed roadmap entry both suppressed correctly; a `DONE`/`COMPLETE`
    roadmap/plan entry flagged as closed-but-unpruned.
  - **D8 (untriaged-age):** the shared `outstanding.extract_untriaged` import drives the age check;
    age derives from git last-commit date and falls back to filesystem `mtime` when git is absent.
- Live-tree `knowledge_lint` is clean on this repo (0 duplicate-block, 0 closed-but-unpruned,
  0 untriaged-stale) — the self-tree reconcile holds.

### 3. Defects found and how fixed (attributed to the surfacing pass)
- **Absolute-path provenance — surfaced by orchestrator self-review, FIXED (operator-requested).**
  The pro/flash verifier passes found no behavioral defect. The orchestrator self-review flagged the
  provenance inconsistency (absolute open-work paths vs. relative untriaged paths); on operator request
  it was fixed by a **re-delegated fresh `deepseek/deepseek-v4-flash` apply-executor** (not hand-fixed):
  a `_rel(root, path)` helper now makes every open-work `source` repo-relative, and a new test
  (`test_open_work_source_is_repo_relative_not_absolute`) locks it. Re-verified: suite green, live
  output now shows repo-relative `source:line` provenance consistent across both buckets, and the
  pro + flash verifier passes were re-run on the fixed tree.
- Context for the archive-executor: the apply phase itself (per the prior handoff) fixed two
  pre-existing bugs in `outstanding.py` before verify — an uncaught `UnicodeDecodeError` (would have
  broken the D2 never-fails contract) and a table-header lookahead off-by-one — and two
  duplicate-block bugs (research/specs dir not actually excluded; overlapping-window false-positive
  spam). All four are covered by tests and independently re-confirmed green at verify.
- Context for the archive-executor: the apply phase itself (per the prior handoff) fixed two
  pre-existing bugs in `outstanding.py` before verify — an uncaught `UnicodeDecodeError` (would have
  broken the D2 never-fails contract) and a table-header lookahead off-by-one — and two
  duplicate-block bugs (research/specs dir not actually excluded; overlapping-window false-positive
  spam). All four are covered by tests and independently re-confirmed green at verify.

### 4. As-built deltas discovered during verify (not already in proposal/design/specs)
- **Open-work provenance was emitted as absolute paths — NOW FIXED (repo-relative).** Resolved during
  verify via the re-delegated fix in field 3 (`_rel` helper; new test). Recorded here as the as-built
  history: the original apply emitted `str(path)` (absolute) for open-work `source` while
  `extract_untriaged` used relative — now unified to repo-relative across both buckets.
- **`plans/` gather is recursive, not top-level.** *(STILL OPEN — operator decision pending, see field 5.)* `_enumerate_prose_files` uses
  `plans_dir.rglob("*.md")` (excluding `plans/archive/`), while `tasks.md` §1.3 and design D6 say
  "top-level `plans/*.md`". The gather therefore also surfaces nested live plans
  (`plans/day-to-day-tooling/`, `plans/succession-hardening/`, `plans/sync-deletion-manifest/`) —
  arguably *more* complete, but a divergence from the written scope, and it disagrees with the
  `_check_closed_unpruned` plan scan which is top-level `glob` only. Net effect: a nested plan marked
  DONE would be listed as live work by the gather but not flagged as closed-unpruned by the lint. The
  `plans/archive` test only plants top-level + archive files, so it passes under either `glob` or
  `rglob` and did not catch the divergence.

### 5. Forward-looking items for the project docs (fold into knowledge/questions/INDEX.md at archive)
- **[RESOLVED] Absolute vs. relative provenance** — fixed during verify (fields 3–4); no follow-on needed.
- **[DECIDED — keep recursive; follow-on to align spec+lint] `plans/` gather scope.** Operator decision
  (2026-07-09): **keep the recursive `rglob` gather** (Option A) — the repo genuinely nests live plans in
  subdirs, so recursive is what keeps the snapshot honest. This leaves a follow-on: the *written spec*
  (design D6 / tasks §1.3 say "top-level `plans/*.md`") and the `_check_closed_unpruned` plan scan
  (top-level `glob` only) must be updated to MATCH the recursive gather, so all three agree on what "a
  plan" is. Captured as a standalone handoff for the next agent (see `plans/plans-scope-alignment.md`)
  and to be pointed-to from `knowledge/questions/INDEX.md` at archive. Non-blocking for this archive.
- **[usability, monitor] `<!-- lint:dup-ok -->` placement is non-obvious.** To suppress a legitimate
  duplicate, the marker must fall *inside the still-matching window* — in practice at an identical
  position inside the block in *all* copies (otherwise it either sits outside the reported range or
  fragments the block below the 8-line floor for the wrong reason). Documented + tested, flag-only.
  Worth a one-line usage note in the `knowledge_lint`/skill docs if a real dup-keep case ever arises.
- **[low, monitor] Config-load robustness asymmetry.** `outstanding.py:main` guards `tomllib.load`
  against a malformed `checks.toml` (graceful defaults); `knowledge_lint._load_knowledge_lint_config`
  and `_check_untriaged_age` call `tomllib.load` without a guard, so a malformed `checks.toml` would
  raise in the linter rather than degrade. Only triggers on an already-broken config; align if the
  linter's other config reads are hardened later.
- **[cosmetic] Delegate arm reports `count: 0`.** The `_run_delegate` `outstanding` arm returns a
  hardcoded `count: 0`; facts never gate and the real counts live in the `.md`/`.json`, but the engine
  report line is inaccurate. Consider returning open-work/untriaged count for an honest report line.
- **[in-code TODO source is a deliberate no-op]** `_enumerate_todo_code` returns `[]` by design
  (design Non-Goal: in-code TODO scanning is optional/lowest-priority). Recorded so a future reader does
  not mistake the empty function for an unfinished one; revisit only if TODO markers become material in
  these repos.
- **Downstream propagation is out of scope here (operator-gated):** `sync_scaffold.py` to `extrends` +
  `psc-monitor` for the new managed files, and each downstream repo's per-repo `[facts.outstanding]`
  config (`findings_globs` / `finding_id_pattern`) + optional `plans/archive/` move. Per the design
  Migration Plan step 2.

### Still owned by archive
- **Reconcile `knowledge/STATUS.md`** — add the outstanding-work-collector section (respect the ≤3-section
  cap; behavior only, no counts).
- **Reconcile `knowledge/decisions/INDEX.md`** — registry line for this change's key decisions
  (D1 delegate-fact dispatch; D6 `plans/archive` convention; D7/D8 linter checks) → the archive dir.
- **Reconcile `knowledge/questions/INDEX.md`** — fold in the field-5 follow-ons above (provenance fix,
  plans-scope decision, dup-ok usability note, config-load robustness, delegate count).
- **Promote delta specs** from `openspec/changes/outstanding-work-collector/specs/` into
  `openspec/specs/` (`outstanding-work-view` new capability + `knowledge-lint` modified capability).
- **Cleanup / disentangle at commit:** the working tree commingles this change with **leftover
  uncommitted knowledge-tree edits from the prior data_lint-SQLite work** — `knowledge/STATUS.md`,
  `knowledge/questions/INDEX.md` (the two new Parked pointers) and the untracked
  `knowledge/questions/data-lint-sqlite-backend.md`, `knowledge/questions/scanner-provisioning-gaps.md`,
  `knowledge/reference/audit-runbook.md`. These are NOT part of outstanding-work-collector; keep them in
  a separate commit (or confirm they were already meant to land with the prior data_lint work).
