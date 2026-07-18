# Review log — roll-decisions-index

## Round 0 — direction gate (explore-brief.md), 2026-07-17, openspec-reviewer @ deepseek-v4-pro

I now have all the evidence needed. Let me write the review.

---

## Review Round 1 — explore-brief.md (Direction Gate)

### Summary

The explore-brief correctly diagnoses a real structural problem — `decisions/INDEX.md` is an append-only, never-rotated registry that grows unboundedly against a fixed boot budget. The evidence is clear: psc-monitor already demonstrated the treadmill (raised to 120KB, FAILed within 48h), and scaffold sits in WARN steady-state. The root cause (unbounded vs. fixed) is properly identified. The proposed direction — a pressure-triggered, byte-budgeted chronological roll into a never-boot-loaded HISTORY.md, mechanized via a `knowledge_lint` check plus a deterministic `roll_decisions.py` — is a coherent resolution that avoids every rejected alternative's known failure modes. The rejected alternatives (raise thresholds, topic split, calendar split, recount budget) are each fairly and convincingly dispatched, especially the year-split which the evidence demonstrates is a genuine no-op (88/88 entries are 2026).

**Factual claims verified against the tree:** ✅ 88 entries in `knowledge/decisions/INDEX.md` (lines 9-96); ✅ OW-13(b) confirms year-split struck down and three options left as operator call; ✅ `boot_surface_lint.py` defaults are WARN=80,000 / FAIL=100,000 with per-repo override via `checks.toml`; ✅ `knowledge/README.md` has no rotation or HISTORY.md convention; ✅ the boot set is exactly the four files enumerated. The specific byte counts (e.g., 83,925 for scaffold) are consistent with observed file sizes and are not critical to the premise — the WARN steady-state signal is sufficient.

No drift from the OW-13(b) source. The brief synthesizes the three options into a concrete direction (chronological roll = a form of split-by-something-other-than-year, plus verbatim-move preserves format integrity, and the budget stops being miscounted because INDEX shrinks).

### 🔴 Blocking Issues

None.

### 🟡 Should Fix

1. **"Entry block" parsing is underspecified for multi-line continuation entries.** The brief says "An entry block = a `- **YYYY-MM-DD** ·` anchor line plus any continuation lines." The current INDEX has several multi-line entries (e.g., line 9 `archive-closed-plan-bundles` spans ~4 continuation lines; line 53 `prune-knowledge` has continuation; line 54 `clarify-audit-tooling-surface` has a ~~strikethrough~~ qualification). The script design must handle continuation lines that don't start with the anchor pattern — this is the single most load-bearing implementation detail. The direction is fine; this is a flag for `design.md` to nail down the block-extent rule precisely (e.g., "all non-blank lines following the anchor until the next anchor or EOF").

2. **The 16KB/12KB calibration relies on average entry size (~407 bytes) but the distribution is skewed.** Several recent entries are 1,000–2,000 bytes (e.g., `archive-mechanization` at line 86, `checks-facts-split` at line 55). If the newest entries average higher than the historical mean, 16KB may capture only 10–15 entries rather than ~40. The brief acknowledges these are "judgment calls" — that's appropriate for explore. But flag this for `design.md`: the hysteresis gap (16KB → 12KB) should be verified against actual entry-size distribution in both repos, not just the mean, or the triggering script should report both the byte count and the entry count it would retain so the operator can calibrate.

3. **Header preservation is implicit, not stated.** The roll script must preserve lines 1–7 of INDEX.md (title, format preamble, separator). The brief's mechanics only describe moving "entry blocks," but the header lines don't match the anchor pattern. This is obvious to a human implementer but worth making explicit so the `design.md` edge-cases section addresses it (e.g., "header lines (everything before the first anchor) stay in INDEX unchanged").

### 💡 Suggestions

1. **Consider making the roll script report what it would do before doing it** (a `--dry-run` or `--check` flag) — the brief says the knowledge_lint finding "names the remedy script" but doesn't say whether the script can preview its actions. A dry-run mode reduces operator anxiety at the point of pressure.

2. **The boot_surface_lint anti-treadmill message could be more specific.** The brief says it will gain "one remedy line — condense/roll first; threshold raises are operator decisions recorded in decisions/INDEX.md." Consider naming the exact command (`python scripts/roll_decisions.py`) in the message so the operator can copy-paste it immediately — the finding message in knowledge_lint would also name the remedy, but boot_surface_lint is the surface that fires the pressure signal.

3. **`knowledge_lint.py` check 4 (dangling archive pointer) should be explicitly verified to cover HISTORY.md.** The brief says "citations are moved verbatim and keep resolving," and notes that `knowledge_lint.py` will scan HISTORY.md as an ordinary knowledge doc — but the dangling-archive-pointer check (check 4) and broken-citation check (check 3) both use repo-wide walks that should pick it up. This is a confidence check for `design.md` verification, not a requirement change.

