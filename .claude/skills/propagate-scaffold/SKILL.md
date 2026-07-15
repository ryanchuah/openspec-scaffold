---
name: propagate-scaffold
description: Propagate scaffold-managed files from this openspec-scaffold golden source to a downstream repo (extrends, psc-monitor) via scripts/sync_scaffold.py. Operator-invoked and operator-gated. Syncs the manifest + AGENTS.md shared spans + config rules block, then handles the per-repo knowledge reconciliation and lint drift the sync surfaces — WITHOUT deleting or burying downstream information. Use when the operator asks to propagate/sync scaffold changes downstream.
license: MIT
metadata:
  author: openspec
  version: "1.0"
---

Propagate the scaffold golden source to a downstream repo. **Scaffold-only** —
propagation is always initiated from this repo (`sync_scaffold.py` does not exist
downstream). Operator-invoked and operator-gated; never propagate on your own
initiative, and **never push** without explicit authorization.

> ## ⚠️ Load-bearing discipline: do NOT delete or bury downstream information
> The sync overwrites *scaffold-managed* files (they are golden-source-owned — that is
> correct). But propagation also **surfaces** per-repo drift that you must reconcile by
> hand, and that reconciliation must **preserve every piece of downstream information**:
> - **Never delete** a downstream knowledge file, finding, decision, question, or roadmap
>   entry to make a check pass.
> - **Never bury** information so it stops being discoverable — do not mark open work
>   "closed", do not collapse a distinct record into a false duplicate, do not remove a
>   navigational pointer without confirming the target is reachable another way.
> - When a stricter synced check flags pre-existing downstream content, reconcile it
>   **additively** (record a truthful disposition, add a `<!-- lint:keep -->` marker with a
>   rationale) — not by removal. When in doubt, retain and flag for the operator.
> - The sync's own deletion pass (`scaffold_manifest_removed.txt`) only removes
>   **renamed/retired scaffold files**; audit those too (Step 2) — never let it remove
>   anything carrying unique downstream content.

Reference: `AGENTS.md` § "Scaffold-managed files & propagation" and the
`scaffold-sync-mechanism` capability spec. `<repo>` below = the downstream repo path
(e.g. `../psc-monitor`).

---

## Step 0 — Preflight

1. **Know what state you are propagating.** `sync_scaffold.py` uses *this checkout's*
   working tree as the source (`_scaffold_root()` = the dir above `scripts/`). If you are
   in a **git worktree**, confirm it reflects the scaffold state you intend to ship —
   a worktree branch can lag `main`. Check:
   ```bash
   git rev-parse HEAD; git log --oneline main..HEAD; git log --oneline HEAD..main
   ```
   If `HEAD` is behind `main` on scaffold-managed files, reconcile first (fast-forward /
   merge). Commits that touch only per-repo knowledge (`knowledge/…`) do **not** affect
   scaffold-managed content, so a lag there is harmless — verify before force-updating.
2. **Downstream working tree is clean.** `cd <repo> && git status` — a dirty tree makes it
   impossible to tell sync changes from pre-existing local work. Stop if not clean.

## Step 1 — Survey drift (read-only)

```bash
python3 scripts/sync_scaffold.py --check <repo>        # 0 = converged, 1 = drift
python3 scripts/sync_scaffold.py --check-refs <repo>   # 0 = citations resolve
```
`--check` lists each file as `IDENTICAL` / `DIFFERS` / `MISSING` (new files) / `STALE`
(a removed-manifest target still present). Note every `DIFFERS`/`MISSING`/`STALE`.

## Step 2 — Audit deletions and clobbering BEFORE syncing

- **Deletions.** Read `scripts/scaffold_manifest_removed.txt`. For each entry, confirm it is
  either already absent downstream or a genuinely renamed/retired scaffold file — **never a
  file carrying unique downstream content**. (The sync's deletion pass has four guards, but
  the "no unique info" judgment is yours.)
- **No clobbering.** For each `DIFFERS` scaffold file, confirm the downstream copy holds no
  repo-specific content the sync would drop. Scaffold files are scaffold-owned, so this is
  usually just staleness — but verify (a quick reverse-diff for lines present downstream and
  absent upstream). `AGENTS.md` (span-merge) and `openspec/config.yaml` (rules-block replace)
  **preserve** each repo's title / `## Project context` / `context:` by design.

## Step 3 — Run the sync

```bash
python3 scripts/sync_scaffold.py <repo>
```
Copies manifest files byte-identical, span-merges `AGENTS.md`, replaces the config `rules:`
block, runs the deletion pass, and writes the `.scaffold-version` provenance beacon. Then
re-verify convergence:
```bash
python3 scripts/sync_scaffold.py --check <repo>        # expect exit 0
python3 scripts/sync_scaffold.py --check-refs <repo>   # expect exit 0
```
A `WARNING: … does not wire scripts/scaffold_check.py` means the downstream edit-guard is
unwired — surface it to the operator.

