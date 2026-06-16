# notes.md — verify-multimodel-gate

## Verify checkpoint (2026-06-16)

### Multi-model passes (audit trail)
The new cascading gate was dogfooded on the very change that introduced it (the new verify skill was live on disk):
- **Pass 1 — self-review (orchestrator, Claude/Opus):** READY. Read all diffs from disk; `openspec validate --strict` valid; scope clean (only the verify skill, AGENTS.md, README.md tracked + the new agent file & change dir untracked).
- **Pass 2 — deepseek-v4-pro verifier (`opencode run`):** VERDICT READY, defects None. Real agent confirmed (no `Falling back to default agent`; parseable `## Verify Pass` + `VERDICT:`).
- **Pass 3 — deepseek-v4-flash verifier (`opencode run`):** VERDICT READY, defects None — with a detailed from-disk evidence trail mapping V1–V5 + D4 hardening + AGENTS.md/README to the implementation.
No pass was re-run (none returned NEEDS REVISION), so there is no original-then-final verdict pair to record.

### 1. Verdict
**READY FOR ARCHIVE.** All three passes READY; implementation faithfully matches the frozen proposal/design/specs/tasks.

### 2. Live output eyeballed (behavior, not counts)
This is a markdown/agent-config change, so the live behavioral check was the **V6 live probe of the new `openspec-verifier` agent**: it was invoked for real on both tiers via hardened `opencode run`. Both invocations loaded the real agent (no fallback warning on stderr), ran to completion (exit 0), and emitted the exact machine-discriminable verdict block the spec defines (`## Verify Pass — <model>` / `VERDICT: READY` / `### Defects` with `- None`). The agent behaved read-only throughout — it reported, never edited. The gate's orchestration plumbing (EXIT-file sentinel, fallback-warning grep, format check, from-disk judgment) all worked as written.

### 3. Defects found + how fixed (attributed to pass/model)
- **Self-review (during apply):** one trivial whitespace nit — the `notes.md`-step "field 3" in the verify skill was over-indented by one space (4-space marker vs the 3-space siblings). Fixed inline by the primary (trivial-typo exception). 
- **Pro pass:** no defects.
- **Flash pass:** no defects.
(Propose-phase reviewer findings — 3🟡 on proposal, 1🟡 on design, 1🟡 on specs, 3🟡 on tasks — were all resolved before freeze and are logged in `review-log.md`; they are not verify defects.)

### 4. As-built deltas
None. The implementation matches the frozen artifacts exactly (agent frontmatter = design D4; skill section at the design D1 anchor with D2–D8 content; AGENTS.md/README per Impact).

### 5. Forward-looking items for project docs (open questions / tuning / follow-ons / monitored risks)
- **Rerun-failed-and-after residual risk** (design D6 / Risks): a fix for a late pass is not re-checked by earlier passes; accepted/monitored trade-off (operator decision). → open-questions.
- **Bash destructive-command denylist** for bash-capable delegated agents (verifier + the apply/archive executors): deferred, not added here. → open-questions.
- **OpenCode Task-tool path was NOT live-probed:** this session ran on Claude Code, so only the `opencode run` pro+flash passes were exercised live. The OpenCode `subagent_type: openspec-verifier` path (runs frontmatter-default flash) is confirmed-by-design but unprobed under a real OpenCode orchestrator. → open-questions (probe when next on OpenCode).
- **V6(d) edit-denial not separately probed:** the verifier's read-only behavior was observed, and `edit: deny` is structurally present in the frontmatter (+ opencode's permission model, proven by the reviewer), but no test forced an edit attempt to see it denied. Low risk; note for completeness. → open-questions.
- **Scaffold has no runnable test suite** (`scripts/test-cmd` absent + no venv, by design): verify of a non-code change leaned on `openspec validate --strict` + the V6 live probe. Future *code-bearing* changes (especially in downstream repos) still require a real green suite per the verify skill. → note.
- **Propagation:** this gate is **scaffold-only and inert** until propagated to extrends/psc (the single-source-plan / "change 2"); operator deferred that. → open-questions (already tracked).

### Still owned by archive
- `STATUS.md` — add the "Latest change — verify-multimodel-gate SHIPPED" section; demote prior; update "Immediate next action".
- `ai-docs/decisions.md` — append the decision + the design D1–D8 rationale (rerun-failed-and-after, third permission category, one-agent-two-models).
- `ai-docs/open-questions.md` — fold in the forward-looking items above (rerun residual risk, bash denylist, OpenCode-path probe, V6(d), propagation).
- **Spec promotion** into `openspec/specs/`: new `verify-multimodel-gate/spec.md`; sync the `noninteractive-delegation-safety/spec.md` MODIFIED delta into the main spec.
- Cleanup: none pending.
