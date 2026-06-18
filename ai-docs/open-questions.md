# Open Questions

Unresolved questions and user-action items. Remove an entry once resolved (record the resolution in decisions.md if it was a meaningful choice).

---

<!-- Add entries as questions arise. -->

## harden-delegation follow-ons (shipped 2026-06-16)

harden-delegation shipped 2026-06-16. Rationale: `ai-docs/decisions.md`; archive: `openspec/changes/archive/2026-06-16-harden-delegation`.

- **[RESOLVED 2026-06-16 — W0 smoke] Commit-test-gate hook wiring live-verified.** The `PreToolUse` hook fires on `Bash(git commit*)`, exit 2 blocks the commit, and `$CLAUDE_PROJECT_DIR` expands — all confirmed in a gated Claude session rooted in a throwaway hook-carrying repo (checks a/b/c passed; script-layer 5-branch smoke also re-confirmed). Resolution + evidence in `ai-docs/decisions.md` ("Commit-test-gate hook wiring live-verified — W0 smoke passed"). Non-obvious gotcha recorded there: the smoke must run from a session whose PROJECT ROOT carries the hook (hooks load once from the project root, not from cwd). Two W0 carry-forwards remain: audit **A5** (cwd no-op) confirmed real → folds into W3; **E5** (opencode skill-enumeration functional smoke; version is 1.17.7) → W5 / next OpenCode session. **→ E5 RESOLVED by W5 (2026-06-17): live skill-enumeration smoke passed against opencode 1.17.7 — all 7 `openspec-*` skills enumerated from `.claude/skills/`, cross-load flag `<unset>`. Procedure + evidence: `docs/test/skill-enumeration-smoke/README.md`; decision: `ai-docs/decisions.md` ("opencode skill-enumeration smoke — W5"). A5 RESOLVED by W3 (2026-06-17): `test-gate.sh` now `cd`s to the repo root before resolving the test command, so the gate blocks (exit 2) even when the hook fires from a non-repo-root cwd.**
- **Monitor rule (a) threshold** — the convergence helper stops after the second same-signature observation (the first fix attempt), slightly stricter than "2 fix attempts." Monitor on real applies; loosen if too eager.
- **OpenCode-side gate plugin (v2)** still deferred — OpenCode-driven commits are NOT gated. Also recorded in design Non-Goals and in decisions.md "Scaffold ships the commit-test-gate hook" (residual gap).
- **Reviewer incremental-emission quality** — observe the first few real reviews after this change; revert the prompt nudge if any review drops to zero findings against the non-incremental baseline or the reviewer reports format confusion.
- **Propagation to extrends + psc-monitor** — this hardening is inert until propagated (the scaffold gate is a no-op locally since there is no `scripts/test-cmd`). The forthcoming single-source change will carry the shared files.

## harden-instruction-surface follow-ons (shipped 2026-06-16)

harden-instruction-surface shipped 2026-06-16. Rationale: `ai-docs/decisions.md`; archive: `openspec/changes/archive/2026-06-16-harden-instruction-surface`. New spec: `openspec/specs/tier-confirmation-gate/spec.md`.

- **Propagation backlog (HIGH).** This change is scaffold-only. `extrends` and `psc-monitor` still carry the identical stale text (hook-free line, fast-track ladder, hard-coded pytest, missing web rule (d), onboard Verify checkbox, "~2 lines"). There are now THREE scaffold changes awaiting propagation — `harden-delegation`, `harden-instruction-surface`, and `harden-delegation-robustness` — all ride on the single-source "change 2".
- **Web-research convention still duplicated (MED).** This change only made the two copies agree (added rule (d) to `research-fetch-convention.md`); AGENTS.md §9 and `research-fetch-convention.md` are still two sources of the same rules. Full single-sourcing deferred to change 2.
- **Deferred audit findings from harden-instruction-surface (MED), not addressed here:**
  - War-story narrative duplicated ~3× across instruction surfaces.
  - Model-assignment matrix duplicated ~5×.
  - The apply "Completion detection" block and the verify MANDATORY block bury the happy path under stacked exceptions (convolution, "M7").
  - Onboard kept as a simplified teaching path (design D6b) rather than fully delegated, by deliberate decision.
- **Reference-rot watch (LOW).** `fast-track-workflow.md` now references the apply skill's ladder by path (`.claude/skills/openspec-apply-change/SKILL.md`); a rename/move of that skill must update this reference. (Recorded in design Risks.)

