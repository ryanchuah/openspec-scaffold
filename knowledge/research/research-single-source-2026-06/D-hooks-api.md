# D — Hook / Plugin API Reference

**Date:** 2026-06-16
**Method:** All page content fetched via `fetch_clean.py` from primary docs. Code-block examples in JS-rendered pages were stripped by the fetcher; those cases are noted inline. WebSearch used only to locate URLs.

---

## System 1 — Claude Code Hooks

**Primary source:** https://code.claude.com/docs/en/hooks
(hooks reference; `fetch_clean.py` retrieved 39 KB; code-block JSON examples stripped by fetcher)

Secondary reference (hooks guide): https://code.claude.com/docs/en/hooks-guide

---

### 1. Full list of hook EVENTS

**VERIFIED** — verbatim from hooks reference table (source: https://code.claude.com/docs/en/hooks):

> "Events fall into three cadences: once per session (`SessionStart`, `SessionEnd`), once per turn (`UserPromptSubmit`, `Stop`, `StopFailure`), and on every tool call inside the agentic loop (`PreToolUse`, `PostToolUse`)"

Full event table (verbatim from the same source):

| Event | When it fires |
|---|---|
| `SessionStart` | When a session begins or resumes |
| `Setup` | When you start Claude Code with `--init-only`, or with `--init` or `--maintenance` in `-p` mode. For one-time preparation in CI or scripts |
| `UserPromptSubmit` | When you submit a prompt, before Claude processes it |
| `UserPromptExpansion` | When a user-typed command expands into a prompt, before it reaches Claude. Can block the expansion |
| `PreToolUse` | Before a tool call executes. Can block it |
| `PermissionRequest` | When a permission dialog appears |
| `PermissionDenied` | When a tool call is denied by the auto mode classifier. Return `{retry: true}` to tell the model it may retry the denied tool call |
| `PostToolUse` | After a tool call succeeds |
| `PostToolUseFailure` | After a tool call fails |
| `PostToolBatch` | After a full batch of parallel tool calls resolves, before the next model call |
| `Notification` | When Claude Code sends a notification |
| `MessageDisplay` | While assistant message text is displayed |
| `SubagentStart` | When a subagent is spawned |
| `SubagentStop` | When a subagent finishes |
| `TaskCreated` | When a task is being created via `TaskCreate` |
| `TaskCompleted` | When a task is being marked as completed |
| `Stop` | When Claude finishes responding |
| `StopFailure` | When the turn ends due to an API error. Output and exit code are ignored |
| `TeammateIdle` | When an agent team teammate is about to go idle |
| `InstructionsLoaded` | When a CLAUDE.md or `.claude/rules/*.md` file is loaded into context. Fires at session start and when files are lazily loaded during a session |
| `ConfigChange` | When a configuration file changes during a session |
| `CwdChanged` | When the working directory changes, for example when Claude executes a `cd` command |
| `FileChanged` | When a watched file changes on disk. The `matcher` field specifies which filenames to watch |
| `WorktreeCreate` | When a worktree is being created via `--worktree` or `isolation: "worktree"`. Replaces default git behavior |
| `WorktreeRemove` | When a worktree is being removed, either at session exit or when a subagent finishes |
| `PreCompact` | Before context compaction |
| `PostCompact` | After context compaction completes |
| `Elicitation` | When an MCP server requests user input during a tool call |
| `ElicitationResult` | After a user responds to an MCP elicitation, before the response is sent back to the server |
| `SessionEnd` | When a session terminates |

**Total: 30 events.** This supersedes shorter lists from third-party sources.

---

### 2. Can a PreToolUse hook BLOCK a tool call? How?

**VERIFIED** — two mechanisms documented (source: https://code.claude.com/docs/en/hooks):

**Mechanism A — exit code 2** (verbatim):

> "**Exit 2** means a blocking error. Claude Code ignores stdout and any JSON in it. Instead, stderr text is fed back to Claude as an error message."

From the exit-code-2 table (verbatim):

> | `PreToolUse` | Yes | Blocks the tool call |

**Mechanism B — JSON `hookSpecificOutput.permissionDecision`** (verbatim from decision-control table):

> | PreToolUse | `hookSpecificOutput` | `permissionDecision` (allow/deny/ask/defer), `permissionDecisionReason` |

The docs also distinguish from the JSON `decision` field used by other events (verbatim):

> "Exit codes only let you block or stay silent, but JSON output gives you finer-grained control. Instead of exiting with code 2 to block, exit 0 and print a JSON object to stdout."
> "You must choose one approach per hook, not both: either use exit codes alone for signaling, or exit 0 and print JSON for structured control. Claude Code only processes JSON on exit 0. If you exit 2, any JSON is ignored."

**Summary:** PreToolUse blocking uses `hookSpecificOutput.permissionDecision: "deny"` (not top-level `decision`). Exit code 2 is the shell-script shorthand. The two are mutually exclusive per invocation.

---

### 3. Matcher + stdin JSON shape for PreToolUse

**VERIFIED** (source: https://code.claude.com/docs/en/hooks):

**Matching a specific tool:**

> "| Only letters, digits, `_`, and `|` | Exact string, or `|`-separated list of exact strings | `Bash` matches only the Bash tool; `Edit|Write` matches either tool exactly |"

> "| `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied` | tool name | `Bash`, `Edit|Write`, `mcp__.*` |"

**Inspecting the command string — the `if` field:**

> "For tool events, you can filter more narrowly by setting the `if` field on individual hook handlers. `if` uses permission rule syntax to match against the tool name and arguments together, so `"Bash(git *)"` runs when any subcommand of the Bash input matches `git *` and `"Edit(*.ts)"` runs only for TypeScript files."

Bash sub-command matching table (verbatim):

> | `Bash(git *)` | `npm test && git push` | yes | each subcommand is checked; `git push` matches |
> | `Bash(rm *)` | `echo $(rm -rf /)` | yes | commands inside `$()` and backticks are checked; `rm -rf /` matches |

**Stdin JSON shape:**

The docs state "For example, a `PreToolUse` hook for a Bash command receives this on stdin:" but the actual JSON code block was stripped by the fetcher (JS-rendered content). However the docs explicitly name the fields (verbatim):

> "Hook events receive these fields as JSON, in addition to event-specific fields documented in each hook event section."
> Common fields: `session_id`, `transcript_path`, `cwd`, `permission_mode`, `effort`, `hook_event_name`

> "`tool_name` and `tool_input` fields are event-specific. Each hook event section documents the additional fields for that event."

The MCP tool hook field docs also confirm `tool_input` structure (verbatim):

> "`input` | no | Arguments passed to the tool. String values support `${path}` substitution from the hook's JSON input, such as `"${tool_input.file_path}"`"

**UNVERIFIED (exact schema):** The verbatim JSON example for a `PreToolUse` Bash event (showing `tool_input.command` key name) was not retrievable — the code block was stripped by the fetcher. The field names `tool_name` and `tool_input` are confirmed; the nested key for the Bash command string (likely `command`) is inferred but not directly quoted.

---

### 4. Do hooks fire for subagent tool calls? SubagentStop event?

**VERIFIED** (source: https://code.claude.com/docs/en/hooks):

Hooks fire inside subagents. The docs add `agent_id` and `agent_type` to the JSON input when a hook fires inside a subagent (verbatim):

> "When a session uses `--agent` or inside a subagent, two additional fields are included:"
> | `agent_id` | Unique identifier for the subagent. Present only when the hook fires inside a subagent call. Use this to distinguish subagent hook calls from main-thread calls. |
> | `agent_type` | Agent name (for example, `"Explore"` or `"security-reviewer"`). Present when the session uses `--agent` or the hook fires inside a subagent. For subagents, the subagent's type takes precedence over the session's `--agent` value. |

`SubagentStop` event exists (verbatim from event table):

> | `SubagentStop` | When a subagent finishes |

Its exit-code-2 behavior (verbatim):

> | `SubagentStop` | Yes | Prevents the subagent from stopping |

Hooks in skills/agents (verbatim):

> "For subagents, `Stop` hooks are automatically converted to `SubagentStop` since that is the event that fires when a subagent completes."

---

### 5. Config format + location

**VERIFIED** (source: https://code.claude.com/docs/en/hooks):

Location options (verbatim from settings table):

> | `~/.claude/settings.json` | All your projects | No, local to your machine |
> | `.claude/settings.json` | Single project | Yes, can be committed to the repo |
> | `.claude/settings.local.json` | Single project | No, gitignored when Claude Code creates it |
> | Managed policy settings | Organization-wide | Yes, admin-controlled |
> | Plugin `hooks/hooks.json` | When plugin is enabled | Yes, bundled with the plugin |
> | Skill or agent frontmatter | While the component is active | Yes, defined in the component file |

Structure (verbatim from hooks guide, https://code.claude.com/docs/en/hooks-guide):

> "The configuration has three levels of nesting: Choose a hook event to respond to, like `PreToolUse` or `Stop` / Add a matcher group to filter when it fires, like 'only for the Bash tool' / Define one or more hook handlers to run when matched"

Actual JSON config examples were JS-rendered and stripped by the fetcher. Structure is: `hooks` object keyed by event name, each value an array of matcher-group objects; each group has `matcher` and `hooks` (array of handler objects with `type`, `command`/`url`/etc.).

---

---

## System 2 — OpenCode Plugins

**Primary source:** https://opencode.ai/docs/plugins/
(fetched via `fetch_clean.py`, 29 KB returned intact — this page is SSR/static, code examples rendered)

Secondary: https://opencode.ai/docs/cli/

---

### 1. Does OpenCode have a plugin/hook system? Config location + file shape?

**VERIFIED** (source: https://opencode.ai/docs/plugins/):

> "Plugins allow you to extend OpenCode by hooking into various events and customizing behavior. You can create plugins to add new features, integrate with external services, or modify OpenCode's default behavior."

**Config locations (verbatim):**

> "Place JavaScript or TypeScript files in the plugin directory."
> "- `.opencode/plugins/` - Project-level plugins"
> "- `~/.config/opencode/plugins/` - Global plugins"
> "Files in these directories are automatically loaded at startup."

Via npm (verbatim):

> "Specify npm packages in your config file."
> ```json
> {
>   "$schema": "https://opencode.ai/config.json",
>   "plugin": ["opencode-helicone-session", "opencode-wakatime", "@my-org/custom-plugin"]
> }
> ```

**Plugin file shape (verbatim):**

> "A plugin is a **JavaScript/TypeScript module** that exports one or more plugin functions. Each function receives a context object and returns a hooks object."

```typescript
export const MyPlugin = async ({ project, client, $, directory, worktree }) => {
  console.log("Plugin initialized!")
  return {
    // Hook implementations go here
  }
}
```

TypeScript typing (verbatim):

> ```typescript
> import type { Plugin } from "@opencode-ai/plugin"
> export const MyPlugin: Plugin = async ({ project, client, $, directory, worktree }) => {
> ```

**Load order (verbatim):**

> "Global config (`~/.config/opencode/opencode.json`) / Project config (`opencode.json`) / Global plugin directory (`~/.config/opencode/plugins/`) / Project plugin directory (`.opencode/plugins/`)"

---

### 2. Plugin hook events — does `tool.execute.before`, `tool.execute.after`, and session lifecycle exist?

**VERIFIED** (source: https://opencode.ai/docs/plugins/):

The complete event list (verbatim):

**Tool Events:**
- `tool.execute.after`
- `tool.execute.before`

**Session Events:**
- `session.created`
- `session.compacted`
- `session.deleted`
- `session.diff`
- `session.error`
- `session.idle`
- `session.status`
- `session.updated`

**Command Events:** `command.executed`

**File Events:** `file.edited`, `file.watcher.updated`

**Installation Events:** `installation.updated`

**LSP Events:** `lsp.client.diagnostics`, `lsp.updated`

**Message Events:** `message.part.removed`, `message.part.updated`, `message.removed`, `message.updated`

**Permission Events:** `permission.asked`, `permission.replied`

**Server Events:** `server.connected`

**Shell Events:** `shell.env`

**Todo Events:** `todo.updated`

**TUI Events:** `tui.prompt.append`, `tui.command.execute`, `tui.toast.show`

**Experimental:** `experimental.session.compacting`

**All three specifically asked about exist — VERIFIED:**
- `tool.execute.before` — fires before tool execution (**VERIFIED**)
- `tool.execute.after` — fires after tool execution (**VERIFIED**)
- Session lifecycle events: `session.created`, `session.idle`, `session.deleted`, `session.compacted` (**VERIFIED**)

---

### 3. Can a plugin (a) run arbitrary code / write files on each tool call, and (b) ABORT/deny a tool call?

**VERIFIED** (source: https://opencode.ai/docs/plugins/):

**(a) Run arbitrary code / write files:**

Plugins receive Bun's shell API (`$`) for executing commands (verbatim):

> "- `$`: Bun's shell API for executing commands."

Example from send-notifications plugin (verbatim):

> ```typescript
> if (event.type === "session.idle") {
>   await $`osascript -e 'display notification "Session completed!" with title "opencode"'`
> }
> ```

**(b) ABORT/deny a tool call — throw to block:**

The `.env` protection example demonstrates throwing to block (verbatim):

> ```typescript
> export const EnvProtection = async ({ project, client, $, directory, worktree }) => {
>   return {
>     "tool.execute.before": async (input, output) => {
>       if (input.tool === "read" && output.args.filePath.includes(".env")) {
>         throw new Error("Do not read .env files")
>       }
>     },
>   }
> }
> ```

This shows `throw new Error(...)` inside `tool.execute.before` aborts the tool call. No alternative JSON decision field documented for the plugin system; throwing is the stated mechanism.

**Note:** `tool.execute.after` — there is no example of blocking from the `after` hook; the docs imply it is observational (tool has already run). UNVERIFIED whether `throw` in `tool.execute.after` has any effect beyond logging.

---

### 4. Do plugins run during `opencode run` (non-interactive)?

**PARTIALLY VERIFIED** (source: https://opencode.ai/docs/cli/):

The CLI docs confirm `opencode run` exists as a non-interactive mode (verbatim):

> "Run opencode in non-interactive mode by passing a prompt directly. This is useful for scripting, automation, or when you want a quick answer without launching the full TUI."

The global CLI flag `--pure` (verbatim) strongly implies plugins ARE loaded by default:

> "`--pure` | Run without external plugins"

This is a global opt-out, meaning the default (without `--pure`) is that external plugins are loaded. Since `opencode run` is listed under the same CLI with the same global flags, plugins should load in non-interactive mode as well.

**UNVERIFIED** in the strict sense: no explicit doc sentence states "plugins fire during `opencode run --agent X`." The inference from `--pure` as a global opt-out is strong but is not a direct quote confirming plugin hooks fire in non-interactive runs.

Also relevant: `OPENCODE_DISABLE_DEFAULT_PLUGINS: boolean | Disable default plugins` is listed in environment variables, further confirming plugins are a default-on system.

---

### 5. Version requirements for the plugin API

**UNVERIFIED** — The plugin documentation at https://opencode.ai/docs/plugins/ makes no mention of minimum OpenCode version requirements for the plugin API. The `@opencode-ai/plugin` npm package is referenced for TypeScript types but no version number appears in the docs.

The `experimental.session.compacting` hook is labeled experimental (verbatim: "experimental.session.compacting") which implies instability, but no version is cited.

---

---

## Cross-system caveats

### Caveat (i): Gating `git commit` on tests passing — Claude Code `PreToolUse`

**Critical caveat:** The `if` filter for `Bash(git commit*)` is documented as **best-effort**, not a security boundary. Verbatim:

> "Note: if filter is best-effort, use the permission system rather than a hook to enforce a hard allow or deny."

Additionally, the exact `if` pattern `"Bash(git commit *)"` is not directly verified against the actual Bash-command-matching table for the `git commit` subcommand shape; but the table shows `Bash(git *)` matching `npm test && git push` correctly (subcommands checked). Claude Code also checks commands inside `$()` and backticks. The hook must run tests synchronously and exit 2 to block; the test command and its exit status must be checked inside the hook script.

**Second caveat:** The JSON blocking mechanism for `PreToolUse` uses `hookSpecificOutput.permissionDecision: "deny"`, NOT the top-level `decision: "block"` that most other events use. Using `decision: "block"` on a `PreToolUse` hook will not have the documented blocking effect.

### Caveat (ii): OpenCode progress/heartbeat line after every tool call — `tool.execute.after`

**Critical caveat:** The plugin event system is labeled **experimental** in a key env variable: `OPENCODE_EXPERIMENTAL_EVENT_SYSTEM: boolean | Enable experimental event system`. This suggests the entire event/plugin system (or parts of it) may require opting into an experimental flag, and may change or break between releases. **UNVERIFIED** which specific events require this flag.

**Second caveat:** `tool.execute.after` is the correct hook, but the docs do not show whether it also receives `input.tool` to distinguish which tool fired. The `.env` protection example uses `input.tool === "read"` in `tool.execute.before`; whether `tool.execute.after` has the same `input` shape is implied but not shown with a verbatim after-hook example.

**Third caveat:** The `session.idle` event (not `tool.execute.after`) is what the official notification example uses for "session complete" signaling. For a per-tool heartbeat, `tool.execute.after` is correct per the event list, but there is no example in the docs showing writing to a file from `tool.execute.after`.
