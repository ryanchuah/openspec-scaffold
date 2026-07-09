## 1. `scripts/outstanding.py` — shared gather module

- [x] 1.1 Create `scripts/outstanding.py` (stdlib-only) with `main(argv) -> int` that gathers all
  configured sources and writes `output/facts/outstanding.md` (self-written) and returns/writes the
  JSON payload to the engine-provided `out_path` (`output/facts/outstanding.json`); every item carries
  `source:line` provenance; exit `0` always (never non-zero on source content).
- [x] 1.2 Implement source enumeration: `knowledge/questions/INDEX.md` Active+Parked in **both** list
  form (`^\s*[-*]\s+`, `^\s*\d+\.\s+`) and table-row form (`|`-delimited, non-header/non-`---`), scoped
  by the enclosing `## Active` / `## Parked` heading; non-archive `openspec/changes/*/tasks.md`
  unchecked `- [ ]`; `knowledge/roadmap.md` non-closed `## ` entries; in-code `TODO/FIXME/HACK/XXX`
  (in-code TODO scan is **optional / lowest-priority** per the design non-goal — may be skipped
  without failing any acceptance criterion).
- [x] 1.3 Implement point-only enumeration for prose sources: every `knowledge/questions/*.md`
  per-item file and every top-level `plans/*.md` (path + first heading + git tracked/`mtime`), never
  fabricating line-items; exclude `plans/archive/**` from the live list (D6).
- [x] 1.4 Implement malformed-source handling: a source that fails to parse yields an explicit
  `UNPARSEABLE — read manually: <path> (<reason>)` entry and does not abort the run (D2).
- [x] 1.5 Implement `extract_untriaged(root: Path, config: dict) -> list[dict]` returning
  `[{"id","file","age_days"}, ...]`: finding IDs matched by `finding_id_pattern` across `findings_globs`
  that appear **nowhere** under `knowledge/questions/` (scan `INDEX.md` + every `*.md` per-item file);
  `age_days` from the containing file's git last-commit date, falling back to filesystem `mtime` when
  git is unavailable.
- [x] 1.6 Render two snapshot buckets — **Open work (triaged)** and **Newly surfaced — untriaged (N;
  oldest <date>)** — and surface the active config plus a findings-files-scanned vs. IDs-matched count.
- [x] 1.7 Read config from `[facts.outstanding]` (`findings_globs` default
  `["knowledge/research/**/FINDINGS*.md"]`, `finding_id_pattern` permissive default) with graceful
  defaults when `checks.toml` is absent.

## 2. Wire the fact into the checks/facts engine

- [x] 2.1 Add the registry entry to `scripts/checks.py` `_REGISTRY`:
  `{"name": "outstanding", "tier": "snapshot", "kind": "delegate", "family": "fact"}`.
- [x] 2.2 Add an `if name == "outstanding":` arm to `_run_delegate` that invokes the
  `scripts/outstanding.py` logic and fills the engine-provided `out_path` (JSON), mirroring the
  `scope`/`index-coverage` arms.
- [x] 2.3 Add `"outstanding": True` to `_autodetect_defaults` (unconditional, no external dep — like
  `inventory`) so the all-facts run includes it.

## 3. `knowledge_lint.py` drift-detection extensions

- [x] 3.1 Add `_check_duplicate_blocks(...)`: flag ≥ 8 consecutive whitespace-normalized identical
  lines across 2+ files in the narrow set (markdown under `knowledge/`, top-level `*.md`, and
  `[knowledge_lint].duplicate_scan_dirs`); exclude `knowledge/research/` and `openspec/specs/`; a
  `<!-- lint:dup-ok -->` marker whose line falls inside a detected window suppresses that finding.
- [x] 3.2 Add `_check_closed_unpruned(...)`: flag a `knowledge/roadmap.md` `## ` entry or a top-level
  `plans/*.md` file whose heading/`**Priority:**`/`**Status:**` line carries a closed-token
  (`CLOSED`/`DONE`/`COMPLETE`/`✅`/`~~…~~`); `<!-- lint:keep -->` opts out.
- [x] 3.3 Add `_check_untriaged_age(...)`: import `outstanding.extract_untriaged` (no re-implementation)
  and flag any untriaged finding older than `[knowledge_lint].untriaged_max_age_days` (default 14).
- [x] 3.4 Wire `_check_duplicate_blocks`, `_check_closed_unpruned`, `_check_untriaged_age` into
  `collect_findings()`.

## 4. Convention, skill, and propagation surface

- [x] 4.1 Establish the `plans/archive/` convention: create `plans/archive/` (with a `.gitkeep`) and a
  brief `plans/README.md` stating top-level = live, `plans/archive/` = shipped/closed (do NOT move
  existing plan files — that is out-of-scope hygiene).
- [x] 4.2 Create `.claude/skills/outstanding-work-review/SKILL.md` (agent-neutral, pull-only): runs
  `facts.py --check outstanding`, reads `output/facts/outstanding.json`, and guides the orchestrator
  through judging into `knowledge/questions/` + `roadmap.md` (durable reconciliation stays at archive).
- [x] 4.3 Add `scripts/outstanding.py`, `scripts/test_outstanding.py`, and
  `.claude/skills/outstanding-work-review/SKILL.md` to `scripts/scaffold_manifest.txt`.

## 5. Tests

- [x] 5.1 `scripts/test_outstanding.py`: clean run writes both `.md`+`.json` and exits 0 **and each
  emitted item carries `source:line` provenance**; malformed source → `UNPARSEABLE` entry and still
  exit 0; Active items extracted from **both** a bullet fixture and a table fixture; a prose-only
  per-item/plan file is enumerated point-only (no fabricated items).
- [x] 5.2 `scripts/test_outstanding.py`: a finding ID absent from `questions/` lands in the untriaged
  bucket; adding a `questions/` reference moves it to triaged on re-run; `plans/archive/**` excluded
  while top-level `plans/*.md` listed; absent-config defaults run cleanly; a per-repo
  `finding_id_pattern` is honored with a visible scanned-vs-matched count.
- [x] 5.3 Extend `scripts/test_knowledge_lint.py`: duplicate-block flagged (≥8 lines) and NOT flagged
  for <8 lines / `knowledge/research/` / `openspec/specs/` / `<!-- lint:dup-ok -->`; closed-unpruned
  flagged for roadmap + top-level plan and NOT flagged under `<!-- lint:keep -->`; untriaged-age
  flagged past the window, not within, and uses `mtime` when git is absent.
- [x] 5.4 In `scripts/test_checks.py`: assert `outstanding` is registered in `_REGISTRY` as
  `kind="delegate"`, `family="fact"`. In `scripts/test_facts.py`: assert it runs via
  `facts.py --check outstanding` and is enabled by default in the all-facts run.

## 6. Reconcile this repo's own tree, then green gate

- [x] 6.1 Make the three new `knowledge_lint` checks pass on openspec-scaffold's **own** tree (the
  live-tree gate runs here): prune graduated closed entries in `knowledge/roadmap.md` or mark
  deliberately-retained ones `<!-- lint:keep -->`; resolve or `<!-- lint:dup-ok -->` any real
  duplicate-block hit; confirm no untriaged-age flags (no matching `FINDINGS*` in this repo, or
  configure). This is in-scope self-tree hygiene; downstream-repo cleanup is NOT (out of scope).
- [x] 6.2 `scripts/check.sh` passes end-to-end: `ruff check` + `ruff format --check` + full `pytest`
  including the `scaffold_lint` SEAL and the live-tree `knowledge_lint` gate (the new managed files
  present in the manifest; `knowledge_lint` clean on this repo's own tree).
