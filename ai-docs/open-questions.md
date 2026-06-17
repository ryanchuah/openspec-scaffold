# Open Questions

Unresolved questions and user-action items. Remove an entry once resolved (record the resolution in decisions.md if it was a meaningful choice).

---

<!-- Add entries as questions arise. -->

## harden-delegation follow-ons (shipped 2026-06-16)

Delegated-work governance hardened: deterministic commit-test-gate, apply-executor non-convergence guard with structured blocker reporting, and reviewer budget/thoroughness protection. Full decision and rationale in `ai-docs/decisions.md` ("Scaffold ships the commit-test-gate hook", "Per-repo test command", "Apply-executor convergence detection offloaded to a deterministic helper", "Structured NON-CONVERGENCE BLOCKER block", "Reviewer budget raised to 780s"). Archive: `openspec/changes/archive/2026-06-16-harden-delegation`.

- **[RESOLVED 2026-06-16 — W0 smoke] Commit-test-gate hook wiring live-verified.** The `PreToolUse` hook fires on `Bash(git commit*)`, exit 2 blocks the commit, and `$CLAUDE_PROJECT_DIR` expands — all confirmed in a gated Claude session rooted in a throwaway hook-carrying repo (checks a/b/c passed; script-layer 5-branch smoke also re-confirmed). Resolution + evidence in `ai-docs/decisions.md` ("Commit-test-gate hook wiring live-verified — W0 smoke passed"). Non-obvious gotcha recorded there: the smoke must run from a session whose PROJECT ROOT carries the hook (hooks load once from the project root, not from cwd). Two W0 carry-forwards remain: audit **A5** (cwd no-op) confirmed real → folds into W3; **E5** (opencode skill-enumeration functional smoke; version is 1.17.7) → W5 / next OpenCode session. **→ E5 RESOLVED by W5 (2026-06-17): live skill-enumeration smoke passed against opencode 1.17.7 — all 7 `openspec-*` skills enumerated from `.claude/skills/`, cross-load flag `<unset>`. Procedure + evidence: `docs/test/skill-enumeration-smoke/README.md`; decision: `ai-docs/decisions.md` ("opencode skill-enumeration smoke — W5"). A5 still open → W3.**
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
- **Live hook-wiring smoke RESOLVED 2026-06-16 (W0).** The `PreToolUse` wiring is verified (fires on `git commit`, exit 2 blocks, `$CLAUDE_PROJECT_DIR` expands). See the resolved entry above and `ai-docs/decisions.md` ("Commit-test-gate hook wiring live-verified — W0 smoke passed").
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

## fix-sync-mechanism follow-ons (shipped 2026-06-17)

The scaffold→downstream sync mechanism shipped: `scripts/sync_scaffold.py` (byte-identical copy with AGENTS.md span-replace), `scripts/scaffold_manifest.txt` (self-listed manifest), `scripts/scaffold_check.py` (PreToolUse guard, exit 2), and `scripts/test_sync_scaffold.py` (unit tests). Scaffold-only; no downstream propagation in this change. Full decision in `ai-docs/decisions.md` ("fix-sync-mechanism (2026-06-17)"). Archive: `openspec/changes/archive/2026-06-17-fix-sync-mechanism`. New spec: `openspec/specs/scaffold-sync-mechanism/spec.md`.

- **Guard coverage limit (M1) — carried, not closed.** `scaffold_check.py` only intercepts Claude Bash-tool commits; operator-terminal and opencode/deepseek executor commits bypass it; `--no-verify` is the sanctioned escape. The W6 manual diff is the backstop. Operator may later want a repo-wide `core.hooksPath`/`.git/hooks/pre-commit` (considered and rejected for W1) — revisit only if silent downstream drift actually occurs.
- **`--check` AGENTS.md first-run cosmetic DIFFERS (D6 caveat).** A formatting mismatch at the span2/tail join boundary can cause a one-time `AGENTS.md DIFFERS` on the first `--check`; running `sync_scaffold.py` once normalizes it, after which `--check` is idempotently clean. Cosmetic, not a correctness bug — but W6 should expect it and not treat a first-run AGENTS.md DIFFERS as real drift.
- **Manifest staleness (R3).** The manifest is self-managed; a newly-added shared file that nobody lists is invisible to sync until the manifest is updated. No automated catch in W1 — W6's drift check is the backstop. Also: `ai-docs/opencode-delegation-notes.md` is deliberately **absent** from the manifest (it does not exist in scaffold yet); it must be promoted into scaffold + added to the manifest in a later dedup/propagation change before it can sync.
- **R1 line-anchored span risk (accepted).** A downstream `## Project context` that itself contained a literal line `## Roles` would mis-slice the AGENTS.md span boundaries. Accepted as low-risk (project context is short, hand-curated) and noted in design R1. No guard added by choice.
- **Live guard hook smoke is W6.** The guard's `git diff --cached` integration is unit-stubbed here; the live `git commit` hook smoke in downstream repos (verifying the PreToolUse wiring blocks on exit 2) is W6, riding the W0-verified exit-2 mechanism.

