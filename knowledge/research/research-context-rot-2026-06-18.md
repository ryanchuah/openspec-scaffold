# Research: "Context Onboarding via Deterministic Bootstrapping" — Claim Verification

*Researched 2026-06-18. All sources fetched via scripts/fetch_clean.py and WebFetch.*

---

## Claim 1: "Context rot" is a recognized, named phenomenon

**Verdict: VERIFIED — but it's a very recent coinage (June 2025), not a long-established term.**

The term was coined by a Hacker News user "Workaccount2" on June 18, 2025, in a thread about AI coding agents:

> "They poison their own context. Maybe you can call it **context rot**, where as context grows and especially if it grows with lots of distractions and dead ends, the output quality falls off rapidly."

Source: https://news.ycombinator.com/item?id=44308711#44310054

Simon Willison picked it up the same day:  
https://simonwillison.net/2025/Jun/18/context-rot/

Drew Breunig formalized it further (June 29, 2025) into four named failure modes — Context Poisoning, Context Distraction, Context Confusion, and Context Clash — with corresponding mitigations:

> "context is not free. Every token in the context influences the model's behavior, for better or worse."

Source: https://simonwillison.net/2025/Jun/29/how-to-fix-your-context/ (Drew Breunig, cited by Willison)

**The "lost in the middle" paper is real and predates the term by two years.** Liu et al. (2023) showed that:

> "performance is often highest when relevant information occurs at the beginning or end of the input context" and degrades when models must retrieve information from the middle of long contexts.

Source: "Lost in the Middle: How Language Models Use Long Contexts", Liu et al., arXiv:2307.03172, July 2023  
URL: https://arxiv.org/abs/2307.03172  
Authors: Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, Percy Liang.

Anthropic's Claude Code best-practices docs echo the phenomenon without using the "context rot" label:

> "Most best practices are based on one constraint: Claude's context window fills up fast, and performance degrades as it fills... When the context window is getting full, Claude may start 'forgetting' earlier instructions or making more mistakes."

Source: https://code.claude.com/docs/en/best-practices

**Summary for Claim 1**: The underlying degradation effect is empirically established (Liu 2023). The label "context rot" is real but was coined on Hacker News in June 2025 — it is organic practitioner vocabulary, not an academic term. A proposal citing it as a long-recognized phenomenon overstates its pedigree; citing it as an emergent engineering concern with supporting empirical evidence is fair.

---

## Claim 2: Repomix — real? what does it do? codebase vs. state compilation?

**Verdict: VERIFIED (tool is real, award nomination is real), but a critical conflation lurks.**

Repomix is a real, actively maintained tool at https://github.com/yamadashy/repomix. Its stated purpose:

> "📦 Repomix is a powerful tool that packs your entire repository into a single, AI-friendly file. It is perfect for when you need to feed your codebase to Large Language Models (LLMs)."

The JSNation nomination is real. From the README:

> "We're honored! Repomix has been nominated for the **Powered by AI** category at the [JSNation Open Source Awards 2025](https://osawards.com/javascript/)."

Note: the proposal may say "Powered by AI" correctly, or may have misstated the category name — the README says "Powered by AI", not a general "open source" award.

**What Repomix actually does**: It compiles **source code files** into a bundle (with token counts, optional compression via Tree-sitter, gitignore-aware filtering). Features include:
- "AI-Optimized: Formats your codebase in a way that's easy for AI to understand and process."
- "Token Counting: Provides token counts for each file and the entire repository."
- Code compression: "uses Tree-sitter to extract key code elements, reducing token count while preserving structure."

**The conflation**: Repomix compiles **codebase files** (source code, directory structure). It is explicitly **not** a tool for compiling present-tense *project state* — i.e., it produces no information about current sprint status, open blockers, open questions, or task progress. If a proposal uses Repomix as evidence/inspiration for "state compilation" it is importing a codebase-packaging tool into a different problem domain. These are categorically different outputs.

---

## Claim 3: Code2Prompt — real? codebase vs. state compilation?

**Verdict: VERIFIED (tool is real), same conflation as Repomix.**

Code2Prompt is real at https://github.com/raphaelmansuy/code2prompt. From its README:

