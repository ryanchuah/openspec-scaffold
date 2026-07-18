# Explore brief — roll-decisions-index

Resolves the parked operator call OW-13(b) (`knowledge/questions/knowledge-surface-bounding-2-follow-ons.md` item 1): decisions/INDEX.md pressure relief. The operator has delegated the condense-vs-raise call to this session.

## Problem

`boot_surface_lint.py` aggregates the four mandatory boot-read files against a byte budget. The
budget is now colliding with reality in both repos that have it wired:

- **psc-monitor: FAIL** — 121,064 bytes against its 120,000 FAIL threshold (its live boot set:
  AGENTS.md 35,725 + STATUS.md 13,428 + questions/INDEX.md 31,402 + decisions/INDEX.md 40,509).
  Its budget was **already raised once** (2026-07-15, `boot-budget-per-repo`: defaults 80k/100k →
  100k/120k) with the recorded rationale that the WARN band should "still fire as an advisory
  signal to keep the surface bounded". It was born in the WARN band and crossed FAIL two days later.
- **openspec-scaffold: WARN steady-state** — 83,925 against 80,000 WARN (AGENTS.md 32,942 +
  STATUS.md 8,370 + questions/INDEX.md 6,766 + decisions/INDEX.md 35,847).

The dominant, still-growing weight in both repos is `knowledge/decisions/INDEX.md` (35.8KB / 88
entries here; 40.5KB in psc-monitor). The questions-index pointer discipline demonstrably works
where applied (scaffold's is 6.8KB); psc-monitor's 31.4KB questions file is that repo failing an
existing convention, not a missing convention — out of scope here, handled downstream.

OW-13(b) already litigated the remedy space on 2026-07-17 and struck down the original plan: a
**year-split is a no-op** (every entry is 2026 — "the original plan quietly assumed a year boundary
would arrive before the pressure did. It did not."). It left three candidate directions and marked
choosing one an operator call. This change is that call.

## Root cause

`decisions/INDEX.md` is an **append-only, never-rotated registry counted at full weight in a
fixed-budget boot set**. Unbounded growth against a fixed budget guarantees collision; the only
questions are when and what gives. Two aggravators:

1. **Essence verbosity drift** — entries average ~407 bytes against the format's terse intent
   (~200); several recent entries run 300–450 chars. Real but secondary: tersening alone buys one
   reprieve, then growth resumes.
2. **The mandate/structure mismatch** — AGENTS.md mandates only "scan the entries relevant to the
   current task" for this file, but a single monolithic file makes partial loading impossible in
   practice: you load all 36–40KB to scan anything.

## Direction (proposed)

**Condense, don't raise — via a pressure-triggered chronological roll, mechanized.** The registry
splits into an always-loaded newest tail and a never-boot-loaded history:

1. **Convention** (`knowledge/README.md`, scaffold-managed): `knowledge/decisions/INDEX.md` holds
   the newest tail of the registry; older entries live in `knowledge/decisions/HISTORY.md` — same
   one-line format, same chronological order, loaded on demand only (grep `knowledge/decisions/`
   when history matters). INDEX carries one standing pointer line to HISTORY.
2. **Detector** (`scripts/knowledge_lint.py`): new `decisions-index-budget` check — a finding when
   `INDEX.md` exceeds **16,000 bytes** (per-repo overridable via the existing `checks.toml`
   `[knowledge_lint]` table, mirroring the `boot_surface_lint` override pattern). The finding
   message names the remedy script — the fix is self-serviceable at the moment of pressure.
3. **Remedy script** (`scripts/roll_decisions.py`, new, manifest-listed, tested): deterministically
   moves the oldest entry blocks from the top of INDEX to the end of HISTORY until INDEX ≤
   **12,000 bytes** (75% hysteresis — the gate doesn't re-trip on the next few archive appends).
   An entry block = a `- **YYYY-MM-DD** ·` anchor line plus any continuation lines. Verbatim
   moves, never rewrites; refuses on malformed structure; idempotent. Moving top-of-INDEX to
   end-of-HISTORY preserves global chronology across both files by construction.
4. **Anti-treadmill line** (`scripts/boot_surface_lint.py`): WARN/FAIL output gains one remedy
   line — condense/roll first; threshold raises are operator decisions recorded in
   `decisions/INDEX.md`. Delivered mechanically exactly when the pressure fires, costing zero
   boot-surface bytes (no AGENTS.md edit, no prefix-cache invalidation).
5. **Apply to self**: roll the scaffold's own INDEX (88 entries → newest tail ≤12KB), taking the
   scaffold's boot surface from 83.9KB (WARN) to ~60KB (clean).
6. **Close OW-13(b)** in the parked follow-ons file.

## Alternatives rejected

- **Raise thresholds (again).** The boot surface is real context burned at the start of every
  session in every repo; the budget exists to force curation. psc-monitor's raise two days ago
  already demonstrated the treadmill: raised to "not FAIL today", FAILed within 48h. Raises remain
  possible but become explicit operator decisions, stated at the point of pressure.
- **Topic split.** Serves "scan the relevant entries" in theory, but adds a per-entry routing
  judgment (misfiling risk), topic drift/overlap, an ambiguous boot set ("which files am I
  required to scan?"), and cross-repo divergence. The chronological roll needs zero judgment, and
  grep over `knowledge/decisions/` serves topic lookup fine.
- **Calendar split (year or half-year files).** Already failed once — all entries are 2026, and at
  the current shipping rate (55 entries in 17 July days) no calendar boundary reliably arrives
  before pressure does. A byte-target roll is boundary-free. Corollary: HISTORY is one file, not
  per-period files — simplest possible roll mechanics, and its size never matters because it is
  never boot-loaded.
- **Recount the budget** (weight decisions/INDEX fractionally since it's scan-only by mandate).
  A raise in disguise unless the file actually becomes partially loadable. The roll achieves real
  partial loading instead: the small INDEX is always loaded, HISTORY only on demand.

## Downstream sequencing (out of scope here)

- **psc-monitor** un-reds via its own SMALL change after this ships: roll its 40.5KB INDEX per
  this convention, enforce the existing questions-pointer discipline (31.4KB → one-line pointers +
  per-item files), trim STATUS to its caps. Its `checks.toml` boot-budget override is then
  expected to become removable (restoring scaffold defaults) — decided there from its landing
  numbers, recorded in its own decisions registry.
- **extrends** receives the convention at the next operator-gated propagation; any needed roll
  happens in that propagation session.

## Risks / checks

- `status_lint.py` validates only `INDEX.md` registry lines; rolled entries leave its scan. The
  script's verbatim-move guarantee preserves format integrity in HISTORY; extending `status_lint`
  to HISTORY is a cheap follow-on, not a blocker.
- `knowledge_lint.py` will scan HISTORY.md as an ordinary knowledge doc: citations are moved
  verbatim and keep resolving (they point at `openspec/changes/archive/` paths); the
  duplicate-block check is unaffected because entries move rather than copy.
- New files must be added to `scripts/scaffold_manifest.txt` (`roll_decisions.py` + its test);
  propagation recorded on the pending-downstream-propagation ledger (operator-gated as always).
- The 16,000/12,000 numbers are judgment calls: 16KB ≈ ~40 recent entries at current verbosity —
  a meaningful recent window; with it, both repos' aggregates sit under the **default** 80k WARN
  with margin (scaffold ~60KB; psc-monitor ~70KB even keeping its larger AGENTS.md); the
  hysteresis gap ≈ 10 archive appends between rolls.
