## 1. AGENTS.md

- [x] 1.1 (D1 / H1) In the "Cross-agent compatibility" section, replace the parenthetical `(A tracked, hook-free `.claude/settings.json` permissions file is also fine.)` (line ~42-43) with text that acknowledges the shipped commit-test-gate `PreToolUse` hook as a sanctioned, Claude-only carve-out running a tracked, agent-neutral script, cross-referencing the `ai-docs/decisions.md` commit-test-gate hook carve-out decision. Do NOT use conditional "may ship" wording (the file exists and is git-tracked) and do NOT create or modify `.claude/settings.json` itself. Must satisfy `commit-test-gate` spec ("Instruction docs acknowledge the shipped gate hook").
- [x] 1.2 (D2 / tier gate) Rewrite the `## Change tiers` lead-in (lines ~114-115: "classify every change yourself and **state the tier** (the operator initiates tier-2/tier-3 lifecycles)") so it states: an agent WITHOUT an explicit fast-track/autonomy grant proposes its tier together with a plan and obtains operator confirmation BEFORE beginning execution (delegating apply / editing implementation code / mutating project state) — producing the plan is NOT gated; with a grant, self-classify and proceed per `ai-docs/fast-track-workflow.md`; if the operator is unavailable, do NOT execute — report the proposed tier/plan and wait. The replacement lead-in MUST still end with a `:` so it introduces the SMALL / MEDIUM / COMPLEX bullet list that follows. Keep the SMALL / MEDIUM / COMPLEX bullets AND the paragraph beneath them (lines ~124-126: the one-line exception, the push-authorization rule, and the failure-ladder-location pointer) intact. Must match the `tier-confirmation-gate` spec.

## 2. ai-docs/fast-track-workflow.md

- [x] 2.1 (D3 / H2) Replace the ENTIRE "Failure ladder: operational crash → retry once → Sonnet subagent; non-crash failure → Sonnet immediately. Always disclose any fallback taken." sentence (line 38) with a pointer that references — does NOT restate — the apply skill's canonical ladder in `.claude/skills/openspec-apply-change/SKILL.md`: operational crash → retry once → Sonnet; non-crash → a declared blocker (`### NON-CONVERGENCE BLOCKER`) routes to orchestrator triage (NOT reflexive Sonnet), an opaque give-up → Sonnet; always disclose any fallback. After the edit the file must contain no "non-crash failure → Sonnet immediately" text. Must match the `apply-convergence-guard` modified spec scenario "Recovery routing holds under fast-track / autonomy".

## 3. .claude/skills/openspec-verify-change/SKILL.md

- [x] 3.1 (D4 / M3) In the MANDATORY block, item 2 (line 18: "Re-run the FULL test suite yourself: `.venv/bin/python -m pytest -q`."), change the full-suite re-run to source its command from `scripts/test-cmd`: prefer `scripts/test-cmd`, falling back to the project's documented test command when absent — never an improvised command; keep `.venv/bin/python -m pytest -q` only as an illustrative example. Leave the line-24 opt-in live-smoke example unchanged. Must match `commit-test-gate` spec ("The orchestrator's verify re-run uses the single per-repo test command").
- [x] 3.2 (D5 / L1) In item 5 (line 25: "if you would write more than ~2 lines of implementation, stop and re-delegate"), reconcile to the single standing threshold — a single disclosed one-line change; anything larger, stop and re-delegate. No "~2 lines" may remain.

## 4. openspec/config.yaml

- [x] 4.1 (D4 / M3) In the `verify` rule, change the full-suite re-run "(.venv/bin/python -m pytest -q)" (line ~36) to source from `scripts/test-cmd` with the documented fallback; present pytest only as an example. Keep wording consistent with the verify SKILL edit (3.1).
- [x] 4.2 (D5 / L1) In the `verify` rule, reconcile the hand-fix threshold "never hand-fix beyond a trivial typo/one-line change; more than ~2 lines of implementation => re-delegate" (line ~41-42) to the single one-line wording; remove "~2 lines".

## 5. .claude/skills/openspec-onboard/SKILL.md

- [x] 5.1 (D6a / M1) In the `tasks.md` template the onboard skill shows (lines ~366-376), remove the `## 2. Verify` / `- [x] 2.1 [Verification step]` block — verify is NOT a `tasks.md` item (per `openspec/config.yaml`). Keep the `## 1. [Category or file]` implementation work items. If useful, mention verify as a separate phase in the EXPLAIN paragraph ABOVE the template (not after it), never as a checkbox.
- [x] 5.2 (D6b / M2) Append a one-line note (AFTER the existing "DO:" narration block at each site) at the implement step (~395-403) and the archive step (~431-434) stating that real changes delegate apply to the apply-executor and archive via the archive skill — the inline implementation and bare `openspec archive` shown here are teaching simplifications. Do not otherwise rewrite the tutorial.

## 6. ai-docs/research-fetch-convention.md

- [x] 6.1 (D7 / M4) Add rule **(d)** matching AGENTS.md:214-217 — never call the built-in `WebSearch` tool from the main thread; route ALL web research through subagents that use `scripts/fetch_clean.py` (discover via a fetched search URL, then fetch the chosen pages). Add it after rule (c), and update the "## Three rules for efficient web research" heading to reflect four rules.
- [x] 6.2 (D7 / L2) Reword the measurement line (lines 5-6) to drop the dead `output/fetch-measure.md` path; present the token reduction as illustrative ("measured to cut tokens substantially on article pages and GitHub HTML vs. raw") rather than citing a non-existent artifact with exact figures.