> "Code2Prompt is a powerful command-line tool that generates comprehensive prompts from codebases, designed to streamline interactions between developers and Large Language Models (LLMs) for code analysis, documentation, and improvement tasks."

Key features:
- "Holistic Codebase Representation: Generate a well-structured Markdown prompt that captures your entire project's essence"
- "Intelligent Source Tree Generation: Create a clear, hierarchical view of your codebase structure"
- "Gitignore Integration"
- Clipboard-ready, Jinja2 templates, token management

**What it does NOT do**: It packages source code into an LLM prompt. It produces no information about project runtime state — no open questions, blockers, task status, or dynamic workflow state. It is a static codebase snapshot tool, not a state compiler.

**The conflation**: Same as Repomix. If a proposal treats Code2Prompt as prior art for "compiling project state into a boot context," it is misclassifying a codebase-packaging tool as a state-compilation tool. These serve different purposes: one answers "what does this code do?", the other would answer "what is happening in this project right now?"

---

## Claim 4: "Progressive disclosure" for AGENTS.md — is "keep root rules ultra-lean and cacheable" a documented norm?

**Verdict: PARTLY TRUE — layered instruction files are real; "ultra-lean and cacheable" is practitioner inference, not documented spec.**

**AGENTS.md is real.** It originated with OpenAI Codex and Devin and is now cross-tool. Devin's docs describe it as:

> "a simple, open standard for providing context and instructions to AI agents — a README for agents."

Source: https://docs.devin.ai/onboard-devin/agents-md

OpenAI Codex documentation confirms the file and recommends hierarchical layering:
- Global defaults in `~/.codex/AGENTS.md`
- Repository-level expectations in root `AGENTS.md`
- Specialized rules in subdirectories via `AGENTS.override.md`
- Default size cap: 32 KiB per file, configurable via `project_doc_max_bytes`

Source: https://developers.openai.com/codex/guides/agents-md

Claude Code reads `CLAUDE.md`, not `AGENTS.md`, but explicitly acknowledges the convention:

> "Claude Code reads CLAUDE.md, not AGENTS.md. If your repository already uses AGENTS.md for other coding agents, create a CLAUDE.md that imports it so both tools read the same instructions."

Source: https://code.claude.com/docs/en/memory

**The "lean" guidance is documented.** Claude Code best practices say:

> "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence."

And the best practices page explicitly states:

> "For each line, ask: 'Would removing this cause Claude to make mistakes?' If not, cut it. Bloated CLAUDE.md files cause Claude to ignore your actual instructions!"

Source: https://code.claude.com/docs/en/best-practices

**What is NOT documented**: The specific phrase "ultra-lean and cacheable" is not in any AGENTS.md or CLAUDE.md specification. Prompt caching is not mentioned in any AGENTS.md documentation reviewed. "Progressive disclosure" as an explicit principle for agent instruction files is not named in any official spec — it is a reasonable inference from the layered/hierarchical approach, but framing it as an "actual documented norm" overstates the evidence.

---

## Claim 5: Google ADK "state machines over history" guidance

**Verdict: UNSUPPORTED — the specific claim is an overreach of what ADK actually says.**

Google ADK (Agent Development Kit) is real. The Python library is at https://github.com/google/adk-python and documentation is at https://adk.dev.

ADK 2.0 does offer a Workflow Runtime described as "a graph-based execution engine for composing deterministic execution flows for agentic apps." The docs do say:

> "Mixing deterministic and non-deterministic tasks: As you build agents for solving more complex problems, you may want to design and build agents that interweave the non-deterministic functionality of AI models with deterministic code, rather than relying on non-deterministic AI models to manage the full execution of a task."

Source: https://adk.dev/agents/

ADK does have session state management, described as key-value pairs organized in session/user/app scopes. The docs warn:

> "directly modifying the `session.state` collection...outside of the managed lifecycle...will likely NOT be saved and breaks persistence."

Source: https://adk.dev/sessions/state/

**What ADK does NOT say**: There is no guideline in the reviewed ADK documentation that says agents should be "grounded in clean deterministic state boundaries generated by code rather than reconstructing state from text files." That specific formulation — "state machines over history" as an explicit ADK principle — does not appear in ADK docs. The ADK does prefer deterministic task flows, but the specific claim that agents should avoid "reconstructing state from text files" is a creative paraphrase, not a documented ADK guideline.

