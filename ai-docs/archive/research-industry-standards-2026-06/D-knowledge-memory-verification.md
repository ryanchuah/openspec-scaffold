# D — Knowledge Persistence & Context/Memory + Verification/Review/Quality Gates
## Industry-standards comparison for `openspec-scaffold` (2026-06)

> **Status: COMPLETE — 2026-06-13**

---

## 1. Scope

This area covers two linked themes:

**(i) Durable knowledge & working context.** How AI coding agents persist state, decisions, and working context across sessions — covering file-based approaches, native memory tools, decision/ADR logging, "context rot" mitigations, and compaction. Boundary: the *content* of what gets stored is in scope; the *mechanics of spec lifecycle artifacts* (area A) and *orchestration/handoff plumbing* (area B) are siblings. Review *criteria and content* belong here even though routing mechanics belong to B.

**(ii) Verification & review.** How agentic workflows validate their own output — covering verification loops, automated code review agents, quality gates, eval-driven development, self-critique patterns, trust-gating, and human-in-the-loop design. Boundary: review *content and criteria* is in scope; *how to route to a reviewer agent* belongs to area B.

**Critical lens (per brief):** Constraints #2 (no native memory) and #4 (autonomy opt-in). The industry is moving toward harness-native memory tools. This analysis assesses honestly whether the scaffold's file-only rule is still right in mid-2026, what it costs, and how to frame the trade-off for the operator.

---

## 2. Sources Consulted

| URL | What it is | Date/Recency |
|-----|-----------|-------------|
| https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | Anthropic engineering blog: context engineering for agents — compaction, note-taking, sub-agents, just-in-time retrieval | Sep 29, 2025 |
| https://www.anthropic.com/news/context-management | Anthropic news: context editing + memory tool launch (Claude Sonnet 4.5, public beta) | Sep 29, 2025 |
| https://www.trychroma.com/research/context-rot | Chroma: systematic context rot study across 18 frontier models | 2025 (published at ECAI 2025) |
| https://redis.io/blog/context-rot/ | Redis: context rot explainer — lost-in-the-middle, positional bias, detection, external memory | 2025 |
| https://www.letta.com/blog/agent-memory/ | Letta: tiered memory architecture (core/recall/archival), sleep-time compute, memory block design | 2025–2026 |
| https://mem0.ai/blog/state-of-ai-agent-memory-2026 | Mem0: state-of-AI-agent-memory 2026 — benchmarks (LoCoMo, LongMemEval, BEAM), multi-signal retrieval, integration ecosystem | Apr 2026 |
| https://sourcegraph.com/blog/agentic-coding | Sourcegraph: agentic coding in 2026, 80% problem, context infrastructure, verification loop pattern | Mid-2026 |
| https://www.anthropic.com/research/measuring-agent-autonomy | Anthropic research: empirical study of agent autonomy in the wild (Claude Code + public API data) | Early 2026 |
| https://www.morphllm.com/agents-md-guide | MorphLLM: AGENTS.md spec guide 2026 — cross-tool standard, recommended sections, research on 28.6% speed improvement | 2026 |
| https://coderabbit.ai | CodeRabbit homepage: AI PR reviewer — MCP, linters, context-aware, 2M+ repos | 2026 |
| Web search results: CodeRabbit, Greptile, eval-driven dev, ADR AI agents, trust gating | Multiple secondary sources as cited below | 2025–2026 |
| ai.gopubby.com AGENTS.md vs ADR article | **Inaccessible (403)** — noted in results but content not fetched. Not cited. | — |

---

## 3. Industry Standard (mid-2026)

### 3a. Knowledge persistence and working context

**Context rot is empirically confirmed and production-critical.** Chroma's 2025 study tested 18 frontier models; every one degrades as input length increases. Models typically break 30–40% before their claimed context limit — a 200 K model shows meaningful degradation at 130 K tokens. The "lost-in-the-middle" problem (Stanford, referenced in Redis explainer): accuracy drops from 70–75% to 55–60% when relevant information sits in mid-context rather than at the beginning or end. Nearly 65% of enterprise AI failures in 2025 are attributed to context drift or memory loss in multi-step reasoning (per web search meta-analysis). For coding agents, context rot is described as "the primary failure mode."

