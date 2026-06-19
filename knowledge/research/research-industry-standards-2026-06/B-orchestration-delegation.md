# B — Multi-agent orchestration, delegation & model routing

> Research date: 2026-06-13. Author: Claude Code (claude-sonnet-4-6).
> Companion to _BRIEF.md; do NOT edit any scaffold file.

---

## 1. Scope

This bucket covers: orchestrator–worker patterns; subagent/agent definitions; task hand-off; model routing (strong planner + cheap executors); parallelism; context isolation between agents; completion detection / liveness (EXIT-file sentinel approach); retry & fold-fix briefs; how leading harnesses structure delegation.

**Out of scope (sibling areas):** spec lifecycle content (A); AGENTS.md/MCP/skills as config mechanisms (C); memory & verification-quality criteria (D). The `openspec-reviewer` agent's review-quality criteria belong to D; its orchestration/handoff role is covered here.

---

## 2. Sources consulted

| URL | What it is | Date/recency |
|-----|-----------|--------------|
| https://www.anthropic.com/research/building-effective-agents | Anthropic canonical "Building effective agents" — orchestrator-workers, prompt chaining, evaluator-optimizer patterns | Dec 2024 (still canonical in mid-2026) |
| https://www.anthropic.com/engineering/multi-agent-research-system | Anthropic engineering writeup on their live Research multi-agent system | 2025, updated |
| https://openai.github.io/openai-agents-python/multi_agent/ | OpenAI Agents SDK — orchestration and LLM/code-driven patterns, agents-as-tools vs. handoffs | 2025–2026 |
| https://openai.github.io/openai-agents-python/handoffs/ | OpenAI Agents SDK — handoff API, input filters, context passing | 2025–2026 |
| https://www.philschmid.de/subagent-patterns-2026 | "How Agents Manage Other Agents: Four Subagents Patterns in 2026" — inline tool, fan-out, agent pool, teams | 2026 |
| https://akitaonrails.com/en/2026/04/25/llm-benchmarks-vale-a-pena-misturar-2-modelos/ | Benchmark: "Is it worth mixing 2 models?" — 3-round empirical comparison of planner+executor vs. solo frontier model | April 2026 |
| https://www.datadoghq.com/blog/ai/harness-first-agents/ | Datadog "harness-first engineering" — verification pyramid, DST, multi-agent harness design | Late 2025/2026 |
| https://opencode.ai/docs/cli/ | OpenCode CLI docs — `opencode run`, headless mode, agent flag | 2025 |
| https://medium.com/@vishal.agarwal.iitk/agent-architectures-planner-executor-router-patterns-148fe54ff595 | Planner/Executor/Router architecture patterns | March 2026 |
| https://gurusup.com/blog/best-multi-agent-frameworks-2026 | Framework comparison: LangGraph, CrewAI, OpenAI Agents SDK in 2026 | 2026 |
| https://opencode.ai/docs/cli/ | OpenCode CLI docs — `opencode run`, `--agent`, `--model`, `--format` flags confirmed | 2025–2026 |
| https://github.com/anomalyco/opencode/issues/24124 | OpenCode bug report: DeepSeek V4 fails with `reasoning_content must be passed back` error in multi-turn conversations | April 2026 |
| https://shipyard.build/blog/claude-code-multi-agent/ | Shipyard: multi-agent orchestration patterns for Claude Code 2026 — Agent Teams, Gas Town, Multiclaude | 2026 |
| LangGraph multi-agent concepts page | Attempted fetch; returned empty. | inaccessible |

**Inaccessible sources:**
- `https://langchain-ai.github.io/langgraph/concepts/multi_agent/` — fetch returned empty/no content. Covered via secondary references in other sources.
- `https://docs.anthropic.com/en/docs/claude-code/sub-agents` — not fetched directly; covered via search results and Claude Code blog coverage.
- `https://arxiv.org/pdf/2603.05344` — returned binary/garbled PDF content; not extractable.

---

## 3. Industry standard (mid-2026)

### 3a. Dominant orchestration patterns

The most-cited and most-deployed orchestration architecture remains the **orchestrator-worker (planner-executor)** pattern first codified by Anthropic in their "Building effective agents" piece. By mid-2026 it has three mainstream variants:

1. **Inline tool / sync spawn:** Orchestrator calls a `call_agent` or `Task` tool; the worker runs synchronously in its own context window and returns a result. This is Pattern 1 in Schmid (2026) and matches OpenAI's "agents as tools" pattern. Works with any model that supports tool use. Used by the OpenAI Agents SDK's `Agent.as_tool()` idiom.

