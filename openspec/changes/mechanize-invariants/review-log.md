# Review log — mechanize-invariants

## Round 1 — tasks.md + notes.md — deepseek-v4-pro — 2026-07-02

## Review Round 1 — `tasks.md` + `notes.md` (mechanize-invariants)

### Summary

The tasks cover the five invariants from the explore-brief correctly, and the notes.md documents all direction-gate resolutions. Overall structure is sound. However, there are **three 🔴 blocking issues** that would cause rework during implementation — the most serious being a claim in task 1.3 that the check detects anchor duplicates, while the `sync_scaffold.py` functions it reuses only detect anchor *presence*, not *uniqueness*. The test in task 2.1 expects duplicates to be flagged, creating a direct contradiction between the implementation approach and the acceptance test. Two other 🔴 issues concern underspecified parsing in task 1.6 and a missing scan-surface exclusion for `_shared/` files in task 1.6.

No D10 drift detected against the `plans/succession-hardening/explore-brief.md` — the problem, scope, and approach are faithful to the brief.

---

### 🔴 Blocking Issues

1. **Task 1.3 anchor-uniqueness gap vs. task 2.1 test expectations.** Task 1.3 claims the `agents-md-structure` check verifies each anchor "exactly once". It directs the implementer to "REUSE `scripts/sync_scaffold.py`'s existing anchor/no-tail logic by importing it — e.g. run its AGENTS.md span extraction against the scaffold's own file and convert any `ValueError` into a finding." But `sync_agents_md()` (the function that contains the anchor logic) uses `re.search` — it detects the *first* match, not the count. Duplicated anchors (e.g., two `## Roles` headings) would NOT raise `ValueError` — `re.search` finds the first and stops. Meanwhile task 2.1 explicitly lists "anchor duplicated" as a violating fixture that should produce a finding. **If the implementer follows the literal instructions in 1.3 (import and call `sync_agents_md`), the "anchor duplicated" test in 2.1 will fail** because the reused function doesn't catch it. The implementer must either (a) add their own count-based check on top of the imported logic (checking `text.count(anchor)` for each anchor pattern), or (b) clarify that uniqueness is a separate check not covered by the reused functions. Either way, task 1.3's text as written is misleading about what the re-used function provides.

2. **Task 1.6 (budget-agreement): the sanctioned-pair parsing algorithm is underspecified for a flash-tier executor.** The task says "the set of sanctioned pairs is parsed from the `timeout` flags column (backtick-quoted `` `-k <G> <B>` `` cells) of the §e table." The table has 5 columns with pipe separators; the `timeout` flags are backtick-quoted cells like `` `-k 30 600` ``. But the task does not describe a parsing algorithm — it doesn't say whether to use a regex over the raw markdown, split on pipes, or something else. A flash executor trying to implement "parse a Markdown table" from this one-sentence spec will likely guess wrong (e.g., splitting on `|` naively breaks on the §c section's inline code spans containing pipes). The embedded-pair-finding regex (`timeout\s+-k\s+(\d+)\s+(\d+)`) is well-specified; the sanctioned-pair parsing is not. **Add a concrete parsing strategy** — at minimum, name the column index (column 3) and the regex to use on table rows (`\|.*\x60-k (\d+) (\d+)\x60` on each row that looks like a table data row). The fallback ("yields zero pairs → finding") is a good safety net but shouldn't be the primary way to detect parse failures.

3. **Task 1.6 (budget-agreement): `_shared/` files are NOT excluded from the scan, but the delegation-harness itself contains the sanctioned pairs — creating a self-referential scan.** The task says to scan "the same file set as 1.5" (AGENTS.md + every `.md` under `.claude/skills/`, `.claude/agents/`, `.opencode/agents/`). `.claude/skills/_shared/delegation-harness.md` is under `.claude/skills/` and would be scanned. It contains both the §e table (the source of sanctioned pairs) AND backtick-quoted cells like `` `-k 30 600` ``. The embedded-pair regex `timeout\s+-k\s+(\d+)\s+(\d+)` would NOT match backtick-quoted text, so this is safe. BUT: the harness doc also contains the raw regex `timeout -k <grace> <budget>` in §c prose, which has angle-bracket placeholders and would NOT match `\d+`. So in practice this is safe. However, **the task doesn't acknowledge this self-referential case**, and a cautious implementer might add a special carve-out or waste time worrying about it. Clarify in the task that the harness file's backtick-quoted and angle-bracket placeholder forms won't match the embedded-pair regex, so no special exclusion is needed.

