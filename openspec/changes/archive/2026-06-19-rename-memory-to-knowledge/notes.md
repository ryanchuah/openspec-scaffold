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

**1. Verdict:** READY FOR ARCHIVE. Self-review + deepseek-v4-pro verifier (READY, 0 defects) +
deepseek-v4-flash verifier (READY, 0 defects) all agree; simplicity gate `(none)`; security review not
triggered (no auth/credential/persisted-data/external-API surface — no live smoke applicable).

**2. Live output eyeballed (behavior, not counts):**
- Ran `status_lint.py` against the renamed scaffold tree → it located and validated `knowledge/STATUS.md`
  and `knowledge/decisions/INDEX.md` (printed OK for both), proving the split-component `"knowledge"` repath
  resolves the new paths.
- Ran `sync_scaffold.py --check-refs` against each repo → scanned the synced markdown and reported no
  dangling `knowledge/` citation, proving `_KNOWLEDGE_PATH_RE` matches the renamed citations.
- Ran `sync_scaffold.py --check` against extrends and psc-monitor → every scaffold-managed file reported
  IDENTICAL, proving the renamed scaffold files (scripts, both executor bodies, `knowledge/README.md`,
  `config.yaml` `rules:`) propagated correctly downstream.
- Path-anchored `grep memory/` in each repo surfaced ONLY the sanctioned folder-vs-feature exceptions —
  scaffold: the `~/.claude/.../memory/` harness path, the historical `ai-docs/→memory/` decisions essence,
  and the `agent-memory/` research URL; downstream: the harness path only.
- Re-ran the full scaffold suite (green) and `ruff` (clean); `openspec validate --type change --strict` valid.

**3. Defects found + who fixed:** No defects from the pro/flash verifier passes or my final self-review.
Two apply-time DEVIATIONS were caught and corrected by me (orchestrator), not the verifier: (a) the scaffold
Sonnet apply-executor hand-edited the two delta-covered MAIN specs to satisfy an over-reaching sweep →
reverted to `memory/` (delta-promoted at archive) and fixed §5.6 + acceptance #7; (b) both downstream Sonnet
subagents used a bulk `memory/`→`knowledge/` replace → I re-ran an over-rewrite scan (harness paths,
`*-memory/` URLs, historical essence) on each repo and confirmed no corruption. Executor for this session:
Sonnet subagents (operator override), not deepseek.

**4. As-built delta:** None beyond what this notes.md already records (the main-spec revert + the
sweep/acceptance correction).

**5. Forward-looking items (fold into project docs at archive):**
- **[operator follow-on — push/merge]** All three repos have COMMITTED but UNPUSHED branches
  `rename-memory-to-knowledge` (scaffold `b79b12d`, extrends `254266e`, psc-monitor `b37d425`). Pushing +
  merging each to its `main`/remote awaits explicit operator go-ahead (handoff §7). This is a pending
  operator-decision item → belongs in `knowledge/questions/INDEX.md` Active and/or STATUS "Immediate next
  action".
- **[session housekeeping — tied to the merge]** The Claude harness auto-memory (`MEMORY.md` +
  `project-restructure-knowledge.md` under `~/.claude/.../memory/`) still cites `memory/STATUS.md` etc.;
  once this rename is MERGED, those pointers should be repathed to `knowledge/` so future sessions don't
  chase a dead path. (Harness-native, not project state — deliberately so — but a real stale-pointer risk.)
- No new open questions about the rename itself; the previously-parked growth-trigger follow-on is unaffected.

**Still owned by archive (do NOT do here — reconciled by the delegated archive-executor):**
- Promote the two MODIFIED delta specs into the main specs `openspec/specs/{knowledge-organization,
  scaffold-sync-mechanism}/spec.md` (`memory/`→`knowledge/`).
- `knowledge/STATUS.md`: new change section (+ Immediate next action = the push/merge gate above).
- `knowledge/decisions/INDEX.md`: append the `rename-memory-to-knowledge` registry entry; consider whether
  to annotate the historical `restructure-project-knowledge` essence line re: the subsequent rename.
- `knowledge/questions/INDEX.md`: add the push/merge operator item (Active).
- Cleanup: discard the gitignored scaffold scratch `tmp_rename-knowledge_handoff.md` post-archive.

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
