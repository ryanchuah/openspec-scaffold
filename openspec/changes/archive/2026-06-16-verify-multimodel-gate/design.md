## Context

The verify step (`.claude/skills/openspec-verify-change/SKILL.md`) is the final gate before a change is archived/released. Today it is a single-reviewer gate: the orchestrator performs a MANDATORY non-delegated behavioral review (read diffs, re-run the full suite, eyeball real output, run live smoke), then a completeness/correctness/coherence checklist, then writes the report + `notes.md`. The existing skill also has a defect-fix path that re-delegates to the apply-executor (deepseek-v4-flash) via a hardened `opencode run` and escalates to Sonnet on failure.

Delegation in this repo is already established: `.opencode/agents/{apply-executor,archive-executor,openspec-reviewer}.md` run on deepseek tiers, and every delegated `opencode run` is hardened per `openspec/specs/noninteractive-delegation-safety/spec.md` (`< /dev/null`, `--dir`, bounded `timeout`, EXIT-file sentinel, fallback-warning assertion). This change reuses all of that machinery; it adds independent verification passes, it does not invent a new delegation mechanism.

## Goals / Non-Goals

**Goals:**
- Add independent multi-model verification passes to verify, layered after the orchestrator's self-review, without weakening the existing self-review ("do not delegate this" stays).
- Platform-correct chains: Claude Code → self → pro → flash; OpenCode → self → flash.
- Hard gates with deterministic recovery: rerun the failed pass and every later pass; bounded loop; operator escalation.
- A read-only-on-files verifier agent that runs the same behavioral review and emits a machine-discriminable verdict the orchestrator judges from disk.
- Keep the hardening invariant complete: every new delegated `opencode run` is hardened; the agent-permission taxonomy covers the verifier's hybrid category.

**Non-Goals:**
- Not changing the propose, apply, or archive phases.
- Not letting the verifier fix defects — fixing stays the orchestrator's job via the existing re-delegation path.
- Not adding a bash destructive-command denylist (tracked as a deferred open question; the verifier is strictly ≤ apply-executor capability).
- Not adding any new model tier or provider; only the two already-configured deepseek models.

## Decisions

### D1 — The passes are additive; the self-review is untouched
The orchestrator first completes its existing MANDATORY behavioral review (pass 1) itself. **Immediately after that behavioral-review block — and before the artifact/spec mapping checklist (the current skill step 5 "Verify Completeness") and the report/`notes.md` steps — it runs the delegated passes.** The completeness/correctness/coherence checklist, the verification report, and `notes.md` are produced **once, last**, after every pass has cleared, so the report reflects all passes (see D8). The self-review's "the main agent MUST itself do all of the following — do not delegate this" rule is unchanged: it governs pass 1, which the orchestrator still performs itself. The delegated passes are *additional independent confirmations*, never a substitute. *Alternative rejected:* replacing the self-review with delegated passes — loses the orchestrator's own from-disk judgment and contradicts the operator's "after self review" sequencing. *Alternative rejected:* running the delegated passes after the artifact checklist — would run the checklist before the behavioral hard gate.

### D2 — Platform-specific chain by model diversity
- **Claude Code orchestrator:** self → `deepseek/deepseek-v4-pro` → `deepseek/deepseek-v4-flash`.
- **OpenCode orchestrator:** self → `deepseek/deepseek-v4-flash` only.
The orchestrator is the first "view." A Claude orchestrator (Anthropic model) gains maximum diversity from both deepseek tiers. An OpenCode orchestrator already runs deepseek-v4-pro, so a second pro pass is near-duplicate; only the cheaper flash tier adds an independent view. The skill already forks on platform ("If you are Claude Code" vs "If you are OpenCode") in the propose skill — reuse that exact fork. *Alternative rejected:* identical chain on both platforms — wastes a redundant pro pass under OpenCode.

### D3 — One verifier agent, model chosen per invocation
New agent `.opencode/agents/openspec-verifier.md`, frontmatter `model: deepseek/deepseek-v4-flash`. The default flash serves the OpenCode Task-tool path (`subagent_type: openspec-verifier`), which needs flash only and cannot pass a per-call `--model`. The Claude Code path invokes `opencode run --agent openspec-verifier --model deepseek/deepseek-v4-pro` then `--model deepseek/deepseek-v4-flash`; `--model` overrides the frontmatter (documented in the propose skill: "`--agent` loads the role prompt and tools; `--model` selects which LLM runs"). One agent file, two models, no duplication. *Alternative rejected:* two agent files (`openspec-verifier-pro` / `-flash`) — duplicated body prompt that must be kept in sync.

