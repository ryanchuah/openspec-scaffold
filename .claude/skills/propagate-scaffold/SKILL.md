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
`scripts/test-cmd`). **Expect the knowledge-lint live-tree test to fail when the sync brought
a stricter `knowledge_lint.py`** — new checks (`closed-but-unpruned`, `untriaged-finding-stale`,
…) fire against *pre-existing* per-repo knowledge. This is the "manual per-repo sweep" AGENTS.md
warns about, not a sync bug. Reconcile in Step 5.

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
- **Wider drift** — run the downstream `scripts/knowledge_lint.py` directly and skim
  `knowledge/reference/`, `roadmap.md`, and parked questions for now-stale claims about
  scaffold changes; flag, don't silently rewrite.

Re-run the suite until the knowledge-lint gate is green.

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

## Step 7 — Commit (downstream, and upstream if you fixed anything)

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

## Step 8 — Report

Summarize per downstream repo: convergence state, files added/updated, **any deletions and
why they were safe**, the knowledge reconciliation (what was triaged/retained and how nothing
was lost), any upstream fix, and what was committed vs. left for the operator. Repeat Steps 1–7
for each downstream repo — `extrends` and `psc-monitor` drift independently.
