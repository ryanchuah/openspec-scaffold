# Review log — checks-facts-split

## Round 1 — tasks.md — 2026-07-03 — deepseek-v4-pro

Now I have comprehensive context from reading all relevant files. Let me synthesize my findings.

---

## Review Round 1 — tasks.md

### Summary

The `tasks.md` is thorough in coverage — every requirement from the explore-brief and notes.md maps to a task. The trichotomy vocabulary and file organization are clearly communicated. However, there are three 🔴 blocking issues: (1) wrong line numbers in task 3.2 that would send the implementer to unrelated code; (2) the interaction between `facts.py` execution and the engine's preflight mechanism is undefined, creating a direct contradiction with the acceptance criteria; and (3) as a consequence, `facts.py`'s contract with the engine (`_mode_multi` vs. direct `_execute_check` loop) is left unspecified, so the implementer must guess.

---

### 🔴 Blocking Issues

1. **Task 3.2 — wrong line numbers for `knowledge_lint.py` config-read sites.** The task says: `"3 sites, ~lines 106/120/290."` I verified:
   - **Line 106** is `"audit-log.md": "knowledge/audit-log.md",` — a canonical-map entry for the *audit log*, not the `audit.toml` config file.
   - **Line 120** is `EPHEMERAL_PATHS: tuple[str, str] = ("knowledge/HANDOFF.md", "knowledge/audit-log.md")` — ephemeral path definitions, also about `audit-log.md`, not `audit.toml`.
   - **Line 290** is the actual config-read: `config_path = root / "audit.toml"`.

   An implementer following these line numbers would waste time hunting for `audit.toml` at lines that contain `audit-log.md` references instead — or worse, change those strings, breaking the audit-log registry check (canonical mapping and ephemeral-path handling). The actual `audit.toml` prose references are at lines 25, 61, and 286 (docstrings), plus the code at line 290; the test-file fixtures are at `test_knowledge_lint.py` lines 202, 216, 232.

