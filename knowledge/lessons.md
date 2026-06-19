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

**Per-deliverable independent review for info-loss-sensitive work.** For cross-repo doc migrations, file moves, or any change where accidental deletion or buried-info counts as data loss, run an independent `deepseek-v4-pro` review on EACH deliverable individually (not batched). Even a mechanical, low-risk task gets its own pro pass — self-review's blind spots are real and per-deliverable review localizes any defect. Also delegate bulk reads/classification to subagents to keep the orchestrator context from filling up, then apply your own judgment to their reports. Gate each deliverable behind: (1) a byte-integrity-gated script where applicable, (2) self-review + independent git-based check, (3) a `deepseek-v4-pro` `openspec-verifier` pass via hardened `opencode run` (assert fallback-count 0, judge VERDICT from disk). Commit per deliverable.

**Prefer battle-tested patterns over bespoke homegrown solutions.** When exploring or designing solutions (especially cross-repo sync, context onboarding, agent-context infra), present options grounded in community-agreed docs/blogs or battle-tested projects — NOT a clever solution invented locally that may or may not scale. Do not be tied to the repo's status quo — discarding existing bespoke machinery in favor of a standard pattern is a valid option. When presenting options, rank/annotate by HOW battle-tested each is (real named projects, official docs, external scar tissue), not just feasibility. Delegate web research to subagents using `scripts/fetch_clean.py` and have them name concrete real-world adopters. The failure mode: `sync_scaffold.py` span-merge is homegrown; its failure modes are ours alone to debug, while a community-standard pattern has external precedent.

---

## 2. Golden-source edit rules

Every change to this scaffold must be **source-traceable** (operator constraint, 2026-06-13):

1. **Established rules only.** Every rule added must point to an existing rule in a project's `AGENTS.md` or memory store. If you can't name the source, drop it or ask. Do NOT invent or extrapolate.

2. **Autonomy stays opt-in.** Never bake "proceed autonomously / batch questions / don't interrupt" defaults into the *normal* workflow. That behavior is operator-told and ephemeral — there is no autonomy doc or mode, by design. The operator explicitly chose "leave interaction guidance as-is."

3. **Respect deliberate prior decisions.** Before reverting or re-adding anything, read the commit body — e.g. `bulk-archive` was removed intentionally. Don't additively sync over a conscious choice.

**Why this matters:** scaffold is upstream for every project; an invented or preference-specific rule propagates everywhere via `sync_scaffold.py` and is hard to walk back.

4. **Single-source restated rules — cite, never re-expand.** Several workflow rules were historically restated 3–5× across the instruction surface, free to drift independently (audit §C2). Each now has ONE canonical home; every other site keeps only its per-context specifics plus a citation. When you edit one of these rules, edit it **only** at its home and leave the citations as citations — never re-expand the rule text at another site (a re-expanded copy is exactly what `sync_scaffold.py` then propagates as drift to all three repos). Each home carries an inline `CANONICAL:` marker.

   **Single-source registry:**

   | Rule | Canonical home |
   |------|----------------|
   | tasks.md = apply-phase only | `openspec/config.yaml` `rules.tasks` (prompt-injected) |
   | model-assignment matrix | `AGENTS.md` `## Roles` |
   | never record test/doc/row counts | `AGENTS.md` (the "Tests green before any commit" bullet) |
   | mock-encoded-idealized-API war-story | `.claude/agents/apply-executor.md` (+ its byte-identical `.opencode` twin) |
   | web-research convention | `openspec/config.yaml` `rules.research` |

---

## 3. Opencode delegation gotchas

**After scaffold→downstream sync, run BOTH gates before committing.** `scripts/sync_scaffold.py --check <repo>` (byte convergence) AND `scripts/sync_scaffold.py --check-refs <repo>` (referential integrity — cited `knowledge/**/*.md` files must exist, and AGENTS.md section-anchor citations must resolve). Require both green before committing the sync. The old single-gate check passed convergence while the cited file was absent downstream — `--check-refs` closes that gap. Before `--check-refs` will pass, seed the per-repo state files that the synced rules cite: `knowledge/questions/INDEX.md`, `knowledge/lessons.md` — these are per-repo and intentionally NOT manifest-synced, so they must exist before the refs gate. Downstream commits touching manifest files use `git commit --no-verify`.

