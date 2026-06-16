## Why

The first-load instruction surface (AGENTS.md + `ai-docs/` + the workflow skills) has drifted out of sync with shipped behavior, and one instruction actively licenses unsafe autonomy. A 2026-06-16 audit found: (1) the `## Change tiers` guidance tells every agent to "classify every change yourself and **state the tier**" (AGENTS.md:114) with no operator checkpoint — an agent recently self-classified a change and began applying edits without ever showing a plan; (2) three 2026-06-16 changes (the commit-test-gate hook, the apply-convergence-guard failure ladder, and the `scripts/test-cmd` single-source) updated the skills and `decisions.md` but were never propagated to older instruction surfaces, leaving stale text an autonomous agent would act on wrongly. These are correctness/safety defects in the instructions themselves, independent of the separate plan to single-source files across repos.

## What Changes

- **NEW guardrail — tier confirmation.** An agent WITHOUT an explicit fast-track/autonomy grant MUST NOT self-assign a change tier and begin executing. It must state its proposed tier and plan and obtain operator confirmation first. Fast-track-granted agents keep self-direction per `ai-docs/fast-track-workflow.md`. Rewrite AGENTS.md `## Change tiers` (currently "classify every change yourself and state the tier") accordingly.
- **Fix H2 — autonomy reverts the hardened ladder.** `ai-docs/fast-track-workflow.md:38` compresses recovery to "non-crash failure → Sonnet immediately," reverting the declared-blocker vs opaque-give-up routing in `openspec-apply-change/SKILL.md:187-197`. Because fast-track is the autonomous mode, this would reflexively Sonnet-fix a declared `### NON-CONVERGENCE BLOCKER`. Align the fast-track ladder to — or reference — the apply skill's canonical ladder.
- **Fix H1 — stale "hook-free" claim.** `AGENTS.md:42-43` calls `.claude/settings.json` a "hook-free permissions file," but it ships only the commit-test-gate `PreToolUse` hook and no permissions. Correct the cross-agent-compatibility text to acknowledge the shipped hook as the sanctioned carve-out already recorded in `ai-docs/decisions.md`.
- **Fix M3 — test command not single-sourced.** `openspec-verify-change/SKILL.md:18` and `openspec/config.yaml:36` hard-code `.venv/bin/python -m pytest -q`, while the apply-executor was migrated to read `scripts/test-cmd` and told never to improvise pytest. Make `scripts/test-cmd` the source for the orchestrator's verify test run too (pytest as illustrative example only).
- **Editorial reconciliations** (no requirement change):
  - `openspec-onboard/SKILL.md` teaches a `tasks.md` template with a `## 2. Verify` checkbox (forbidden by `openspec/config.yaml` and four other places) and teaches inline implementation plus a bare `openspec archive` CLI call, contradicting the delegated role split. Fix the template and add a one-line "real changes delegate apply/archive" note (M1/M2).
  - `ai-docs/research-fetch-convention.md` is missing rule (d) — the WebSearch-from-main-thread ban present in AGENTS.md:214-217 — and cites a non-existent `output/fetch-measure.md`. Add rule (d); drop or soften the dead reference (M4/L2).
  - Reconcile the "one-line" vs "~2-line" hand-fix threshold stated differently across AGENTS.md:124, verify SKILL:25, and `openspec/config.yaml` (L1).

## Capabilities

### New Capabilities
- `tier-confirmation-gate`: a non-fast-track agent must confirm the change tier (and plan) with the operator before executing, instead of self-classifying and proceeding.

### Modified Capabilities
- `apply-convergence-guard`: the declared-blocker vs opaque-give-up recovery routing applies in ALL autonomy modes; the fast-track failure-ladder text must not revert it.
- `commit-test-gate`: the single per-repo test command (`scripts/test-cmd`) is the source for every orchestrator test invocation (the gate AND the verify re-run AND config examples), and the cross-agent-compatibility guidance acknowledges the shipped gate hook (no "hook-free" claim).

## Out of Scope

- Does **not** create `.claude/settings.json` — it already exists and is git-tracked in the scaffold (the commit-test-gate `PreToolUse` hook is present); H1 only corrects stale text *about* it.
- Does **not** add a `scripts/test-cmd` to the scaffold (the gate stays inert here) and does **not** modify `scripts/test-gate.sh`.
- Does **not** introduce the cross-repo single-source / sync mechanism (that is the separate "change 2"); edits land in `openspec-scaffold` only.
- Does **not** change any executor/reviewer model assignments, timeouts, or the OpenSpec lifecycle phase gates themselves.

## Impact

- **Docs/instructions edited:** `AGENTS.md` (`## Change tiers`, cross-agent-compatibility, web-research convention, one-line threshold), `ai-docs/fast-track-workflow.md`, `ai-docs/research-fetch-convention.md`, `.claude/skills/openspec-verify-change/SKILL.md`, `.claude/skills/openspec-onboard/SKILL.md`, `openspec/config.yaml`.
- **Specs:** new `tier-confirmation-gate`; delta specs for `apply-convergence-guard` and `commit-test-gate`.
- **No runtime/code behavior change** beyond instruction text and `scripts/test-cmd` sourcing; no new dependencies.
- **Propagation:** edits land in `openspec-scaffold` only; `extrends`/`psc-monitor` inherit them via the separate single-source change. No `scripts/test-cmd` is added to the scaffold (the gate stays inert here).
- **Cross-agent:** all edits are to tracked, agent-neutral files; no harness-private state introduced.