2. **Task 1.4 — `facts.py` preflight contract undefined, contradicts acceptance criteria.** The task says `facts.py` is "a thin CLI over the engine imported from `scripts/checks.py`" and that it "exits 0 once arguments parse; per-fact tool degradation (e.g. radon absent) is recorded in the JSON as today, never a process failure" (matching notes.md acceptance criterion #3: "facts.py in a tmp git repo exits 0 with radon absent"). But task 2.2 adds **preflight** to `_mode_multi`: BEFORE executing any check, compute availability; if any selected+enabled check is unavailable, print messages and exit 3 with **nothing executed**.

   If `facts.py` calls `_mode_multi` (the natural interpretation of "thin CLI over the engine"), preflight would fire for fact-family checks when radon is absent → `facts.py` exits 3, violating the "always exit 0" contract. The task does **not** specify:
   - Whether `facts.py` calls `_mode_multi` at all
   - Whether it calls `_execute_check` directly in a loop with no availability check
   - Whether it has its own multi-fact loop that skips preflight
   - How `out_dir` is set to `output/facts/` (the engine currently writes to whatever `out_dir` is passed to `_mode_multi` or `_mode_check`)

   Without this specification, the implementer must guess, and the wrong guess produces a hard-to-detect acceptance-criteria violation discovered only at verify time.

3. **Task ordering: 1.4 (create `facts.py`) executes BEFORE 2.2 (add preflight to engine).** Even if the implementer guesses the right contract for task 1.4, the engine's `_mode_multi` signature and behavior change in section 2. If `facts.py` is written against the pre-section-2 engine, it may silently break or need rework after section 2 lands. The sequential executor needs either: (a) a warning that `facts.py` must be checked/retested after section 2, or (b) tasks reordered so engine changes (section 2) come before the `facts.py` creation that depends on them. This is a consequence of issue #2 — resolve the contract and this ordering concern disappears.

---

### 🟡 Should Fix

4. **Task 7.1 (SKILL.md rewrite) bundles ~4 hours of work into one task.** The task includes: (a) command-string renames everywhere, (b) trichotomy documentation for `--report` running both families, (c) preflight semantics and install-or-disable decision docs, (d) day-to-day entry points (`facts.py`) explanation, (e) staleness-cadence from `audit_anchor.commits_since`, (f) annual "re-justify the suppression baseline" reminder, and (g) frontmatter description path updates. This is the most complex single task in the list; splitting it into two tasks (e.g. 7.1a command-rename + 7.1b prose rewrite) would reduce the surface area and make review easier.

5. **Task 7.4 ("Repoint stragglers") is underspecified — it says "fix live references" but doesn't list the specific files.** The `grep` instruction is a discovery mechanism, not a specification. The actual straggler files (verified live) include: `knowledge/reference/exit-codes.md` (line 9: `audit_bundle.py` → `checks.py`), `knowledge/reference/resync-verification.md` (line 60: `audit.toml`), `knowledge/README.md` (line 16: `output/audit/<date>/`), `knowledge/STATUS.md` (lines 12, 68), `knowledge/questions/run-audit-untested.md` (lines 5, 7, 14), `knowledge/questions/deterministic-tooling-layer-follow-ons.md` (line 41), `knowledge/questions/audit-skill-metadata-cleanup.md` (line 7), and `openspec/config.yaml` rules block (line 9: context string still says "audit" — though this is the `context:` block which is per-repo, not `rules:`). The task should enumerate these so the sequential executor knows where to look. (Note: AGENTS.md and the SKILL.md are already covered by tasks 7.1–7.2, and the explore-brief explicitly excludes `knowledge/decisions/INDEX.md` from updates.)

6. **Task 6.4's `audit_anchor` test setup is partially specified.** It says "init a tmp git repo, tag, count" but doesn't state whether the test fixture needs to be a full git repo with an `audit/*` tag (i.e. `git tag audit/2026-01-01`) or just any tag. The `audit_scope._latest_audit_tag` function referenced in task 1.5 probably expects a specific tag format. The test should be explicit about the tag naming convention so the test doesn't pass accidentally with a wrong tag prefix.

---

### 💡 Suggestions

7. **Task 1.2 — `family` assignment for `scope` changes `--floor` behavior.** Scope is currently tier `"floor"`, and `--floor` runs all floor-tier checks. After assignment `family: "fact"` and task 1.3's `--floor` filter (`family == "check"` only), scope will no longer run in `--floor`. This is intentional per the explore-brief (scope is a fact-generating metric, not a detector), but the task doesn't call it out. A one-line note would help the implementer understand the behavioral change.

8. **Task 1.3 says `--list` is "unchanged (list gains a FAMILY column)."** "Unchanged" and "gains a column" are slightly contradictory. Consider: "`--list` keeps the same shape but gains a FAMILY column."

9. **Task 1.4's `--list` for `facts.py` is underspecified.** It says "`--list` (fact family only)" — but the current `_mode_list` in the engine prints *all* checks. Does `facts.py --list` filter locally, or does the engine gain a family-filter parameter? This is minor because `facts.py` can filter after calling or replicate the list format, but it should be explicit.

10. **Task 6.1 — the `git mv` of test file needs an import-path update caveat.** The current test uses `import audit_bundle  # noqa: E402` (verified at line 28 of `test_audit_bundle.py`). After rename to `test_checks.py`, the import should become `import checks`. The task says "update imports" generically; a specific mention of the self-import pattern would reduce ambiguity.

---

### Premise Verdict (assessing direction — `tasks.md` as the sole propose artifact for MEDIUM tier)

This `tasks.md` is directionally aligned with the verified explore-brief — it faithfully implements the checks/facts/audit trichotomy, the preflight requirements, and the self-explaining-failure contract. No drift detected.

PREMISE: AGREE
- None

---

### Verdict

NEEDS REVISION — address 🔴 issues #1 (wrong line numbers in 3.2) and #2 (undefined facts.py/preflight contract) before proceeding to apply. Issue #3 resolves automatically once #2 is fixed (the ordering concern disappears when the contract is explicit).

## Round 2 — tasks.md — 2026-07-03 — deepseek-v4-pro

Confirmed. Now I have everything needed. Let me emit the review.

---

## Review Round 2 — tasks.md (checks-facts-split)

### Summary

The revision cleanly resolved all three round-1 🔴 blocking issues: knowledge_lint line numbers are now correct and explicitly exclude the audit-log.md lines (106/120); the `facts.py`/preflight contract is explicit (direct `_execute_check` loop, never calls `_mode_multi`); and task ordering places engine changes (sections 1–2) before `facts.py` creation (section 3). The task list is thorough and maps to every acceptance criterion in `notes.md`. However, one new 🔴 line-number defect was introduced in task 7.5, and a 🟡 manifest-ordering fragility around `test_facts.py` should be addressed.

---

### 🔴 Blocking Issues

1. **Task 7.5 — `openspec/config.yaml` wrong line number (9 → 5).** The task says `"openspec/config.yaml:9 (context-block mention of the audit layer — this repo's own per-repo context, safe to update here)."` But `config.yaml` line 5 is the actual audit-layer mention (`"Purpose: ...deterministic audit + scaffold-lint tooling..."`), while line 9 is about Web research conventions and contains zero mention of the audit layer. An implementer following line 9 would either find nothing to change or (worse) modify the Web research rule. **Correct reference: line 5.**

---

### 🟡 Should Fix

2. **Task 5.2 adds `scripts/test_facts.py` to manifest before it exists (created in 6.3).** `scaffold_lint.py`'s `check_manifest_completeness` verifies every manifest entry exists on disk (confirmed at lines 250–254). For a strictly sequential executor who doesn't run intermediate tests, this is harmless — the file exists by the time task 6.6 runs the full suite. But it violates the spec's "manifest SHALL list only files that exist" invariant in the intermediate state, and would produce a false `manifest-completeness` failure if any test run happens between 5.2 and 6.3. **Fix:** either add a parenthetical note in 5.2 (`"(test_facts.py created in 6.3; final suite confirms completeness)"`) or move the `test_facts.py` manifest entry addition to task 6.3.

---

### 💡 Suggestions

3. **Task 4.2 labels lines 202 and 216 as "fixtures" — they are a comment and an assertion.** The line references are correct (both are part of the per-repo config test section that references `audit.toml`), but the label "fixtures" is misleading. Consider: `"update the test code at lines 202, 216, and 232 (the per-repo config section that references audit.toml)."`

4. **Task 5.3 assumes `scaffold_manifest_removed.txt` exists** — it does (confirmed: lists `openspec-onboard` from a prior portfolio change), but the task doesn't state that dependency. Since change B (which creates the removal logic) is a prerequisite per the explore-brief, a brief note would help: `"(file exists from change B; append to it)"`.

---

### Verdict

NEEDS REVISION — address 🔴 issue #1 (wrong line number in task 7.5 for `openspec/config.yaml`) before proceeding to apply. Issues #2–4 are non-blocking.

---

### Premise Verdict

```
PREMISE: AGREE
```
- **Root, not symptom**: AGREE — the tasks implement the three-tier (checks/facts/audit) layering diagnosed in the explore-brief; no reframing.
- **Solution targets root**: AGREE — engine split into checks.py + facts.py, preflight with self-explaining failures, cache-semantics facts surface, all per the brief.
- **Scope right-sized**: AGREE — no scope creep or shrinkage relative to the brief's change A definition.
- **Blind spots**: None. The one line-number defect is mechanical, not directional.
- **Drift (D10)**: No drift from the verified explore-brief — no reframed problem, no ruled-out approach, no scope expansion.
- **Drift (D11)**: Not applicable (propose, not explore altitude).

## Round 3 — tasks.md — 2026-07-03 — deepseek-v4-pro

Good — the existing `openspec/specs/knowledge-lint/spec.md` confirms task 7.4's delta spec has a valid base. `scaffold_manifest_removed.txt` exists on disk, validating task 5.3's claim. Now I have everything needed to confirm the four edits and rule out regressions.

---

## Review Round 3 — tasks.md (final)

### Summary

All four round-2 fixes are correctly applied. Every edited line number was spot-checked against the live source files — all correct. No new defect was introduced by the four edits. The `tasks.md` is now free of 🔴 blocking issues and the 🟡 findings from round 2 are all resolved.

### 🔴 Blocking Issues
None.

### 🟡 Should Fix
None.

### 💡 Suggestions
None.

### Verdict

**PASS — ready to freeze and proceed to apply.**

---

### Fix Verification (round-2 → round-3)

| Round-2 Finding | Fix Applied | Verified |
|---|---|---|
| 🔴 7.5: `config.yaml:9` → `:5` | Now `openspec/config.yaml:5` + "do NOT touch the Web-research rule at line 9" | Line 5 live-verified: contains `"deterministic audit + scaffold-lint tooling"`; line 9 is indeed the Web-research rule |
| 🟡 5.2: manifest names `test_facts.py` before it exists | `test_facts.py` removed from 5.2; added to 6.3 alongside file creation | 5.2 now says "Do NOT add...deferred to 6.3"; 6.3 says "in the same task add...deferred from 5.2" |
| 🟡 4.2: misleading "fixtures" label | Reworded to `"(the per-repo config section referencing `audit.toml`)"` | Confirmed — no longer says "fixtures"; line refs 202/216/232 all verified against live `test_knowledge_lint.py` |
| 🟡 5.3: doesn't state `manifest_removed.txt` pre-exists | Added `"(exists from the sync-deletion-manifest change — append, don't create)"` | File confirmed on disk at `scripts/scaffold_manifest_removed.txt` |

### Premise Verdict

```
PREMISE: AGREE
```
- None (direction unchanged from rounds 1–2; no drift detected).
