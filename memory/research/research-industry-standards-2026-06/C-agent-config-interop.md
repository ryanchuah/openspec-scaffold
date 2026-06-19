# C — Agent Configuration & Interoperability Standards (mid-2026)

> Research bucket C of the `openspec-scaffold` industry-standards comparison.
> Covers: how agent behaviour, tools, and capabilities are *declared and made portable across tools*.
> NOT in scope: spec lifecycle content (A), orchestration/delegation mechanics (B), memory & verification-quality (D).

---

## 1. Scope

This bucket analyses the mechanisms by which AI coding agents declare and share their
configuration, capabilities, and workflow rules across tools. Specifically:

- **AGENTS.md** as the emerging cross-tool instruction standard
- **SKILL.md / Agent Skills** as the emerging cross-tool capability unit
- **MCP (Model Context Protocol)** as the standard for exposing tools and context to agents
- **Claude-specific config surfaces** (hooks, slash commands, `settings.json`) and their portability
- **OpenCode agent/config system** (`.opencode/agents/`, `opencode.json`)
- **Cursor `.cursorrules` / Cline** — tool-specific alternatives and their coverage
- The cost of the `.claude/` vs `.opencode/` duplication in the scaffold

Central question per constraint #1 (agent-neutral): which standards are genuinely cross-tool vs Claude-only, and what should a *neutral* template adopt?

---

## 2. Sources Consulted

| URL | What it is | Date / Recency |
|---|---|---|
| https://agents.md | AGENTS.md official site — spec, adoption list, FAQ | Fetched 2026-06-13; site live |
| https://github.com/openai/agents.md | AGENTS.md GitHub repo — README, minimal spec | Fetched 2026-06-13; stewarded by Agentic AI Foundation/Linux Foundation |
| https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview | Claude API Agent Skills docs — full SKILL.md spec, progressive disclosure | Fetched 2026-06-13 |
| https://www.agensi.io/learn/agent-skills-open-standard | SKILL.md as open standard — cross-tool adoption detail | Fetched 2026-06-13; published 2026-04-13 |
| https://opencode.ai/docs/agents/ | OpenCode agents config — types, markdown format, permission fields | Fetched 2026-06-13 |
| https://www.morphllm.com/claude-code-hooks | Claude Code hooks — all 30 events, JSON shapes, settings.json | Fetched 2026-06-13 |
| https://mcp.directory/blog/cross-agent-skills-cursor-codex-cline-antigravity-gemini-mastra-portability | Cross-agent skills portability — all 8 major agents, discovery paths, OpenCode `.opencode/skills/` | Fetched 2026-06-13 |
| https://www.deployhq.com/blog/ai-coding-config-files-guide | CLAUDE.md / AGENTS.md / Copilot Instructions comparison — Claude Code reads AGENTS.md as fallback when no CLAUDE.md exists | Fetched 2026-06-13 |
| WebSearch: "AGENTS.md standard adoption 2026" | Broad adoption picture — 60k repos, Linux Foundation | 2026-06-13 |
| WebSearch: "Model Context Protocol MCP adoption coding agents 2026" | MCP adoption metrics — 10k servers, near-universal | 2026-06-13 |
| WebSearch: "Claude Code agent skills SKILL.md portable standard 2026" | SKILL.md portability details | 2026-06-13 |
| WebSearch: "Claude Code hooks settings.json configuration 2026" | Hooks detail, 21-30 event count, HTTP type | 2026-06-13 |
| WebSearch: "OpenCode agent configuration skills 2026" | OpenCode skill support discovery | 2026-06-13 |
| WebSearch: "Cursor rules Cline cross-tool portability 2026" | Cross-tool comparison | 2026-06-13 |

**Not accessible / not fetched:**
- agentskills.io/specification — the formal published spec (referenced in mcp.directory article as the canonical source; the mcp.directory article quotes the spec verbatim so coverage is sufficient, but the primary URL was not fetched directly)
- modelcontextprotocol.io/specification — (not fetched; MCP coverage from WebSearch summaries is sufficient for this analysis; noted as open question)

---

