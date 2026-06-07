# openspec-scaffold

Reusable project scaffold for OpenSpec projects, worked by **OpenCode (DeepSeek/GLM) and/or Claude Code**.

Copy this repo to start a new project. Fill in the two placeholder files, run the per-project setup steps, and you're ready to use the full workflow with the apply-delegation and behavioral-verify hardening already in place.

---

## What's included

| File | Purpose |
|---|---|
| `AGENTS.md` | Project instructions loaded by OpenCode at session start |
| `STATUS.md` | Live project status — what's done, what's next |
| `ai-docs/decisions.md` | Durable architectural decisions and rationale |
| `ai-docs/open-questions.md` | Unresolved questions and user-action items |
| `openspec/config.yaml` | OpenSpec project config — injected into every artifact prompt; carries the `tasks` (delegate apply), `verify` (behavioral review), and `archive` (reconcile-as-handoff) rules |
| `.opencode/agents/apply-executor.md` | DeepSeek V4 Flash subagent for the apply phase (OpenCode) |
| `.claude/agents/apply-executor.md` | Sonnet subagent for the apply phase (Claude Code) |
| `scripts/fetch_clean.py` | Token-efficient web content fetcher for research |
| `scripts/harden_opsx.py` | Re-applies the propose/apply/verify hardening to the generated skill files (run after `openspec init`/`update`) |
| `dev-requirements.txt` | Python deps for fetch_clean.py |

---

## One-time global setup

Do this once on a new machine. Skip if already done.

### 1. Install tools

```bash
npm install -g @fission-ai/openspec@latest
# OpenCode: https://opencode.ai
```

> **Version note.** This scaffold was built and tested against **OpenSpec 1.4.1**.
> `scripts/harden_opsx.py` (Step 6) patches the *generated* `/opsx` command files, so it
> is coupled to that template layout. If you install a newer OpenSpec, the harden script
> will print a version-mismatch warning — re-check it before relying on the output (see
> the note at the top of `scripts/harden_opsx.py`).

### 2. Set DeepSeek V4 Pro as the default model

Edit `~/.config/opencode/opencode.jsonc`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "deepseek/deepseek-v4-pro"
}
```

### 3. Create the global GLM 5.1 reflection agent

Create `~/.config/opencode/agents/openspec-reviewer.md`:

```markdown
---
name: openspec-reviewer
description: OpenSpec Change Reviewer — called after proposal artifacts are created and before implementation begins. Reviews proposal.md, design.md, tasks.md, and specs for substantive defects that would cause implementation failure or rework. Invoked by the primary agent between the propose and apply phases.
mode: subagent
model: zai/glm-5.1
permission:
  read: allow
  edit: deny
  bash: deny
  glob: allow
  grep: allow
  list: allow
  webfetch: deny
  websearch: deny
---

You are an **OpenSpec Change Reviewer** — a critical thinker and auditor focused on substance.

Your job is to review every artifact in an OpenSpec change before it moves to implementation,
and find the issues that would actually cause implementation failure or rework.

## Core Principle

**Substantive defects** = issues that cause implementation to go in the wrong direction,
miss critical scenarios, create contradictions, or make acceptance impossible.

**Formatting issues** = style or wording differences that don't affect implementation quality.

Find the former. Mention the latter only as optional suggestions at the end.

## Severity levels

- 🔴 **Blocking** — must be fixed before moving on
- 🟡 **Should Fix** — important but not a hard blocker
- 💡 **Suggestion** — optional improvement

## Output format

\`\`\`
## Review Round N — [artifact reviewed]

### Summary
One paragraph: overall quality and the most important concern.

### 🔴 Blocking Issues
[numbered list — or "None"]

### 🟡 Should Fix
[numbered list — or "None"]

### 💡 Suggestions
[numbered list — or "None"]

### Verdict
PASS — ready to freeze and move to next artifact
  or
NEEDS REVISION — address 🔴 issues before proceeding
\`\`\`

## Rules

- **Constructive and strict.** For every issue explain WHY it would cause rework.
- **Specific.** Point to exact file locations, section names, task numbers.
- **Context-aware.** Evaluate against existing specs in `openspec/specs/`.
- **Read-only.** Never modify files. You surface problems; the primary agent fixes them.
- **No rubber-stamping.** No vague feedback. No jumping to solutions.
```

### 4. Connect providers in OpenCode

Open OpenCode (`opencode .`) and run:

```
/connect   → select DeepSeek    → paste API key from platform.deepseek.com
/connect   → select ZhipuAI     → paste API key from bigmodel.cn
```

### 5. (Claude Code) No extra global setup

If you work the project with Claude Code instead of — or alongside — OpenCode, there is
**no global model config to set**; Claude Code uses its own models. The project files
cover the Claude path: `AGENTS.md` + `openspec/config.yaml` + `.claude/agents/apply-executor.md`
(Sonnet executor). The GLM `@openspec-reviewer` is **not** available under Claude Code —
on the Claude path, the primary self-reviews each artifact with genuine rigor (actively
hunting for defects, not rubber-stamping) before proceeding to the next.