4. **Task 1.5 (dangling-skill-refs): the token `lint-knowledge` is in the literal scan list, but it is also a skill directory name — causing a false-negative on the `openspec-*` match path.** This is NOT a bug — it's intentional that `lint-knowledge` is a separately-enumerated token. But the task says "plus the literal token `lint-knowledge`" without explaining WHY it's special-cased (it doesn't start with `openspec-`). For a flash executor who might wonder "should I also scan for `apply-executor` as a literal?" — clarify that `lint-knowledge` is the ONLY non-`openspec-*` skill-name token that needs literal scanning, because all other skill names match the `openspec-*` pattern.

---

### 🟡 Should Fix

1. **Task 2.3 (live-repo test) is order-sensitive and fragile.** It runs `scaffold_lint.py` against the real repo and asserts zero findings. This test will pass ONLY after task 2.2 fixes the live violation. But if ANY later task in the sequence (or a concurrent edit outside this change) introduces a new violation, the test breaks. The task's safety valve ("STOP and report it as a blocker") is good, but the test itself is inherently fragile — it's a snapshot of repo state at a point in time. Consider either (a) making the live-repo test tolerant of known-excluded findings that aren't the 2.2 fix, or (b) explicitly noting in the test docstring that this test is a SEAL — once it passes, no further instruction-file edits should introduce new violations without updating the test.

2. **Task 3.1 (hook-wiring warning) and stderr assertion compatibility.** The task says "If existing `test_sync_scaffold.py` tests assert on captured stderr, update only those assertions." I reviewed `test_sync_scaffold.py` (823 lines) and found NO tests that capture or assert on stderr content — the existing tests use `self.assertRaises(SystemExit)` which discards stderr. The precaution is correct but the warning about updating assertions may confuse the implementer who can't find any to update. Consider noting "no existing stderr assertions were found — if that changes, update them."

3. **Task 4.1 and 4.2 are redundant.** Task 4.1 says "create `scripts/test-cmd` containing `python3 -m pytest -q` ... run `scripts/test-gate.sh` once and confirm it prints `tests passed`." Task 4.2 says "Run the full suite `python3 -m pytest -q` from the repo root and confirm it is green." Since `test-gate.sh` runs `python3 -m pytest -q` (via `test-cmd`), 4.1 already implicitly runs the full suite. Task 4.2 adds nothing new. Either merge them or make 4.2 a distinct check (e.g., verify `test-gate.sh` was the coverage, and 4.2 is a direct `pytest` run to cross-check the gate script itself).

4. **Task 1.2 (manifest-completeness) glob for `scripts/*` uses "plain files only, not dirs" — but this filter isn't needed for the skill/agent globs and isn't explained.** The `scripts/*` glob has a "plain files only" qualifier because `scripts/` contains subdirectories. The skill globs (`.claude/skills/*/SKILL.md`) inherently filter to files. This is correct but the asymmetry in description could confuse. Add a brief note: "the `scripts/*` glob needs the plain-files-only filter because `scripts/` mixes files and dirs; the skill/agent globs are inherently file-only."

---

### 💡 Suggestions

1. **Task 1.5 scan set could explicitly exclude `_shared/`. `delegation-harness.md` is a mechanical reference, not an instruction surface — scanning it for dangling skill refs is harmless but wastes cycles.** Consider excluding it or noting it's low-value.

2. **Task 1.6's fallback "If the harness table yields zero pairs, that itself is a finding" could fire on a real parse failure vs. an empty table.** The two cases are distinguishable (parse failure → the table rows were found but no pairs extracted; empty table → no §e section at all). For better diagnostics, distinguish them.

3. **The notes.md acceptance criteria include a "seeded-violation probe" (criterion 3) that requires temporarily editing the real repo.** This is a good behavioral check but relies on the verifier creating and reverting temporary edits. Note in the criterion that after each probe the edit MUST be reverted before proceeding.

---

### Verdict

**NEEDS REVISION** — address 🔴 issues 1, 2, and 3 before proceeding. Issues 1 and 2 directly affect implementability for a flash executor; issue 3 is a self-referential scan edge case that should be documented to avoid wasted cycles.

---

### Drift Check (D10)

No drift detected against `plans/succession-hardening/explore-brief.md`:
- Problem: enforcement gap for prose-only invariants — faithfully reflected.
- Scope: manifest completeness, AGENTS.md/config anchors, dangling refs, budget agreement, commit-gate arming, sync-time warning — all present, no additions.
- Approach: deterministic checks + reuse of `sync_scaffold.py` functions — followed.
- The "exactly once" uniqueness check in task 1.3 is a minor implementation-level addition beyond the brief's "anchor invariants" language, but is a reasonable detail, not scope drift.

## Round 2 — tasks.md + notes.md — deepseek-v4-pro — 2026-07-02

## Review Round 2 — `tasks.md` + `notes.md` (mechanize-invariants)

### Summary

Round 2 is a substantial improvement over Round 1. All three 🔴 blocking issues from Round 1 have been resolved: the anchor-uniqueness check is now an explicit count-based sub-check separate from the reused extraction function (task 1.3), the §e table parsing algorithm is specified line-by-line (task 1.6), and the self-referential harness-scan case is documented as needing no exclusion (task 1.6). The task granularity is appropriate, the dependency order is sound, and the acceptance criteria in `notes.md` are testable and comprehensive.

No 🔴 blocking issues remain. There are three 🟡 items worth addressing — two concern underspecification that a flash executor could stumble on, and one concerns the NON-CONVERGENCE BLOCKER's surface mechanism. Three 💡 suggestions follow.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **Task 1.3(a) — counting method for `> **MANDATORY` is ambiguous.** The task specifies "line-start anchors counted per-line via `startswith`" for `## Roles` and `## After reading this file`, but for `> **MANDATORY` it only says "count occurrences in AGENTS.md." The implementer could use `str.count()` (which would match substrings inside code blocks) or per-line `startswith()`. In practice `> **MANDATORY` only appears once at line-start, but an executor who picks `str.count()` and later encounters a quoted appearance in a fenced code block would get a false positive. **Recommendation:** specify the same per-line `startswith()` method for `> **MANDATORY` (it does appear at line-start in the real file), or explicitly state `str.count()` is acceptable.

2. **Task 1.4 — "trailing-key validation by import" is underspecified.** The task says to reuse `sync_scaffold.py`'s trailing-key validation by import, but does not name the function (`sync_config_yaml`) or describe the calling pattern (pass the config text as both scaffold and target, catch `ValueError`). A flash executor who hasn't read `sync_scaffold.py` source will need to discover the mechanism by code-reading — and the natural first guess (calling `_extract_rules_block` and then writing their own trailing-key check) bypasses the reuse goal. **Recommendation:** explicitly name `sync_config_yaml` and the call pattern, mirroring the level of detail in task 1.3(b).

3. **Task 2.3 — NON-CONVERGENCE BLOCKER surface mechanism is unspecified.** The task says "STOP and report it as a blocker (`### NON-CONVERGENCE BLOCKER` per your agent instructions)." But the apply-executor runs autonomously — at minimum, it needs to know WHERE to write/dump this finding so the orchestrator can see it after the executor terminates. The `### NON-CONVERGENCE BLOCKER` heading suggests a format, but not a destination (stdout? a file under the change dir? the agent's return message?). A flash executor hitting this gate could silently exit or bury the finding in a large test log. **Recommendation:** specify that the blocker report goes to `openspec/changes/mechanize-invariants/notes.md` (append a `## NON-CONVERGENCE BLOCKER` section) AND to the executor's final return message — the two-surface approach guarantees the orchestrator sees it regardless of how it reads executor output.

---

### 💡 Suggestions

1. **Task 1.5 — `_shared/` files are in the scan set but aren't instruction surfaces.** The dangling-skill-refs scan includes `.claude/skills/_shared/*.md` because the glob `.claude/skills/*/SKILL.md` doesn't cover `_shared/`. The delegation-harness is a mechanical reference doc; if it contains a skill token as an example (not a directive) that changes name later, the scan would flag it. This is harmless in practice (the allowlist catches valid refs), but for completeness you could either (a) explicitly note that `_shared/` files are intentionally included and expected to stay clean, or (b) exclude them. Either way is defensible.

2. **Task 1.6 — prose-only timeout references are not caught, and that's by design but not stated.** The embedded-pair regex requires the literal `timeout` prefix. If an instruction file says "the sanctioned budget is `-k 15 780`" without the `timeout` prefix, it won't match. This is correct for the check's purpose (catching copypasted shell commands, not descriptive prose), but stating this intent explicitly would help the executor understand the regex choice and avoid scope-creeping it.

3. **Task 2.1 — missing-anchor case for uniqueness sub-check is not explicitly tested.** The test list includes "anchor renamed" (which triggers both uniqueness count=0 AND presence-not-found) and "anchor duplicated" (which triggers uniqueness count>1). But there's no explicit "anchor completely deleted" test case. The renamed-anchor test likely covers this (a renamed heading wouldn't `startswith`-match the original), but an explicit one would be more thorough, especially since the uniqueness check and presence check use different mechanisms. The live-repo test (2.3) is the ultimate guard here.

---

### Verdict

**PASS** — ready to freeze and move to implementation. No 🔴 issues block the apply-executor from producing correct, complete work. The three 🟡 items are refinements worth addressing but the tasks are implementable as-is; a flash executor who reads the referenced source files (`sync_scaffold.py`) would resolve the underspecification on their own. The 💡 items are polish.

**Disposition:** PASS with zero 🔴 → frozen. All three 🟡 and all three 💡 applied to tasks.md before freeze (startswith counting for all anchors; sync_config_yaml named with call pattern; blocker two-surface destination; _shared inclusion note; timeout-prefix intent note; anchor-deleted fixture).

**Post-freeze correction (orchestrator, 2026-07-02):** tasks 4.1/4.2 and notes criterion 1 pinned `python3 -m pytest -q`, which does not resolve on this machine (pytest is user-installed for python3.13 only; `pytest -q` → 198 passed). Replaced with `pytest -q`. Environment fact-fix only — no scope or behavior change.