### Premise Verdict

The problem is real, the root cause is correctly identified, the solution direction (pressure-triggered chronological roll, mechanized via a budget check + deterministic script) resolves the root cause without the treadmill of threshold raises, the judgment cost of topic splits, or the inapplicability of calendar splits. Rejected alternatives are fairly dispatched. The three 🟡 issues above are implementation-detail concerns appropriate for `design.md`, not direction-level defects.

PREMISE: AGREE

### Verdict

PASS — ready to freeze and move to `proposal.md`.

VERDICT: PASS

## Round 2 — tasks.md + delta specs, 2026-07-17, openspec-reviewer @ deepseek-v4-pro (VERDICT: NEEDS REVISION — both 🔴 fixed: 1.4 no-`---` header fallback added; 2.5 re-roll pointer-idempotence + --target-bytes tests added. 🟡 adopted: 1.5b comparison target made explicit; 3.4c override tested both directions; 4.1 remedy line qualified; 💡 adopted: 5.1 README row guidance, status_lint mid-apply note)

All evidence gathered. Writing the review now.

---

## Review Round 2 — tasks.md + delta specs (MEDIUM, tasks-only propose)

### Summary

The task set is mechanically faithful to the verified explore-brief — every element of the proposed direction maps to a concrete, ordered task. The delta specs (`knowledge-organization`, `knowledge-lint`) are consistent with the tasks and with the existing `openspec/specs/` baseline. No D10 drift: the brief's six-point direction (convention, detector, script, anti-treadmill line, self-application, OW-13(b) closure) maps cleanly to tasks 5, 3, 1–2, 4, 6.1–6.3, and 6.3 respectively. Test coverage is strong — byte conservation, continuation lines, idempotence, guards, config fallback, dry-run — with two specific gaps.

The most important concern: task 1.4 assumes INDEX.md headers always end with `---`, but this format element is not guaranteed for downstream repos that will independently run `roll_decisions.py`. Without a fallback, the script's behavior is undefined.

### Premise Verdict

The explore-brief was already reviewed and returned `PREMISE: AGREE`. No drift detected — the tasks solve the stated problem with the stated approach, scope is preserved, and no rejected alternative has crept back in.

PREMISE: AGREE

### 🔴 Blocking Issues

1. **Task 1.4 — Pointer-line insertion assumes a `---` separator with no fallback.** The task says insert the pointer line "immediately after the header's closing `---` separator." The scaffold's own `knowledge/decisions/INDEX.md` does end its header with `---` (line 7), so the self-application in task 6.1 works. But the brief and the delta spec scope this convention to all repos — downstream repos (`psc-monitor`, `extrends`) will run their own rolls during propagation sessions, and their INDEX.md headers are per-repo prose (not scaffold-managed). If a downstream header lacks `---`, the script has no defined behavior — the mechanical apply-executor follows the spec literally and may crash, error, or silently misplace the pointer line. **Fix:** add one sentence to 1.4: "If the header has no `---` separator, append the pointer line as the last line of the header block (immediately before the first entry)."

2. **Task 2.5 — Missing test for pointer-line idempotence on a *re-roll* (not a no-op).** Task 2.5 covers two scenarios: "a second run after a roll reports no-op" (INDEX ≤ target, nothing to do) and "an under-target INDEX is untouched." Both are the no-op path. But task 1.4 guarantees the pointer line is "never duplicated on re-runs" — and the scenario that tests this guarantee is: roll → pointer line added → operator appends entries → INDEX exceeds target again → second roll fires but must NOT add a second pointer line. Task 2.5 does not test this re-roll path. The byte-conservation invariant (1.5b) would catch a duplicated pointer line as a reconstruction mismatch, but a dedicated edge-case test for the explicit "never duplicated" contract is appropriate. **Fix:** add a test case to 2.5: first roll creates HISTORY + pointer line, then append entries to push INDEX over target again, run roll again, assert pointer line appears exactly once in INDEX and HISTORY header is not duplicated.

### 🟡 Should Fix

1. **Task 1.5b — Byte-conservation comparison methodology is slightly ambiguous.** The invariant says "header + retained blocks + moved blocks reconstruct the original INDEX text exactly (compare strings before writing; the only permitted delta is the pointer line of 1.4)." The ambiguity: the "header" in the reconstruction includes the newly-inserted pointer line, which was not in the original. The comparison must either (a) compare against `original_text + pointer_line` or (b) strip the pointer line from the reconstruction before comparing. Either approach works; the task should state which one so the test in 2.3 can assert the correct shape. "The only permitted delta" language signals intent correctly — just needs the comparison target made explicit.