## Step 4 — Run the downstream test suite

Run the downstream repo's full suite (e.g. `cd <repo> && .venv/bin/pytest -q`, or its
`scripts/test-cmd`). **Expect a stricter synced check to fail against *pre-existing* per-repo
content** — this is the "manual per-repo sweep" AGENTS.md warns about, not a sync bug. Two
recurring classes (reconcile in Step 5):
- **`knowledge_lint` live-tree test** — new checks (`closed-but-unpruned`,
  `untriaged-finding-stale`, …) fire against pre-existing per-repo knowledge.
- **`boot_surface_lint` live-tree test** (`test_boot_surface_live_tree_not_fail`) — a
  legitimately larger downstream repo can exceed the scaffold's default 100 KB boot budget and
  hard-FAIL (exit 2), breaking the commit gate. Reconcile via the per-repo budget (Step 5).

Also re-run **`--check-refs` after the sync** (not just `--check`): a synced `AGENTS.md` /
`knowledge/README.md` can newly cite a per-repo file that does not exist downstream yet (e.g.
`knowledge/ratchet-log.md` — a per-repo ledger, NOT scaffold-managed, so the sync never creates
it). That surfaces as a `DANGLING` ref even though `--check` is converged. Seed it in Step 5.

## Step 5 — Reconcile per-repo knowledge (info-preserving — see the disclaimer)

Fix each finding **additively**. Common cases:

- **`untriaged-finding-stale`** — a finding ID (in a `knowledge/research/**/FINDINGS.md`) has
  gone untriaged past the threshold. "Triaged" = the ID **string appears anywhere under
  `knowledge/questions/`** (that is the whole mechanism; `FINDINGS.md` is never edited). Record
  a **truthful disposition** for each ID in the natural questions/ file — `DONE (shipped …)`,
  `deferred/low-priority`, `won't-fix`, or `OPEN — carried forward`. **Do not false-close open
  debt** just to clear the check; recording it as OPEN under questions/ still satisfies the
  check and keeps it honest and discoverable.
- **`closed-but-unpruned`** — a `knowledge/roadmap.md` (or `plans/*.md`) entry carries a closed
  token (`COMPLETE`/`DONE`/`✅`/`~~…~~`). Two info-preserving fixes: (a) **prune** it *only* if
  the full record is durably elsewhere (archive + `STATUS.md`) **and** no navigational pointer
  is lost; or (b) **retain in place** with a `<!-- lint:keep -->` marker plus a `<!-- … -->`
  rationale comment (anywhere between the heading and the next `##`). Prefer (b) when unsure.
- **`--check-refs` DANGLING to an unseeded per-repo ledger** — a synced `AGENTS.md` /
  `knowledge/README.md` references a per-repo file the downstream lacks (the recurring case is
  `knowledge/ratchet-log.md`, added by the finding-closure-ratchet capability). **Seed it**, do
  not delete the reference. The seed is the scaffold ledger's **header/format template ONLY, with
  ZERO entries** — never copy the scaffold's own ratchet entries: their `check:`/`test:` pointers
  cite scaffold files (`scripts/scaffold_lint.py`, …) absent downstream, which `knowledge_lint`
  would then flag as unresolvable. Also repoint the header's "See … spec" line: the
  `finding-closure-ratchet` capability spec is **upstream-only** (scaffold capability specs are not
  propagated), so point to the downstream **AGENTS.md `Finding closure ratchet` rule** instead of
  `openspec/specs/…`. Re-run `--check-refs` + `knowledge_lint` (both clean) after seeding.
- **`boot_surface_lint` FAIL (boot surface over budget)** — the mandatory-boot-read byte budget
  is **per-repo configurable** (added 2026-07-15). Add a top-level `[boot_surface_lint]` table to
  the downstream `checks.toml` (per-repo, NOT scaffold-managed) with `warn_bytes` / `fail_bytes`
  raised to fit a legitimately larger repo — e.g. `warn_bytes = 100000`, `fail_bytes = 120000`.
  This is info-preserving (touches no knowledge). The alternative — condensing the boot files per
  the AGENTS.md Active/Parked split rule — risks burying live gates, so when the overage is large
  **surface the choice to the operator** (raise-budget vs condense) rather than unilaterally
  restructuring live deploy/status knowledge.
- **Wider drift** — run the downstream `scripts/knowledge_lint.py` directly and skim
  `knowledge/reference/`, `roadmap.md`, and parked questions for now-stale claims about
  scaffold changes; flag, don't silently rewrite.

