# Research: Cross-Repository Agent Context Synchronization — Citation & Claims Verification

**Verified by:** skeptical research subagent  
**Date:** 2026-06-18  
**Source proposal:** `/home/pang/Projects/openspec-scaffold/tmp_prompt_agent_sync.md`

---

## Part A — Citations

### 1. Kondratyev (n.d.)
**Claimed:** "complex software spanning multiple interdependent repositories quickly exceeds the bounds of a single repository's localized context window."

**Verdict: NOT FOUND — likely fabricated**

No arXiv paper, no identifiable blog post, no traceable publication by anyone named Kondratyev makes this claim. An arXiv author search for "Kondratyev" returns papers in quantum physics, finance, and mathematics — nothing on AI agents or context windows. A broader web search finds Vladislav Kondratyev (vladislavkon.com), a junior developer building agent tools (PyPI packages: `gagent`, `gorchestrator`, `gmirror`) with no published work matching this claim. The sentiment itself (multi-repo scope exceeds single-repo context) is a widely-repeated community observation, not an authored claim with a citable source. The citation appears fabricated.

---

### 2. Gloaguen (n.d.)
**Claimed:** "recent empirical evaluations of AGENTS.md files reveal that over-stuffing repository-level context files with redundant, non-project-specific requirements reduces coding agents' task success rates and increases token costs."

**Verdict: REAL & BROADLY SUPPORTED — but framing is slightly misleading**

The paper exists: **arXiv:2602.11988**, "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?" by Thibaud Gloaguen, Niels Mündler, Mark Müller, Veselin Raychev, Martin Vechev (submitted February 12, 2026). Source: https://arxiv.org/abs/2602.11988

The actual finding: "context files **tend to reduce task success rates** compared to providing no repository context, while also **increasing inference cost by over 20%**." The recommendation is "human-written context files should describe only minimal requirements."

Misrepresentation: The proposal reframes this as a problem of "over-stuffing with redundant, non-project-specific requirements" — implying that lean, focused context files work fine. The actual paper found that even well-formed context files hurt performance; the effect isn't limited to over-stuffed files. The proposal uses this citation to justify "minimize per-repo AGENTS.md" which is directionally consistent with the paper's conclusion, but the causal mechanism is mischaracterized.

The "(n.d.)" date designation is also wrong — the paper has a clear submission date of Feb 2026.

---

### 3. Vasilopoulos (n.d.)
**Claimed:** "Codified Context Infrastructure"

**Verdict: REAL & RELEVANT**

The paper exists: **arXiv:2602.20478**, "Codified Context: Infrastructure for AI Agents in a Complex Codebase" by Aristidis Vasilopoulos (submitted February 24, 2026). Source: https://arxiv.org/abs/2602.20478

The paper proposes a three-component framework developed during a 108,000-line C# project: (1) a "hot-memory constitution encoding conventions, retrieval hooks, and orchestration protocols," (2) 19 specialized agent roles, and (3) a "cold-memory knowledge base of 34 on-demand specification documents." The phrase "Codified Context Infrastructure" appears in this context as a descriptive label for treating documentation as load-bearing infrastructure for AI agents.

The "(n.d.)" designation is wrong — the paper has a clear submission date. Otherwise the citation is legitimate.

---

### 4. Bi (n.d.)
**Claimed:** "automated context synchronization tools / scripting symlink managers to map and extract reusable context artifacts across repositories."

**Verdict: NOT FOUND — likely fabricated**

No arXiv paper, GitHub repository, blog post, or identifiable author named Bi can be found writing about symlink managers or automated context synchronization across repositories for AI agents. An arXiv author search on "Bi" returns numerous unrelated papers (physics, CV, robotics, NLP). A web search for this specific concept finds real tools (alexandrbasis/claude-agents-sync, sync-ai-coding-instructions) and GitHub projects, but none attributed to an author named Bi. The tooling concept itself is real, but the citation is fabricated.

---

