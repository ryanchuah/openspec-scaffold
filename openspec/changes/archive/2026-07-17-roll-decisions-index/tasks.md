# Tasks — roll-decisions-index

Read `explore-brief.md` first for the why. Convention in one line: `knowledge/decisions/INDEX.md`
holds only the newest tail of the registry (byte-budgeted); older entries move verbatim to
`knowledge/decisions/HISTORY.md`, which is never boot-loaded.

## 1. The roll script

- [x] 1.1 Create `scripts/roll_decisions.py` (executable, `#!/usr/bin/env python3`, stdlib only,
  module docstring describing the convention). CLI: `roll_decisions.py [repo_root] [--target-bytes N]
  [--dry-run]`; `repo_root` defaults to the script's parent-of-`scripts/` repo root (mirror
  `boot_surface_lint.py`'s pattern); `--target-bytes` defaults to a module constant
  `TARGET_BYTES = 12_000`.
- [x] 1.2 Parsing: read `knowledge/decisions/INDEX.md` as text. The **anchor** is
  `re.compile(r"^- \*\*(\d{4}-\d{2}-\d{2})\*\*")` — byte-for-byte the same pattern as
  `status_lint._DATE_ANCHOR_RE`. The **header** is everything before the first anchor line and
  always stays in INDEX. An **entry block** is an anchor line plus all following lines (including
  blank lines) up to the next anchor line or EOF — single-line entries are the norm today, but
  continuation lines must travel with their anchor. The trailing block extends to EOF.
- [x] 1.3 Roll semantics: if INDEX's byte size is already ≤ target, print a no-op summary and exit 0.
  Otherwise move entry blocks **oldest-first (top of the entry list)** out of INDEX until its size
  is ≤ target, but always retain at least one entry block in INDEX (never empty the live registry;
  if even one block exceeds the target, keep that one and exit 0 with a note). Moved blocks are
  appended **verbatim, in order, at the end of** `knowledge/decisions/HISTORY.md` — creating that
  file with a short header if absent (`# Decisions Registry — history` + one line: rolled verbatim
  from `INDEX.md`, same format, oldest first, never boot-loaded — grep `knowledge/decisions/` on
  demand + `---`). Because rolls always take INDEX's oldest remaining entries, appending at
  HISTORY's end preserves global chronological order across both files by construction.
- [x] 1.4 Pointer line: after a roll (and only when HISTORY.md exists), ensure the INDEX header
  contains the exact line
  `Older entries: \`knowledge/decisions/HISTORY.md\` (rolled, load on demand).`
  — inserted once, immediately after the header's closing `---` separator; if the header has no
  `---` line (downstream headers are per-repo prose), append it as the last header line,
  immediately before the first anchor line. Idempotent: never duplicated on re-runs.
- [x] 1.5 Safety invariants (each enforced in code, aborting with a message and exit 2, writing
  nothing): (a) INDEX has at least one anchor line; (b) **byte conservation** — the comparison
  target is explicit: (new INDEX content, with the pointer line of 1.4 removed ONLY when this
  run inserted it — a pointer line already present in the original stays in both sides) +
  (the blocks this run appended to HISTORY) MUST equal the original INDEX text exactly,
  compared as strings before any write; (c) both writes (INDEX shrink, HISTORY append) happen
  only after both new contents are fully computed.
- [x] 1.6 `--dry-run`: compute and print the same summary (bytes before/after, entry counts
  retained/rolled, whether the pointer line would be added) but write nothing. The normal run
  prints the same summary after writing.

## 2. Roll script tests

