# notes — rename-memory-to-knowledge

**Tier:** MEDIUM (operator-set). Near-pure rename: the tracked project-knowledge folder `memory/` →
`knowledge/` across all three repos (scaffold + extrends + psc-monitor), plus the spec, the sync/lint
mechanism, and every live citation. No content transform, no knowledge rescue. Motive: the tracked
`memory/` folder collides with Claude Code's harness-native `~/.claude/.../memory/`, and the name
contradicts the `all-state-in-tracked-files` / `no-lifecycle-hooks` decisions and the project's own
"knowledge" vocabulary (`knowledge-organization`, "the knowledge taxonomy").

Delta specs (both `MODIFIED`, path strings only — no behavior change):
`knowledge-organization` (4 requirements) and `scaffold-sync-mechanism` (1 requirement,
`manifest-declares-shared-files`). The lone `commit-test-gate` reference is a non-delta main-spec
hand-edit (task 4.6).

## Acceptance criteria (all must hold before archive)

1. **No `memory/` directory** in any of the three repos; `knowledge/` holds the full layout in each
   (`README.md`, `STATUS.md`, `decisions/INDEX.md`, `questions/` + per-item, `lessons.md`, `reference/`,
   `research/` + INDEX, `roadmap.md`).
2. **Scaffold suite green:** `pytest` (incl. `test_sync_scaffold.py`, `test_status_lint.py`,
   `test_executor_body_agreement.py`) and `ruff check` clean.
3. **`openspec validate rename-memory-to-knowledge --type change --strict`** passes.
4. **Scaffold self-gates exit 0:** `status_lint.py` (against `knowledge/STATUS.md` +
   `knowledge/decisions/INDEX.md`) and `sync_scaffold.py --check-refs <scaffold>` (no dangling
   `knowledge/` citation in the synced files).
5. **Downstream gates exit 0** for extrends AND psc-monitor, each run from the scaffold checkout:
   `sync_scaffold.py --check <repo>`, `sync_scaffold.py --check-refs <repo>`, `status_lint.py <repo>`.
6. **Both `archive-executor.md` bodies byte-identical** (`test_executor_body_agreement.py` proves it);
   `config.yaml` `rules:` still the final top-level block; `AGENTS.md` span anchors intact in all repos;
   psc-monitor's `AGENTS.md` `# Project reference` tail preserved.
7. **Folder-vs-feature preserved:** run from each repo root AFTER all that repo's renames + syncs are
   complete (a mid-rename grep yields false positives), `grep -rn 'memory/' <repo>` (excluding `/.git/`,
   `openspec/changes/` — frozen archive + this change's own artifacts — and, in the scaffold, the two
   delta-covered MAIN specs `openspec/specs/{knowledge-organization,scaffold-sync-mechanism}/spec.md`, which
   retain `memory/` until the archive promotes the `MODIFIED` deltas) returns hits ONLY for the three
   sanctioned exceptions — the
   `~/.claude/.../memory/` harness path in `AGENTS.md`, the historical `restructure-project-knowledge`
   essence in `decisions/INDEX.md`, and the `agent-memory/` URL in the research file — and nothing in
   live mechanism, specs, skills, or state files.
8. **History preserved:** the rename used `git mv` (not delete+create) in every repo.

## Verify results

_(filled during the verify phase — self-review + multi-model verifier verdicts go here.)_

## Process note (this session only)

- **Apply executor override (operator-set, this session):** delegate the scaffold apply (tasks §1–§5) to a
  Claude **`apply-executor` subagent on Sonnet** (via the Agent tool), NOT deepseek-v4-flash via
  `opencode run`. This is the sanctioned fallback path, invoked deliberately. §6/§7 (extrends + psc-monitor)
  remain primary cross-repo work. Gates/verify unchanged. The propose-phase reviewer stayed on
  deepseek-v4-pro as designed.

## Decisions / discoveries

- **Apply (§1–§5) — main-spec hand-edit reverted (orchestrator correction).** The Sonnet apply-executor,
  to satisfy the original §5.6 sweep, hand-edited the two delta-covered MAIN specs
  (`openspec/specs/knowledge-organization/spec.md`, `scaffold-sync-mechanism/spec.md`) `memory/`→`knowledge/`.
  That contradicts the OpenSpec convention (prior change task 6.2: *"do not hand-edit the main spec — archive
  syncs the delta"*). Verified every `memory/` ref in both committed main specs falls inside a requirement the
  deltas MODIFY (knowledge-organization: 4 requirements; scaffold-sync-mechanism: `manifest-declares-shared-files`),
  so the archive promotion fully covers them. Reverted both main specs to their committed `memory/` state via
  `git checkout HEAD --`; the deltas remain the single source and promote at archive (proven flow from the
  prior change). Kept the `commit-test-gate` single-ref hand-edit (task 4.6 — non-delta, sanctioned). Fixed
  §5.6 + acceptance #7 to exclude the two delta-covered main specs from the live `memory/` sweep.
- **Apply (§6–§7) — downstream migrations (parallel Sonnet subagents, orchestrator-verified).** extrends and
  psc-monitor migrated concurrently on fresh `rename-memory-to-knowledge` branches: `git mv memory knowledge`
  → `sync_scaffold.py` from the scaffold → per-repo citation repath → 3 gates. Both subagents used a bulk
  `memory/`→`knowledge/` replace on their knowledge trees; I independently re-ran every gate AND an
  over-rewrite scan (corrupted `~/.claude/.../knowledge/` harness paths, corrupted `*-memory/` URLs,
  `ai-docs/→knowledge/` historical-essence corruption). Both clean — neither downstream repo carries a (b)
  URL or (c) historical-essence exception, so the only sanctioned remnant in each is the AGENTS.md:58 harness
  path (a). Gates per repo: `--check` 0, `--check-refs` 0, `status_lint` 0; `git mv` preserved history;
  psc-monitor's `# Project reference` tail + span anchors intact. Committed: extrends `254266e`,
  psc-monitor `b37d425` (both `--no-verify` — intentional scaffold-managed-file commits, per handoff §3).
  NOT pushed/merged — awaiting operator go-ahead.
