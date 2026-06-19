# Native single-source mechanisms: Claude Code + OpenCode

Research date: 2026-06-14
Problem: 3 sibling repos (`openspec-scaffold`, `extrends`, `psc-monitor`) each carry their own copy of
`.claude/skills/`, `.opencode/agents/`, `AGENTS.md`, `ai-docs/`. Goal: ONE source so a single edit
propagates, while both Claude Code (claude-cli) and OpenCode (`opencode run`) keep working.

All load-bearing claims below are quoted verbatim from primary docs (docs.claude.com /
code.claude.com, opencode.ai/docs) or the OpenCode GitHub release changelog. Items I could not
confirm from a primary source are explicitly labelled UNVERIFIED.

---

## PART 1 — CLAUDE CODE

### 1.1 User-level vs project-level skills (scope, precedence, discovery)
Source: https://code.claude.com/docs/en/skills

**What it is:** Skills are `SKILL.md` files Claude loads on demand. They live at four scopes.

**Exact behavior — where skills live (verbatim table):**
> | Location | Path | Applies to |
> | Enterprise | See managed settings | All users in your organization |
> | Personal | `~/.claude/skills/<skill-name>/SKILL.md` | All your projects |
> | Project | `.claude/skills/<skill-name>/SKILL.md` | This project only |
> | Plugin | `<plugin>/skills/<skill-name>/SKILL.md` | Where plugin is enabled |

**Precedence (verbatim, from WebSearch summary of the same docs page — see caveat):** "enterprise
overrides personal, and personal overrides project. However, when a project Skill and a personal
Skill share the same name, the project-level Skill takes priority." NOTE: the skills doc body I
fetched states plugin skills are namespaced (`plugin-name:skill-name`) "so they cannot conflict with
other levels" and "if a skill and a command share the same name, the skill takes precedence." The
exact personal-vs-project tiebreak wording is UNVERIFIED from the fetched page text (it came from the
search snippet, not the page body I captured); treat the namespacing + command/skill rule as the
verified parts.

**Discovery (verbatim):**
> "Project skills load from `.claude/skills/` in your starting directory and in every parent
> directory up to the repository root ... Claude Code also discovers skills from nested
> `.claude/skills/` directories on demand."

**Live reload (verbatim):**
> "Adding, editing, or removing a skill under `~/.claude/skills/`, the project `.claude/skills/`, or
> a `.claude/skills/` inside an `--add-dir` directory takes effect within the current session without
> restarting."

**Verdict:** `~/.claude/skills/` (Personal scope) is a true single source for SKILL.md content across
ALL projects on the machine — and (see 2.2) OpenCode also reads it. Strong candidate for the SKILL
half of the problem. Does NOT cover agents/AGENTS.md.

---

### 1.2 Plugins and plugin marketplaces
Sources: https://code.claude.com/docs/en/plugins , https://code.claude.com/docs/en/discover-plugins

**What it is:** A plugin is a self-contained directory bundling skills, agents, commands, hooks, MCP
servers, LSP servers, monitors, and default settings. Distributed via a git "marketplace"
(`.claude-plugin/marketplace.json`).

**Exact behavior — what a plugin can bundle (verbatim table):** `skills/`, `commands/`, `agents/`
("Custom agent definitions"), `hooks/`, `.mcp.json`, `.lsp.json`, `monitors/`, `bin/`,
`settings.json`. So unlike `--add-dir`, a plugin DOES distribute agents + commands across projects.

**Why plugins for multi-repo (verbatim):**
> "Use plugins when: ... You need the same skills/agents across multiple projects ... You want
> version control and easy updates for your extensions ... You're distributing through a marketplace"

**Install / scope (verbatim, discover-plugins):**
> "User scope: install for yourself across all projects / Project scope: install for all
> collaborators on this repository (adds to `.claude/settings.json`) / Local scope: ..."

**Team auto-install (verbatim):**
> "Add `extraKnownMarketplaces` to your project's `.claude/settings.json`. When team members trust
> the repository folder, Claude Code prompts them to install these marketplaces and plugins."