2. **Fan-out / async spawn-wait:** Orchestrator spawns multiple workers immediately, continues its own work, then collects via `wait_agent`. Workers run in parallel. This is Pattern 2 in Schmid (2026) and corresponds to OpenAI's parallelization pattern. Anthropic's Research feature uses it (lead Opus 4 + parallel Sonnet 4 subagents, beating single-agent by 90.2% on their internal eval).

3. **Handoff (ownership transfer):** Used in OpenAI Agents SDK — a triage agent transfers execution ownership to a specialist. The specialist "becomes the active agent." Distinct from inline tool because the specialist now owns the user-facing conversation. Used in customer-service routing scenarios; less relevant for batch coding pipelines.

The Anthropic Research system runs a **synchronous lead–subagent pattern** in production (Anthropic 2025): "Currently, our lead agents execute subagents synchronously, waiting for each set of subagents to complete before proceeding." They note this simplifies coordination but creates bottlenecks. Async is on the roadmap.

### 3b. Subagent context isolation

The canonical 2026 practice is **per-worker context isolation**: each worker/subagent gets its own clean context window, seeded with a tightly scoped brief (objectives, output format, tool guidance, task boundaries). Anthropic (2025): "each subagent provides separation of concerns — distinct tools, prompts, and exploration trajectories — which reduces path dependency and enables thorough, independent investigations." Subagents write results to a **shared filesystem** (or artifact store), with lightweight references passed back to the coordinator.

The Anthropic Research guidance is explicit: "Subagent output to a filesystem to minimize the 'game of telephone.'" Rather than funnelling all subagent text through the coordinator's context, subagents store outputs externally (files, databases), and the coordinator receives references. This directly matches the scaffold's pattern of having executors write to the working tree, with the orchestrator reading back via `git diff`.

### 3c. Model routing (strong planner + cheap executor)

This is the most empirically contested area in mid-2026. The canonical narrative is: "use a strong frontier model to plan, route to a cheap model for execution." The reality is more nuanced:

**Where it works:** Tasks that are genuinely parallelizable and have little internal dependency (e.g., apply the same refactor to 50 independent files, generate 100 UI components from a shared pattern). In these cases, the planner's cost is amortized across many parallel executions. Akitaonrails benchmark (April 2026) Round 3 shows Opus 4.7 + Kimi K2.6 tying solo Opus 4.7 at 97/100 while costing less per executor-token.

**Where it fails:** Tasks with high internal dependency (cohesive greenfield coding, integrated system build). Akitaonrails (2026): "mixing 'strong frontier planner + cheap executor' loses to just using Opus 4.7 alone in a mature harness." The benchmark found frontier models **do not delegate** when they judge a task cohesive — 7/7 variants in Round 1 had zero delegations, the agents doing 100% of the work themselves. When delegation was *forced*, all variants produced lower quality than solo frontier (90–95 vs 97/100) and consumed more elapsed time.

**Critical discovery — harness overhead costs dominate:** In the manual cross-process orchestration (Akitaonrails Round 3), ~14 dispatches across two runs generated ~$11 in hidden orchestrator token cost (Opus turns spent reading output, writing briefs, monitoring), versus $4 for solo Opus solo. "Manual orchestration costs 3× more than solo." The cheap executor only saves money when the planner cost is pre-paid or amortized.

**The operational implication:** The cost of the cheaper executor is only real savings if the orchestrator overhead (brief-writing, output-reading, retry coordination) is minimal. When that overhead is minimized (tight briefs, structured output, clear task scoping), the model yields real savings; when it is not, the overhead erases gains.

**Current recommendation in the literature:** Use the frontier model solo unless: (a) tasks are genuinely independent and parallelizable, or (b) you have a pay-as-you-go stack where executor savings are real. For subscription plans (monthly token quota), the marginal cost of additional frontier model tokens is effectively zero, making cost-motivated delegation counterproductive.

### 3d. Completion detection

No dominant 2026 standard specifically prescribes EXIT-file sentinel polling. The mainstream approaches are:

1. **Inline synchronous return:** Tool call blocks until the worker completes; result arrives as the tool response. This is the most common pattern. No sentinel needed — the harness manages the call/return natively.

2. **ID + notification injection:** In async fan-out (Pattern 2/Schmid), `spawn_agent` returns an ID immediately; the result is injected as a notification message when the worker finishes. The orchestrator calls `wait_agent` to collect. No sentinel file; framework-managed.

