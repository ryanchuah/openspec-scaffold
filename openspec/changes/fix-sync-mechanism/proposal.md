## Why

Four shipped scaffold changes sit inert in the downstream repos (extrends, psc-monitor) because there
is no mechanism to propagate the golden source outward. A prior plan (`scaffold-sync`) designed one, but
a principal review found two blocking runtime bugs and one over-engineered subsystem, so it must not be
applied as written:

- The pre-commit guard exits `1`, but Claude Code `PreToolUse` only **blocks** on exit `2` — so the guard
  is a silent no-op.
- The AGENTS.md "DO NOT EDIT" header is re-inserted on every sync (the title region is read back out of
  the target), so the **second** sync writes a second header line and the file drifts. Because the whole
  premise is "re-run the sync to propagate each future change," a mechanism that corrupts on the second
  run cannot be used at all.

This change builds the sync mechanism correctly and minimally, so that a later one-time propagation (W6)
has a tool it can trust. It is scaffold-only; it propagates nothing.

## What Changes

- **NEW** `scripts/sync_scaffold.py` — copies every manifest-listed file byte-identical from scaffold to a
  target repo; handles `AGENTS.md` via span-replace that preserves each repo's `## Project context` and
  any tail (psc-monitor's `# Project reference`); a `--check` mode reports IDENTICAL / DIFFERS / MISSING
  and exits **1** on drift (a diagnostic CLI, not a blocking hook).
- **NEW** `scripts/scaffold_manifest.txt` — the authoritative, self-listed inventory of scaffold-managed
  files; excludes per-repo and volatile state.
- **NEW** `scripts/scaffold_check.py` — the `PreToolUse` hook helper that blocks a Claude commit touching
  a scaffold-managed file (detected by intersecting the manifest with `git diff --cached --name-only`) and
  directs the editor to change scaffold instead; **exits `2`** so it actually blocks.
- **NEW** `scripts/test_sync_scaffold.py` — unit tests for the span-replace algorithm, sync idempotency,
  per-repo section/tail preservation, and the abort guards.
- **REMOVED (vs the prior `scaffold-sync` plan)** the "DO NOT EDIT" header subsystem in its entirety: no
  header is injected into synced files, `--check` collapses to a plain byte compare for regular files, and
  the single human-facing "scaffold-managed — edit upstream" note lives once in `AGENTS.md` rather than as
  a per-file banner. This removal is what eliminates the AGENTS.md non-idempotency bug.
- The guard's coverage limit is **documented, not engineered around**: it intercepts only commits Claude
  makes through its Bash tool; operator-terminal and opencode/deepseek executor commits bypass it, and
  `git commit --no-verify` is the sanctioned escape for deliberate scaffold-managed edits.

## Capabilities

### New Capabilities
- `scaffold-sync-mechanism`: the tooling and guards that keep shared workflow files byte-identical between
  the golden source (openspec-scaffold) and downstream repos — the sync script, the self-managed manifest,
  the `--check` drift report, and the commit-time guard.

### Modified Capabilities
<!-- None. scaffold-sync-mechanism was proposed but never archived, so there is no existing spec to modify. -->

## Impact

- **Scaffold repo only.** Adds four files under `scripts/`; touches no app code and no downstream repo.
- **No propagation.** Wiring `scaffold_check.py` into downstream `.claude/settings.json` and running the
  sync against extrends/psc-monitor is the one-time snapshot in **W6**, out of scope here.
- **Depends on W0.** The exit-`2` blocking convention this guard relies on was live-verified in W0
  (commit-test-gate hook fires and exit 2 blocks); this change reuses that mechanism.
- **Supersedes** the frozen `openspec/changes/scaffold-sync` plan, which stays on disk as source material
  only until W1 + W6 land.