**Briefs MUST live INSIDE the target repo.** Opencode sandboxes file reads to the project dir and auto-rejects external paths:
```
permission requested: external_directory (/tmp/*); auto-rejecting
```
A brief written to `/tmp` is silently unreadable — the run no-ops. Write the brief to an untracked file INSIDE the target repo, reference it by relative path, delete it after.

**Exit 0 ≠ success.** `opencode run` exits 0 even when it did nothing useful (rejected brief, silent agent fallback). Always judge from the actual `git diff` before trusting the run. An empty diff is the signal.

**Deepseek-flash introduces cosmetic collateral.** It can re-indent adjacent table rows, reformat nearby paragraphs, etc. when making targeted edits. The line-by-line diff review is the only catch — fix inline when found.

**For precise golden-source edits:** give deepseek an exact FIND/REPLACE brief (verbatim current text → verbatim replacement, "make ONLY these edits, do not reformat, do not commit"), not a vague description. See `.claude/skills/_shared/delegation-harness.md` for the standard invocation pattern.

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

### Verify workflow before flagging mechanism risk

When a tool's mechanism could cause harm (e.g. `openspec init`/`update` overwriting customized files via plain `writeFile`), do NOT escalate it to a "verified landmine needing a guard" until you've checked: (1) does our actual documented workflow ever invoke the dangerous command? (check `README.md` "Per-project setup", `scripts/sync_scaffold.py`, and whether the repo has the relevant package manager); (2) is the prohibition already documented (README/AGENTS.md)? Only if the workflow genuinely triggers it AND it's undocumented treat it as actionable. State "mechanism real but precluded by workflow" rather than "landmine." The failure mode: the `openspec update` clobber risk was called a landmine and a CI guard was recommended; verification showed new-repo bootstrap is `cp -r` + fill placeholders (no generation), `sync_scaffold.py` is file-copy only (no init/clone), downstream repos have no `package.json`, and `README.md` already bans `openspec init`/`update` twice. The risk was precluded by construction and already documented — the proposed guard was over-engineering.

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

**Resume staleness check — run it before trusting `knowledge/STATUS.md`.** The T2-5 rule (and the AGENTS.md preamble) requires running `git log --oneline -5` and confirming `knowledge/STATUS.md` reflects those commits before acting. This has caught active state divergence — e.g. it caught that `ab96c33` already existed, preventing a duplicate decisions.md entry.

**Hook smoke MUST run from a session rooted in the hook-carrying repo.** Claude Code loads `PreToolUse` hooks once from the project root at startup. A session rooted elsewhere (e.g. a meta-workspace directory) cannot exercise or test the hook even if the hook-carrying repo is a subdirectory. Procedure: `tests/commit-gate-smoke/` + the throwaway-repo recipe.

**`opencode debug skill` must be captured to a file before grepping.** The stream is ~120 KB; piping it directly to grep races the output and returns only a 3–4 skill subset (false negative). Capture to a file, THEN grep.

---

## 7. Industry standards context

The 2026-06 industry-standards research (4 parallel subagents, research artifacts in `knowledge/research/research-industry-standards-2026-06/`) found that **this scaffold was AHEAD of industry** on its quality gates:
- Separate-model pre-implementation review
- Behavioral verify beyond just running tests
- Trust-gated autonomy (strictly opt-in)
- Archive-as-fresh-context (fresh executor with structured change-dir as sole input)

This was a **polish pass, not catch-up**. Applied polish: glob fix, harness-neutral skill wording, "don't fan out cohesive/dependency-laden work" guardrail, resume-staleness check, `.claude/skills/` exception documented. The research also confirmed: opencode ≥1.16 auto-loads `.claude/skills/` (no duplication needed); deepseek multi-turn fallback bug was fixed in opencode v1.14.24 (not a live issue).

When evaluating future "industry best practice" claims: verify the claim against real docs before accepting it as a scaffold change. The pattern of confident-but-wrong subagent outputs (§1) applies to research as much as code.