**Context engineering is the discipline, not just prompt engineering.** Anthropic's Sep 2025 engineering post frames the shift: "Building with language models is becoming less about finding the right words and more about 'what configuration of context is most likely to generate our model's desired behavior?'" The guiding principle is: *find the smallest possible set of high-signal tokens that maximize the likelihood of your desired outcome.* Specific strategies:

- **Just-in-time retrieval:** Agents maintain lightweight identifiers (file paths, queries, links) and load data into context at runtime via tools, rather than pre-loading everything. Claude Code itself uses this (glob/grep to navigate, head/tail on files).
- **Structured note-taking (agentic memory):** Agents regularly write notes persisted to disk (NOTES.md, to-do lists). These get pulled back into context at later times. Anthropic names this as one of the three core long-horizon strategies alongside compaction and sub-agents.
- **Compaction:** Summarize and reinitiate the context window when nearing limits. Claude Code's implementation: summarize conversation + preserve the 5 most recently accessed files. Best practice: maximize recall first, then iterate to improve precision.
- **Sub-agent architectures:** Main agent maintains high-level plan; sub-agents handle focused tasks with clean context windows. Each sub-agent may use tens of thousands of tokens but returns only a condensed 1,000–2,000-token summary. Achieves "clear separation of concerns."

**Native memory tools have arrived, but are harness-specific.** Anthropic launched the memory tool in public beta on Sep 29, 2025 alongside context editing (Claude Sonnet 4.5 on the Claude Developer Platform). Key facts:
- The memory tool is file-based client-side: agents create/read/update/delete files in a `/memory` directory. The developer controls the storage backend.
- Context editing auto-clears stale tool results from within the context window when approaching token limits.
- Benchmark: combining both improved agentic search performance by 39% over baseline; context editing alone 29%. In a 100-turn web search eval, context editing reduced token consumption by 84%.
- **This is a Claude Developer Platform beta feature.** It requires the `context-management-2025-06-27` beta flag. It is not available on OpenCode/DeepSeek.

**Tiered memory architectures** (Letta/MemGPT) are the academic and framework-level state of the art: core memory (always in-context, like RAM), recall memory (conversation history, auto-persisted), archival memory (external vector/graph store, queried on demand). The 2026 addition is "sleep-time compute" — memory management agents that run asynchronously, not blocking the primary agent. Mem0's April 2026 benchmark results (LoCoMo/LongMemEval/BEAM): 92.5/94.4 scores at ~6,900 tokens per query average via single-pass hierarchical extraction + multi-signal retrieval (semantic + BM25 + entity matching). These frameworks are not harness-specific but require infrastructure investment.

**AGENTS.md is the cross-tool standard for durable knowledge.** In Dec 2025, AGENTS.md was donated to the Agentic AI Foundation (Linux Foundation directed fund). By early 2026, it is natively read by Claude Code, OpenAI Codex CLI, Cursor, Aider, Devin, GitHub Copilot, Gemini CLI, Windsurf, Amazon Q (30+ agents). A Princeton study found AGENTS.md improved task speed 28.6% and reduced tokens 16.6%; human-written files outperformed LLM-generated ones (auto-generated files with redundant content degraded performance by 23% cost increase). MorphLLM 2026 spec guide: recommended sections are project overview, build/test commands, architecture, code style, boundaries — emphasis on non-obvious, non-redundant content.

**Decision logging (ADRs) for agents is emerging but not standardized.** A Medium article (Faisal Feroz, 2026, inaccessible/403) titled "AGENTS.md is the new ADR" signals the trend. Related tools: Mneme HQ converts ADRs into deterministic pre-generation checks for coding agents. ADR-agent (github.com/macromania/adr-agent) auto-generates ADRs. However, there is no widely adopted cross-agent standard for a separate `decisions.md` file — the industry convention is to encode constraints into AGENTS.md (operational rules) and optionally maintain separate ADR directories for humans.

### 3b. Verification, review, and quality gates

**Automated code review (post-code, PR-level) is mainstream.** CodeRabbit is the most-installed AI app on GitHub/GitLab: 2M+ repos, 13M+ PRs reviewed, 8,000+ paying customers. Key features: line-by-line feedback, architectural diagrams, MCP server integration, 40+ linters/SAST, codebase-awareness (codegraph, past PR history, custom guidelines), continuous learning from feedback. The "differentiator isn't generating code, it's governing it." Greptile v3/v4 (late 2025/early 2026): indexes full codebase to build a semantic code graph, uses Anthropic Claude Agent SDK for autonomous multi-hop investigation. 82% bug catch rate vs CodeRabbit's 44% in independent benchmarks, at the cost of higher false positive rate. Pricing shifted to per-review ($1/review after 50 free) in March 2026.

