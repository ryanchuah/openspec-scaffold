# Open Questions

Unresolved questions and user-action items. Remove an entry once resolved (record the resolution in decisions.md if it was a meaningful choice).

---

<!-- Add entries as questions arise. -->

## harden-delegation follow-ons (shipped 2026-06-16)

Delegated-work governance hardened: deterministic commit-test-gate, apply-executor non-convergence guard with structured blocker reporting, and reviewer budget/thoroughness protection. Full decision and rationale in `ai-docs/decisions.md` ("Scaffold ships the commit-test-gate hook", "Per-repo test command", "Apply-executor convergence detection offloaded to a deterministic helper", "Structured NON-CONVERGENCE BLOCKER block", "Reviewer budget raised to 780s"). Archive: `openspec/changes/archive/2026-06-16-harden-delegation`.

- **[REQUIRED] Live-smoke-test the commit-test-gate hook in a Claude session before relying on the gate in any consuming repo.** The `PreToolUse` hook wiring (firing on `Bash(git commit*)` and blocking on exit 2) was doc-verified but NOT live-tested — hooks apply to the running Claude session and could not be safely sandboxed from this session. Smoke-test in a gated session (after propagation to extrends/psc, or a scaffold-based session): confirm a failing `test-cmd` blocks the commit, a passing `test-cmd` permits it, and `$CLAUDE_PROJECT_DIR` expands correctly on the operator's Claude version. **BLOCKING** — gates reliance on the gate in consuming repos.
- **[REQUIRED] Harden the canary fixture.** `docs/test/canary-non-convergence` is gameable — the impossibility (`assert 1+1==3`) lives in the same file the executor may edit, so it could be made green by editing the assertion. Move the contradiction into an impl module the test imports (e.g. `assert add(1,1)==2 and add(1,1)==3`) and forbid editing the test, so the executor is forced into genuine non-convergence. **BLOCKING** — gates reliable e2e canary verification of the convergence guard.
- **Monitor rule (a) threshold** — the convergence helper stops after the second same-signature observation (the first fix attempt), slightly stricter than "2 fix attempts." Monitor on real applies; loosen if too eager.
- **OpenCode-side gate plugin (v2)** still deferred — OpenCode-driven commits are NOT gated. Also recorded in design Non-Goals and in decisions.md "Scaffold ships the commit-test-gate hook" (residual gap).
- **Reviewer incremental-emission quality** — observe the first few real reviews after this change; revert the prompt nudge if any review drops to zero findings against the non-incremental baseline or the reviewer reports format confusion.
- **Propagation to extrends + psc-monitor** — this hardening is inert until propagated (the scaffold gate is a no-op locally since there is no `scripts/test-cmd`). The forthcoming single-source change will carry the shared files.

## harden-instruction-surface follow-ons (shipped 2026-06-16)

Instruction-surface audit reconciled six stale/hazardous first-load instruction sites and added a tier-confirmation gate: non-fast-track agents must now confirm the change tier and plan with the operator before executing. The fast-track failure ladder was aligned with the declared-blocker triage routing, the "hook-free" claim about `.claude/settings.json` was corrected, the orchestrator's verify re-run was single-sourced from `scripts/test-cmd`, the research-fetch convention was completed, and the onboard tutorial was fixed. Docs/instruction-only change — no code, no test suite in scaffold, ran clean. Full decision in `ai-docs/decisions.md` ("Tier-confirmation gate for non-fast-track agents") and "Scaffold ships the commit-test-gate hook" (post-hoc note). Archive: `openspec/changes/archive/2026-06-16-harden-instruction-surface`. New spec: `openspec/specs/tier-confirmation-gate/spec.md`. Modified specs: `openspec/specs/apply-convergence-guard/spec.md`, `openspec/specs/commit-test-gate/spec.md`.

- **Propagation backlog (HIGH).** This change is scaffold-only. `extrends` and `psc-monitor` still carry the identical stale text (hook-free line, fast-track ladder, hard-coded pytest, missing web rule (d), onboard Verify checkbox, "~2 lines"). There are now TWO scaffold changes awaiting propagation — `harden-delegation` and `harden-instruction-surface` — both ride on the single-source "change 2".
- **Web-research convention still duplicated (MED).** This change only made the two copies agree (added rule (d) to `research-fetch-convention.md`); AGENTS.md §9 and `research-fetch-convention.md` are still two sources of the same rules. Full single-sourcing deferred to change 2.
- **Deferred audit findings from harden-instruction-surface (MED), not addressed here:**
  - War-story narrative duplicated ~3× across instruction surfaces.
  - Model-assignment matrix duplicated ~5×.
  - The apply "Completion detection" block and the verify MANDATORY block bury the happy path under stacked exceptions (convolution, "M7").
  - Onboard kept as a simplified teaching path (design D6b) rather than fully delegated, by deliberate decision.
- **Reference-rot watch (LOW).** `fast-track-workflow.md` now references the apply skill's ladder by path (`.claude/skills/openspec-apply-change/SKILL.md`); a rename/move of that skill must update this reference. (Recorded in design Risks.)
