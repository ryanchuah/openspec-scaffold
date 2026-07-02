# Review log — deterministic-tooling-layer

## Round 1 — tasks.md (deepseek-v4-pro via opencode run, 2026-07-02)

## Review Round 1 — `tasks.md`

### Summary

`tasks.md` is **well-constructed and thoroughly specified** for a MEDIUM-tier change. Every task maps to concrete acceptance criteria in `notes.md`, all D1–D9 design decisions from the direction-gated `explore-brief.md` are pulled forward, and the shared exit-code contract (0/2/3) is consistently applied. There is **zero drift** from the verified explore-brief — no reframed problem, no ruled-out approach resurrected, no scope expansion. The four scripts are well-decomposed with detailed CLI contracts, output formats, and test coverage.

However, three blocking ambiguities would cause the apply-executor to guess — and guessing on these specifics would propagate wrong behavior into the entire downstream ecosystem (wrong hotspot rankings, broken baseline diffs across sessions, silent version mismatches). Fix these and the artifact is ready to freeze.

---

### 🔴 Blocking Issues

1. **Task 1.1 — Hotspot formula ambiguity: "max complexity in file"**  
   The hotspot score formula is `churn × (1 + max complexity in file, or 1 when unavailable)`. But `radon cc -j` outputs **per-function** cyclomatic complexity — a file may have 20 functions each with a different McCabe score. "Max complexity in file" could mean:
   - The **maximum** cyclomatic complexity of any single function in the file (most useful for hotspot detection)
   - The **average** complexity across all functions
   - Some radon aggregate like the "block" score
   
   The implementer will guess, and two different guesses produce different hotspot rankings. **Specify exactly which radon metric to extract** (e.g., "the maximum `complexity` value across all function entries in radon's JSON output for that file"). This affects audit_scope.py, the test fixtures in task 1.4, and every downstream audit that uses hotspot ranking to prioritize review attention.

2. **Task 4.3 — Version probe mechanism underspecified: `<tool> --version|version`**  
   The pipe notation `--version|version` is ambiguous. Does the bundle try `--version` first and fall back to `version` on failure? Does it try both and compare? What if `--version` succeeds but returns `v1.0` while the pinned format is `1.0.0`? The task says "mismatch naming expected vs found" but doesn't say what constitutes a match (exact string? prefix? semver?). **Specify the probe protocol explicitly**: e.g., "try `<tool> --version`; if exit ≠ 0, try `<tool> version`; if both fail, tool is unavailable; parse the stdout for a version string (capture group `\d+\.\d+\.\d+`) and compare exact-match to the pinned string." This affects the bundle's reliability guarantee (D9) — a mis-parsed version means a drifted binary runs silently.

3. **Task 4.6 — Baseline fingerprint joining convention not specified**  
   The fingerprint is "sha1 of `(check, rule, path, whitespace-normalized message)`" but the tuple-to-bytes encoding isn't specified. If one implementer joins with `\n` and another with `\t`, two bundles produce different hashes for the same finding, breaking baseline portability across sessions and agents. **Specify the joining convention**: e.g., "join the four components with the null byte `\0` (or tab `\t`) before hashing; whitespace-normalize the message to single spaces." Also clarify: is `check` the check name (e.g., `ruff`) or the tool name? Is `rule` the ruff rule code (e.g., `F401`) or something else? The task says "normalized-findings `{check, rule, path, line?, message}`" in 4.2, so these component names are established — make the mapping explicit.

---

### 🟡 Should Fix

1. **Task 2.1 — Recursive `*.sql` discovery ambiguous**  
   "For each `*.sql` file in the checks dir (sorted by name)" — does this include subdirectories? If someone organizes checks as `checks/integrity/`, `checks/dupes/`, etc., the current wording implies a flat directory. The explore-brief D4 says "~5 deliberate checks per repo, grown from incidents" — a flat dir is probably fine for that scale, but the ambiguity should be resolved. Either state "flat directory only" or specify `glob.glob("**/*.sql", recursive=True)`.

2. **Task 2.1 — No connection timeout for `psql`**  
   The shared exit-code contract (3 = infrastructure failure) covers connection failures, but there's no timeout. A hung `psql` process (e.g., waiting on a lock, or network partition) would hang the entire bundle run indefinitely — violating the "stop-on-first-failure" contract by never failing at all. Add a timeout (e.g., `statement_timeout` via `PGOPTIONS` or subprocess timeout).