2. **Task 2.5 / 1.1 — No explicit test for the `--target-bytes` CLI flag.** Task 1.1 defines `--target-bytes N` with default `TARGET_BYTES = 12_000`. Task 2.2 tests the basic roll (implicitly using the default). But there is no test that `--target-bytes 8000` causes the roll to target 8,000 bytes. The flag is specified in the CLI contract; a test verifies it works. Add a test (or extend 2.2): run with `--target-bytes N`, assert INDEX ≤ N after roll.

3. **Task 3.4(c) — Override test only covers the "lower-than-default" direction.** The test says "small override flags a small file" — override to e.g. 100 bytes, create a 200-byte INDEX, verify finding. This tests lowering the threshold. But the override can also *raise* the threshold (useful for downstream repos with larger budgets). There is no test for: set `decisions_index_max_bytes = 100_000`, create an 80KB INDEX (would flag at default 16KB, should NOT flag at 100KB), verify no finding. This positive-direction test is important because the psc-monitor propagation scenario (task 6.4) explicitly contemplates repos with different budgets. Add this case to 3.4(c).

4. **Task 4.1 — The remedy line addresses only `decisions/INDEX.md` as the pressure source.** The output line says "remedy: roll knowledge/decisions/INDEX.md oldest entries via: python3 scripts/roll_decisions.py." This is correct for the scaffold's current situation (INDEX is 35.8KB of the 83.9KB total). But boot-surface WARN/FAIL can also be caused by growth in AGENTS.md, STATUS.md, or questions/INDEX.md, for which rolling decisions/INDEX is not a fix. The remedy line is appropriate as the *first* thing to try (it's the dominant and most-frequently-growing component), but an operator whose pressure comes from a different file would find it misleading. Consider qualifying with "If decisions/INDEX.md is the dominant growth, roll oldest entries..." or similar. This is 🟡 because it's a UX issue, not a functional defect — the current pressure is real and the remedy is correct for it.

### 💡 Suggestions

1. **Task 1.2 — Blank-line handling at the end of the last moved block.** The entry-block definition includes "all following lines (including blank lines) up to the next anchor line or EOF." This means trailing blank lines after the last anchor get moved to HISTORY. If the original INDEX ends with a trailing newline (which renders as a blank line in `splitlines()`), that blank line moves to HISTORY. This is mechanically correct but may look odd in HISTORY (trailing blank line after the last entry). Consider trimming trailing empty strings from the moved blocks before appending to HISTORY. Cosmetic only — byte conservation still holds either way.

2. **Task 6.1 — The mid-apply timing note is good; consider also noting `status_lint.py` behavior.** The note on task 3 correctly warns that `knowledge_lint.py` will flag the live tree between task 3 and task 6.1. `status_lint.py` will remain clean (it validates the date-anchor format of remaining INDEX entries, which are unchanged). But HISTORY.md's entries are also valid date-anchor lines — `status_lint.py` deliberately does NOT scan HISTORY.md (per the explore-brief). This is worth a quick note so the apply-executor doesn't panic if they happen to run `status_lint.py` mid-apply. "`status_lint.py` will stay clean — it scans only INDEX.md, and rolled entries keep their valid format."

3. **Task 5.1 — Convention text placement in `knowledge/README.md`.** The README currently has a table row for Decisions (`| Decisions | What did we choose, and why? | knowledge/decisions/INDEX.md ... | on-demand |`). The roll convention should update that row (or add a note below the table) to reflect that INDEX.md is now a rolling window with HISTORY.md. The task says "in the section describing `knowledge/decisions/`" — this could be interpreted as either the table cell or the Usage Notes. The executor would benefit from slightly more direction: "Update the Decisions row of the table to read `knowledge/decisions/INDEX.md` (rolling newest-tail window) and `knowledge/decisions/HISTORY.md` (on-demand older entries), and add ≤3 lines in Usage Notes below explaining the roll convention."

### Verdict

PASS — two 🔴 issues (task 1.4 `---` fallback, task 2.5 re-roll idempotence test) need resolution before freeze. The 🟡 items are important but non-blocking. The overall design is sound.

VERDICT: NEEDS REVISION

## Round 3 — tasks.md + delta specs, 2026-07-17, openspec-reviewer @ deepseek-v4-pro (VERDICT: PASS; its one 🟡 — 1.5b strip-only-when-this-run-inserted on re-roll — fixed before freeze, with the 💡 wording adopted)

All data gathered. Writing the review.

---

## Review Round 3 — tasks.md + delta specs

### Summary

