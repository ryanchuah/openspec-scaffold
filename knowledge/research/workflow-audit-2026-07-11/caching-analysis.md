# Sub-D: Token economy & prompt caching analysis — openspec-scaffold / extrends / psc-monitor

## 1. Boot-surface table (bytes / est. tokens = bytes/4)

| File | scaffold | extrends | psc-monitor |
|---|---|---|---|
| AGENTS.md | 28,820 B / ~7,205 tok | 29,211 B / ~7,303 tok | 31,473 B / ~7,868 tok |
| knowledge/STATUS.md | 12,001 B / ~3,000 tok | 19,051 B / ~4,763 tok | 9,337 B / ~2,334 tok |
| knowledge/questions/INDEX.md | 3,460 B / ~865 tok | 16,377 B / ~4,094 tok | 17,792 B / ~4,448 tok |
| knowledge/decisions/INDEX.md | 14,874 B / ~3,718 tok | 52,056 B / ~13,014 tok | 28,803 B / ~7,201 tok |
| openspec/config.yaml | 5,858 B / ~1,464 tok | 5,686 B / ~1,422 tok | 6,047 B / ~1,512 tok |
| **TOTAL** | **65,013 B / ~16,253 tok** | **122,381 B / ~30,595 tok** | **93,452 B / ~23,363 tok** |

extrends' boot surface is ~1.9x scaffold's; psc-monitor ~1.4x. Both downstream repos have
outgrown the scaffold's own boot cost, driven mostly by decisions/INDEX.md (extrends 52KB,
psc 28.8KB vs scaffold's 14.9KB) and, for extrends, STATUS.md + questions/INDEX.md too.

Caveat: AGENTS.md's own mandatory-read text scopes decisions/INDEX.md to "entries relevant to
the current task" and questions/INDEX.md to "Active section only" — not full-file. But a single
Read tool call loads the whole file regardless of which part is "mandatory," so the practical
token cost is close to the full-file bytes above unless the agent actively greps/tails instead
of reading the whole file.

### Scaffold-only: skill files (loaded on invocation, NOT part of mandatory boot)

| Skill file | Bytes | ~Tokens |
|---|---|---|
| openspec-verify-change/SKILL.md | 28,438 | 7,110 |
| openspec-propose/SKILL.md | 18,337 | 4,584 |
| openspec-archive-change/SKILL.md | 18,263 | 4,566 |
| openspec-apply-change/SKILL.md | 15,347 | 3,837 |
| openspec-explore/SKILL.md | 14,268 | 3,567 |
| _shared/delegation-harness.md | 6,279 | 1,570 |
| run-audit/SKILL.md | 5,294 | 1,324 |
| knowledge-drift-review/SKILL.md | 5,491 | 1,373 |
| openspec-sync-specs/SKILL.md | 4,926 | 1,232 |
| outstanding-work-review/SKILL.md | 3,998 | 1,000 |
| **Total** | **120,641** | **~30,160** |

Good design already present: the 4 delegating skills (propose/apply/verify/archive) each cite
`_shared/delegation-harness.md` instead of restating the invocation/assert-ran/timeout/EXIT-sentinel
contract 4x — single-sourcing avoided ~4x duplication of that ~6.3KB block.

## 2. Churn since 2026-05-01 (scaffold repo, `git log --oneline --since=2026-05-01 -- <file> | wc -l`)

**Mandatory boot files (ranked):**
| File | Commits |
|---|---|
| AGENTS.md | **32** |
| knowledge/STATUS.md | 24 |
| knowledge/questions/INDEX.md | 18 |
| knowledge/decisions/INDEX.md | 18 |

AGENTS.md is the single highest-churn always-loaded file — edited ~33% more often than STATUS.md
and ~78% more often than either INDEX.md, despite AGENTS.md's own text declaring itself
"stable... edit it only to add durable project context" and explicitly claiming "stability means
this file caches well across sessions" (AGENTS.md line 31-35). The claim and the observed behavior
are in tension.

**Skill files (loaded only on invocation, ranked):**
| File | Commits |
|---|---|
| openspec-verify-change/SKILL.md | 19 |
| openspec-archive-change/SKILL.md | 15 |
| openspec-apply-change/SKILL.md | 12 |
| openspec-propose/SKILL.md | 12 |
| openspec-explore/SKILL.md | 3 |
| openspec-sync-specs/SKILL.md | 2 |
| run-audit/SKILL.md | 2 |
| _shared/delegation-harness.md | 2 |
| knowledge-drift-review/SKILL.md | 1 |
| outstanding-work-review/SKILL.md | 1 |

