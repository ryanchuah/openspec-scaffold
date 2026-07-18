# HANDOFF — curated next-session work queue (written 2026-07-18)

> Not a context-exhaustion dump. The `graduate-sast-scanners` session completed cleanly through
> archive; this is a deliberately-curated queue of follow-ons the operator asked to hand forward.
> Absorb it, do the work it describes (starting with Priority 1), and **delete this file** once the
> items are either done or re-parked. Its normal state is absent.

---

## Priority 1 — Commit-lint (commit-test-gate) is bypassable; explore a git-native pre-commit hook

**Operator ask (2026-07-18):** "Some agents manage to bypass the commit lint check by accident — I
suspect `cd dir && git commit …` which doesn't trigger the lint. Explore this — e.g. should we
install pre-commit hooks?"

**This is CONFIRMED, not hypothetical, and already analyzed** — see
`knowledge/questions/commit-gate-bypass.md` (full write-up). Summary:
- The gate is a Claude Code **PreToolUse hook** in `.claude/settings.json` with condition
  `if: "Bash(git commit*)"` — a **prefix-anchored glob**. It only fires when the tool command
  *starts with* `git commit`. These forms silently skip it:
  - `cd /repo && git commit …` (starts with `cd`) ← exactly the operator's suspicion
  - `git -C /repo commit …` (starts with `git -C`)
  - `env FOO= git commit …` (starts with `env`)
  - any `!`-bang command, operator-terminal commit, **or any non-Claude (OpenCode/DeepSeek) agent** —
    PreToolUse hooks are Claude-only, so the cross-agent case never runs the gate at all.
- Irony: `scripts/test-gate.sh` already strips env-prefixes and handles `git -C`/`-c` internally —
  but that hardening is dead code behind a matcher that never lets it fire for those spellings.
- `git commit --no-verify` does NOT bypass this hook (it's external to git); the exposure is the
  *silent prefix-evasion* forms, not an explicit opt-out.
- Concrete evidence: psc-monitor commit `0e5a823` (2026-07-16) landed a file the live-tree
  `knowledge_lint` gate would have blocked ⟹ it reached HEAD via one of the evasion paths.

**Recommended direction (from the parked question, ready to prototype):** add a **git-native
`pre-commit` hook** via `core.hooksPath` that execs the existing `scripts/check.sh` (single
definition of green). git fires it on every `git commit` regardless of spelling, AND it covers
non-Claude agents — closing both gaps. Keep the Claude PreToolUse hook as belt-and-braces if desired.

**Task for next session (scope: likely SMALL–MEDIUM scaffold change, runs the lifecycle):**
1. Prototype `scripts/githooks/pre-commit` (execs `check.sh`) + a repo-setup step that runs
   `git config core.hooksPath scripts/githooks` (the clone-safe way — raw `.git/hooks/` is not
   tracked/copied on clone).
2. Decide **scaffold-managed vs per-repo** (like `test-gate.sh` is byte-identical downstream) and add
   to `scripts/scaffold_manifest.txt` if managed.
3. Weigh caveats: `--no-verify` is a visible opt-out (acceptable, far better than silent evasion);
   `core.hooksPath` must be set once per clone (onboarding line); interaction with the existing
   Claude PreToolUse hook.
4. Propagate (operator-gated) after archive.
   This ties to the AGENTS.md cross-agent-compatibility invariant — that's the stronger argument for
   doing it. **Not blocked by anything.**

---

## Priority 2 — `_custom_checks` `family=` fix (the one actionable graduate-sast-scanners follow-on)

See `knowledge/questions/custom-checks-family-fix.md`. Let a `[checks.custom.<name>]` entry in
`checks.toml` register a **fact**-family (preflight-exempt, graceful-degrade) check by honoring
`spec.get("family", "check")` — today `_custom_checks` (in `scripts/checks.py`) hardcodes
`family="check"`. This unblocks downstream repos registering app-specific fact snapshots (e.g.
psc-monitor's route-authz) without standalone scripts. Clean SMALL change. **Not blocked.**

---

## The other 3 graduate-sast-scanners follow-ons — event-triggered, NOT actionable now

None are blocked; each is *waiting for a trigger event* — do nothing until it happens:
- **`semgrep-needs-config`** (`knowledge/questions/semgrep-needs-config.md`) — monitor. Add a
  preflight WARNING ("semgrep enabled but no `--config` in args") only **if operator confusion
  recurs** during downstream propagation.
- **`sast-auto-detection-trigger`** (`knowledge/questions/sast-auto-detection-trigger.md`) — deferred
  by design. Revisit only **when a downstream repo asks** to auto-enable; any trigger must preserve
  sync-safety (nothing auto-enables on a downstream repo the moment sync lands).
- **`sast-tool-json-version-sensitivity`** (`knowledge/questions/sast-tool-json-version-sensitivity.md`)
  — monitor. Update parser key-paths only **if a bandit/semgrep major bump** produces empty/nonsensical
  findings. Parsers validated at bandit 1.9.4 / semgrep 1.170.0; version-recorded-not-gated so a bump
  never INFRA-FAILs.

---

## Also outstanding (operator-gated — not for the agent to run unprompted)

Downstream propagation of **two** shipped-but-unpropagated changes is pending in
`knowledge/reference/pending-downstream-propagation.md`: `graduate-sast-scanners` (scaffold files
byte-identical; `security-scanners.md` needs a manual per-repo sweep) and `roll-decisions-index`
(extrends needs its own pre-roll first). Push to remote is also operator-gated. Do these only on
explicit operator instruction (via the `propagate-scaffold` skill).
