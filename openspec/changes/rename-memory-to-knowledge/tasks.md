**Binding invariants (hold for every task below):**
- **Folder-vs-feature.** Rewrite the *tracked project-knowledge folder* `memory/` → `knowledge/`. Do
  NOT rewrite text about Claude's *harness-native* memory. Three concrete landmines a blind
  `sed 's|memory/|knowledge/|g'` would corrupt — leave each verbatim:
  (a) `AGENTS.md` — the literal harness path `~/.claude/.../memory/` and its `MEMORY.md` index (in the
  "Claude Code harness memory — deliberately not used" section);
  (b) `memory/decisions/INDEX.md` — the historical essence line for `restructure-project-knowledge`
  (`ai-docs/→memory/`, `taxonomy synced via memory/README.md`) describes a *past* change → leave it
  (git mv only, no content edit; the archive-executor reconciles decisions);
  (c) `memory/research/research-industry-standards-2026-06/D-knowledge-memory-verification.md` — the
  `letta.com/blog/agent-memory/` URL is a citation, not a folder path → leave it.
- **Do NOT touch any `openspec/changes/archive/**`** in any repo — frozen history; its `memory/` is correct.
- **Both `archive-executor.md` bodies stay byte-identical** (`.claude/agents/` + `.opencode/agents/`) —
  edit both in the same pass; `scripts/test_executor_body_agreement.py` enforces it.
- **`openspec/config.yaml` keeps `rules:` as the final top-level block** (sync span is `^rules:`→EOF).
- **`AGENTS.md` span anchors preserved verbatim** (`> **MANDATORY`, `## Roles`, `## After reading this file`).
- **`sync_scaffold.py` is ALWAYS run FROM the scaffold checkout**, targeting the downstream repo path —
  never from inside the downstream repo.
- **Scaffold first** (§1–§5), then the downstream repos (§6, §7) — sync copies the renamed scaffold-managed
  files (incl. `knowledge/README.md`, the repathed scripts, both executor bodies, skills, `config.yaml`
  `rules:`), so the scaffold rename must be complete and green before any downstream sync.

## 1. Scaffold — move the knowledge tree

- [ ] 1.1 `git mv memory/ knowledge/` (preserves history for all files under it). Confirm the full layout
  lands at `knowledge/`: `README.md`, `STATUS.md`, `decisions/INDEX.md`, `questions/` (INDEX + per-item),
  `lessons.md`, `reference/`, `research/` (+ INDEX), `roadmap.md`. Confirm no `memory/` directory remains.

## 2. Scaffold — rewrite live `knowledge/` citations inside the moved tree

- [ ] 2.1 Rewrite internal folder citations `memory/<path>` → `knowledge/<path>` in the moved knowledge
  files that carry them — `knowledge/STATUS.md`, `knowledge/questions/INDEX.md`, `knowledge/research/INDEX.md`,
  `knowledge/README.md`, `knowledge/roadmap.md`, `knowledge/lessons.md`,
  `knowledge/questions/restructure-growth-trigger.md` — so no moved file points back at a dead `memory/` path.
- [ ] 2.2 `knowledge/decisions/INDEX.md`: make NO content change (its only `memory/` tokens are the
  historical `restructure-project-knowledge` essence — invariant (b)). The git mv in 1.1 is the only change.
- [ ] 2.3 `knowledge/research/research-industry-standards-2026-06/D-knowledge-memory-verification.md`:
  make NO change — its only `memory/` is the `agent-memory/` URL (invariant (c)).

## 3. Scaffold — sync mechanism (scripts + manifest)

- [ ] 3.1 `scripts/scaffold_manifest.txt`: change the `memory/README.md` entry → `knowledge/README.md`
  (update the section comment too if it names the path).
- [ ] 3.2 `scripts/sync_scaffold.py`: rewrite every `memory/` literal → `knowledge/` and rename the identifier
  `_AIDOC_PATH_RE` → `_KNOWLEDGE_PATH_RE` at BOTH its definition and its use. Specifically:
  `_REF_SCAN_EXCLUDE` (`memory/research/` → `knowledge/research/`); `_AIDOC_PATH_RE = re.compile(r"memory/[\w./-]+\.md")`
  → `_KNOWLEDGE_PATH_RE = re.compile(r"knowledge/[\w./-]+\.md")`; the `.finditer(text)` call site;
  `_synced_files()` filter `line.startswith("memory/")` → `knowledge/`; the section-citation guard
  `cited_file.startswith("memory/")` → `knowledge/`; and all docstring/comment `memory/` mentions.