All six round-2 findings are addressed concretely — the 🔴 fixes (1.4 `---` fallback, 2.5 re-roll idempotence + `--target-bytes` test), the 🟡 items (1.5b comparison target, 3.4c both-direction override test, 4.1 qualified remedy line, section 3 `status_lint` mid-apply note), and the 💡 items (5.1 README table-row update, flow clarifications). The delta specs remain clean and consistent with the existing `openspec/specs/` baseline. No scope creep and no drift from the explore-brief.

The one new issue: task 1.5b's byte conservation comparison, now made explicit in the round-2 fix, works mechanically for the first-roll case but is inconsistent with the re-roll scenario that task 2.5 now tests — on a re-roll the original INDEX already carries a pointer line from a prior roll, so stripping it from the reconstruction before comparing against the original produces a mismatch of exactly that pointer line. A competent implementer will surface this when the 2.5 re-roll test hits the byte conservation guard, but the spec should not hand over a known inconsistency.

### 🔴 Blocking Issues

None.

### 🟡 Should Fix

1. **Task 1.5b — Byte conservation comparison is correct for first roll, inconsistent with re-roll.** The comparison subtracts the pointer line from the reconstruction before comparing against the original. On the first roll, the original INDEX has no pointer line, so `(new INDEX − pointer) + moved = original` holds. But on a re-roll (task 2.5), INDEX already carries a pointer line from round one — the original text includes it — but the reconstruction strips it, so the equation fails by exactly `len(pointer_line)` bytes. The re-roll test in 2.5 will surface this; the spec should pre-empt it. **Fix:** either (a) qualify the comparison so it only strips the pointer line when it wasn't already in the original, or (b) change the comparison to compare `header` + `sorted(entries)` rather than the full file text, so the pointer line is orthogonal. Either is one sentence.

### 💡 Suggestions

1. **Task 1.5b wording — "the blocks appended to HISTORY" is slightly ambiguous.** Could be read as the full post-append HISTORY content vs. the delta blocks moved in this roll. The comparison target (equals `original INDEX text`) makes the intent clear — it must be the delta — but a single qualifying word (`"newly appended"` / `"the blocks this run appended"`) would eliminate the ambiguity without changing the substance.

### Verdict

PASS — one 🟡 byte-conservation re-roll inconsistency the implementer will surface naturally, but worth fixing now rather than during apply. The round-2 fixes are all correctly applied. No 🔴 issues remain.

VERDICT: PASS

### Premise Verdict

The explore-brief was already AGREE via round 0. The tasks faithfully implement its six-point direction — no drift, no scope shift, no rejected alternative has crept back in.

PREMISE: AGREE
- None

## Verify round — 2026-07-17 (orchestrator self-review + pro behavioral pass + simplicity gate)

Self-review: full-diff read, check.sh green, live-roll byte-reconstruction exact vs HEAD, six orchestrator adversarial fixtures pass (no-`---` header, positional no-sort, exact-budget boundary, --target-bytes 0, orphan pointer, live-copy re-roll). One counts-rule wording defect in two doc edits, fixed inline (trivial). Simplicity gate (/code-review low): one accepted torn-write finding (git-recoverable; rationale in notes.md field 3). Security gate: not triggered.

## Verify Pass — deepseek/deepseek-v4-pro
VERDICT: READY
### Defects
- None

---

**Evidence summary** (what the verdict is based on, for the change's `notes.md` verify checkpoint):

| Criterion | Result |
|---|---|
| `bash scripts/check.sh` (ruff + pytest) | **665 passed, 0 failures, 14.67s** |
| `roll_decisions.py --dry-run` on live tree | no-op (11,773 ≤ 12,000 target) |
| `roll_decisions.py` idempotency | second run produces same no-op |
| Anchor conservation (git HEAD → INDEX+HISTORY) | **88 = 24 (INDEX) + 64 (HISTORY)** — exact |
| Boundary continuity (HISTORY last → INDEX first) | `sonnet-first-pre-route` → `checks.py-universal-builtins` (entries #64→#65 of git HEAD, continuous) |
| `boot_surface_lint.py .` | **OK — 59,851 bytes** (was WARN at 83,925 pre-roll; now well under 80,000 threshold) |
| `knowledge_lint.py` | **OK** — clean on rolled tree |
| `status_lint.py .` | **OK** — clean |
| `openspec validate roll-decisions-index --type change --strict` | **valid** |
| `test_roll_decisions.py` (11 tests) | **11 passed** |
| `test_knowledge_lint.py` decisions-index-budget (9 tests) | **9 passed** |
| `test_knowledge_lint.py` invalid-override (3 tests, string/negative/bool) | **3 passed** |
| `test_boot_surface_lint.py` (12 tests, incl remedy-line) | **12 passed** |
| External-API surface | **None** — pure local file I/O, confirmed by grepping diff for network patterns (zero hits) |
