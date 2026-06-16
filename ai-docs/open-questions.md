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
