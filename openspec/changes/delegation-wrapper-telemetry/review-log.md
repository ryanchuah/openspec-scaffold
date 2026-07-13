# review-log — delegation-wrapper-telemetry (OW-7)

## Round 1 — propose (deepseek-v4-pro, openspec-reviewer) — PASS · PREMISE: AGREE

Reviewed: `tasks.md`, `notes.md`, `specs/delegation-wrapper/spec.md`, `recon-delegation-sites.md`.
Verdict: **PASS** (zero 🔴). **PREMISE: AGREE** (problem = toil + observability gap correctly
identified as root, not symptom; post-processing-only scope right-sized against the budget-agreement
+ delegation-safety guards). Three 🟡 (robustness/test gaps) + three 💡. Full text in
`/tmp/ow7-review-out.jsonl`.

### 🟡 findings — all fixed pre-freeze
1. **`assert_markers` doesn't catch `re.error`** — violates T3's "never raise" contract (a malformed
   `--require-marker` regex would crash all 8 sites). → FIXED: T1 `assert_markers` now catches
   `re.error` per marker (treat as not-matched); T3 states it; T4 adds a malformed-marker test.
2. **`classify_status` `exit_code=None` path untested** — `parse_exit_file` can return `None`. → FIXED:
   T4 table adds `(None,False,"x",True)→ok` and `(None,False,None,True)→crash` rows; T1 contract note
   added.
3. **Spec R2 scenario omits `ts` + `marker_ok`** from its "at least" field list vs the requirement's
   "at minimum". → FIXED: scenario field list now includes `ts` and `marker_ok`.

### 💡 folded in
- 💡1 — `classify_status` `exit_code=None` behavior now called out explicitly in T1 (self-documenting).
- 💡3 — T1 `best_effort_duration` now flagged as an assumption (opencode jsonl ts format uncited;
  defensive `None` on any parse issue).
- 💡2 — recon §3 fix-executor code block omits the EXIT sentinel shown in its prose; no change needed
  (T3's unreadable-exit-file grace covers it; T8 correctly assumes `--exit-file /tmp/fix-out.exit`).

**Disposition:** zero 🔴 + PREMISE: AGREE → FREEZE-OK after the three 🟡 edits above. No re-review round
required (🟡-only; edits are to spec/test wording + one robustness bullet, not the design). Advancing
to apply.

## Apply — deepseek-v4-flash (apply-executor) — clean, no fallback

10/10 tasks landed; `bash scripts/check.sh` exit 0 (497 tests). No Sonnet fallback. The precise
tasks.md held for the prose-surgery wiring — flash preserved every literal invocation line.

## Verify (MEDIUM: self-review → pro behavioral pass)

### Self-review (orchestrator, inline independent exercise) — PASS
Built my own fixtures (real `.part.time` opencode shape) and ran the actual
`scripts/opencode_delegate.py` end-to-end: ok/READY, fallback, timeout(124), crash(no-text),
marker-missing, malformed-regex-no-crash (T3), sync `--exit`, append-only ledger with all 12 core keys
on every line — ALL correct. Byte-verified via `git diff` that NO literal `timeout -k`/`< /dev/null`
invocation line changed (budget-agreement + delegation-safety guards intact). Reviewed the full script
(clean, faithful) and the 8-site wiring (correct per-site flags; disk-state judgment + failure ladders
retained in prose).

**Disclosed inline change at verify (mechanical, no re-review):** `best_effort_duration` /
`_extract_timestamps` improved to read the REAL opencode timestamp shape `part.time = {start,end}`
(epoch-ms), which I probed from live output — the frozen tasks.md T1 had guessed a scalar `time`, so
duration was always null. Now populates (verified 8.2s on a fixture; 223.7s on the real verifier run).
Added `test_observed_part_time_object_form` to pin it. Backward-compatible with the executor's 7
scalar-based duration tests. Non-load-bearing best-effort field (notes A2), so no design impact.
Also removed a stray `test-quality.json` the executor's T10 detector run left at repo root.

### Pro behavioral verifier pass — deepseek-v4-pro — VERDICT: READY, Defects: None
Independently exercised the wrapper through 9 scenarios (matching self-review), confirmed both spec
SHALLs on their first physical line, `check.sh` exit 0, scaffold_lint + knowledge_lint clean, the
invocation-line grep EMPTY, and all 8 sites' wiring correct with failure ladders/disk-judgment
retained. Post-processed via the new wrapper itself (dogfood): first real ledger line recorded
`status=ok, verdict=READY, duration_s=223.7`. Full report in `/tmp/verify-pro-out.jsonl.text.txt`.

**Simplicity/quality gate:** the wrapper is minimal and single-purpose (ingest-only; no disk judgment,
no ladder, no gate); no over-engineering. **Artifact/spec mapping:** the NEW `delegation-wrapper`
capability's two requirements map to the implementation (R1 = the tested ingest wrapper; R2 = the
one-line-per-run ledger with the pinned schema). **Verify: PASS → advancing to archive.**