**Updates (verbatim):**
> "When auto-update is enabled for a marketplace, Claude Code refreshes the marketplace data and
> updates installed plugins to their latest versions."

**Marketplace sources (verbatim):** GitHub `owner/repo`, any Git URL (GitLab/Bitbucket/self-hosted),
**local paths** ("Add a local directory that contains a `.claude-plugin/marketplace.json` file"), and
remote `marketplace.json` URLs. Local-path marketplaces matter here: the golden-source repo itself
could BE a local marketplace.

**Namespacing caveat (verbatim):** "Plugin skills are always namespaced (like
`/my-first-plugin:hello`) ... To change the namespace prefix, update the `name` field in
plugin.json." So skill command names change from `/openspec-propose` to `/<plugin>:openspec-propose`.

**Version caveat:** `/plugin` requires a recent Claude Code; context-cost/last-updated/"Will install"
panels are v2.1.143–145+. `--plugin-url` zip loading needs v2.1.128+.

**Verdict:** The ONLY native Claude mechanism that ships skills + agents + commands together from one
versioned git source to many repos. Strong candidate for the Claude side — but OpenCode does NOT
consume Claude plugins (see Part 2), and skill names become namespaced.

---

### 1.3 Settings precedence (enterprise / user / project / local)
Source: https://code.claude.com/docs/en/settings

**Scopes (verbatim table):** Managed (`managed-settings.json` / plist / registry) → User
(`~/.claude/`) → Project (`.claude/`) → Local (`.claude/settings.local.json`).

**Precedence (verbatim):**
> "Managed (highest) - can't be overridden by anything / Command line arguments / Local - overrides
> project and user settings / Project - overrides user settings / User (lowest)"
> "Permission rules behave differently because they merge across scopes rather than override."

**What uses scopes (verbatim table):** Settings, Subagents (`~/.claude/agents/` user vs
`.claude/agents/` project — "Local location: None"), MCP servers, Plugins, CLAUDE.md.

**Verdict:** Settings precedence is about config values, not file sharing; not itself a single-source
mechanism, but it confirms `~/.claude/agents/` is a user-level home for subagents shared across all
projects (Claude only).

---

### 1.4 `--add-dir` / additional directories
Source: https://code.claude.com/docs/en/skills (and memory doc for CLAUDE.md)

**What it is:** Grants Claude file access to a directory outside the working dir.

**Critical exception (verbatim):**
> "The `--add-dir` flag and `/add-dir` command grant file access rather than configuration discovery,
> but skills are an exception: `.claude/skills/` within an added directory is loaded automatically.
> This exception applies only to `--add-dir` and `/add-dir`. The `permissions.additionalDirectories`
> setting in `settings.json` grants file access only and does not load skills."

**What it does NOT load (verbatim):**
> "Other `.claude/` configuration such as subagents, commands, and output styles is not loaded from
> additional directories."
> "CLAUDE.md files from `--add-dir` directories are not loaded by default. To load them, set
> `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`."

**Verdict:** `--add-dir <golden-source>` is a clean way to pull the golden repo's `.claude/skills/`
into any sibling repo's session WITHOUT copying — but only skills, not agents/commands, and CLAUDE.md
only behind an env var. Requires passing the flag every launch (could be wrapped in settings/alias).
Useful as a skills-only single source for Claude; does not help OpenCode.

---

### 1.5 CLAUDE.md / AGENTS.md discovery + `@path` imports + `.claude/rules/` symlinks
Source: https://code.claude.com/docs/en/memory

**AGENTS.md handling (verbatim — KEY):**
> "Claude Code reads `CLAUDE.md`, not `AGENTS.md`. If your repository already uses `AGENTS.md` for
> other coding agents, create a `CLAUDE.md` that imports it so both tools read the same instructions
> without duplicating them."

**`@path` imports (verbatim):**
> "CLAUDE.md files can import additional files using `@path/to/import` syntax ... Both relative and
> absolute paths are allowed. Relative paths resolve relative to the file containing the import ...
> Imported files can recursively import other files, with a maximum depth of four hops."

