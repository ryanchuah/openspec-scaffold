# add-status-lint — review log

## Round 1 — tasks.md (deepseek-v4-pro `openspec-reviewer`, 2026-06-18) — VERDICT: NEEDS REVISION

### 🔴 Blocking
1. **Exempt-heading prefix match on `done`/`pointers` over-broad (1.2).** `startswith` would silently exempt a change-entry like `## Done-archive migration`. AGENTS.md names only preamble + `## Immediate next action` as exempt. Fix: exact-match, or remove `done`/`pointers`; document the allowlist.

### 🟡 Should fix
2. **Missing test: exempt section >150w must NOT fire C2 (2.2).**
3. **Missing test: combined decisions.md violations (no Status AND >300w → two violations) (2.2).**
4. **Change-record regex `\b(fix|add|tune|remove|update|refactor)-` broader than AGENTS.md (`fix/add/tune`) without justification (1.3).** Tighten or document.
5. **Exempt-heading list broader than AGENTS.md without justification (1.2).** Same root as #1.

### 💡 Suggestions
6. Test: STATUS.md present, decisions.md absent (asymmetric).
7. Test: STATUS.md with zero change-entries (preamble + exempt only) → pass.
8. "byte-identical" wording imprecise — the two executor files differ by a sanctioned intro clause that `test_executor_body_agreement.py` normalizes; reword to "shared body."

### Resolution (primary, same day)
- #1/#5 → exempt matching changed to **exact** normalized-heading match; allowlist kept (`current state`/`immediate next action`/`done`/`pointers`) with rationale added to notes.md (real structural sections in scaffold+extrends; exact-match prevents over-exemption).
- #4 → regex **tightened** to `\b(fix|add|tune)-` to match AGENTS.md exactly; rationale in notes.md.
- #2, #3, #6, #7 → test cases added to task 2.2.
- #8 → task 3.1 reworded to "shared body … sanctioned intro divergence."
- Re-review required (🔴 fix is not self-certifiable) → Round 2.

## Round 2 — tasks.md (deepseek-v4-pro `openspec-reviewer`, 2026-06-18) — VERDICT: READY

Zero 🔴. All Round 1 findings confirmed genuinely resolved (exact-match exemption, tightened regex, added tests, "shared body" wording). Remaining items were 🟡/💡 narrow edge cases the reviewer said need no further re-review round:
1. 🟡 add a `## Done-archive migration` exact-match regression test.
2. 🟡 strip fenced code blocks in the decisions.md checks too (consistency with 1.2).
3. 💡 mention decisions.md fix-guidance in the 3d/3.3 resolution text.
4. 💡 soften the "enforces AGENTS.md invariants" wording for the pragmatic exempt extension.
5. 💡 anchor the change-record regex (`^(fix|add|tune)-`) so it can't match mid-heading.

### Resolution (primary, same day — polish on an already-READY artifact, no 🔴 cleared, so no further round needed)
All five folded into tasks.md: regex anchored `^(fix|add|tune)-`; decisions.md checks now strip code fences first; exact-match regression test added to 2.2; 1.1 wording softened + 1.2 parenthetical added; 3d body now covers decisions.md violation fixes. **Artifact FROZEN — proceed to apply (deepseek-flash).**