3. **Task 4.2 — Inventory `getenv` regex is imprecise**  
   The pattern `os.environ|getenv|process.env` uses `|` which in regex means `os.environ` OR `getenv` OR `process.env`. The bare `getenv` would match accidental occurrences in comments or variable names (e.g., `my_getenv_wrapper`). Also misses `os.environ.get()` if the regex isn't anchored. Recommend: `os\.environ|os\.getenv\b|process\.env` or a more precise pattern. Minor — this is a snapshot, not a gate — but imprecise env-var extraction undercuts the inventory's utility.

4. **Task 4.4/4.6 — `--out` directory collision behavior unspecified**  
   What happens when `--out` points to an existing directory from a prior run (non-resume)? Overwrite, merge, or error? The task says `--resume` reads from existing output, implying the directory persists — but a fresh `--report` run with the same `--out` could silently overwrite prior findings (losing the baseline needed for D6). Specify: either auto-increment (e.g., `output/audit/<date>-<n>/`) or refuse to overwrite with an error suggesting `--resume`.

5. **Task 4.2 — Custom check exit code default not specified**  
   Custom checks have a `gate` config: "nonzero exit = findings vs report-only." But what's the *default* if `gate` is omitted? The bundle needs to know whether to treat a nonzero custom check exit as findings (exit 2) or just capture the output and continue. Specify the default behavior (e.g., "`gate` defaults to `true`: nonzero exit → findings").

6. **Task 4.4 — `--floor` with no floor checks enabled**  
   What if `audit.toml` disables all floor checks, and someone runs `--floor`? Does it exit 0 with a message? Exit 3 as a misconfiguration? This edge case should be specified.

7. **Task 3.1/3.3 — Test fixture gap: multi-line SQL extraction**  
   The test in 3.3 covers "SQL literal extraction from a `.py` fixture" but the explore-brief already flags that f-strings and concatenation evade static extraction. The test fixture should include at least one edge case — a multi-line triple-quoted SQL string — to ensure the regex handles real-world patterns. Without it, the test passes on a toy fixture while the real psc-monitor codebase (f-strings, raw psycopg2 with hand-rolled SQL) produces no leads at all.

8. **Task granularity — several sub-tasks likely exceed ~2 hours**  
   Tasks 4.2 (check registry with 8+ built-in parsers + delegated checks + inventory snapshot), 4.4 (four modes with resumability), and 4.7 (comprehensive test suite with stubs for 7+ tools) are each substantial. This isn't blocking — the sequential executor will work through them — but flagging for awareness: these may take 4-6+ hours each, not the ~2 hour guideline.

---

### 💡 Suggestions

1. **Add effort estimates per sub-task** — following the AGENTS.md "~N hours" convention would help the apply-executor plan its time.

2. **Document the D3 caveat for custom checks** — the bundle cannot prevent a custom `command` from writing to disk. This is a downstream responsibility but should be noted in the `audit.toml` schema docstring so repo owners who add custom checks understand the contract.

3. **Task 5.1 — the AGENTS.md insertion point "after Web research convention"** could be made more precise by referencing the section header name (`## Web research convention`) and specifying "between that section and the next `##` heading" — the current wording is clear enough but the section name reference guards against future edits shifting the layout.

4. **Task 5.3 — the scaffold_manifest.txt line format** could be made explicit: "add the following lines in the `# Scripts` block, one per line, in alphabetical order among existing entries." The exact format is implied by existing entries, but explicitness prevents a format mismatch.

---

### Premise Verdict

**PREMISE: AGREE**

