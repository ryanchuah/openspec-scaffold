## Why

Verify is the final gate before a change is declared "good to release," yet today it rests on a single reviewer: the orchestrator's own behavioral self-review. One model's blind spots therefore decide release. Independent models reliably catch *different* falsifiable defects — a discipline this project already follows, and one that has repeatedly caught real blocking defects the primary missed. The highest-stakes gate should not be the one place we rely on a single set of eyes.

## What Changes

Add mandatory, independent **multi-model verification passes** to the verify step, layered **after** (never replacing) the orchestrator's existing self-review behavioral review. The self-review's "do not delegate this" rule is unchanged — the new passes are *additional independent verifications*, not a substitute.

- **Chain design (platform-specific).** The pass sequence depends on which platform the orchestrator is:
  - **Claude Code orchestrator:** self-review → `deepseek/deepseek-v4-pro` verifier pass → `deepseek/deepseek-v4-flash` verifier pass. Three independent passes.
  - **OpenCode orchestrator:** self-review → `deepseek/deepseek-v4-flash` verifier pass only. An OpenCode orchestrator already runs on deepseek-v4-pro, so a second pro view adds little model diversity; flash is the cheap independent second pair of eyes.
- **Gate semantics.** Each pass is a **hard gate**. On a pass's NEEDS-REVISION verdict, the orchestrator fixes the defect via the *existing* defect re-delegation path (re-delegate to the apply-executor, one attempt, escalate to Sonnet), then **re-runs the pass that failed and every pass after it** — never the passes before it. Accepted trade-off: re-running only the failed pass and later ones (not the earlier ones) means a fix could introduce a defect an earlier pass would have caught, and the orchestrator applying the fix is the same model that missed the original. This is accepted for cost/latency reasons — the orchestrator still judges every later pass's output from disk, and the cheaper flash pass is always last — but it is recorded as a monitored design risk.
- **Verifier agent contract.** A new delegated **verifier** agent runs the *same* behavioral review the self-review runs (read the diffs, re-run the full test suite, eyeball real output, run the live smoke for external-API changes) and emits a machine-discriminable verdict with file:line evidence. It is **read-only on files** (no `edit`/`write`); fixing defects stays the orchestrator's job.
- **Hardening.** The Claude Code path runs the verifier as two `opencode run` invocations (pro then flash), each hardened exactly like the rest of the workflow (`< /dev/null`, `--dir <repoRoot>`, bounded `timeout`, EXIT-file sentinel, "real agent ran" fallback-warning assertion). The OpenCode path spawns the verifier in-process via the Task tool (`subagent_type: openspec-verifier`); being in-process it is **not** subject to the `opencode run` stdin-hang failure mode, so the noninteractive-delegation-safety hardening applies to the Claude Code `opencode run` passes, not the Task-tool spawn.
- **Judgment from disk.** The orchestrator judges verifier findings **from disk** (`git diff` / re-run), treating them as leads to confirm rather than gospel, and may overrule a demonstrably false finding only with recorded rationale (mirrors the propose reviewer-can-be-wrong rule).
- **Audit trail.** The verification report and `notes.md` record each pass's verdict, the model that ran it, and which defect (if any) each pass caught.

## Capabilities

### New Capabilities
- `verify-multimodel-gate`: the verify step requires independent multi-model verification passes — the platform-specific chain, the hard-gate / rerun-failed-and-after recovery semantics, and the read-only delegated verifier agent contract — layered on top of the orchestrator's self-review.

### Modified Capabilities
- `noninteractive-delegation-safety`: (a) extend the "every delegated `opencode run` invocation in the OpenSpec workflow" hardening enumeration to include the new **Claude Code** verify verifier passes (close stdin via `< /dev/null`, pass `--dir <repoRoot>`); and (b) add an explicit **third permission category** to the agent-permission taxonomy for the verifier — a bash-capable but write-denied agent (`bash: allow`, `edit: deny`/`write: deny`) takes the executor-style `external_directory` containment (`"*": deny`, `/tmp/**: allow`), not the read-only reviewer's `external_directory: allow`, because bash makes it write-capable in practice.

## Impact

- **New agent:** `.opencode/agents/openspec-verifier.md` — deepseek; `read`/`bash` allowed, `edit`/`write`/`task` denied, executor-style `external_directory` containment (`"*": deny`, `/tmp/**: allow`). Strictly less capable than the existing apply-executor (which already runs deepseek+bash here), so it introduces **no new trust boundary**. Frontmatter default `model: deepseek/deepseek-v4-flash` so the OpenCode Task-tool spawn runs flash with no override; the Claude Code path selects the model per pass via `--model` (pro then flash).
- **Modified skill:** `.claude/skills/openspec-verify-change/SKILL.md` — insert the delegated pass chain after the self-review and before the report/`notes.md` steps; document both the Claude Code (`opencode run` ×2, pro then flash) and OpenCode (Task tool, flash only) invocation paths, plus the rerun-failed-and-after gate semantics.
- **Modified docs:** `AGENTS.md` and `README.md` — describe the multi-model verify gate alongside the existing reviewer/executor delegation roles.
- **Specs:** new `openspec/specs/verify-multimodel-gate/spec.md`; modified `openspec/specs/noninteractive-delegation-safety/spec.md` (both promoted at archive).
- **Cost / surface area:** adds 1–2 extra full test-suite runs per verify (the OpenCode path adds one flash pass; the Claude path adds a pro and a flash pass). The asymmetry is deliberate — the OpenCode orchestrator is already deepseek-v4-pro, so only a flash pass is needed for independent model diversity, whereas the Claude orchestrator (Anthropic model) gains diversity from both deepseek tiers. An accepted cost at the final release gate. No change to the propose, apply, or archive phases.
