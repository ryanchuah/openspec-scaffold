## 1. Widen the handoff-file lint (`scripts/knowledge_lint.py`)

- [x] 1.1 Rename `_check_root_handoff_files(root)` → `_check_handoff_files(root, is_ignored)` and replace its root-only `root.iterdir()` scan with a repo-wide `os.walk(root)` walk. Mirror `_check_orphan_duplicate`'s **directory** pruning: `dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not is_ignored(_relpath(root, Path(dirpath) / d))]`. Then, for each remaining file compute `rel = _relpath(root, Path(dirpath) / filename)` and **additionally filter each file** through `is_ignored(rel)` — `continue` if `rel == "knowledge/HANDOFF.md"` (sole exemption) or `is_ignored(rel)`; otherwise flag when `"handoff" in filename.lower() or "handover" in filename.lower()`. NOTE: `_check_orphan_duplicate` prunes only directories and does NOT filter individual files; the per-file `is_ignored(rel)` filter is added here and is load-bearing for the "gitignored handoff files are not flagged" contract (a gitignored file need not sit under a gitignored directory).
- [x] 1.2 Change the emitted `Finding` slug from `"root-handoff-file"` to `"handoff-file"` and the message to `f"handoff-named file {rel}; the only sanctioned handoff file is knowledge/HANDOFF.md"`.
- [x] 1.3 Update the call site in `collect_findings` (line ~945): `_check_root_handoff_files(root)` → `_check_handoff_files(root, is_ignored)` (`is_ignored` is already in scope there).
- [x] 1.4 Update the `# Check 6 — root-level handoff files` section comment (line ~522) and the function docstring to describe the widened repo-wide, case-insensitive-substring scope with the single `knowledge/HANDOFF.md` exemption.
- [x] 1.5 Fix the two stale "root-handoff-file check" cross-references in the promoted `openspec/specs/knowledge-lint/spec.md` **overview** — the top paragraph (line ~11: "a root-handoff-file check mechanizes the handoff-file convention") and the overview requirement's check list (line ~22: "and a root-handoff-file check.") — to name the widened repo-wide handoff-file check. This is a direct main-spec edit because both phrases live in overview prose the requirement-level delta does not carry; it touches neither the renamed requirement (delta-synced at archive) nor any other requirement, so there is no archive-sync conflict.

## 2. Update the check's tests (`scripts/test_knowledge_lint.py §7.1`)

- [x] 2.1 Update the finding slug `"root-handoff-file"` → `"handoff-file"` at all three call sites (lines ~742, ~759, ~771).
- [x] 2.2 Keep the existing root-level-flag and clean-tree and `knowledge/HANDOFF.md`-exempt cases (all still valid). Add three cases: (a) a nested `plans/foo-handoff.md` **is** flagged; (b) a nested `docs/HANDOVER.md` (uppercase) **is** flagged; (c) a `handoff`-named file under a gitignored dir is **not** flagged — build this with the `git init` + `.gitignore` fixture pattern already used at line ~432, INCLUDING its `@pytest.mark.skipif(shutil.which("git") is None, …)` guard so it skips cleanly in gitless environments (e.g. `.gitignore` = `output/\n`, file `output/x-handoff.md`).
- [x] 2.3 Fix the stale term in `scripts/test_doc_lint_gate.py` line ~6: the module docstring says "a root-handoff file" — update to "a handoff-named file" (comment-only; the gate assertions need no functional change since the scaffold tree has only `knowledge/HANDOFF.md`).

## 3. Signpost outstanding-work discovery (`AGENTS.md` — shared span)

- [x] 3.1 In the "## Working process" section add one bullet naming the canonical entry point for enumerating outstanding work: to find what work is outstanding, invoke the pull-only `outstanding-work-review` skill — deliberately never boot-wired. The bullet itself is just that pointer (skill name + pull-only + not-boot-wired); do NOT restate the skill's internals (the `facts.py --check outstanding` mechanics named in this task are context for you, not text for the bullet).

## 4. Name the residual LLM sweep (`.claude/skills/outstanding-work-review/SKILL.md`)

- [x] 4.1 In the "Judge (orchestrator)" step (step 3) add a named **"Residual sweep"** sub-step stating what the deterministic gather does NOT cover and must be read by hand: prose *bodies* of the point-enumerated `plans/` and `knowledge/questions/*.md` files (open each and classify consumed / live / orphaned), in-code `TODO`/`FIXME` (a deliberate no-op in `outstanding.py`), and stray research docs. Frame it as converting the "occasional human/LLM sweep" into a documented, repeatable step — do not change what the deterministic collector enumerates.

## 5. Green gate

- [x] 5.1 Run `bash scripts/check.sh` (ruff + format + full pytest, incl. the doc-lint live-tree gate and the scaffold SEAL) and confirm green. Run `openspec validate outstanding-and-continuity-hardening --strict` and confirm clean.
