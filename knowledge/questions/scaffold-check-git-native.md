# scaffold_check.py — parallel prefix-evasion + Claude-only bypass class

**Status:** parked follow-on, low priority. Surfaced 2026-07-18 during `git-native-commit-gate`.

## The problem

`git-native-commit-gate` (shipped 2026-07-18, `openspec/changes/archive/2026-07-18-git-native-commit-gate/`)
closed the commit-test gate's prefix-evasion + cross-agent bypass class by adding a git-native
`pre-commit` hook. `scripts/scaffold_check.py` — the scaffold-managed-file guard, wired as its own
Claude Code `PreToolUse` hook — is a **structurally identical** bypass class: it is also a
prefix-anchored, Claude-only `PreToolUse` hook, so the same evasion spellings (`cd … && …`,
`git -C … …`, `env … …`) and the same cross-agent gap (OpenCode/DeepSeek never run it) apply to it too.

A prior note (`scripts/scaffold_check.py:16`, referenced in `git-native-commit-gate`'s design.md)
records that a git-native `core.hooksPath` hook was "considered and rejected for W1" for this guard
specifically — but that rejection predates the commit-test-gate's own git-native adoption and should
be revisited in that light.

## Why this is NOT a straightforward git-native port

Unlike the commit-test gate (which should always run), `scaffold_check.py`'s entire purpose is to
**catch accidental edits to scaffold-managed files** — so it must:
- **NOT run in the golden source** (this repo) — editing scaffold-managed files here is the point,
  not a mistake to catch.
- **Stay `--no-verify`-skippable** — an intentional scaffold-file edit needs an escape hatch.

A byte-identical git-native hook (the pattern `git-native-commit-gate` used) can't host this
conditional logic unconditionally without re-introducing per-repo drift or a golden-source detection
mechanism inside a hook that is supposed to be byte-identical everywhere.

## Disposition

Parked. When picked up: design how a git-native adaptation of `scaffold_check.py` could distinguish
golden source from downstream (e.g. a repo-identity marker file, or keeping it PreToolUse-only and
accepting the residual bypass class as a lower-severity risk than the commit-test gate's, since its
blast radius is scaffold-file drift, not shipping broken code). Not blocking any other work.