## harden-delegation-robustness follow-ons (shipped 2026-06-16)

harden-delegation-robustness shipped 2026-06-16. Rationale: `ai-docs/decisions.md`; archive: `openspec/changes/archive/2026-06-16-harden-delegation-robustness`. New spec: `openspec/specs/noninteractive-delegation-safety/spec.md`.

- **Propagation backlog (HIGH).** This change is scaffold-only and inert in `extrends` and `psc-monitor` — the hang persists there until the single-source "change 2" carries the shared agent/skill files. There are now THREE scaffold changes awaiting propagation (harden-delegation, harden-instruction-surface, harden-delegation-robustness). Operator chose scaffold-only for now (2026-06-16).
- **Live hook-wiring smoke RESOLVED 2026-06-16 (W0).** The `PreToolUse` wiring is verified (fires on `git commit`, exit 2 blocks, `$CLAUDE_PROJECT_DIR` expands). See the resolved entry above and `ai-docs/decisions.md` ("Commit-test-gate hook wiring live-verified — W0 smoke passed").
- **`question: deny` deferred.** opencode's `question` permission also defaults to `ask` and could theoretically trigger an unanswerable prompt, but its runtime behavior was not probed. The stdin close neutralizes it generically. Adopt later if a question-path hang is ever observed despite `< /dev/null`.
- **Optional `bash` destructive-command denylist** for the write-capable executors (defense-in-depth beyond the `external_directory` path containment). Deferred unless the operator wants it in scope.
- **`doom_loop` left at default `ask`.** Neutralized generically by the stdin close, not pinned per agent. Monitor: if a doom-loop-specific hang is ever seen despite `< /dev/null`, pin it per-agent.
- **Canary trigger is a/b/c, not a fixed `a`.** Deliberate: pytest re-renders the failure signature as the impl changes, so the canary cannot promise a single fixed trigger. The guarantee is a declared stop, not a specific trigger. If a deterministic single trigger is ever wanted, a different fixture is required.

## verify-multimodel-gate follow-ons (shipped 2026-06-16)

verify-multimodel-gate shipped 2026-06-16. Rationale: `ai-docs/decisions.md`; archive: `openspec/changes/archive/2026-06-16-verify-multimodel-gate`. New spec: `openspec/specs/verify-multimodel-gate/spec.md`.

- **Rerun-failed-and-after residual risk (monitored).** A fix for a late pass is not re-checked by earlier passes — e.g., a flash-pass fix is never seen by the self-review or pro pass. Accepted/monitored trade-off (operator decision); the orchestrator still judges every later pass from disk, and flash (cheapest) is always last. Open: should a passing release ever force a full self→…→flash re-run after the final fix? Deferred.
- **OpenCode Task-tool verifier path not live-probed.** The Claude Code `opencode run` passes (pro + flash) were exercised live against this change and returned READY, but the OpenCode `subagent_type: openspec-verifier` path (runs frontmatter-default flash) is confirmed-by-design and not probed under a real OpenCode orchestrator. Probe when next on OpenCode.
- **V6(d) edit-denial not separately probed.** The verifier's read-only behavior was observed throughout the live passes, and `edit: deny` is structurally present in the agent frontmatter (the same permission model proven by the existing `openspec-reviewer`), but no test forced an edit attempt to see it explicitly denied. Low risk.
- **Bash destructive-command denylist deferred.** Defense-in-depth beyond `external_directory` containment for bash-capable delegated agents (verifier + apply/archive executors). Deferred unless the operator wants it in scope.
- **Scaffold has no runnable test suite** (`scripts/test-cmd` absent + no venv, by design). For this docs/config-only change, verification leaned on `openspec validate --strict` + the V6 live probe. Future code-bearing changes (especially in propagated repos) still need a real green suite per the verify skill.
- **Propagation backlog (HIGH).** This gate is scaffold-only and inert until propagated to extrends/psc (the single-source "change 2"). There are now FOUR scaffold changes (harden-delegation, harden-instruction-surface, harden-delegation-robustness, verify-multimodel-gate) awaiting that propagation. Already tracked in prior follow-ons above.

## fix-sync-mechanism follow-ons (shipped 2026-06-17)

fix-sync-mechanism shipped 2026-06-17. Rationale: `ai-docs/decisions.md`; archive: `openspec/changes/archive/2026-06-17-fix-sync-mechanism`. New spec: `openspec/specs/scaffold-sync-mechanism/spec.md`.

