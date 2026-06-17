# Shared brief — Industry-standards comparison for `openspec-scaffold` (2026-06)

> Every research subagent reads this first. It defines the mission, the hard constraints you must
> respect, the required web-research method, and the exact output format. Your per-bucket prompt
> adds only the topic, baseline files, seed sources, and sibling boundaries.

## Mission

`openspec-scaffold` (`~/Projects/openspec-scaffold`) is the **golden source of truth** — a generic,
reusable template for AI-agent coding workflows used across multiple real projects. We are in the
**read-only research phase** of hardening it: compare the scaffold against **current (mid-2026)
industry standards** for agentic AI coding workflows, then (later, separately) apply the best of
those to the scaffold. Today is **2026-06-13**; assume the state of the art has moved since early
2026 — find what is *current*, not just what you already know.

Your job: a rigorous **gap analysis + candidate recommendations** for ONE topic area, written to a
file, for a principal engineer + the operator to review. **You do NOT edit any scaffold file.** The
only file you write is your findings file (path in your per-bucket prompt).

## Stance

Principal engineer: skeptical, detail-oriented, source-driven. Note where the scaffold is **already
at or ahead of** industry standard (do not invent gaps). Note where an industry practice **does not
fit** the scaffold's constraints, and say why. Prefer a few high-confidence, well-sourced findings
over a long shallow list. Cite everything.

## The 5 HARD CONSTRAINTS of the scaffold (use as lenses; flag every recommendation against them)

1. **Agent-neutral / dual-harness.** The scaffold is driven by BOTH Claude Code AND OpenCode/DeepSeek
   agents; every mechanism is mirrored in `.claude/` and `.opencode/`. Any recommendation that relies
   on a Claude-only feature (Anthropic-specific skills, hooks, native memory tool, etc.) must be
   explicitly flagged **"Claude-only — needs an OpenCode-equivalent or is unsuitable for a neutral
   template."** Cross-tool-standard mechanisms (AGENTS.md, MCP) are fine.
2. **All state in tracked, agent-neutral files — NEVER harness/native memory.** Project state lives in
   tracked files (`AGENTS.md`, `ai-docs/`, `openspec/`). Do **not** recommend harness-native memory as
   a state store.
3. **Generic template.** The scaffold uses `<FILL:…>` placeholder markers and is instantiated
   per-project. Recommendations must fit a reusable template, not one project.
4. **Autonomy stays opt-in.** The *normal* workflow keeps explicit phase gates and an "ask when
   genuinely unsure" stance. "Proceed autonomously / batch questions / don't interrupt" lives ONLY in
   a separate, trust-gated `ai-docs/fast-track-workflow.md`. Do **not** recommend baking autonomous
   operation into the default workflow.
5. **Source-traceable.** Every recommendation must cite the concrete industry source (practice + URL)
   it derives from. No hand-waving; if you can't source it, drop it or mark it an open question.

## Required web-research method

- **Discover** current/authoritative sources with the **WebSearch** tool. Target 2025–2026 material.
- **Fetch full page content ONLY via the scaffold's fetcher** (do NOT use WebFetch for full pages; do
  NOT `git clone`). Exact command:
  ```
  /home/pang/Projects/workflow-optimize/.venv/bin/python /home/pang/Projects/openspec-scaffold/scripts/fetch_clean.py "<url>"
  ```
  - Append `--jina-fallback` if a page returns `empty/thin content`.
  - It auto-rewrites GitHub URLs to raw — for GitHub just pass the normal `github.com/...` URL.
  - `WebFetch` is allowed ONLY for a narrow, targeted question on a page you won't otherwise cite.
- **Be targeted** (convention rule c): only fetch a page if you will cite it. Default 40k-char cap is fine.
- **Checkpoint** (convention rule c): write partial findings to your output file AS YOU GO; don't hold
  everything in context. Use the Write tool to create it, Edit/Write to append sections.
- If a fetch keeps failing, record the URL as **inaccessible** — never fabricate its content.

## Scaffold baseline facts (so you don't re-derive them)

- Skills (`.claude/skills/*/SKILL.md`): `openspec-explore`, `-onboard`, `-propose`, `-apply-change`,
  `-verify-change`, `-archive-change`, `-sync-specs`. Mirrored conceptually for OpenCode.
- Agents: `.claude/agents/` + `.opencode/agents/` hold `apply-executor` + `archive-executor`;
  `.opencode/agents/openspec-reviewer.md` is the review agent. Executors are delegated to via
  `opencode run` against cheaper models (e.g. deepseek), with EXIT-file sentinel-polling for
  completion detection.
- `ai-docs/`: `decisions.md`, `open-questions.md`, `improvement-roadmap.md`, `fast-track-workflow.md`,
  `research-fetch-convention.md`.
- `AGENTS.md` (≈179 lines) is the agent-neutral instruction hub; `openspec/config.yaml` (≈55 lines)
  holds change-tier config; `openspec/{changes,specs}/` are empty `.gitkeep` template stubs.

## Output file format

Write to the path in your per-bucket prompt (inside this workspace — NEVER inside the scaffold). Use:

1. **Scope** — what this area covers; its boundary with sibling areas.
2. **Sources consulted** — every URL fetched, each with a 1-line note (what it is + recency/date).
3. **Industry standard (mid-2026)** — concise synthesis of the current state of the art for this area.
4. **Scaffold baseline** — what the scaffold currently does, cited as `file:line`.
5. **Gap table** — rows: `Practice | Status (Present/Partial/Absent/Divergent/Ahead) | Evidence | Assessment`.
6. **Candidate recommendations** — numbered; each with: the change; **Source** (practice + URL);
   **Confidence** (High/Med/Low); **Constraint-compat** (conflicts with any of the 5? Claude-only?);
   **Effort/Risk**. These are CANDIDATES for operator review, NOT decisions.
7. **Already-ahead / doesn't-fit** — where the scaffold already meets/beats standard, and which popular
   practices you deliberately did NOT recommend (and why).
8. **Open questions for the operator.**

## What to return to the orchestrator (your final message)

A TIGHT summary (not the whole file): the 3–6 highest-value candidate recommendations with confidence,
anything where the scaffold is already ahead, and any source you could not access. Keep full detail in
the file.