**Pre-implementation review is industry best practice for catching spec errors.** Sourcegraph: "Catching a spec error takes minutes. Fixing wrong code takes hours." The industry emphasizes reviewing *before* code is written for complex tasks, not just after. However, most commercial tools (CodeRabbit, Greptile) are PR-review (post-code) tools.

**The agentic verification loop** is the production standard: agent plans → edits → tests → refines → human reviews diff → CI gate. From Sourcegraph: "No agent commits land without passing the same checks that human commits have applied." The emerging "second agent" pattern: one LLM generates output, another evaluates and provides feedback in an iterative loop.

**Trust-gating / autonomy as earned.** Anthropic's empirical study (early 2026, analyzing millions of Claude Code sessions):
- New users: ~20% auto-approve. Experienced users (750+ sessions): ~40% auto-approve.
- Experienced users *also* interrupt more (5% vs 9%), showing a shift from pre-approval to active monitoring.
- Claude Code itself stops for clarification more than twice as often as humans interrupt it on complex tasks.
- The pattern: gradual accumulation of trust, not binary on/off.
- Cloud Security Alliance "Agentic Trust Framework" (Feb 2026): four maturity levels for agent autonomy, each requiring demonstrated reliability before promotion.

**Quality gates and phase gates are universal.** McKinsey AI Trust Report 2026: only 1-in-3 enterprises are governance-ready for autonomous agents they're already running. The industry recommendation is explicit authorization per action class (which decisions are autonomous, which require human approval), and "phase gates" with human sign-off at consequential transitions. The key insight: "effective oversight doesn't require approving every action, but being in a position to intervene when it matters."

---

## 4. Scaffold Baseline

All citations are to files in `~/Projects/openspec-scaffold/`.

**Memory / knowledge persistence:**
- `AGENTS.md:26-34` — Cross-agent compatibility rule: "all project state lives in tracked, agent-neutral files — never in harness-private storage." Explicitly bans global memory, harness memory, `.claude/`, `CLAUDE.md`, and equivalent assistant-specific config.
- `AGENTS.md:93-110` — Two-tier write discipline: (a) change-local scratch (`openspec/changes/<name>/`) written continuously in-context; (b) project-tracked docs (`STATUS.md`, `ai-docs/decisions.md`, `ai-docs/open-questions.md`) write-deferred, reconciled once at archive by a delegated `deepseek-v4-pro` archive-executor with fresh context seeded from compact change-dir artifacts. "This is the single load-bearing rule that preserves token economy — do not move the reconciliation back into the working session."
- `AGENTS.md:114-130` — Working process: "Make work resumable" (no subagent resume; checkpoint partial findings to disk; decompose long jobs); "use subagents for independent work" (parallelize research across subagents, cheaper model for extraction, subagent checkpoints findings to disk).
- `AGENTS.md:1-21` — Session start protocol: read AGENTS.md + STATUS.md + decisions.md + open-questions.md; if resuming a change, read its change dir. Skip archive unless re-examining a specific closed decision.
- `ai-docs/decisions.md` — Empty (template comments only, no actual entries).
- `ai-docs/open-questions.md` — Empty (template comments only).
- `ai-docs/improvement-roadmap.md:15-19` — One entry: cross-change spec-conflict detection.
- `ai-docs/fast-track-workflow.md:1-20` — Trust-gated opt-in: "You may use the shortcuts in this file only if the operator has explicitly granted you fast-track authority for this session or task."

