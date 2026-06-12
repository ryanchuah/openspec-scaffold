# openspec-scaffold

Reusable project scaffold for OpenSpec projects, worked by **OpenCode (DeepSeek) and/or Claude Code**.

Copy this repo to start a new project. Fill in the placeholder files and you're ready to use the full workflow — the skills, agents, config, and planning dirs all ship ready, with the apply-delegation and behavioral-verify rules already baked into the skills. There is **no skill-generation or hardening step**.

---

## What's included

| File | Purpose |
|---|---|
| `AGENTS.md` | Project instructions loaded by OpenCode at session start |
| `STATUS.md` | Live project status — what's done, what's next |
| `ai-docs/decisions.md` | Durable architectural decisions and rationale |
| `ai-docs/open-questions.md` | Unresolved questions and user-action items |
| `openspec/config.yaml` | OpenSpec project config — injected into every artifact prompt; carries the `tasks` (delegate apply), `verify` (behavioral review), and `archive` (reconcile-as-handoff) rules |
| `openspec/changes/`, `openspec/specs/` | Planning home for in-flight changes and promoted capability specs (ship empty, with `.gitkeep`) |
| `.claude/skills/openspec-*/` | The 8 workflow skills (explore/propose/apply/verify/archive/sync/bulk-archive/onboard) — pre-built and ready; loaded by both Claude Code and OpenCode |
| `.opencode/agents/apply-executor.md` | DeepSeek V4 Flash apply-phase executor (driven via `opencode run`) |
| `.opencode/agents/archive-executor.md` | DeepSeek V4 Pro archive executor — moves change dir, syncs delta specs, reconciles project docs (driven via `opencode run`) |
| `.opencode/agents/openspec-reviewer.md` | DeepSeek V4 Pro reviewer agent — reviews proposal artifacts before implementation (project-local; driven via `opencode run`) |
| `.claude/agents/apply-executor.md` | Sonnet subagent — apply-phase executor fallback under Claude Code |
| `.claude/agents/archive-executor.md` | Sonnet subagent — archive-executor fallback under Claude Code |
| `scripts/fetch_clean.py` | Token-efficient web content fetcher for research |
| `dev-requirements.txt` | Python deps for fetch_clean.py |

> **Note — OpenCode runtime deps are intentionally not shipped.** `.opencode/` carries
> only the agent definitions (`agents/*.md`). The OpenCode runtime artifacts
> (`.opencode/node_modules/`, `package.json`, lockfiles) are **not** committed — they are
> install artifacts that OpenCode regenerates locally. Do not add them to the scaffold. If
> `opencode run --agent …` ever fails to load an agent because of missing deps, install
> them in the project's `.opencode/` locally rather than committing them here.

---

## One-time global setup

Do this once on a new machine. Skip if already done.

### 1. Install tools

```bash
npm install -g @fission-ai/openspec@latest
# OpenCode: https://opencode.ai
```

> **Version note.** The shipped skills were authored against **OpenSpec 1.4.1** CLI
> behavior (artifact templates, `openspec status --json`, `openspec new change`, etc.).
> They are checked-in files — the CLI is used only to drive changes, not to regenerate
> them. Do **not** run `openspec update`/`openspec init` over this repo; that overwrites
> the rich skills with stock templates (see the caveat in per-project setup).

### 2. Set DeepSeek V4 Pro as the default model

