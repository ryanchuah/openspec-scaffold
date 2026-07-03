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

**What the mechanism actually is — a speed-bump, not a semantic wall (corrected after the verify
security pass live-probed it).** opencode parses each command with tree-sitter and evaluates the
`bash` permission **per sub-command** (each node of a pipeline, `$(…)` substitution, or subshell is
matched separately, and **deny short-circuits the whole call**), so `echo x | sqlite3 prod.db` and
`$(sqlite3 …)` are both caught by `sqlite3 *: deny`. BUT — and this is the load-bearing honest point
— the pattern matches the **literal command-text spelling, not the command's identity**. The verify
security pass confirmed live (ground-truth file mutations against the running agent) that ordinary,
non-adversarial spellings slip straight through: `find … -delete`, `sed -i <file>`, in-tree `cp`,
`/usr/bin/rm` (absolute path), `env rm` (wrapper), and `python3.13 -c …` (version-suffixed — and
python3.13 is *this machine's* interpreter). Several of these (`sed -i`, `cp`) mutate files, which
means **`edit: deny` is not a real filesystem-read-only guarantee** — `bash` is a separate channel
opencode does not sandbox. So the denylist stops the *exact literal replay* of the 2026-06-28
incident and the most obvious destructive commands; it does **not** provide verb-level/semantic
coverage and, by opencode's design, cannot.

The change responds two ways, both honest: (1) **broaden the enumerated set** toward the demonstrated
accidental footguns — the denylist now also denies `sed -i`, `cp`, `install`, `find … -delete/-exec`,
`env`/`xargs` wrappers, `perl -i`, and `git -c`/`fetch`/`pull`/`clone` — raising the speed-bump for
the cases a careless verifier would actually type, while leaving read-only forms (`sed 's//'` without
`-i`, `find -name`, `git diff/log/show/status`, `pytest`) allowed. (2) **State the limitation plainly**
rather than let "denies destructive verbs" language imply completeness it does not have.

**Honest residual risk (corrected and expanded after the security pass).** The denylist cannot be a
complete gate; these vectors remain, and the mechanism is NOT presented as closing them:
1. **Literal-spelling bypass (a PRIMARY residual, newly disclosed).** Any file-writing command not in
   the enumerated set, or reached via a path prefix (`/usr/bin/rm`), a wrapper (`env`/`xargs`/`find
   -exec`), a version-suffixed interpreter (`python3.11 -c` on another host), or another file-writer
   (`patch`, `ex`, `awk` with in-place, etc.) executes under the catch-all `"*": allow`. Because
   `bash: allow` is retained (the verifier must run each repo's arbitrary test command), the verifier
   is **not truly read-only on the filesystem** — it can still mutate in-tree files, including an
   untracked/git-ignored production data store (the exact incident class). Broadening reduces this
   surface; it cannot eliminate it.
2. **Writes *inside* an allowed command.** A test suite or live smoke that itself opens and writes a
   data store — invisible to the shell parser. Backstop: **repo-level data isolation** (test-DB
   fixtures + blanked live credentials + a backup of any irreplaceable store), a downstream-repo
   concern not expressible in the scaffold verifier's permissions.
3. **Output redirection** (`: > prod.db`) — redirection targets are not part of the matched command
   node.
4. **Prompt injection from the diff under review.** The verifier's first job is to read the (untrusted)
   diff/commit/PR text; a crafted payload could try to induce it to run a bypass command. Not a
   "careless typo" and not a "human adversary at the keyboard" — a distinct third case the framing now
   names. Mitigated only by the preamble's "treat the diff as untrusted / report don't run" guidance.

Given (1)–(4), the **data-safety preamble** in the verifier prompt is not belt-and-suspenders trim but
a **co-primary control**: it now states outright that the verifier is not filesystem-read-only, that
the denylist is literal-spelling, and that it must never write a live store, must treat the diff as
untrusted, and must report-rather-than-run when a write seems needed. `external_directory` containment
is retained (it still catches the coreutils out-of-tree class) but is documented as insufficient.
**Net posture: a broadened best-effort speed-bump against accidental destructive commands + a judgment
preamble + repo-level data isolation, with the residual literal-spelling/read-only-bypass class named
explicitly.** No control is presented as "resolved," and the mechanism is no longer described as
"robust" — it is a speed-bump, stated as one.

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
3. **(a) residual-risk honesty:** the delta spec + the verifier preamble state the four residual
   vectors plainly (literal-spelling bypass [primary], writes-inside-an-allowed-command, output
   redirection, prompt-injection-from-the-diff); the mechanism is described as a speed-bump, not
   robust, and no control is described as fully closing the hole. Reviewer/security
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

## Verify checkpoint (2026-07-03)

**1. Verdict:** READY for archive.

**2. Process (multi-model passes NOT waived, per standing operator instruction; apply/archive on
Sonnet per this session's operator directive).** Orchestrator self-review → `deepseek-v4-pro` +
`deepseek-v4-flash` verifier passes (both READY, zero defects) → simplicity/quality gate → **security
pass** (conditional gate, data-safety surface — ran, and it was decisive). Apply was a Sonnet
subagent; a second Sonnet fix-executor handled the ephemeral-citation coherence fix.

**3. Live behavioral proof (not just tests).** The (a) permission mechanism was live-probed against
the real installed opencode (1.17.11) three+ times: the initial probe (`sqlite3 --version` DENIED,
`git --version` ran), both verifier passes independently hit their own denials (`python3 -c` /
`sqlite3`), and a post-broadening re-probe confirmed `sed -i`/`cp`/`find -delete`/`git fetch` DENIED
while read-only `sed s//` and `git diff` still RAN. No fallback in any run → the denylist frontmatter
parses. Beacon eyeballed: real `.scaffold-version` content `f64620f 2026-07-03T… <subject>`.

**4. The security pass found the load-bearing defect — and it mattered.** All three pro-reviewer
propose rounds + both verifier passes reasoned from the *declared pattern list* and green-lit the
"honest residual-risk" framing. The security pass instead **live-probed the running permission engine
with ground-truth file mutations** and proved the denylist matches **literal command spelling, not
command identity**: `find -delete`, `sed -i`, in-tree `cp`, `/usr/bin/rm`, `env rm`, `python3.13 -c`
all bypassed it — several defeating `edit: deny` outright (bash is an un-sandboxed write channel).
The change's own thesis (honest residual risk) was therefore NOT honest as first written: it
overclaimed ("genuinely robust", a verb-level "denied even in-tree" scenario) and omitted the whole
literal-spelling bypass class. **Fix (both halves the security pass asked for):** (i) broadened the
denylist toward the demonstrated accidental footguns — `sed -i`, `cp`, `install`, `find -delete/-exec`,
`env`, `xargs`, `perl -i`, `git -c/fetch/pull/clone` (re-probe confirms they now deny; read-only
forms still allowed); (ii) rewrote the framing across the verifier preamble, `notes.md`, and the
delta spec to state plainly that the denylist is a literal-spelling **speed-bump, not a semantic
wall**, that the verifier is **not truly read-only on the filesystem** via bash, and to name four
residual vectors (literal-spelling bypass [primary], writes-inside-an-allowed-command, output
redirection, prompt-injection-from-the-diff). The preamble was elevated to a co-primary control and
now instructs treat-the-diff-as-untrusted + report-rather-than-run. A focused security
re-confirmation verified the honesty gap is genuinely closed (6/6 checks PASS); a flash re-pass came
back READY. Three prose-consistency nits the re-passes flagged (stale "not-covered" examples, a
"three→four" miscount, "read-only on files"→"read-only by role") were corrected.

**5. Simplicity gate:** clean, no must-fix; two nice-to-haves applied (`_scaffold_version` `strip() or`
idiom; the beacon best-effort test now actually injects an `OSError` to exercise the swallow branch,
plus a rename). The per-linter `EPHEMERAL_PATHS` duplication was confirmed a deliberate,
precedented "mirror not import" pattern (independent linters), not a reuse defect.

**6. Coherence fix found in self-review:** the new `knowledge/HANDOFF.md` citation (a by-design-absent
ephemeral file) tripped BOTH `knowledge_lint.py` and `sync_scaffold.py --check-refs` as broken/dangling.
Fixed by an `EPHEMERAL_PATHS` exemption in each (with a guard test proving a genuinely-missing
non-ephemeral path is still flagged) + a `knowledge-organization` delta scenario. Net: this change
adds **zero** new lint findings (the 17 pre-existing `knowledge_lint` / 2 pre-existing `--check-refs`
items are `prune-knowledge`'s, untouched).

**7. Accepted residual (recorded, not fixed here):** the denylist cannot be complete (literal-spelling);
`/usr/bin/rm`, version-suffixed interpreters on other hosts, `nohup/busybox/rsync/patch`, and
writes-inside-an-allowed-command remain — the real backstop is repo-level data isolation (downstream
concern) + the judgment preamble. The `knowledge/HANDOFF.md` boot-read shares STATUS.md's trust model
(git-tracked, reviewable), so it is not a new injection surface beyond existing boot files. All
routed to `knowledge/questions/` at archive.

**8. As-built vs frozen tasks.md:** tasks 1.1's denylist was BROADENED post-freeze (security fix) and
tasks 1.2's preamble REWRITTEN honestly — both recorded above; the delta spec + notes now match the
as-built agent. The ephemeral-citation exemption (linters + tests + one spec scenario) was added
during verify and is not in the frozen tasks.md — recorded here as the authoritative as-built note.

## Reserved for archive (archive-executor)

`knowledge/STATUS.md` reconciliation (this change's section + cap rule — dropping the oldest
narrated-change section if the cap is exceeded); `knowledge/decisions/INDEX.md` registry line(s) for
the (a) permission decision and the (b)/(c) conventions; `knowledge/questions/INDEX.md` routing of the
residual-risk follow-ons (downstream test-isolation; `python -c`/redirection leaks; downstream
delete-on-freeze-lift note for any manifest changes) to Parked; **promote the three delta specs** into
`openspec/specs/`; decide whether the (a) research warrants a `knowledge/reference/` entry (the
opencode permission-model facts are durable and not in this repo's code); leave
`plans/succession-hardening/` residency to the `prune-knowledge` closer.