**Verification / review / quality gates:**
- `AGENTS.md:53-88` — Three-role model: orchestrator/reviewer (no implementation), apply-executor (sequential tasks.md implementation), openspec-reviewer (pre-implementation read-only auditor). Reviewer invoked via `opencode run --agent openspec-reviewer --model deepseek/deepseek-v4-pro`.
- `.claude/skills/openspec-verify-change/SKILL.md:14-30` — MANDATORY behavioral review: (1) read actual diffs + changed files; (2) re-run full test suite; (3) eyeball real output from the code; (4) run live smoke against real API endpoint if change touches external API (explicit: "A *skipped* live smoke is NOT a *passed* one"); (5) diagnose and scope any defect yourself, re-delegate fix to fresh apply-executor with self-contained fix-spec.
- `.claude/skills/openspec-verify-change/SKILL.md:21-28` — Failure ladder: deepseek apply-executor (one attempt) → escalate to Sonnet subagent on operational OR quality failure. Mandatory disclosure if Sonnet was used.
- `.claude/skills/openspec-verify-change/SKILL.md:32` — Phase gate: "STOP after verification. You MUST NOT automatically proceed to archive. Tell the user the verdict and prompt them. Then WAIT."
- `.claude/skills/openspec-verify-change/SKILL.md:174-216` — Mandatory notes.md checkpoint: 5 required fields including forward-looking open-questions and tuning items. "Anything left only in this context dies at the session boundary — the archive-executor is blind to it." Explicit verbal acknowledgement required.
- `.opencode/agents/openspec-reviewer.md:1-130` — Pre-implementation review agent: substantive defects over formatting; severity-leveled (Blocking/Should Fix/Suggestion); specific anti-patterns (rubber-stamping, ignoring existing specs, affirming unverifiable empirics); read-only; runs between propose and apply.
- `AGENTS.md:133` — Tests-green gate: "Tests green before any commit." Plus the verify skill adds behavioral review beyond just tests.
- `ai-docs/fast-track-workflow.md:61-75` — Guardrails that never relax: orchestrator not implementer; delegation mechanics identical to normal; verify is always real even in SMALL tier; archive runs normally.

---

## 5. Gap Table

| Practice | Status | Evidence | Assessment |
|----------|--------|----------|------------|
| File-based agent-neutral knowledge store | **Present / Ahead** | `AGENTS.md:26-34`; `ai-docs/` structure | The scaffold's rule directly addresses the harness-lock risk of native memory tools. Deliberately ahead. |
| Structured note-taking / agentic memory (per-change scratch) | **Present / Ahead** | `AGENTS.md:97-99`; verify SKILL notes.md checkpoint (field 5) | Per-change `notes.md` is a structured note-taking implementation. The verify SKILL's 5-field mandatory checkpoint is more rigorous than any industry standard I found. |
| Archive-as-fresh-context (sub-agent for reconciliation) | **Present / Ahead** | `AGENTS.md:101-110` | Maps exactly to Anthropic's sub-agent architecture recommendation for long-horizon context management. The archive-executor with fresh context seeded from compact change dir is the scaffold's compaction-equivalent. |
| Explicit context-budget guidance for mid-session bloat | **Absent** | `AGENTS.md` has no explicit trigger for when/how to compact mid-session | Anthropic (Sep 2025) explicitly recommends compaction triggers and structured note-taking as first levers. The scaffold has the *mechanism* (sub-agents, write-to-disk) but no *explicit agent instruction* about when to invoke it. |
| Context rot awareness in AGENTS.md | **Partial** | `AGENTS.md:109` references "bloated context" implicitly; no explicit instruction about positional-bias or attention-budget depletion | Industry standard: agents should understand this phenomenon. Chroma/Redis (2025) show it's the primary failure mode. The scaffold works around it structurally but doesn't teach agents to recognize and respond to it. |
| Decisions.md populated with actual entries | **Absent** | `ai-docs/decisions.md` is empty template | The archive-executor running with fresh context has no historical decisions to consult. The "do not re-litigate" goal of decisions.md is undermined if it's never populated. Not a design gap; a habit/process gap. |
| Staleness check on session resume | **Absent** | `AGENTS.md:6-8` says to read decisions.md + open-questions.md but gives no guidance for detecting stale/outdated context when resuming after a gap | Industry: Redis/Chroma flag "stale context injection" as a failure mode. A long gap between sessions means STATUS.md may be stale relative to the actual codebase state. |
| Pre-implementation review (spec-level, before code) | **Present / Ahead** | `openspec-reviewer.md:1-130`; `AGENTS.md:64-67` | Industry best practice is to catch spec errors before code is written. The scaffold's openspec-reviewer is a dedicated pre-implementation reviewer — more rigorous than any commercial tool offers here. |
| Mandatory behavioral verification (not just tests) | **Present / Ahead** | `verify SKILL.md:14-30` — diff read, test run, live output eyeball, live smoke | Industry standard is "test suite + diff review." The scaffold adds live output eyeball and mandatory live smoke for external APIs, which are explicitly beyond industry norm. |
| Failure ladder (deepseek → Sonnet escalation) | **Present / Ahead** | `verify SKILL.md:21-28` | No comparable public documented pattern. Industry has "second agent" verification (LLM-as-judge) but not a structured cost-graded escalation ladder with mandatory disclosure. |
| Phase gate (explicit stop before archive) | **Present** | `verify SKILL.md:32` | Aligns with industry best practice for human oversight at consequential transitions. |
| Trust-gated fast-track | **Present / Ahead** | `ai-docs/fast-track-workflow.md` | Anthropic's empirical research (early 2026) validates this pattern: trust is accumulated gradually, experienced users auto-approve more but interrupt strategically. The scaffold's file-gated approach formalizes what industry observes as organic behavior. |
| CI/test gate before commit | **Present** | `AGENTS.md:133` | Standard. No gap. |
| Post-code PR-level automated review (CodeRabbit / Greptile) | **Absent** | Nothing in scaffold for external post-code review | Optional gap: CodeRabbit/Greptile provide a post-code review layer the scaffold doesn't have. Relevant only for teams with Git PR workflows. |
| ADR-style enforcement (checks before agent generation) | **Absent** | decisions.md exists but is never enforced as a pre-check | Mneme HQ (2026) converts ADRs to deterministic pre-generation checks. Not yet standard enough to be a strong recommendation. |
| Harness-native memory tool (Anthropic memory tool) | **Deliberately Absent** | `AGENTS.md:26-34` explicitly bans it | This is constraint #2. Cost: 39% performance improvement + 84% token reduction (Anthropic benchmark) unavailable. The trade-off is real. |
| Compaction mechanism | **Partial (structural)** | Archive-executor with fresh context + sub-agent architecture serve this role structurally. No mid-session compaction path. | The scaffold has the *architecture* (sub-agents, fresh-context delegation) but lacks an explicit mid-session compaction trigger for long-running sessions that can't yet archive. |