### D4 — Verifier permission block (the "third category")
```yaml
mode: all
model: deepseek/deepseek-v4-flash
permission:
  read: allow
  edit: deny
  glob: allow
  grep: allow
  list: allow
  bash: allow
  task: deny
  webfetch: deny
  websearch: deny
  external_directory:
    "*": deny
    "/tmp/**": allow
```
The verifier must run the test suite and render real output → it needs `bash: allow`. It must not fix → `edit: deny` (in opencode, `edit` is the single file-modification permission; there is no separate `write` key — confirmed against `apply-executor.md`/`openspec-reviewer.md` which use only `edit`). Because `bash: allow` makes it write-capable *in practice*, it takes the **executor-style** `external_directory` containment (`"*": deny`, `/tmp/**: allow`), NOT the read-only reviewer's `external_directory: allow`. This is a third permission category between the existing two and must be stated explicitly in the noninteractive-delegation-safety spec. The verifier is strictly less capable than the apply-executor (no `edit`, no `task`), so it crosses **no new trust boundary**. *Alternative rejected:* reuse `openspec-reviewer` with `bash` flipped to allow — conflates the read-only propose auditor (whose `bash: deny` is load-bearing for its "cannot affirm empirics" anti-pattern) with a test-running verifier.

### D5 — Machine-discriminable verdict, judged from disk
The verifier runs the same behavioral review the self-review runs (read `git diff` and changed files; re-run the FULL suite via the per-repo command — `scripts/test-cmd` or the documented command, never improvised; eyeball a concrete real-output sample; for external-API changes run the live smoke, where a *skipped* smoke is NOT a pass and a *missing* smoke is itself CRITICAL). It does **not** fix anything. It emits exactly this block (the orchestrator greps for it, analogous to `## Review Round` and `### NON-CONVERGENCE BLOCKER`):
```
## Verify Pass — <model-id>
VERDICT: READY            # or exactly: VERDICT: NEEDS REVISION
### Defects
- 🔴 <file:line> — <what is wrong and the evidence>
```
The `### Defects` section is **always present**; when the verdict is READY with no defects it contains the single literal entry `- None`. The verifier's input prompt has a fixed shape (also used by V6): *"Review the current git diff and changed files; re-run the full test suite via the per-repo command; eyeball one concrete real-output sample; for any external-API surface run the live smoke (a skipped smoke is not a pass); do NOT fix anything; emit a `## Verify Pass — <model>` block with your VERDICT and any file:line defects."*
Before trusting any pass output the orchestrator asserts the real verifier ran (reusing the propose checks): grep stderr for `Falling back to default agent` (→ escalate, do not use output), and confirm the extracted text contains a `## Verify Pass` heading AND a `VERDICT:` line. The orchestrator then judges every finding **from disk** (`git diff`, re-run), treating findings as leads to confirm — not gospel. It may overrule a demonstrably false finding, but only with rationale recorded in `review`/`notes.md` (mirrors the propose "reviewer can be wrong" rule). A genuine NEEDS REVISION is a hard gate.

