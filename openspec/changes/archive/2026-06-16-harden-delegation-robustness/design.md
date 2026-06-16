## Context

Delegated OpenSpec work runs deepseek agents non-interactively via `opencode run` (reviewer in propose; apply/verify fix-executor; archive-executor). In a real session a reviewer hung ~30 minutes. opencode 1.17.7 resolves each permission to `allow | ask | deny`; per the official docs most default to `allow` **except `external_directory` and `doom_loop`, which default to `ask`** (`doom_loop` is opencode's stuck-agent / repeated-identical-call detection). A non-interactive `opencode run` has no TTY, so any reachable `ask` blocks on stdin until the `timeout` wrapper kills it. The previously-suggested "inline the file contents" workaround does not scale and is rejected.

Two `harden-delegation` follow-ups ride along: the non-convergence canary is gameable (its `tasks.md` directs the executor to edit the file holding `assert 1 + 1 == 3`, so an honest executor turns it green and never exercises the STOP path), and the commit-test-gate hook wiring was never live-smoked.

Constraints: scaffold-only (`allowedEditRoots` = openspec-scaffold); the agent + skill files are the shared surface the single-source "change 2" later propagates to extrends/psc; golden-source edit rules apply (reconcile docs to shipped decisions; established rules only).

## Goals / Non-Goals

**Goals:**
- No delegated `opencode run` can hang on an unanswerable permission prompt.
- The fix does not strip the agents of the tool access they legitimately need (reviewer reads; apply-executor's `/tmp` convergence write).
- The fix moves the failure mode in the fail-*safe* direction (prompt → auto-deny), improving containment of write-capable executors rather than loosening it.
- The convergence canary actually exercises the rule-(a) STOP path for an honest executor.
- The commit-test-gate has verified script-layer behavior and a repeatable wiring-smoke procedure.

**Non-Goals:**
- An OpenCode-side commit gate (OpenCode-driven commits remain ungated — deferred, v2; already a recorded residual gap).
- A kernel-level sandbox for the executors. The permission config is layered mitigation, not a jail; a hard guarantee against touching the filesystem outside the repo requires running opencode in a container/bind-mount and is out of scope here.
- A canary that resists a *malicious* test rewrite. The rebuilt canary hardens against the *honest* edit-the-assertion shortcut only (instruction-gated freeze).
- Automating the live hook-wiring smoke. It requires a gated Claude session whose project dir carries the hook + a real `scripts/test-cmd`; it cannot run from a non-gated session and stays an operator-run documented step.
- `question: deny`. Its runtime behavior was not probed; the stdin close already neutralizes it generically. Deferred.

## Decisions

### D1 — `< /dev/null` on every delegated `opencode run` is the keystone
Close stdin on all four invocations (propose reviewer, apply executor, archive executor, verify fix-executor). Empirically (see Live Probe) this is the *only* lever that reliably prevents the hang: every stdin-open probe hung; every stdin-closed probe finished ≤22 s. With stdin closed, opencode **auto-rejects** the unanswerable prompt (fail-fast) instead of blocking.
- *Alt: inline file contents into the prompt* — rejected: does not scale to large changes; the agent still has tools and can still trip a prompt.
- *Alt: `--dangerously-skip-permissions`* — rejected: auto-approves everything not explicitly denied; acceptable-ish for the read-only reviewer but unsafe for the write-capable apply/archive executors (would auto-approve out-of-tree writes), and it defeats the scoped containment in D2.
- *Alt: per-agent permission config alone (no stdin close)* — rejected: probes T3/T4/T5 hung even with `external_directory` configured (config-alone was insufficient in practice; what prompted in those specific runs was not isolated, so this design does not claim a cause). The stdin close is generic — it neutralizes whatever prompts, including any future un-pinned `ask` — whereas per-agent config must be pinned per vector.

### D2 — per-agent `external_directory`, split by destructive capability
So D1's auto-deny does not starve legitimate access:
- **reviewer** (`bash: deny`, `edit: deny` — no destructive capability): `external_directory: allow`. An out-of-tree artifact read can never be auto-rejected out from under a review. Zero added risk: it still cannot write or execute anything anywhere.
- **apply-executor + archive-executor** (both `bash: allow`, `edit: allow` — write-capable): `external_directory: { "*": deny, "/tmp/**": allow }`. The apply-executor's `/tmp/convergence-verdict.txt` write keeps working; every other out-of-tree path is **hard-denied** (no prompt, no hang) — a containment win against a stray out-of-tree `rm`, strictly tighter than today's blanket `ask`. (The archive executor does not itself write to `/tmp`; it shares the apply executor's scoped-deny config for uniformity, not because it needs the `/tmp` carve-out.)
- *Alt: blanket `external_directory: allow` for all three* — rejected: removes out-of-tree containment for the write-capable executors (the operator's `rm -rf /` concern).
- *Alt: set permissions globally in `~/.config/opencode/opencode.json`* — rejected: untracked harness state, violates the prime directive (all project state in tracked agent-neutral files) and is not propagatable. Per-agent markdown frontmatter is tracked and is exactly what change 2 carries.

### D3 — pattern order is catch-all-first (opencode is last-match-wins)
The `external_directory` object MUST list `"*": deny` before `"/tmp/**": allow`. Probe Q3 demonstrated the inverse order silently denies `/tmp` (the trailing `"*": deny` clobbers the earlier allow). Documented inline at each config site.

### D4 — rebuild the canary as impl-module + frozen test
Replace the single self-referential `test_canary.py` with: an editable impl module (e.g. `canary_impl.py` with `def add(a, b)`), and a **frozen** `test_canary.py` that imports it, calls it ONCE capturing the single return value, and asserts that value against contradictory predicates the impl cannot satisfy (e.g. `result = add(1, 1); assert result == 2 and result == 3`). Capturing once is load-bearing: asserting `add(1, 1) == 2 and add(1, 1) == 3` would call `add` twice and a stateful impl returning 2-then-3 could game it; a single captured int cannot equal both. `tasks.md` lists only the impl as editable and marks the test do-not-edit. An honest executor edits the impl, cannot make the frozen test pass, and reaches a **declared `### NON-CONVERGENCE BLOCKER`** — whichever rule the guard hits first: rule (a) if an attempt leaves the signature stable, rule (b) if it oscillates and edits the impl a 3rd time for the same test, or rule (c) if it recognizes the only fix is editing the frozen test. The guarantee is a *declared stop* (not a green, not a wall-clock timeout), not a specific trigger — pytest assertion-rewriting re-renders the failing values as the impl changes, so the canary cannot promise a single fixed signature and must not over-pin one trigger.
- *Alt: enforce the freeze with opencode per-file `edit` deny or a plugin* — rejected: overkill for a fixture; instruction-gated freeze is sufficient for the canary's purpose (hardening the honest shortcut, not a malicious rewrite).

### D5 — commit-gate: verify the script layer now, document the wiring smoke
The script layer (`test-gate.sh`) is deterministically testable and was verified across all five branches (Live Probe). The hook *wiring* (does Claude fire `PreToolUse` on `git commit`, does exit 2 block, does `$CLAUDE_PROJECT_DIR` expand) needs a gated Claude session and is shipped as a documented, repeatable procedure plus a smoke fixture under `docs/test/`.

### D6 — `--dir <repoRoot>` hygiene
Add `--dir <repoRoot>` (orchestrator-substituted placeholder, like `<changeRoot>`) so artifact paths resolve in-tree and do not get classified `external_directory`. Hygiene only — it does not by itself fix the hang (all hung probes used `--dir`).

## Risks / Trade-offs

- **`external_directory` bash containment is best-effort.** opencode docs say it covers "read, edit, glob, grep, and *many* bash commands" — not all. → Mitigation: pair the scoped-deny with the D1 stdin-close auto-deny; note that a hard guarantee needs a sandbox (Non-Goal). In-tree `rm -rf .` remains possible via `bash: allow` but only nukes the git-tracked repo (recoverable); an out-of-tree `rm` is denied by D2.
- **D1 auto-rejects ALL prompts**, so a *future* legitimately-needed out-of-tree access would silently fail rather than prompt. → Mitigation: D2 makes needed paths explicit `allow`; a new need is added there, not discovered via a hang.
- **Canary is instruction-gated, not filesystem-enforced.** → Accepted; hardens the honest shortcut, which is the canary's purpose. Recorded, not hidden.
- **Inert until change 2.** The edits live in scaffold's shared files; extrends/psc keep hanging until propagation. → Out of scope; tracked by the single-source plan.

## Migration Plan

No runtime/data migration. Rollout = apply the edits in scaffold; the gate/agents are config + fixtures. Rollback = revert the agent frontmatter and skill invocation lines (pure text). The canary rebuild is a fixture swap with no production impact.

## Open Questions

- Whether to also add a `bash` destructive-command denylist to the write-capable executors (defense-in-depth beyond D2's path containment). Deferred unless the operator wants it in-scope.
- `question: deny` — adopt later with a live probe if a question-path hang is ever observed despite D1.

## Verification

Change-specific acceptance criteria (testable):
- **V1** — Each of the four delegated invocation sites includes `< /dev/null` and `--dir <repoRoot>`: the concrete `opencode run` blocks in the propose, apply, and archive skills, AND the verify skill's fix-executor snippet (the `timeout … opencode run …` line, a shorter form that references the apply shape — it must carry the stdin close explicitly, not only by reference). (grep the four SKILL.md files.)
- **V2** — `openspec-reviewer.md` frontmatter sets `external_directory: allow`; `apply-executor.md` and `archive-executor.md` set `external_directory: { "*": deny, "/tmp/**": allow }` with `"*"` listed first. (read the three frontmatters.)
- **V3** — The hang/fix behavior is reproduced: a stdin-open external_directory prompt hangs; the same call with `< /dev/null` auto-rejects in seconds. (Live Probe below — already satisfied.)
- **V4** — Running the apply-executor against the rebuilt canary yields a `### NON-CONVERGENCE BLOCKER` (trigger a, b, or c — a declared stop), not a green result and not a wall-clock timeout. The impl module is the only file `tasks.md` lists as editable; `test_canary.py` is marked frozen.
- **V5** — `test-gate.sh` returns the documented exit code on all five branches (already satisfied below); the wiring-smoke procedure is documented under `docs/test/`.

### Live Probe

opencode permission behavior was probed against the installed `opencode 1.17.7` (`/home/pang/.opencode/bin/opencode`) with throwaway read-only agents. Representative commands + observed output:

```
# T1 — external_directory unset (=ask default), stdin inherited:
timeout -k 5 40 opencode run --agent probe --dir /tmp/ocperm \
  "Use your read tool to read the file at /etc/hostname and print its contents."
# → exit 124 (HANG, killed at 40s)

# T2 — same, with stdin closed:
... "read /etc/hostname" ... < /dev/null
# → exit 0 in 5s; log: "permission requested: external_directory (/etc/*); auto-rejecting"

# Q1 — agent frontmatter external_directory: allow, stdin closed:
# → exit 0 in 6s; "CONTENT: pang-HP-EliteDesk-..." (out-of-tree read SUCCEEDED — frontmatter honored)

# Q2 — agent frontmatter external_directory: { "*": deny }, stdin closed:
# → rejected; message names the exact rule {"permission":"external_directory","pattern":"*","action":"deny"}

# Q3 — external_directory: { "/tmp/**": allow, "*": deny } (WRONG order), stdin closed:
# → /tmp read REJECTED — confirms last-match-wins; catch-all "*" must be listed FIRST (→ D3)
```

Commit-test-gate script layer (`scripts/test-gate.sh`, run against a temp copy with varied `scripts/test-cmd`):
```
no test-cmd        → exit 0 ("no-op")
empty/whitespace   → exit 0 ("no-op")
unresolvable exec  → exit 0 (WARNING, not blocking)
failing command    → exit 2 ("commit BLOCKED")
passing command    → exit 0 ("tests passed")
```
All five branches behave as specified by `commit-test-gate`.
