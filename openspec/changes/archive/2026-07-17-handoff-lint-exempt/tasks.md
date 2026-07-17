## 1. Single-source the sanctioned handoff path

- [x] 1.1 In `scripts/knowledge_lint.py`, add a module-level constant `SANCTIONED_HANDOFF: str = "knowledge/HANDOFF.md"` next to `EPHEMERAL_PATHS`, with a comment stating it is the sole sanctioned mid-session handoff and that it is exempt from prose-hygiene checks both as a citation target and as a scanned source.
- [x] 1.2 Add a helper `_is_sanctioned_handoff(root: Path, path: Path) -> bool` beside `_is_research`, returning `_relpath(root, path) == SANCTIONED_HANDOFF`. Use **exact** equality, never a substring/`in` test — a substring match would wrongly exempt e.g. `plans/knowledge/HANDOFF.md`.
- [x] 1.3 Replace **all three** existing hardcoded `"knowledge/HANDOFF.md"` literals with `SANCTIONED_HANDOFF`: (a) the `rel == "knowledge/HANDOFF.md"` exemption in `_check_handoff_files` (~line 805); (b) the first element of `EPHEMERAL_PATHS` (~line 138); and (c) the **finding message** in `_check_handoff_files` (~line 817, `"...the only sanctioned handoff file is knowledge/HANDOFF.md"`) — interpolate the constant so the user-facing message cannot drift from the path actually exempted. Behavior must be unchanged — this only removes duplicate literals so the sites cannot drift apart.

## 2. Exempt the handoff from the four prose-hygiene checks

- [x] 2.1 In `collect_findings`, exclude the sanctioned handoff from the content-check set: change `content_check_md = [p for p in all_knowledge_md if not _is_research(root, p)]` to also drop paths where `_is_sanctioned_handoff(root, p)`. This covers `retired-path-token` and `broken-prose-path-citation` in one place.
- [x] 2.2 In `collect_findings`, stop passing the handoff to the archive-pointer check: give `_check_dangling_archive_pointers` a list filtered with `not _is_sanctioned_handoff(root, p)` instead of the raw `all_knowledge_md`. Do **not** change what `_check_dangling_archive_pointers` itself does — filter at the call site, mirroring how `content_check_md` is built.
- [x] 2.3 In `_duplicate_scan_files`, skip the sanctioned handoff when collecting `knowledge/` markdown, so it is absent from the compared set. This must remove BOTH the finding on the handoff AND the collateral finding on the file it quoted — the handoff must not be one of the "2+ files" a duplicate window is counted across. **Implementation hint:** unlike the other loops, `_duplicate_scan_files` computes `rel` only for the *directory*, not per file — so compute `_relpath(root, full)` for each file before appending and skip when it equals `SANCTIONED_HANDOFF`.
- [x] 2.4 Leave every other check untouched: `_check_orphan_duplicate`, `_check_handoff_files`, `_check_audit_log`, `_check_ratchet_log`, `_check_closed_unpruned`, `_check_audit_dossier`, `_check_untriaged_age`, `_check_audit_liveness`, `_check_post_close_ledger`, `_check_claims_ledger_staleness` all keep their current inputs and behavior.

## 3. Close the same blind spot in the ref-checker

- [x] 3.1 In `scripts/sync_scaffold.py`, exclude the sanctioned handoff from `_tracked_markdown`'s returned source list so `--check-refs` does not resolve refs sourced **from** a target repo's `knowledge/HANDOFF.md`. Add an **exact-match** exclusion (`r != "knowledge/HANDOFF.md"`) rather than appending to `_REF_SCAN_EXCLUDE`, whose members are substring-matched — the exemption must key on the exact path.
- [x] 3.2 Update the comment above `_REF_SCAN_EXCLUDE` / `_EPHEMERAL_PATHS` to record that the handoff is now excluded in **both** directions (as a citation target via `_EPHEMERAL_PATHS`, and as a scanned source), and keep the existing "keep in step with `knowledge_lint.EPHEMERAL_PATHS`" note accurate.

## 4. Tests — knowledge_lint

- [x] 4.1 In `scripts/test_knowledge_lint.py`, add a test building a `tmp_path` repo with a `knowledge/HANDOFF.md` that simultaneously trips all four checks — a citation to a non-existent path under a real top-level dir, a retired-path token (`ai-docs/`), a pointer to a non-existent `openspec/changes/archive/<dir>/`, and a ≥8-line block copied verbatim from another `knowledge/` file. Assert `collect_findings` returns **zero** findings whose `path` is `knowledge/HANDOFF.md`.
- [x] 4.2 Add an assertion to the same test that **zero** `duplicate-content-block` findings are reported against the *quoted* file either — proving the collateral finding is gone, not just the handoff-side one.
- [x] 4.3 Add the over-broad-suppression guard test (load-bearing): place the identical four constructs in a **non-handoff** knowledge file (e.g. `knowledge/reference/notes.md`) and assert each is **still flagged**. Without this the exemption could be widened to `knowledge/*` and the suite would stay green.
- [x] 4.4 Add a test that a handoff-named file at another path (e.g. `plans/session-handoff.md`) containing a broken citation is **still** flagged by both the handoff-named-file check and the broken-citation check — proving the exemption keys on the exact path and does not leak to other handoff-named files.
- [x] 4.5 Verify the existing tests at `test_knowledge_lint.py:385` (HANDOFF as an exempt citation *target*) and `:821` (the sanctioned handoff is not flagged by the handoff-named check) still pass unmodified — no regression to the two already-shipped carve-outs.

## 5. Tests — sync_scaffold

- [x] 5.1 In `scripts/test_sync_scaffold.py`, add a test that `--check-refs` reports **no** dangling ref sourced from a target repo's `knowledge/HANDOFF.md` when that handoff cites a non-existent `knowledge/...` path.
- [x] 5.2 Assert in the same test that a dangling `knowledge/...` ref from a **non**-handoff tracked doc in that target repo is **still** reported — the source-exclusion must not blind the check generally.
- [x] 5.3 Verify the existing tests at `test_sync_scaffold.py:625-638` (HANDOFF as an exempt citation *target*) still pass unmodified.
- [x] 5.4 Pin the **git-unavailable fallback** path: `_tracked_markdown` falls back from `git ls-files` to `rglob("*.md")` when git is absent or errors, and the handoff exclusion must apply on that branch too. Add a test that forces the fallback (e.g. a target dir that is not a git repo, or monkeypatching `subprocess.run` to raise `FileNotFoundError`) and asserts the handoff is still excluded as a source there. The exclusion is applied after both enumerations so this should pass on the first run — the test exists to keep the branch from silently regressing.

## 6. Green gate

- [x] 6.1 Run `bash scripts/check.sh` and confirm it exits 0 (ruff check, ruff format, full pytest). Fix any lint/format violations the change introduces.
- [x] 6.2 Run `python3 scripts/knowledge_lint.py` against the live repo and confirm it exits clean, with no handoff present (baseline unchanged).