## dedup-scaffold (W2) follow-ons (shipped 2026-06-17)

W2 single-sourced the `opencode run` delegation harness: the shared invocation/assert-ran/surgical-kill/
EXIT-sentinel prose + the timeout budgets now live once in `ai-docs/delegation-harness.md`, with the four
delegating skills (apply/verify/propose/archive) reduced to citations + their per-phase specifics. Scope
was C1 + B3 only (C2 rule-restatements → W6; C4 `.claude`/`.opencode` body-agreement guard → W4). Archive:
`openspec/changes/archive/2026-06-17-dedup-scaffold` (pending). Three follow-ups surfaced and are logged
here at operator instruction:

- **[BUG — archive-executor omits the EXIT-sentinel] (MED, pre-existing).** `openspec-archive-change`
  backgrounds its executor (`run_in_background: true`) but its `opencode run` invocation does **not** append
  `; echo "EXIT=$?" > /tmp/archive-out.exit` — it is the only backgrounded delegation missing the sentinel
  (apply + verify have it; propose is synchronous and correctly doesn't need it). So the harness §(d)
  completion-detection contract (poll `[ -f …archive-out.exit ]`; conclude crash/timeout only on exit
  124/137) **cannot work for archive**, and the archive skill's own "exit 124 = operational crash" line
  references an exit code it never captures. Latent because archive usually finishes fast / leans on the
  harness background-completion notification, but timeout/crash detection there is unreliable. **One-line
  fix:** append the sentinel exactly like apply. Pre-existing C1 drift, surfaced (and documented inline in
  the archive skill + doc §d) by W2 but deliberately **not fixed** (extraction-not-redesign). Candidate for
  a tiny standalone follow-up change.
- **[Orchestration — stress slicing large changes into task ranges] (MED).** The first W2 apply **timed
  out** (`EXIT=124`): all 13 tasks were dispatched to deepseek-flash in one 600s `opencode run`; flash was
  making real progress (it finished the doc + the apply skill) but the budget couldn't cover the whole
  extraction. The apply skill *already* advises "prefer splitting delegation across task ranges over
  raising the ceiling" — but the guidance is easy to miss and was missed here (monolithic dispatch). The
  harness's EXIT-sentinel correctly **detected** the timeout (it's a completion-*detection* mechanism, not
  a budget fix) and the tight-brief + 780s retry recovered it. Follow-up: make the "slice big MEDIUM/COMPLEX
  changes" guidance more load-bearing/prominent (apply skill and/or the tier-confirmation+plan step), so
  the orchestrator slices rather than dispatching a fat change in one shot.
- **[Tier-scale the delegation timeout budgets] (MED).** The `delegation-harness.md` §(e) timeout table is
  fixed per phase (apply 600s regardless of change size), so a large change pays the same budget as a
  one-task change → spurious timeouts like the one above. Consider scaling the apply/verify budgets by
  change tier or task count (rhymes with audit **B2** "verify gate not tier-scaled"). Currently a deliberate
  non-goal; revisit as a hardening change. Pairs naturally with the slicing item above.

## lifecycle-gates (W4) follow-ons (shipped 2026-06-17)

The verify gate was tier-scaled (SMALL exempted from multi-model passes), a simplicity/quality gate and a conditional security gate were added to verify, the archive-executor bodies were hardened for RENAMED spec requirements, and a new `scripts/test_executor_body_agreement.py` guard byte-compares each executor pair's body. Six audit findings (E1/B2/D-ii/E3/D-i/C4) folded into one MEDIUM change. Full decision in `ai-docs/decisions.md` ("lifecycle-gates (2026-06-17)"). Archive: `openspec/changes/archive/2026-06-17-lifecycle-gates`. Modified spec: `openspec/specs/verify-multimodel-gate/spec.md`.

- **C4 guard coverage is partial (LOW).** `test_executor_body_agreement.py` checks only the apply-executor + archive-executor pairs. The `openspec-reviewer` and `openspec-verifier` agents exist as `.opencode`-only agents (no `.claude` twin), so they are out of scope today. If a `.claude` counterpart is ever added for either, extend the guard to that pair.
- **Gates reference Claude-only harness skills (MED).** The simplicity gate (`simplify`/`/code-review`) and security gate (`security-review`) reference Claude Code built-in skills that do not live in the scaffold tree. If those skills are renamed or removed harness-side, the Claude path silently degrades — the concrete OpenCode checklists are the durable floor. No automated detection of this degradation exists.
- **SMALL is now formally exempt from the verify gate (MED).** A SMALL change does its own verification and MAY run a single optional flash pass at orchestrator discretion. Monitor that risky SMALL changes (e.g., auth or data-touching one-liners) aren't under-verified in practice. The orchestrator's judgment on what constitutes "risky" is the sole gate.
- **Scaffold-only; propagation is W6 (HIGH).** The new `scripts/test_executor_body_agreement.py` guard and its manifest entry join the W6 one-time snapshot to extrends/psc-monitor. Until then, the guard is inert downstream — executor-pair drift in consuming repos is not checked.