## 3. Industry Standard (mid-2026)

### 3a. AGENTS.md — cross-tool project-instruction file

AGENTS.md has become the **de facto cross-tool standard** for project-level agent instructions. It is:
- Stewarded by the Agentic AI Foundation under the Linux Foundation (formalised in 2025–26).
- Adopted by 60,000+ open-source repositories.
- Natively read by: Claude Code, OpenAI Codex CLI, Cursor, GitHub Copilot (added Aug 2025), Google Jules/Gemini CLI, Windsurf, Aider, Factory, Amp, Zed AI, Roo Code, Cline, and 20+ others.
- No required schema beyond free-form Markdown with conventional section headings (Dev environment, Testing, Code style, PR instructions). No frontmatter required.
- Supports nested per-directory AGENTS.md for monorepos.
- The agent-neutral complement to README.md: carries agent-focused build/test/style rules that would clutter READMEs.

**Claude Code and AGENTS.md:** Claude Code reads `AGENTS.md` as a fallback when no `CLAUDE.md` exists in a directory (deployhq.com, fetched 2026-06-13). A project can ship `AGENTS.md` only and both Claude Code and all other tools read it — this is the correct neutral-template pattern.

**AGENTS.md vs Skills trade-off:** The mcp.directory article (2026-06-13) cites a Vercel eval: "100% pass rate with an 8KB AGENTS.md doc index versus 79% for Skills with explicit instructions and 53% for Skills with default invocation." Skills require the agent to decide whether to invoke them; AGENTS.md content is always in context. For high-priority procedural rules (phase gates, delegation protocols), AGENTS.md is more reliable; for domain-specific expertise packages, skills are better. The scaffold uses both: AGENTS.md for cross-cutting rules, skills for phase procedures. This split is validated by current best practice.

**Tool-specific alternatives:** `.cursorrules` (Cursor-only), `.clinerules` (Cline-only), `.windsurfrules` (Windsurf-only) exist but are tool-locked. The consensus is to write AGENTS.md and use tool-specific files only for Cursor/Cline-only advanced features. When both exist, Cursor prefers its own `.cursorrules`. Codex CLI also supports `AGENTS.override.md` as a gitignored personal-override file alongside the committed `AGENTS.md`.

### 3b. SKILL.md / Agent Skills — cross-tool capability units

**Agent Skills** was formalised as an open standard on 2025-12-18 (Anthropic origin; now cross-industry).

Supported tools as of mid-2026: Claude Code, OpenAI Codex CLI, Gemini CLI, GitHub Copilot (VS Code agent mode), Cursor (manual placement), Cline, Windsurf, OpenCode. The canonical discovery path is `.claude/skills/<name>/SKILL.md` (Claude) or the equivalent per-tool location.

**Skill format — three levels of content (progressive disclosure):**
- Level 1: YAML frontmatter (`name`, `description`) — loaded at startup into system prompt, ~100 tokens per skill.
- Level 2: SKILL.md body (markdown instructions) — loaded on-demand when triggered, <5k tokens.
- Level 3: Bundled scripts, reference docs, templates — accessed via bash only when referenced; no context cost until read.

**Core portability:** the `name + description + markdown body` format is universally portable. The formal spec (agentskills.io/specification, quoted in mcp.directory cross-agent article) defines:
- Required fields: `name` (max 64 chars, lowercase-kebab, must match parent directory name) and `description` (max 1024 chars).
- Optional fields: `license`, `compatibility` (max 500 chars), `metadata` (arbitrary key-value), and `allowed-tools` (explicitly marked *Experimental*; support varies).
- Tool-specific extensions (Claude Code's `context: fork`, Codex's `openai.yaml`) don't port cleanly but are optional; skills using only the core format are cross-tool.