## 3. OpenCode prompt construction — confirmed from decompiled opencode binary (v1.17.18)

Reverse-engineered `/home/pang/.opencode/bin/opencode` (bun-compiled JS, readable via `strings`).
Two load-bearing facts confirmed directly in the runtime code:

**(a) AGENTS.md IS auto-injected into every opencode session**, fresh, every single `opencode run`
invocation (each is a new process = new session, no continuity). The `InstructionContext` module
walks up from cwd to the project root collecting files literally named `AGENTS.md` (target list
`["AGENTS.md", ...("CLAUDE.md" unless disabled), "CONTEXT.md"]`), reads them, and formats each as
`Instructions from: <path>\n<content>`.

**(b) The request's `system` field is built as `system: [R.info?.system, oH.baseline]`** — i.e. a
two-element array: element 0 is the **selected agent's own system prompt** (the `.opencode/agents/
<name>.md` body, e.g. apply-executor.md), element 1 is a **combined "baseline"** context block that
includes the AGENTS.md instructions (via the same `Instruction.system()`/`combine` pipeline) plus
other built-in system context. Order: **agent-specific prompt first, AGENTS.md-bearing baseline
second**, then the user's turn (the CLI prompt string) follows as the first message.

**Consequence for DeepSeek prefix caching:** the agent-`.md` segment is low-churn (1-19 commits
since May) and forms a genuinely stable, cacheable prefix. But it is immediately followed by the
AGENTS.md-bearing baseline — and AGENTS.md is the highest-churn file in the whole boot surface (32
commits since May 1, roughly one edit every 2 days of active work). Every AGENTS.md edit
invalidates the cached system-prefix for **all 5** opencode agents (apply-executor, archive-executor,
openspec-reviewer, openspec-verifier, explore-flash) simultaneously, until the file stabilizes again.
This is a bigger caching lever than any single per-call prompt string, because it is shared
infrastructure hit by every delegated call, not just one phase.

**Content-relevance mismatch, independent of caching:** AGENTS.md is written entirely from the
*primary orchestrator's* point of view — its own closing section says (verbatim) "your role as
orchestrator/reviewer who runs the OpenSpec lifecycle and **does not implement**" (AGENTS.md
line 392-393). This exact text is injected into the apply-executor's context on every apply call —
an agent whose entire job **is** to implement. ~7,200 tokens of largely orchestrator-scoped content
is paid by every sub-executor call regardless of relevance to that role.

### Per-invocation user-prompt strings — variable content placement (checked against literal skill text)

| Caller | Prompt template (paraphrased, path = literal excerpt) | Variable position |
|---|---|---|
| apply-executor | `"Implement the OpenSpec change in <changeRoot>. Work <changeRoot>/tasks.md sequentially..."` | **word 5** — `<changeRoot>` appears immediately |
| archive-executor | `"Archive the OpenSpec change. changeRoot: <changeRoot>. archivePath: ...` | **word 5** |
| openspec-reviewer | `"Review the artifact at <changeRoot>/<artifact>.md. Also read the explore-brief..."` | **word 4** |
| openspec-verifier (D5, both pro+flash passes) | `"Review the current git diff and changed files; re-run the full test suite via the per-repo command; eyeball one concrete real-output sample; for any external-API surface run the live smoke...; do NOT fix anything; emit a ## Verify Pass — <model> block..."` | **none** — fully fixed string, same every call, references no path (verifier discovers the diff itself via `git diff`) |

Source for the verifier's exact prompt: `openspec/changes/archive/2026-06-16-verify-multimodel-gate/design.md`
§D5 (the live text; `.claude/skills/openspec-verify-change/SKILL.md` only says `"<the fixed verifier
prompt from design D5>"` as a placeholder).

**Finding:** 3 of 4 delegated-call prompt templates put the per-change variable (a path) in the
first handful of words, ahead of ~40-60 words of otherwise byte-identical instruction text. Because
prefix caching only rewards a shared *prefix*, not a shared *suffix* or shared substring, putting the
variable early means the entire remaining (mostly boilerplate) instruction text never gets prefix-
cache credit against any other invocation, even though the words are literally identical across
every apply/archive/review call ever made. The 4th template (verifier) is the exception and is
already optimally shaped for caching — it never inlines a path at all, which is also why it's
reusable byte-for-byte across the pro and flash passes and across every future verify call.