- **Root, not symptom:** ✅ The three operator goals (cheap audits, agent assistance, missing workflow categories) correctly trace to the root: no deterministic tooling layer exists — tasks.md builds exactly that.
- **Solution targets the root:** ✅ Four stdlib-only, JSON-output scripts with a check-only orchestrator, pinned tools, and a scaffold-managed delivery model directly replace the LLM-burning mechanical passes.
- **Scope right-sized:** ✅ The scaffold-managed scripts + convention docs scope is clearly boxed; per-repo wiring, actual audits, formatters, and downstream sync are all explicitly out.
- **D10 — no drift from verified explore-brief:** ✅ Every D1–D9 design decision is pulled forward into task descriptions. The tool roster matches the brief's §4. No reframed problem, no ruled-out approach resurrected (EXPLAIN plan diffs stay killed; graphify stays rejected), no scope expansion (the inventory snapshot in 4.2 adds implementation detail to the brief's "DIY tree-entry-env script" mention — not a new capability).
- **Blind spots cited:** 🟡 The tasks.md doesn't explicitly note that the `inventory` and `index_coverage` output is best-effort/lead-quality (the scripts' module docstrings capture this, per tasks 3.1/4.2, but the tasks themselves could flag it); the `test_executor_body_agreement.py` reference in 5.4 is correct (file exists) but the test's relationship to these audit scripts is unclear to a new reader.

---

### Verdict

**NEEDS REVISION** — address the three 🔴 blocking issues (hotspot formula, version probe protocol, fingerprint joining convention) before proceeding to freeze. The 🟡 items are important but can be resolved during implementation if the apply-executor is well-briefed on the design carrier (explore-brief.md).
### Round 1 disposition (orchestrator, 2026-07-02)

- 🔴1 hotspot formula → FIXED (1.1): per-file complexity = maximum `complexity` across all radon block
  entries for the file; no-block files score 0.
- 🔴2 version probe → FIXED (4.3): exact protocol — `--version` then `version` fallback, both-fail =
  unavailable; first `\d+\.\d+(\.\d+)?` from combined stdout+stderr; exact-string compare to bare pins.
- 🔴3 fingerprint encoding → FIXED (4.6): `sha1("\0".join([check, rule, path, message]))` with each
  component defined against the 4.2 normalized-finding fields; message whitespace-collapsed.
- 🟡1 flat vs recursive checks dir → FIXED (2.1): flat only, documented.
- 🟡2 psql hang → FIXED (2.1): 120s subprocess timeout per check (`--timeout` override), timeout = infra.
- 🟡3 env-var regex → FIXED (4.2): anchored alternation `os\.environ` / `os\.getenv\s*\(` / `process\.env`.
- 🟡4 --out collision → FIXED (4.4): refuse non-empty --out without --resume, exit 3.
- 🟡5 custom `gate` default → FIXED (4.1): defaults true; false = report-only.
- 🟡6 --floor with nothing enabled → FIXED (4.4): exit 0, "no floor checks enabled".
- 🟡7 multi-line SQL fixture → FIXED (3.3): triple-quoted multi-line fixture required.
- 🟡8 task granularity → ACKNOWLEDGED, not split: the apply-executor is sequential and 4.2/4.4/4.7 are
  cohesive units; splitting them would create artificial intermediate states with failing imports/tests.
- 💡1 per-task effort estimates → REJECTED: AGENTS.md has no "~N hours" convention (reviewer asserted
  one that does not exist in this repo); estimates would be noise the executor cannot act on.
- 💡2 D3 caveat for custom checks → ADOPTED (4.1 docstring requirement).
- 💡3 AGENTS.md insertion point → ADOPTED (5.1 names both flanking `##` headings).
- 💡4 manifest line format → ADOPTED (5.3 explicit format + alphabetical order).

## Round 2 — tasks.md (deepseek-v4-pro via opencode run, 2026-07-02)

Now let me check for any conflicts with existing specs and the codebase conventions referenced by tasks.md.
Now let me check the scaffold-sync-mechanism spec for any conflict with the manifest format specified in task 5.3.
## Review Round 2 — `tasks.md`

### Summary

`tasks.md` is in **excellent shape** for Round 2. All three 🔴 blocking issues from Round 1 are concretely resolved:
- The hotspot formula now unambiguously specifies "maximum `complexity` value across all block entries" with fallback to 1;
- The version-probe protocol is fully specified (two-attempt `--version`/`version` → first regex match → exact-string compare to bare pins);
- The baseline fingerprint encoding is explicit (`sha1("\0".join([check, rule, path, message]))` with each component sourced from the 4.2 normalized-finding fields).

All seven 🟡 should-fix items are addressed with precise language (flat-only checks dir, 120s psql timeout, anchored env-var regex, `--out` collision refusal, custom `gate` default `true`, `--floor` graceful no-op, multi-line triple-quoted SQL fixture). The three 💡 suggestions from Round 1 are either adopted or correctly rejected with reasoning recorded in `review-log.md`.

