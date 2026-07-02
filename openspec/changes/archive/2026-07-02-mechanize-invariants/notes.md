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

## Verify checkpoint (2026-07-02)

**1. Verdict:** READY for archive.

**Process notes (operator overrides, recorded):** implementation was executed by the **Sonnet
apply-executor subagent by explicit operator directive** (deepseek-flash path deliberately not
attempted); the **deepseek pro+flash verifier passes were waived by explicit operator directive**
("self review is enough… keep the simplicity/quality gate") — the orchestrator's own behavioral
review ran in full and confidence was high, so the waiver was not escalated; the
**simplicity/quality gate ran** (four parallel review agents: reuse/simplification/efficiency/
altitude) and its confirmed findings were fixed by a **fresh Sonnet fix-executor** (same operator
executor preference, disclosed). Security gate: not triggered (no auth/credential/data/network
surface).

**2. Live output eyeballed (behavior, not counts):** all four seeded-violation probes against the
real repo produced exactly the expected finding lines and exit 1, and the repo returned to
`scaffold-lint: clean` exit 0 after each revert — anchor rename produced BOTH sub-check findings
(uniqueness count 0 + reused-extraction missing-anchor); unlisted bogus skill file named in a
manifest-completeness finding; `-k 15 999` named with file:line in a budget-agreement finding;
`openspec-nonexistent` named in a dangling-refs finding. The armed commit gate blocked a
deliberately red suite (`commit BLOCKED`, exit 2) and passed the green one. The sync hook-wiring
warning fired on an unwired fixture target and stayed silent for psc-monitor, whose `--check`
drift output was unchanged (still exactly the known pending-sync set). Probes re-run identically
after the simplicity-gate refactor.

**3. Defects found and fixes:** behavioral review found **zero functional defects**. The
simplicity gate surfaced seven findings across four angles; five were fixed by the fix-executor
(anchors single-sourced as new `sync_scaffold.AGENTS_ANCHORS` with regexes derived via
`re.escape` — byte-identical semantics; managed globs folded to one loop; `lint-knowledge` twin
constant removed; shared scan set pre-read once in `collect_findings` and passed to both
consumers; dead test flexibility removed). One was skipped by the executor's escape hatch:
reusing `sync_scaffold._read_manifest` is impossible today because it is hardcoded to the real
scaffold root (fixture tests would break) — recorded as a follow-on below. Overruled with
rationale: JSON-parsing the hook-wiring check (substring is the frozen reviewed contract,
advisory-only; recorded as a monitored limitation below); cross-importing `knowledge_lint`'s
one-line helpers (couples independent linters); test-helper dedup with `test_knowledge_lint`
(same accepted-debt class the deterministic-tooling-layer review-log already defers); tests'
double API+CLI run (deliberate coverage of `main()`, not waste).

**4. As-built deltas vs frozen tasks.md (internal, contract unchanged):** the three anchor
strings now live in `sync_scaffold.AGENTS_ANCHORS` and are imported by scaffold_lint (tasks.md
described a local tuple); `check_dangling_skill_refs` / `check_budget_agreement` take
`(root, scanned)` with the scan set pre-read once (tasks.md described each scanning
independently); `_MANAGED_GLOBS` is a single 5-entry tuple. Check-ids, finding formats, exit
codes, and the exclusion list are exactly as specified.

**5. Forward-looking items (for knowledge/questions at archive — recorded nowhere else):**
- **Hook-wiring warning depth:** the check is substring-based and advisory; a settings.json
  containing `scaffold_check.py` under the wrong hook event (or in a comment) would silently
  count as wired. Deepen to JSON `hooks.PreToolUse` parsing only if a real false-negative
  appears.
- **`sync_scaffold._read_manifest` is root-hardcoded**, forcing scaffold_lint to keep its own
  manifest parse. Small follow-on: parameterize it (`_read_manifest(path)`) and dedupe.
- **Manifest deletion/tombstone gap** (from propose): deleting a manifest-listed file upstream
  orphans it downstream silently; the prune change will handle any deletion manually per repo.
- **Downstream applicability of scaffold_lint:** deliberately golden-source-only today; consider
  whether a subset (dangling-refs, budget-agreement) is worth syncing downstream later.
- **Cross-cutting observation from this session's exploration (route to the right home at
  archive):** `knowledge_lint.py`'s `DEFAULT_RETIRED_PATHS` bakes a personal path (`/home/me/`)
  from one downstream incident into golden-source defaults — a repo-agnosticism smell worth a
  look during the succession-hardening prune change.

**Still owned by archive:** `knowledge/STATUS.md` reconciliation (this change's section + cap
rule), `knowledge/decisions/INDEX.md` registry line, `knowledge/questions/INDEX.md` routing of the five
items above (Parked unless blocking), **no delta specs to promote** (tasks-only MEDIUM — but
consider whether the new linter warrants a capability-spec addition; archive-executor to judge
against existing `scaffold-sync-mechanism` spec), cleanup of `plans/succession-hardening/`
residency (portfolio brief spans three more changes — leave in place until the portfolio closes).

## Out of scope

Portfolio changes 2–4 (instruction repairs beyond task 2.2's one-line fix, knowledge pruning,
delegated-agent safety); any downstream repo edits; manifest deletion tombstones; adding
`scaffold_lint.py` to the manifest.
