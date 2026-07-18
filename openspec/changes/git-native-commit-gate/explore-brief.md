# Explore brief — git-native commit-test gate (close the prefix-evasion + cross-agent bypass)

**Tier (self-classified under autonomy grant):** **COMPLEX** — enforcement/safety-mechanism change
whose subtle failure mode (a false defer = silent gate gap) demands a reviewed design; cross-repo
blast radius (scaffold-managed → extrends + psc-monitor); touches the load-bearing cross-agent
invariant and the AGENTS.md carve-out. Runs the full OpenSpec lifecycle (proposal + design + tasks,
each reviewed; verify adds the flash lens pass). *Upgraded from an initial MEDIUM lean after the
direction gate flagged the defer mechanism as architecturally non-trivial and explicitly requested a
design-level specification (see carry-forward below).*

## Problem

The commit-test gate (the "commit lint") is silently bypassable, and agents hit the bypass by
accident. Operator ask (2026-07-18): *"Some agents manage to bypass the commit lint check by
accident — I suspect `cd dir && git commit …`. Should we install pre-commit hooks?"*

## Root cause

The gate is a **Claude Code `PreToolUse` hook** in `.claude/settings.json` matched on
`if: "Bash(git commit*)"` — a **prefix-anchored glob** that only fires when the tool command
*starts with* the literal `git commit`. Two independent gaps:

1. **Prefix evasion (Claude).** Any commit whose command does not *start* with `git commit` skips
   the gate: `cd repo && git commit …`, `git -C repo commit …`, `env FOO= git commit …`, `!`-bang
   commits, operator-terminal commits. Irony: `test-gate.sh` already strips env-prefixes and handles
   `git -C`/`-c` internally — but that hardening is dead code behind a matcher that never lets it
   fire for those spellings.
2. **Cross-agent gap (the stronger argument).** `PreToolUse` hooks are Claude-only. OpenCode/DeepSeek
   agents — which this scaffold explicitly supports (AGENTS.md "Cross-agent compatibility",
   load-bearing) — never run the gate at all.

**Not hypothetical.** psc-monitor commit `0e5a823` (2026-07-16) landed a file the live-tree
`knowledge_lint` gate would have blocked ⟹ it reached HEAD via one of these evasion paths.

`git commit --no-verify` does NOT bypass the current hook (it is external to git); the exposure is
the *silent* prefix-evasion / non-Claude forms, not an explicit opt-out.

## Prior reasoning acknowledged (not re-litigated blindly)

`scripts/scaffold_check.py:16` records that a repo-wide `core.hooksPath` / `.git/hooks/pre-commit`
"was considered and **rejected for W1**." That rejection was **scoped to the scaffold-managed-file
guard**, whose stated purpose is narrowly "catching Claude's *accidental edits* — which this already
does." That rationale does not transfer to the commit-*test* gate, because the test gate has a
**documented cross-agent coverage requirement** the scaffold_check guard does not. The
`commit-gate-bypass.md` write-up (2026-07-16, later, with the psc-monitor evidence) re-opened exactly
this. So the per-clone-install cost the W1 note weighed is now justified by evidence that did not
exist at W1. We adopt git-native **for the test gate**; the scaffold_check guard's separate
Claude-only-is-fine calculus is untouched here (see follow-on below).

## Solution direction

Add a **git-native `pre-commit` hook** that git itself runs on every `git commit` regardless of
command spelling and regardless of harness. Git resolves it via `core.hooksPath` (the clone-safe way
— raw `.git/hooks/` is not tracked and not copied on clone). The hook execs the existing
`scripts/check.sh` (the single definition of green), so there is exactly one definition of "green."

### Components
- **`scripts/githooks/pre-commit`** (new, scaffold-managed, byte-identical downstream) — execs
  `scripts/check.sh`. No stdin/command parsing needed: git fires pre-commit only on real commits.
- **`scripts/setup-hooks.sh`** (new, scaffold-managed) — idempotent; runs
  `git config core.hooksPath scripts/githooks`. One per-clone bootstrap step.
- **Bootstrap doc** — add the `setup-hooks.sh` step to `knowledge/reference/new-repo-bootstrap.md`
  (scaffold-local checklist), alongside the existing manual hook-wiring step.

### Key design decision — what happens to the existing Claude `PreToolUse` test-gate hook?