**Discovery paths per tool (from mcp.directory cross-agent portability article, 2026-06-13):**
- **Claude Code:** `.claude/skills/<name>/` (project), `~/.claude/skills/<name>/` (global) — canonical reference implementation.
- **OpenCode:** `.opencode/skills/<name>/` (project), `~/.config/opencode/skills/<name>/` (global). The Vercel installer's `opencode` target explicitly points to `.opencode/skills/`. There is NO documented auto-discovery of `.claude/skills/` by OpenCode — unlike Cline (which scans `.claude/skills/` as a compat path) and Cursor (which also scans `.claude/skills/` as a legacy compat path).
- **Codex CLI:** `.agents/skills/` (project) or `$HOME/.agents/skills/` (global), also 4-tier system.
- **Cursor:** `.cursor/skills/`, `.agents/skills/`, `.claude/skills/` (legacy compat), `~/.cursor/skills/`.
- **Cline:** `.cline/skills/`, `.clinerules/skills/`, `.claude/skills/` (compat path). Deliberately reads `.claude/skills/`.
- **Gemini CLI:** `.gemini/skills/` or `.agents/skills/` (workspace); `~/.gemini/skills/`.
- **Google Antigravity:** `.agent/skills/<name>/` (singular `.agent`; differs from plural `.agents/` used by Codex/Cursor/Gemini).

**Key portability risk for the scaffold:** Claude Code and OpenCode use *different* canonical skill paths (`.claude/skills/` vs `.opencode/skills/`). The scaffold only ships `.claude/skills/`. Whether OpenCode auto-discovers `.claude/skills/` is NOT confirmed by OpenCode's own docs — the mcp.directory article says OpenCode uses `.opencode/skills/` and uses the Vercel installer for other-path skills. This is a material gap.

**Discovery in Claude Code:** Claude discovers skills automatically via the filesystem; no manifest needed. Skills can be invoked by slash command or auto-triggered by description match.

### 3c. Model Context Protocol (MCP) — tool/context server standard

MCP is now "the USB-C for AI" — the dominant standard for connecting agents to external tools and context sources.

As of mid-2026:
- Anthropic, OpenAI, Google, Microsoft all have native MCP support.
- LangChain, CrewAI, LangGraph, LlamaIndex have adopted MCP as their default tool protocol.
- 10,000+ public MCP servers registered; 97M+ monthly SDK downloads (Anthropic, Dec 2025).
- Dominant clients: Claude Code, Cursor, Cline, Windsurf, VS Code native agent mode.
- MCP enables agents to connect to filesystem, Git, databases, APIs, and custom services via a single protocol.

**Relevance to a neutral template:** MCP server references live in harness configuration (`settings.json` for Claude, `opencode.json` for OpenCode), not in tracked project files. For a generic template the question is whether to ship an example `mcp_servers` stanza (as a commented template) in the config files. MCP config itself is harness-native and does not belong in `AGENTS.md`.

### 3d. Claude Code config surfaces: hooks, settings.json, slash commands

**Hooks (Claude Code):**
- 30 lifecycle events (expanded from 14 in early 2025 to 21 in March 2026, to 30 by mid-2026).
- Four handler types: `command`, `prompt`, `agent`, `http`.
- Key blockable events: `PreToolUse`, `PostToolBatch`, `UserPromptSubmit`, `Stop`, `SubagentStop`.
- Registered in `settings.json` under `hooks.*`; shell commands read JSON from stdin, signal via exit code + stdout JSON.
- Typical uses: auto-format after edits, block dangerous commands, enforce policies, run tests after write.
- **Claude-only.** OpenCode has no equivalent hook system; its equivalent is agent `permission` fields (allow/ask/deny per tool type) plus model-level configuration.

**settings.json (Claude Code):**
- Carries permissions, MCP server references, hook registrations, model preferences.
- Lives at project level (`.claude/settings.json`) or user level (`~/.claude/settings.json`).
- **Claude-only.**

**Slash commands (Claude Code):**
- Stored in `.claude/commands/` as markdown files; invoked with `/command-name`.
- Skills have largely replaced slash commands for reusable workflows (skills have frontmatter and progressive disclosure; slash commands are simpler).
- **Claude-only** (though the SKILL.md standard has made skills the cross-tool unit instead).

### 3e. OpenCode agent config