3. **End-state evaluation:** Anthropic Engineering (2025) recommends evaluating agent completion by checking the *end state* of modified artifacts (files, task lists), not by monitoring process liveness. "Focus on end-state evaluation rather than turn-by-turn analysis... evaluate whether it achieved the correct final state."

4. **Explicit completion tool:** The worker calls a `complete(status, summary)` tool to signal completion, rather than relying on process termination. This is the SentinelBench approach (arxiv 2606.05342, found in search).

The EXIT-file sentinel approach (orchestrator writes a file after `$?`) is not a documented standard — it is a pragmatic workaround for a specific constraint: the orchestrator runs `opencode run` as an external subprocess via Bash, and needs to detect completion without polling the live process. The _standard_ alternative would be to use the `opencode` SDK programmatically (so the call/return is native), or to use framework-level awaiting.

### 3e. Retry and fold-fix

The industry pattern for executor failures is:

1. **Structured failure classes:** Distinguish operational crash (non-zero exit, empty output) from non-crash failure (ran but output is wrong). The OpenAI Agents SDK handles this at the framework level with configurable retry policies and backoff.

2. **Baseline snapshot + restore:** Anthropic Research (2025): "We built systems that can resume from where the agent was when the errors occurred." Restore before retry, not after. The scaffold's pre-handoff checkpoint commit + `git reset --hard HEAD` for botched executors directly matches this.

3. **Fold-fix into next slice brief:** Prescribe the fix as the first item of the next dispatch. This keeps sequential execution and avoids concurrent writers. Addressed in the scaffold's SKILL.md.

4. **Escalation ladder:** Retry with tighter brief → escalate to stronger model. The scaffold's deepseek-first → Sonnet-fallback ladder matches this pattern.

### 3f. Dedicated review agent (evaluator-optimizer)

Anthropic's "Building effective agents" explicitly describes the **evaluator-optimizer** workflow: "one LLM call generates a response while another provides evaluation and feedback in a loop." Used when "LLM responses can be demonstrably improved when a human articulates their feedback." This matches the `openspec-reviewer` pattern — a read-only auditor before implementation that surfaces defects without modifying files.

The OpenAI pattern calls this "running the agent in a while loop with an agent that evaluates." LangGraph implements it as "evaluator-optimizer" cycles between subgraphs.

The mid-2026 standard for this pattern:
- Read-only reviewer with `bash: deny, edit: deny` — cannot hallucinate empirical confirmation
- Severity tiering (blocking / should-fix / suggestion) — standard in code-review agents
- Explicit verdict (PASS / NEEDS REVISION) that gates the pipeline
- Separate context from the planner — not the same session

The scaffold's `openspec-reviewer` matches all four of these. The `bash: deny` constraint is well-motivated by the reviewer anti-pattern Anthropic identified: a reviewer that "confirmed" a constructor kwarg was "available" in a library, which then crashed on the real host.

---

## 4. Scaffold baseline

All citations are to scaffold files.

### Primary orchestrator

`AGENTS.md:52–54` — "The primary agent is the orchestrator and reviewer — not the implementer. It runs the OpenSpec lifecycle (explore, propose, verify, archive) and reviews output; it does not write implementation code."

### Executor dispatch (apply phase)

`AGENTS.md:55–60` — Two executor paths: under Claude Code, `deepseek-v4-flash` via `opencode run` (Sonnet subagent as fallback); under OpenCode, DeepSeek V4 Flash via `@apply-executor`. Either way, implements `tasks.md` sequentially, top-to-bottom, checking off each task.

`.claude/skills/openspec-apply-change/SKILL.md:86–105` — Exact `opencode run` invocation with `--agent apply-executor --model deepseek/deepseek-v4-flash --format json`, `timeout -k 30 600`, stdout to `/tmp/apply-out.jsonl`, stderr to `/tmp/apply-err.log`, with the mandatory `echo "EXIT=$?" > /tmp/apply-out.exit` sentinel.

`.opencode/agents/apply-executor.md:1–6` — OpenCode executor definition: `model: deepseek/deepseek-v4-flash`, `mode: all`, `task: deny` (no further delegation).

`.claude/agents/apply-executor.md:1–6` — Claude Code fallback executor: `model: sonnet`, used only if deepseek/opencode crashes.

### Executor dispatch (archive phase)

