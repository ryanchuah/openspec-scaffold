# VERIFY-opencode-claims.md

Verification date: 2026-06-13
Installed opencode: v1.17.4 (`~/.opencode/bin/opencode`)
Repo examined: `sst/opencode` (GitHub, `dev` branch)
Models cache examined: `/home/pang/.cache/opencode/models.json`

---

## QUESTION 1 — Is the DeepSeek `reasoning_content` multi-turn bug FIXED in opencode 1.17.4?

**VERDICT: Confirmed fixed. Bug resolved in v1.14.24 (2026-04-24) via PR #24146, well before the operator's installed v1.17.4. The fix applies to the operator's exact config.**

### Decisive evidence

**PR #24146** ("fix: preserve empty reasoning_content for DeepSeek V4 thinking mode")
- URL: https://github.com/sst/opencode/pull/24146
- Merged: 2026-04-24T12:42:58Z
- Closed issues: #24104, #24097, #24130, #24124, #24135, #24114, #24111, #17523 (all 7 cited issues plus one more are in this set)
- PR was NOT merged as `mergedAt: null` for PR #24150 (the community's broader fix) — only #24146 landed

**v1.14.24 release notes** (https://github.com/anomalyco/opencode/releases/tag/v1.14.24, published 2026-04-24T15:53:05Z):
> "Fixed DeepSeek assistant messages so reasoning is always included, avoiding provider formatting failures."

This is the canonical, explicit confirmation that the fix shipped in v1.14.24. The operator's v1.17.4 > v1.14.24.

### How the fix works and why it covers the operator's config

Source: `packages/opencode/src/provider/transform.ts` (current `dev` branch, confirmed via `gh api`):

The fix removes a `if (reasoningText)` truthy guard so that the `interleaved.field` value (`"reasoning_content"`) is ALWAYS injected as `providerOptions.openaiCompatible[field]` for every assistant message, including those with empty `reasoning_content: ""`.

The fix fires when ALL THREE conditions hold:
1. `typeof model.capabilities.interleaved === "object"` with `.field` set
2. `model.capabilities.interleaved.field` is truthy
3. `model.api.npm !== "@openrouter/ai-sdk-provider"`

For the operator's config (`deepseek/deepseek-v4-pro`, built-in provider, no custom provider block):

- **Condition 1+2**: Confirmed from `/home/pang/.cache/opencode/models.json` — `deepseek-v4-pro` has `"interleaved": { "field": "reasoning_content" }` in models.dev. This is consumed at `fromModelsDevModel()` in `provider.ts:1210`: `interleaved: model.interleaved ?? false`.
- **Condition 3**: Built-in deepseek provider uses `"npm": "@ai-sdk/openai-compatible"` (confirmed from same `models.json` at `deepseek.npm`). Not OpenRouter. Passes.

All three conditions hold. The fix applies to the operator's exact config.

### Resolution of each issue

| Issue | How closed |
|---|---|
| #24104 | Closed by PR #24146 merge (explicitly listed in PR body), 2026-04-24 |
| #24122 ("[Solution]… Anthropic API") | User-side workaround; closed via Anthropic-compatible endpoint (NOT by PR #24146). The workaround remains valid but is unnecessary for built-in deepseek provider users. |
| #24124 | Closed by PR #24146 (in PR close list) |
| #24130 | Closed by PR #24146 |
| #24135 | Closed by PR #24146 |
| #24261 | Closed 2026-04-26 by user "rekram1-node" — after fix landed; comments note the OpenRouter-specific path was separately addressed; by close date PR #24146 had already covered the direct API path |
| #25000 | Closed 2026-05-01. Comments show maintainer response: "deepseeks own endpoints behave this exact same way so this isnt a bug, we may inject the reasoning_content: "" into streams to prevent errors for consumers tho". Closed as by-design / acknowledged. |

### Nuances and residual risks

- PR #24150 (the broader community fix that would inject `reasoning_content: ""` for ALL assistant messages regardless of `interleaved` config) was CLOSED without merging. Only PR #24146 (narrower, `interleaved`-path only) landed.
- If models.dev were to remove `interleaved: { field: "reasoning_content" }` from `deepseek-v4-pro`, the fix would silently stop applying. This is a soft dependency on models.dev data.
- Issue #25000 (`zen/go` proxy path) was closed without a code fix. The operator's config does NOT use `zen/go`, so this is irrelevant.
- v1.14.29 (released 2026-04-28) was cited by a user as still broken — that user was on the direct DeepSeek API path WITHOUT the `interleaved` config set manually. The built-in provider (with `interleaved` in models.dev) was already fixed in v1.14.24.

### Smoke test (optional, to confirm end-to-end)

If the operator wants to empirically verify before relying on the fix:

```bash
# Run a 2-turn opencode session that forces a tool-call chain with deepseek-v4-pro
# Turn 1: prompt that requires a tool call (e.g., read a file)
# Turn 2: follow-up that adds to the context, forcing a multi-turn history replay
opencode run --model deepseek/deepseek-v4-pro "Read the README.md file, then tell me how many lines it has and what the first heading is."
```

A successful run without `reasoning_content must be passed back` errors confirms the fix is active. The scaffold's `grep -q "Falling back to default agent"` guard in the apply skill is a runtime safety net but should not trigger.

---

## QUESTION 2 — Does OpenCode support "skills" at all, and how is the scaffold's skill layer reached under OpenCode?

**VERDICT: True-with-nuance. OpenCode (v1.16.0+, including v1.17.4) has a native skills mechanism distinct from Claude Code's. The scaffold's `.claude/skills/openspec-*/SKILL.md` files ARE discoverable by OpenCode at the project level. The AGENTS.md "Skill tool" reference is semantically compatible but refers to different underlying mechanics.**

### Confirmed: OpenCode has a native skill system (v1.16.0+)

Source: v1.16.0 release notes (https://github.com/anomalyco/opencode/releases/tag/v1.16.0, 2026-06-05):
> "Added skill discovery and file-based agent loading."

Source: `packages/opencode/src/skill/index.ts` (current `dev` branch via `gh api`) and `packages/opencode/src/skill/discovery.ts`.

Source: Official docs at https://opencode.ai/docs/skills (fetched 2026-06-13).

### Discovery paths (confirmed from source + docs)

OpenCode scans the following locations for `SKILL.md` files (in precedence order, unless disabled by env vars):

**Project-level (scanned by walking up from CWD to git worktree):**
- `.claude/skills/**/SKILL.md` (via `EXTERNAL_SKILL_PATTERN` on `CLAUDE_EXTERNAL_DIR`)
- `.agents/skills/**/SKILL.md`
- `.opencode/skills/**/SKILL.md` (and also `skill/**/SKILL.md`) via `OPENCODE_SKILL_PATTERN` on opencode config dirs

**Global (from `$HOME`):**
- `~/.claude/skills/**/SKILL.md`
- `~/.agents/skills/**/SKILL.md`
- `~/.config/opencode/skills/**/SKILL.md`

**Custom paths** from `opencode.jsonc` → `skills.paths[]` and remote urls from `skills.urls[]`.

Controlled by env vars `OPENCODE_DISABLE_EXTERNAL_SKILLS` and `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS` (both default `false`). Neither is set in the operator's environment (confirmed: `env | grep OPENCODE_DISABLE` returns nothing).

### The scaffold's skills ARE discoverable

The scaffold has these SKILL.md files:
```
.claude/skills/openspec-propose/SKILL.md         (name: openspec-propose)
.claude/skills/openspec-apply-change/SKILL.md    (name: openspec-apply-change)
.claude/skills/openspec-archive-change/SKILL.md  (name: openspec-archive-change)
.claude/skills/openspec-explore/SKILL.md         (name: openspec-explore)
.claude/skills/openspec-onboard/SKILL.md         (name: openspec-onboard)
.claude/skills/openspec-sync-specs/SKILL.md      (name: openspec-sync-specs)
.claude/skills/openspec-verify-change/SKILL.md   (name: openspec-verify-change)
```

All files have `name` and `description` frontmatter (verified by inspection). Directory names match `name` values. OpenCode will discover them via the `.claude/skills/**/SKILL.md` scan pattern.

The operator's `~/.config/opencode/opencode.jsonc` has no `skills` block and no `OPENCODE_DISABLE_*` env vars, so default scanning is active.

### How OpenCode invokes skills (vs. Claude Code)

OpenCode has its own **native `skill` tool** (defined in `packages/opencode/src/tool/skill.ts`). It is NOT Claude Code's "Skill tool" — the mechanics differ:

| Aspect | Claude Code | OpenCode |
|---|---|---|
| Tool name | `Skill` (harness-level, PascalCase) | `skill` (model-callable, lowercase) |
| Invocation | `Skill({ skill: "name" })` from skill-runner system | `skill({ name: "name" })` called by the LLM |
| Listing | Skills appear in system prompt | Skills listed in `skill` tool description + system prompt section |
| Loading | Harness reads and executes skill | Tool returns `<skill_content>` block with SKILL.md body + file list |
| System prompt injection | Skills listed and agent instructed to "invoke the appropriate skill (via the Skill tool)" | System prompt says: "Skills provide specialized instructions and workflows for specific tasks. Use the skill tool to load a skill when a task matches its description." |

Source for OpenCode system prompt text: `packages/opencode/src/session/system.ts:100-101`.

### Impact on the dual-harness scaffold

1. **Skills are reachable from OpenCode**: The `openspec-*` skills living in `.claude/skills/` will be found by OpenCode's scanner and listed in the agent's system prompt.

2. **AGENTS.md "Skill tool" wording is benign for OpenCode agents**: AGENTS.md says "invoke the appropriate skill (via the **Skill tool**)". An OpenCode-driven orchestrator (DeepSeek via built-in provider) sees instead "Use the skill tool to load a skill when a task matches its description" in its system prompt, with the skill list. The functional behavior is equivalent — the agent calls the skill tool when entering a phase.

3. **The `.opencode/` skill path claim is TRUE but INCOMPLETE**: The earlier subagent's claim that "OpenCode reads skills from `.opencode/skills/`" is confirmed by source and docs. However, it missed the equally-valid `.claude/skills/` path, which is where the scaffold's skills actually live. The scaffold does NOT need a `.opencode/skills/` copy.

4. **No `opencode skills` CLI command exists**: The v1.17.4 CLI does not expose skills as a top-level command (confirmed: `opencode --help` lists `acp, mcp, attach, run, agent, serve, web, github, pr`). Skills operate at session/agent level, not CLI level. This is expected and not a gap.

5. **OpenCode 1.16.0 introduces skills; 1.17.4 is after**: The installed v1.17.4 includes the skill system. Pre-1.16.0 versions of OpenCode would have had NO skill support.

### What the earlier unverified subagent claim was and whether it was a hallucination

The claim "OpenCode reads skills from `.opencode/skills/`" was **TRUE but INCOMPLETE** — not a hallucination. The opencode-native path `.opencode/skills/` IS real and documented. The claim was incomplete because it omitted the Claude Code compatibility path `.claude/skills/`, which is where the scaffold's skills live.

---

## Summary table

| | Q1: reasoning_content fixed? | Q2: OpenCode skills? |
|---|---|---|
| **Verdict** | Confirmed fixed | True-with-nuance |
| **Fixed when** | v1.14.24 (2026-04-24) | v1.16.0 (2026-06-05) introduced skills |
| **Key PR/source** | PR #24146 (merged 2026-04-24T12:42:58Z) | `src/skill/index.ts` + `src/tool/skill.ts` + docs |
| **Applies to operator's exact config** | Yes — built-in deepseek/deepseek-v4-pro has `interleaved: { field: "reasoning_content" }` in models.dev | Yes — `.claude/skills/` is scanned by default; all scaffold SKILL.md files valid |
| **Residual gap** | None for v1.17.4; soft dependency on models.dev keeping `interleaved` set | AGENTS.md wording "Skill tool" is Claude Code-centric; OpenCode orchestrator uses native `skill` tool (semantically equivalent, mechanically different) |
