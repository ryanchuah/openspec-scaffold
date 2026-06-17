# Review log — dedup-scaffold

## Review Round 1 — `tasks.md` — deepseek-v4-pro (openspec-reviewer), 2026-06-17

**Invocation:** `opencode run --agent openspec-reviewer --model deepseek/deepseek-v4-pro`, hardened
(`< /dev/null`, `--dir`), steered read-only (bash:deny). Real-agent-ran asserted: `EXIT=0`, no
`Falling back to default agent` in stderr, output carried `## Review Round` + severity markers.

**Verdict: PASS** — 0 🔴 blocking, 6 🟡 should-fix, 5 💡. "Ready to freeze after addressing the 🟡."

### Disposition (all six 🟡 applied before freeze)

1. **🟡 EXIT-sentinel not scoped to background-only** → applied. 1.1(d) now scopes the sentinel to
   `run_in_background: true` calls; flags propose-synchronous (correctly no sentinel) and archive's
   pre-existing missing-sentinel drift (document, don't fix here).
2. **🟡 task 3.2 `--check` needs a downstream repo that isn't present** → applied. 3.2 now does
   manifest-honesty via `test_sync_scaffold.py` + path-existence; real downstream `--check` deferred to
   W6; throwaway-git-repo option noted.
3. **🟡 task 4.1 EXIT-sentinel grep underspecified** → applied. 4.1 now greps the distinctive phrase
   `never poll with pgrep`, with an explicit warning not to grep `echo "EXIT="` (legit residual in
   inline invocations).
4. **🟡 task 2 doesn't point at the anchor table** → applied. Task 2 intro now directs the executor to
   the explore-brief anchor table and names the easy-to-miss verify variants (`:88`, `:27`).
5. **🟡 task 1.2 kill-grace tie-break ambiguous** → applied. 1.2 now sets authority = preserve existing
   values (`-k 30` apply/archive, `-k 15` verify/propose), extraction-not-redesign, no spec contradiction;
   added explicit table columns.
6. **🟡 task 2.5 "esp." list omits the 3rd reconciliation item** → applied. 2.5 now names all three
   (kill-grace, assert-ran, EXIT-sentinel scope); notes.md reconciliation item 3 expanded to match.

### 💡 folded in (cheap, reduce rework)
- 💡1 table column structure → added to 1.2.
- 💡4 concrete self-sufficiency checklist (1/2/3 test) → added to 4.3.
- 💡5 keep the invocation command inline explicitly → added to the task-2 intro.

### 💡 declined
- 💡2 before/after snippet in tasks.md — unnecessary weight for a tasks file; the anchor table +
  "keep" lists suffice.
- 💡3 reviewer-budget rationale-duplication note — already covered by 1.2's cross-reference constraint.

**Status: FROZEN** (no 🔴; 🟡 resolved). Ready for the apply phase on operator go.
