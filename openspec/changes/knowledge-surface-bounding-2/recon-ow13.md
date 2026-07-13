# Recon — OW-13 (knowledge-surface bounding round 2)

Read-only reconnaissance for tasks.md authoring. All facts below were gathered against the live
tree at `/home/pang/Projects/openspec-scaffold` on 2026-07-13 (HEAD `3db1623`). No source files
were edited to produce this report.

---

## 1. `scripts/status_lint.py` — exact structure

File is 288 lines, stdlib-only, exit 0 (clean) / 2 (violations). Structure:

- **`EXEMPT_HEADINGS`** (line 38-45): a `frozenset` of four normalized heading strings —
  `{"current state", "immediate next action", "done", "pointers"}`. Normalization
  (`_normalize_heading`, line 63) lowercases, strips the `## ` prefix, collapses whitespace — so
  matching is exact-after-normalization (a prefix like `"Done-archive migration"` is NOT exempt;
  pinned by `test_done_dash_archive_not_exempt`).
- **`_split_sections(text)`** (line 91): splits STATUS.md into `(preamble, [(heading_line, body), ...])`
  by scanning for lines starting with `"## "`. Returns raw heading lines (e.g. `"## Current state"`)
  paired with their body text (stripped, joined by `\n`).
- **`_remove_fenced_code_blocks(text)`** (line 72): strips ` ``` `-delimited fence lines (and their
  contents) before word-counting, so code blocks don't inflate a body's count.
- **`_word_count(text)`** (line 86): `len(re.findall(r"\S+", text))` — whitespace-token count.
- **`_check_status_md(repo_root)`** (line 127): loads STATUS.md, splits sections, partitions into
  exempt vs. non-exempt ("change-entry") sections via `_normalize_heading(...) in EXEMPT_HEADINGS`.
  Runs two checks on change-entries ONLY:
  - **C1** — cap count: max 3 change-entries.
  - **C2** — per-entry word budget: each change-entry body ≤150 words (post fence-strip).
  Exempt sections currently have **zero** budget enforcement — this is exactly the gap OW-13(a)
  targets.
- **`_check_decisions_index(repo_root)`** (line 165): a SEPARATE check, format-only (not
  word-budget) — every `- **YYYY-MM-DD**`-anchored line in `knowledge/decisions/INDEX.md` must be
  a 3-part `· `-separated registry line ending in `[inline] ...` or a `→ \`openspec/changes/archive/<dir>/\``
  pointer that resolves to an existing directory. No length/word bound at all today.
- **`main()`** (line 234): runs both checks, prints per-file OK/FAIL, aggregates violations, exit
  2 if any.

### Where per-exempt-section word budgets would slot in

`_check_status_md` already has the exact information needed — it iterates `sections` and knows
which are exempt (the loop at line 138-142 currently just `continue`s past them). The natural
change: replace the flat `EXEMPT_HEADINGS` frozenset with a `dict[str, int]` mapping normalized
heading → max word budget (or `None`/absent-key = still-unbounded), and add a C3 check that
mirrors C2's fence-strip + `_word_count` logic against exempt sections using their budget instead
of skipping them outright. Concretely:

```python
EXEMPT_HEADINGS: dict[str, int | None] = {
    "current state": 400,
    "immediate next action": 400,
    "done": 300,
    "pointers": 150,
}
```
(`None` would mean "exempt from cap-count AND word-budget", preserving an escape hatch if ever
needed — but given the evidence (a 1,645-word accretion log), every exempt heading should probably
get a real numeric cap, not `None`.) The `in EXEMPT_HEADINGS` membership check becomes
`norm in EXEMPT_HEADINGS` (dict membership is identical dict-key membership, so the C1 partition
logic at line 138-142 is UNCHANGED) — only a new loop over exempt sections applying `EXEMPT_HEADINGS[norm]`
as the budget needs to be added, structurally parallel to the existing C2 loop at line 156-160.

### THIS repo's current exempt-section word counts (computed via `status_lint._split_sections` +
`_word_count` + `_remove_fenced_code_blocks` directly against `knowledge/STATUS.md`, verified
live, not estimated):