`.claude/skills/openspec-archive-change/SKILL.md:126–158` — Same `opencode run` pattern with `--agent archive-executor --model deepseek/deepseek-v4-pro`, same timeout + sentinel. Archive-executor uses V4 Pro (not Flash) because reconciling three project docs is heavier reasoning work.

`.opencode/agents/archive-executor.md:1–14` — Archive executor: `model: deepseek/deepseek-v4-pro`, `webfetch: deny, websearch: deny` (no external access during archive).

### EXIT-file sentinel + completion detection

`.claude/skills/openspec-apply-change/SKILL.md:108–144` — Detailed completion detection rules: "Detect completion by `[ -f /tmp/apply-out.exit ]` in a bounded sleep loop"; "NEVER poll with `until ! pgrep -f '<pattern>'`" (self-matching pattern bug); "never judge a run from a mid-execution jsonl snapshot — deepseek-v4-flash/pro can legitimately take >5 minutes and a short jsonl mid-run is NORMAL. Conclude crash/timeout ONLY if the exit file shows nonzero (124 = timeout, 137 = SIGKILL)."

### Failure ladder

`.claude/skills/openspec-apply-change/SKILL.md:167–181` — Failure ladder: operational crash → retry once with tight brief → Sonnet subagent; non-crash failure → immediately Sonnet subagent. Mandatory disclosure when Sonnet runs.

`.claude/skills/openspec-archive-change/SKILL.md:181–193` — Same ladder for archive, plus explicit baseline-restore before retry.

### Pre-handoff checkpoint

`.claude/skills/openspec-archive-change/SKILL.md:95–119` — Pre-handoff checkpoint commit (`git commit -am`) before delegating to archive-executor. Recovery: `git reset --hard HEAD` + path-scoped `git clean -fd` if executor botches the tree. Never `git stash`; never unscoped `git clean`.

### Review agent

`AGENTS.md:61–66` — `@openspec-reviewer` (`deepseek/deepseek-v4-pro`) is invoked between propose and apply phases. Under Claude Code: `opencode run --agent openspec-reviewer --model deepseek/deepseek-v4-pro`; under OpenCode: Task tool with `subagent_type: "openspec-reviewer"`.

`.opencode/agents/openspec-reviewer.md:1–10` — `model: deepseek/deepseek-v4-pro`, `edit: deny`, `bash: deny` (read-only). `mode: all` — full context access for reading specs/artifacts.

`.opencode/agents/openspec-reviewer.md:35–37` — Position: "between proposal creation and implementation." PASS / NEEDS REVISION verdict gates the pipeline.

### Context isolation

`AGENTS.md:101–110` — "Project-tracked docs — write-deferred, reconciled at archive by a delegated executor. The executor runs with fresh context seeded from the compact, structured change dir artifacts — not the conversation transcript." The archive-executor gets a fresh context with only the specific artifacts it needs (notes.md, proposal.md, design.md, STATUS.md) — not the full session.

### Parallelism stance

`AGENTS.md:126–129` — "Use subagents for independent work. Parallelize independent research/extraction across subagents freely; prefer a cheaper model (e.g. Sonnet) for extraction."

### Sequential apply discipline

`.opencode/agents/apply-executor.md:26–31` — Tasks worked sequentially top-to-bottom; each marked `[x]` before moving to the next.

`.claude/skills/openspec-apply-change/SKILL.md:140–144` — "A premature retry or Sonnet fallback spawns CONCURRENT writers on the same working tree (this has left duplicate work) — which is exactly why completion must be judged from the sentinel, not guessed from process state."

---

## 5. Gap table

