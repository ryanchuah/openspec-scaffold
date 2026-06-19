# review-log — rename-memory-to-knowledge

## Round 1 — @openspec-reviewer (deepseek-v4-pro) — 2026-06-19 — tasks.md + notes.md + delta specs

**Verdict: PASS.** Blocking 🔴: none. The delta specs were confirmed correct (every requirement body
containing `memory/` covered — 4 in knowledge-organization, 1 in scaffold-sync-mechanism; headers match
the main spec exactly; full bodies preserved, only path strings changed). The three folder-vs-feature
exceptions are correctly captured and respected. Rename surface essentially complete; acceptance criteria
specific and verifiable.

🟡 should-fix (applied before freeze):
1. Task 3.3 — `status_lint.py` builds paths from a SPLIT `"memory"` component
   (`repo_root / "memory" / "STATUS.md"`, ×2 each for STATUS and decisions); a full-path replace would
   miss them. → task 3.3 amended to name the split-component gotcha.
2. Task 5.2 — `test_status_lint.py` `_make_repo()` helper has the same split `"memory"` constructions
   (lines 36, 40). → task 5.2 amended.

💡 suggestions (applied):
1. Rename test method `test_memory_section_citation_checks_file_existence_only` →
   `test_knowledge_...` (test_sync_scaffold.py:566). → folded into task 5.1.
2. Task 5.1 — clarify `_KNOWLEDGE_PATH_RE` exists only after the 3.2 module rename. → amended.
3. notes.md acceptance #7 — run the grep after all renames/syncs complete, from each repo root. → amended.

All findings verified against the live source before applying (line numbers confirmed). No 🔴, so no
re-review round required; artifacts frozen.

Raw review text: /tmp/review-text.md (transient).
