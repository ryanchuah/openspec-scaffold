# Explore brief — harden-delegation-robustness

Context captured during the explore phase. The reviewer should treat the empirical
results below as ground truth (they were produced by live probes, not inferred).

## Three combined threads
1. **(c) opencode non-interactive hang** — a delegated `opencode run --agent openspec-reviewer`
   hung ~30 min in a real session.
2. **(b) gameable convergence canary** — `harden-delegation` follow-up, still open.
3. **(a) commit-test-gate hook never live-smoked** — `harden-delegation` follow-up, still open.

## (c) Root cause — EMPIRICALLY CONFIRMED, not guessed
opencode 1.17.7 permissions resolve to `allow | ask | deny`. Per the official docs
(opencode.ai/docs/permissions, fetched via `scripts/fetch_clean.py`): "most permissions default
to `allow`" EXCEPT `doom_loop` and `external_directory`, which default to **`ask`**. A non-interactive
`opencode run` has no TTY, so any reachable `ask` blocks on stdin until the `timeout` wrapper kills it.

Probe suite (8 bounded `opencode run` calls against throwaway read-only agents; `timeout -k` bounded):

| Probe | Permission config | stdin | Outcome |
|---|---|---|---|
| T1 | `external_directory` unset (=ask) | open | **HANG** (40 s timeout, exit 124) |
| T2 | same | `< /dev/null` | **5 s**; log: `permission requested: external_directory (/etc/*); auto-rejecting` |
| T3–T5 | frontmatter `external_directory` configs | open | **HANG** (all) |
| Q1 | `external_directory: allow` | `< /dev/null` | **6 s, read SUCCEEDED** (config honored) |
| Q2 | `{ "*": deny }` | `< /dev/null` | rejected; message names the exact rule (config honored) |
| Q3 | `{ "/tmp/**": allow, "*": deny }` | `< /dev/null` | rejected — **pattern-order bug, see below** |

Conclusions:
- The hang IS `external_directory` prompting with no answerer (T2 log is the smoking gun).
- **`< /dev/null` is the keystone fix**: every stdin-closed run finished ≤22 s; every stdin-open run hung.
  With stdin closed opencode AUTO-REJECTS the prompt (fail-fast) — the fail-*safe* direction.
- `--dir` alone does NOT prevent the hang (all hung probes used `--dir`).
- Agent-markdown frontmatter `permission` (including object/pattern syntax) IS honored (Q1, Q2).
- **opencode is last-match-wins**; the catch-all `"*"` must be listed FIRST. Q3 put `"/tmp/**": allow`
  before `"*": deny`, so the deny clobbered the allow. The correct order is `{ "*": deny, "/tmp/**": allow }`.

### Design implication
- Keystone: `< /dev/null` on all four `opencode run` invocations (propose/apply/archive/verify).
- Refinement so auto-deny does not starve legit paths, split by destructive capability:
  - **reviewer** (read-only, `bash`/`edit` deny): `external_directory: allow` — harmless, prevents an
    auto-rejected out-of-tree read from starving a review.
  - **apply AND archive executors** (both `bash`/`edit` allow → write-capable):
    `external_directory: { "*": deny, "/tmp/**": allow }` — keeps the apply-executor's
    `/tmp/convergence-verdict.txt` write working while hard-denying every other out-of-tree path
    (containment against a stray out-of-tree `rm`).
- `--dir <repoRoot>` as hygiene (keeps artifact paths in-tree).
- `doom_loop`/`question` were NOT independently reproduced as hang vectors here; they are documented
  `ask`/blocking sources that `< /dev/null` also neutralizes — that genericity is why the stdin-close
  is the keystone rather than chasing each vector. **`question: deny` is therefore deferred** (its
  runtime behavior was unprobed); this change does not assert it and relies on the stdin close.

## (b) Canary is gameable — confirmed by reading the fixture
`docs/test/canary-non-convergence/` holds `assert 1 + 1 == 3` in `test_canary.py`, and `tasks.md`
literally says *"Files affected: `test_canary.py`"* with acceptance "pytest exits 0." So an HONEST
executor edits the assertion → green → the rule-(a) STOP path is NEVER exercised. Fix: move the
contradiction into an impl module the FROZEN test imports; the only editable file (the impl) cannot
satisfy the frozen test → genuine non-convergence. Enforcement is instruction-level (tasks.md marks
the test frozen); the apply-executor has `edit: allow`, so this hardens against the honest shortcut,
not a malicious rewrite — sufficient for the canary's purpose.

## (a) Commit-gate — script layer VERIFIED here; wiring still needs a gated session
`test-gate.sh` was live-run across all five branches: no `scripts/test-cmd` → exit 0 no-op; empty →
0; unresolvable executable → 0 + warning; failing cmd → **exit 2 (BLOCKED)**; passing cmd → 0. The
remaining gap is the HOOK WIRING (does Claude Code fire the `PreToolUse` hook on `git commit`, does
exit 2 block, does `$CLAUDE_PROJECT_DIR` expand) — this needs a Claude session whose project dir
carries the settings.json + a real `scripts/test-cmd`; it cannot run from a non-gated session. Ship a
repeatable smoke procedure; leave the live wiring smoke as a documented gated-session step.

## Constraints
- Scaffold-only (`allowedEditRoots` = openspec-scaffold). Inert until single-source "change 2"
  propagates the shared agent/skill files to extrends/psc.
- Golden-source edit rules apply: established/documented rules only; reconcile docs to shipped decisions.
