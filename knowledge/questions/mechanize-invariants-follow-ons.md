# mechanize-invariants follow-ons

## Hook-wiring warning depth (monitored limitation)

The `sync_scaffold.py` hook-wiring warning is substring-based and advisory; a `settings.json`
containing `scaffold_check.py` under the wrong hook event (or in a comment) would silently
count as wired. Deepen to JSON `hooks.PreToolUse` parsing only if a real false-negative
appears.

## `sync_scaffold._read_manifest` root-hardcoded

`sync_scaffold._read_manifest` is hardcoded to the real scaffold root, forcing
`scaffold_lint.py` to keep its own manifest parse. Small follow-on: parameterize it
(`_read_manifest(path)`) and dedupe.

## Manifest deletion/tombstone gap — RESOLVED (2026-07-03)

Deleting a manifest-listed file upstream orphans it downstream silently — `manifest-completeness`
only checks files that exist. RESOLVED by a *mechanism*, not the anticipated manual per-repo
sweep: the `scaffold_manifest_removed.txt` tombstone list (consumed by `sync_scaffold.py`)
deterministically deletes removed files downstream. Shipped under clarify-audit-tooling-surface
and lint-knowledge-tombstone (see `knowledge/decisions/INDEX.md`).

## Downstream applicability of scaffold_lint

`scaffold_lint.py` is deliberately golden-source-only today. Consider whether a subset of
checks (dangling-refs, budget-agreement) is worth syncing downstream later.

## `knowledge_lint.py` DEFAULT_RETIRED_PATHS personal path

The `/home/me/` entry has been removed from `DEFAULT_RETIRED_PATHS` (prune-knowledge task 1.2,
2026-07-03) — RESOLVED.