Re-run the suite until the knowledge-lint **and** boot-surface gates are green (a boot-surface
WARN, exit 1, is acceptable — only FAIL, exit 2, blocks).

## Step 6 — Handle lint drift on byte-identical files (fix UPSTREAM)

A scaffold file that is byte-identical downstream can still fail the downstream's
`ruff check .` for **environmental** reasons — most often isort **first-party** classification:
if the downstream has a top-level package whose name matches a scaffold module (e.g. a
`checks/` dir makes `import checks` first-party), ruff demands a different import grouping than
in the scaffold (which has no such package). **Never edit the scaffold-managed file
downstream** (forbidden, and it breaks the byte-identical invariant + trips `scaffold_check.py`).
Fix it **in the scaffold golden source** so the shared file is robust everywhere — e.g. add a
targeted `# noqa: I001` (the shared `ruff.toml` does not select RUF100, so an unused noqa is
harmless upstream) with a comment explaining why it is load-bearing — then **re-sync**
(Step 3). Verify both the scaffold's own suite and the downstream's `ruff check .` go green.

## Step 7 — Prune stale/done entries (operator-prompted, same rigor — see the disclaimer)

Before committing, look for knowledge-tree entries/files (in the downstream repo AND/OR the
scaffold source) that are now **genuinely done** and can be pruned — but hold every candidate to
the **same strict readiness bar as the disclaimer: never delete or bury information.** Prune only
what is *unambiguously* finished, whose full record is durably preserved elsewhere.

Typical candidates and their readiness tests:
- **A completed roadmap entry** (`✅ COMPLETE` / `DONE`) — prunable *only if* the full record is
  durably held elsewhere (archive + `STATUS.md`) **and** every pointer it carries resolves
  independently (verify the targets are reachable without it). Otherwise retain with `lint:keep`
  (Step 5).
- **An executed handoff file** (`knowledge/HANDOFF.md`) — prunable *only once its work is actually
  applied/verified/archived*. If the changes it hands off are still in `openspec/changes/`
  (un-archived) or their `tasks.md` are unchecked, the work is **NOT done — KEEP it.** Verify;
  never infer "done" from the file's presence or age.
- **A resolved follow-on** (`knowledge/questions/*.md` whose INDEX line is resolved and whose work
  shipped) — prunable if its outcome/rationale is recorded elsewhere (`decisions/INDEX.md` + the
  change archive) and it is referenced only from its INDEX line. Delete the file **and** collapse
  that INDEX line to an inline `RESOLVED …` note (no dangling `→` pointer), or `--check-refs` /
  `knowledge_lint` will flag the orphan.

Procedure:
1. Compile the candidate list. For **anything at all ambiguous or non-obvious, do NOT prune — ask
   the operator.**
2. Get an **independent deepseek-flash review of the candidate filenames** ("did I miss anything?
   is each one truly done?") — point it at the live tree so it verifies claims itself (e.g. that a
   handoff's changes are genuinely un-archived). Its verdict is advisory; apply your own judgment.
3. **Prompt the operator: if there is anything prunable, ask whether to prune it — never prune on
   your own initiative.** Present each candidate with its readiness evidence and a recommendation,
   and surface every ambiguous one for a decision.
4. Apply only the approved prunes, then re-run the downstream suite + `--check-refs` to confirm no
   dangling references. Prunes land in the same reviewed commit set as the sync (Step 8).

## Step 8 — Commit (downstream, and upstream if you fixed anything)

- **Downstream sync commit needs `git commit --no-verify`.** `scaffold_check.py` (a downstream
  PreToolUse hook) blocks *any* staged scaffold-managed file — that guard exists to catch
  *accidental* local edits, and its sanctioned escape for a **deliberate sync** is `--no-verify`.
  Because `--no-verify` also skips the downstream test gate (`test-gate.sh`), **run every gate
  manually first** and confirm green: `ruff check .`, `ruff format --check .`, the full suite,
  and `--check` / `--check-refs`. Bundle the sync + its knowledge reconciliation in one commit
  so no intermediate state is red.
- **Upstream fixes** (Step 6, or a reverse-promoted improvement) are committed in the scaffold
  the normal way (its gate is only `test-gate.sh`; `scaffold_check.py` is not wired here). Keep
  scaffold and downstream commits separate and small.
- **Push is operator-gated** — do not push either repo without explicit authorization. If the
  scaffold fix landed on a worktree branch, note that it must be merged to `main` so future
  syncs (run from `main`) stay converged.

## Step 9 — Report

Summarize per downstream repo: convergence state, files added/updated, **any deletions and
why they were safe**, the knowledge reconciliation (what was triaged/retained and how nothing
was lost), any upstream fix, and what was committed vs. left for the operator. Repeat Steps 1–7
for each downstream repo — `extrends` and `psc-monitor` drift independently.
