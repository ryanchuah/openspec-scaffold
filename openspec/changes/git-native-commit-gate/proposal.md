## Why

The commit-test gate ("commit lint") is silently bypassable, and agents hit the bypass by accident.
It is wired only as a Claude Code `PreToolUse` hook matched on `Bash(git commit*)` — a
**prefix-anchored** glob that fires only when the tool command *starts with* `git commit`. Two gaps
follow: (1) any other spelling skips it silently — `cd repo && git commit …`, `git -C repo commit …`,
`env FOO= git commit …`, `!`-bang or operator-terminal commits; (2) `PreToolUse` hooks are Claude-only,
so OpenCode/DeepSeek agents — which this scaffold explicitly supports (the load-bearing "Cross-agent
compatibility" invariant) — never run the gate at all. This is not hypothetical: psc-monitor commit
`0e5a823` (2026-07-16) landed a file the live-tree `knowledge_lint` gate would have blocked, meaning
it reached HEAD via one of these evasion paths.

## What Changes

- **Add a git-native `pre-commit` hook** (`scripts/githooks/pre-commit`, scaffold-managed,
  byte-identical downstream) that execs `scripts/check.sh` (the single definition of green). git runs
  it on every `git commit` regardless of command spelling and regardless of harness — closing both the
  prefix-evasion gap and the cross-agent gap in one mechanism.
- **Add `scripts/setup-hooks.sh`** (scaffold-managed) — the clone-safe wiring that sets
  `git config --local core.hooksPath scripts/githooks`. **Conflict-safe:** idempotent no-op when
  already `scripts/githooks`; sets it when unset; **warns and aborts WITHOUT overwriting** when an
  existing `core.hooksPath` points elsewhere (never silently clobbers a developer's custom hooks — the
  developer reconciles). (`core.hooksPath` is the clone-safe wiring; raw `.git/hooks/` is not tracked
  and not copied on clone.) Add the step to `knowledge/reference/new-repo-bootstrap.md`.
- **Make the existing Claude `PreToolUse` test-gate defer to git-native (Option D — defense-in-depth,
  no double-run).** `scripts/test-gate.sh` gains a **fail-safe** early branch: it no-ops **only** when
  it positively confirms git-native will fire (an executable pre-commit hook at the configured
  `core.hooksPath`) **and** the commit is not `--no-verify`/`-n`; on any uncertainty it runs `check.sh`
  as today. Net effect: a normally set-up clone runs `check.sh` at most **once** per commit; a clone
  that forgot `setup-hooks.sh` still has the Claude-only fallback (no silent regression); Claude's
  `--no-verify` commits stay gated (matching today).
- **Add a deterministic automated test** for the git-native layer — a throwaway-repo pytest that
  asserts commits are blocked (red) / allowed (green) across every evasion spelling. This is the first
  commit-gate layer that does not require a gated Claude session to smoke.
- **Update the AGENTS.md cross-agent-compatibility carve-out** and the `commit-test-gate` spec so the
  git-native hook (tracked, agent-neutral) is recorded as the primary enforcement layer and
  `test-gate.sh` as its Claude-only fallback.

**Not breaking.** Existing behavior is preserved where git-native is not wired; the change only adds a
stronger, agent-neutral enforcement layer and makes the Claude hook defer to it when present.

## Capabilities

### New Capabilities
No new capability specs — this change modifies the existing `commit-test-gate` capability only.

### Modified Capabilities
- `commit-test-gate`: adds a git-native `pre-commit` enforcement layer (spelling-agnostic,
  cross-agent) as the primary gate; the `PreToolUse` hook becomes a fail-safe Claude-only fallback
  that defers to git-native when it is wired; the smoke-fixture requirement gains a deterministic
  automated git-native test; the instruction-docs carve-out covers the git-native hook.

## Impact

- **New scaffold-managed files:** `scripts/githooks/pre-commit`, `scripts/setup-hooks.sh` (+ manifest
  entries), and a new `scripts/test_githook_pre_commit.py` (+ manifest entry).
- **Modified scaffold-managed files:** `scripts/test-gate.sh` (fail-safe defer branch), `AGENTS.md`
  (cross-agent carve-out span).
- **Modified non-scaffold-managed test/docs:** `tests/commit-gate-smoke/README.md` (document the
  git-native layer — NOT in the manifest; do not add it) and
  `knowledge/reference/new-repo-bootstrap.md` (scaffold-local bootstrap step).
- **Test dependency note:** the new throwaway-repo pytest exercises `check.sh`, which runs
  `ruff check .` — the fixture must provide a `ruff.toml` at the throwaway repo root (or the lint
  stage is skipped/degraded), mirroring the existing smoke fixture. `check.sh` scans the whole working
  tree (not just staged files) — preserved behavior, not a regression.
- **Spec:** delta to `openspec/specs/commit-test-gate/spec.md`.
- **Out of scope (deferred follow-ons):** adapting `scaffold_check.py`'s identical prefix-evasion
  bypass to git-native (it must not run in the golden source and must stay `--no-verify`-skippable);
  downstream propagation and any downstream `settings.json` edits (operator-gated, post-archive);
  retiring `test-gate.sh` (kept as the fallback).
