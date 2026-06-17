# Tier-2 edit plan — openspec-scaffold (APPLIED 2026-06-14, commit `0aa1088`)

**STATUS: APPLIED in scaffold commit `0aa1088`** (main, unpushed). Applied via
`opencode run` + deepseek-v4-pro; the orchestrator reviewed the diff before commit. Landed:
**T2-5** + **T2-7** (AGENTS.md) and **T2-8 TodoWrite** (propose skill). **Dropped:** T2-1/2/3/4/6.
**Deferred:** T2-8 AskUserQuestion (8 sites). Dossiered against the *actual* current scaffold text
(AGENTS.md + the apply/archive/propose skills, read in full this session). Same discipline as Tier-1:
form an independent verdict per candidate, do **not** trust `_SYNTHESIS.md` recs at face value.

**Headline of the review:** of the **7** Tier-2 candidates (T2-1..T2-7), **only 2 survive a
real-text check** (T2-5, T2-7) — the other 5 are redundant, ceremony, or constraint-violating
once read against the file. One **new finding (T2-8)** surfaced during the dossier (incomplete
harness-neutralization — same class as Tier-1 A1). This mirrors Tier-1, where ~half the
candidates fell away on inspection, and is consistent with the program headline: *the scaffold
is ahead of industry; this is polish, not catch-up.*

Verdict legend: **APPLY** (solid, source-traceable, constraint-compatible) · **DROP** (redundant /
ceremony / anchor-wrong) · **HOLD** (depends on an open decision).

| # | Candidate (source) | Verdict |
|---|--------------------|---------|
| T2-1 | retry tight-brief *template* in apply (B-R2) | **DROP** — synthesis claim is false |
| T2-2 | named executor-brief structure (B-R3) | **DROP** — already concrete; not a project rule |
| T2-3 | "write non-obvious choices to decisions.md at archive" + seed (D-R2) | **DROP** — fully redundant |
| T2-4 | context-budget trigger heuristic (D-R1) | **DROP** — covered; not agent-neutral |
| T2-5 | session-resume staleness check (D-R3) | **APPLY** — genuine gap |
| T2-6 | change-tier classification in propose (A-R3) | **DROP** — ceremony or gate-relaxing |
| T2-7 | clarify `.claude/skills/` exempt from no-harness-state rule (found last session) | **APPLY** — real contradiction |
| T2-8 | **NEW** — finish harness-neutral wording (TodoWrite / AskUserQuestion) | **APPLY** TodoWrite; operator-call on AskUserQuestion |

---

## APPLY

