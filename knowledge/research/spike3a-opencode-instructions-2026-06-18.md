# OpenCode Instruction-Include Mechanism — Research Spike

**Date:** 2026-06-18
**Scope:** How OpenCode loads additional instruction context (AGENTS.md, config `instructions:`, global vs project layering, @import support)

---

## Sources

| Artifact | URL |
|---|---|
| OpenCode config loader (app layer) | `github.com/anomalyco/opencode/blob/dev/packages/opencode/src/config/config.ts` |
| Instruction service (loads files at runtime) | `github.com/anomalyco/opencode/blob/dev/packages/opencode/src/session/instruction.ts` |
| Core config schema (TypeScript/Effect Schema) | `github.com/anomalyco/opencode/blob/dev/packages/core/src/v1/config/config.ts` |
| Official docs — Config page | `https://opencode.ai/docs/config` |
| Official docs — Rules page | `https://opencode.ai/docs/rules` |

---

## Q1: Does `instructions: [...]` exist? Exact key and schema?

**Confirmed YES.**

The exact config key is `instructions` (lowercase, singular). It appears in both the canonical config schema and the official docs.

**Schema definition** (from `packages/core/src/v1/config/config.ts`):
```typescript
instructions: Schema.optional(Schema.mutable(Schema.Array(Schema.String))).annotate({
  description: "Additional instruction files or patterns to include",
}),
```

**Docs example** (from `opencode.ai/docs/config#instructions`):
```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": ["CONTRIBUTING.md", "docs/guidelines.md", ".cursor/rules/*.md"]
}
```

The key is valid in both `opencode.json` and `opencode.jsonc` formats, at both the project level and the global `~/.config/opencode/opencode.json`.

---

## Q2: Can entries reference files OUTSIDE the repo? Do they support globs?

**Confirmed YES to both.**

From `packages/opencode/src/session/instruction.ts` (`systemPaths()` function):

```typescript
const instruction = raw.startsWith("~/") ? path.join(global.home, raw.slice(2)) : raw
const matches = yield* (
  path.isAbsolute(instruction)
    ? fs.glob(path.basename(instruction), {
        cwd: path.dirname(instruction),
        absolute: true,
        include: "file",
      })
    : relative(instruction)
)
```

This means:
- **`~/path/to/file.md`** — expanded to the user's home directory (explicit support)
- **`/absolute/path/file.md`** — absolute paths, fully supported, may be anywhere on the filesystem
- **Globs** — supported for both absolute (`fs.glob`) and relative (`fs.globUp`) entries
- **HTTP/HTTPS URLs** — also supported; fetched remotely with a 5-second timeout

From the official docs (`opencode.ai/docs/rules#custom-instructions`):
```json
{
  "instructions": ["CONTRIBUTING.md", "docs/guidelines.md", ".cursor/rules/*.md"]
}
```
```json
{
  "instructions": ["https://raw.githubusercontent.com/my-org/shared-rules/main/style.md"]
}
```

**Important caveat on global vs project array merging:** The config loader uses remeda's `mergeDeep` for regular config merging, which **replaces** arrays rather than concatenating them. So if:
- Global `~/.config/opencode/opencode.json` has `"instructions": ["~/universal-rules.md"]`
- Project `opencode.json` has `"instructions": ["CONTRIBUTING.md"]`

...then the **project array replaces the global array** — `~/universal-rules.md` is NOT loaded when the project also defines `instructions`. The only merge that concatenates `instructions` arrays is the macOS MDM managed-preferences path (`mergeConfigConcatArrays`), not normal config layering.

**Workaround:** Each project config that wants universal rules must include the shared path explicitly:
```json
{ "instructions": ["~/path/to/universal.md", "CONTRIBUTING.md"] }
```

---

## Q3: AGENTS.md discovery and @import

**AGENTS.md discovery** (from `instruction.ts`):

```typescript
const globalFiles = [
  path.join(global.config, "AGENTS.md"),     // ~/.config/opencode/AGENTS.md
  ...(!flags.disableClaudeCodePrompt ? [path.join(global.home, ".claude", "CLAUDE.md")] : []),
]
const instructionFiles = [
  "AGENTS.md",
  ...(!flags.disableClaudeCodePrompt ? ["CLAUDE.md"] : []),
  "CONTEXT.md", // deprecated
]
```

