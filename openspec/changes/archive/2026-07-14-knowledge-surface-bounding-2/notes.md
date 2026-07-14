# notes — knowledge-surface-bounding-2 (OW-13, MEDIUM)

## Problem
The always-loaded boot surface grows unbounded in two places that today's tooling does **not** catch:

1. **STATUS.md cap-exempt sections accrete.** `scripts/status_lint.py` bounds *change-entry*
   sections (≤3 sections, ≤150 words each — C1/C2), but the cap-exempt headings
   (`current state`, `immediate next action`, `done`, `pointers`) have **zero** budget. The
   scaffold's own `## Immediate next action` has become a ~950-word append-only accretion log
   (an entry per recently-shipped change + a downstream-propagation ledger). Downstream evidence:
   extrends' `Immediate next action` reached 1,645 words. `## Immediate next action` is *deliberately*
   exempt from the ≤3-cap (AGENTS.md STATUS cap rule), which is exactly why shipped-change narratives
   that would otherwise be capped get dumped there instead.

2. **No aggregate boot-read budget.** AGENTS.md states "the boot set is a fixed budget, not a
   growing list," but nothing measures the aggregate byte size of the mandatory boot-read set.
   The downstream evidence (extrends ~122KB boot surface) shows this silently balloons.

## Root cause
The canonical bounding rules exist as **prose** (`AGENTS.md` ~L35 "fixed budget"; `AGENTS.md` ~L274
STATUS cap/budget rule) but are only *partially* mechanized: `status_lint` enforces the per-change-entry
budget, and nothing enforces (a) the cap-exempt-section budget or (b) the aggregate boot-read byte
budget. Prose that isn't mechanized drifts (mechanism-over-docs).

## Solution (this change — OW-13, scoped to the live-impactful core)
Two deterministic mechanisms that enforce the *existing* canonical prose rules:

- **(a) status_lint per-section word budgets (C3).** Replace the flat `EXEMPT_HEADINGS` frozenset
  with a `dict[str, int]` mapping each normalized cap-exempt heading → a max word budget, and add a
  C3 check that word-counts each *present* exempt section (reusing the existing
  `_remove_fenced_code_blocks` + `_word_count`) against its budget. C1 (≤3 cap) and C2 (≤150 words)
  are **unchanged** — dict-key membership is identical to the old frozenset membership, so the
  exempt/non-exempt partition is byte-for-byte the same.
- **(c) `scripts/boot_surface_lint.py`.** A new stdlib-only script that sums the byte sizes of the
  fixed mandatory boot-read file set and reports a three-way verdict against WARN/FAIL thresholds.

Plus the **companion STATUS reconciliation** (orchestrator work — see split below) that trims the
accreted `## Immediate next action` and relocates its shipped-but-not-propagated ledger to an
on-demand `knowledge/reference/` doc, so the scaffold's own tree passes the new budgets and the
boot surface actually shrinks.

## Design decisions

### D1 — No spec delta (deliberate)
This MEDIUM change promotes **no `specs/` delta**, matching the round-1 bounding precedent and the
scaffold's single-source discipline:
- The round-1 bounding work (`add-status-lint`, `lean-boot-context`) mechanized STATUS budgets into
  `status_lint.py` with **no spec delta** (lean-boot-context notes: "no delta-spec promotion").
- `knowledge-organization`'s `knowledge-storage-stays-scalable` requirement *deliberately* defers
  numeric bounds to tooling: "the bound is defined and enforced by the project's bounds tooling …
  **not by this spec**." Adding a spec requirement for the budgets would contradict that design.