- [ ] 3.3 `scripts/status_lint.py`: rewrite every `memory/STATUS.md` and `memory/decisions/INDEX.md`
  literal → `knowledge/...` (docstrings, the path constants it lints, and all message strings). NOTE: the
  path constants are built from a SPLIT `"memory"` component — `repo_root / "memory" / "STATUS.md"` and
  `repo_root / "memory" / "decisions" / "INDEX.md"` (both appear twice). The `"memory"` string component
  must become `"knowledge"`; a blind `memory/STATUS.md`→`knowledge/STATUS.md` replace would miss these.

## 4. Scaffold — rules / instruction surface

- [ ] 4.1 `.claude/agents/archive-executor.md` AND `.opencode/agents/archive-executor.md`: rewrite every
  `memory/<path>` → `knowledge/<path>` in BOTH bodies in the same pass, keeping the two bodies byte-identical
  (only the sanctioned frontmatter/intro clause may differ).
- [ ] 4.2 `.claude/skills/openspec-archive-change/SKILL.md` and `.claude/skills/openspec-verify-change/SKILL.md`:
  rewrite `memory/<path>` → `knowledge/<path>`.
- [ ] 4.3 `AGENTS.md`: rewrite the tracked-folder `memory/` → `knowledge/` throughout (the mandatory-read
  block, the "where everything lives" pointers to `knowledge/README.md`, the State/write-discipline rules,
  the Roles archive-executor targets). PRESERVE invariant (a): leave `~/.claude/.../memory/` and its
  `MEMORY.md` index in the "Claude Code harness memory" section untouched. Keep the three span anchors verbatim.
- [ ] 4.4 `openspec/config.yaml`: rewrite the `memory/STATUS.md` / `memory/decisions/INDEX.md` /
  `memory/questions/INDEX.md` references → `knowledge/...`. Keep `rules:` as the final top-level block.