### 5. Galster (n.d.)
**Claimed:** "Claude's @ imports to reference central global instruction sets from a localized CLAUDE.md/AGENTS.md is an emerging standard."

**Verdict: REAL BUT MISREPRESENTED**

Matthias Galster is a real and active researcher. The cited paper is almost certainly **arXiv:2602.14690**, "Configuring Agentic AI Coding Tools: An Exploratory Study" (Matthias Galster, Seyedmoein Mohsenimofidi, Jai Lal Lulla, Muhammad Auwal Abubakar, Christoph Treude, Sebastian Baltes; submitted Feb 2026). Source: https://arxiv.org/abs/2602.14690

The paper's actual finding: "Context Files dominate the configuration landscape and are often the sole mechanism in a repository, with **AGENTS.md emerging as an interoperable standard across tools**."

The misrepresentation: The proposal attributes to Galster the claim that Claude's @imports are "an emerging standard for tool configuration." The paper says no such thing. It says AGENTS.md (the plain Markdown file format) is becoming an interoperable standard. Claude's @import mechanism is a Claude Code-specific feature covered in the paper's taxonomy but never called an "emerging standard." Galster's work actually leans toward AGENTS.md portability across tools — which cuts against the @import pattern (since @imports are Claude Code-specific).

The "(n.d.)" date is also wrong.

---

## Part B — Technical Claims

### 6. Claude Code `@path` imports in CLAUDE.md
**Verdict: VERIFIED — including absolute paths and home-dir imports**

Fully confirmed from official Claude Code docs at https://code.claude.com/docs/en/memory (current authoritative source; docs.anthropic.com/en/docs/claude-code/memory redirects here).

Key facts extracted directly from the docs:

- **Syntax:** `@path/to/file` anywhere in a CLAUDE.md file (e.g., `@README`, `@~/.claude/my-project-instructions.md`, `@docs/git-instructions.md`)
- **Paths:** Both relative (resolved relative to the importing file, not cwd) and absolute are allowed
- **Home directory:** Explicitly supported — `@~/.claude/...` works
- **Cross-repo:** Absolute paths work, so an import like `@/home/user/shared-repo/SHARED_RULES.md` is technically valid. No documented restriction to "current repo" but also no native "cross-repo" concept
- **Depth limit:** Maximum 4 hops of recursive imports
- **Loading:** Imported files are expanded and loaded into context at launch alongside the importing CLAUDE.md — they are NOT lazy-loaded
- **AGENTS.md import:** Docs explicitly document the pattern of importing AGENTS.md into CLAUDE.md: `@AGENTS.md` at the top of CLAUDE.md, with Claude-specific additions below
- **Approval gate:** First encounter of external imports shows an approval dialog; declining disables them permanently
- **Symlinks:** `.claude/rules/` directory supports symlinks for sharing rule sets across projects

One important caveat from the docs on size: "Splitting into [@path imports] helps organization but does not reduce context, since imported files load at launch."

---

### 7. AGENTS.md `@import` / include directives — cross-harness support
**Verdict: FALSE for AGENTS.md; Claude-Code-specific only; OpenCode has no equivalent**

The AGENTS.md format (as documented at agents.md) is "just standard Markdown" — no import, include, or @path directives are part of the AGENTS.md specification. Scoping in AGENTS.md is directory-based only: "agents automatically read the nearest file in the directory tree, so the closest one takes precedence." There is no file inclusion mechanism in the AGENTS.md standard itself.

**OpenCode specifically:** OpenCode does support AGENTS.md (it creates one on `/init` and reads it for project context). However, OpenCode has NO @import mechanism for AGENTS.md. Its config uses JSON (`opencode.json`) and markdown agent definitions in `~/.config/opencode/agents/` or `.opencode/agents/`. The only external file reference syntax in OpenCode is `{file:./path}` within agent prompt strings in JSON config — this is for prompt content only, not full config file import.

