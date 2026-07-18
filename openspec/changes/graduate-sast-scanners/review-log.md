# Review log — graduate-sast-scanners

## Round 0 — Direction gate (explore-brief premise review)
- Model: deepseek/deepseek-v4-pro via opencode (openspec-reviewer), 2026-07-18
- Verdict: **PREMISE: AGREE**, **VERDICT: PASS**, zero 🔴.
- 🟡/💡 (all design-detail, resolved in tasks.md since MEDIUM has no design.md):
  - Semgrep invocation shape + ruleset + JSON key-paths must be explicit → tasks.md pins
    `semgrep --json --quiet <args:--config> <paths>`, parser keys results[].{check_id,path,start.line,extra.message}.
  - Bandit stdout-vs-file + JSON shape → tasks.md pins `bandit -r <paths> -f json -q` (JSON to stdout;
    exit 1 on findings is fine — _run_builtin_tool_json parses stdout regardless of exit code),
    parser keys results[].{test_id,filename,line_number,issue_text}.
  - Both tools emit JSON to **stdout** → generic _run_builtin_tool_json + generic test stub fit both
    (the 💡 'may need a dedicated runner' is refuted: the runner ignores exit code and parses stdout).
  - pip guard mirrors the Go guard: warn on stderr → point to security-scanners.md → exit 0 (degrade-don't-block).
  - Auto-detection: no trigger (default-disabled); future trigger deliberately TBD.

### Full direction-gate review text
```
## Review Round 1 — `explore-brief.md`

### Summary

The explore-brief correctly identifies a real gap — the scaffold's curated built-in check set has no Semgrep or Bandit member, even though both were proven workable for security scanning in psc-monitor's S0 session. The root cause is accurate (no built-in check members; install-tools.sh only provisions Go scanners). The solution direction — graduating them as built-in parsed checks mirroring the existing `ruff`/`osv-scanner` pattern, default-disabled for sync-safety, with pip provisioning in `install-tools.sh` — is architecturally sound and consistent with the scaffold's existing conventions. The scope is well-bounded, and the deferrals (`_custom_checks` family fix, npm-audit wiring, flipping to gating) are all justified. No 🔴 blocking issues at explore altitude. However, there are several material unknowns about Semgrep's and Bandit's invocation shape and ruleset selection that the design phase will need to resolve.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **Semgrep invocation shape is materially under-specified for exploration of a *parser*.** The brief says the parser should normalize Semgrep's JSON → `{check, rule, path, line, message}`, but doesn't identify which Semgrep invocation (`semgrep scan --json`? `semgrep ci --json`?), what ruleset(s) the scaffold runner should default to, or what the critical JSON key paths are (`results[].check_id`, `results[].path`, `results[].start.line`, `results[].extra.message` in recent Semgrep versions). The psc-monitor `run_semgrep_security.py` wrapper likely captured these, but the brief doesn't carry any of that forward. This is a design-level question, not a direction fault — but it is the most load-bearing unknown for `design.md` to resolve. At minimum the brief should acknowledge "Semgrep invocation shape and default ruleset TBD — capture from psc-monitor probe" as an open question.

2. **Bandit JSON output shape is similarly untreated.** Bandit's `--format json` output nests findings under `results[]`, each carrying `filename`, `line_number`, `test_id`, `issue_text` — these need to be mapped to the standard `{check, rule, path, line, message}` shape. The brief says Bandit should use `_run_builtin_tool_json` via `_BUILTIN_RUNNERS`, but Bandit's output is NOT pure JSON on stdout — it writes to a file by default (`-o` flag), or emits JSON to stdout with `--format json`. The runner shape needs an explicit decision: stdout capture (like ruff) or file-then-read (like deptry). Acknowledge as open.

3. **Semgrep is not Python-only — auto-detection trigger is ambiguous.** The brief says "default-disabled" (no auto-detection trigger), which is correct for sync-safety. But it doesn't discuss whether a future auto-detection trigger could be considered (e.g., Python source present OR `.semgrep.yml` present). This isn't blocking — default-disabled is the safe starting point — but the design should document the ambient question so a future operator doesn't wire the wrong trigger pattern.

---

### 💡 Suggestions

1. **Consider whether `_run_builtin_tool_json` is sufficient for Semgrep.** Semgrep's JSON output includes nested `extra` metadata and path information that may not be a flat list — the parser might need its own dedicated runner (like `_run_deptry` or `_run_gitleaks`) rather than the generic `_run_builtin_tool_json`. The brief groups both Semgrep and Bandit under `_run_builtin_tool_json` (line 33-34), but this may not survive contact with Semgrep's actual output shape. Flag this in the open questions so the design doesn't silently force-fit.

2. **`install-tools.sh` pip guard should mirror the Go guard's degrade-don't-block posture.** The brief says "guarded on `pip`, degrade-don't-block if absent." The existing Go guard (line 35-43 of `install-tools.sh`) warns and exits 0. The design should document the specific degrade behavior: warn on stderr, point to `security-scanners.md`, exit 0 — same pattern as the Go guard. Not a flaw, just a design detail to carry forward.

3. **Consider embedding in the brief a pointer to the psc-monitor deferred item for traceability.** The brief cites `psc-monitor/plans/security-audit-ap1/s0-tooling.md, Deferred section` (line 13). If that file is at a known path relative to the downstream repo checkout, a more precise citation (section heading, or a short quote) would help the design phase (and any future operator) trace the provenance unambiguously.

4. **The `test_checks.py` stub pattern for the two new scanners should be explicitly called out.** The brief says "mirror the existing stub-on-PATH tests for the two new checks" (line 40). Since Semgrep outputs JSON to stdout (generic stub pattern) and Bandit may output via `-o` file (needs a special stub like deptry), the design should explicitly identify which stub pattern each scanner uses. At explore altitude, noting "existing test pattern applies" is fine.

---

### Premise Verdict

The direction is sound. The problem is real and traceable to the psc-monitor deferred item. The root cause — no Semgrep/Bandit member in the scaffold's built-in parsed check set — is correct. The solution direction (graduate as built-in parsed checks, default-disabled, version-recorded-not-gated, pip-provisioned) is consistent with the scaffold's existing conventions (`jscpd`/`vulture` for opt-in pattern; `ruff`/`deptry` for Python-tool version posture; Go-guard for degrade-don't-block). Scope is material and well-bounded; the deferred `_custom_checks` family fix is orthogonal and properly separated.

**Blind spot:** the actual invocation shape and JSON output schema of both Semgrep and Bandit are load-bearing unknowns that `design.md` must resolve — the psc-monitor wrappers likely captured these, and the design should carry those shapes forward explicitly rather than assuming `_run_builtin_tool_json` fits both out of the box.

```
PREMISE: AGREE
```

---

### Verdict

PASS — no 🔴 blocking issues. The brief is ready to serve as the frozen context for `proposal.md`. The 🟡 items above are material design questions; they should be resolved during the design phase, not held against the explore brief.

```
VERDICT: PASS
``````

## Round 1 — tasks.md (apply contract) pro review
- Model: deepseek/deepseek-v4-pro via opencode (openspec-reviewer), 2026-07-18
- freeze_check: **FREEZE: READY** — VERDICT: PASS, zero 🔴. Premise re-confirmed, no drift.
- 🟡/💡 applied to tasks.md before freeze (non-blocking clarity):
  - Added task 1.12: update the two stale 'seven parsers' comments (checks.py:808, 1744) → nine.
  - Task 4.2: noted the 1.1→4.2 set-equality dependency.
  - Task 4.6: pinned exact version-not-gated assertions (was underspecified).

### Full tasks.md review text
```
Now I have all the context needed for a thorough review. Let me compose the findings.

---

## Review Round 1 — `tasks.md` (MEDIUM apply contract)

### Summary

The apply contract is **solid**. Every runner argv and parser JSON key-path is explicitly pinned, resolving all the 🟡 design-detail questions the direction gate flagged. The task granularity is appropriate (~2h each), dependencies are implicit but navigable for a sequential executor, and the delta spec’s requirements are all covered. The green gate (task 5.1) won’t break from these changes — no task introduces syntax errors, changes execution paths for existing checks, or alters test fixture behavior in a way that would red an unrelated test. I found no 🔴 blocking defect.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **`_normalize_finding_paths` docstring comment is under-counted** — Line 808 of `scripts/checks.py` reads `"means all seven parsers (ruff, gitleaks, osv-scanner, deptry, radon, jscpd, vulture) are covered"`. After this change, bandit and semgrep are also funneled through that function, making it *nine* parsers. Task 1.11 updates the module docstring but doesn’t mention this function-level comment. The comment is not code (the behavior is correct either way), but a stale count is a small drift that could confuse a future maintainer comparing the registry against the claim. Either add a sub-task note to update this comment, or fold it into 1.11.

2. **Implicit ordering dependency between tasks 1.1 and 4.2** — Task 1.1 adds bandit/semgrep to `_REGISTRY`, which causes `--list` to emit them. Task 4.2 updates `expected_names` in `test_list_includes_every_check_with_tier_and_availability`, which uses set-equality. If the executor does 1.1 without 4.2, that **specific test** will fail. The tasks are numbered top-to-bottom (section 1 → section 4), so an executor following sequential order will naturally fix this, but the dependency isn’t noted. A one-line dependency note in 4.2 ("Depends on 1.1 — do them together or expect a transient test-list failure") would make the contract fully unambiguous.

---

### 💡 Suggestions

1. **The `_normalize_finding_paths` function body also has seven lines of per-runner commentary you might want to note** — line 804 references "all seven builtin parsers funnel through this one point" in the code path comment inside `_execute_check`. Task 1.11 (or a note) could mention this too. Again, cosmetic only.

2. **The pip install command in task 2.2 doesn’t guard against `pip` being a wrapper that exits 0 but doesn’t actually install** — This is the existing posture of the Go guard, so it’s consistent. No action needed; just noting symmetry.

3. **Test for `PythonToolVersionRecordedTest` extension in 4.6 is underspecified relative to 4.4/4.5** — Tasks 4.4 and 4.5 are exact (precise fixture, which method to add to, exact assertions). Task 4.6 says "Extend … or add a sibling test" without pinning the exact assertions. The executor has latitude. This is fine at MEDIUM tier where `tasks.md` is the only propose artifact, but the orchestrator should verify that the version-not-gated assertion actually proves the invariant (i.e., set a wrong version, run `--check`, assert rc=0/ok, and assert no INFRA-FAIL in output).

---

### Premise Check (re-confirmed from frozen explore-brief)

- **Root detection**: ✅ — The problem is a real gap (no SAST scanner in the scaffold’s built-in parsed check set), not a symptom.
- **Solution targets root**: ✅ — Adding bandit/semgrep as first-class built-in parsed checks in the golden source fixes the gap.
- **Scope right-sized**: ✅ — IN: `checks.py`, `install-tools.sh`, `security-scanners.md`, delta spec, `test_checks.py`. OUT: `_custom_checks` family, npm-audit, scanner-PATH, lockfile→osv activation, per-repo gating flip.
- **Blind spot addressed**: ✅ — The direction gate flagged invocation shape and JSON key-paths as unknowns; all are now pinned in the task bodies.

**No drift detected** — the tasks faithfully execute the explore-brief’s solution direction and do not reframe the problem, switch to a ruled-out approach, or expand scope.

---

### Verdict

PASS — no 🔴 blocking issues. The contract is specific enough for a sequential apply-executor to implement without improvisation, and the green gate will stay green. The two 🟡 items above are clarity improvements that would make the contract fully unambiguous but do not threaten implementation correctness.

```
VERDICT: PASS
``````

## Round 2 — verify: independent behavioral verifier pass (MEDIUM)
- Model: deepseek/deepseek-v4-pro via opencode (openspec-verifier), 2026-07-18
- **VERDICT: READY**, Defects: None (real verifier ran, no fallback).
- Confirmed: full suite green; --list shows bandit/semgrep heavy/check/disabled; absent from
  EXPECTED_TOOL_VERSIONS; parser key-paths + runner argv correct vs documented JSON contracts;
  exit-code-agnostic stdout parse sound; install-tools.sh restructure correct; delta scenarios covered.