- [x] 2.1 Create `scripts/test_roll_decisions.py` (`unittest`, mirroring
  `test_boot_surface_lint.py`'s style) with a `tmp_path`-style fixture builder that writes a
  synthetic `knowledge/decisions/INDEX.md` (header + N dated single-line entries of known sizes).
- [x] 2.2 Test the basic roll: over-target INDEX → oldest entries land at HISTORY's end in order,
  INDEX ≤ target, header lines intact, pointer line present exactly once.
- [x] 2.3 Test byte conservation: concatenating (HISTORY's appended blocks + rolled INDEX's entry
  blocks) reproduces the original entry sequence byte-for-byte; header unchanged apart from the
  pointer line.
- [x] 2.4 Test continuation lines: an entry block whose anchor line is followed by two non-anchor
  continuation lines moves as one block, never split.
- [x] 2.5 Test idempotence and no-op: a second run after a roll reports no-op and changes neither
  file; an under-target INDEX is untouched. Also test the **re-roll** path (pointer-line
  idempotence under pressure, not the no-op): first roll creates HISTORY + pointer line, then
  append enough new entries to push INDEX over target again, run the roll again — the pointer
  line appears exactly once in INDEX and HISTORY's header is not duplicated. And test the
  `--target-bytes` flag: a run with an explicit `--target-bytes N` leaves INDEX ≤ N.
- [x] 2.6 Test guards: INDEX with no anchor lines → exit 2, nothing written; `--dry-run` on an
  over-target INDEX → files untouched; never-empty guard — an INDEX whose single entry exceeds
  the target keeps that entry.
- [x] 2.7 Test appending to an **existing** HISTORY.md: prior content is preserved, new blocks land
  strictly after it, and the file's header is not duplicated.

## 3. knowledge_lint budget check

> Mid-apply note: once this section lands and until task 6.1 rolls the live tree, running the full
> suite/`knowledge_lint.py` against this repo will flag its own INDEX (currently ~36KB > 16KB).
> That is expected sequencing, not a defect — do NOT weaken the check or roll early; task 6.1
> resolves it, and the green gate runs in section 7. (`status_lint.py` stays clean throughout —
> it scans only INDEX.md, whose remaining entries keep their valid format.)

- [x] 3.1 In `scripts/knowledge_lint.py`, extend `_load_knowledge_lint_config` with key
  `decisions_index_max_bytes` (default module constant `DECISIONS_INDEX_MAX_BYTES = 16_000`).
  Validate: non-`int` (a `bool` counts as non-int) or negative values fall back to the default
  with a one-line stderr note (mirroring `boot_surface_lint`'s validation spirit).
- [x] 3.2 Add `_check_decisions_index_budget(root: Path) -> list[Finding]` following the existing
  check-function pattern: read the size of `knowledge/decisions/INDEX.md` (missing file → no
  findings), load the budget via `_load_knowledge_lint_config`, and when size **exceeds** the
  budget emit one finding, check slug `decisions-index-budget`, whose message includes the actual
  size, the budget, the exact remedy command `python3 scripts/roll_decisions.py` (rolls oldest
  entries to `knowledge/decisions/HISTORY.md`; convention in `knowledge/README.md`), and the
  sentence `Raising the budget is an operator decision recorded in the decisions registry.` The
  check never inspects HISTORY.md's size.
- [x] 3.3 Register it in `collect_findings` (append after `_check_claims_ledger_staleness`), and
  document the new config key in the module docstring's per-repo-config section.
- [x] 3.4 In `scripts/test_knowledge_lint.py`, add tests: (a) INDEX over budget → exactly one
  `decisions-index-budget` finding whose message names `roll_decisions.py`; (b) at/under budget →
  no such finding; (c) `checks.toml` `[knowledge_lint] decisions_index_max_bytes` override is
  honored in **both directions** — a small override flags a small file, AND a raised override
  (e.g. 100,000) silences a file the 16,000 default would flag; (d) invalid override (string / negative / `true`)
  falls back to the 16,000 default; (e) missing INDEX → no finding; (f) a huge HISTORY.md alone
  never triggers the check.

## 4. boot_surface_lint remedy line

- [x] 4.1 In `scripts/boot_surface_lint.py`, when the verdict is WARN or FAIL, append one output
  line after the verdict line:
  `remedy: condense the boot files — if knowledge/decisions/INDEX.md is the dominant weight, roll its oldest entries via: python3 scripts/roll_decisions.py (see knowledge/README.md); raising warn/fail thresholds is an operator decision recorded in the decisions registry.`
  OK output is unchanged.
- [x] 4.2 In `scripts/test_boot_surface_lint.py`, assert the remedy line is present in WARN and
  FAIL output and absent from OK output (extend the existing threshold tests rather than
  duplicating fixtures where practical; do not touch `test_boot_surface_live_tree_not_fail`).

## 5. Convention text + manifest

- [x] 5.1 In `knowledge/README.md`: update the Decisions row of the taxonomy table so its location
  cell reads `knowledge/decisions/INDEX.md` (rolling newest-tail window) + `knowledge/decisions/HISTORY.md`
  (older entries, on demand), and add a short block (≤10 lines) in the notes/usage area below
  documenting the rolling-window convention: INDEX.md = newest tail, byte-budgeted
  (`decisions-index-budget`, default 16,000, per-repo overridable via `checks.toml`); HISTORY.md =
  older entries rolled verbatim, same one-line format, chronological, never part of the mandatory
  boot set, loaded on demand (grep `knowledge/decisions/`); the roll is performed by
  `scripts/roll_decisions.py` (dry-run supported) down to its 12,000-byte hysteresis target;
  budget/threshold raises are operator decisions recorded in the decisions registry.
- [x] 5.2 Add `scripts/roll_decisions.py` and `scripts/test_roll_decisions.py` to
  `scripts/scaffold_manifest.txt` in its existing sort position/style.

## 6. Apply the convention to this repo + close the parked item

- [x] 6.1 Run `python3 scripts/roll_decisions.py --dry-run` from the repo root, sanity-check the
  summary, then run it for real. Expected effect: `knowledge/decisions/HISTORY.md` created,
  `knowledge/decisions/INDEX.md` ≤ 12,000 bytes with the newest entries + pointer line retained.
- [x] 6.2 Confirm `python3 scripts/boot_surface_lint.py .` now exits 0 (scaffold back under the
  80,000 WARN threshold) and its output shows no remedy line.
- [x] 6.3 In `knowledge/questions/knowledge-surface-bounding-2-follow-ons.md`, rewrite item 1
  (OW-13(b)) as resolved: the operator call landed 2026-07-17 on the pressure-triggered
  chronological roll (`roll-decisions-index` change — this change), which supersedes the
  year-split idea; keep items 2 and 3 untouched. Three sentences maximum.
- [x] 6.4 In `knowledge/reference/pending-downstream-propagation.md`, append to the pending list:
  `roll-decisions-index` adds two manifest files (`scripts/roll_decisions.py`,
  `scripts/test_roll_decisions.py`), modifies `scripts/knowledge_lint.py` /
  `scripts/boot_surface_lint.py` / `knowledge/README.md`, and requires a **per-repo roll**
  downstream (each repo runs `roll_decisions.py` against its own tree during its propagation
  session, BEFORE its live-tree `knowledge_lint` gate sees the new check — psc-monitor's INDEX is
  over the new budget today and would otherwise redden its gate on sync). Follow the file's
  existing entry format.

## 7. Green gate

- [x] 7.1 Run `bash scripts/check.sh` and confirm exit 0 (ruff check, ruff format, full pytest —
  including the live-tree `knowledge_lint`/`boot_surface_lint` gates against the freshly-rolled
  tree). Fix any lint/format violations this change introduced.
- [x] 7.2 Run `python3 scripts/knowledge_lint.py` and `python3 scripts/status_lint.py .` directly
  and confirm both exit clean on the rolled tree.