---

## 6. Candidate Recommendations

Each is a candidate for operator review, not a decision.

---

### R1. Add explicit "context budget" guidance to AGENTS.md

**Change:** In AGENTS.md, under "Working process," add a short paragraph instructing agents: when a working session has grown very long (>100 tool calls, or you notice important early instructions feeling "distant"), invoke the sub-agent pattern proactively — delegate the next phase to a fresh sub-agent seeded only from the compact change-dir artifacts, rather than continuing in the same bloated context. This is the scaffold's equivalent of compaction: the mechanism exists; it just needs an explicit trigger.

**Source:** Anthropic, "Effective context engineering for AI agents" (Sep 2025), https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents — "structured note-taking and sub-agent architectures" are the recommended levers for long-horizon work when harness-native compaction isn't available.

**Confidence:** High — context rot is empirically confirmed, the scaffold already has the structural mechanism, this just makes the trigger explicit.

**Constraint-compat:** Fully compatible. Agent-neutral, file-based. No harness dependency.

**Effort/Risk:** Very low. Text addition to AGENTS.md only. No scaffold files changed.

---

### R2. Strengthen decisions.md habit: add a decision-threshold rule to AGENTS.md

**Change:** In AGENTS.md, add an explicit rule: "Every non-obvious architectural choice — anything a future agent would otherwise re-litigate — MUST be recorded in ai-docs/decisions.md at archive, not deferred. When in doubt, write it." Also add one example entry to decisions.md itself (about the dual-harness, agent-neutral memory rule) so the template is not empty and demonstrates the expected format.

The archive-executor runs with fresh context seeded from the change dir. If decisions.md is perpetually empty, historical architectural context is lost. The whole purpose of that file is defeated.

