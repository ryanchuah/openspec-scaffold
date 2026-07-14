## Review Round 1 — `plans/succession-hardening/explore-brief.md`

### Summary

The explore brief identifies a real and well-evidenced problem: the scaffold's remaining safety rests on prose conventions that only a frontier-class operator can reliably sustain. Seven concrete failure modes are enumerated, backed by file evidence I can independently verify. The root-cause diagnosis — an **enforcement gap**, not a documentation gap — is accurate and well-supported. The four-change direction converts prose-only invariants into deterministic, commit-time checks with agent-neutral reference for the irreducible remainder, directly targeting that root. The scope boundaries are explicit and reasonable. There are a few implementation-level risks worth flagging, but no direction-level defect.

---

### Premise Verdict

```
PREMISE: AGREE
```

- **Root, not symptom:** All seven failure modes trace to the same pattern — invariants encoded as prose with no machine enforcement. Correct diagnosis.
- **Solution targets the root:** The four changes convert these to deterministic checks (manifest completeness, anchor invariants, budget-drift detection, dangling references, knowledge drift) plus agent-neutral conventions for what can't be mechanized. Sound approach.
- **Scope right-sized:** Four changes at appropriate tiers (MEDIUM/SMALL/SMALL/MEDIUM), with explicit out-of-scope (no downstream syncs, no lifecycle redesign, no CI infrastructure, low-priority debt). "What's-out" is stated. No scope creep.
- **Blind spot — minor, not direction-threatening:** Change 4's data-safety fix for the verifier is itself a prose-based convention ("mandatory data-safety preamble"), which sits in tension with the "mechanism over docs" philosophy the brief otherwise champions. The brief acknowledges the limitation of permission-based tightening, but this tension warrants attention during design.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **Data-safety fix is prose, not mechanism.** The verifier incident (item 5a) is pinned on `bash: allow` permissions, but the proposed fix — a "mandatory data-safety preamble in `openspec-verifier.md`" — relies on the same prose enforcement the brief argues is the root cause. The design phase should explore whether any permission-level tightening (e.g., `external_directory` scoping, `bash` allowlist restriction, or a dedicated read-only verifier agent) is feasible in the OpenCode permission model, before defaulting to a preamble. If preamble is the best available, the design should explicitly acknowledge the residual risk rather than present it as resolved.

2. **AGENTS.md title/project-context spans hazard.** Change 2 proposes to "fill the scaffold's own AGENTS.md title/project-context spans (per-repo spans — will not propagate)." The scaffold's AGENTS.md IS the golden template; its current `<FILL:>` placeholders correctly signal downstream repos to fill them. Filling them with scaffold-specific content risks polluting downstream repos if the span-merge logic doesn't correctly exclude them. The design must explicitly confirm which AGENTS.md line ranges are in the "shared spans" vs. "preserved per-repo" regions, and verify that `sync_scaffold.py`'s span-merge correctly excludes the filled sections.

3. **Change 1: `scaffold_lint.py` test command support.** The brief says "arm the scaffold repo's own dormant commit-test gate (`scripts/test-cmd` running pytest)." No `scripts/test-cmd` exists today (confirmed: glob returned empty). The existing `scripts/test-gate.sh` invokes whatever `scripts/test-cmd` returns. Creating `test-cmd` is correct, but the design should address: will `scaffold_lint.py` itself be part of the pytest suite, or a separate check? The commit gate is a PreToolUse hook — adding a lint check to it means pytest must invoke the linter (or `test-cmd` itself chains the linter before/alongside pytest).

---

### 💡 Suggestions

1. **Merge changes 2 and 3?** The brief itself raises this as an open question. Both are SMALL, doc-surface passes touching instruction files and knowledge files respectively. The knowledge prune (change 3) has a file-removal tombstone dependency on change 1 if the manifest needs a deletion mechanism. If that dependency is cheaply folded into change 1, merging 2 and 3 into one SMALL change (3 sub-tasks) would reduce overhead. If the tombstone check in change 1 is complex, keeping them separate is defensible. The design phase for change 1 should produce the concrete answer.

2. **Budget-agreement check brittleness.** The brief's open question about parsing bash blocks from markdown is well-placed. An alternative would be to reduce the embedded blocks to citations (e.g., "Per harness §e row 3, budget 600s/-k30") rather than duplicating exact timeout lines, then have the linter verify citations are valid — simpler than parsing bash. Worth considering in design.

3. **Verifier agent path discrepancy.** The explore brief refers to "The `openspec-verifier` agent (`bash: allow`)" without specifying its path. It exists at `.opencode/agents/openspec-verifier.md` (not `.claude/agents/`). The claim about data mutation is a downstream incident, not directly verifiable from the scaffold. The design for change 4 should cite the exact agent file and confirm the incident with concrete evidence (e.g., a git log entry from extrends showing the DB rollback).

---

### Verdict

**PASS** — ready to freeze and move to design/proposal. The direction is sound, the root cause is correctly identified, and the four-change split targets it coherently. The 🟡 concerns above are design-level details that don't threaten the premise.