So a one-line `CLAUDE.md` in each repo can be `@/abs/path/to/golden/AGENTS.md` (or
`@~/...` style via home), making the golden AGENTS.md the single source for Claude. Note: "imported
files still load and enter the context window at launch" (no token savings, but single-source works).

**`.claude/rules/` + symlinks (verbatim — KEY for ai-docs/conventions):**
> "The `.claude/rules/` directory supports symlinks, so you can maintain a shared set of rules and
> link them into multiple projects. Symlinks are resolved and loaded normally, and circular symlinks
> are detected and handled gracefully."
> "Personal rules in `~/.claude/rules/` apply to every project on your machine."

Rules also support `paths:` frontmatter for path-scoped loading.

**Verdict:** `@path` import of a shared AGENTS.md (absolute path to the golden repo) is the cleanest
native single-source for the AGENTS.md/rules half on the Claude side. `.claude/rules/` symlinks +
`~/.claude/rules/` cover the `ai-docs/`/conventions half. Both Claude-only, but pair naturally with
OpenCode's `instructions` field (2.4) since the underlying shared file can be the same.

---

## PART 2 — OPENCODE

### 2.1 Global vs project config + precedence
Source: https://opencode.ai/docs/config/

**Locations / precedence (verbatim):**
> "Config sources are loaded in this order (later sources override earlier ones): Remote config (from
> `.well-known/opencode`) ... Global config (`~/.config/opencode/opencode.json`) ... Custom config
> (`OPENCODE_CONFIG` env var) ... Project config (`opencode.json` in project) ... `.opencode`
> directories ... Inline config (`OPENCODE_CONFIG_CONTENT`) ... Managed config files ... macOS
> managed preferences (highest)."
> "Configuration files are merged together, not replaced. ... Later configs override earlier ones
> only for conflicting keys."

**Custom config dir (verbatim):**
> "Specify a custom config directory using the `OPENCODE_CONFIG_DIR` environment variable. This
> directory will be searched for agents, commands, modes, and plugins just like the standard
> `.opencode` directory."

**Verdict:** Global `~/.config/opencode/` is OpenCode's user-level single source for agents/commands/
plugins across all projects. `OPENCODE_CONFIG_DIR` could even point every repo at one shared dir, but
that's machine-global, not per-repo selectable without env juggling.

---

### 2.2 OpenCode auto-loads `.claude/skills/` and `~/.claude/skills/` — VERSION CONFIRMED
Sources: https://opencode.ai/docs/skills/ , GitHub `sst/opencode` release changelog (via `gh api`)

**Skill search locations (verbatim):**
> "OpenCode searches these locations: Project config `.opencode/skills/<name>/SKILL.md`; Global config
> `~/.config/opencode/skills/<name>/SKILL.md`; Project Claude-compatible `.claude/skills/<name>/SKILL.md`;
> Global Claude-compatible `~/.claude/skills/<name>/SKILL.md`; Project agent-compatible
> `.agents/skills/<name>/SKILL.md`; Global agent-compatible `~/.agents/skills/<name>/SKILL.md`."
> "Global definitions are also loaded from `~/.config/opencode/skills/*/SKILL.md`,
> `~/.claude/skills/*/SKILL.md`, and `~/.agents/skills/*/SKILL.md`."

**Invocation model (verbatim):** "Skills are loaded on-demand via the native `skill` tool — agents
see available skills and can load the full content when needed." (Differs from Claude's
auto-pattern-match; OpenCode the agent explicitly calls the `skill` tool.)

**VERSION (from GitHub release changelog — primary):** The operator's "~v1.16" guess is WRONG. Actual:
- **v1.0.190** — "feat: add native skill tool with permission system (#5930)" (the `skill` tool itself)
- **v1.0.210** — "Read global Claude skills in addition to project-specific skills" (i.e. project
  `.claude/skills` already worked; `~/.claude/skills` global support landed here)