### T2-5 — Session-resume staleness check — `AGENTS.md` MANDATORY preamble (~:12-14)
**Why it's a genuine gap:** the preamble (`:6-10`) mandates *reading* `STATUS.md` on startup, and
the override rule (`:12-14`) says *if the files conflict with the codebase, update them*. But nothing
tells the agent to **detect** that `STATUS.md` has fallen behind what actually happened — the exact
"stale context injection" failure D-R3 names. (I performed this very check at session start —
`git log` vs. the handoff's claimed commits — so it is operator-validated practice, not just theory.)

Append to the override paragraph (after `:14`, inside the blockquote):
```
> On resume specifically, sanity-check freshness before trusting `STATUS.md`: run
> `git log --oneline -5` and confirm `STATUS.md` reflects those latest commits — if it
> lags, reconcile it to reality first.
```
**Source:** D-R3 + operator practice. **Constraint:** agent-neutral (`git log` works under both) ✓;
no autonomy/phase-gate change ✓. Operationalizes an existing rule rather than adding a new one.

### T2-7 — `.claude/skills/` is exempt from the "no harness-state" rule — `AGENTS.md` cross-agent block (:28-34)
**Why it's a real contradiction:** `:28-31` says *do not rely on … `.claude/` … directories*, but the
architecture deliberately **does** rely on `.claude/skills/`, `.claude/agents/`, and `.opencode/agents/`
— and `ai-docs/decisions.md:21-25` (the Tier-1 seed) records that reliance as intended (OpenCode
cross-loads `.claude/skills/`). A future agent reading `:30` literally could "fix" the architecture by
distrusting the skills dir. Internal inconsistency in the golden source.

**Minimal fix (my lean): leave the load-bearing ban sentence untouched; add an explicit exception
line** after the two bullets (before `Maintain this discipline…` on `:34`):
```
**Exception — shared workflow definitions, not private state.** The tracked
`.claude/skills/`, `.claude/agents/`, and `.opencode/agents/` directories ARE relied
upon by design: they are version-controlled and loaded by *both* harnesses (OpenCode
auto-discovers `.claude/skills/` — see `ai-docs/decisions.md`). The rule above bans
harness-*private* state/memory, not these shared, tracked definitions.
```
**Source:** internal — AGENTS.md vs. `ai-docs/decisions.md:21-25` + the verified cross-load.
**Constraint:** ✓ (clarifies, does not weaken; the "no harness-private state" rule stands).
**Alt (only if you prefer):** also narrow the bullet's parenthetical from the whole `.claude/` to the
real offenders (`harness/session memory, CLAUDE.md, scratch config`). I lean *don't* — touching the
load-bearing sentence is higher-risk than a clean rule-plus-exception.

### T2-8 (NEW this session) — finish the harness-neutralization Tier-1 A1 started
Tier-1 A1 neutralized only the "**Skill** tool" line. The dossier shows two more Claude-specific tool
names left in **shared** (non-platform-branched) skill steps — the same coupling A1 fixed. (The
`Agent`/`Task`-tool mentions are correctly inside `### If you are Claude Code` / `### If you are
OpenCode` branches — those are fine.)

- **APPLY — `TodoWrite` (1 site, `openspec-propose/SKILL.md:55`).** Shared step, zero UX tradeoff.
  Current: `Use the **TodoWrite tool** to track progress through the artifacts.`
  Proposed: `Track progress through the artifacts with a running checklist (your harness's todo tool, if it has one).`
  **Source:** same as A1. **Constraint:** ✓ wording-only, agent-neutral.

- **OPERATOR CALL — `AskUserQuestion` (8 sites: propose:31,207 · apply:32 · archive:37,57,70 ·
  verify:40 · sync-specs:22).** Also Claude-coupled and in shared steps, so strict A1-consistency
  says neutralize. **But** unlike TodoWrite it carries a mild tradeoff: naming `AskUserQuestion`
  nudges Claude toward its *structured multiple-choice picker*; a fully-neutral "ask the user to
  select" loses that nudge. And it's 8 sites of churn. **My lean: leave AskUserQuestion as-is for now**
  (low harm — the OpenCode model reads the intent and prompts anyway; the original authors left these
  shared deliberately). Neutralize only if you want strict harness-symmetry; if so the pattern is
  `ask the user to select the change` (drop the tool name).

---

## DROP (with reasons)

### T2-1 — retry tight-brief *template* in apply — **DROP (synthesis claim is false)**
`_SYNTHESIS` said "skill says 'tight brief' but **gives none**." Not true: `apply:167-173` already
specifies the three tight-brief elements inline — *(1) name the exact files to read, (2) front-load
the facts you've already verified as given, (3) forbid codebase re-exploration.* A fill-in template
would be copy-paste convenience, not a missing-content fix, and the apply skill is already long/dense.
**Drop** (or, if you specifically want a paste-able skeleton, a 4-line example — low value; say so).

### T2-2 — named executor-brief structure — **DROP**
The briefs already exist and are concrete (`apply:98-103`, `archive:138-147`). Their completion-report
fields are **deliberately different** per operation (apply reports "what was implemented / assumed
external-API behavior"; archive reports "what was moved / specs synced / docs reconciled") — so a
single rigid "required-fields" schema wouldn't even fit, and would add an abstraction layer that must
stay in sync with two instances. Also not traceable to an established project rule (B-R3's source is
OpenAI's *typed/programmatic* handoffs, which don't map to free-text `opencode run` briefs).

### T2-3 — "write non-obvious choices to decisions.md at archive" + seed — **DROP (fully redundant)**
The capture→reconcile pipeline is already specified end-to-end: `AGENTS.md:99` says append
*decisions / rejected approaches / discoveries* to `notes.md` continuously; `archive:144` reconciles
the project docs from `notes.md`/`proposal.md`/`design.md`; `archive:238-240` requires each
`decisions.md` entry carry "the why … with alternatives rejected." And Tier-1 already **seeded**
`decisions.md` with 3 example entries. Nothing genuinely missing. (The handoff's NB was right.)

### T2-4 — context-budget trigger heuristic — **DROP (covered + not agent-neutral)**
The principle is already present: delegate *independent* work to subagents (`AGENTS.md:127-134`),
"decompose long jobs into steps that each complete and return … granularity buys resumability"
(`:121-126`), and the load-bearing reconcile-in-fresh-context rule (`:102-111`). A *quantitative*
context-% trigger is harness-specific (Claude and OpenCode report context differently), so it can't be
made agent-neutral, and it isn't traceable to an established project rule. At most this is one
qualitative line restating "delegate independent work" — not worth bloating the dense Working-process list.

### T2-6 — change-tier classification step in propose — **DROP (ceremony or gate-relaxing)**
A "nominal-only" classification that records a tier but changes nothing is **ceremony**; one that
*acts* on the tier would relax the normal-flow phase gates — violating the operator's hard constraint
#2 (*autonomy/right-sizing stays opt-in*) and the deliberate "full gates in the normal flow" decision
(`_SYNTHESIS:104`). Tiering already lives, gated, in `ai-docs/fast-track-workflow.md`. Keep it there.

---

## Decision points for you
- **D-1 — APPLY T2-5 + T2-7 + T2-8(TodoWrite)?** My recommendation: **yes, all three** — they are
  correctness/clarity fixes (a stale-status guard, an internal-contradiction carve-out, and finishing
  A1's neutralization), each agent-neutral, none touching autonomy or phase gates.
- **D-2 — AskUserQuestion (8 sites): neutralize or leave?** My lean: **leave** (low harm, churn, mild
  Claude-UX cost). Override me if you want strict harness-symmetry.
- **D-3 — confirm the 5 DROPs.** If you disagree with any drop, the fallback is the minimal version
  noted under that item (e.g. a 4-line tight-brief example for T2-1).

## Net change set if you approve my recommendations (D-1 yes, D-2 leave, D-3 drops confirmed)
- `AGENTS.md`: T2-5 (resume staleness line) + T2-7 (exception line) — 2 edits.
- `.claude/skills/openspec-propose/SKILL.md`: T2-8 TodoWrite neutralization — 1 edit.
- **Dropped:** T2-1, T2-2, T2-3, T2-4, T2-6. **Deferred:** T2-8 AskUserQuestion (8 sites).
- One commit to `main`, unpushed.