OpenCode agents are defined via:
- **Markdown files** at `.opencode/agents/<name>.md` (project) or `~/.config/opencode/agents/<name>.md` (global).
- **JSON stanzas** in `opencode.json` / `opencode.jsonc`.
- Frontmatter fields: `name`, `description`, `mode` (primary/subagent), `model`, `temperature`, `max_steps`, `disable`, `prompt` (path to system-prompt file), `permission` (per-tool allow/ask/deny).
- Permission keys: `read`, `edit`, `glob`, `grep`, `list`, `bash`, `task`, `external_directory`, `todowrite`, `webfetch`, `websearch`, `lsp`, `skill`.
- Subagents are `@mention`-invokable; primary agents cycle with Tab.
- Built-ins: Build (all tools), Plan (restricted), General, Explore, Scout (read-only), plus system agents (Compaction, Title, Summary).

**OpenCode has no native hook system** analogous to Claude's 30-event lifecycle hooks. Its policy enforcement is through the permission matrix at agent-definition time, not runtime hooks.

---

## 4. Scaffold Baseline

| Item | Location | Line(s) | What it does |
|---|---|---|---|
| AGENTS.md project instructions hub | `AGENTS.md:1–180` | Entire file | Cross-agent neutral instructions; role definitions; workflow lifecycle; state rules; working process; web-research convention |
| Cross-agent compatibility section | `AGENTS.md:24–34` | Explicitly bars harness-native storage; bars `.claude/`, `CLAUDE.md`, memory files | Agent-neutral principle encoded |
| Roles section | `AGENTS.md:53–68` | Defines apply-executor as role fillable by either agent family | Dual-harness aware |
| `.claude/agents/apply-executor.md` | `.claude/agents/apply-executor.md:1–30` | Sonnet fallback; tool list in frontmatter (`Read, Edit, Write, Bash, Glob, Grep`); FALLBACK label | Claude-specific subagent definition |
| `.opencode/agents/apply-executor.md` | `.opencode/agents/apply-executor.md:1–36` | OpenCode format: `mode: all`, `model: deepseek/deepseek-v4-flash`, `permission` block (task: deny) | OpenCode agent definition — parallel |
| `.opencode/agents/openspec-reviewer.md` | `.opencode/agents/openspec-reviewer.md:1–130` | OpenCode reviewer; `model: deepseek/deepseek-v4-pro`; `permission: read:allow, edit:deny, bash:deny` | OpenCode agent definition — no Claude counterpart |
| `.claude/skills/openspec-*/SKILL.md` | 7 skill files | YAML frontmatter (`name`, `description`, `license`, `compatibility`, `metadata`); markdown body | Claude Skills using standard SKILL.md format |
| `.opencode/agents/archive-executor.md` | `.opencode/agents/archive-executor.md` | OpenCode archive executor | OpenCode agent — no `.claude/skills/` counterpart for the OpenCode path |
| ABSENT: settings.json | Nowhere in scaffold | — | No Claude `settings.json` (permissions, hooks, MCP) shipped |
| ABSENT: hooks config | Nowhere in scaffold | — | No hooks registered anywhere |
| ABSENT: MCP config | Nowhere in scaffold | — | No MCP server stanzas |
| ABSENT: .claude/commands/ | Nowhere in scaffold | — | No slash commands directory |
| ABSENT: .opencode/skills/ | Nowhere in scaffold | — | OpenCode skills dir not present (skills are Claude-side only) |

**Key structural asymmetry observed:**
- `.claude/` has BOTH agents (2) AND skills (7). `.opencode/` has agents only (3). There is no `.opencode/skills/` directory.
- The `openspec-reviewer` agent exists only in `.opencode/`; under Claude it is invoked via `opencode run` (same OpenCode process), so no `.claude/agents/openspec-reviewer.md` is needed. This is intentional and correct.
- The Claude skill files carry the OpenSpec workflow logic for BOTH harnesses (branched internally by "If you are Claude Code" / "If you are OpenCode" sections — see `SKILL.md:83–206`). So skills are the primary workflow carriers for the Claude path; OpenCode reads them too via the Agent Skills open standard (confirmed: OpenCode reads Claude-compatible skill locations).

