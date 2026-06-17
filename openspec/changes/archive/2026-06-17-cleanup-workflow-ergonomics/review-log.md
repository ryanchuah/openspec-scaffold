# Review log — cleanup-workflow-ergonomics (W5)

## Round 1 — deepseek-v4-pro (openspec-reviewer), 2026-06-17 — tasks.md + notes.md

Verdict: **PASS** (0 🔴). Two 🟡 + three 💡 — all addressed in tasks.md (2.4 validate scoping; 3.1 pin E4 to the state section; 4.3 example annotation; 5.2 append-not-overwrite; 1.4 added a multi-model-passes drift grep).

(First pro attempt was discarded: it spent its turn re-reading files to re-verify line numbers and emitted no `## Review Round` report — ran 195s, re-run per the propose salvage path. Raw: /tmp/review-out.round1.jsonl.)

Full report:

## Review Round 1 — tasks.md + notes.md

### Summary

The task list is well-scoped, covering all four audit findings (B1, D-iii, E4, E5) with concrete, testable acceptance criteria. Sequencing hazards with concurrent W4 are explicitly documented. The B1 reorder-only framing is safe — task 1.4 provides a self-audit grep gate that catches any accidental deletion. No 🔴 blocking issues. Two 🟡 concerns and a few 💡 suggestions.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **Task 2.4 may produce noisy change-dir validation warnings.** The task says `openspec validate --strict` for "the whole repo," but this is a MEDIUM change with no `proposal.md` or `design.md`. If `openspec validate` checks the change dir for completeness and rejects a missing proposal, the implementer won't know whether the failure is from the specs (the real gate) or the change-dir shape (expected for MEDIUM). **Why this matters:** a deepseek-flash executor seeing a validate failure might waste time trying to "fix" it. **Fix:** clarify task 2.4 to scope the gate to the two edited specs specifically, or note that change-dir warnings are expected and ignorable for MEDIUM.

2. **Task 3.1 names two possible insertion points (`:103` and `:149`) but the acceptance criteria in notes.md narrows to "the lifecycle/state section."** The implementer could reasonably pick the `:103` spot (OpenSpec workflow section) and still satisfy the task, but the notes.md verifier would look for it in the state section. **Risk:** verification ambiguity. **Fix:** align task 3.1 to match the notes.md criterion — direct the insertion to the state/write-discipline section only, or update the notes to accept either location.

---

### 💡 Suggestions

1. **Task 4.3 says "clear/annotate the E5 line in `ai-docs/open-questions.md`"** but doesn't specify what the annotation should say. A flash executor might write an unclear note. Consider adding one example phrase (e.g., "→ RESOLVED by W5, live smoke passed against opencode 1.17.7").

2. **Task 5.2 partially overlaps task 4.3** (both write to `ai-docs/decisions.md`). Since tasks are sequential this is harmless, but a note in 5.2 to "append, don't overwrite" would reduce risk of a flash executor clobbering the E5 entry written by 4.3.

3. **Task 1.4's grep list** omits one phrase present in the verify MANDATORY blockquote — "Mandatory disclosure" is listed, but the verbatim multi-model-passes instruction block (`:36+`) is stated as "unchanged" in 1.3. If any phrase from that section drifts during the 1.3 rewrite, this grep won't catch it. Consider adding one more grep for a distinctive multi-model-passes phrase (e.g., "invoke the verifier") to harden the gate.

---

### Verdict

**PASS** — no 🔴 blocking issues. The two 🟡 items are low-risk alignment concerns that won't derail implementation. Ready to freeze after the 🟡 items are addressed (or deliberately waived).