- **v1.0.211** — "docs: global claude skills"
- **v1.1.7** — "Allow disabling .claude prompt and skills loading" (opt-out env vars added)
- **v1.1.48** — "Make skills invokable as sla[sh] [commands]"
So `.claude/skills` consumption has existed since the v1.0.190–v1.0.210 range, NOT v1.16.

**Disable switch (verbatim, rules doc):** "To disable Claude Code compatibility, set one of these
environment variables" (the doc lists env vars; exact names not rendered in fetch — see UNVERIFIED).

**Verdict:** STRONGEST cross-tool finding. A single SKILL.md in `~/.claude/skills/<name>/` is read by
BOTH Claude Code (Personal scope) AND OpenCode (global Claude-compatible) with zero duplication. This
is the natural single source for the skills half across both tools. Caveat: skill names must be
unique across all locations; OpenCode invokes via the `skill` tool, not Claude's pattern-matching.

---

### 2.3 AGENTS.md discovery / precedence in OpenCode + Claude compatibility
Source: https://opencode.ai/docs/rules/

**Precedence (verbatim):**
> "When opencode starts, it looks for rule files in this order: Local files by traversing up from the
> current directory (`AGENTS.md`, `CLAUDE.md`); Global file at `~/.config/opencode/AGENTS.md`; Claude
> Code file at `~/.claude/CLAUDE.md` (unless disabled). The first matching file wins in each category.
> ... if you have both `AGENTS.md` and `CLAUDE.md`, only `AGENTS.md` is used."

**Claude compat (verbatim):**
> "Project rules: `CLAUDE.md` in your project directory (used if no `AGENTS.md` exists). Global rules:
> `~/.claude/CLAUDE.md` (used if no `~/.config/opencode/AGENTS.md` exists). Skills: `~/.claude/skills/`"

**Note:** OpenCode natively reads `AGENTS.md` (project root and global `~/.config/opencode/AGENTS.md`).
Claude reads `CLAUDE.md` only. So a shared `AGENTS.md` needs a tiny `CLAUDE.md` shim that imports it
(see 1.5) for full cross-tool coverage from one file.

**Verdict:** OpenCode is AGENTS.md-native; the missing link is Claude, solved by a `@AGENTS.md`
import. Combined with 1.5 this gives a genuine single-source AGENTS.md for both tools.

---

### 2.4 OpenCode `instructions` field (file globs, remote URLs, file references) — KEY
Source: https://opencode.ai/docs/rules/ and https://opencode.ai/docs/config/

**What it is (verbatim):**
> "You can specify custom instruction files in your `opencode.json` or the global
> `~/.config/opencode/opencode.json`. This allows you and your team to reuse existing rules rather
> than having to duplicate them to AGENTS.md."
> "You can also use remote URLs to load instructions from the web. Remote instructions are fetched
> with a 5 second timeout. All instruction files are combined with your `AGENTS.md` files."

**Globs + sharing (verbatim, config doc):** the `instructions` option "takes an array of paths and
glob patterns to instruction files."

**External file references (verbatim):**
> "The recommended approach is to use the `instructions` field in `opencode.json`" ... enables you to
> "Share rules across projects via symlinks or git submodules."

**`{file:...}` substitution (verbatim, config doc):** "Use `{file:path/to/file}` to substitute the
contents of a file ... absolute paths starting with `/` or `~`."

**Verdict:** OpenCode's `instructions: ["/abs/path/to/golden/ai-docs/**/*.md", ...]` (or a remote
URL) is the cleanest native single-source for shared conventions/AGENTS-style rules on the OpenCode
side — point all three repos' `opencode.json` at the golden repo's files. Mirrors Claude's `@path`
import. The shared target files can be identical for both tools.

---

### 2.5 OpenCode plugins
Source: https://opencode.ai/docs/config/

**What it is (verbatim):**
> "Plugins extend OpenCode with custom tools, hooks, and integrations. Place plugin files in
> `.opencode/plugins/` or `~/.config/opencode/plugins/`. You can also load plugins from npm through
> the `plugin` option."

