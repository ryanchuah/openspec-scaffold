# Review Log — harden-instruction-surface

## proposal.md

### Round 1 — 2026-06-16 — deepseek/deepseek-v4-pro (openspec-reviewer) — **PASS** (zero 🔴)

Reviewer verified every audit claim against source and confirmed scope is well-bounded; no
blocking issues. Full verdict captured below, followed by orchestrator dispositions.

> **Summary:** "Every claim I verified against the source files checks out — the stale text, the
> hard-coded pytest command, the onboard skill's forbidden template, the fast-track ladder collapse,
> the missing rule (d), and the dead `output/fetch-measure.md` reference are all confirmed. … No
> conflicts with existing specs."
>
> **🔴 Blocking Issues: None.**
>
> **🟡 Should Fix:**
> 1. H1 — claims `.claude/settings.json` does not exist on disk (`glob("**/.claude/settings*")` → 0);
>    design should create the file or use conditional language.
> 2. M3 — `scripts/test-cmd` sourcing needs an explicit fallback for when the file is absent (match the
>    apply-executor's "prefer test-cmd, fall back to documented command, never improvise" pattern).
> 3. L1 — reconciliation leaves the target threshold ("one-line" vs "~2-line") unspecified; pick one.
> 4. No `## Out of Scope` section — optional but recommended for a six-file change.
>
> **💡 Suggestions:** (1) tier-confirmation-gate should state operator-unavailable behavior; (2) the
> onboard M1/M2 fixes are behavioral (safety), not merely editorial; (3) spelling "guardrail" vs
> "guardrails".
>
> **Verdict: PASS — ready to freeze and move to design.md.**

#### Orchestrator dispositions

- **🟡 #1 — REJECTED (false premise).** `.claude/settings.json` **does exist** and is **git-tracked**
  (`git ls-files --error-unmatch` succeeds; not gitignored; 311 bytes; contains the `PreToolUse` hook).
  The reviewer's `glob("**/.claude/settings*")` returned zero due to glob semantics not matching a
  top-level dotfile directory, not because the file is absent. The H1 fix therefore needs **no**
  conditional hedging and **no** file creation — it simply corrects the stale "hook-free" wording to
  acknowledge the present, tracked hook. Recorded in `## Out of Scope`. (Per the verification
  discipline: separate-model reviewers are confidently wrong on falsifiable specifics — verified
  directly before acting.)
- **🟡 #2 — ACCEPTED → design.** The verify SKILL / config.yaml edits will use the
  apply-executor's canonical phrasing: prefer `scripts/test-cmd`, fall back to the project's
  documented test command when absent, never improvise.
- **🟡 #3 — ACCEPTED → design.** Reconcile to a single standing threshold: **a single disclosed
  one-line change** (strictest, matches AGENTS.md and fast-track's "single trivial one-liner");
  the "~2 lines" phrasings in verify SKILL / config.yaml are brought to that wording.
- **🟡 #4 — ACCEPTED.** Added `## Out of Scope` to proposal.md (also clears the #1 confusion).
- **💡 #1 — ACCEPTED → design/spec.** tier-confirmation-gate will specify operator-unavailable
  behavior (default: treat as not-confirmed → do not execute; the agent reports the proposed
  tier/plan and waits, rather than proceeding).
- **💡 #2 — NOTED.** Onboard M1/M2 retain the "editorial/teaching-surface" label (there is no
  onboard capability spec to modify) but the task wording will make the safety dimension explicit
  (the template currently teaches a forbidden pattern + inline implementation).
- **💡 #3 — minor; the proposal's singular "guardrail" is grammatically correct for one rule. Left as-is.**

**Outcome: proposal.md frozen.** Post-PASS edits were the additive `## Out of Scope` section only
(reviewer-recommended, non-blocking) — no re-review required.

## specs/ (3 delta files)

### Round 1 — 2026-06-16 — deepseek/deepseek-v4-pro (openspec-reviewer) — **PASS** (zero 🔴)

Reviewer confirmed delta notation, RFC-2119 SHALL usage, every requirement has ≥1 scenario, the
MODIFIED `apply-convergence-guard` block preserves existing content verbatim + appends the fast-track
clause/scenario, and the deltas fully deliver the proposal's Capabilities contract.

> **🔴 Blocking Issues: None.**
>
> **🟡 Should Fix #1 — tier-confirmation-gate body vs. scenario mismatch.** Requirement body bans "any
> execution action — … or running the OpenSpec lifecycle," which could be read as blocking even the
> propose phase, while the scenario only bans apply/code/archive. Ambiguous about where the gate sits.
> Fix: remove "running the OpenSpec lifecycle" (gate sits between planning and execution).
>
> **💡 #1** commit-test-gate R2: add a second scenario for when the section omits settings.json entirely.
> **💡 #2** normalize scenario title casing.
>
> **Verdict: PASS — ready to freeze.**

#### Orchestrator dispositions

- **🟡 #1 — ACCEPTED.** Reworded the tier-confirmation-gate requirement body: removed "running the
  OpenSpec lifecycle"; the gate now explicitly sits "between planning and execution" — producing the
  plan/proposal is how the agent surfaces the choice and is NOT gated; only apply/code-edit/state-mutation
  is. Re-validated `--strict`: valid.
- **💡 #1 — ACCEPTED.** Added the "Guidance omits settings.json entirely" scenario to commit-test-gate R2.
- **💡 #2 — declined (titles already consistent sentence case; no functional impact).**

**Outcome: specs/ frozen.** Post-PASS edits addressed the non-blocking 🟡 + one 💡; no re-review required.

## design.md

### Round 1 — 2026-06-16 — deepseek/deepseek-v4-pro (openspec-reviewer) — **PASS** (zero 🔴)

Reviewer confirmed all seven fixes map to a decision (D1-D7), every decision aligns with the frozen
specs, no contradictions, Goals/Non-Goals correctly fence out change-2, and the false settings.json
premise is correctly rejected. Four precision 🟡 (no 🔴).

> **🟡 Should Fix:** (1) M3 verification criterion is semantic, not grep-checkable → decompose into two
> greps. (2) "seven files" should be "six" (Impact lists 6). (3) D3 ambiguous whether the whole "Failure
> ladder" sentence or only the non-crash clause is replaced → replace the whole sentence (option b).
> (4) L1 grep covers only 2 of 3 sites → enumerate AGENTS.md too.
> **💡:** (1) cite the specific decisions.md entry in D1; (2) specify placement of the D6b note;
> (3) drop the template-carryover live-probe phrasing.
> **Verdict: PASS — ready to freeze and move to tasks.md.**

#### Orchestrator dispositions

- **🟡 #1-#4 — ALL ACCEPTED.** M3 verification split into two concrete greps (`scripts/test-cmd` present
  + hard-coded pytest absent from the re-run text); "seven" → "six"; D3 clarified to replace the entire
  "Failure ladder" sentence with a reference to the apply skill's full ladder; L1 grep broadened to all
  three sites (AGENTS.md + verify SKILL + config.yaml).