### D6 — Gate, recovery, and loop bound
Passes are numbered: Claude `1=self, 2=pro, 3=flash`; OpenCode `1=self, 2=flash`. On a pass's NEEDS REVISION (after the orchestrator confirms the defect is real from disk):
1. Fix via the **existing** defect re-delegation path (re-delegate a self-contained fix-spec to the apply-executor; one attempt; escalate to a Sonnet subagent on operational or quality failure; disclose if Sonnet was used).
2. **Re-run the pass that failed and every pass after it**, in order — never the earlier passes. (Operator decision.)
**Loop bound:** if the same pass returns NEEDS REVISION across **3** fix cycles without clearing, STOP and escalate to the operator with the accumulated verdicts (mirrors the reviewer's max-3). A pass-1 (self-review) failure is the existing behavioral-review-fails path: fix, re-run from pass 1.

### D7 — noninteractive-delegation-safety is extended, not just referenced
Two MODIFIED edits to that spec keep its invariant complete:
- **Invocation enumeration:** the Claude Code verifier passes (the pro and flash `opencode run` calls) join the enumerated set (propose reviewer, apply executor, archive executor, verify fix-executor) that SHALL close stdin and pass `--dir <repoRoot>`. The **OpenCode** verifier pass is an in-process Task-tool spawn, not an `opencode run`, so it is explicitly out of scope for the stdin-hang requirement (no separate process, no TTY-stdin to block).
- **Permission taxonomy:** add the third category — a bash-capable, write-denied agent (`bash: allow`, `edit: deny`) SHALL take executor-style `external_directory` containment.

### D8 — Audit trail in report + notes.md
The verification report gains a "Multi-model passes" subsection listing each pass (self / pro / flash), its model, its verdict, and the defects it caught. `notes.md` field 3 ("defect found and how it was fixed") is extended to attribute *which pass/model* surfaced each defect. This makes the multi-model gate auditable and records which model caught what (the project's separate-model-catches-real-defects discipline, now measurable).

## Risks / Trade-offs

- **Rerun-failed-and-after can let a late fix slip a new defect past earlier passes** → a fix for a flash-pass finding is not re-checked by the self-review or pro pass. Mitigation: the orchestrator confirms and judges every later pass from disk; flash (cheapest) is always last so its fixes trigger the least rerun; the residual is an accepted, monitored trade-off (operator decision), recorded as an open question.
- **Extra test-suite runs (1–2 per verify)** → cost/latency at the final gate. Mitigation: accepted; verify is the lowest-frequency, highest-stakes phase; flash is cheap.
- **A delegated verifier could hallucinate a defect (false NEEDS REVISION)** → wasted fix cycle. Mitigation: from-disk confirmation before any fix; overrule-with-rationale path; 3-cycle bound → operator.
- **`bash: allow` on a delegated agent** → arbitrary command exposure. Mitigation: identical posture to the existing apply/archive executors (already bash-capable here); verifier is strictly less capable (no `edit`/`task`); `--dir` + `external_directory` containment; destructive-command denylist deferred as an open question.

## Migration Plan

Additive and scaffold-only. Rollback = revert the new agent file + skill/spec/doc edits; no state migration, no external dependency. The gate is inert until propagated to extrends/psc-monitor (separate, operator-gated change). Deploy order at apply: create the verifier agent → wire the skill chain → write the spec deltas → reconcile AGENTS.md/README.md.

## Open Questions

- **Rerun-and-after residual risk** (D6/Risks): should a passing release ever force a full self→…→flash re-run after the final fix? Deferred; current decision is rerun-failed-and-after only.
- **Bash destructive-command denylist** for bash-capable delegated agents (verifier + executors): deferred; not added here.
- **OpenCode Task-tool model pinning:** confirmed-by-design that `subagent_type: openspec-verifier` runs the frontmatter model (flash); if a future OpenCode wants a pro pass it would need a model override mechanism not assumed here.

## Verification

Change-specific acceptance criteria (testable at this change's apply/verify):
- **V1** — `.claude/skills/openspec-verify-change/SKILL.md` documents both chains (Claude self→pro→flash; OpenCode self→flash), each delegated pass with its hardened invocation, inserted immediately after the MANDATORY behavioral-review block and before the artifact/spec mapping checklist (the current step 5 "Verify Completeness") and the report/`notes.md` steps.
- **V2** — `.opencode/agents/openspec-verifier.md` exists with exactly the D4 permission block (`read`/`glob`/`grep`/`list`/`bash` allow; `edit`/`task`/`webfetch`/`websearch` deny; `external_directory` `"*": deny` + `/tmp/**: allow`) and default `model: deepseek/deepseek-v4-flash`.
- **V3** — The skill specifies rerun-failed-and-after recovery, the existing re-delegation fix path, the 3-cycle loop bound, and operator escalation.
- **V4** — The skill specifies the `## Verify Pass` / `VERDICT:` verdict format, the "assert real verifier ran" checks (fallback-warning grep + format check), and from-disk judgment with overrule-with-rationale.
- **V5** — `specs/verify-multimodel-gate/spec.md` captures the chain + gate + verifier contract; `specs/noninteractive-delegation-safety/spec.md` delta adds the Claude verifier passes to the invocation enumeration AND the third permission category.
- **V6 (live integration probe, at verify)** — invoke `opencode run --agent openspec-verifier --model deepseek/deepseek-v4-flash --dir <repoRoot> "<the fixed verifier prompt from D5>" < /dev/null` against a trivial real diff and confirm: (a) no `Falling back to default agent`, (b) it actually runs the suite via bash, (c) it emits a parseable `## Verify Pass` + `VERDICT:` block, (d) an `edit` attempt is denied.

### Live Probe

No propose-time external-API probe is required: this change adds no new code-level external-library surface. Its only external surface is the opencode delegation integration, and every assumption it relies on reuses an already-proven mechanism in this repo:
- `--model` overriding frontmatter — documented and used in `.claude/skills/openspec-propose/SKILL.md` (the reviewer invocation) and the verify fix-executor invocation.
- `bash: allow` on a delegated deepseek agent — proven by `.opencode/agents/apply-executor.md` and `archive-executor.md`.
- `edit: deny` on a delegated deepseek agent — proven by `.opencode/agents/openspec-reviewer.md`.
- `external_directory: { "*": deny, "/tmp/**": allow }` — proven by both executors.
- OpenCode `subagent_type` spawn of a project agent — proven by the propose skill's OpenCode branch (`subagent_type: "openspec-reviewer"`).
The only genuinely *new* artifact is the **combination** of `bash: allow` + `edit: deny` in one agent (independent opencode permission keys, expected to compose). Because the production agent does not exist until apply, this combination is validated by **V6 at the verify phase of this change**, not by a throwaway probe at propose time.
