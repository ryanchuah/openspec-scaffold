# Explore — Agent Context Infrastructure (2026-06-18)

**Status:** EXPLORE output — a holistic MAP, **not a change**. No code touched. Captures
options + a recommendation for two problems, plus the research provenance (what was
searched, what was ruled out, and why) so a fresh session can continue without re-deriving.

> **UPDATE 2026-06-18 (spikes run):** Four open spikes from §4 were executed (boot-cost
> measurement, `copier` fit, OpenCode `instructions:`, and an OpenSpec native-customization
> audit). Results in **§6** materially revise the recommendations in §1d and §2e — read §6
> for the current position. Headlines: **`copier` is now ruled OUT** (no intra-file region
> merge); **the bespoke sync is legitimately bespoke** (fills a gap OpenSpec doesn't cover);
> the `openspec update` skill-clobber **mechanism is real but already neutralized** by our
> documented copy-only bootstrap + README ban (NOT a live risk — see §6.4/§7.1, corrected
> 2026-06-18); and Problem 1's real cost is **growing mutable state files (worst in
> extrends)**, not psc-monitor's (cache-friendly) appendix. Scale fixed at **3 repos**.
> Citations (§2a) are abandoned as unreliable — treat all as fabricated.

**Targets:** the two sibling repos `psc-monitor` and `extrends`. This scaffold only *feeds*
them — the problems bite in the targets, where agents actually onboard and run.

**Operator steers that frame everything below:**
1. **Ground options in community-agreed docs / battle-tested projects**, not clever bespoke
   designs that may not scale as the target repos grow. (Codified in harness memory
   `feedback-ground-in-battle-tested-patterns`.)
2. **Do not be tied to the status quo** — an option that discards the existing scaffold/sync
   machinery and does a large migration is fully valid if a more standard pattern fits better.