**Fix:** restructure apply/archive/reviewer prompts as `"<fixed instructions in full>... Target: <changeRoot>."` i.e. move the substituted value to the end. Purely mechanical, no behavior change, zero risk to the mandatory-boot-read contract (this is delegated-call construction, not Claude's own boot read).

### Minor/uncertain observation (flagged, not asserted)
The decompiled code sets `providerOptions: { openai: { promptCacheKey: tL } }` where `tL` is derived
from the **session ID**. Since every `opencode run` call creates a fresh session, this cache-routing
hint differs on every invocation. If the provider/routing layer uses this key for cache-shard
locality (as OpenAI's own docs describe `prompt_cache_key`), a different key per call could reduce
warm-cache hit probability even when the underlying token prefix is identical. Could not confirm
whether DeepSeek's own endpoint (vs. an OpenAI-compatible shim) honors this field — flagged as a
secondary factor worth testing empirically (e.g. compare latency/cost of two immediately-successive
`opencode run --agent apply-executor` calls with identical prompts), not asserted as fact.

## 4. Redundant loads

- **No prompt inlines large artifact content** — apply/archive/reviewer/verifier all point at paths
  (`<changeRoot>/tasks.md`, `knowledge/STATUS.md`, etc.) rather than pasting file contents into the
  CLI prompt string. This is good for keeping the *orchestrator's own* context (the string Claude
  constructs and runs via Bash) small — the multi-KB artifact bodies never appear in Claude's own
  transcript, only in the executor's.
- **But because each `opencode run` is a stateless fresh process**, this same design means every
  delegated call independently pays full (uncached) token cost to read the same underlying files via
  its own Read tool calls, with zero cross-call reuse — there is no session continuity to exploit, and
  Read-tool-result content lands mid-conversation at a position that won't line up byte-for-byte across
  separate invocations even when the file content itself is identical. Concretely, over one MEDIUM/
  COMPLEX change's lifecycle: `proposal.md` gets independently re-read by the propose reviewer's
  proposal-round, again referenced (for consistency-checking) by the design-round and the tasks-round,
  again by apply-executor, again by archive-executor — up to ~5 separate full reads across 5 different
  processes, each paying full input-token price. `design.md` similarly gets re-read ~4x (tasks-round,
  design-round, apply-executor, archive-executor).
- **Verify's dual pro+flash passes each independently re-run the full test suite and re-read the
  diff** — this is *intentional* redundancy for independent-model verification, not a mistake; flagged
  for completeness but not a fix candidate (the design doc D6 explicitly wants two independent views).
- **explore-flash sub-delegation is in-process** (spawned via OpenCode's own `task` tool from within
  an already-running agent session, not a new `opencode run` process), so it does not re-pay the
  parent's system-prompt/AGENTS.md cost — this path is efficient and not a redundant-load concern.

## 5. STATUS.md accretion verdict

`scripts/status_lint.py` enforces exactly one rule: `## Latest change` / `## Prior change` sections
are capped at 3 total, each ≤150 words. It explicitly **exempts** 4 headings from any bound:
`current state`, `immediate next action`, `done`, `pointers` (see `EXEMPT_HEADINGS` in the script).

All three repos pass the enforced rule cleanly (`status_lint.py` exits 0 on all three) — every
actual change-entry is comfortably under 150 words (scaffold 136/117/144; extrends 131/129/109;
psc-monitor 92/132/115).

But the **exempt** sections have grown unevenly, because nothing mechanically bounds them:

| Section | scaffold | extrends | psc-monitor |
|---|---|---|---|
| Current state (preamble) | 376 words | 294 words | 373 words (uses a compact status table) |
| Immediate next action | 583 words | **1,645 words** | 233 words |
| Done | — | — | 50 words |
| Pointers | — | — | 87 words |

**Verdict: the cap rule is working exactly as designed for the part it covers, but the accretion
has simply moved to the uncapped sections.** extrends is the clear outlier — its "Immediate next
action" section (nominally "what's the next single step") has become a ~1,645-word chronological
log covering ~10 separate dated items (Session E, B2 labeling, two SMALLs, session-c-field-rendering,
story-grouped-digest, audit-correctness-wave4, the notability-title-probe fix, Session A digest,
the Mon cron confirmation, the accuracy program, the six-slice audit, breadth-unit, S2 corpus,
notability rerank...) stacked with no pruning mechanism, which is exactly the "unbounded accretion
log" pattern the 3-entry cap was built to prevent for change-entries. It just wasn't extended to
this heading. psc-monitor is the best-behaved of the three — its "Immediate next action" stays
tight and its "Current state" uses a status table instead of an ever-growing prose paragraph, which
is a much more token-efficient pattern for state that only flips a few cells over time.

Scaffold itself is in between: "Immediate next action" (583 words) already reads as a running log of
propagation history (extrends sync, psc-monitor sync, scaffold-tooling fix, scanner-provisioning
gaps) rather than a single next step, though far short of extrends' degree.

**This is a real gap in the existing mechanism** (not a new rule to invent) — the same status_lint.py
already has the machinery (word-count + section-cap logic) to bound these sections too; it simply
doesn't apply it to them today.

## 6. Ranked improvements (excludes anything weakening the mandatory-boot-read contract)

1. **Move variable content (changeRoot/paths) to the END of the apply-executor, archive-executor, and
   openspec-reviewer delegated prompt templates**, instructions first. Zero risk, mechanical, restores
   prefix-cache eligibility for the ~40-60 words of boilerplate instruction text that's currently
   byte-identical across every call but never gets cache credit because a variable sits at word 4-5.
   The verifier's D5 prompt is already the right shape — copy its pattern.

2. **Extend `status_lint.py`'s word-budget mechanism to the "Current state" and "Immediate next
   action" headings** (e.g. a generous cap like ≤400/≤300 words, or a WARN-not-FAIL tier so it doesn't
   block on judgment calls) instead of leaving them in `EXEMPT_HEADINGS` unconditionally. This directly
   targets extrends' 1,645-word outlier and would have caught scaffold's own drift in this direction
   before it reached 583 words. Doesn't touch the boot-read contract — the file still gets read in
   full; this just stops it from growing without bound.

