# SMALL plan — sync deletion manifest (change B of the day-to-day-tooling portfolio)

**Tier:** SMALL (operator-confirmed 2026-07-03, portfolio confirmation).
**Premise pass:** WAIVED by operator instruction 2026-07-03 ("skip the deepseek direction
review pass") — the portfolio-level direction gate already returned `PREMISE: AGREE`
(`plans/day-to-day-tooling/premise-review.md`).

## Problem statement

`sync_scaffold.py` copies manifest-listed files to downstream repos but has **no deletion
mechanism**. When a scaffold file is removed or renamed, downstream copies linger until
someone hand-deletes them ("tombstones"): the `openspec-onboard` skill removal required a
manual `rm -rf` per repo, and psc-monitor still carries the stale
`.claude/skills/openspec-onboard/` directory today. The upcoming checks/facts rename
(portfolio change A) would repeat this manual sweep. `--check` also cannot see this class
of drift: a stale downstream file that no longer exists upstream is invisible to it.

## Proposed approach

1. **New authoring-side list `scripts/scaffold_manifest_removed.txt`** — same line format
   as `scaffold_manifest.txt` (blank lines and `#` comments skipped). Each entry is a
   repo-relative path that must NOT exist downstream. A trailing `/` marks a directory
   entry; anything else is a file entry. Seed it with `.claude/skills/openspec-onboard/`
   (the outstanding psc-monitor tombstone — extrends already clean, so the no-op path is
   exercised too).
2. **`sync()` deletion pass** (after the copy pass): for each removed-list entry present in
   the target, delete it (file → `unlink`; trailing-slash dir → `rmtree`) and print
   `REMOVED  <path>`; absent entries are silent no-ops (idempotent).
   Guards (all hard errors, before any deletion):
   - a path listed in BOTH `scaffold_manifest.txt` and the removed list → conflict, abort;
   - a removed-list path that still exists in the scaffold repo itself → lists disagree
     with reality, abort;
   - the resolved target path must stay inside the target root (reject `..`/absolute/
     symlink escapes);
   - a dir-marked entry that is a file downstream (or vice versa) → abort rather than
     guess.
3. **`check()` reports stale paths:** a removed-list entry present in the target prints
   `STALE  <path>` and exits 1 (drift), so rename leftovers finally show up in
   `--check`.
4. **`scaffold_lint.py` guard (one small check):** no path may appear in both manifest
   files — mechanizes the conflict rule at commit time.
5. **Tests** (extend `scripts/test_sync_scaffold.py`, tmp-fixture style, plus a
   `test_scaffold_lint.py` case for the new guard): deletion of file and dir entries;
   idempotent no-op when absent; `check` STALE reporting; both-lists conflict; upstream-
   still-exists conflict; path-escape rejection; missing removed-list file tolerated
   (empty list — backward compatible).

## Out of scope

- Change A's actual renames (its old filenames are appended to the removed list when A
  lands — this change only builds the mechanism and seeds the onboard tombstone).
- Any change to `scaffold_check.py`, the AGENTS.md/config.yaml span-merge logic,
  `--check-refs`, or the provenance beacon.
- Running the sync against any downstream repo (operator-gated, happens at portfolio
  step D1/D2).