**Verdict:** OpenCode plugins are JS/TS tool+hook extensions (npm-distributable), NOT a vehicle for
sharing AGENTS.md/skills text the way Claude plugins are. Not a fit for this problem, and they are
NOT interoperable with Claude plugins.

---

### 2.6 Does OpenCode auto-load `.claude/agents/`? — LIKELY NO (primary docs)
Sources: https://opencode.ai/docs/agents/ , https://opencode.ai/docs/skills/

The OpenCode agents doc lists markdown agent locations as ONLY:
> "Global: `~/.config/opencode/agents/`; Per-project: `.opencode/agents/`."
It does NOT list `.claude/agents/` as a fallback. The skills doc explicitly enumerates Claude-compat
paths for *skills* but the agents doc has no equivalent for agents. An earlier WebSearch snippet
claimed OpenCode "loads .claude/agents" — I could NOT confirm that from any primary doc and the agents
doc contradicts it. **Treat "OpenCode reads `.claude/agents/`" as UNVERIFIED / probably FALSE.**

Implication: Claude subagents (`.claude/agents/`) and OpenCode agents (`.opencode/agents/`) are NOT
natively shared. The repos' `.opencode/agents/` cannot be single-sourced via a Claude mechanism, and
vice-versa, except by symlink/submodule on the filesystem (not a tool feature).

---

## RANKED SHORTLIST — most promising NATIVE single-source mechanisms

1. **`~/.claude/skills/` (Personal scope) — covers skills for BOTH tools.** Claude reads it (Personal
   scope, all projects); OpenCode reads it (global Claude-compatible). One SKILL.md, both tools, zero
   copies. Confirmed since OpenCode v1.0.210. Caveat: machine-global (not per-repo opt-in); unique
   names required; OpenCode invokes via `skill` tool.

2. **Shared `AGENTS.md` file + per-repo `CLAUDE.md` `@import` shim — covers workflow rules for BOTH.**
   OpenCode reads AGENTS.md natively; Claude reads a 1-line `CLAUDE.md` that does `@/abs/path/AGENTS.md`.
   Plus OpenCode `instructions: [globs/URLs]` can point at the same golden files. One source, both tools.

3. **Claude plugin (in a local/git marketplace) — covers skills + agents + commands for Claude across
   all repos, versioned, auto-updatable.** Best Claude-side bundling. Downsides: OpenCode ignores it;
   skill names become namespaced (`/plugin:skill`).

4. **`--add-dir <golden>` — skills-only, Claude-only, no-copy.** Cheap to adopt (skills exception
   auto-loads), but must pass the flag each launch and excludes agents/commands; CLAUDE.md needs an env var.

5. **`.claude/rules/` symlinks + `~/.claude/rules/`, and OpenCode `instructions` globs — covers
   `ai-docs/`/conventions.** Filesystem symlinks/submodules are the only way to truly single-source the
   per-repo `.opencode/agents/` since no tool feature shares agents across both Claude and OpenCode.

**Bottom line for THIS problem:** No single native feature covers all four asset types across both
tools. The best native combo is: (1) `~/.claude/skills/` for skills [both tools], (2) one golden
`AGENTS.md` + Claude `@import` shim + OpenCode `instructions` for rules/conventions [both tools], and
either a Claude plugin OR `--add-dir` for the Claude-only extras. The `.opencode/agents/` <-> Claude
agents gap has no native bridge and needs symlinks/submodules.

## UNVERIFIED claims (could not confirm from primary sources)
- Exact personal-vs-project skill tiebreak wording (came from a WebSearch snippet, not the page body
  I captured). Plugin namespacing + skill-beats-command ARE verified.
- The exact env var NAMES to disable OpenCode's Claude-compat loading (rules doc references them but
  the values did not render in the cleaned fetch; changelog confirms the capability exists since v1.1.7).
- "OpenCode auto-loads `.claude/agents/`" — NOT in primary docs; agents doc lists only
  `~/.config/opencode/agents/` and `.opencode/agents/`. Treat as false unless proven otherwise.