**Cross-harness reality for the user's dual-harness setup (Claude Code + OpenCode):**
- Claude Code: `@AGENTS.md` in CLAUDE.md works — Claude Code reads the AGENTS.md content via import
- OpenCode: reads AGENTS.md directly (no @import needed or supported)
- Shared edits to AGENTS.md propagate to both harnesses, but only Claude Code can augment this with @imports for Claude-specific overrides
- There is no symmetric import mechanism; the two harnesses do not share an import protocol

---

### 8. Workspace / "repo-of-repos" pattern
**Verdict: PARTLY TRUE — community practice, not a formally standardized pattern**

The pattern is real in community discussions. Web searches surface blog posts and GitHub repos describing a "workspace" or "repo-of-repos" approach for shared AI agent instructions. The core idea (clone multiple repos under a parent directory and use a root-level AGENTS.md or monorepo config) is discussed as a community pattern.

However, there is no formally documented standard or widely-adopted tooling for this. It's an emerging community practice, not a recognized architecture pattern with canonical documentation. Claude Code's `--add-dir` flag (with `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`) provides official support for loading CLAUDE.md from additional directories outside the main working directory — this is the closest official support for a "workspace" approach. OpenCode has no equivalent.

---

### 9. Dedicated sync tooling / symlink managers for agent config across repos
**Verdict: PARTLY TRUE — real tools exist but Bi's attribution is fabricated**

Real tools found during research:

- **alexandrbasis/claude-agents-sync** (Oct 2025): Syncs CLAUDE.md ↔ AGENTS.md within a single project using Claude Code hooks. Does NOT use symlinks; does NOT work across repos. Scope: single project.
- **sync-ai-coding-instructions** (PyPI, Nov 2025): Purpose unclear from available data (page failed to load), but name suggests cross-tool instruction sync.
- **Claude Code built-in symlink support**: `.claude/rules/` directory supports symlinks natively. The docs explicitly show: `ln -s ~/shared-claude-rules .claude/rules/shared` — this IS a symlink-based sharing mechanism, documented in official Claude Code docs.
- **AGENTS.md ↔ CLAUDE.md symlink**: Claude Code docs explicitly document `ln -s AGENTS.md CLAUDE.md` as an alternative to @import when no Claude-specific additions are needed.
- **GNU Stow and dotfile managers**: General-purpose symlink managers commonly used for config file distribution, adaptable to agent config sharing but not purpose-built for it.

The concept of "scripting symlink managers to map and extract reusable context artifacts across repositories" is a real approach (and Claude Code explicitly documents symlink support). But there is no identifiable author "Bi" behind this idea, and no single canonical tool dominates this space.

---

## Bottom line

- **Citations 1 (Kondratyev) and 4 (Bi) are almost certainly fabricated.** No author by those names has identifiable published work matching the attributed claims. Both claims are paraphrases of commonly-discussed ideas that don't need a citation.

- **Citations 2 (Gloaguen) and 3 (Vasilopoulos) are real arXiv papers** (arXiv:2602.11988 and arXiv:2602.20478 respectively, both Feb 2026), but both are cited with "(n.d.)" which is wrong. Gloaguen's claim is directionally right but the proposal softens the actual finding — the paper found context files hurt performance even when well-crafted, not just when "over-stuffed."

- **Citation 5 (Galster) names a real researcher but misrepresents his work.** Galster's paper says AGENTS.md (the file format) is becoming an interoperable standard across tools. The proposal attributes to him that Claude @imports are an emerging standard — that's a fabrication layered on a real citation.

- **Claude Code @imports are real and work with absolute paths including `~/`**, making cross-repo import technically feasible via absolute path. However, imported files load into context at launch, so pulling in a large shared config from another repo still costs tokens. The depth limit is 4 hops.

- **@imports do NOT work cross-harness.** AGENTS.md has no import spec; OpenCode has no @import mechanism. The `@path` pattern is Claude Code-only. A shared AGENTS.md file is the only cross-harness portable artifact, and both tools read it natively but differently (Claude Code reads it via import or symlink from CLAUDE.md; OpenCode reads it directly). Any architecture relying on `@imports` for cross-harness sync will not work in OpenCode.