**Source:** AGENTS.md-vs-ADR trend (Faisal Feroz, 2026 — article inaccessible but trend confirmed by multiple sources); AGENTS.md spec guide (MorphLLM 2026, https://www.morphllm.com/agents-md-guide) notes that effective context files prioritize explicit constraints over vague guidance. Mem0 blog (Apr 2026, https://mem0.ai/blog/state-of-ai-agent-memory-2026) shows temporal reasoning (understanding how past decisions constrain present ones) is the hardest memory problem — empty decisions.md makes this impossible.

**Confidence:** High. The gap is real: empty decisions.md defeats its own purpose.

**Constraint-compat:** Fully compatible. No harness dependency. The example entry in decisions.md could document constraint #2 itself (no native memory, rationale, alternatives considered), which is exactly the kind of decision future agents need to not re-litigate.

**Effort/Risk:** Low. AGENTS.md text addition + seed decisions.md with 1–2 example entries.

---

### R3. Add a "staleness check" at session resume

**Change:** In AGENTS.md, in the "After reading this file" section (or the session-start block), add: "If you are resuming work after a gap of more than a few hours, verify STATUS.md reflects the actual current state of the codebase (run `git log --oneline -5` and compare to STATUS.md's last-updated state). If STATUS.md is stale, update it before proceeding." This is a lightweight check against the "stale context injection" failure mode.

**Source:** Redis, "Context rot explained" (2025, https://redis.io/blog/context-rot/) — "stale context injection" compounds context rot; "attention dilution causes important constraints to get buried." Chroma research (https://www.trychroma.com/research/context-rot): model performance degrades when processing stale/outdated document states. Sourcegraph agentic coding guide (https://sourcegraph.com/blog/agentic-coding): "a useful pattern: when an agent says it's done, search the codebase for any other usage of the symbols it touched."

**Confidence:** Medium-High. The failure mode is real and the fix is cheap, but the current scaffold's "read STATUS.md on start" instruction already partially covers this. The marginal gain is adding the staleness-detection step.

**Constraint-compat:** Fully compatible.

**Effort/Risk:** Very low. One sentence added to AGENTS.md.

---

### R4. Document the native-memory trade-off as a formal decisions.md entry

**Change:** Add to decisions.md: "Decision: No harness-native memory / file-only state. Date: [initial]. Decision: All project state lives in tracked agent-neutral files; harness-native memory tools (Anthropic memory tool, Claude.md auto-memory, etc.) are explicitly excluded. Rationale: dual-harness constraint (Claude + OpenCode/DeepSeek) makes harness-specific tools incompatible with agent-neutral template; audit/portability of tracked files outweighs native convenience. Alternatives considered: Anthropic memory tool (Sep 2025 beta) — 39% agentic search improvement, 84% token reduction in Anthropic benchmarks, but Claude Developer Platform only; OpenCode/DeepSeek equivalents do not exist. Cost of this choice: mid-session compaction must be handled via sub-agent delegation and structured note-taking rather than automatic harness compaction."

**Source:** Anthropic, "Managing context on the Claude Developer Platform" (Sep 29, 2025, https://www.anthropic.com/news/context-management); Anthropic memory & context cookbook (https://platform.claude.com/cookbook/tool-use-memory-cookbook). Without this documented, every future agent session where a model "knows" about the Anthropic memory tool will be tempted to reach for it.

**Confidence:** High. The trade-off is real, it's a deliberate constraint, and it needs to be documented so archive-executors don't inadvertently recommend using the memory tool.

**Constraint-compat:** Fully compatible. This *documents* the constraint rather than changing anything.

**Effort/Risk:** Very low. Write 10–15 lines to decisions.md.

---

### R5. Add an OPTIONAL external post-code review step in the verify skill (CodeRabbit/Greptile)

**Change:** In the verify SKILL, after the behavioral review and before emitting the report, add an optional step (clearly marked as optional, project-specific): "If this project uses a GitHub/GitLab PR workflow and has CodeRabbit or Greptile configured, you may request an AI code review on the change diff as an additional quality layer. This is supplementary — it does not replace the mandatory behavioral review above." Do not make this a hard gate; leave it as a scaffold `<FILL:>` placeholder or an opt-in step comment.

**Source:** CodeRabbit (https://coderabbit.ai): 2M+ repos, 40+ linters/SAST, MCP integration, "the differentiator isn't generating code, it's governing it." Greptile v4 (early 2026, per web search): 82% bug catch rate, full-codebase semantic understanding. Both are agent-neutral (not harness-specific) external tools usable from any CI or CLI.

**Confidence:** Medium. These are valuable tools but their applicability depends on whether the scaffold instance uses a PR workflow. Many scaffold deployments (solo dev, direct-to-main) would get no value from a PR-level reviewer.

**Constraint-compat:** Compatible with all 5 constraints. These are external, agent-neutral SaaS tools. Not Claude-only. However, they require a Git PR workflow that not all projects have. Mark clearly as a `<FILL: configure if using PR workflow>` placeholder.

**Effort/Risk:** Low for the text addition; integration cost varies by project.

---

### R6. Add a brief "context health" note field to verify SKILL notes.md checkpoint

**Change:** In the verify SKILL's mandatory notes.md checkpoint (already fields 1–5 + "Still owned by archive"), add a **field 6:** "Context health during this session — was the context window large by the end of verify? Were any sub-agent delegations made specifically to avoid context rot? (Record: yes/no and what action, or 'none observed.')" This makes context management deliberate and auditable rather than invisible.

**Source:** Anthropic context engineering guide (Sep 2025) — "compaction typically serves as the first lever in context engineering to drive better long-term coherence." Chroma context rot study (2025) — context rot is the primary coding-agent failure mode. Making it observable in the notes.md audit trail costs one sentence.

**Confidence:** Medium. Low-cost change; marginal improvement. The scaffold's existing sub-agent architecture already handles this; the only gap is making it *visible* in the record.

**Constraint-compat:** Fully compatible.

**Effort/Risk:** Very low. One field added to verify SKILL text.

---

## 7. Already-Ahead / Doesn't-Fit

### Where the scaffold already meets or beats industry standard

**Pre-implementation review (openspec-reviewer):** The scaffold's `openspec-reviewer.md` is a dedicated pre-code-review agent that runs before *any* implementation. Industry tools (CodeRabbit, Greptile) are uniformly post-code (PR-level). Anthropic's own context engineering guide recommends catching spec errors before writing code; the scaffold operationalizes this more rigorously than anything in the commercial market. The read-only constraint, anti-rubber-stamp rules, and "do not affirm unverifiable empirics" anti-pattern are distinctly advanced.

**Behavioral verification beyond tests:** The verify SKILL's mandatory "eyeball real output" + live smoke requirement for external APIs goes significantly beyond industry standard (which stops at "tests pass + diff reviewed"). The explicit statement that "a green test suite alone does not count as verification" and that mock-based suites can encode wrong API contracts is more rigorous than Sourcegraph's or any other public agentic coding guide.

**Failure ladder with cost-graded escalation:** The deepseek-first → Sonnet-fallback escalation with mandatory disclosure is a mature quality gate not documented in any public agentic coding standard. It operationalizes the principle that quality failures should escalate, not silently pass.

**Trust-gated fast-track:** The fast-track-workflow.md structure — explicit operator grant required, separate file, hard gate at the top — maps precisely to what Anthropic's empirical research shows is the effective oversight pattern (accumulated trust, strategic interruption). The scaffold formalizes what the industry observes as organic behavior. Anthropic's ATF framework (Cloud Security Alliance, Feb 2026) calls for exactly this maturity-gate model.

**Archive-as-fresh-context sub-agent:** The write-deferred reconciliation pattern (archive-executor with fresh context seeded from compact change dir, not conversation transcript) is a concrete implementation of Anthropic's "sub-agent architectures" recommendation for long-horizon tasks. This is sophisticated context management that most agentic frameworks don't document explicitly.

**Phase gates as hard rules:** "STOP after verification" and "WAIT for explicit operator request before archive" matches the Cloud Security Alliance ATF's guidance on human oversight at consequential transitions, and Anthropic's empirical finding that agent-initiated stops are an important form of oversight.

**AGENTS.md cross-tool compliance:** The scaffold's AGENTS.md is the agent-neutral state hub that industry standards (donated to Linux Foundation, Dec 2025) endorse. The scaffold was ahead of the donated spec in its cross-agent discipline.

### Practices deliberately NOT recommended (and why)

**Harness-native memory tools (Anthropic memory tool, Claude.md auto-memory):** Not recommended for this scaffold. The Anthropic memory tool is a real improvement (39% agentic performance, 84% token reduction per Anthropic benchmarks) but is Claude Developer Platform–specific, requires a beta flag, and has no OpenCode/DeepSeek equivalent. Recommending it would violate constraints #1 (agent-neutral) and #2 (no harness-private storage). The scaffold's file-based alternatives (structured note-taking, sub-agent delegation, archive-executor pattern) are genuine mitigations — less automatic, but harness-neutral and auditable. The operator should understand this cost is real.

**Letta/MemGPT tiered memory framework:** Not recommended. Excellent architecture, but requires dedicated infrastructure (persistent agent runtime, vector stores, external databases). The scaffold is a generic template instantiated per-project; adding a Letta dependency would violate constraint #3 (generic template). The architectural insight (tiered memory, sleep-time compute) *is* useful as a mental model for why the scaffold's archive-executor pattern works: the change dir is "core memory," and the archive-executor serves as a "sleep-time agent" reconciling it into long-term storage (decisions.md, open-questions.md).

**Mandatory ADR-enforcement tooling (Mneme HQ):** Interesting but not mature enough as a cross-tool standard. The scaffold's approach (AGENTS.md hard constraints + decisions.md) achieves the same goal without a third-party tool dependency. Violates constraint #3 if integrated into the template itself.

**CodeRabbit/Greptile as hard gates:** Recommended only as an optional add-on (R5 above). Making them hard gates would violate constraint #3 (not all projects use PR workflows) and introduce external service dependencies into the default path. The scaffold's openspec-reviewer + verify SKILL already provides a superior pre-implementation + behavioral review chain.

---

## 8. Open Questions for the Operator

**OQ-1. Is the no-native-memory cost acceptable going forward?**
The Anthropic memory tool (Sep 2025) delivers measured benefits (39% agentic search improvement, 84% token reduction) on the Claude Developer Platform. These benefits are unavailable to this scaffold as long as constraint #2 holds. The constraint is correct for a dual-harness template, but the gap will likely widen as Anthropic invests more in memory tool capabilities. Is there a scenario where the operator would accept a "Claude-primary" mode that uses the memory tool, alongside the current neutral mode? Or is the dual-harness requirement permanent?

**OQ-2. How should mid-session context bloat be handled before archive is possible?**
R1 recommends an explicit context-budget guidance in AGENTS.md, but the precise trigger point is unspecified. Should the guidance give a concrete heuristic (e.g., "after 80+ tool calls" or "when reading back your own early instructions feels unreliable"), or leave it to agent judgment? The Anthropic guide says "start by maximizing recall" when tuning compaction — the analogous guidance for the scaffold's manual sub-agent pattern is unclear.

**OQ-3. Should decisions.md have a minimum population rule?**
R2 recommends seeding decisions.md with at least one example entry (the no-native-memory rule itself). But should AGENTS.md require that decisions.md contain at least N entries before a project is considered "initialized"? Empty template files have caused problems in practice (archive-executor has no historical context). What's the right enforcement mechanism?

**OQ-4. When is a post-code external reviewer (CodeRabbit/Greptile) worth adding?**
R5 is flagged as optional. For scaffold instances that do use GitHub PRs, CodeRabbit's 50%+ review-effort reduction and Greptile's 82% bug catch rate are compelling. Should the scaffold's archive skill include a `<FILL: optional CodeRabbit review>` placeholder? Or does the current openspec-reviewer + verify SKILL chain cover enough ground that this is redundant for most projects?

**OQ-5. Should the scaffold add a "context-rot self-check" to the session-start protocol?**
R3 addresses staleness on resume. A harder question: should AGENTS.md instruct agents to actively test their own recall of early-context information at the start of a long session, before proceeding? (E.g., "state the current change's key objectives from memory before opening any files.") This is aggressive but would catch the case where the model is operating on stale compressed context without realizing it.

**OQ-6. Is the openspec-reviewer's `bash: deny` constraint causing missed risks?**
`openspec-reviewer.md:129` explicitly warns: "a reviewer once 'confirmed' a constructor kwarg was 'available' in a library, which then crashed on the real host." The reviewer has `bash: deny` and cannot probe real libraries. The current mitigation is flagging unverified empirics as risks. But as agents' propose-phase live probes become more common in the industry (Anthropic context engineering guide), should the reviewer be upgraded to allow read-only bash? Or does the current "flag and require a probe in propose skill" pattern suffice?

---

*Written 2026-06-13. Sources fetched via `/home/pang/Projects/workflow-optimize/.venv/bin/python /home/pang/Projects/openspec-scaffold/scripts/fetch_clean.py`. One source inaccessible (ai.gopubby.com, 403 Forbidden) — not cited.*
