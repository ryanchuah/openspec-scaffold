# Notes — delegated-agent-safety

**Tier:** MEDIUM (tasks.md-only per AGENTS.md; acceptance criteria live here). This change also
carries **delta specs** for the three sub-scopes that alter a capability *contract* (a/b/c) — the
security-relevant requirement (a) especially is authored at propose so the pro reviewer audits the
*normative requirement*, not just the implementation.

**Direction:** change 4 of 4 in the succession-hardening portfolio (operator resequenced ahead of
`prune-knowledge` on risk priority, 2026-07-03). Portfolio brief at
`plans/succession-hardening/explore-brief.md`; direction gate `PREMISE: AGREE` at
`plans/succession-hardening/premise-review.md` (pro, 2026-07-02). The shared brief stays in `plans/`
(covers all four changes; the closer `prune-knowledge` decides its final home). **Downstream
propagation of everything here is FROZEN** per the standing operator hold — do NOT run
`sync_scaffold.py`. Scaffold-managed files touched here (the verifier agent, AGENTS.md shared spans,
`knowledge/README.md`, `sync_scaffold.py`) join the frozen pending-sync queue.

## Why (one paragraph)

The verify **verifier** (`.opencode/agents/openspec-verifier.md`, `bash: allow`, `edit: deny`)
mutated extrends' production SQLite DB during a real 2026-06-28 verify run. The standing mitigation
was assumed to be "only a per-prompt warning string," but investigation found the verifier already
carries `external_directory: {"*": deny, "/tmp/**": allow}` (present since its first commit,
2026-06-16 — *before* the incident). So directory-scoping was already in force and the write still
happened. This change closes the actual hole with a permission-level mechanism, adds a sanctioned
mid-session handoff file so downstream stops improvising root HANDOFF files outside every discipline,
makes scaffold staleness visible from the downstream repo (a sync provenance beacon), and files the
new-repo bootstrap steps as on-demand reference.

## The (a) design — permission-level fix, source-grounded (resolves direction-gate 🟡)

The direction gate required exploring PERMISSION-LEVEL tightening before settling for a prose
preamble. Done — with the opencode source (tag v1.17.4, the installed line; CLI binary is 1.17.11)
read directly, not just the docs.

**Root cause (source-verified — `packages/opencode/src/tool/shell.ts`):** `external_directory` only
path-scans a bash command when the command's binary is in a *hardcoded coreutils allowlist*
(`cd, rm, cp, mv, mkdir, touch, chmod, chown, cat, …` + powershell/cmd equivalents). Any other
binary — `sqlite3`, `psql`, `mysql`, `python`, `node`, `dd`, `tee` — and output redirection
(`> /outside/file`) are **never scanned**, so with `bash: allow` they execute regardless of
`external_directory`. The tool's own description calls command-argument path detection "advisory
only." So `sqlite3 ../extrends/prod.db "DELETE…"` bypasses the existing containment entirely — the
confirmed incident vector class. `external_directory` is NOT a reliable bash sandbox; it never was.

**The mechanism (the fix):** convert the verifier's `bash: allow` scalar to a **`bash:` pattern map
denylist** — catch-all `"*": allow` FIRST (opencode is last-match-wins via `findLast`, and the
verifier MUST retain the ability to run each downstream repo's arbitrary, unknowable test/smoke
command, so an *allowlist* is infeasible), then explicit `deny` rules for the destructive command
verbs a read-only reviewer has no business running: `rm/rmdir/mv/dd/truncate/shred/tee`, the raw
data-store clients `sqlite3/psql/mysql/mongo/mongosh/redis-cli`, mutating git
(`git push/commit/reset/checkout/restore/clean/rebase/merge`), and shell-wrappers `bash -c*`/`sh -c*`
(a cheap, rarely-needed evasion path to close).

**Why this is genuinely robust, not prose-in-disguise (source-verified):** opencode parses each
command with tree-sitter and evaluates the `bash` permission **per sub-command** — every node in a
pipeline, `$(…)` substitution, or subshell is matched separately, and **deny short-circuits the whole
call**. So `echo x | sqlite3 prod.db` and `$(sqlite3 …)` are both caught by `sqlite3 *: deny`. This
is a real permission gate on the direct/piped/substituted destructive-command vector, not a request
the model may ignore.

