# Outstanding-work-collector follow-ons

Parked follow-ons from the outstanding-work-collector change (archived
`openspec/changes/archive/2026-07-09-outstanding-work-collector/`). None are blocking;
all are deferred or monitor-only.

## plans/ gather scope: keep recursive, align spec+lint

The as-built gather uses `plans_dir.rglob("*.md")` (recursive), while the written spec
(design D6, tasks §1.3) and `_check_closed_unpruned` plan scan both say "top-level
`plans/*.md`" (`glob`, non-recursive). Operator decision (2026-07-09): **keep the recursive
gather**. This leaves a follow-on: update the spec and the closed-unpruned scan to match.
Handoff details at `plans/plans-scope-alignment.md`.

## `<!-- lint:dup-ok -->` placement is non-obvious

To suppress a legitimate duplicate, the marker must fall *inside the still-matching window* —
in practice at an identical position inside the block in *all* copies (otherwise it either
sits outside the reported range or fragments the block below the 8-line floor for the wrong
reason). Documented + tested, flag-only. Worth a one-line usage note in the
`knowledge_lint`/skill docs if a real dup-keep case ever arises.

## Config-load robustness asymmetry

`outstanding.py:main` guards `tomllib.load` against a malformed `checks.toml` (graceful
defaults); `knowledge_lint._load_knowledge_lint_config` and `_check_untriaged_age` call
`tomllib.load` without a guard, so a malformed `checks.toml` would raise in the linter
rather than degrade. Only triggers on an already-broken config; align if the linter's
other config reads are hardened later.

## Delegate arm reports `count: 0`

The `_run_delegate` `outstanding` arm returns a hardcoded `count: 0`; facts never gate and
the real counts live in the `.md`/`.json`, but the engine report line is inaccurate.
Consider returning open-work/untriaged count for an honest report line.

## In-code TODO source is a deliberate no-op

`_enumerate_todo_code` returns `[]` by design (design Non-Goal: in-code TODO scanning is
optional/lowest-priority). Recorded so a future reader does not mistake the empty function
for an unfinished one; revisit only if TODO markers become material in these repos.