- **Guard coverage limit (M1) — carried, not closed.** `scaffold_check.py` only intercepts Claude Bash-tool commits; operator-terminal and opencode/deepseek executor commits bypass it; `--no-verify` is the sanctioned escape. The W6 manual diff is the backstop. Operator may later want a repo-wide `core.hooksPath`/`.git/hooks/pre-commit` (considered and rejected for W1) — revisit only if silent downstream drift actually occurs.
- **`--check` AGENTS.md first-run cosmetic DIFFERS (D6 caveat).** A formatting mismatch at the span2/tail join boundary can cause a one-time `AGENTS.md DIFFERS` on the first `--check`; running `sync_scaffold.py` once normalizes it, after which `--check` is idempotently clean. Cosmetic, not a correctness bug — but W6 should expect it and not treat a first-run AGENTS.md DIFFERS as real drift.
- **Manifest staleness (R3).** The manifest is self-managed; a newly-added shared file that nobody lists is invisible to sync until the manifest is updated. No automated catch in W1 — W6's drift check is the backstop. Also: `ai-docs/opencode-delegation-notes.md` is deliberately **absent** from the manifest (it does not exist in scaffold yet); it must be promoted into scaffold + added to the manifest in a later dedup/propagation change before it can sync.
- **R1 line-anchored span risk (accepted).** A downstream `## Project context` that itself contained a literal line `## Roles` would mis-slice the AGENTS.md span boundaries. Accepted as low-risk (project context is short, hand-curated) and noted in design R1. No guard added by choice.
- **Live guard hook smoke is W6.** The guard's `git diff --cached` integration is unit-stubbed here; the live `git commit` hook smoke in downstream repos (verifying the PreToolUse wiring blocks on exit 2) is W6, riding the W0-verified exit-2 mechanism.

## dedup-scaffold (W2) follow-ons (shipped 2026-06-17)

dedup-scaffold shipped 2026-06-17. Rationale: `ai-docs/decisions.md`; archive: `openspec/changes/archive/2026-06-17-dedup-scaffold`.

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

lifecycle-gates shipped 2026-06-17. Rationale: `ai-docs/decisions.md`; archive: `openspec/changes/archive/2026-06-17-lifecycle-gates`.

- **C4 guard coverage is partial (LOW).** `test_executor_body_agreement.py` checks only the apply-executor + archive-executor pairs. The `openspec-reviewer` and `openspec-verifier` agents exist as `.opencode`-only agents (no `.claude` twin), so they are out of scope today. If a `.claude` counterpart is ever added for either, extend the guard to that pair.
- **Gates reference Claude-only harness skills (MED).** The simplicity gate (`simplify`/`/code-review`) and security gate (`security-review`) reference Claude Code built-in skills that do not live in the scaffold tree. If those skills are renamed or removed harness-side, the Claude path silently degrades — the concrete OpenCode checklists are the durable floor. No automated detection of this degradation exists.
- **SMALL is now formally exempt from the verify gate (MED).** A SMALL change does its own verification and MAY run a single optional flash pass at orchestrator discretion. Monitor that risky SMALL changes (e.g., auth or data-touching one-liners) aren't under-verified in practice. The orchestrator's judgment on what constitutes "risky" is the sole gate.
- **Scaffold-only; propagation is W6 (HIGH).** The new `scripts/test_executor_body_agreement.py` guard and its manifest entry join the W6 one-time snapshot to extrends/psc-monitor. Until then, the guard is inert downstream — executor-pair drift in consuming repos is not checked.

## fix-convergence-guard (W3) follow-ons (shipped 2026-06-17)

fix-convergence-guard shipped 2026-06-17. Rationale: `ai-docs/decisions.md`; archive: `openspec/changes/archive/2026-06-17-fix-convergence-guard`.

- **Minor cleanup — redundant `_FINGERPRINTS_KEY` re-assignment on the CONTINUE path (LOW).** `scripts/_convergence.py` re-assigns the fingerprints dict on the CONTINUE path even though it was already assigned earlier. Harmless (same value, no side effects), but a tiny readability cleanup candidate for a future sweep.
- **`openspec validate <change-id>` does not recognize MEDIUM tasks-only changes (LOW).** W3 is a MEDIUM change with `tasks.md` only (no `proposal.md`, no change-scoped `specs/` delta). `openspec validate fix-convergence-guard` would fail because it expects at minimum a `proposal.md`. Validation for this change was via the live spec (`openspec validate --all`), which passed 8/8. Consider teaching `openspec validate` about MEDIUM tasks-only changes so the command works uniformly across tiers.