---

## 5. Gap Table

| Practice | Status | Evidence | Assessment |
|---|---|---|---|
| AGENTS.md as cross-tool project instruction file | **Present — Ahead** | `AGENTS.md:1–180` is a rich, structured agent instruction hub far beyond the minimal AGENTS.md convention. Adopted by 60k repos. | Scaffold is ahead of the minimal standard; AGENTS.md is the right vehicle. No gap. |
| SKILL.md core format (`name` + `description` + markdown body) | **Present** | All 7 skills use YAML frontmatter with `name`, `description`, `license`, `compatibility`, `metadata`. Core format is cross-tool. | Standard: name + description required. Scaffold adds optional fields (`license`, `compatibility`, `metadata`). All additive — compatible. |
| OpenCode skill mirror (`.opencode/skills/`) | **Absent — Likely Gap** | `.opencode/` has no `skills/` directory. The mcp.directory cross-agent portability article (fetched 2026-06-13) confirms OpenCode's canonical path is `.opencode/skills/`; the Vercel installer uses that path. OpenCode does NOT document reading `.claude/skills/` as a compat path (unlike Cursor and Cline which do). | Real gap: if OpenCode does not auto-discover `.claude/skills/`, the 7 workflow skills are invisible to the OpenCode primary agent. Needs live verification (see OQ1). If confirmed absent, the fix is either symlinks or a `.opencode/skills/` mirror. |
| MCP config (server references in harness config) | **Absent** | No `settings.json`, no `opencode.json` MCP stanza | MCP is the dominant tool-connection standard (10k servers, near-universal). Template ships no MCP config — arguably correct for a generic template since MCP is project-specific; could ship a commented example. |
| Claude Code hooks (lifecycle automation) | **Absent** | No `settings.json` with hooks stanzas, no `.claude/settings.json` | Hooks are Claude-only (30 events). No OpenCode equivalent. The scaffold's explicit constraint #1 (agent-neutral) makes shipping hooks in the default template a bad fit — they'd work only under Claude. |
| Claude Code `settings.json` (permissions, MCP, hooks) | **Absent** | No `.claude/settings.json` present | Template-appropriate absence: permissions and hooks are per-operator and per-project; committing a settings.json with wrong permissions could cause security issues. Open question: should a commented template settings.json be provided? |
| Claude Code slash commands (`.claude/commands/`) | **Absent** | No `.claude/commands/` directory | SKILL.md has largely superseded slash commands for reusable workflows. Skills provide the same invocation pattern plus progressive disclosure and cross-tool portability. Not a gap. |
| Dual-agent format divergence | **Present — Divergent** | `.claude/agents/` uses Claude frontmatter (`tools:`, `model:`, no `permission:`); `.opencode/agents/` uses OpenCode frontmatter (`mode:`, `permission:`, `model:`). Core content is the same but fields differ. | Expected and necessary: each harness requires its own frontmatter schema. Content parity is what matters. Spot-check: both apply-executor files have same rules, same mock-API warning, same no-commit rule — well-maintained. |
| AGENTS.md section describing skill invocation | **Partial** | `AGENTS.md:83` references `.claude/skills/openspec-*/SKILL.md` but does not mention OpenCode skills path | Minor: should clarify which skills path OpenCode uses, especially given the gap identified above. |
| No CLAUDE.md at project root | **Present — Deliberate** | Scaffold ships AGENTS.md at root, no CLAUDE.md. deployhq.com guide (fetched 2026-06-13) confirms: "Claude Code also reads AGENTS.md as a fallback if no CLAUDE.md is found." So the scaffold's AGENTS.md IS read by Claude Code. | Correct approach for a neutral template: one file serves both Claude Code and OpenCode. No gap. Constraint #1 satisfied. |
| Explicit OpenCode global config instruction | **Present** | `README.md:57–62` documents `~/.config/opencode/opencode.jsonc` model config | Not in the tracked project files — appropriately in README for one-time setup. |

---

## 6. Candidate Recommendations

### R1 — Add a commented `.claude/settings.json` template stub