- The canonical homes for the rules these checks enforce are `AGENTS.md` (~L35 fixed-boot-budget;
  ~L274 STATUS cap/budget) — a `specs/` delta would **duplicate a canonical rule** (HANDOFF lesson
  #1's anti-pattern). The new scripts *mechanize* those canonical rules; they do not create new ones.
- Discoverability is carried by: the script docstrings, the manifest entries, the live-tree pytest
  gates, and `knowledge/reference/exit-codes.md`.

`applyRequires` for this MEDIUM change is `["tasks"]`. `openspec validate` is proposal.md-gated and
will error "Unknown item" on this proposal-less change — **expected, not a failure** (HANDOFF lesson
#6). Green gate = `bash scripts/check.sh` only.

### D2 — status_lint budgets (words)
Normalized-heading → max-word budget map:

| heading | budget | this repo today | rationale |
|---|---:|---:|---|
| `current state` | 500 | ~380 | passes with headroom; archive reconciles into it |
| `immediate next action` | 550 | ~950 → pruned to ≤~450 | restores the "bounded pointer, not accretion log" property; ~100-word headroom for archive to add the next change's line |
| `done` | 300 | absent | bounds downstream repos that use this heading |
| `pointers` | 200 | absent | bounds downstream repos that use this heading |

Budgets are intentionally *tighter than legalizing the status quo* — a budget that merely permits the
current 950 words would defeat OW-13(a). The companion prune (below) brings the scaffold under budget
**before** the new C3 activates, so the change ships green.

### D3 — boot_surface_lint scope, thresholds, exit codes
- **File set (fixed):** `AGENTS.md`, `knowledge/STATUS.md`, `knowledge/questions/INDEX.md`,
  `knowledge/decisions/INDEX.md` — the four unconditionally-scanned boot-orientation files.
  - `knowledge/README.md` **excluded**: AGENTS.md references it as a taxonomy pointer to consult,
    not a mandatory full read.
  - `knowledge/HANDOFF.md` **excluded**: ephemeral (absent in steady state); including it would make
    a *fixed* budget fluctuate. (A present HANDOFF is real transient boot cost, but it is not a
    steady-state budget line.)
- **Thresholds:** WARN ≥ 80,000 bytes, FAIL ≥ 100,000 bytes.
- **Exit convention:** `0` = under WARN (clean), `1` = WARN band (advisory, non-blocking),
  `2` = FAIL (blocking). Mirrors `checks.py`'s clean/warn/hard three-way; documented in the script
  docstring and `knowledge/reference/exit-codes.md`.
- **Scaffold today:** the four files sum to **~80.4KB right now** — already *just into* the WARN
  band (an honest live example of exactly the bloat this check exists to catch: the ~950-word
  `## Immediate next action` accretion is the proximate cause). The companion prune (relocating the
  propagation ledger off the boot surface) brings the total to **~76KB → clean (exit 0)** with
  several-KB headroom. The prune MUST land the total under 80,000 with headroom, not merely at the
  boundary — verify the post-prune total before delegating apply. Downstream (extrends ~122KB) will
  FAIL — the point.
- **Live-tree pytest gate** asserts only that the **FAIL** threshold is not crossed
  (`boot_surface_lint.main([REPO_ROOT]) != 2`), NOT that the tree is clean — otherwise a non-blocking
  WARN would redden the suite and become indistinguishable from FAIL. The WARN tier is exercised by
  fixture unit tests and surfaced by standalone runs.

### D4 — Orchestrator vs executor split
- **Executor (deepseek-flash) — code/tests/scripts only (tasks.md):** the status_lint C3 refactor +
  its tests, `boot_surface_lint.py` + its tests, the two manifest lines, and the `exit-codes.md`
  addition.
- **Orchestrator (primary) — judgment-heavy state editing, NOT in tasks.md, done before the
  executor's `check.sh` gate:** the STATUS `## Immediate next action` prune and the new
  `knowledge/reference/pending-downstream-propagation.md`. These edit load-bearing per-repo state
  (normally archive-executor territory) and require judgment about what is safely relocatable, so
  they are not flash-delegable. They are sequenced **first** so that when the executor adds C3 and
  runs `check.sh`, STATUS already fits the new budget.
- The prune is **lossless**: the shipped-but-not-yet-propagated ledger currently sitting under
  `## Immediate next action` is *relocated* (not deleted) into on-demand `knowledge/reference/`
  (per `migration-preserves-not-in-code-knowledge`), which also moves the accretion off the boot
  surface — the correct direction. `knowledge/reference/` is per-repo (not manifest/scaffold-managed),
  so the ledger does not propagate downstream (each repo's propagation state differs — correct).

## Out of scope (deferred, with rationale)
- **OW-13(b) decisions/INDEX.md year-split.** DEFERRED. It is a **no-op on the scaffold** (all
  entries are 2026; zero pre-year entries to move) and would introduce a *from-scratch* filename
  convention that nothing exercises. decisions/INDEX.md's size (~24.7KB) is already captured inside
  `boot_surface_lint`'s aggregate, so its growth **is** surfaced. Building an unexercised split
  convention adds risk for zero live value. → follow-on.
- **OW-13(d) plans/-count lint.** DEFERRED. Near-no-op on the scaffold (10 files, not the 68-file
  downstream case), and per the OW-13 recon it is **coupled to the unexecuted
  `plans/plans-scope-alignment.md` fix** (a recursive-vs-top-level scope disagreement between
  `outstanding.py`, the promoted spec text, and `knowledge_lint`); a count lint built now would
  inherit that disagreement. Sequence it *after* plans-scope-alignment. → follow-on.
- **OW-8 (delegated-context caching hygiene)** and **OW-12 (archive mechanization)** are distinct
  surfaces (delegation prompt templates; archive scripts) with higher blast radius / no recon —
  separate changes, not folded here.

## Acceptance criteria (change-specific — guides verify)
1. `scripts/status_lint.py` C3 fires: a cap-exempt section over its budget → exit 2; at/under →
   contributes no C3 violation. C1 (≤3) and C2 (≤150 change-entry) behavior is **unchanged**
   (existing tests still pass without modification of their asserted outcomes, except the single
   `test_exempt_sections_skip_c2` behavioral counter-case, which is intentionally superseded).
2. Boundary correctness (adversarial, verify-authored): a section exactly at budget passes; one word
   over fails; fenced code blocks and the heading line are excluded from the count; a section whose
   heading is NOT a recognized exempt heading is still treated as a change-entry (C1/C2), not
   silently budget-exempted.
3. `scripts/boot_surface_lint.py`: sums exactly the four fixed files; missing file is skipped (not an
   error); total < 80,000 → exit 0; 80,000 ≤ total < 100,000 → exit 1; total ≥ 100,000 → exit 2.
   Boundary values (exactly 80,000; exactly 100,000) resolve to the WARN and FAIL sides respectively.
4. Both scripts are in `scripts/scaffold_manifest.txt` with their tests; `scaffold_lint.py`'s
   manifest-completeness check stays green (no unlisted scaffold script under `scripts/`).
5. `knowledge/STATUS.md` `## Immediate next action` ≤ 550 words and `## Current state` ≤ 500 words;
   the relocated propagation ledger is captured in `knowledge/reference/pending-downstream-propagation.md`
   and cited from STATUS; no load-bearing propagation-state fact is lost.
6. `bash scripts/check.sh` is green (ruff + format + full pytest incl. the two new live-tree gates).
7. `knowledge/reference/exit-codes.md` documents `boot_surface_lint`'s 0/1/2 convention.

## Assumptions (non-blocking defaults; batch-surfaced at the next operator gate)
- **A1 — Budgets/thresholds are round-number judgment calls**, chosen to bound real accretion while
  shipping the scaffold green. If the operator prefers tighter/looser numbers, they are a one-line
  edit each (`EXEMPT_HEADING_BUDGETS` dict; `WARN_BYTES`/`FAIL_BYTES` constants).
- **A2 — boot_surface counts whole files**, including `decisions/INDEX.md` which the boot rule only
  "scans relevant entries" of. Charging the whole file is the conservative/mechanically-measurable
  choice (there is no way to size "the relevant subset").
- **A3 — Downstream propagation of these scaffold-managed scripts is operator-gated and deferred**
  (joins the standing deferred-propagation list). On the next authorized sync, extrends/psc-monitor
  will likely FAIL `boot_surface_lint` (they are over budget today) — that is the intended signal,
  and cleaning them up is separate downstream work, not this change.

---

## Verify checkpoint (2026-07-14) — READY for archive

1. **Verdict:** READY for archive. Self-review PASS → pro behavioral verifier (deepseek-v4-pro)
   `VERDICT: READY` zero defects → simplicity gate PASS. `check.sh` green. Zero Sonnet fallback
   anywhere (propose review, apply, verify all clean on deepseek).

2. **Live output eyeballed (behavior, not counts):** ran `boot_surface_lint.py` on the live tree — it
   summed the four boot files and returned OK under the 80,000 WARN threshold with real headroom (the
   post-prune total; per-file breakdown printed: AGENTS.md, STATUS.md, questions/INDEX.md,
   decisions/INDEX.md). `status_lint.py` returned OK on the pruned STATUS.md (both cap-exempt sections
   under their C3 budgets). Independently authored 21 adversarial/boundary fixtures and confirmed each
   behaved: C3 passes AT budget and fails ONE word over for every heading; a DUPLICATE
   `## Immediate next action` has its over-budget instance flagged (C3 walks `sections` directly, not
   a heading-keyed dict); a trailing-text heading (`## Immediate next action — notes`) is routed to
   C2 (max 150), NOT C3-exempted; fenced code is excluded from the count; boot_surface returns WARN at
   exactly 80,000 and FAIL at exactly 100,000, skips missing files, and returns clean when all boot
   files are absent.

3. **Defect found + fix:** none. The executor's implementation was correct on the first pass; no
   re-delegation needed. (The mandated STATUS prune + reference-doc relocation were orchestrator work
   done before apply, as designed — not a defect.)

4. **As-built delta vs artifacts:** none — the implementation matches `tasks.md`/`notes.md` exactly
   (budgets 500/550/300/200; thresholds 80k/100k; BOOT_FILES = the four-file core; live-tree gate
   asserts `!= 2`). One trivial PRE-EXISTING nit (not introduced here, not fixed): `status_lint.py`'s
   module docstring still opens "Enforces the bounds specified in design.md §D-E" — a stale reference
   to the original `add-status-lint` change's design.md; out of scope for this change.

5. **Forward-looking items (fold into `knowledge/questions/INDEX.md` Parked at archive):**
   - **OW-13(b) decisions/INDEX.md year-split — DEFERRED.** decisions/INDEX.md is now the single
     largest boot-surface contributor (~27KB of the ~73KB total); `boot_surface_lint` will WARN as the
     aggregate grows, and the year-split is the eventual pressure-relief. No-op on the scaffold today
     (all entries 2026). → Parked.
   - **OW-13(d) plans/-count lint — DEFERRED.** Coupled to the unexecuted `plans/plans-scope-alignment.md`
     fix (recursive-vs-top-level scope disagreement); build it after that lands. Already tracked in
     questions/Parked — no new pointer needed.
   - **Budget/threshold tuning (notes.md A1).** 500/550/300/200 words and 80k/100k bytes are
     round-number judgment calls; revisit if downstream noise warrants (one-line constant edits). → Parked.
   - **boot_surface WARN tier is advisory-only in pytest** (live-tree gate asserts `!= 2`, so a WARN
     does not redden the suite — by design). A WARN is only surfaced by a standalone run. Consider
     wiring `boot_surface_lint` into `run-audit`'s reported surface so WARN is visible without a manual
     run. → Parked (monitored).
   - **Propagation-ledger relocation is NEW and load-bearing for archive:** the shipped-but-deferred
     downstream-propagation ledger moved OUT of STATUS `## Immediate next action` INTO
     `knowledge/reference/pending-downstream-propagation.md` (on-demand, off the boot surface). The
     archive-executor MUST record THIS change's own deferred propagation in that reference doc — NOT
     re-accrete it into STATUS — and keep STATUS's `## Immediate next action` / `## Current state` under
     the new C3 budgets (550 / 500 words).
   - **Downstream propagation deferred/operator-gated** for the scaffold-managed edits here
     (`status_lint.py`, new `boot_surface_lint.py`, `scaffold_manifest.txt`); extrends/psc will FAIL
     `boot_surface_lint` on first sync (extrends ~122KB). Recorded in the new reference doc.

**Still owned by archive (do NOT edit here — reconciled at archive by the delegated executor):**
- `knowledge/STATUS.md` — add the "Latest change — knowledge-surface-bounding-2" section (≤150 words),
  drop the oldest of the current 3 change-entries (≤3 cap → `apply-throughput-resume` drops), and keep
  `## Immediate next action` ≤550 / `## Current state` ≤500 words (the NEW C3 budgets — the live-tree
  `status_lint` gate will block the commit otherwise).
- `knowledge/decisions/INDEX.md` — append one registry line for this change → its archive dir.
- `knowledge/questions/INDEX.md` — add the Parked pointers from field 5 above.
- **Spec promotion: NONE** — no `specs/` delta by design (D1). Do not synthesize one.
- `knowledge/reference/pending-downstream-propagation.md` — record this change's deferred propagation
  (see field 5); this is the new home, not STATUS.
- `knowledge/HANDOFF.md` — the current handoff has been absorbed this session; the archive step / a
  new end-of-session handoff supersedes it (do not leave the old wave-2 handoff stale).