The denylist also denies the common interpreter **eval flags** (`python -c`, `python3 -c`, `node -e`/
`--eval`, `ruby -e`, `perl -e`) and shell wrappers (`bash -c`, `sh -c`) — the primary single-command
wrapper-evasion path for a destructive command. The verifier never needs these for legitimate work
(it runs the suite via `pytest`/`scripts/test-cmd`/`python -m pytest`). Trade-off, recorded: a
downstream repo whose canonical test or eyeball command is itself such a wrapper will surface a
permission *denial* (fail-loud, recoverable) the orchestrator must grant an exception for — never a
silent data loss.

**Honest residual risk (recorded, not hidden — the 🟡's explicit ask).** The denylist still cannot
cover, because covering them would break the verifier's core job or exceeds the accidental-incident
threat model:
1. **Writes *inside* an allowed command (the PRIMARY residual)** — the test suite (`pytest`) or a
   live smoke that itself opens and writes a data store. The shell parser cannot see inside `pytest`.
   The real backstop is **repo-level test isolation** (test-DB fixtures + blanked live credentials —
   already an AGENTS.md testing rule), a *downstream-repo* concern not expressible in the scaffold
   verifier's permissions.
2. **Output redirection** (`: > prod.db`) — redirection targets are not part of the matched command
   node, so a truncating redirect on an allowed base command is not caught by a `bash` pattern.
3. **Determined multi-step evasion** — e.g. writing a script to `/tmp` (allowed) then executing it,
   or an interpreter/eval form outside the enumerated set. This is outside the threat model (the
   incident class is an *accidental* destructive command by a well-intentioned verifier, not an
   adversary), but it is acknowledged rather than hidden.

Because of (1)–(3), a **data-safety preamble** in the verifier prompt is retained as the *judgment
layer* (snapshot/never-write-live-stores, eyeball via read-only paths or fixtures) — belt-and-
suspenders over the mechanism, explicitly the tertiary control, not the primary one. `external_directory`
containment is kept (it still catches the coreutils out-of-tree class) but is documented as
insufficient for the incident class. **Net posture: a real permission mechanism for the sharp edges +
honest documentation of what only repo-level test hygiene can close.** No control is presented as
"resolved" that isn't.

The spec delta for (a) (`noninteractive-delegation-safety`, ADDED requirement) encodes this and its
residual-risk boundary as a reviewed contract.

## The (b)/(c)/(d) designs

- **(b) Sanctioned mid-session handoff — `knowledge/HANDOFF.md`.** A single blessed file for a
  session that runs out of context mid-change, *before* archive reconciliation. STATUS.md is the
  wrong home: its write-discipline is "reconciled once at archive by the archive-executor," so it is
  deliberately NOT written mid-change — which is exactly the gap. Convention: **boot-read if present**
  (a booting agent reads it right after STATUS.md), **deleted on absorption** (ephemeral; its absence
  is the normal state, so it never grows the boot load — compatible with `knowledge-storage-stays-
  scalable`). Touches AGENTS.md span1 (the MANDATORY boot list) + `knowledge/README.md` taxonomy
  (both scaffold-managed → frozen queue). Delta: `knowledge-organization` (MODIFY boot-set +
  home-table).
- **(c) Sync drift beacon.** `sync()` stamps a small **non-manifest** provenance file
  (`.scaffold-version` at the target root) recording the scaffold's HEAD short-SHA, the commit's own
  committer-date, and subject — so a downstream agent can see how stale its scaffold is without
  running `--check` from the scaffold side. **Non-manifest is load-bearing:** `check()` iterates only
  manifest lines, so the beacon can never make `--check` report drift. Content is derived from the
  scaffold HEAD (deterministic per commit, not wall-clock) so `sync-is-idempotent` holds — two syncs
  at the same HEAD write byte-identical beacons. Best-effort: any git failure writes an `unknown`
  marker and never aborts the sync. Delta: `scaffold-sync-mechanism` (ADD sync-stamps-scaffold-
  provenance). Edits `scripts/sync_scaffold.py` (scaffold-managed → frozen queue) + tests.
- **(d) New-repo bootstrap checklist.** A small on-demand `knowledge/reference/new-repo-bootstrap.md`
  — the manual per-repo wiring a `cp -r`/sync does not do (chiefly the `.claude/settings.json`
  PreToolUse → `scaffold_check.py` hook and the commit-test gate `scripts/test-cmd`, plus filling
  per-repo AGENTS.md `## Project context` + config.yaml `context:` and seeding `knowledge/STATUS.md`
  / `questions/INDEX.md`). Change 1's sync-time hook-wiring warning already flags the mechanical half;
  this documents the fix. Scaffold-local reference file (NOT manifest-listed — you consult it in the
  scaffold when standing up a new repo). No spec delta.

## Acceptance criteria (verify phase)

1. **Full suite green:** `pytest -q` from repo root (`python3 -m pytest` does NOT resolve on this
   machine — pytest is python3.13 user install; use `pytest -q` or `scripts/test-cmd`). Includes new
   `scripts/test_sync_scaffold.py` beacon cases.
2. **(a) permission mechanism — live behavioral proof (not just docs):** with the edited verifier
   frontmatter, run `opencode run --agent openspec-verifier` (flash) on a throwaway prompt that (i)
   attempts a denied destructive command (e.g. `sqlite3 /tmp/probe.db "…"` or `rm /tmp/probe`) and
   confirm it is DENIED/auto-rejected, and (ii) runs an allowed read command (`git diff`, `pytest`)
   and confirm it proceeds. Confirms the pattern map parses in the installed opencode and that deny
   actually fires. A skipped/未-run probe is NOT a pass.
3. **(a) residual-risk honesty:** the delta spec + the verifier preamble state the three
   uncovered vectors plainly; no control is described as fully closing the hole. Reviewer/security
   pass confirms no overclaim.
4. **(b) handoff convention:** with a `knowledge/HANDOFF.md` present, the AGENTS.md boot instruction
   directs reading+absorbing+deleting it; `knowledge/README.md` lists the home; the
   `knowledge-organization` delta's boot-set scenario matches. `sync_scaffold.py --check ../psc-monitor`
   AGENTS.md span comparison behaves (span-merge still reconstructs cleanly — eyeball, do not sync).
5. **(c) drift beacon behaves:** `sync_scaffold.py <fixture-target>` writes `.scaffold-version` with
   the scaffold HEAD short-SHA/date/subject; a second sync at the same HEAD leaves it byte-identical;
   `--check <target>` still reports exactly the pre-existing manifest drift set and exit code —
   byte-for-byte unchanged — and never mentions `.scaffold-version`. Unit-tested; git-failure path
   writes `unknown` and does not abort.
6. **(d) bootstrap reference:** `knowledge/reference/new-repo-bootstrap.md` exists, is accurate
   against the real repo (each cited file/flag verified present), and `scripts/knowledge_lint.py`
   stays clean on it.
7. **scaffold_lint clean:** `python3 scripts/scaffold_lint.py` exits 0 after all edits (AGENTS.md
   anchors intact, no dangling skill refs introduced, budgets untouched).
8. **Multi-model verification per the verify skill (MEDIUM: self → pro → flash), simplicity/quality
   gate, AND the conditional security pass** — (a) is a data-safety surface, so the security pass
   applies and is NOT waived (standing operator instruction: do not waive multi-model passes unless
   explicitly told).
9. **No downstream sync in this change** — propagation stays frozen; scaffold-managed edits join the
   pending-sync queue at archive.

## Out of scope

- Any downstream repo edit or sync (frozen; operator authorizes separately).
- OS-level sandboxing of the verifier — opencode has no `--readonly`/sandbox mechanism (source-
  confirmed); permission config is the ceiling of what is expressible.
- Fixing repo-level test isolation in downstream repos (the real backstop for residual vector 2) —
  that is per-repo test-config work, recorded as a follow-on, not done here.
- Parser-based external_directory detection (opencode has an upstream TODO for it) — not ours to fix.
- Portfolio change `prune-knowledge` (the closer) — separate change.

## Reserved for archive (archive-executor)

`knowledge/STATUS.md` reconciliation (this change's section + cap rule — dropping the oldest
narrated-change section if the cap is exceeded); `knowledge/decisions/INDEX.md` registry line(s) for
the (a) permission decision and the (b)/(c) conventions; `knowledge/questions/INDEX.md` routing of the
residual-risk follow-ons (downstream test-isolation; `python -c`/redirection leaks; downstream
delete-on-freeze-lift note for any manifest changes) to Parked; **promote the three delta specs** into
`openspec/specs/`; decide whether the (a) research warrants a `knowledge/reference/` entry (the
opencode permission-model facts are durable and not in this repo's code); leave
`plans/succession-hardening/` residency to the `prune-knowledge` closer.