- **💡 #1-#3 — ALL ACCEPTED.** D1 now cites "the commit-test-gate hook carve-out decision"; D6b specifies
  the note is appended after the existing "DO:" narration block; the live-probe phrasing trimmed to a
  plain "no external-API surface" statement.

**Outcome: design.md frozen.** Post-PASS edits were precision-only (4 🟡 + 3 💡); no re-review required.

## tasks.md

### Round 1 — 2026-06-16 — deepseek/deepseek-v4-pro (openspec-reviewer) — **PASS** (zero 🔴)

Reviewer confirmed 11 tasks across 6 file groups are all apply-phase text edits (no verify/archive
checkboxes — the change practices its own new rule), each traces to a design decision + spec delta,
all seven fixes covered, checkbox format correct, no spec contradiction.

> **🟡 Should Fix:** (1) task 1.2 — the lead-in's trailing `:` is structural (introduces the
> SMALL/MEDIUM/COMPLEX bullets); the rewrite must also end with `:`. (2) task 5.1 — "surrounding prose"
> is ambiguous; specify the EXPLAIN paragraph above the template.
> **💡:** (1) effort estimates; (2) 5.1 line range slightly broad; (3) 1.2 "keep" scope should name
> lines 124-126 (three sentences).
> **Verdict: PASS — ready to freeze.**

#### Orchestrator dispositions

- **🟡 #1 & #2 — ACCEPTED.** Task 1.2 now instructs the replacement lead-in to end with `:`; task 5.1
  now specifies the EXPLAIN paragraph above the template.
- **💡 #3 — ACCEPTED** (1.2 keep-scope now names lines 124-126: one-line exception + push-auth +
  ladder pointer). **💡 #1 declined** (each edit is <1h; estimates add noise). **💡 #2 noted** (the
  ~366-376 range is intentionally generous context for the executor; safe).

**Outcome: tasks.md frozen. All four artifacts reviewed + frozen — change is apply-ready.**