| Practice | Status | Evidence | Assessment |
|----------|--------|----------|------------|
| Orchestrator–worker pattern | **Present** | AGENTS.md:52–66; SKILL.md apply & archive | Matches canonical Anthropic/OpenAI pattern precisely |
| Model routing: cheap executor for implementation | **Present** | AGENTS.md:55–58; deepseek-v4-flash as apply-executor | Matches "strong planner + cheap executor" intent |
| Strong model for heavier reasoning (archive, review) | **Present** | deepseek-v4-pro for archive-executor and reviewer | Tiered model selection matches literature best practice |
| Context isolation per subagent | **Present** | AGENTS.md:101–110; fresh context seeded from change artifacts | Matches Anthropic "subagent output to filesystem" guidance |
| Sequential task execution by executor | **Present** | apply-executor.md; SKILL.md sequential loop | Correct for dependency-laden coding tasks (see §3c) |
| Pre-handoff baseline snapshot | **Present** | SKILL.md archive:95–119 | Matches Anthropic "resume from checkpoint" pattern |
| Baseline-restore before retry | **Present** | SKILL.md archive:181–193 | Matches Anthropic recovery discipline |
| Failure ladder (retry → escalate) | **Present** | SKILL.md apply:167–181; archive:181–193 | Matches structured failure class pattern |
| Read-only reviewer agent with bash/edit denied | **Present** | openspec-reviewer.md:6–9 | Matches evaluator-optimizer + anti-hallucination practice |
| Severity-tiered reviewer output (🔴/🟡/💡) + verdict | **Present** | openspec-reviewer.md:99–121 | Matches industry code-review agent pattern |
| EXIT-file sentinel for completion detection | **Present (divergent)** | SKILL.md apply:108–127 | Functional but non-standard (see §3d). Industry uses native SDK return or end-state evaluation; sentinel is a workaround for external subprocess invocation |
| Async fan-out / parallelism for independent tasks | **Partial** | AGENTS.md:126–129 mentions subagent parallelism; but apply/archive are always serialized | Apply and archive executors are single-dispatch; no fan-out for multi-task parallelism |
| pgrep-based process liveness polling | **Explicitly banned** | SKILL.md apply:127–132 | Ahead of teams that still use this pattern; the anti-pattern is called out explicitly |
| Framework-managed retry/backoff (SDK-level) | **Absent** | Retry is hand-coded in SKILL.md | No SDK-level retry policy; all retry logic is prompt-scripted |
| Structured handoff context (typed input_type schema) | **Partial** | Executor briefs are freeform strings in `opencode run` prompt | OpenAI Agents SDK provides typed `input_type` for handoff payloads; scaffold uses plain text |
| Agent observability / tracing | **Absent** | No mention of tracing in any scaffold file | Anthropic Research and Datadog both cite production tracing as essential for debugging |
| Empirical cost validation for planner+executor routing | **Absent** | No measurement of orchestration overhead in scaffold docs | Akitaonrails (2026) shows hidden planner cost can dominate; scaffold has no cost instrumentation |

---

## 6. Candidate recommendations

### R1 — Document the EXIT-file sentinel limitation and add end-state eval as primary success signal

**Change:** In `SKILL.md` apply (step 6.3 "Determine success vs. failure"), add end-state disk verification as the primary success signal: read `tasks.md` for all `[x]` and verify target files exist. The EXIT-file check (`/tmp/apply-out.exit`) should be explicitly labeled what it is — a harness-level liveness sentinel, not a semantic completion check. Rename the comment to "liveness sentinel" and document why: `opencode run` is an external subprocess; in a native SDK integration (Pattern 1 or 2 in Schmid 2026) this sentinel would be replaced by the tool return value.

