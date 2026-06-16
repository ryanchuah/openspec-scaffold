## 1. Sync script — `scripts/sync_scaffold.py`

- [x] 1.1 Implement `sync_agents_md(scaffold_text, target_text)` per design D3 (header-free span-replace):
  detect scaffold anchors (`> **MANDATORY`, `## Roles`, `## After reading this file`) and abort with a
  `ValueError` if any is missing; abort if scaffold carries a tail after `## After reading this file`
  (scaffold-tail invariant); detect target anchors (`> **MANDATORY`, `## Roles`, `## After reading this
  file`) and abort if any is missing; assemble `t_title + span1 + proj_ctx + span2 + tail` preserving the
  target title, `## Project
  context`, and tail verbatim with **no** header injected; if the target exceeds 300 lines and yields no
  tail separator, abort rather than truncate.
- [x] 1.2 Implement the copy pass: read the manifest (skip `#`/blank lines); copy each regular file
  byte-identical from scaffold to `<target>/<path>` (creating parent dirs); route `AGENTS.md` through
  `sync_agents_md`. Validate first, write second: abort non-zero and make **no** changes if the target path
  has no `.git`, or if any manifest-listed source file is missing in scaffold. Inject no header text.
- [x] 1.3 Implement `--check <target>`: report IDENTICAL / DIFFERS / MISSING per manifest file; compare
  regular files byte-for-byte against the scaffold source; compare `AGENTS.md` by reconstructing
  `sync_agents_md(scaffold_text, current_target_text)` and diffing against the current target; exit `1` if
  any file is not IDENTICAL, else `0`.
- [x] 1.4 Add the CLI entry `sync_scaffold.py <target-repo-path> [--check]` with argument validation and a
  clear usage error. This script is scaffold-only and is **not** added to the manifest.

## 2. Commit guard — `scripts/scaffold_check.py`

- [x] 2.1 Implement the guard per design D5: resolve the manifest via `Path(__file__).resolve().parent /
  "scaffold_manifest.txt"` (not cwd); build the managed set from non-comment manifest lines; get staged
  paths from `git diff --cached --name-only`; if the intersection is non-empty, print a message naming the
  files and directing the editor to change scaffold (+ the `--no-verify` escape) and `sys.exit(2)`; else
  `sys.exit(0)`.
- [x] 2.2 Add a module docstring documenting the coverage limitation (M1): the guard is a Claude Code
  `PreToolUse` hook that only intercepts commits Claude makes via its Bash tool; operator-terminal and
  opencode/deepseek executor commits bypass it, and `git commit --no-verify` is the sanctioned escape.

## 3. Manifest — `scripts/scaffold_manifest.txt`

- [x] 3.1 Create the manifest with the design-D2 contents: an ordinary leading `#` comment ("scaffold-managed
  inventory — edit upstream…"), then the grouped repo-relative paths (`.claude/agents` + skills, `.opencode`
  agents, `ai-docs/fast-track-workflow.md` + `ai-docs/research-fetch-convention.md`, the `scripts/*` set
  including `scaffold_check.py` and `scaffold_manifest.txt` itself, and `AGENTS.md`). Create this **after**
  tasks 1–2 so every self-referenced file already exists.
- [x] 3.2 Confirm the manifest is honest: every listed path exists in scaffold; `scripts/sync_scaffold.py`
  and the volatile/per-repo state files (STATUS.md, ai-docs/decisions.md, ai-docs/open-questions.md,
  ai-docs/improvement-roadmap.md, ai-docs/archive/**, .claude/settings.json, scripts/test-cmd) are absent
  from the list; and `ai-docs/opencode-delegation-notes.md` is **not** listed (absent in scaffold).

## 4. Unit tests — `scripts/test_sync_scaffold.py`

- [x] 4.1 Mirror `scripts/test_convergence.py` (stdlib `unittest`, no pytest dependency, `sys.path` import
  of the sibling module, `tempfile` fixtures, runnable standalone with `unittest.main()`). Build helper(s)
  that construct fixture scaffold + target trees in a tmpdir.
- [x] 4.2 Span-replace tests: `## Project context` preserved byte-identical; no-`## Project context` case
  (extrends-like) succeeds without inserting an empty section; a psc-monitor-like long tail
  (`# Project reference` after `## After reading this file`) preserved byte-for-byte; missing-anchor abort;
  scaffold-tail-invariant abort; >300-line no-tail abort.
- [x] 4.3 Idempotency tests: syncing a fixture target twice leaves files unchanged and `--check` exits `0`
  after the second run; `sync_agents_md` applied to its own output returns a byte-identical string.
- [x] 4.4 `--check` tests: exits `0` when the fixture target matches scaffold; exits `1` and names the file
  after a one-byte edit to a synced file or a deleted file; reports `AGENTS.md` IDENTICAL when only the
  per-repo `## Project context`/tail differ but the shared spans match.
- [x] 4.5 No-header test: the synced fixture output (regular files and `AGENTS.md`) contains no
  "DO NOT EDIT — synced from openspec-scaffold" string injected by the script.
- [x] 4.6 Guard tests: with `git diff --cached --name-only` stubbed, `scaffold_check.py` returns `2` when a
  manifest-listed path is staged (message names the file(s) and directs the editor to change scaffold) and
  `0` when none is.
- [x] 4.7 Sync abort tests (assert non-zero exit AND no files written on abort): target path does not exist
  or lacks `.git` (`sync-aborts-on-bad-target`); and a manifest-listed source file is missing from scaffold
  (`sync-aborts-on-missing-scaffold-source`).
- [x] 4.8 Parent-dir test: syncing a manifest entry whose parent directory does not yet exist in the target
  creates the directory and writes the file at the correct nested path (`sync-creates-parent-dirs`).

## 5. Run the suite

- [x] 5.1 Run `python scripts/test_sync_scaffold.py`; all tests pass.