| Section | Present in this repo? | Word count |
|---|---|---|
| `current state` | yes | **380** |
| `immediate next action` | yes | **950** |
| `done` | **no** (no `## Done` heading exists today) | n/a |
| `pointers` | **no** (no `## Pointers` heading exists today) | n/a |

Non-exempt change-entries in this repo today (for contrast, already budget-enforced at ≤150):
"Latest change — defect-prevention-detectors" = 129 words, "Prior change — instruction-surface-coherence"
= 121 words, "Prior change — composition-audit-cadence" = 138 words — all comfortably under 150,
confirming C1/C2 are already satisfied.

**Budget-picking implication:** `immediate next action` is already at 950 words in the scaffold's
own tree (the task's downstream evidence was 1,645 words — this repo is not yet that bad, but
trending the same direction: it currently reads as an append-only accretion log with an entry per
recently-shipped change, e.g. "correctness-audit-skill SHIPPED", "verify-stack-redirect SHIPPED",
etc., stacked chronologically). **A naive budget picked without headroom (e.g. 150, matching the
non-exempt cap) would immediately red this repo's own tree.** Any proposed budget for `immediate
next action` needs to either (a) be set generously above 950 (e.g. 1200-1500) purely to avoid an
immediate red, deferring the actual trim to a follow-up prune, or (b) be paired with a same-change
prune of `knowledge/STATUS.md`'s "Immediate next action" section down under the chosen budget
before the lint ships. Recommend **(b)** — trim first, then set a tight budget (e.g. 400-500) that
actually restores the "bounded pointer, not an accretion log" property the design intends; a
generous budget that merely legalizes the current 950 words defeats the point of OW-13(a).
`current state` at 380 words has more headroom relative to a plausible ~400-500 budget.

---

## 2. `scripts/test_status_lint.py` — structure

403 lines, `unittest` (NOT pytest-decorated, though collected by pytest fine) — stdlib only, no
fixtures beyond a hand-rolled `_make_repo()` / `_make_archive_dir()` helper writing into a
`tempfile.mkdtemp()` dir, manually torn down in `tearDown` (no `pytest.tmp_path`). Two test
classes:

- **`StatusLintTest`** — behavioral tests, each builds a synthetic STATUS.md / decisions/INDEX.md
  string via `_make_repo(...)`, invokes `status_lint.main([str(repo)])`, and asserts the exit
  code. Organized by check ID in comment-delimited sections: "C1 — Cap count", "`## Operations`
  counts as change-entry", "Exact-match guard", "C2 — Word budget", "Exempt sections skip C2",
  "Zero change-entries", "Graceful absence", "decisions/INDEX.md — registry format (D-E)".
  Helper `_n_words(n)` (line 52) generates `n` space-separated single-letter tokens (`"w0 w1 w2..."`)
  for deterministic word-count fixtures — this is exactly the helper new budget tests would reuse.
  The existing exemption test is `test_exempt_sections_skip_c2` (line 191): builds all 4 exempt
  headings at 200-500 words each plus 3 compliant change-entries, asserts exit 0. **New
  per-section-budget tests would invert this**: one exempt section over its new budget → exit 2;
  under budget → exit 0; would likely replace/split this single test into per-heading budget
  tests (test naming convention already established: `test_word_budget_over_150_fails` /
  `test_word_budget_under_150_passes` / `test_word_budget_exactly_150_passes` — same 3-shape
  pattern (over/under/exact-boundary) should be mirrored per exempt heading, or at minimum for the
  worst-offender headings `current state` and `immediate next action`).
- **`HelperTest`** — direct unit tests of `_word_count`, `_remove_fenced_code_blocks`,
  `_normalize_heading`, `_split_sections` — pure function tests, no repo fixture. No new helper
  functions are anticipated for the budget-map feature (it reuses `_word_count` and
  `_remove_fenced_code_blocks` as-is), so no new `HelperTest` cases are strictly required unless a
  new pure function (e.g. a budget-lookup helper) gets extracted.