- [ ] 4.5 `README.md` and `tests/skill-enumeration-smoke/README.md`: rewrite `memory/<path>` → `knowledge/<path>`.
- [ ] 4.6 `openspec/specs/commit-test-gate/spec.md`: hand-edit the single `memory/decisions/INDEX.md`
  reference → `knowledge/decisions/INDEX.md` (this lone ref is a non-delta main-spec edit, per the
  prior change's precedent; the two `MODIFIED` delta specs in this change carry the rest).

## 5. Scaffold — tests + green gate

- [ ] 5.1 `scripts/test_sync_scaffold.py`: repath every `memory/` fixture path and expectation → `knowledge/`
  (incl. the manifest/`README.md` fixtures and the ref-checker fixtures). The test imports from
  `sync_scaffold`; any reference to `_AIDOC_PATH_RE` must become `_KNOWLEDGE_PATH_RE` to match the identifier
  renamed in 3.2 (the new name exists only after that task lands). Also rename the test method
  `test_memory_section_citation_checks_file_existence_only` → `test_knowledge_section_citation_checks_file_existence_only`
  for post-rename consistency.
- [ ] 5.2 `scripts/test_status_lint.py`: repath the `memory/STATUS.md` / `memory/decisions/INDEX.md`
  fixtures and expectations → `knowledge/...`. This includes the SPLIT `"memory"` path constructions in the
  `_make_repo()` helper (`repo / "memory"` and `repo / "memory" / "decisions"`) — the `"memory"` component
  must become `"knowledge"`, same gotcha as 3.3.
- [ ] 5.3 Run the full scaffold suite green: `pytest` (incl. `test_sync_scaffold.py`, `test_status_lint.py`,
  `test_executor_body_agreement.py`) and `ruff check`. Resolve failures until clean.
- [ ] 5.4 Run `openspec validate rename-memory-to-knowledge --type change --strict` → valid.
- [ ] 5.5 Run `python3 scripts/status_lint.py` against the scaffold (now `knowledge/STATUS.md` +
  `knowledge/decisions/INDEX.md`) → exit 0, and `python3 scripts/sync_scaffold.py --check-refs
  /home/pang/Projects/openspec-scaffold` → exit 0 (no dangling `knowledge/` citation in the synced files).
- [ ] 5.6 Final sweep: `grep -rn 'memory/' .` (excluding `/.git/` and `openspec/changes/archive/`) returns
  hits ONLY for the three sanctioned folder-vs-feature exceptions (invariant (a)/(b)/(c)) — nothing in live
  mechanism, specs, skills, or state files.

## 6. extrends migration (primary — cross-repo, run from the scaffold checkout; NOT delegated to the executor)

*Prerequisite: §1–§5 green. Work on a fresh branch in `/home/pang/Projects/extrends`. Never touch its
`openspec/changes/archive/**`.*

- [ ] 6.1 In extrends, `git mv memory/ knowledge/` (its per-repo state tree: `STATUS.md`, `decisions/`,
  `questions/`, `lessons.md`, `roadmap.md`, `reference/`, `research/`, and the synced `README.md`).
- [ ] 6.2 Rewrite extrends' live `memory/<path>` → `knowledge/<path>` citations in its tracked files
  (the moved knowledge-tree internal citations, the `AGENTS.md` per-repo `## Project context` pointer to
  `knowledge/README.md`, and the `openspec/config.yaml` per-repo `context:` block if it cites the folder),
  EXCEPT its `openspec/changes/archive/**` and any harness-native-memory prose (invariant (a)–(c) apply here too).
- [ ] 6.3 From the scaffold checkout, run `python3 /home/pang/Projects/openspec-scaffold/scripts/sync_scaffold.py
  /home/pang/Projects/extrends` (brings `knowledge/README.md`, the repathed scripts + tests, both executor
  bodies, skills, `config.yaml` `rules:`, and `AGENTS.md` shared spans).
- [ ] 6.4 `git rm` any `memory/` sync-orphan left in extrends (defensive — the wholesale mv in 6.1 should
  leave none); confirm the `memory/` directory is gone.
- [ ] 6.5 Gate extrends — all exit 0, run from the scaffold checkout targeting extrends:
  `sync_scaffold.py --check /home/pang/Projects/extrends`, `sync_scaffold.py --check-refs
  /home/pang/Projects/extrends`, and `status_lint.py /home/pang/Projects/extrends`. Spot-check: no `memory/`
  dir; `knowledge/` holds the full layout; `AGENTS.md` links `knowledge/README.md`.

## 7. psc-monitor migration (primary — cross-repo, run from the scaffold checkout; NOT delegated to the executor)

*Prerequisite: §6 green. Work on a fresh branch in `/home/pang/Projects/psc-monitor`. Preserve its
`AGENTS.md` `# Project reference` tail appendix and the span anchors. Never touch its
`openspec/changes/archive/**`.*

- [ ] 7.1 In psc-monitor, `git mv memory/ knowledge/` (its per-repo state tree + the synced `README.md`).
- [ ] 7.2 Rewrite psc-monitor's live `memory/<path>` → `knowledge/<path>` citations in its tracked files
  (moved knowledge-tree internals, `AGENTS.md` `## Project context` pointer, `config.yaml` `context:` block),
  EXCEPT its `openspec/changes/archive/**` and harness-native-memory prose. Leave the `# Project reference`
  tail untouched unless it cites the folder path.
- [ ] 7.3 From the scaffold checkout, run `python3 /home/pang/Projects/openspec-scaffold/scripts/sync_scaffold.py
  /home/pang/Projects/psc-monitor`.
- [ ] 7.4 `git rm` any `memory/` sync-orphan left in psc-monitor (defensive); confirm `memory/` is gone.
- [ ] 7.5 Gate psc-monitor — all exit 0, run from the scaffold checkout targeting psc-monitor:
  `sync_scaffold.py --check /home/pang/Projects/psc-monitor`, `sync_scaffold.py --check-refs
  /home/pang/Projects/psc-monitor`, and `status_lint.py /home/pang/Projects/psc-monitor`. Spot-check: no
  `memory/` dir; `knowledge/` holds the full layout; `AGENTS.md` links `knowledge/README.md` and the
  `# Project reference` tail is intact.