3. **Reduce AGENTS.md's churn rate or split it so the auto-injected opencode baseline is less
   frequently invalidated.** AGENTS.md is both (a) the single highest-churn boot file (32 edits since
   May 1 — more than STATUS.md, more than either INDEX.md) and (b) confirmed via decompiled opencode
   to sit in the system-prompt "baseline" segment injected into every one of the 5 opencode agents on
   every call. Every edit resets the cache-prefix for all delegated calls simultaneously, not just
   Claude's own boot read. Concretely: batch related AGENTS.md edits instead of landing them
   incrementally, and audit whether some of what currently lives in AGENTS.md (which churns) could
   move to a separately-cited, less-frequently-touched reference doc while AGENTS.md keeps only the
   genuinely stable orchestration rules its own preamble claims it holds.

4. **Investigate scoping/trimming what opencode sub-executors receive from AGENTS.md.** AGENTS.md is
   written entirely in the primary orchestrator's voice (explicitly: "your role... does not implement")
   and is injected verbatim into the apply-executor, whose entire job is to implement. The
   `.opencode/agents/*.md` bodies already appear reasonably self-contained (they inline the rules they
   need rather than only citing AGENTS.md), which suggests testing whether `OPENCODE_DISABLE_
   PROJECT_CONFIG=1` scoped to just the delegated `opencode run` calls is safe — it would drop the
   ~7,200-token, high-churn, largely-irrelevant AGENTS.md injection for sub-executors and leave only
   the small, low-churn agent-specific prompt as the system prompt. This needs validation (grep each
   `.opencode/agents/*.md` for implicit AGENTS.md dependencies before flipping it) rather than blind
   rollout, but the payoff (cutting ~7,200 tokens of system-prompt off every one of the ~4-6+ delegated
   calls per change, and removing AGENTS.md's churn as a cache-invalidation source for those calls
   entirely) is the largest single number in this analysis.

5. **(Lower confidence / exploratory)** Consider whether the propose reviewer's 3 review rounds could
   share more than they do today — each round is a fresh process that independently re-reads
   proposal.md (and, by round 3, design.md too) with no cross-call caching benefit. This is harder to
   fix without either session continuity (which the harness deliberately avoids, for good
   crash-isolation reasons) or restructuring what gets inlined vs. Read-tool-fetched — flagged as
   worth a deliberate design discussion, not a mechanical fix like #1.

None of these require reducing what Claude reads at session start, and none touch the Active-only /
relevant-entries scoping already built into AGENTS.md's mandatory-read rule.