---

## Per-project setup

### Step 1 — Copy this scaffold

```bash
cp -r ~/Projects/openspec-scaffold ~/Projects/your-project-name
cd ~/Projects/your-project-name
rm -rf .git && git init
```

### Step 2 — Fill in the two placeholder files

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

### Step 4 — Initialise OpenSpec

```bash
openspec init
# When prompted: select BOTH Claude Code and OpenCode (this scaffold supports both)
# This generates the /opsx:* skills for each selected tool
```

### Step 5 — Enable the expanded workflow (adds /opsx:verify)

```bash
openspec config profile
# Select: Workflows only → enable verify (and bulk-archive, onboard if wanted)

openspec update
# Regenerates the skill set with the full lineup
```

### Step 6 — Harden the generated skills

`openspec init`/`update` regenerate the skill files from the **stock** OpenSpec
templates, which do not enforce this scaffold's apply-delegation and behavioral-verify
rules. Re-apply them (idempotent — safe to re-run after every `openspec update`):

```bash
python scripts/harden_opsx.py
```

This injects three blocks into the generated Claude Code command + skill files:
- **propose**: sequential-creation mandate (finalize each artifact before starting the next)
  and concrete-fix guidance (decisions must be specific choices, not paraphrases of the problem)
- **verify**: mandatory behavioral-review preamble (read diffs, re-run full suite, eyeball
  real output, re-delegate fixes)
- **apply**: delegation override (delegate to the apply-executor; don't implement inline)

The same apply/verify rules also live in `openspec/config.yaml` (which reaches OpenCode at
runtime), so this step is belt-and-suspenders for the generated skill files.

> Pinned to **OpenSpec 1.4.1** — the script warns at runtime if your installed version
> differs, since the injection depends on the generated file layout.

That's it. Open your agent in the project directory and start with `/opsx:explore` or `/opsx:propose`.

---

## Workflow reference

| Command | When to use |
|---|---|
| `/opsx:explore` | Research and scope a change before proposing |
| `/opsx:propose <name>` | Create and review artifacts (GLM reviewer runs automatically) |
| `/opsx:apply` | Implement — delegates to the apply-executor (Sonnet subagent under Claude Code; `@apply-executor`/DeepSeek Flash under OpenCode) |
| `/opsx:verify` | The orchestrator's own behavioral review — re-run suite, eyeball real output, re-delegate fixes (not a rubber-stamp) |
| `/opsx:archive` | Close a finished change |
| `openspec status` | See status of all open changes |
| `openspec status --change <name>` | Status of a specific change |

### Model roles

**OpenCode path:**

| Model | Role |
|---|---|
| DeepSeek V4 Pro | Primary agent — explore, propose, verify, archive |
| GLM 5.1 | `@openspec-reviewer` — reviews proposal artifacts (called automatically during propose) |
| DeepSeek V4 Flash | `@apply-executor` — implements tasks (called automatically during apply) |

**Claude Code path:**

| Model | Role |
|---|---|
| Opus / Sonnet (your choice) | Primary agent — explore, propose, verify, archive; self-reviews each artifact with rigorous defect-hunting before finalizing (GLM reviewer unavailable here) |
| Sonnet | apply-executor (`.claude/agents/apply-executor.md`) — implements tasks during apply |

### Context and sessions

- The primary session (DeepSeek V4 Pro) runs continuously across all `/opsx:*` commands.
- Each `@openspec-reviewer` call is an isolated child session — it starts fresh, reads the artifact files, returns its review, and exits.
- Each `/opsx:apply` delegation is an isolated child session — it reads the frozen artifacts, implements, and returns a report.
- Because the artifacts are on disk, you can safely split across sessions: end a session after `/opsx:propose` and start a fresh one for `/opsx:apply` without losing anything.
- **Write discipline:** during a change, write its `openspec/changes/<name>/` files freely (check off `tasks.md`, jot `notes.md`). Do **not** edit `STATUS.md` / `ai-docs/` mid-change — that keeps the working context small.
- **Archive = handoff:** `/opsx:archive` is where `STATUS.md` + `ai-docs/` get reconciled from the change dir. Run it in a **fresh session seeded from the change dir**, not the bloated working session — that keeps the multi-file reconciliation cheap.

### Key files per change

```
openspec/changes/<name>/
  explore-brief.md   ← context from /opsx:explore (prevents context loss)
  proposal.md        ← frozen after reviewer PASS
  design.md          ← frozen after reviewer PASS
  tasks.md           ← frozen after reviewer PASS
  notes.md           ← change-local scratch: decisions, rejected approaches (replaces session-notes)
  review-log.md      ← append-only log of all review rounds
```

---

## What NOT to customise per-project

The following live in `~/.config/opencode/` and are shared across all projects. Do not copy them into individual project repos:

- `opencode.jsonc` — default model
- `agents/openspec-reviewer.md` — GLM 5.1 reflection agent
- `AGENTS.md` — global fallback workflow instructions (project AGENTS.md takes precedence)