## propagate-baseline (W6) follow-ons (shipped 2026-06-17)

propagate-baseline shipped 2026-06-17. Rationale: `ai-docs/decisions.md`; archive: `openspec/changes/archive/2026-06-17-propagate-baseline`.

- **[C2 — the one consolidation finding NOT shipped] (MED).** The audit's §C2 (rules restated 3–5× across the instruction surface: "tasks.md = apply-only", the model-assignment matrix ~5×, "never record counts" ~5×, the mock-encoded-API war-story ~3–4× *within scaffold*, and the web-research convention ×2) was cut from W2 (which did C1+B3 only) and pointed at "W6". But W6 turned out to be pure propagation + the cross-repo **Option-Y war-story relocation** (extrends' downstream copies → `extrends/ai-docs/workflow-lessons.md`) — it did **not** dedup the within-scaffold rule-restatements. So C2 is twice-deferred and never became a change. It is now the single outstanding item from the consolidation plan's findings ledger. Severity is 🟡 (maintainability, not correctness), but it matters more post-W6: the live sync pipe now propagates whatever rule-restatements (and any drift among the 5+ copies) sit in scaffold to all three repos. Promoted to a roadmap entry ("Single-source the restated rules (audit C2)") as the candidate next change ("W7"). Pattern to follow: the same single-source-then-cite approach W2/C1 used for the delegation harness; manifest-changing → would need its own sync pass to the two downstream repos afterward. **→ RESOLVED 2026-06-17: shipped as `single-source-rules` (C2/W7) — all five rule-families single-sourced to canonical homes with cite-don't-restate convention; decision + rejected alternatives in `ai-docs/decisions.md` § single-source-rules. Its Phase-2 downstream propagation is tracked as the active item under `## single-source-rules` above.**
- **psc-monitor `## Purpose` spec-validation failures (LOW, pre-existing, NOT W6).** `openspec validate --strict` in psc-monitor flags `report-quota`, `historical-reports`, and the in-flight `invoice-payment-failed-alert` change for missing `## Purpose` sections. Untouched by the sync (it never writes under `openspec/`) — psc-monitor's own spec hygiene, likely the same H1→`## Purpose` normalization W5 applied to scaffold's specs but not yet to psc's. Fix in psc-monitor when convenient.
- **Downstream commit-test gate ships dormant (LOW).** Both repos got the gate machinery wired but no `scripts/test-cmd` (matching scaffold's template posture), so the gate is a no-op until each repo opts in by dropping in a `test-cmd`. extrends has `.venv` + pytest available; psc-monitor's suite is Postgres-backed (wire only when gate-safe).

## cap-status-log follow-ons (shipped 2026-06-17)

cap-status-log shipped 2026-06-17. Rationale: `ai-docs/decisions.md`; archive: `openspec/changes/archive/2026-06-17-cap-status-log`.

- **extrends one-time cleanup — DONE (2026-06-17).** Per-repo state — done directly in extrends, not via the scaffold; all commits local/unpushed.
  - *STATUS.md cap — DONE (extrends commits `7a2a49e`, `f642541`).* Capped change-paragraph backlog to 3; older paragraphs moved verbatim to `extrends/ai-docs/archive/status-log.md` (newest-first); findability pointers added (`## Pointers` + inline note); byte-integrity + findability verified across two deepseek-pro information-loss review rounds (READY, zero defects). Migration script: `extrends/scripts/_status_cap_oneoff.py`.
  - *Propagate the cap rule to extrends — DONE (extrends commit `8b1733c`).* `sync_scaffold.py` brought cap-status-log's 4 managed files (AGENTS.md span-merge + both archive-executor bodies + the archive skill checklist) up to scaffold HEAD; `--check` then all IDENTICAL; span-merge preserved extrends' title / Project context / tail. deepseek-pro information-loss review: READY, zero defects.
  - *Prune extrends `open-questions.md` — DONE (extrends commit `9a4c2f5`).* Moved only unambiguously-resolved items (explicit ✅ / RESOLVED / DONE / CONFIRMED / "No open items") into `extrends/ai-docs/archive/retired-notes.md` via a byte-integrity-gated one-off (`extrends/scripts/_open_questions_prune_oneoff.py`); every still-open / monitored / deferred / BLOCKING follow-on left in place. Pure line-partition (recombine == source byte-for-byte; moved lines land verbatim; idempotent re-run guard); independently re-verified from git; deepseek-pro information-loss review READY with an adversarial item-by-item no-burying table, zero defects.

- **[RESOLVED 2026-06-17 — `split-open-questions`] `open-questions.md` is not actually bounded by the retired-notes mechanic in a high-activity repo (raised 2026-06-17).** cap-status-log assumed `open-questions.md` could stay "read in full" because resolved items prune to `retired-notes.md`. But extrends' `open-questions.md` remained **over the Read tool's length cap even after** the conservative resolved-items prune above — the file is dominated by *genuinely-open* follow-ons, so the prune mechanic alone cannot bound it. RESOLVED by the horizon-split rule: `open-questions.md` now holds ONLY active items; the deferred/monitored long tail lives in `ai-docs/parked-follow-ons.md`. Full decision in `ai-docs/decisions.md` ("split-open-questions (2026-06-17)"). The always-loaded surface is now bounded to simultaneously-live blockers, which is self-limiting. The legacy file here in scaffold will be migrated in a follow-up one-time cleanup (see `ai-docs/parked-follow-ons.md` § migration).

## split-open-questions (shipped 2026-06-17)

split-open-questions shipped 2026-06-17. Rationale: `ai-docs/decisions.md`; archive: `openspec/changes/archive/2026-06-17-split-open-questions`.

- **Propagation to extrends + psc-monitor — DONE (2026-06-17).** `sync_scaffold.py` carried this change's four managed files (AGENTS.md span-merge + both archive-executor bodies + the archive skill checklist) downstream; `--check` then all IDENTICAL on both repos; the AGENTS.md span-merge preserved each repo's title / `## Project context` / tail (per-repo diff reviewed via subagent). extrends commit `14f95d2`; psc-monitor commit `5139511` (psc-monitor's prior sync predated cap-status-log too, so that catch-up rode along on the same four files). All commits local/unpushed.
- **extrends `open-questions.md` one-time horizon split — DONE (extrends commit `4e46eb9`).** The real over-cap case: split the legacy file into active (`open-questions.md`) + parked (`ai-docs/parked-follow-ons.md`) via a byte-integrity-gated, section-level pure line-partition (`extrends/scripts/_open_questions_split_oneoff.py`; recombine == source byte-for-byte; idempotent guard). Active-vs-parked classification authored by hand (not delegated); the active file now reads in full under the Read cap. Independently re-verified from git HEAD; deepseek-v4-pro information-loss review READY (all parked blocker-keyword hits adjudicated — no live blocker parked; all live blockers retained), zero defects.

## single-source-rules (shipped 2026-06-17)

Decision and rationale: `ai-docs/decisions.md`; archive: `openspec/changes/archive/2026-06-17-single-source-rules`. All follow-ons resolved — Phase 2 propagation completed 2026-06-18; resolution record in `ai-docs/archive/retired-notes.md`.

## lean-boot-context (shipped 2026-06-18)

Decision and rationale: `ai-docs/decisions.md`; archive: `openspec/changes/archive/2026-06-18-lean-boot-context`.

- **Enforcement untested against a live archive — monitor.** The 3 state-bounding rules are forward-only — they bind at each repo's *next* archive, not retroactively. Watch the next real archive (any repo) to confirm the archive-executor applies the ≤150-word STATUS budget, the open-questions parking+pointer-stub, and the decisions Date/Status+≤300-word cap.
- state-bounding / sync-mechanism / psc-monitor: tune-after-evidence items → parked-follow-ons.md § state-bounding, § sync-mechanism, § psc-monitor

## add-status-lint (shipped 2026-06-18)

Decision and rationale: `ai-docs/decisions.md`; archive: `openspec/changes/archive/2026-06-18-add-status-lint`.

- **Phase B — linter-driven one-time STATUS/decisions cleanup (active).** Once the linter ships, the
  primary (with archive-executor on pro tier where summarization is needed) uses it to drive the
  cleanup the external review called for: extrends — trim the 3 retained STATUS entries (324/280/289)
  to ≤150-word headlines (surplus → `status-log.md` verbatim), trim the over-budget
  `## Immediate next action`, relocate `ai-docs/improvement-roadmap.md` → `plans/` and update
  cross-refs; scaffold — trim its over-budget `split-open-questions` STATUS entry; psc-monitor — run
  the linter and trim any flagged entries. Each is reconciliation/summarization (judgment), gated by
  `status_lint.py` going green — not mechanical flash work, which is why it is split out of this
  tool-shipping change.
