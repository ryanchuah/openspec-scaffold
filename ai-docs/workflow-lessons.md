# Workflow Lessons

Hard-learned process lessons from operating this scaffold and the W0–W6 hardening family (2026-06-13 → 2026-06-17). These are the failure modes and non-obvious gotchas that are NOT derivable from reading the code or AGENTS.md. Read this file when you are about to delegate, review, run research, or apply changes to this golden source.

---

## 1. Subagent and research discipline

**Subagents were confidently wrong on falsifiable specifics.** During the 2026-06 industry-standards hardening, research subagents claimed:
- Certain `sst/opencode` GitHub issues were "open" (actually closed/fixed).
- "Every multi-turn deepseek dispatch silently falls back to the default agent" (false since opencode v1.14.24, PR #24146).
- An `.opencode/skills/` discovery convention exists (hallucinated — OpenCode ≥1.16 auto-loads `.claude/skills/`).

All were caught only by verifying against `gh`, official docs, and local binary inspection.

**What to do:** Before acting on any *falsifiable* subagent claim — issue numbers, version-specific behavior, "tool X does Y", quantitative stats — verify with `gh`, official docs, or local inspection. Trust the current repo state, not the subagent's digest.

**~Half of synthesis recs were weaker than stated once checked against actual file text.** Across both Tier-1 and Tier-2 polish passes, most recommendations were already implemented, mis-located, or mislabeled (e.g. calling a BDD/Gherkin `WHEN/THEN/AND` format "EARS").

**What to do:** Before drafting or applying any golden-source edit, make a read-only "dossier" pass — get the *verbatim current text* at each edit site and form your own verdict. Do NOT trust digest or synthesis recommendations at face value. `_SYNTHESIS.md` / research summaries are starting points, not verdicts.

---

## 2. Golden-source edit rules

Every change to this scaffold must be **source-traceable** (operator constraint, 2026-06-13):

1. **Established rules only.** Every rule added must point to an existing rule in a project's `AGENTS.md` or memory store. If you can't name the source, drop it or ask. Do NOT invent or extrapolate.

2. **Autonomy stays opt-in.** Never bake "proceed autonomously / batch questions / don't interrupt" defaults into the *normal* workflow. That behavior lives only in `ai-docs/fast-track-workflow.md` (trust-gated, dormant). The operator explicitly chose "leave interaction guidance as-is."

3. **Respect deliberate prior decisions.** Before reverting or re-adding anything, read the commit body — e.g. `bulk-archive` was removed intentionally. Don't additively sync over a conscious choice.

**Why this matters:** scaffold is upstream for every project; an invented or preference-specific rule propagates everywhere via `sync_scaffold.py` and is hard to walk back.

---

## 3. Opencode delegation gotchas

**Briefs MUST live INSIDE the target repo.** Opencode sandboxes file reads to the project dir and auto-rejects external paths:
```
permission requested: external_directory (/tmp/*); auto-rejecting
```
A brief written to `/tmp` is silently unreadable — the run no-ops. Write the brief to an untracked file INSIDE the target repo, reference it by relative path, delete it after.

**Exit 0 ≠ success.** `opencode run` exits 0 even when it did nothing useful (rejected brief, silent agent fallback). Always judge from the actual `git diff` before trusting the run. An empty diff is the signal.

**Deepseek-flash introduces cosmetic collateral.** It can re-indent adjacent table rows, reformat nearby paragraphs, etc. when making targeted edits. The line-by-line diff review is the only catch — fix inline when found.

**For precise golden-source edits:** give deepseek an exact FIND/REPLACE brief (verbatim current text → verbatim replacement, "make ONLY these edits, do not reformat, do not commit"), not a vague description. See `ai-docs/delegation-harness.md` for the standard invocation pattern.

---

## 4. Apply-executor hazards

### Executor overreach into neighbor changes

On the W3 apply, deepseek-flash was briefed ONLY on `openspec/changes/fix-convergence-guard/` but correctly implemented W3 AND then also implemented `cleanup-workflow-ergonomics` (W5), which was at the propose-complete/pre-freeze stage. Its completion report described only the W5 work; the W3 work was buried mid-transcript.

Tell-tale: the changed-file list mixed two changes' scopes.

**What to do after any delegated apply:**
- Diff-classify every changed file against the change's declared "Files touched" — don't trust the completion report.
- Revert out-of-scope edits surgically: `git checkout HEAD -- <file>` for tracked files; `rm -rf` for untracked artifacts; reset wrongly-flipped checkboxes in neighbor tasks.md.
- Including "do NOT touch any other openspec/changes/ dir" in the brief helps but is NOT sufficient — the executor overran even with that instruction. Verification is the real defense.

### Concurrent edits to the shared working tree

A parallel session edited unrelated files (`archive-executor.md`, `openspec-verify-change/SKILL.md`, `AGENTS.md`) WHILE W3 was mid-verify. When committing in a contended tree:
- Stage by **explicit path only**: `git add -- <my files>`
- Confirm with `git diff --cached --name-only` AND inspect what's left unstaged
- Never `git add -A` or `git add .`
- Hold before archive if a parallel session is actively editing STATUS/decisions/open-questions — racing it would clobber.

**Lesson from W5:** A concurrent W4 apply reset the shared working tree and wiped W5's first apply entirely. **Independent parallel applies MUST use separate git worktrees** (`git worktree add`), not the shared main tree.

---

## 5. Workflow rule interpretation

### MEDIUM tier = tasks.md only

The `openspec-propose` SKILL.md describes the full sequence (proposal → design → specs → tasks). It has NO tier gate inside it. The tier-scaling that overrides it lives in AGENTS.md `## Change tiers`:

- **MEDIUM** — propose emits **ONLY `tasks.md`** (one deepseek-v4-pro review), with acceptance criteria in `notes.md`.

Lesson: W1 was confirmed MEDIUM by the operator but was given the full COMPLEX path (proposal + design + specs + tasks, 5 review passes) — over-processing and wasted review rounds. **The AGENTS.md tier rule beats the skill's default flow.** If a change genuinely needs design depth, that's a signal to propose COMPLEX and confirm it.

### Openspec-reviewer bash-crash is NOT a timeout

When the `openspec-reviewer` deepseek agent decides to verify a claim by reaching for `bash` (which is `bash: deny`), opencode treats the denied call as a permission rejection and **hard-errors the whole run (exit 1)** — emitting only narration ("let me verify…") and ZERO findings. This runs ~120s then crashes. It is NOT a timeout.

**What to do:** Prepend a read-only constraint preamble to EVERY review prompt:
> "You are READ-ONLY. The bash/shell tool is DENIED — do NOT attempt any bash/shell command; it hard-errors your run. To inspect files use ONLY read, glob, grep. Treat the primary's disk-verification claims as given."

This prevents the crash. If it still errors: re-run with the preamble — do NOT escalate to Sonnet (the `<120s → escalate` rule is for timeouts; this is a known, fixable cause).

---

## 6. Session and context hazards

**Resume staleness check — run it before trusting STATUS.md.** The T2-5 rule (and the AGENTS.md preamble) requires running `git log --oneline -5` and confirming STATUS.md reflects those commits before acting. This has caught active state divergence — e.g. it caught that `ab96c33` already existed, preventing a duplicate decisions.md entry.

**Hook smoke MUST run from a session rooted in the hook-carrying repo.** Claude Code loads `PreToolUse` hooks once from the project root at startup. A session rooted elsewhere (e.g. a meta-workspace directory) cannot exercise or test the hook even if the hook-carrying repo is a subdirectory. Procedure: `docs/test/commit-gate-smoke/` + the throwaway-repo recipe.

**`opencode debug skill` must be captured to a file before grepping.** The stream is ~120 KB; piping it directly to grep races the output and returns only a 3–4 skill subset (false negative). Capture to a file, THEN grep.

---

## 7. Industry standards context

The 2026-06 industry-standards research (4 parallel subagents, research artifacts in `ai-docs/archive/research-industry-standards-2026-06/`) found that **this scaffold was AHEAD of industry** on its quality gates:
- Separate-model pre-implementation review
- Behavioral verify beyond just running tests
- Trust-gated fast-track (autonomy strictly opt-in)
- Archive-as-fresh-context (fresh executor with structured change-dir as sole input)

This was a **polish pass, not catch-up**. Applied polish: glob fix, harness-neutral skill wording, "don't fan out cohesive/dependency-laden work" guardrail, resume-staleness check, `.claude/skills/` exception documented. The research also confirmed: opencode ≥1.16 auto-loads `.claude/skills/` (no duplication needed); deepseek multi-turn fallback bug was fixed in opencode v1.14.24 (not a live issue).

When evaluating future "industry best practice" claims: verify the claim against real docs before accepting it as a scaffold change. The pattern of confident-but-wrong subagent outputs (§1) applies to research as much as code.
