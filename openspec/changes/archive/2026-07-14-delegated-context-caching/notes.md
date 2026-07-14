# notes — delegated-context-caching (OW-8)

## Acceptance criteria (SMALL)
- The 4 delegated prompt strings (apply, archive, propose-reviewer base, AGENTS.md SMALL-premise)
  place all per-change variables at the tail; the fixed instruction body precedes any `<…>` variable.
- No wrapper-asserted marker is dropped: `### Premise Verdict` + `PREMISE: AGREE|DISSENT` still present
  in the propose proposal.md-append and the AGENTS.md SMALL-premise prompt.
- Semantics preserved: each reshaped prompt instructs the executor to do exactly what it did before.
- `delegation-harness.md` carries the variable-last convention; AGENTS.md's stability preamble carries
  the batch-edits note.
- `bash scripts/check.sh` green.

## ⭐ B-BLOCKED finding (durable — full evidence; archive → decisions entry + Parked follow-on)
**Claim:** In opencode **v1.17.18**, `OPENCODE_DISABLE_PROJECT_CONFIG=1` cannot be used to strip the
AGENTS.md system-prompt injection from delegated executor calls, because it also disables
`.opencode/agents/` discovery — the two are coupled in one env-var gate.

**Why it was attractive (AUDIT finding 2 / caching-analysis §6.4):** AGENTS.md (~7.2k tokens,
orchestrator-voice, highest-churn boot file) is auto-injected into every `opencode run` executor.
Stripping it for sub-executors was "the largest single number in the analysis" — it would remove
~7.2k tokens/call AND remove AGENTS.md churn as a cache-invalidation source for all delegated calls.

**Evidence (this session, reproducible, zero model cost):**
1. Binary (`strings /home/pang/.opencode/bin/opencode`, v1.17.18): three code sites gate the project
   AGENTS.md/CLAUDE.md/CONTEXT.md walk-up on `!OPENCODE_DISABLE_PROJECT_CONFIG` — when set, instruction
   globbing falls back to the global config dir only (project AGENTS.md NOT injected). Confirms it
   *would* strip AGENTS.md. Same var also gates project `tui`/plugin/config loading.
2. Empirical:
   - `opencode agent list` → lists our project agents: `apply-executor (all)`, `archive-executor (all)`,
     `openspec-reviewer (all)`, `openspec-verifier (all)`, `explore-flash (subagent)`.
   - `OPENCODE_DISABLE_PROJECT_CONFIG=1 opencode agent list` → **0** of our project agents; only
     built-ins (`build`, `plan`, `general`, `explore`, `summary`, `title`, `compaction`).
   ⇒ With the var set, `opencode run --agent apply-executor` cannot find the agent → **silent fallback
   to a built-in default** (right `--model`, WRONG role prompt). Catastrophic silent role-swap.
3. No per-agent frontmatter opt-out for instruction injection exists (grep of binary + agent
   frontmatter). `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT` affects CLAUDE.md only, not AGENTS.md.
   `--pure` / `OPENCODE_PURE` is plugins-only.

**Disposition:** B deferred. Revisit only if (a) opencode adds a targeted per-agent instruction-scoping
mechanism (frontmatter field / flag that disables project-instruction injection WITHOUT disabling agent
discovery), or (b) AGENTS.md is deliberately split so its injected footprint shrinks (separate, larger
work with downstream blast radius). Until then, the only lever on AGENTS.md-injection cache cost is the
**batch-edits convention** (shipped as D2). Re-test on any opencode major-version bump.

## C-DROPPED rationale (durable)
"Single-source the triplicated premise prompt" (AUDIT finding 2 sub-item) inspected and dropped: the
premise prompt is not fatly triplicated. Byte-identical shared substring across the 3 call sites =
only `### Premise Verdict block (PREMISE: AGREE|DISSENT)` (~7 words). Verdict FORMAT already
single-sourced in `.opencode/agents/openspec-reviewer.md` (the producer) + `premise-review-gate` spec;
invocation skeleton already single-sourced in `delegation-harness.md`. A `_shared/` extraction for ~7
words is net-negative indirection. Possible future follow-on: a `model-id-agreement`-style lint that
asserts every premise call-site uses the sanctioned marker spellings (drift-prevention as a check, not
a refactor).

## Assumptions (non-blocking; recorded per AGENTS.md batching rule)
- A1: apply/archive reshapes bind the paths at the tail; the executor treats `tasks.md`/`design.md`/etc.
  as relative to the trailing `<changeRoot>`. deepseek executors already operate inside the change dir;
  the trailing binding is explicit ("… are all in the change directory: <changeRoot>"). No behavior
  change intended.
- A2: propose reshape keeps the conditional appends (premise, drift) as suffixes after the reshaped
  base — unchanged — since cross-round caching already diverges at `<artifact>` before the appends.
- A3: naming the change `delegated-context-caching` (matches OW-8 "Delegated-context caching hygiene").

## Verify result (SMALL)
- Orchestrator deep review: all 4 reshapes semantically equivalent; no directive dropped; markers intact.
- Deterministic checks: `### Premise Verdict`/`PREMISE: AGREE|DISSENT` present in A4 + propose append;
  `brief completion report` present in apply/archive; first per-change `<var>` at the tail of each.
- `bash scripts/check.sh` green (ruff clean, scaffold_lint incl. model-id-agreement + executor-body
  agreement, status_lint C3, boot_surface_lint 73.9KB < 80KB WARN; full pytest suite passed).
- Independent `deepseek/deepseek-v4-flash` verifier pass: **VERDICT: READY, Defects: None** — it
  produced a full side-by-side semantic-equivalence table, verified marker preservation with line
  refs, variable-at-tail, and §(g)/AGENTS.md-note accuracy, and re-ran the suite green. Not a rubber
  stamp. Zero Sonnet fallback on both delegated passes (premise + verify).

## Archive reconciliation material (for the Sonnet archive-executor)
- STATUS: new "Latest change" section (respect ≤3 cap + C3 word budgets); demote/drop oldest.
- decisions/INDEX.md registry line (decisions-entry-format):
  `- **2026-07-14** · delegated-context-caching · var-paths-last delegated-prompt reshape + batch-AGENTS.md
    convention; OPENCODE_DISABLE_PROJECT_CONFIG proven to couple AGENTS.md-injection with agent-discovery
    (B deferred) → \`openspec/changes/archive/2026-07-14-delegated-context-caching/\``
- questions/INDEX.md Parked: add
  `delegated-context-caching follow-ons (OW-8): B — AGENTS.md-injection strip blocked on opencode env-var
   coupling, revisit on per-agent instruction-scoping / AGENTS.md split; C-drop lint idea →
   knowledge/questions/delegated-context-caching-follow-ons.md`
- OUTSTANDING-WORK.md: mark OW-8 SHIPPED (A+D; B deferred-blocked, C dropped).