**Recommended: Option D — defer-to-git-native (defense-in-depth, no double-run, no orphaning).**
Keep `test-gate.sh` wired as the `PreToolUse` hook, but give it **one new early branch**: if the
git-native hook is installed and active (`core.hooksPath` resolves to `scripts/githooks` and
`scripts/githooks/pre-commit` is executable), it prints "deferring to git-native pre-commit" and
exits 0 (no-op) — because git will run `check.sh` a moment later. Otherwise it runs `check.sh` as
today. Result:
- **Normal clone (git hook wired):** `PreToolUse` no-ops → git-native runs `check.sh` **once**. No
  double-run.
- **Clone that forgot `setup-hooks.sh` (git hook absent):** `PreToolUse` runs `check.sh` as a
  Claude-only fallback → regression risk (unset `core.hooksPath` = no gate) is closed for Claude.
- Git-native is the primary, agent-neutral, spelling-agnostic gate; `test-gate.sh` degrades to a
  Claude-only safety net that only fires when the primary is not wired.

**Considered and rejected:**
- **A — keep both, unconditional:** `check.sh` runs twice on well-behaved Claude commits. Adds
  friction to the *well-behaved* path — perverse, since friction is what breeds the bypasses we are
  fixing.
- **B — remove `PreToolUse` entirely, git-native only:** simplest, but a clone that skips
  `setup-hooks.sh` has **no** gate at all (worse than today's Claude-gated). Loses the belt-and-braces
  regression guard for zero benefit over D.
- **C — repurpose `PreToolUse` to a cheap "is the git hook installed?" assert:** orphans
  `test-gate.sh` (its tests, smoke fixture, downstream wiring) for a marginal gain over D.

### Why the git-native layer is a quality win
Unlike the Claude `PreToolUse` hook (which needs a *gated Claude session* to smoke — see
`tests/commit-gate-smoke/`), the git-native hook is **deterministically unit-testable**: a pytest can
create a throwaway git repo, set `core.hooksPath`, and assert commits are blocked (red suite) /
allowed (green suite) across every evasion spelling (`cd &&`, `git -C`, `env FOO=`). This is the
first commit-gate layer we can fully automate.

## Scope boundary (explicit out-of-scope)
- **`scaffold_check.py`'s identical prefix-evasion bypass** (the scaffold-managed-file guard is *also*
  a prefix-anchored `PreToolUse` hook, and also Claude-only downstream). Same evasion class; folding
  it into the git-native hook downstream is a natural follow-on — but scaffold_check must **not** run
  in the golden-source repo (editing scaffold files is the point here) and must stay
  `--no-verify`-skippable, so a byte-identical hook can't host it unconditionally. **Deferred** to a
  follow-on question; this change keeps the git-native hook running `check.sh` **only**.
- **Downstream propagation** of this change (operator-gated) and any downstream `settings.json`
  edits — happen after archive, on explicit operator instruction.
- **Retiring `test-gate.sh`** — kept (Option D uses it as the fallback); no orphaning.

## Success criteria
1. A commit that would fail `check.sh` (red suite or lint violation) is **blocked** by git in a
   throwaway repo with `core.hooksPath` set — across `git commit`, `cd && git commit`,
   `git -C … commit`, and `env FOO= git commit` spellings.
2. A green commit is **allowed**.
3. `test-gate.sh` no-ops (defers) when the git hook is active; runs `check.sh` when it is not.
4. `check.sh` runs at most **once** per commit in a normally-set-up clone.
5. Scaffold's own `pytest` suite (incl. `scaffold_lint`) green; the new hook + defer branch covered
   by automated tests.

## Direction-gate carry-forward (PREMISE: AGREE, 2026-07-18) — design.md must resolve

The pro direction gate agreed with the direction and flagged that the Option-D defer mechanism is
**architecturally non-trivial** (`test-gate.sh` is currently git-free). Acknowledged here; the precise
specification is deferred to `design.md`:
- **🔴 Defer algorithm must be fail-safe** — defer ONLY on positive confirmation git-native will fire;
  on any uncertainty (git absent, `rev-parse`/config failure, path-resolution ambiguity) run
  `check.sh`. A false defer = silent gap.
- **🟡 Preserve Claude `--no-verify` test coverage** — do not defer when the commit carries
  `--no-verify`/`-n`; test-gate runs `check.sh` itself. (Git-native inherently skips on `--no-verify`
  — a visible opt-out, accepted for non-Claude.)
- **🟡 `setup-hooks.sh`** — `git config --local`; warn on overwriting a differing existing
  `core.hooksPath`.
- **🟡 Test strategy** — specify the throwaway-repo fixture (or minimal stub-hook) concretely.

Full review captured in `premise-review.md`.