**Source:** Anthropic Engineering (2025): "focus on end-state evaluation rather than turn-by-turn analysis — evaluate whether it achieved the correct final state" (https://www.anthropic.com/engineering/multi-agent-research-system).

**Confidence:** High

**Constraint-compat:** No constraint conflicts. Agent-neutral (applies equally to the OpenCode and Claude Code paths). State lives in tracked files (`tasks.md`). Does not increase autonomy.

**Effort/Risk:** Low — documentation change only; SKILL.md already has "read back from disk" in step 6.3, this just promotes it and names the sentinel accurately.

---

### R2 — Add a "tight brief" template for retry dispatches

**Change:** In SKILL.md apply, step 6.4 "Failure ladder" (operational crash → retry with tight brief), provide a brief template that (a) names exact files to read, (b) front-loads the already-verified facts, (c) states the remaining unchecked tasks, (d) forbids re-exploration. Currently SKILL.md says "retry with a tight brief: name the exact files to read, front-load the facts you've already verified as given" but provides no template, which leaves the brief quality to the orchestrator's discretion.

**Source:** Anthropic Engineering (2025): "Teach the orchestrator how to delegate... without detailed task descriptions, agents duplicate work, leave gaps, or fail to find necessary information" (https://www.anthropic.com/engineering/multi-agent-research-system). Also: Akitaonrails (April 2026) found that the executor "burns its budget re-deriving context you already have" when briefs are vague (https://akitaonrails.com/en/2026/04/25/llm-benchmarks-vale-a-pena-misturar-2-modelos/).

**Confidence:** High

**Constraint-compat:** No conflicts. Agent-neutral (the brief format is harness-agnostic text). Not autonomy-increasing — tighter briefs reduce deviation from the plan.

**Effort/Risk:** Low — template addition to SKILL.md; no logic change.

---

### R3 — Add input-filter/context-scoping convention for executor handoffs

**Change:** Define a standard "executor brief" structure: (1) frozen artifact paths (proposal, design, tasks), (2) the exact scope of remaining work (unchecked task IDs), (3) explicit "do not re-read files outside this list," (4) completion-report format. Document this in `AGENTS.md` under "State, write discipline" or as a comment block in SKILL.md before the `opencode run` command. This is the freeform-text equivalent of OpenAI Agents SDK's typed `input_type` schema for handoffs (https://openai.github.io/openai-agents-python/handoffs/).

Currently the handoff brief is an inline string in the `opencode run` command; it is correct but informal. A documented template makes the convention explicit for future maintainers and provides a target structure for both platforms (Claude Code and OpenCode).

**Source:** OpenAI Agents SDK handoffs (https://openai.github.io/openai-agents-python/handoffs/): `input_type` provides typed, validated payload scoping; the principle is "metadata the model decides at handoff time, not application state you already have." Anthropic Research (2025): "Each subagent needs an objective, an output format, guidance on the tools and sources to use, and clear task boundaries."

**Confidence:** Medium — the current practice is already close; this is about making the convention explicit, not fixing a functional gap.

**Constraint-compat:** No conflicts. Agent-neutral (template is plain text). Not Claude-only. Fits template/placeholder (`<FILL:…>`) structure.

**Effort/Risk:** Low-medium — adds a documented convention; risk of template over-prescribing and reducing flexibility for unusual changes.

---

### R4 — Add a "fold-fix" protocol for verify-found defects

**Change:** In AGENTS.md (working process) and in the verify SKILL.md (if it exists), explicitly document the fold-fix pattern: "when verify finds a defect, diagnose and scope it, then treat the fix as the *first item* of a new apply-executor brief (not a separate fix run)." AGENTS.md:173 already says "re-delegate the fix to a fresh executor (deepseek-first, Sonnet-fallback)" but does not say to fold the fix into a new scoped brief rather than running a second full `tasks.md` pass. The distinction matters: a full re-run re-reads the entire change context and may re-implement already-done tasks.

**Source:** Scaffold SKILL.md apply:140–144 mentions fold-fix for multi-slice large changes ("fold the scoped fix as the first item of slice N+1's brief instead of a separate fix run"). This should be elevated to a general rule in AGENTS.md, not buried in a conditional SKILL comment. Matches Anthropic's "sequential, no concurrent writers, one fewer invocation" principle.

**Confidence:** High — this is already in the scaffold at one level of specificity; elevating it to a cross-cutting rule in AGENTS.md reduces the chance of a future maintainer missing it.

**Constraint-compat:** No conflicts. Agent-neutral. No autonomy increase (still explicit gate between phases).

**Effort/Risk:** Low — text addition to AGENTS.md.

---

### R5 — Add a brief note on when NOT to delegate (dependency-laden vs. parallelizable)

**Change:** In AGENTS.md under "Use subagents for independent work," add a 2-sentence note: "Delegation only saves cost/time when tasks are genuinely independent (no output of task A needed to start task B). Cohesive, dependency-laden work (building an integrated feature in a single codebase) degrades quality and increases total cost under delegation; the sequential executor pattern exists specifically to handle this case in-process."

This documents a deliberate design choice that is easy to misread as a limitation (why only one executor, not a fan-out?). Without this note, a future maintainer may add parallelism assuming it will help.

**Source:** Akitaonrails (April 2026): "Sequential task with dependencies = building a cohesive app. There's no parallelization possible, and adding agents only adds overhead." (https://akitaonrails.com/en/2026/04/25/llm-benchmarks-vale-a-pena-misturar-2-modelos/) + Anthropic Research (2025): "most coding tasks involve fewer truly parallelizable tasks than research, and LLM agents are not yet great at coordinating and delegating to other agents in real time" (https://www.anthropic.com/engineering/multi-agent-research-system).

**Confidence:** High — strongly sourced empirical finding directly applicable to the scaffold's coding-task domain.

**Constraint-compat:** No conflicts. Not Claude-only. Does not change behavior, only documents the rationale for the existing sequential design.

**Effort/Risk:** Very low — 2 sentences to AGENTS.md.

---

### R6 — Consider a minimal completion-signal convention for the OpenCode executor

**Change:** Evaluate whether the OpenCode `@apply-executor` and `@archive-executor` should write a lightweight completion receipt to disk (e.g., a `.done` file with exit status and summary path) at the end of their run — independently of the `opencode run` sentinel. Under Claude Code the EXIT-file is written by the `echo "EXIT=$?"` Bash wrapper; under OpenCode the Task tool returns natively and no such file is written. If OpenCode resumes become unreliable (e.g., the orchestrator context truncates before the task return), the OpenCode path currently has no filesystem-level evidence of completion, while the Claude Code path does.

This is a low-confidence candidate because OpenCode's Task tool return is synchronous and generally reliable, but it would make both paths symmetric in their observable completion evidence.

**Source:** Anthropic Engineering (2025): "Without effective mitigations, minor system failures can be catastrophic for agents... we built systems that can resume from where the agent was when the errors occurred. We combine the adaptability of AI agents built on Claude with deterministic safeguards like retry logic and regular checkpoints." (https://www.anthropic.com/engineering/multi-agent-research-system)

**Confidence:** Low — the current OpenCode path is probably fine; this only matters if Task tool reliability degrades.

**Constraint-compat:** No conflicts. Agent-neutral (each platform writes to the shared working tree). State is a tracked file. Autonomy unchanged.

**Effort/Risk:** Low effort if added; low risk of harm. Main risk: maintenance overhead of one more convention.

---

## 7. Already-ahead / doesn't-fit

### Already ahead of standard

**Anti-pgrep documentation:** The scaffold explicitly bans `until ! pgrep -f "<pattern>"` completion polling with a detailed explanation of *why* (self-matching the poller's own command line). This is a specific, well-known failure mode that is not documented in any of the industry sources consulted. The scaffold's treatment is ahead of published guidance. (SKILL.md apply:127–132)

**Sequential executor discipline with explicit "no concurrent writers" rationale:** The scaffold explicitly documents *why* parallelism must be avoided for coding tasks (concurrent writers on the same working tree). Most multi-agent frameworks encourage fan-out by default without this caveat. The scaffold's stance matches the empirical finding in Akitaonrails (2026) but gets there from first principles, documented in 2024–2025 before that benchmark existed.

**Baseline-restore-before-retry pattern:** The archive skill's `git reset --hard HEAD` + path-scoped `git clean` baseline restore before any executor retry is more rigorous than the retry patterns documented in OpenAI Agents SDK or Anthropic's public guidance, which describe retry in conceptual terms but not the exact filesystem restore protocol.

**Dual-harness symmetry:** The scaffold maintains complete functional parity between Claude Code (`opencode run` + EXIT sentinel) and OpenCode (`@apply-executor` via Task tool). Industry standards from Anthropic, OpenAI, and LangGraph are each single-platform. The dual-harness design is a unique scaffold property with no direct industry parallel.

**`task: deny` on apply-executor:** The apply-executor explicitly blocks the `task` tool (`task: deny` in `.opencode/agents/apply-executor.md:13`), preventing the executor from spawning its own sub-executors. This limits blast radius and keeps the concurrency model simple. Industry guidance (Schmid 2026, Pattern 3–4) warns that models lose track of multi-agent state; `task: deny` is a principled constraint that is not commonly documented.

### Practices deliberately not recommended

**Agent pool / teams patterns (Schmid Patterns 3–4):** Not recommended. Require frontier-class models at every agent node, add cross-agent message routing complexity, and exceed the scaffold's Constraint 4 (autonomy stays opt-in). The scaffold's use case (sequential coding tasks with a single executor) does not benefit from persistent agent pools or agents messaging each other.

**Claude Code Agent Teams:** Claude Code introduced "Agent Teams" (experimental, opt-in via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, added in v2.1.32) where teammates can message each other directly via a shared task list (Shipyard 2026). This is **Claude-only** (Constraint 1 — no OpenCode equivalent exists). Additionally, Agent Teams are explicitly designed for large parallel workloads ("multiple Claude Code instances") — the opposite of the scaffold's sequential coding pattern. Flagged: Claude-only — no OpenCode equivalent; unsuitable for a neutral template.

**Framework-managed retry (SDK-level):** Not recommended as a replacement for the current hand-coded ladder. The scaffold's explicit ladder gives the orchestrator fine-grained control over which failure type triggers which response. SDK-managed retry is opaque and does not distinguish between operational crash and non-crash failure. The scaffold's explicit `grep '"Falling back to default agent"'` check (SKILL.md:149) is a correctness check that SDK retry cannot replicate.

**Async execution (lead-agent fan-out):** Not recommended for the apply phase. Anthropic Research (2025) notes async is on their roadmap but adds "challenges in result coordination, state consistency, and error propagation." For coding tasks specifically, the sequential dependency constraint makes async fan-out actively harmful (concurrent writes to the same files). Partial for research/explore tasks where the scaffold's AGENTS.md already permits parallelism.

**Cost-optimization by model downgrade:** Not recommended as a general policy. Akitaonrails (April 2026) empirically shows that for typical coding tasks, the "savings" of a cheaper executor are erased by planner overhead and quality degradation. The scaffold already makes a well-considered model choice (deepseek-v4-flash for apply, deepseek-v4-pro for heavier reasoning in archive/review). Further downgrade is not supported by current evidence.

**LLM-as-judge for executor output:** Not recommended at this time. The scaffold's orchestrator reviews executor output directly (reads `git diff`, checks `tasks.md`). Adding a separate LLM judge step would increase latency and cost for a use case where deterministic checks (all tasks `[x]`, diff is non-empty) are more reliable than LLM evaluation.

---

## 8. Open questions for the operator

**OQ-1 (model choice validity):** The deepseek-v4-flash / deepseek-v4-pro choices were made at scaffold creation time. Akitaonrails (April 2026) found that OpenCode + solo Opus 4.7 outperforms all planner+executor combinations on a greenfield coding task. Has the operator benchmarked deepseek-v4-flash vs. a frontier model solo for the scaffold's apply phase? The model choices may need revisiting as model capabilities shift.

**OQ-2 (EXIT-file sentinel adequacy):** The scaffold notes the harness has "no subagent resume" (AGENTS.md:123) and that a killed agent restarts cold. If `opencode run` is killed mid-task (OOM, SIGKILL), the EXIT-file may never be written (timeout kill at 600s writes exit=124; abrupt SIGKILL at the OS level would not). Is the 600s timeout sufficient for all expected task sizes? The SKILL.md suggests splitting large changes into slices; is this constraint documented as a ceiling on task size?

**OQ-3 (parallelism for explore/research phases):** AGENTS.md:126–129 says to parallelize independent research across subagents. The scaffold has no `explore-executor` analog — explore work is done inline by the orchestrator. Is this intentional (explore is cheap enough to keep inline) or a gap to address?

**OQ-4 (cost instrumentation):** The scaffold has no mechanism to track per-phase token cost or execution time. Akitaonrails (2026) discovered that hidden orchestrator overhead was 3× the executor cost. If cost becomes a concern (pay-as-you-go projects), adding even minimal cost logging (timestamp + rough token estimate per executor dispatch) would surface unexpected overhead.

**OQ-5 (deepseek reasoning_content bug — confirmed, multiple GitHub issues open):** Akitaonrails Round 3 found a structural incompatibility: deepseek-v4-pro returns `reasoning_content` on every response, and opencode strips that field when constructing the next request, causing the DeepSeek API to reject turn 2 with `"reasoning_content must be passed back to the API"`. **This is confirmed by at least 7 separate GitHub issues on the opencode repo** (issues #24104, #24122, #24124, #24130, #24135, #24261, #25000 — all opened late April 2026): "DeepSeek V4 enables thinking mode by default and returns `reasoning_content` in responses. The `@ai-sdk/openai-compatible` SDK doesn't handle this field, causing it to be lost between conversation turns." The conversation fails at turn 2 of any dispatch. The known workaround is to use the Anthropic-compatible endpoint (`baseURL: https://api.deepseek.com/anthropic`) with `@ai-sdk/anthropic` as the provider, which "properly preserves `reasoning_content` across conversation turns."

**If the scaffold's deepseek-v4-pro executor (archive-executor, reviewer) uses the standard DeepSeek provider via opencode, every multi-turn dispatch silently falls back to the `general` agent.** The SKILL.md's `grep '"Falling back to default agent"'` check would catch this, but only if the operator reads the assert-the-real-executor-ran step. The bug affects both deepseek-v4-flash and deepseek-v4-pro.

Action item for operator: (a) verify which opencode provider config is in use for the scaffold's DeepSeek models; (b) check whether the Anthropic-compatible endpoint workaround is applied; (c) confirm the `Falling back to default agent` assert has been run at least once to validate the executor identity. The pending-extrends-sync findings file may already track this if it surfaced during the 2026-06-13 audit.