**Provenance:** four subagents (2 Explore over the repos, 2 Sonnet web-research forced through
`scripts/fetch_clean.py` per `ai-docs/research-fetch-convention.md`). Raw research dumps were
written to `tmp_research_context_rot.md` and `tmp_research_agent_sync.md` (temp; their load-bearing
findings are folded in below so nothing is lost when they're cleaned). Source prompts:
`tmp_prompt_context_rot.md`, `tmp_prompt_agent_sync.md`.

---

## 0. The unifying frame — three layers of agent context

Both problems are the same stack hit at different layers. Naming the layers makes the right
mechanism per problem obvious.

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1 — UNIVERSAL   (roles, lifecycle, workflow, tiers,    │  ← Problem 2
│   model matrix, delegation, skills, executor agents)         │    "sync"
│   identical across psc-monitor + extrends + future repos     │
├─────────────────────────────────────────────────────────────┤
│ LAYER 2 — PROJECT     (domain, schema, stack, conventions)   │  ← the global/
│   per-repo, hand-written, SHOULD be lean                     │    local split
├─────────────────────────────────────────────────────────────┤
│ LAYER 3 — DYNAMIC STATE (STATUS latest, active blockers,     │  ← Problem 1
│   active open-questions, in-flight OpenSpec changes)         │    "context rot"
│   per-repo, present-tense, changes every session             │
└─────────────────────────────────────────────────────────────┘
```

- Problem 2 = share **Layer 1** without drift.
- Problem 1 = ingest **Layer 3** cheaply at boot.
- The thing both prompts circle — "shrink per-repo AGENTS.md" — is really *getting Layer 1 out
  of the per-repo file so Layer 2 can be lean.*

---

## 1. Problem 1 — Context onboarding ("context rot")

**Original proposal (`tmp_prompt_context_rot.md`):** replace AGENTS.md's English conditional
routing logic with a deterministic `scripts/bootstrap_context.py` that compiles present-tense
repo state into an ephemeral `.context.txt` (gitignored); AGENTS.md shrinks to "read `.context.txt`
to orient." Claimed prior art: Repomix, Code2Prompt, "progressive disclosure", Google ADK
"state machines over history".

### 1a. What the research confirmed vs. inflated

| Claim | Verdict | Note |
|---|---|---|
| "Lost in the middle" degradation | ✅ REAL | Liu et al. 2023, `arXiv:2307.03172` (peer-reviewed, pre-cutoff — trustworthy). |
| "Context rot" is a named phenomenon | ✅ REAL but **very recent** | Coined Jun 18 2025 (HN user "Workaccount2"), amplified by Simon Willison same day; Drew Breunig formalized 4 sub-categories Jun 29 2025. Practitioner vocab, not academic. **It describes session-length degradation, not boot-time cost.** |
| Repomix / Code2Prompt are real tools | ✅ REAL | Repomix: JSNation "Powered by AI" nomination confirmed in README. Code2Prompt: PyPI, MIT. |
| "Keep instruction files lean" | ✅ DOCUMENTED | Claude Code guidance: target under ~200 lines; "bloated CLAUDE.md files cause Claude to ignore your actual instructions." |
| Repomix/Code2Prompt as prior art for **state compilation** | ❌ **CATEGORY ERROR** | Both compile **source code** ("what does the code look like?"), say nothing about status/blockers/open-questions. Conflating "code packaging" with "state compilation." |
| ADK "state machines over history" | ❌ OVERREACH | ADK prefers deterministic task flows + has key-value session state, but documents no "avoid reconstructing state from text files" principle. |
| Root rules must be "cacheable" | ❌ UNSUPPORTED | "lean" is documented; "cacheable" is not in any AGENTS.md spec reviewed. |
| "Compile project state into ephemeral boot context" | ❌ **NOVEL** | Not a named/established pattern in any framework docs or practitioner literature. It is new engineering — fine to build, but don't call it industry-standard. |

### 1b. Repo diagnostic facts (from the Explore mapping)

- **The English "routing logic" is tiny** — ~15–34 lines of mandatory preamble in each repo
  (`AGENTS.md:3-34`). Shrinking it is a rounding error.
- **The real always-loaded bloat is Layer 2 in the wrong place:** `psc-monitor/AGENTS.md` is
  **707 lines**, of which **~412 are an inlined "Project reference" appendix** (schema, API,
  matcher logic). `extrends/AGENTS.md` is **299 lines** and **already lean** — it pushes domain
  detail out to `openspec/config.yaml` + `ai-docs/`. So the two repos have *already diverged* on
  the global/local split; extrends is the model, psc-monitor the outlier.
- **State-file parseability is asymmetric** — a *deterministic* parser is only safe on
  psc-monitor (ISO dates, `## Decision:` + structured blocks → LOW difficulty). `extrends`
  state files are prose with inline markers (`✅ RESOLVED`, `**BLOCKING**`, no per-entry dates →
  MED-HIGH difficulty). A regex compiler would be **fragile exactly where scale-fragility was
  the operator's stated worry.**
- Neither repo has a `.context.txt` or a gitignore entry for one (only `.env` ignored).

### 1c. Options

| # | Option | Battle-tested? | Verdict |
|---|---|---|---|
| **1A** | **Lean-file + progressive disclosure.** Move psc-monitor's 412-line appendix out of AGENTS.md into `ai-docs/` reference loaded on demand — make psc-monitor look like extrends. Keep boot routing as-is. | ✅ documented Claude Code norm | **RECOMMENDED CORE.** Cheap, harmonizes the two repos, attacks the real always-loaded bloat. |
| **1B** | **Structure the state at the source.** Give STATUS/open-questions explicit fields (frontmatter, ISO dates, status enums) so *any* consumer — agent or script — reads them deterministically. | ✅ "docs-as-data"/front-matter standard | Good enabler; prerequisite if 1C is ever to be non-fragile. Medium effort (touches state files in both repos). |
| **1C** | **`bootstrap_context.py` → `.context.txt`** (the prompt's proposal). | ❌ novel, no precedent | **DEFER.** Only after 1B makes parsing trivial, and only if boot cost is *measured* high. If built, keep it dumb (concatenate already-bounded sections), not an NLP parser. Drop the Repomix framing. |
| **1D** | **Do nothing.** Progressive disclosure is already best practice; routing is tiny. | ✅ | Defensible but ignores psc-monitor's real bloat. |

### 1d. Recommendation + what we ruled out

**Recommend 1A now; 1B if determinism is wanted; 1C only as a deferred, dumb add-on.**
The most battle-tested fix is making AGENTS.md lean — **not** building a state compiler.

**Ruled out / cautioned:**
- The **Repomix/Code2Prompt analogy** — ruled out as prior art (category error: code ≠ state).
- A **deterministic prose parser** as the v1 of bootstrap — ruled out as fragile on extrends
  until 1B structures the inputs.
- Conflation alert: a **boot-time** compiler does **not** cure "context rot" (a *session-length*
  phenomenon). If 1C is built, justify it by measured boot-token cost, not by the (misapplied)
  context-rot literature.

---

## 2. Problem 2 — Cross-repo agent sync

**Original proposal (`tmp_prompt_agent_sync.md`):** decouple global instruction infrastructure
from per-repo files. Evaluate three patterns: (1) Workspace / repo-of-repos, (2) scripted
sync / symlink managers, (3) native `@import` directives. Shrink per-repo AGENTS.md to
project-specific only.

### 2a. ⚠️ Citation integrity — the prompt's "industry validation" is partly fabricated

The proposal cites five `(n.d.)` authorities. Verdicts from web research:

| Citation | Claimed | Verdict |
|---|---|---|
| **Kondratyev (n.d.)** | multi-repo software exceeds a single repo's context window | ❌ **FABRICATED** — no matching published work. |
| **Bi (n.d.)** | automated context-sync tools / symlink managers across repos | ❌ **FABRICATED** — no matching published work. |
| **Gloaguen** | over-stuffed AGENTS.md reduces agent success / raises tokens | ⚠️ REAL author, **MISREPRESENTED + softened** — real finding reportedly *stronger*: context files can hurt even when well-formed, not only when over-stuffed. Cited as `arXiv:2602.11988` — **UNVERIFIED (post-cutoff), confirm before quoting.** |
| **Vasilopoulos** | "Codified Context Infrastructure" | ⚠️ REAL, cited as `arXiv:2602.20478` — **UNVERIFIED, confirm.** |
| **Galster** | Claude `@imports` are "an emerging standard" | ❌ **REVERSED** — real paper (`arXiv:2602.14690`, UNVERIFIED) reportedly argues AGENTS.md portability **over** tool-specific `@import` patterns — the opposite of the cited claim. |

**Action for any future proposal:** strip Kondratyev + Bi entirely; re-read Gloaguen/Vasilopoulos/
Galster from source and re-state accurately; verify all `2602.*` arXiv IDs (they post-date the
assistant's Jan 2026 knowledge cutoff).

### 2b. This is ~90% already solved — by bespoke machinery

`scripts/sync_scaffold.py` (+ `scaffold_manifest.txt`, `_convergence.py` is unrelated,
`scaffold_check.py` pre-commit guard, `test_sync_scaffold.py`) already does:
- **Manifest-driven file copy** (skills, `.claude/` + `.opencode/` executor agents, shared
  `ai-docs/*`, scripts) — byte-identical.
- **AGENTS.md span-merge** that *replaces* two shared spans (`> **MANDATORY` → project-context;
  `## Roles` → `## After reading this file`) while *preserving* each repo's title,
  `## Project context`, and tail (psc-monitor's 412-line appendix survives verbatim).
- **Two gates:** `--check` (byte/span convergence) and `--check-refs` (referential integrity —
  cited `ai-docs/*` files + `AGENTS.md §"..."` sections must resolve downstream).
- **Idempotent**, tested, deployed (W6 propagation 2026-06-17; dangling-refs fix 2026-06-18).

So the prompt's "we manually copy-paste, it's brittle" framing is **outdated.** The real
decision is **harden the homegrown span-merge vs. migrate to a battle-tested standard** — and
the operator's steer leans migrate.

### 2c. Hard constraints that filter every option

1. **Dual-harness (Claude Code + OpenCode):** `@import` is **Claude-Code-only** and **does
   nothing in OpenCode** (OpenCode reads AGENTS.md natively but has no in-file import). ⇒
   `@import` is disqualified as a *primary* mechanism. *(Discrepancy to resolve: the scaffold's
   own prior research notes OpenCode supports a config-level `instructions: [paths]` array in
   `opencode.json` that can include external files — that is a real "reference outside repo"
   path, just per-harness config, not AGENTS.md syntax. Verify current OpenCode behavior.)*
2. **Carries code, not just text:** skills, executor agents, scripts must propagate too ⇒
   pure instruction-reference mechanisms (global `CLAUDE.md`, `@import`) **can't cover it**.
3. **Must scale to N repos:** current ceiling is manual per-repo invocation, no registry.

### 2d. Options

| # | Option | Battle-tested? | Code+text? | Cross-harness? | Verdict |
|---|---|---|---|---|---|
| **2A** | **Harden the bespoke script** (add repo registry, keep span-merge). | ❌ homegrown | ✅ | ✅ | Works; but it's the machinery the operator is wary of owning. |
| **2B** | **Global+local via native harness hierarchy** — universal text in `~/.claude/CLAUDE.md` (Claude) + `opencode.json instructions:[...]` (OpenCode); per-repo AGENTS.md = project-only. | ✅ documented per-harness | ❌ text only | ⚠️ two entry points | Great for Layer-1 *text*; still needs another mechanism for code. The operator's "reference outside the repo" idea — viable but partial. |
| **2C** | **`copier` template with `copier update`.** | ✅✅ mature OSS, *exactly* this use case | ✅ | ✅ (files land physically) | **STRONGEST STANDARD MATCH.** `copier update` re-applies an evolving template to existing repos with 3-way merge preserving local edits — precisely what the span-merge reimplements by hand. |
| **2D** | **Git submodule / subtree** of a shared `agent-scaffold` repo. | ✅ standard git | ✅ | ✅ (physically present) | Harness-agnostic, versioned, pinnable. Submodule UX is notoriously painful; subtree trades that for merge complexity. |

### 2e. Recommendation + what we ruled out

**Recommend: adopt the global/local split (lean per-repo AGENTS.md = Layer 2 only) and replace
the bespoke span-merge with `copier` (2C) as the propagation engine** — its whole reason to exist
is "keep many projects in sync with an evolving template while preserving local edits." Optionally
layer 2B on top for *truly* universal text rules so they need no syncing at all.

*Caveat (do not skip):* confident on the **shape** (standard template-sync tool > bespoke
span-merge), but `copier`'s exact fit to the AGENTS.md "preserve title/project-context/tail"
semantics deserves a **half-day spike** before committing. Don't trade a *tested* homegrown tool
for an *unproven* migration without that spike.

**Ruled out:**
- **`@import` as primary mechanism** — ruled out: Claude-Code-only, silently dead in OpenCode.
  (Also independently rejected by the scaffold's own earlier research.)
- **Workspace / repo-of-repos (prompt option 1)** — ruled out earlier by the scaffold's research
  for dual-harness incompatibility (Claude Code vs OpenCode have different workspace/config
  discovery); no need to re-litigate unless the harness set changes.
- **Pure symlink manager (GNU Stow / chezmoi)** — viable for *text* dotfiles but weaker than
  copier/subtree for shipping code + per-repo local-edit preservation; not recommended as the
  primary, but a fallback if a no-dependency approach is required.
- **cookiecutter** — ruled out vs copier: one-shot generation, **no update/re-apply** workflow.

---

## 3. Combined target architecture

```
        shared "agent-scaffold" template (copier)
        ├── Layer 1 universal: AGENTS.md core spans, skills,
        │     executor agents, scripts   ── copier update ──┐
        └── (optional) truly-universal TEXT also in            │
              ~/.claude/CLAUDE.md + opencode.json instructions  │
                                                                ▼
   ┌────────────────────────────┐      ┌────────────────────────────┐
   │ psc-monitor                │      │ extrends                   │
   │ AGENTS.md = Layer 2 only   │      │ AGENTS.md = Layer 2 only   │
   │  (reference appendix moved │      │  (already lean ✓)          │
   │   to ai-docs/, lean now)   │      │                            │
   │ Layer 3 state files (+opt. │      │ Layer 3 state files (+opt. │
   │  structured for boot read) │      │  structured for boot read) │
   └────────────────────────────┘      └────────────────────────────┘
```

---

## 4. Open questions / spikes before any proposal

1. **Measure the boot cost.** Is reading STATUS + open-questions + decisions-headers actually
   expensive enough to justify *any* Layer-3 tooling? If not, Problem 1 collapses to "1A."
2. **`copier` spike.** Can it express the AGENTS.md "preserve title/project-context/tail" merge
   as cleanly as the current script? If yes → migrate; if no → 2A.
3. **Resolve the OpenCode `instructions:` discrepancy** (2c, note 1) against current OpenCode.
4. **How many repos is "scale"?** Two repos barely justify migrating off a working script; 5+
   tilts decisively toward a standard tool + registry.
5. **Citation hygiene:** strip fabricated citations; verify all `2602.*` arXiv IDs before any
   artifact cites them.

---

## 5. Research method / provenance

- All web research routed through **subagents** using `python scripts/fetch_clean.py <url>` per
  `ai-docs/research-fetch-convention.md` (orchestrator never called `WebSearch` directly).
- Codebase mapping via two read-only Explore agents over `psc-monitor`, `extrends`, and this
  scaffold's sync machinery.
- Raw research dumps: `tmp_research_context_rot.md`, `tmp_research_agent_sync.md` (temp — key
  findings folded in above). Source prompts: `tmp_prompt_context_rot.md`, `tmp_prompt_agent_sync.md`.
- Prior internal research this builds on: `ai-docs/archive/research-single-source-2026-06/`
  (A-native-mechanisms, B-polyrepo-patterns) and `ai-docs/archive/research-industry-standards-2026-06/`.

---

## 6. Spike results (2026-06-18) — what changed

Four spikes from §4 were run via subagents (boot-cost: local read; copier + OpenCode:
web via `fetch_clean.py`; OpenSpec audit: local read of the cloned `OpenSpec/` + our
scaffold). Scale decision from the operator: **3 repos**. Citation hygiene (§4.5) is
**dropped** — the upstream research agent is unreliable; treat §2a citations as fabricated
and cite nothing from them. Full per-spike dumps: `tmp_spike1_bootcost.md`,
`tmp_spike2_copier.md`, `tmp_spike3a_opencode_instructions.md`,
`tmp_spike3b_openspec_customization_audit.md`.

### 6.1 Spike 1 — boot-token cost (reframes Problem 1)

Estimates (bytes/4; ranges = decisions.md read headers-only → full):

| Repo | Always-loaded boot tokens | Dominant cost | Per-session marginal |
|---|---|---|---|
| psc-monitor | ~16.2k → ~21.6k | 47KB inlined AGENTS.md appendix (~12k), **stable** | ~4k (appendix caches in prompt cache) |
| extrends | ~20.5k → ~71.7k | **mutable** state files: STATUS+open-questions ~14k, decisions.md up to ~52k | ~full reload each boot (state changes every session) |

**Neither is "cheap"** (both well over the ~5k bar). The surprise: **extrends is the worse
per-session case, not psc-monitor.** psc-monitor's bulk is a *stable* appendix that prompt-
caching largely amortizes; extrends' bulk is *mutable* state that changes every session and
pays full reload. ⇒ Problem 1 does **not** collapse to "make psc-monitor lean." The real
live lever is **bounding the growing Layer-3 state files** (the thing 1B/1C target),
especially in extrends.

*Caveats:* numbers are bytes/4 estimates, not tokenizer-exact; the cache argument assumes
prompt caching is active, the appendix sits before mutable content, and is weaker under
OpenCode. Treat the **direction** (extrends state files = the growing cost; psc-monitor
appendix caches) as the finding, not the exact figures.

**Revised Problem-1 position:** still do **1A** (move psc-monitor's appendix to `ai-docs/`)
— it cuts cold-cache and OpenCode-without-caching cost and harmonizes the repos — but
**promote 1B** (bound/structure the state files: e.g. decisions.md headers-only at boot,
rotate/archive resolved entries, cap STATUS/open-questions) from "optional" to the **primary
lever**. A `bootstrap_context.py` compiler (1C) is still **not** required: simpler bounding +
progressive disclosure on state addresses the measured cost without novel tooling.

### 6.2 Spike 2 — `copier` (rules copier OUT for the span-merge)

`copier update` has **no intra-file region primitive.** File-level knobs are only
`_skip_if_exists` (skip whole file) and `_exclude` (never touch). Its sole "preservation"
path is a synthetic-baseline diff/patch 3-way merge (regenerate old template → diff vs current
file → re-apply on new template); local edits survive only when they don't conflict. There is
no way to say "lines X–Y are always the repo's." Our AGENTS.md need — *replace 2 named spans,
preserve title + project-context + long appendix tail* — would degrade into **whole-file
3-way merges that emit conflict markers on nearly every update across every repo**, since both
template and per-repo content evolve. That is **strictly worse** than the current span-merge,
which has explicit ownership semantics. (copier *does* carry code/dotfiles byte-for-byte fine —
that part was never the hard problem.)

**Revised Problem-2 position:** **`copier` is RULED OUT** as the AGENTS.md propagation engine
(reverses §2e's recommendation). The earlier "strongest standard match" call was made before
testing copier against the *intra-file* requirement, which is the whole difficulty.

### 6.3 Spike 3a — OpenCode `instructions:` (refines the global-text option)

- `instructions: [...]` **confirmed** (exact key, lowercase singular) in `opencode.json` and
  global `~/.config/opencode/opencode.json`. Entries may be relative paths, globs, `~/`-home,
  absolute `/`, or `http(s)://` URLs — external/outside-repo references **are supported.**
- **Footgun:** OpenCode merges config arrays by **replace, not concat** (remeda `mergeDeep`).
  A project `opencode.json` that sets its own `instructions:` **silently drops** the global
  array. So "universal rules in the *global* `instructions:`" is fragile.
- `@import`-style includes inside `AGENTS.md` are a **confirmed no-op** in OpenCode (docs say
  so explicitly; it reads AGENTS.md as plain text). Confirms §2c.1 — `@import` stays
  disqualified as a primary mechanism.
- **Better global-TEXT channel:** `~/.config/opencode/AGENTS.md` (always loaded, no per-project
  config, the OpenCode analogue of `~/.claude/CLAUDE.md`). Reserve `instructions:` for
  per-project additions.

**Revised 2B:** a truly-universal *TEXT* layer is viable cross-harness via the two **global
AGENTS files** (`~/.claude/CLAUDE.md` + `~/.config/opencode/AGENTS.md`) — **not** via the
global `instructions:` array. But this carries **text only**; skills, executor agents, and
scripts still need physical propagation. 2B is a complement, not a replacement, for the sync.

### 6.4 Spike 3b — OpenSpec native-customization audit (answers "did we veer off course?")

The honest answer is **mostly no — with one real landmine.** OpenSpec's extension points
operate at a *different layer* than what we customize:

| Capability | OpenSpec-native mechanism | What our scaffold does | Verdict |
|---|---|---|---|
| Workflow **skill bodies** (apply/archive/verify behavior) | none — `openspec update` regenerates them from fixed templates | hand-edited the generated SKILL.md (delegation block, `opencode run`, failure ladder, NON-CONVERGENCE grep, phase gates) | **REINVENTING + colliding** (see landmine) |
| Per-tool **commands** | generated per tool | use OpenSpec's | ALIGNED |
| Multi-tool (claude+opencode) **generation** | `openspec init/update --tools` | partly hand-synced via `sync_scaffold.py` | overlaps, but see below |
| **Executor agents** (`.claude/agents`, `.opencode/agent`) | **not an OpenSpec concept** (it manages skills+commands only) | our invention | **LEGITIMATELY-BESPOKE** |
| **AGENTS.md** roles/tiers/workflow text | OpenSpec does **not** manage AGENTS.md bodies | our hand-written file + span-merge | **LEGITIMATELY-BESPOKE** |
| **Cross-project sharing** of the above | global-overrides / community-schema repos carry **only** schema.yaml + artifact templates | `sync_scaffold.py` carries skill bodies, agents, AGENTS.md spans, ai-docs, scripts | **LEGITIMATELY-BESPOKE** (real gap) |
| Project **context/rules injection** | `openspec/config.yaml` | extrends already uses config.yaml ✓ | ALIGNED where used |
| Custom **workflow artifacts** | `openspec/schemas/` (fork/define) | not used | available, unused (fine) |

Three takeaways:

1. **The cross-repo sync is NOT off course.** OpenSpec's overrides/schemas carry only artifact
   templates + schema.yaml — never skill bodies, executor agents, AGENTS.md spans, or ai-docs.
   Those are exactly our payload. There is **no native hook we ignored**; the span-merge fills
   a genuine gap. (And §6.2 says don't migrate it to copier either.)

2. **`openspec update` skill-clobber — real mechanism, already neutralized (corrected
   2026-06-18).** All 7 `.claude/skills/openspec-*/SKILL.md` carry `generatedBy: "1.4.1"`;
   `OpenSpec/src/core/update.ts` regenerates a hardcoded `SKILL_NAMES` set with a plain
   `FileSystemUtils.writeFile` (no merge), so `openspec init`/`update` *would* overwrite our
   customizations with stock templates. **But this is not a live risk:** our new-repo bootstrap
   is `cp -r` the scaffold + fill placeholders (`README.md` "Per-project setup") — **no
   generation step**; `sync_scaffold.py` propagates by file-copy, never via the CLI; the
   downstream repos aren't even npm packages (no `package.json`, so no postinstall); and
   `README.md` (L49-53 + L136-143) **already bans `openspec init`/`update` twice**, with the
   rationale and the recovery command (`git checkout .claude/skills`). The only `openspec` CLI
   commands the workflow uses are change-lifecycle (`new change`/`status`/`archive`/`validate`),
   which don't touch skill files. ⇒ **No action needed.** (Earlier drafts of this doc called this
   a "landmine needing a CI guard" — that was over-engineering; the workflow precludes and
   documents it. The one genuinely "off course" observation stands only in spirit: we ship
   customized files that carry OpenSpec's `generatedBy` stamp — cosmetically misleading, but
   harmless given the ban.)

3. **config.yaml is the one native hook we under-use.** Context/rules injection (Layer-2
   project facts, §0) is exactly what `openspec/config.yaml` is for; extrends uses it,
   psc-monitor's inlined appendix is partly content that could move there or to `ai-docs/`.

### 6.5 Net revised recommendations (supersede §1d, §2e)

- **Problem 1 (onboarding cost):** 1A (psc-monitor appendix → `ai-docs/`/`config.yaml`) **plus**
  1B as the *primary* lever (bound + lightly structure the mutable state files, worst in
  extrends). No compiler (1C) needed.
- **Problem 2 (sync):** **Keep and harden the bespoke `sync_scaffold.py`** (option 2A) — it is
  legitimate, not a reinvention of any OpenSpec hook; **`copier` is ruled out** (§6.2).
  Optionally add a global-TEXT layer for truly-universal rules via the two global AGENTS files
  (refined 2B, §6.3). **Separately and first, defuse the `openspec update` clobber landmine**
  (§6.4 finding 2) — it threatens the skills regardless of which sync we keep.
- **Scale = 3 repos:** below the 5+ threshold that would justify a heavy standard tool +
  registry; this *reinforces* "harden the working script" over "migrate."

**Still explore.** None of this is implemented. When a thread is ready, the operator can say
"propose a change for X" (likeliest first cuts: the `openspec update` landmine fix; psc-monitor
appendix relocation).

---

## 7. Options + recommendation per priority (2026-06-18)

Three option-spikes (subagents, local read) explored the three priorities. Full dumps:
`tmp_opt_p1_landmine.md`, `tmp_opt_p2_appendix.md`, `tmp_opt_p3_state.md`. Recommendations
below are the orchestrator's, with judgment applied on top of the subagent findings.

### 7.1 Priority 1 — defuse the `openspec update` clobber

**Mechanics (verified, cited in dump):** the regenerated set is a hardcoded `SKILL_NAMES`
array (`tool-detection.ts:14-26`), **not** keyed on the `generatedBy` stamp — the stamp only
drives the version-skip gate. `update` regenerates when stamp≠current-version OR profile drift
(missing/extra skills); `--force` bypasses both; `init` always writes. Commands are overwritten
too. **No** user-modification detection (plain `fs.writeFile`); **no** template-override or
hook seam.

| Option | Works? | Effort | UX cost |
|---|---|---|---|
| (a) alter `generatedBy` stamp | partial — fails on version bump + `--force` | low+recurring | ongoing debt |
| (b) rename skill dirs off `openspec-*` | no — upstream still regenerates canonical names; breaks slash IDs | high | high |
| (c) **no-update policy + CI/pre-commit stamp guard** | **yes, fully** | low | ~none |
| (d) upstream a skill-body hook to OpenSpec | not now — no seam | high | low later |
| (e) vendor-and-patch overlay (`patch-package` style) | yes | medium + per-upgrade | medium ops |

**Recommendation (corrected 2026-06-18): NO ACTION — already handled; drop P1.** The earlier
"pick a mitigation / add a guard" framing was over-engineered. Verifying the actual workflow
settled it: new-repo bootstrap is `cp -r` + fill placeholders (`README.md` "Per-project setup",
no generation step); `sync_scaffold.py` propagates by file-copy and has no init/clone mode; the
downstream repos have no `package.json` (no npm lifecycle, no postinstall); and `README.md`
(L49-53 + L136-143) **already bans `openspec init`/`update` twice**, with rationale + recovery
(`git checkout .claude/skills`). So nothing in the workflow triggers regeneration, and the
prohibition is already documented. The option matrix above is retained only for the hypothetical
future where we *want* to consume upstream skill changes (then option (e) vendor-and-patch or a
deliberate branch-update + re-apply would apply). *Optional, marginal:* the ban lives in
`README.md` (human-facing), not `AGENTS.md` (agent-facing) — a one-line mirror in AGENTS.md would
cover an agent that never reads the README, but the risk of an agent spontaneously running
`openspec update` is low; not worth a change on its own.

### 7.2 Priority 2 — relocate psc-monitor's AGENTS.md appendix (1A)

**Plan:** move the ~412-line inlined appendix into ~4 on-demand `ai-docs/` files
(`schema-reference`, `api-reference`, `repo-layout`, `ops-runbook`); **pull the handful of
load-bearing pitfall notes UP into `## Project context`** (they're always-needed, must not go
on-demand); replace the tail with a ~15-line "On-demand references" pointer table. Net 707 →
~335 lines (~53%, matching extrends). **No `config.yaml` change** — reference material belongs
in on-demand `ai-docs/`, not in always-injected `context:` (don't relocate always-loaded bloat
into a different always-loaded channel).

**Sync impact: none.** `sync_scaffold.py` tail-detection keys on the `---` separator that still
precedes the new pointer section; the new `ai-docs/` files are project-unique (do **not** add to
`scaffold_manifest.txt`).

**Recommendation: do it** (cheapest, documented "lean file + progressive disclosure" norm,
zero sync risk). **Judgment additions for the proposal:** (a) before deleting any section,
grep psc-monitor for ``AGENTS.md §"…"`` citations and repoint them to the new files (refs gate
does NOT cover the preserved tail); (b) don't blanket-drop `## Do not do` / `## Known issues` —
audit them and move genuine constraints into `## Project context` or an `ai-docs/` gotchas file
rather than deleting; (c) add an explicit existence check for the new `ai-docs/` files to the
tasks.

### 7.3 Priority 3 — bound the mutable state files (1B)

**Mapping (est tokens, bytes/4):** extrends `STATUS.md` ~7k (~65% archivable, already **over**
its own 3-entry cap), `open-questions.md` ~7k (~50% is tune-after-runs bullets in *shipped*
sections), `decisions.md` ~52k full but **headers-only at boot already** (bounded). psc-monitor
state files already well-bounded (~4k). ⇒ **The bloat is a discipline gap, not a missing tool:**
extrends is over its existing caps and the archive step under-enforces them.

**Recommendation: A + D + C(forward-only)** — tighten the conventions (no compiler):
1. `STATUS.md`: each change-entry ≤~150 words; full narrative lives in the change archive.
2. `open-questions.md`: at archive, park shipped-section non-BLOCKING bullets to a parked file;
   leave a **mandatory one-line pointer stub** at boot so the prompt-to-load stays visible.
3. `decisions.md`: new entries carry `Date:` + `Status:`; change-record entries capped (~300
   words) — lightly structures extrends toward psc-monitor's format, enabling future archiving.

Projected: extrends always-loaded state ~14k → ~5k (~65%). **Judgment additions:** place these
rules in the **canonical home per the single-source-rules convention (cite-don't-restate), not
re-inlined ad hoc**, and make enforcement an explicit archive-executor step. **Main risk:**
operational "tune-after-N-runs" context moves one hop away — the mandatory pointer stub is the
mitigation; verify it's load-bearing-safe.

### 7.4 Suggested sequence

**P1 is dropped (§7.1) — already handled by documented workflow.** Remaining:

1. **P3 first** — biggest *measured* live win (extrends ~14k→~5k per session); rule-level change
   propagated via the scaffold to both repos.
2. **P2 anytime** — contained, low-risk cleanup; benefits cold-cache + OpenCode (psc-monitor's
   per-session cost is already largely cache-amortized, so it's lower-urgency than P3).

P2 is fully independent (psc-monitor-only); P3 edits the scaffold conventions and propagates to
both repos. Each should be its own OpenSpec change.