Edit `~/.config/opencode/opencode.jsonc`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "deepseek/deepseek-v4-pro"
}
```

### 3. Connect DeepSeek in OpenCode

Open OpenCode (`opencode .`) and run:

```
/connect   → select DeepSeek    → paste API key from platform.deepseek.com
```

### 4. (Claude Code) Also needs OpenCode CLI + DeepSeek

Claude Code drives the apply-executor (`deepseek/deepseek-v4-flash`) and the reviewer
(`deepseek/deepseek-v4-pro`) via `opencode run`. This means the Claude Code path
requires the same prerequisites as the OpenCode path:

- **OpenCode CLI** installed (step 1 above)
- **DeepSeek API key** connected to OpenCode (step 3 above)

No separate global model config is needed for Claude Code itself; the project files
cover the Claude path: `AGENTS.md` + `openspec/config.yaml` + `.claude/agents/apply-executor.md`
(Sonnet, used only as fallback) + `.opencode/agents/openspec-reviewer.md` and
`.opencode/agents/apply-executor.md` (invoked via `opencode run`).

> **Reviewer location.** The `@openspec-reviewer` agent is **project-local** at
> `.opencode/agents/openspec-reviewer.md` (included in this scaffold). There is no
> global reviewer to configure — it travels with each project.

---

## Per-project setup

### Step 1 — Copy this scaffold

```bash
cp -r ~/Projects/openspec-scaffold ~/Projects/your-project-name
cd ~/Projects/your-project-name
rm -rf .git && git init
```

### Step 2 — Fill in the placeholder files

**`AGENTS.md`** — replace every `<FILL: ...>` with project-specific content:
- Heading: project name
- Project context paragraph: what it does, who uses it
- Tech stack line
- Hard constraints (or delete that section)

**`openspec/config.yaml`** — replace every `<FILL: ...>`:
- `Project:` name
- `Purpose:` one or two sentences
- `Tech stack:` language, DB, key libraries
- `Testing:` framework and philosophy

**`STATUS.md`** — update the "Immediate next action" line.

### Step 3 — Set up the Python venv

```bash
python3 -m venv .venv
.venv/bin/pip install -r dev-requirements.txt
```

### Step 4 — That's it

The skills, agents, `openspec/config.yaml`, and the empty `openspec/changes/` +
`openspec/specs/` planning dirs all ship with the scaffold, so there is **nothing to
generate**. Just confirm the OpenSpec CLI is installed (`openspec --version`) and open
your agent in the project directory — say "explore" to research a change, or "propose"
to start one. The apply-delegation and behavioral-verify rules live directly in the
skills (`.claude/skills/`) and in `openspec/config.yaml`, and load automatically.

> ⚠️ **Do NOT run `openspec init` or `openspec update` in this repo.** Those regenerate
> the skill files from **stock** OpenSpec templates and overwrite the rich, pre-built
> skills this scaffold ships (the detailed `opencode run` delegation, the live-probe and
> behavioral-verify procedures, the failure ladders — all of which live in the skill
> bodies). If you ever run them by accident, restore the skills with
> `git checkout .claude/skills`. The CLI's *change* commands (`openspec new change`,
> `openspec status`, `openspec archive`, `openspec validate`) are safe — they operate on
> `openspec/`, not the skill files.

---

## Workflow reference

| Invocation | When to use |
|---|---|
| "explore \<topic\>" | Research and scope a change before proposing |
| "propose \<name\>" | Create and review artifacts (reviewer runs automatically) |
| "apply \<name\>" | Implement — delegates to the apply-executor (deepseek-v4-flash via `opencode run` under Claude Code; `@apply-executor`/DeepSeek Flash under OpenCode; Sonnet subagent as fallback) |
| "verify \<name\>" | The orchestrator's own behavioral review — re-run suite, eyeball real output, re-delegate fixes (not a rubber-stamp) |
| "archive \<name\>" | Close a finished change |
| `openspec status` | See status of all open changes |
| `openspec status --change <name>` | Status of a specific change |

### Model roles

**OpenCode path:**

| Model | Role |
|---|---|
| DeepSeek V4 Pro | Primary agent — explore, propose, verify, archive |
| DeepSeek V4 Pro (project-local `@openspec-reviewer`) | Reviewer — reviews proposal artifacts (called automatically during propose) |
| DeepSeek V4 Flash | `@apply-executor` — implements tasks (called automatically during apply) |
| DeepSeek V4 Pro (`@archive-executor`) | Archive executor — moves change dir, syncs delta specs, reconciles project docs (called automatically during archive; primary reviews and commits) |

**Claude Code path:**

| Model | Role |
|---|---|
| Opus / Sonnet (your choice) | Primary agent — explore, propose, verify, archive |
| DeepSeek V4 Pro (via `opencode run`) | `@openspec-reviewer` — reviews proposal artifacts (project-local at `.opencode/agents/openspec-reviewer.md`; called automatically during propose) |
| DeepSeek V4 Flash (via `opencode run`) | apply-executor — implements tasks during apply (primary path) |
| DeepSeek V4 Pro (via `opencode run`) | archive-executor — moves change dir, syncs delta specs, reconciles project docs during archive (primary path; primary reviews and commits) |
| Sonnet | apply-executor fallback and verify fix-executor fallback (`.claude/agents/apply-executor.md`); archive-executor fallback (`.claude/agents/archive-executor.md`) |

### Context and sessions

- The primary session runs continuously across all phases (explore → propose → verify → archive).
- Each `@openspec-reviewer` call is an isolated child session — it starts fresh, reads the artifact files, returns its review, and exits.
- Each apply delegation is an isolated child session — it reads the frozen artifacts, implements, and returns a report.
- Because the artifacts are on disk, you can safely split across sessions: end a session after propose and start a fresh one for apply without losing anything.
- **Write discipline:** during a change, write its `openspec/changes/<name>/` files freely (check off `tasks.md`, jot `notes.md`). Do **not** edit `STATUS.md` / `ai-docs/` mid-change — that keeps the working context small.
- **Archive = handoff:** archive is where `STATUS.md` + `ai-docs/` get reconciled from the change dir. Delegated to a `deepseek/deepseek-v4-pro` archive-executor (fresh context; Claude via `opencode run`, OpenCode via a subagent), then reviewed and committed by the primary — that keeps the multi-file reconciliation cheap.

### Key files per change

```
openspec/changes/<name>/
  explore-brief.md   ← context from explore (prevents context loss)
  proposal.md        ← frozen after reviewer PASS
  design.md          ← frozen after reviewer PASS
  tasks.md           ← frozen after reviewer PASS
  notes.md           ← change-local scratch: decisions, rejected approaches
  review-log.md      ← append-only log of all review rounds
```

---

## What NOT to customise per-project

The following live in `~/.config/opencode/` and are shared across all projects. Do not copy them into individual project repos:

- `opencode.jsonc` — default model
- `AGENTS.md` — global fallback workflow instructions (project AGENTS.md takes precedence)

> **Note:** The `@openspec-reviewer` agent is **project-local** (`.opencode/agents/openspec-reviewer.md`
> in this scaffold) — it belongs in each project repo and does not go in `~/.config/opencode/`.
