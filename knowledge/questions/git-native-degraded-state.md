# Silent degraded git-native state — monitored risk

**Status:** monitored follow-on, low priority. Surfaced 2026-07-18 during `git-native-commit-gate`
(`openspec/changes/archive/2026-07-18-git-native-commit-gate/`, design.md Risks).

## The risk

The git-native commit-test-gate layer depends on two pieces of `.git/config` / filesystem state that
are **not tracked or verified on every commit**:
- `core.hooksPath` is set to `scripts/githooks` (repo-local `git config`, not cloned/synced).
- `scripts/githooks/pre-commit` exists and is executable.

If `core.hooksPath` is set but the hook file is later **deleted** or **loses its executable bit**
(e.g. a careless `chmod`, a broken sync step, an editor that strips the exec bit on save), git-native
silently stops firing — with **no error, no warning**. The commit-test gate does not go fully dark
for Claude sessions (the Claude `PreToolUse` `scripts/test-gate.sh` fail-safe defer branch requires
positively confirming the hook is present+executable before deferring, so it re-gates itself when the
hook is missing) — but a **non-Claude commit** (OpenCode/DeepSeek/operator terminal) would be silently
ungated, with no signal to anyone that the primary layer degraded.

## Recommended direction

A future preflight/`facts.py` warning — e.g. "core.hooksPath is set to scripts/githooks but the
pre-commit hook is missing or not executable" — could surface this degraded state proactively rather
than relying on someone noticing an ungated bad commit after the fact.

## Disposition

Parked, monitored. Not built as part of `git-native-commit-gate` (accepted risk, mitigated by the
Claude-side fail-safe fallback). Revisit if a real degraded-state incident occurs, or opportunistically
alongside other `facts.py`/preflight work.
