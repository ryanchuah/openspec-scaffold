# Commit-test-gate is bypassable — the `if: Bash(git commit*)` matcher is prefix-anchored

**Status:** monitored todo, not urgent. Surfaced 2026-07-16 from a concrete psc-monitor incident.

## The problem

The commit-test-gate is wired as a Claude Code **PreToolUse hook** in `.claude/settings.json`:

```json
{ "matcher": "Bash", "hooks": [
  { "type": "command", "if": "Bash(git commit*)",
    "command": "\"$CLAUDE_PROJECT_DIR/scripts/test-gate.sh\"" } ] }
```

The `if: "Bash(git commit*)"` condition is a **prefix-anchored glob** — it only fires when the tool
command *starts with* the literal string `git commit`. Any commit invocation that does not begin
with those exact tokens silently **skips the gate entirely**:

- `cd /repo && git commit -m …`   (starts with `cd`)
- `git -C /repo commit -m …`      (starts with `git -C`)
- `env FOO= git commit -m …`      (starts with `env`)
- a `!`-bang command or a commit run in the operator's own terminal — neither routes through the
  Bash-tool PreToolUse hook at all.

The irony: `scripts/test-gate.sh` **already** has robust internal command-detection that strips
leading env-var assignments and handles `git -C`/`-c` global options — but that logic only runs
*if the hook fires*, and the `if` condition prevents it from firing for exactly those forms. The
gate's own hardening is dead code behind a matcher that never lets it run.

Note `git commit --no-verify` does **not** bypass this hook (the harness hook is external to git),
so the exposure is specifically the *prefix-evasion* forms above, not an explicit opt-out.

## Concrete evidence (why this is not hypothetical)

psc-monitor commit `0e5a823` (2026-07-16) committed a tracked handoff-named file under `plans/` even though
`knowledge_lint` Check 7 flags any non-git-ignored `*handoff*`-named file and
`test_knowledge_lint_live_tree_clean` fails deterministically on it. The gate command
(`scripts/test-cmd` → full `pytest`) *would* have returned exit 2 and blocked a normal Bash-tool
`git commit`. The commit reached HEAD anyway ⟹ it went through one of the prefix-evasion / non-hook
paths above. So the gate is demonstrably not a hard guarantee.

## Cross-agent gap (the stronger argument)

PreToolUse hooks are **Claude-Code-only**. OpenCode/DeepSeek agents — which this scaffold explicitly
supports (AGENTS.md "Cross-agent compatibility") — never run this gate at all. So the *only*
enforced pre-commit check today is Claude-side, and even there it is prefix-evadable.

## Recommended direction — a git-native `pre-commit` hook via `core.hooksPath`

Move the gate (or add a second enforcement layer) to a **git-native `pre-commit` hook** that git
itself invokes on every `git commit`, however the command is spelled (compound, `-C`, env-prefixed,
bang, operator terminal). Make it clone-safe and tracked by committing the hook under a tracked dir
(e.g. `scripts/githooks/pre-commit` <!-- lint:planned -->) and setting `git config core.hooksPath scripts/githooks` in the
repo-setup step (`core.hooksPath` is the clone-safe way — raw `.git/hooks/` is not tracked and not
copied on clone). The hook just execs the existing `scripts/check.sh`, so there is a single
definition of green.

Benefits:
- Closes the prefix-evasion gap (git fires the hook regardless of command spelling).
- **Covers non-Claude agents** (git runs it no matter which harness issued the commit) — the current
  PreToolUse hook does not.
- Keeps the Claude PreToolUse hook if desired (belt-and-braces), but it is no longer the sole guard.

Caveats to weigh:
- `git commit --no-verify` skips git-native hooks — but that is an explicit, visible opt-out, far
  better than today's *silent* matcher evasion.
- `core.hooksPath` must be set once per clone (a setup-script/`install.sh` step) — worth a line in
  the scaffold's onboarding.
- Decide whether the hook is scaffold-managed (byte-identical downstream) like `test-gate.sh`.

## Disposition
Open todo. When picked up: prototype the `core.hooksPath` pre-commit in the scaffold, decide
scaffold-managed vs per-repo, and propagate. Ties to the cross-agent-compatibility invariant.