No existing test constructs a `dict`-shaped exemption table — the map-shape refactor is new
ground, so its own construction (e.g. "budget map missing a key defaults to X" or "budget map has
an entry for a section that isn't a recognized exempt heading") may want 1-2 dedicated helper
tests once the concrete map shape is chosen in design.md.

---

## 3. `knowledge/decisions/INDEX.md` — structure, size, year-split feasibility

- **Size:** 24,733 bytes, 75 lines (1 preamble/format-doc block + 74 date-anchored registry
  entries, plus a `---` separator).
- **Structure:** flat, NOT grouped by year or date sub-heading — every entry is a single
  `- **YYYY-MM-DD** · <slug> · <essence-or-[inline]-rationale>` bullet in one continuous list,
  chronological, oldest-first. No `## 2026` year sub-headings exist; it is a pure registry, not a
  narrative doc.
- **Year distribution (computed by extracting every `**YYYY-MM-DD**` anchor and counting by
  year):** **all 66 date-anchored entries are dated 2026** (earliest `2026-06-13`, latest
  `2026-07-13`). There are **zero pre-2026 entries** in this repo's decisions/INDEX.md today.
- **Year-split feasibility, concretely:** a "current year stays, older years split to a sibling
  file" convention would be a **complete no-op on this repo's actual content right now** — there
  is nothing to move, because the repo has not yet crossed a year boundary since decisions
  tracking began (2026-06-13 is the earliest entry, decisions/INDEX.md itself didn't exist before
  the 2026-06-18 `add-status-lint` change). This means: (a) the split lint CAN be built and tested
  now (against synthetic fixtures, exactly like `test_status_lint.py` already does for
  decisions/INDEX.md format), but (b) it cannot be verified against this repo's live tree with
  real data — the live-tree gate would need to assert "no entries older than current year exist in
  INDEX.md, OR they do and there's a sibling file" as a vacuously-true-today invariant. This is a
  forward-looking bound, not a today-active one, for this specific repo (a downstream repo further
  along could differ — worth checking if extrends/psc-monitor's decisions files have pre-2026
  entries, though that's out of this recon's scope which is the scaffold repo itself).
- **Existing convention doc — `knowledge/README.md`:** the Decisions row of the taxonomy table
  reads exactly:
  > `Decisions | What did we choose, and why? | knowledge/decisions/INDEX.md (one line per
  > decision → archive; rationale inline when no archive exists) | on-demand`
  This documents the ONE-LINE-PER-DECISION and pointer-vs-inline convention but says **nothing
  about a year-split** — that convention does not exist yet anywhere (not in README.md, not in
  status_lint.py's docstring, not in the INDEX.md format-doc preamble). OW-13(b) would be
  introducing this convention from scratch, not mechanizing an existing one (contrast with
  OW-13(a), which mechanizes an already-real growth problem).
- **Where older entries would move:** given the sibling-file convention, the natural name
  parallels `knowledge/questions/` per-item split pattern already in use — e.g.
  `knowledge/decisions/INDEX-<year>.md` or `knowledge/decisions/archive-<year>.md` (no existing
  precedent file name to imitate exactly; `plans/archive/` is the nearest sibling convention in
  spirit — a `-archive` dir suffix, but decisions/INDEX.md is a single file not a directory of
  items, so a sibling **file** per past year, not a subdirectory, is the natural shape). Needs a
  design.md decision on exact filename.

---

## 4. Mandatory boot-read set (from AGENTS.md's top block) + byte sizes

AGENTS.md's mandatory-read blockquote (top of file, before "## Cross-agent compatibility")
enumerates, in this exact order and with this exact conditionality:

1. **`AGENTS.md`** itself (unconditional — "You are reading this file").
2. **`knowledge/STATUS.md`** (unconditional).
3. **Active section of `knowledge/questions/INDEX.md`** (unconditional; explicitly "stays bounded
   — active blockers only"). The **Parked section is explicitly EXCLUDED** ("NOT part of this
   mandatory read — load ... on demand").
4. **`knowledge/decisions/INDEX.md`** — conditional/partial: "scan the entries relevant to the
   current task" (NOT "read in full" — this is the softest of the four; a byte-budget check
   would need to decide whether to charge the whole file or treat it as out-of-scope precisely
   because only a relevant subset is mandated).
5. **`knowledge/HANDOFF.md`** — conditional on existence ("if it exists ... read it right after
   STATUS.md"); "its normal state is absent" — so this is not steady-state boot weight, but it IS
   currently present in this repo (see below).
6. **`knowledge/README.md`** — referenced ("See knowledge/README.md for the full knowledge
   taxonomy") but NOT phrased as a mandatory read — it is a pointer to consult for orientation on
   the taxonomy, not listed alongside 1-4 as something every boot must ingest. Borderline; the
   design should explicitly decide in/out.
7. `openspec/changes/<name>/` artifacts — explicitly conditional ("if you are resuming an
   in-progress change") and explicitly excluded otherwise ("Otherwise skip"). Not a fixed-size
   boot cost — variable per in-flight change — almost certainly out of scope for a fixed
   `boot_surface` byte sum (there's no single file to size; it's a whole directory conditionally
   loaded).

### Byte sizes (measured live, `wc -c`):

| File | Bytes | Mandatory? |
|---|---:|---|
| `AGENTS.md` | 31,964 | yes, unconditional |
| `knowledge/STATUS.md` | 15,122 | yes, unconditional |
| `knowledge/questions/INDEX.md` (whole file — Active section alone is ~1 line/comment; Parked is the bulk) | 5,289 | Active-only mandatory; whole-file size charged here since that's the mechanically measurable unit |
| `knowledge/decisions/INDEX.md` (whole file — only "relevant entries" mandated) | 24,733 | partial/on-demand by wording, but only whole-file size is mechanically measurable |
| `knowledge/README.md` | 2,934 | referenced, not explicitly "mandatory read" |
| `knowledge/HANDOFF.md` (currently present — this session's own wave-2 handoff) | 9,864 | conditional-on-existence; present right now |

### Candidate sums (four plausible scope definitions):

| Scope | Sum (bytes) | ≈ KB (÷1000) | ≈ KiB (÷1024) |
|---|---:|---:|---:|
| AGENTS.md + STATUS.md + questions/INDEX.md + decisions/INDEX.md (strict 4-file core, no README, no HANDOFF) | 77,108 | 77.1 KB | 75.3 KiB |
| + README.md | 80,042 | **80.0 KB** | 78.2 KiB |
| + README.md + HANDOFF.md (current live state — HANDOFF present today) | 89,906 | 89.9 KB | 87.8 KiB |
| strict 4-file core + HANDOFF.md (no README) | 86,972 | 87.0 KB | 84.9 KiB |

**Is the scaffold under 80KB? — Right at the line, not clearly under.** The tightest
plausible scope (4-file core, no README, no HANDOFF) is 77.1 KB — under the proposed 80KB warn
threshold, but with only ~3KB of headroom. The moment README.md is counted, the sum is **80,042
bytes — landing almost exactly ON the proposed ~80KB warn threshold** (80.0 KB if KB=1000; 78.2
KiB if KiB=1024, i.e. still technically under if KiB is the unit of measure). Any scope that also
counts the currently-present `HANDOFF.md` (which IS part of today's real, live boot cost, since it
exists right now and the AGENTS.md rule makes it mandatory-when-present) pushes the sum to ~87-90KB
— solidly INTO warn territory, though still under the 100KB fail line.

**Implication for design:** this is a live, real finding, not a hypothetical — OW-13(c)'s chosen
scope definition and threshold will determine whether the scaffold's OWN tree is clean or already
warning the moment the check ships. Recommend the tasks.md/design.md explicitly pick: (1) exact
file list (core-4 vs. +README vs. +HANDOFF-when-present), (2) KB vs. KiB, and (3) whether to
accept a warn-state on this repo today (arguably correct/honest — the ~950-word "Immediate next
action" section and the currently-live HANDOFF.md genuinely ARE boot-surface bloat symptoms this
whole change exists to catch) or to require a companion prune (of STATUS.md's "Immediate next
action" per §1 above, and/or absorbing+deleting HANDOFF.md, which the AGENTS.md rule already says
should happen "once absorbed") so the check ships green. Given the task brief for OW-13 frames
this as detecting real bloat, shipping in a warn state on the scaffold's own tree is defensible —
but should be a stated, deliberate choice, not an oversight.

---

## 5. Where the `boot_surface` check should live

**Recommendation: a new standalone `scripts/boot_surface_lint.py`**, not folded into
`status_lint.py` or `knowledge_lint.py`, for these reasons drawn from the existing pattern:

- `status_lint.py`'s docstring explicitly scopes itself to "STATUS.md and decisions/INDEX.md
  mechanical invariants" (line 2) — it is about the SHAPE/format of two specific files, not a
  cross-file byte-budget sum. A boot_surface check spans a different, disjoint file set
  (AGENTS.md + STATUS.md + questions/INDEX.md + decisions/INDEX.md [+ README/HANDOFF depending on
  scope]) — AGENTS.md and questions/INDEX.md are outside status_lint's current file scope
  entirely.
- `knowledge_lint.py`'s docstring explicitly scopes itself to "tracked per-repo knowledge" drift
  detection (orphans, retired paths, broken citations, dangling pointers, log formats) — a
  fundamentally different check shape (filesystem-walk + content-pattern matching) than a fixed
  byte-sum-vs-threshold check.
- Both `status_lint.py` and `knowledge_lint.py` already establish the "one file, one concern,
  composed via `collect_findings`/`main`" pattern (see `scaffold_lint.py`'s `collect_findings`
  at line 463, which is a flat sequence of `findings.extend(check_X(...))` calls — NOT a dynamic
  registry; same shape in `knowledge_lint.py`'s `collect_findings` at line 1366). A new
  `boot_surface_lint.py` would follow this exact established shape: a `main()` that sums bytes for
  a fixed file-list constant, compares against WARN/FAIL thresholds, prints, and returns 0/1/2.
- **Exit-code convention split already exists and matters:** `status_lint.py` uses 0/2 (hard fail
  only, no warn state — see its docstring "Exit codes: 0 — clean, 2 — violations"), while
  `knowledge_lint.py` uses 0/1 ("drift-diagnostic convention, matching sync_scaffold.py --check's
  1"). A boot_surface check needs a THREE-way outcome (clean / warn / fail) that neither existing
  script's convention natively expresses — another reason for a standalone script with its own
  documented exit-code contract (e.g. 0=clean, 1=warn-non-blocking, 2=fail-blocking, mirroring
  `checks.py`'s already-established "shared 0/2/3 exit triple" pattern per the
  `deterministic-tooling-layer` decision in decisions/INDEX.md — worth aligning with that existing
  triple rather than inventing a fourth exit-code convention).

### How `check.sh` invokes the lints — confirmed mechanism

`scripts/check.sh` (the single green gate) does NOT invoke `status_lint.py` / `knowledge_lint.py`
/ `scaffold_lint.py` directly by name at all. Its stages are: (a) `ruff check .`, (b) `ruff format
--check .`, (c) whatever `scripts/test-cmd` names — which in this repo is literally `pytest -q`
(confirmed: `scripts/test-cmd` contents = `pytest -q`). **The three lints are wired in entirely via
pytest, through dedicated "live-tree gate" test files that call the lint module's `main()`/
`collect_findings()` against `REPO_ROOT = Path(__file__).resolve().parent.parent` (the real repo,
not a `tmp_path` fixture):**

- `scripts/test_doc_lint_gate.py` (confirmed live-tree gate for BOTH status_lint and
  knowledge_lint): `test_knowledge_lint_live_tree_clean()` asserts
  `knowledge_lint.collect_findings(REPO_ROOT) == []`; `test_status_lint_live_tree_clean()` asserts
  `status_lint.main([str(REPO_ROOT)]) == 0`. Docstring: "Mirrors the real-root pattern from
  scripts/test_scaffold_lint.py."
- `scripts/test_scaffold_lint.py` has its own live-tree SEAL test, `test_live_repo_lints_clean()`
  (near line 525), asserting `scaffold_lint.collect_findings(tmp_path-or-real-root)` is empty
  against the real tree — explicitly documented as "not test fragility... a red result here means
  a real invariant was violated."

A new `boot_surface_lint.py` would need its OWN live-tree pytest gate function, following this
exact established pattern — either a new test appended to `scripts/test_doc_lint_gate.py`
(natural fit, since that file already exists specifically to aggregate live-tree doc-surface
gates) or a new `scripts/test_boot_surface_lint.py` mirroring the file-per-script convention
(`status_lint.py`↔`test_status_lint.py`, `knowledge_lint.py`↔`test_knowledge_lint.py`). Given
`test_doc_lint_gate.py`'s stated purpose ("Live-tree doc-lint gate... Any drift introduced into a
knowledge doc... will turn the suite red"), **appending a third `test_boot_surface_live_tree_clean()`
function there is the better fit** than a new file, since it is already the designated
aggregation point for this exact category of check, and its docstring would only need a small
addition rather than a wholly new live-tree-gate file. Both `boot_surface_lint.py` itself and its
live-tree test would need adding to `scripts/scaffold_manifest.txt` for downstream propagation
(see §7).

**Note on exit-code semantics for pytest wiring:** because `check.sh`/pytest can only really
express pass/fail (not a 3-way warn/fail), a WARN-level boot_surface result should likely NOT fail
the pytest gate at all (else "warn" becomes indistinguishable from "fail" in the one place it's
actually enforced) — the live-tree test would assert only that the FAIL threshold (~100KB) is not
crossed, while the WARN threshold (~80KB) is surfaced via the script's own stdout/exit-1 when run
standalone (e.g. from `run-audit` or an operator-invoked check), not as a hard pytest assertion.
This mirrors how `knowledge_lint.py`/`status_lint.py` findings ARE hard-asserted in
`test_doc_lint_gate.py` (they have no warn tier — everything is a hard violation), so a
boot_surface warn-tier is a genuinely new shape relative to the existing two live-tree gates and
should be designed deliberately, not just copy-pasted.

---

## 6. `plans/` — count and existing convention

**Current count (this repo, live tree):** `find plans -type f` → **10 files**; `find plans -type
d` → **5 directories** (`plans/`, `plans/archive/`, `plans/day-to-day-tooling/`,
`plans/succession-hardening/`, `plans/sync-deletion-manifest/`). This is far from the "68-file
shadow workflow" the downstream evidence describes — OW-13(d) (marked OPTIONAL in the brief) would
be a near-total no-op on this repo today, similar in spirit to the decisions/INDEX.md year-split
(mechanism buildable now, not exercised by this repo's own content).

**Existing convention — `plans/README.md`** (183 bytes, quoted in full):
```
# Plans directory

- Top-level `plans/*.md` — **live** plans (active or in progress).
- `plans/archive/` — **shipped / closed** plans (cited from `knowledge/decisions/INDEX.md`).
```

**A live, not-yet-executed handoff already exists at `plans/plans-scope-alignment.md`** (4,125
bytes) documenting a KNOWN, already-diagnosed inconsistency directly relevant to any plans/-count
lint: the gather (`scripts/outstanding.py`) enumerates `plans/` **recursively** (`rglob`, excluding
`plans/archive/`), the promoted spec text (`openspec/specs/outstanding-work-view/spec.md`) still
says **"top-level `plans/*.md`"** (stale), and `knowledge_lint.py`'s `_check_closed_unpruned` scans
**top-level only** (`glob`, not `rglob`) — so a nested plan marked DONE is invisible to that lint
today. This is flagged in `knowledge/questions/INDEX.md` Parked as: "plans/ gather scope: keep
recursive, align spec+lint (buried, unexecuted handoff — SMALL, ready to run) →
`plans/plans-scope-alignment.md`." **If OW-13(d) (a plans/-count lint) is picked up, it should be
sequenced together with or after this existing plans-scope-alignment fix**, since a new
count-based lint built against the CURRENT inconsistent recursive/top-level split would inherit
the same disagreement (does "count" mean recursive file count, or top-level only?) unless that
prior alignment work lands first.

---

## 7. Scaffold-manifest check — is STATUS.md/decisions/INDEX.md scaffold-managed?

Checked `scripts/scaffold_manifest.txt` directly (74 lines, full contents inspected):

- **`knowledge/STATUS.md` — NOT in the manifest.** Zero matches for "STATUS" or "decisions"
  anywhere in the manifest file (`grep -c` returned 0).
- **`knowledge/decisions/INDEX.md` — NOT in the manifest** either (same 0-match grep).
- **`scripts/status_lint.py` — IS in the manifest** (line 50), alongside its test
  `scripts/test_status_lint.py` (line 62).
- **`scripts/knowledge_lint.py` — IS in the manifest** (line 47), alongside its test
  `scripts/test_knowledge_lint.py` (line 60).
- **`scripts/test_doc_lint_gate.py` — IS in the manifest** (line 66) — the live-tree gate file
  itself propagates too.
- `knowledge/README.md` is ALSO in the manifest (line 32, "Knowledge taxonomy map
  (scaffold-managed; per D-I)") — confirming it is the one `knowledge/` file that IS scaffold-wide,
  consistent with it being a shared taxonomy doc rather than per-repo state.
- `AGENTS.md` is in the manifest too (line 73, "span-replace, not wholesale copy (see D3)") — so
  the mandatory-boot-read block itself IS scaffold-managed and propagates (span-replace, meaning
  only specific marked spans sync, not the whole file byte-for-byte) — relevant because any
  boot-read-set redefinition in AGENTS.md's mandatory block needs to land inside whatever span is
  sync-eligible.

**This confirms the premise stated in the task brief exactly:** the LINT mechanisms
(`status_lint.py`, `knowledge_lint.py`, their tests, `test_doc_lint_gate.py`, and the taxonomy doc
`knowledge/README.md` + `AGENTS.md`'s synced span) are scaffold-managed and will propagate to
`extrends`/`psc-monitor` via `sync_scaffold.py` once authorized — but the CONTENT they lint
(`knowledge/STATUS.md`, `knowledge/decisions/INDEX.md`) is per-repo and does NOT propagate. A new
`boot_surface_lint.py` (or a check added to an existing scaffold-managed script) would need an
explicit new line added to `scripts/scaffold_manifest.txt` to propagate — this is a task-list item
in itself (manifest entry + `scaffold_lint.py`'s own `check_manifest_completeness` will flag the
new script as an unlisted scaffold file if it's added under `scripts/` without a manifest line, per
that check's behavior described in `scripts/test_scaffold_lint.py`).

---

## Summary of file paths referenced in this recon

- `/home/pang/Projects/openspec-scaffold/scripts/status_lint.py`
- `/home/pang/Projects/openspec-scaffold/scripts/test_status_lint.py`
- `/home/pang/Projects/openspec-scaffold/scripts/knowledge_lint.py`
- `/home/pang/Projects/openspec-scaffold/scripts/test_knowledge_lint.py`
- `/home/pang/Projects/openspec-scaffold/scripts/scaffold_lint.py`
- `/home/pang/Projects/openspec-scaffold/scripts/test_scaffold_lint.py`
- `/home/pang/Projects/openspec-scaffold/scripts/test_doc_lint_gate.py`
- `/home/pang/Projects/openspec-scaffold/scripts/check.sh`
- `/home/pang/Projects/openspec-scaffold/scripts/test-cmd`
- `/home/pang/Projects/openspec-scaffold/scripts/scaffold_manifest.txt`
- `/home/pang/Projects/openspec-scaffold/AGENTS.md`
- `/home/pang/Projects/openspec-scaffold/knowledge/STATUS.md`
- `/home/pang/Projects/openspec-scaffold/knowledge/decisions/INDEX.md`
- `/home/pang/Projects/openspec-scaffold/knowledge/questions/INDEX.md`
- `/home/pang/Projects/openspec-scaffold/knowledge/README.md`
- `/home/pang/Projects/openspec-scaffold/knowledge/HANDOFF.md`
- `/home/pang/Projects/openspec-scaffold/plans/README.md`
- `/home/pang/Projects/openspec-scaffold/plans/plans-scope-alignment.md`