**Honest assessment**: ADK supports deterministic workflows and session state, so the directional point (prefer code-managed state over free-form text history) is reasonable engineering guidance — but attributing it as explicit ADK doctrine is an overreach. The underlying principle appears in the O'Reilly "year of building with LLMs" piece in passing ("the likelihood that an agent completes a multi-step task successfully decreases exponentially") but not as a named ADK pattern.

---

## Claim 6: "Compile project state into ephemeral boot context file" — established named pattern?

**Verdict: UNSUPPORTED as a named/established pattern — this is novel or at minimum unnamed in published literature.**

Research found no named pattern called "context compiler," "session bootstrap," "deterministic bootstrapping," or similar in:
- Framework docs: ADK, LangChain, CrewAI, OpenAI Agents SDK, Aider
- Major practitioner blogs: Simon Willison, Lilian Weng, Jason Liu, Hamel, Anthropic Engineering
- The Anthropic SWE-bench agent description explicitly uses a *minimalist* approach: "give as much control as possible to the language model itself, and keep the scaffolding minimal" — the opposite of compiling state upfront.

The **closest prior art** found:
1. Repomix / Code2Prompt — compile *source code* into a context bundle (not project state).
2. Claude Code's CLAUDE.md — a *static*, manually maintained instruction file (not generated/ephemeral).
3. Hacker News "context rot" thread suggestion: "creating summaries of conversations periodically, then starting fresh contexts seeded with previous summaries" — this is the clearest conceptual ancestor, but it is an informal comment, not a named pattern.
4. Drew Breunig's "Context Offloading" mitigation — move information out of the working context — is the closest named concept, but it's about pruning rather than boot-time compilation.
5. Aider's approach: manually adding/dropping files per step — a runtime, user-driven approach, not compiled-state.

**Assessment**: The *idea* — generate a fresh, deterministic state snapshot and feed it to the agent at session start rather than letting context accumulate — is directionally supported by the context rot discourse and the general "prefer clean state over accumulated history" engineering principle. But it does not appear to be a formalized, named pattern with documented prior art. It is genuinely novel ad hoc engineering at this point. That is not a reason not to build it — it may be a good idea — but the proposal should not claim it as an established pattern.

---

## Bottom line

**Which claims are solid:**
- The "lost in the middle" paper (Liu et al. 2023, arXiv:2307.03172) is real and well-cited — the empirical basis for context performance degradation is solid.
- "Context rot" as a term is real but dates only to June 2025 (Hacker News origin, popularized by Simon Willison and Drew Breunig). Practitioners are actively talking about it; it is not yet academic vocabulary.
- Repomix (JSNation "Powered by AI" nomination) and Code2Prompt are both real, well-maintained tools.
- AGENTS.md is a real cross-tool convention (OpenAI Codex, Devin); the "keep instructions lean" norm is documented in Claude Code and implied by OpenAI's 32 KiB cap.

**Which claims are inflated or conflated:**
- Repomix and Code2Prompt compile **source code files**, not **project state** (status/blockers/open questions). A proposal treating them as prior art for "state compilation" is conflating two different problems. This is the most important technical distinction in the proposal.
- "Keep root rules ultra-lean and cacheable" — the "lean" part has support; "cacheable" has no documented backing in AGENTS.md specs.
- The ADK "state machines over history" claim is a creative paraphrase of ADK's actual state docs, not an explicit ADK guideline. Citing it as documented ADK doctrine is an overreach.
- "Compile project state into ephemeral boot context" is not a recognized named pattern anywhere in reviewed literature. It is novel engineering.

**Single most important caveat for someone deciding whether to build this script:**

The tooling analogies (Repomix, Code2Prompt) are doing different work than what is being proposed: they answer "what does the code look like?" while the proposal answers "what is the project's current state?" There is no established prior art for the latter. The proposal is solving a real problem (context rot in long agentic sessions), but the "this is like Repomix for project state" framing is a category error that could mislead stakeholders about the novelty and risk of the work. Build it, but call it what it is: new tooling, not a well-trodden pattern.