OpenCode:
1. Checks for a global `~/.config/opencode/AGENTS.md` (falls back to `~/.claude/CLAUDE.md` unless disabled)
2. Walks up from the project directory looking for `AGENTS.md`, `CLAUDE.md`, or `CONTEXT.md` — **first match wins**

**`@import` in AGENTS.md — confirmed NO-OP.**

OpenCode reads instruction files with a plain `fs.readFileString(filepath)` — there is zero parsing of in-file directives. The official docs state this explicitly:

> "While opencode doesn't automatically parse file references in `AGENTS.md`..."

The docs provide two alternatives:
1. Use `instructions: [...]` in `opencode.json` (recommended)
2. Teach the model via prose in AGENTS.md to use its Read tool when it encounters a `@reference` marker (a prompt-engineering workaround, not a harness feature)

Claude Code's `@path` / `@import` directive inside AGENTS.md/CLAUDE.md does nothing in OpenCode.

---

## Q4: Global vs project layering

**Config file precedence** (from `opencode.ai/docs/config`, confirmed in source):

1. Remote config (`.well-known/opencode`) — organizational defaults
2. Global config (`~/.config/opencode/opencode.json`) — user preferences
3. Custom config (`OPENCODE_CONFIG` env var)
4. Project config (`opencode.json` in project root)
5. `.opencode/` directories — agents, commands, plugins
6. `OPENCODE_CONFIG_CONTENT` env var — runtime overrides
7. Managed config files (system paths, admin-controlled)
8. macOS managed preferences (MDM `.mobileconfig`) — highest priority

For **instruction file discovery** (AGENTS.md, etc.), global and project files are both loaded and combined — the `systemPaths()` function adds all matched paths into a single Set.

For **`instructions` config array**, standard `mergeDeep` semantics apply: later config wins for the whole array (project replaces global). Only MDM-managed preferences use `mergeConfigConcatArrays`.

---

## Q5: Precedence / ordering for multiple instruction sources

From `instruction.ts` `system()` function, the order of content delivery to the model is:

1. Paths matched by `systemPaths()` in insertion order:
   a. Global AGENTS.md / CLAUDE.md (first found)
   b. Project AGENTS.md / CLAUDE.md / CONTEXT.md (first found, walking upward)
   c. Each entry from `config.instructions` (in array order, with `~` and absolute paths resolved)
2. Remote URL entries from `config.instructions` (http/https), fetched separately

Each instruction block is prefixed with `Instructions from: <path>` so the model knows the source.

---

## Cross-harness "universal rules" viability summary

| Feature | Claude Code | OpenCode |
|---|---|---|
| In-file `@import` in AGENTS.md/CLAUDE.md | YES (native harness feature) | NO-OP |
| Config-level instruction include | `CLAUDE.md` only, no array | `instructions: [...]` in opencode.json |
| Absolute / `~/` paths | Yes (via `@import` in CLAUDE.md) | Yes (native in `instructions` entries) |
| Globs | Yes (via `@import`) | Yes (native in `instructions` entries) |
| HTTP URLs | No | Yes |
| Global config propagates `instructions` to projects | N/A | NO — project array replaces global |
| Global AGENTS.md/CLAUDE.md loaded | Yes (`~/.claude/CLAUDE.md`) | Yes (`~/.config/opencode/AGENTS.md`) |

**Bottom line:** A single "universal rules live once" file can be loaded in both harnesses, but the mechanism is asymmetric:
- Claude Code: put `@import ~/universal-rules.md` inside `~/.claude/CLAUDE.md`
- OpenCode: put `"instructions": ["~/universal-rules.md"]` inside every project's `opencode.json`, OR inside the global `~/.config/opencode/opencode.json` (but only if no project also defines `instructions`, which is fragile)

The pattern is viable but requires per-repo boilerplate in OpenCode's `opencode.json` unless projects never define their own `instructions` arrays. The global `~/.config/opencode/AGENTS.md` approach is the closest equivalent to Claude Code's global CLAUDE.md — it applies universally without per-project configuration.