No 🔴 blocking issues remain. Three 🟡 items and two 💡 notes are flagged below — all minor enough that the apply-executor can handle them without design ambiguity.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **Task 4.3 — Python tool version-recording protocol not specified.**  
   The probe protocol is fully detailed for binary tools (`EXPECTED_TOOL_VERSIONS`: `--version` → `version` fallback → regex extract → exact-string compare). But for Python-ecosystem tools (ruff, deptry, radon, vulture) the task says only "the bundle only records their reported versions into the run manifest" — with no specification of *how*. Does the bundle run `<tool> --version`? Does it use `pip show`? The implementer will guess — likely correctly (`--version` is near-universal), but a one-line clarification ("probe Python tools the same way — `<tool> --version` — but only record the result, never fail on mismatch") would close the gap.  
   **Location:** task 4.3, line 136.

2. **Task 4.4 — `--date` / `--out` interaction ambiguity.**  
   The task says `--report --out <dir>` defaults to `output/audit/<YYYY-MM-DD>/` and `--date` is optional, defaulting to today and "pinning the dir name when given." It is clear that `--date` drives the default `--out` template. But what happens when the user passes **both** `--out <explicit-dir>` and `--date <other-date>`? The most reasonable reading is that explicit `--out` takes precedence over the default template, and `--date` is only used for the manifest record. Stating this explicitly prevents the executor from guessing.  
   **Location:** task 4.4, line 145–146.

3. **Task 3.2 — `unparsed_statements` semantics undefined.**  
   The JSON output contract includes an `unparsed_statements` field, but the task does not define what qualifies as "unparsed." Is it any SQL fragment the regex couldn't extract table/column info from? Every statement that didn't match the WHERE/JOIN/ORDER-BY patterns? The test fixture (task 3.3) will clarify through behavior, but one sentence in 3.1 defining the boundary would strengthen the spec.  
   **Location:** task 3.2, line 84.

---

### 💡 Suggestions

1. **Task 1.1 — JSON value types for `complexity` could be explicit.** The task says `complexity: null` when radon is unavailable and "scores 0" for no-block files when radon IS available. The implementer can infer that the available case writes `complexity: 0` (a number, not null), but making the JSON types explicit across both cases would remove any ambiguity about the field's type in the output schema.

2. **Task 4.4 — `run-manifest.json` append semantics.** The task says "append its record" to the JSON manifest file — standard JSON doesn't support streaming append to a closed array without rewriting. The implementer will resolve this (either rewrite-on-each-checkpoint or use JSON Lines), and either approach satisfies the resumability goal. Noting the intended wire format just avoids rework.

---

### Premise Verdict

```
PREMISE: AGREE
```

- **D10 — no drift from verified explore-brief:** Every D1–D9 design decision is pulled forward into task descriptions. The check-only rule (D3), output contract (D8b), flat-only data checks (D4), same-analysis-two-shapes (D1), eager-vs-heavy tier split (D8e), and baseline-delta exit semantics (D6) are all intact. No reframed problem, no ruled-out approach resurrected (EXPLAIN diffs stay killed; graphify stays rejected; standing generated prose stays out), no scope expansion beyond the brief's §5 bounds.
- **Root/symptom, solution fit, and scope are unchanged from the direction gate — all were `AGREE` in Round 1 and remain sound.**

---

### Verdict

**PASS** — ready to freeze and hand off to the apply-executor. The three 🟡 items are minor clarifications the executor can resolve during implementation; none would cause wrong behavior if the executor applies reasonable defaults.
### Round 2 disposition (orchestrator, 2026-07-02) — artifact FROZEN

Zero 🔴, verdict PASS, PREMISE: AGREE, no D10 drift. The reviewer's three 🟡 clarifications and two 💡
notes were folded in verbatim before sealing the freeze (Python-tool versions probed record-only /
never-fail; explicit --out precedence over the date-templated default; unparsed_statements defined;
complexity JSON type nailed to number-or-null; run-manifest.json = single JSON array rewritten
atomically via os.replace). tasks.md is FROZEN on the round-2 zero-🔴 review.
