# Open Questions

Unresolved questions and user-action items. Remove an entry once resolved (record the resolution in decisions.md if it was a meaningful choice).

---

<!-- Add entries as questions arise. -->

## harden-delegation follow-ons (shipped 2026-06-16)

Delegated-work governance hardened: deterministic commit-test-gate, apply-executor non-convergence guard with structured blocker reporting, and reviewer budget/thoroughness protection. Full decision and rationale in `ai-docs/decisions.md` ("Scaffold ships the commit-test-gate hook", "Per-repo test command", "Apply-executor convergence detection offloaded to a deterministic helper", "Structured NON-CONVERGENCE BLOCKER block", "Reviewer budget raised to 780s"). Archive: `openspec/changes/archive/2026-06-16-harden-delegation`.

- **[REQUIRED] Live-smoke-test the commit-test-gate hook wiring in a gated Claude session.** The script-layer behavior is now verified across all five branches (smoke fixture at `docs/test/commit-gate-smoke/`), but the hook *wiring* — that Claude Code fires the `PreToolUse` hook on `Bash(git commit*)`, that exit code 2 blocks the commit, and that `$CLAUDE_PROJECT_DIR` expands — still needs a live smoke in a gated Claude session (procedure documented in `docs/test/commit-gate-smoke/`). This cannot be automated from a non-gated session. **BLOCKING** — gates reliance on the gate in consuming repos.
- **Monitor rule (a) threshold** — the convergence helper stops after the second same-signature observation (the first fix attempt), slightly stricter than "2 fix attempts." Monitor on real applies; loosen if too eager.
- **OpenCode-side gate plugin (v2)** still deferred — OpenCode-driven commits are NOT gated. Also recorded in design Non-Goals and in decisions.md "Scaffold ships the commit-test-gate hook" (residual gap).
- **Reviewer incremental-emission quality** — observe the first few real reviews after this change; revert the prompt nudge if any review drops to zero findings against the non-incremental baseline or the reviewer reports format confusion.
- **Propagation to extrends + psc-monitor** — this hardening is inert until propagated (the scaffold gate is a no-op locally since there is no `scripts/test-cmd`). The forthcoming single-source change will carry the shared files.

## harden-instruction-surface follow-ons (shipped 2026-06-16)

Instruction-surface audit reconciled six stale/hazardous first-load instruction sites and added a tier-confirmation gate: non-fast-track agents must now confirm the change tier and plan with the operator before executing. The fast-track failure ladder was aligned with the declared-blocker triage routing, the "hook-free" claim about `.claude/settings.json` was corrected, the orchestrator's verify re-run was single-sourced from `scripts/test-cmd`, the research-fetch convention was completed, and the onboard tutorial was fixed. Docs/instruction-only change — no code, no test suite in scaffold, ran clean. Full decision in `ai-docs/decisions.md` ("Tier-confirmation gate for non-fast-track agents") and "Scaffold ships the commit-test-gate hook" (post-hoc note). Archive: `openspec/changes/archive/2026-06-16-harden-instruction-surface`. New spec: `openspec/specs/tier-confirmation-gate/spec.md`. Modified specs: `openspec/specs/apply-convergence-guard/spec.md`, `openspec/specs/commit-test-gate/spec.md`.

- **Propagation backlog (HIGH).** This change is scaffold-only. `extrends` and `psc-monitor` still carry the identical stale text (hook-free line, fast-track ladder, hard-coded pytest, missing web rule (d), onboard Verify checkbox, "~2 lines"). There are now THREE scaffold changes awaiting propagation — `harden-delegation`, `harden-instruction-surface`, and `harden-delegation-robustness` — all ride on the single-source "change 2".
- **Web-research convention still duplicated (MED).** This change only made the two copies agree (added rule (d) to `research-fetch-convention.md`); AGENTS.md §9 and `research-fetch-convention.md` are still two sources of the same rules. Full single-sourcing deferred to change 2.
- **Deferred audit findings from harden-instruction-surface (MED), not addressed here:**
  - War-story narrative duplicated ~3× across instruction surfaces.
  - Model-assignment matrix duplicated ~5×.
  - The apply "Completion detection" block and the verify MANDATORY block bury the happy path under stacked exceptions (convolution, "M7").
  - Onboard kept as a simplified teaching path (design D6b) rather than fully delegated, by deliberate decision.
- **Reference-rot watch (LOW).** `fast-track-workflow.md` now references the apply skill's ladder by path (`.claude/skills/openspec-apply-change/SKILL.md`); a rename/move of that skill must update this reference. (Recorded in design Risks.)

## harden-delegation-robustness follow-ons (shipped 2026-06-16)

