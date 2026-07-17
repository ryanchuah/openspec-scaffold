# review-log — handoff-lint-exempt

## Round 1 — tasks.md + deltas — deepseek-v4-pro (openspec-reviewer) — 2026-07-17

Delegation: status=ok exit=0 fallback=no marker_ok=yes. `freeze_check --artifact tasks` → `FREEZE: READY`.

## Review Round 1 — tasks.md (handoff-lint-exempt, MEDIUM tier)

### Summary

Overall quality is high. The problem is clearly stated in `notes.md`, the root cause is correctly identified (category mismatch: the linter treats a forward-looking handoff as steady-state prose), and the approach — extending the existing `knowledge/research/` exclusion precedent to cover the handoff as a scanned source — is proportionate and surgically targeted. Every acceptance criterion maps to one or more tasks, and the over-broad-suppression guard tests (4.3, 4.4) are load-bearing and correctly specified. The granularity is reasonable for a MEDIUM change.

I have one 🟡 should-fix (a maintenance hazard in a hardcoded literal that the constant-consolidation pass misses) and two 💡 suggestions. No 🔴 blocking issues.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **Un-replaced hardcoded literal in `_check_handoff_files` finding message** — Task 1.3 correctly consolidates the two hardcoded `"knowledge/HANDOFF.md"` literals (the `_check_handoff_files` exemption at line 805 and the first element of `EPHEMERAL_PATHS` at line 138) to use the new `SANCTIONED_HANDOFF` constant. But there is a **third** hardcoded occurrence at line 817-818:

   ```python
   f"handoff-named file {rel}; the only sanctioned handoff file is knowledge/HANDOFF.md",
   ```

   This user-facing string is not one of the two sites task 1.3 calls out, but it *should* also use the constant — otherwise, if `SANCTIONED_HANDOFF` changes, the message silently drifts from the actual exemption path, making debug output lie. This is a genuine maintenance hazard, not cosmetic. Low: the string happens to agree with the constant today, and discoverability is good (the message appears next to the `==` comparison at line 805). Adding it to task 1.3 would close the gap with zero risk.

---

### 💡 Suggestions

1. **`knowledge-drift-review` skill interaction** — The change exempts the handoff from the deterministic linter but does not address the operator-invoked `knowledge-drift-review` skill (which runs `knowledge_lint.py` first, then performs LLM judgment sweeps). The skill's stale-claim pass could flag a handoff's forward-referencing prose as a contradiction (e.g. a feature described as "not yet built" in a handoff vs. the current tree). This is operator-invoked, not a commit gate, so it does not re-create the self-defeating loop — but noting it in `notes.md`'s out-of-scope or a post-archive follow-up would help the next operator who encounters it.

2. **Task 2.3 implementation detail** — The task says "skip the sanctioned handoff when collecting `knowledge/` markdown" in `_duplicate_scan_files`, but unlike the other file-loops that already compute `_relpath`, `_duplicate_scan_files` does not compute a relative path for individual files in its inner loop (it only computes `rel` for the directory). A first-time implementer could miss that they need to call `_relpath(root, full)` and compare against `SANCTIONED_HANDOFF`. Adding a one-sentence hint ("compute `_relpath(root, full)` for each file before appending and skip when it equals `SANCTIONED_HANDOFF`") would prevent a trivial implementation stall. The intent is clear enough that this is not blocking, but it's the one spot in the task list where the "how" is materially fuzzier than the other subtasks.

---

### Premise Verdict

**Direction assessment:** The problem is the real root cause — the handoff mechanism is mandated by the `knowledge-organization` spec, but the linter's model of "broken prose" is categorically wrong for a forward-looking work order. This is not a symptom of a deeper issue (e.g. a flawed handoff design); it is a genuine conflict between two load-bearing spec requirements. The solution targets the root by extending an existing, proven carve-out pattern (`knowledge/research/`) to cover the mirror-image case (forward-looking rather than backward-looking prose). Scope is right-sized: the exemption is keyed to exactly one file path, the tests include an over-broad-suppression guard, and the out-of-scope section explicitly excludes blanket suppression and broadening beyond the sanctioned path.

**Blind spot:** The `sync_scaffold.py` task (3.1) excludes the handoff from `_tracked_markdown` via an exact-match addition to the comprehension — but `_tracked_markdown` is also the fallback enumerator for `check_references` when git is unavailable. In that fallback path, `rglob("*.md")` enumerates every `.md` file recursively, and the exclusion is applied afterward. This is correct behavior (the handoff should be excluded in both code paths), but nothing in the test plan exercises the fallback path. Task 5.1-5.3 tests all use the normal git path. This is low-risk (the fallback path uses the same exclusion list) but it is the one disanalogous code path the tests miss.

PREMISE: AGREE
- Root cause correctly identified: linter model mismatch, not handoff design flaw
- Solution matches root: category-level exclusion, not line-level annotation
- Scope right-sized: single file, over-broad guard, explicit out-of-scope
- Blind spot noted: `_tracked_markdown` git-unavailable fallback path not covered by test plan (low risk)

---

### Verdict

PASS — one 🟡 should-fix (the un-replaced hardcoded literal in the finding message) and two 💡 suggestions, but nothing that would cause implementation to go in the wrong direction or create rework. Ready to freeze and proceed to apply.

VERDICT: PASS
---

### Orchestrator disposition (round 1)

`FREEZE: READY` + `PREMISE: AGREE` → artifact frozen. No 🔴. All non-blocking points folded in
rather than deferred, since each is concrete and zero-risk:

- **🟡 third hardcoded literal** (finding message, ~line 817) — ACCEPTED. Genuine drift hazard the
  reviewer caught and the orchestrator missed; the debug message would silently lie if the constant
  moved. Folded into task 1.3.
- **💡 1 knowledge-drift-review interaction** — ACCEPTED as an out-of-scope note in notes.md. Correctly
  reasoned: that skill is operator-invoked, not a commit gate, so it does NOT re-create the
  self-defeating loop. Recording the boundary, not widening scope.
- **💡 2 task 2.3 fuzziness** — ACCEPTED. `_duplicate_scan_files` computes `rel` only per-directory, so
  the per-file `_relpath` call is a real implementation stall. Hint added to task 2.3.
- **Premise blind spot — `_tracked_markdown` git-unavailable fallback** — ACCEPTED. The strongest
  finding in the review: the exclusion is applied after both the `git ls-files` and the `rglob`
  fallback enumerations, so behavior is correct, but no test pinned the fallback path. Added as task
  5.4 — an untested branch is exactly how this class of bug returns.

No finding was overruled.