**Change:** Add `.claude/settings.json` with the project's tool-permission whitelist commented out, and empty stanzas for hooks and MCP servers. Purpose: make the settings.json surface visible and self-documenting when the scaffold is instantiated. The file would ship with all hooks disabled and all MCP stanzas empty (commented).

**Source:** Claude Code settings.json reference (https://gist.github.com/mculp/c082bd1e5a439410158974de90c89db7; updated 2026-04-13); hooks guide (https://www.morphllm.com/claude-code-hooks).

**Confidence:** Medium. Useful as discoverability scaffolding; not required for the workflow to function.

**Constraint-compat:**
- Constraint #1 (agent-neutral): PARTIAL CONFLICT. `settings.json` is Claude-only. The stub is useful for Claude users but invisible/irrelevant to OpenCode. Label it clearly as Claude-side config. Do NOT ship hooks in it by default (hooks are opt-in per constraint #4).
- Constraint #4 (autonomy opt-in): Safe if all hooks are commented out.
- Constraint #3 (generic template): The file can ship as a template (all values as `<FILL:...>` or commented examples).

**Effort/Risk:** Low effort (create one file). Risk: a misconfigured `settings.json` could inadvertently grant or deny permissions — mitigated by shipping it fully commented.

---

### R2 — Verify and resolve OpenCode skill discovery path: add `.opencode/skills/` symlinks or mirror

**Change:** First, live-verify whether OpenCode discovers `.claude/skills/` automatically (see OQ1). If OpenCode does NOT auto-discover `.claude/skills/`:

**Option A (preferred):** Add symlinks in the scaffold: `.opencode/skills/ → ../.claude/skills/` so that both harnesses discover the same SKILL.md files without content duplication. (Git tracks symlinks natively.)

**Option B:** Ship a committed `.opencode/skills/` directory that symlinks each individual skill subdirectory. More granular but more maintenance overhead.

**Source:**
- mcp.directory cross-agent portability article (fetched 2026-06-13): "The Vercel installer's `opencode` target points to an `.opencode/skills/` project path."
- opencode.ai/docs/agents/ (fetched 2026-06-13): OpenCode's permission schema lists `skill` as a gatable permission key, implying native skill awareness — but does not document cross-path discovery from `.claude/skills/`.
- agensi.io (2026-04-13): "Skills can be stored in project config at `.opencode/skills/<n>/SKILL.md`, global config at `~/.config/opencode/skills/<n>/SKILL.md`, or in Claude-compatible and agent-compatible locations" — the "Claude-compatible" clause is ambiguous; insufficient to assume auto-discovery without a live test.

**Confidence:** High that the gap exists (paths are different; OpenCode docs don't list `.claude/skills/` as a discovery path). High that the symlink fix is correct. Conditional on OQ1 live test.

**Constraint-compat:** All five constraints satisfied. Cross-tool, file-based (symlinks are tracked files), generic, no autonomy change, sourceable.

**Effort/Risk:** Low effort (one symlink `ln -s ../../../.claude/skills .opencode/skills`). Low risk. If OpenCode does auto-discover via a compat path not documented in the official docs, the symlink is harmless (it just provides an additional discovery path).

---

### R3 — Add a commented MCP stanza example to the README or a `opencode.json.template`

**Change:** Add a commented example of MCP server registration to the README (or a non-tracked `opencode.json.example` file) so that operators know where to configure MCP servers when extending the scaffold for tools-connected workflows.

**Source:** MCP adoption statistics (https://www.digitalapplied.com/blog/mcp-adoption-statistics-2026-model-context-protocol; https://www.getknit.dev/blog/the-guide-to-the-mcp-ecosystem). MCP is now the dominant tool-connection standard and most projects will encounter it.

**Confidence:** Medium. The scaffold's generic nature makes the exact MCP config project-specific; the recommendation is only to make the *surface visible*, not to pre-configure it.

**Constraint-compat:**
- Constraint #1 (agent-neutral): MCP is genuinely cross-tool (Claude, OpenCode, Cursor, Codex all support it). Config syntax differs slightly per harness (Claude: `settings.json` `mcpServers`; OpenCode: `opencode.json` `mcp.servers`). The README could show both.
- Constraint #3 (generic template): An example/template file is fine; a committed `settings.json` with MCP values is not.
- All other constraints satisfied.

**Effort/Risk:** Low effort. Risk: none — it's documentation only.

---

### R4 — Verify skill `name` field matches directory name (spec compliance check — already passing)

**Finding:** The agentskills.io/specification (quoted in mcp.directory article, 2026-06-13) states: "name (max 64 chars, lowercase letters, numbers, hyphens; no leading, trailing, or consecutive hyphens; **must match the parent directory name**)." Checked against the scaffold: `openspec-apply-change/SKILL.md:2` has `name: openspec-apply-change` matching directory `openspec-apply-change/`; `openspec-explore/SKILL.md:2` has `name: openspec-explore` matching `openspec-explore/`. All 7 skills follow this pattern (verified by directory listing).

The optional fields `compatibility`, `license`, and `metadata` are all explicitly listed as optional in the published spec. They are additive and compliant; other agents harmlessly ignore them.

**Change:** No change needed. Verification complete — all 7 skills are spec-compliant on the name-matches-directory rule.

**Source:** agentskills.io/specification (as quoted in https://mcp.directory/blog/cross-agent-skills-cursor-codex-cline-antigravity-gemini-mastra-portability, 2026-06-13).

**Confidence:** High (verified against spec + scaffold).

**Constraint-compat:** N/A — this is a verification finding, not a recommendation.

**Effort/Risk:** Zero.

---

### R5 — Document the absence of hooks as a deliberate constraint-#1 choice

**Change:** Add a short entry to `ai-docs/decisions.md` recording: "Hooks are Claude-only (30 lifecycle events in `settings.json`); they are intentionally absent from the default scaffold because they conflict with constraint #1 (agent-neutral). Per-project hook configuration is left to the operator in their local `.claude/settings.json`."

**Source:** Claude Code hooks (https://www.morphllm.com/claude-code-hooks — 30 events, Claude-only). OpenCode has no equivalent hook system (confirmed from opencode.ai/docs/agents/ — only permission matrix).

**Confidence:** High. The absence is clearly correct but currently undocumented, which could confuse operators who know hooks exist and wonder why the scaffold doesn't use them.

**Constraint-compat:** All constraints satisfied. This is a documentation-only change.

**Effort/Risk:** Minimal.

---

## 7. Already-Ahead / Doesn't-Fit

### Already-ahead

- **AGENTS.md depth.** The scaffold's AGENTS.md (180 lines) is dramatically richer than the minimal convention (free-form Markdown with a few section headers). It encodes roles, phase gates, state discipline, commit rules, and working process in a stable, cache-friendly format. This is well ahead of the community standard, and appropriate for a template that needs to survive context resets.
- **AGENTS.md (not CLAUDE.md) as primary config — correct for a neutral template.** The deployhq.com guide (fetched 2026-06-13) confirms: "Claude Code also reads AGENTS.md as a fallback if no CLAUDE.md is found." The scaffold ships no CLAUDE.md, which means Claude Code reads AGENTS.md (same file OpenCode reads). This is the right cross-tool approach: one file, two harnesses. The only risk is if a future version of Claude Code stops reading AGENTS.md as a fallback, but there is no indication of that.
- **Dual-harness mirroring.** Maintaining parallel `.claude/agents/` and `.opencode/agents/` with consistent content but tool-appropriate frontmatter is not a common practice in community scaffolds — most pick one harness. The scaffold's deliberate mirroring is ahead of what the industry has converged on.
- **SKILL.md with progressive disclosure.** The 7 skills already use the standard SKILL.md format (name + description + body). The progressive-disclosure architecture (metadata loaded at startup, body on-demand) is the same pattern that the Agent Skills open standard mandates.
- **Agent Skills standard compliance (spec-verified).** The skill frontmatter (`name`, `description`, `license`, `compatibility`, `metadata`) is a superset of the required standard fields. Crucially, each skill's `name` field matches its parent directory name exactly — satisfying the spec's naming constraint. The optional additive fields are harmlessly ignored by non-Claude agents. The core format is fully portable.

### Deliberately not recommended

- **Claude Code hooks.** Hooks are Claude-only (30 events, `settings.json`-registered shell commands). There is no OpenCode equivalent. Shipping hooks in the default scaffold would violate constraint #1. Not recommended for the neutral template — operator-local configuration only. Documented as a gap in R5.
- **Claude Code slash commands (`.claude/commands/`)** The SKILL.md open standard has superseded slash commands as the reusable-workflow unit. Skills offer cross-tool portability, progressive disclosure, and frontmatter metadata; slash commands have none of these. Not recommended.
- **Native memory tools.** Claude's native memory tool, OpenCode's todo system, and similar harness-native state stores are explicitly ruled out by constraint #2. Not evaluated further.
- **Tool-specific instruction files (`.cursorrules`, `.clinerules`).** These are single-tool formats with no cross-tool value. Not recommended for a neutral template.
- **Baking MCP server config into the template.** MCP servers are project-specific (database, filesystem, API endpoints). A generic template cannot pre-configure them. Recommend only a commented stanza example (R3).

---

## 8. Open Questions for the Operator

**OQ1 — CRITICAL: Does OpenCode auto-discover skills from `.claude/skills/` without a `.opencode/skills/` directory?**
The mcp.directory portability article (2026-06-13) says OpenCode's project path is `.opencode/skills/`, and the Vercel installer explicitly targets that path. OpenCode's own docs list `.opencode/skills/` and `~/.config/opencode/skills/` but do NOT mention `.claude/skills/` as a compat path (unlike Cursor and Cline which do). The agensi.io article mentions "Claude-compatible locations" ambiguously. **This is the highest-priority open question in this bucket.** Recommended live test: run `opencode .` in the scaffold, ask it to "explore", and check whether it loads/acknowledges the `openspec-explore` skill. If it does NOT: implement R2 (symlink `.opencode/skills/` → `.claude/skills/`). If it does: add a documentation note in AGENTS.md clarifying this is working by compat-path, not by canonical OpenCode path.

**OQ2 — Should the scaffold ship a `.claude/settings.json` template?**
R1 proposes a commented stub. The counter-argument: committed `settings.json` files risk project-by-project permission drift; operators may forget to fill in or remove the stubs. The alternative is to document the settings.json surface in the README only. Operator call.

**OQ3 — Is the MCP spec (modelcontextprotocol.io/specification) relevant to the AGENTS.md content?**
The current scaffold does not mention MCP anywhere. Given MCP's near-universal adoption, should `AGENTS.md` include a note like "Tool access is provided via MCP servers configured in the operator's harness settings; do not assume any specific MCP server is available — check `STATUS.md` for this project's tool configuration"? This would make MCP awareness explicit without baking in harness-specific config. Operator call.

**OQ4 — Should the `.opencode/agents/openspec-reviewer.md` frontmatter include a `skill:` permission entry?**
Current OpenCode agent frontmatter (`.opencode/agents/openspec-reviewer.md`) does not include a `skill:` permission key. The OpenCode permission schema includes `skill` as a gatable key. Since the reviewer is read-only, it should probably explicitly deny skill invocation (no side-effects): `skill: deny`. Low priority but worth checking.

**OQ5 — RESOLVED: Scaffold SKILL.md format is spec-compliant.**
The mcp.directory article (fetched 2026-06-13) quotes the agentskills.io/specification verbatim. The scaffold's skills comply with all required fields (`name` matches directory, `description` present). The optional fields (`license`, `compatibility`, `metadata.*`) are explicitly listed in the spec as optional. The spec also lists `allowed-tools` as experimental; the scaffold does not use it — correct, since support is inconsistent. See R4 for the verified finding. The only remaining verification gap: whether `metadata.generatedBy: "1.4.1"` (an OpenSpec CLI version pin) might cause unexpected behavior on strict parsers — extremely low risk since unknown metadata keys are expected to be ignored.