Delegation robustness hardened: all delegated `opencode run` invocations close stdin to prevent permission-prompt hangs, per-agent `external_directory` permissions contain write-capable executors, the non-convergence canary is rebuilt as a non-gameable impl-module+frozen-test, and the commit-test-gate ships a smoke fixture with documented hook-wiring procedure. Full decisions in `ai-docs/decisions.md` ("Delegated `opencode run` closes stdin", "Per-agent `external_directory` posture", "The non-convergence canary is an impl-module + instruction-frozen test"). Archive: `openspec/changes/archive/2026-06-16-harden-delegation-robustness`. New spec: `openspec/specs/noninteractive-delegation-safety/spec.md`. Extended specs: `openspec/specs/apply-convergence-guard/spec.md`, `openspec/specs/commit-test-gate/spec.md`.

- **Propagation backlog (HIGH).** This change is scaffold-only and inert in `extrends` and `psc-monitor` — the hang persists there until the single-source "change 2" carries the shared agent/skill files. There are now THREE scaffold changes awaiting propagation (harden-delegation, harden-instruction-surface, harden-delegation-robustness). Operator chose scaffold-only for now (2026-06-16).
- **Live hook-wiring smoke STILL PENDING.** Only the script layer is verified; the `PreToolUse` wiring (fires on `git commit`, exit 2 blocks, `$CLAUDE_PROJECT_DIR` expands) needs a gated Claude session. Procedure documented in `docs/test/commit-gate-smoke/`. This is the residual of the original `[REQUIRED]` hook-smoke open-question above (narrowed, not resolved).
- **`question: deny` deferred.** opencode's `question` permission also defaults to `ask` and could theoretically trigger an unanswerable prompt, but its runtime behavior was not probed. The stdin close neutralizes it generically. Adopt later if a question-path hang is ever observed despite `< /dev/null`.
- **Optional `bash` destructive-command denylist** for the write-capable executors (defense-in-depth beyond the `external_directory` path containment). Deferred unless the operator wants it in scope.
- **`doom_loop` left at default `ask`.** Neutralized generically by the stdin close, not pinned per agent. Monitor: if a doom-loop-specific hang is ever seen despite `< /dev/null`, pin it per-agent.
- **Canary trigger is a/b/c, not a fixed `a`.** Deliberate: pytest re-renders the failure signature as the impl changes, so the canary cannot promise a single fixed trigger. The guarantee is a declared stop, not a specific trigger. If a deterministic single trigger is ever wanted, a different fixture is required.

## verify-multimodel-gate follow-ons (shipped 2026-06-16)

Independent multi-model verification passes added as hard gates in the verify step: a new `openspec-verifier` agent runs the behavioral review read-only with a machine-discriminable verdict; platform-specific chains (Claude self→pro→flash, OpenCode self→flash); rerun-failed-and-after recovery; three-cycle escalation bound. The gate was dogfooded on its own change — all three passes returned READY with no defects. Full decision in `ai-docs/decisions.md` ("Independent multi-model verification passes as hard gates in the verify step"). Archive: `openspec/changes/archive/2026-06-16-verify-multimodel-gate`. New spec: `openspec/specs/verify-multimodel-gate/spec.md`. Modified spec: `openspec/specs/noninteractive-delegation-safety/spec.md`.

- **Rerun-failed-and-after residual risk (monitored).** A fix for a late pass is not re-checked by earlier passes — e.g., a flash-pass fix is never seen by the self-review or pro pass. Accepted/monitored trade-off (operator decision); the orchestrator still judges every later pass from disk, and flash (cheapest) is always last. Open: should a passing release ever force a full self→…→flash re-run after the final fix? Deferred.
- **OpenCode Task-tool verifier path not live-probed.** The Claude Code `opencode run` passes (pro + flash) were exercised live against this change and returned READY, but the OpenCode `subagent_type: openspec-verifier` path (runs frontmatter-default flash) is confirmed-by-design and not probed under a real OpenCode orchestrator. Probe when next on OpenCode.
- **V6(d) edit-denial not separately probed.** The verifier's read-only behavior was observed throughout the live passes, and `edit: deny` is structurally present in the agent frontmatter (the same permission model proven by the existing `openspec-reviewer`), but no test forced an edit attempt to see it explicitly denied. Low risk.
- **Bash destructive-command denylist deferred.** Defense-in-depth beyond `external_directory` containment for bash-capable delegated agents (verifier + apply/archive executors). Deferred unless the operator wants it in scope.
- **Scaffold has no runnable test suite** (`scripts/test-cmd` absent + no venv, by design). For this docs/config-only change, verification leaned on `openspec validate --strict` + the V6 live probe. Future code-bearing changes (especially in propagated repos) still need a real green suite per the verify skill.
- **Propagation backlog (HIGH).** This gate is scaffold-only and inert until propagated to extrends/psc (the single-source "change 2"). There are now FOUR scaffold changes (harden-delegation, harden-instruction-surface, harden-delegation-robustness, verify-multimodel-gate) awaiting that propagation. Already tracked in prior follow-ons above.
