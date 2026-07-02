# Notes — mechanize-invariants

**Tier:** MEDIUM (tasks.md-only per AGENTS.md; acceptance criteria live here).
**Direction:** change 1 of 4 in the succession-hardening portfolio — brief at
`plans/succession-hardening/explore-brief.md`, direction gate `PREMISE: AGREE` at
`plans/succession-hardening/premise-review.md` (pro, 2026-07-02). The shared brief stays in
`plans/` because it covers four changes; the prune change (portfolio change 3) will decide its
final home. Downstream propagation of everything here is FROZEN per the standing operator hold.

## Why (one paragraph)

The scaffold's remaining silent-failure modes are prose conventions with no machine enforcement:
files forgotten from `scaffold_manifest.txt` never propagate and nothing notices; the AGENTS.md
span-merge anchors and the config.yaml rules-block-last invariant are unmarked and only fail at
sync time, far from the edit; instruction files can cite skills that don't exist (live example:
`openspec-continue-change` in the apply skill); the delegation-harness §e budget table is
"authoritative" but ~9 embedded `timeout` invocations carry the literal numbers with no drift
check. This change converts each into a deterministic commit-time check (`scripts/scaffold_lint.py`
+ live-repo pytest test), arms this repo's dormant commit-test gate so the suite actually gates
commits, and adds a sync-time warning for the known bootstrap gap (target repos lacking the
`scaffold_check.py` hook wiring).

## Decisions (incl. resolutions of the direction-gate 🟡 items)

- **Enforcement wiring (gate 🟡3):** `scaffold_lint.py` is a standalone CLI; enforcement happens
  via a live-repo test inside the pytest suite, and the suite gates commits once `scripts/test-cmd`
  arms `test-gate.sh`. No hook changes needed.
- **Budget check approach (gate 💡2):** parse numeric `timeout -k G B` pairs rather than reducing
  embedded blocks to citations — the blocks are load-bearing copy-paste commands for agents;
  citations would degrade executability. The regex is narrow (numeric-only) and unit-tested; the
  harness's placeholder text (`timeout -k <grace> <budget>`) does not match it.
- **Scaffold-only tool:** `scaffold_lint.py` + its test are authoring-side (like
  `sync_scaffold.py`) — NOT manifest-listed, never synced. The manifest-completeness exclusion
  list encodes this.
- **Manifest tombstone (gate 💡1):** NOT folded in. Deleting a manifest-listed file upstream still
  orphans it downstream; that gap stays recorded in the portfolio brief and goes to
  `knowledge/questions/` at archive. The prune change will handle any deletion manually per repo.
- **Known live violation:** the dangling `openspec-continue-change` reference is fixed here (task
  2.2) because the live-repo lint test cannot pass with it present. Portfolio change 2
  (`repair-instruction-surface`) no longer needs that item.

## Acceptance criteria (verify phase)

1. Full suite green: `pytest -q` from repo root (`python3 -m pytest` does NOT resolve on this
   machine — pytest is user-installed for python3.13 only; includes new
   `scripts/test_scaffold_lint.py` and the new `test_sync_scaffold.py` cases).
2. Live behavioral eyeball — linter clean on the real repo: `python3 scripts/scaffold_lint.py`
   exits 0 with no output (or explicit "clean" line only).
3. Seeded-violation probes (temporary edits, reverted after each, or a scratch copy of the repo):
   (a) rename `## Roles` in AGENTS.md → `agents-md-structure` finding, exit 1;
   (b) add `.claude/skills/bogus-skill/SKILL.md` not in the manifest → `manifest-completeness`
   finding; (c) change one embedded `timeout -k 15 780` to `timeout -k 15 999` →
   `budget-agreement` finding naming the file; (d) add token `openspec-nonexistent` to a skill →
   `dangling-skill-refs` finding. Each probe edit MUST be reverted before the next probe, and
   `git status` must be clean (modulo the change dir) after the last probe.
4. Commit-gate armed: `scripts/test-gate.sh` exits 0 and prints `tests passed` on the green suite;
   with a deliberately failing test temporarily added (see `tests/commit-gate-smoke/` fixture
   procedure), it exits 2 and prints `commit BLOCKED`; the temporary failure is then removed.
5. Sync warning behaves: `python3 scripts/sync_scaffold.py --check ../psc-monitor` prints NO
   wiring warning (psc-monitor has the hook wired) and its drift output/exit code is byte-for-byte
   unchanged from before this change, aside from the (expected, pre-existing) pending-sync diffs.
   A fixture target without the wiring produces the warning (unit-tested).
6. Multi-model verification per the verify skill (MEDIUM: self → pro → flash), simplicity/quality
   gate; security gate not triggered (no auth/credential/network surface).
7. No downstream sync in this change — propagation stays frozen.

## Out of scope

Portfolio changes 2–4 (instruction repairs beyond task 2.2's one-line fix, knowledge pruning,
delegated-agent safety); any downstream repo edits; manifest deletion tombstones; adding
`scaffold_lint.py` to the manifest.
