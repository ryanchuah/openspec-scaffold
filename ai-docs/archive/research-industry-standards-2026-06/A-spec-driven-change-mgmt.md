# Bucket A — Spec-Driven Development & Structured Change Management
**Industry-standards comparison for `openspec-scaffold` (2026-06)**

---

## 1. Scope

This analysis covers the **OpenSpec-based change lifecycle** of the scaffold: how a change is
proposed, how specs serve as durable source of truth, change tiering/sizing, task
decomposition, spec→code traceability, pre-implementation artifact review, how completed
work folds back into living specs, and how an agent is onboarded to the spec system.

**Sibling boundaries (mention only, not analyzed here):**
- Executor-delegation/orchestration *mechanics* — how the apply-executor is invoked, failure
  ladders, sentinel polling (Bucket B).
- AGENTS.md/MCP/skills as a *config mechanism*, tool mirroring across Claude/OpenCode
  (Bucket C).
- Knowledge persistence, memory systems, and verification-quality criteria beyond basic
  behavioral review (Bucket D).

---

## 2. Sources Consulted

| URL | What it is | Date / Recency |
|-----|-----------|----------------|
| https://github.com/Fission-AI/OpenSpec | OpenSpec upstream README (the golden-source parent) | Current (v1.4.1, 2026) |
| https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md | OpenSpec upstream concepts guide — change/spec model, workspace, principles | Current (2026) |
| https://github.com/Fission-AI/OpenSpec/blob/main/docs/getting-started.md | OpenSpec getting-started — artifact structure, delta spec format, workflow paths | Current (2026) |
| https://github.com/Fission-AI/OpenSpec/blob/main/docs/opsx.md | OpenSpec OPSX workflow doc — "fluid not rigid" philosophy, command reference | Current (2026) |
| https://github.com/Fission-AI/OpenSpec/releases | OpenSpec releases page — version history confirms v1.4.1 is current | Current (2026) |
| https://github.com/github/spec-kit | GitHub Spec Kit README — constitution, /specify, /plan, /tasks, /implement workflow | Current (v0.8.7, May 2026, 90k+ stars) |
| https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/ | GitHub blog post introducing Spec Kit — rationale, 4-phase workflow, human-checkpoint model | May 2026 |
| https://kiro.dev/docs/specs/ | AWS Kiro specs docs — requirements.md/design.md/tasks.md, wave execution, Quick Plan | Updated May 5, 2026 |
| https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices | Thoughtworks article — SDD definition, what makes a good spec, comparison to waterfall | Late 2025 |
| https://github.com/bmad-code-org/bmad-method | BMAD Method README — multi-agent agentic planning, spec sharding, scale-adaptive | Current (V6, 2026) |
| https://docs.bmad-method.org/ | BMAD docs overview — modules, workflow overview | Current (2026) |
| https://developer.microsoft.com/blog/spec-driven-development-ai-native-engineering | Microsoft Developer blog on SDD — Spec Kit lifecycle, constitution, real project examples | 2026 |
| https://www.augmentcode.com/guides/what-is-spec-driven-development | Augment Code SDD guide — 6 elements of a good spec, adversarial agent pattern, EARS notation, tool comparison | 2026 |
| https://thebcms.com/blog/spec-driven-development | BCMS definitive 2026 SDD guide — EARS notation, all major tools, phase workflow | May 2026 |
| WebSearch results (multiple) | Synthesis of search snippets: change tiering, traceability, SDD adoption landscape | June 2026 |

**Inaccessible:** https://www.marktechpost.com/2026/05/08/meet-github-spec-kit-an-open-source-toolkit-for-spec-driven-development-with-ai-coding-agents/ (403 Forbidden) — omitted.

---

## 3. Industry Standard (mid-2026)

### 3.1 The universal 4-phase convergence

By mid-2026 every major SDD tool (GitHub Spec Kit, AWS Kiro, BMAD, OpenSpec) has converged on
the same structural lifecycle, regardless of naming:

```
Specify / Propose → Plan / Design → Tasks → Implement
```

Critically, the GitHub Spec Kit blog states: *"each phase has a specific job, and you don't move
to the next one until the current task is fully validated."* Human checkpoints at every phase
boundary are the standard, not the exception — in both GitHub Spec Kit and BMAD. Kiro's
"Quick Plan" mode (batch artifact creation without approval gates) is explicitly an alternative
**opt-in shortcut**, not the primary workflow.

### 3.2 Spec as durable source of truth

Industry consensus is unambiguous: the spec — not the prompt history, not the code — is the
primary artifact. GitHub blog: *"We're moving from 'code is the source of truth' to 'intent is
the source of truth.'"* Thoughtworks (late 2025): *"specs are merely elements that drive code
generation... Executable code remains the source of truth you need to maintain"* — a dissenting
view, held by an important minority (the Thoughtworks author describes this as "more old-school
technologists"). The majority practice treats specs as the version-controlled, evolving source
of truth alongside code.

The standard structure: `specs/` (current system behavior) ← merged from `changes/<name>/specs/`
(delta specs per change). This is the delta-spec model.

### 3.3 Pre-implementation review: where industry falls short

This is a notable **gap in industry practice**. None of the major open-source tools has an
automated, separate-model artifact review before implementation:

- **GitHub Spec Kit**: `/speckit.analyze` (cross-artifact consistency check) is a human-facing
  command run optionally after `/tasks`, before `/implement`. It is a single-model self-check,
  not an independent reviewer.
- **Kiro**: The IDE warns of inconsistencies and ambiguities in-process. No separate reviewer
  model.
- **BMAD**: Mentions multiple agent "personas" (PM, Architect, QA) but these are role-play
  within one session; they are not deployed as independent models reviewing artifacts before
  freeze.
- **Upstream OpenSpec** (OPSX): No reviewer. `/opsx:propose` batch-creates all artifacts.
  Upstream philosophy is "fluid, iterate freely, no gates."

The closest academic/emerging pattern is the **adversarial agent pattern** (Coordinator +
Implementor + Verifier roles with separate agent instances), described in the Augment Code
guide as "the most underused pattern in spec-driven development." The arXiv paper
*"Spec-Driven Development: From Code to Contract in the Age of AI"* (Feb 2026) formalizes
"Spec-Anchored" patterns with governance checkpoints but does not mandate a separate reviewer
model as a universal standard.

### 3.4 Change tiering / right-sizing

Industry is converging on the recognition that not every change needs the full lifecycle:

- **Microsoft/Spec Kit blog** (2026): *"Not every change needs the full lifecycle, so adoption
  should be right-sized."*
- **Augment Code guide**: Provides a "When to use a spec / skip the spec" table keyed on
  reversibility, scope, and review cost.
- **BMAD**: "Scale-Domain-Adaptive — automatically adjusts planning depth based on project
  complexity."
- **Kiro**: Quick Plan (batch, no gates) for well-understood features; Requirements-First and
  Design-First for full workflows.

No tool has standardized on named tiers (S/M/L). The convention is: use judgment, with informal
guidance. A risk-tiered review model (lighter review for low-risk changes like docs/tests/isolated
features; full human sign-off for security/shared library changes) is described in search results
as "teams responding to agent-driven PR volume" but is not yet codified in any tool's built-in
workflow.

### 3.5 Task decomposition

Standard practice: tasks should be *atomic, independently shippable, verifiable in isolation*.
GitHub Spec Kit blog: *"Each task should be something you can implement and test in isolation...
like a test-driven development process for your AI agent."* BCMS guide on a good task: single
objective, explicit inputs, explicit outputs (files to create/modify), and an acceptance check.

**Kiro** introduces dependency-graph wave execution: independent tasks run concurrently (wave N),
their dependents in the next wave. This is the most advanced task execution model in the field.

Standard in **all tools**: tasks.md holds implementation-only work (code, tests, scripts).
Post-implementation phases (verify, archive) are not tasks.

### 3.6 Spec→code traceability

**Current state**: mostly absent in open-source tooling. There are no standard
requirement-ID-to-code-line traceability mechanisms in GitHub Spec Kit, Kiro, or BMAD. The
approach is: specs (especially in EARS notation) are clear enough that a code reviewer can check
alignment by reading. The emerging Augment Code/Intent tool claims semantic dependency graph
analysis linking specs across files, but it's a commercial product.

**Compliance pressure**: EU AI Act (August 2026) is driving demand for audit trails. Commercial
tools like Tessl provide them. Open-source tools do not.

**EARS notation** (Easy Approach to Requirements Syntax, Mavin et al., Rolls-Royce 2009) is
the de facto AI-readable spec format in mid-2026 — adopted explicitly by GitHub Spec Kit (BCMS
guide), Kiro's requirements.md, BMAD constitution documents, and referenced in multiple 2025-26
guides. Five patterns: Ubiquitous, Event-driven, State-driven, Unwanted behavior, Optional
features. The notation makes requirements unambiguous enough for agents to generate code and
tests without guessing.

### 3.7 Spec promotion: completed work folds back into living specs

Standard practice: when a change is archived, its delta specs are merged into the main
`openspec/specs/<capability>/spec.md`. This is explicit in OpenSpec upstream's archive flow.
GitHub Spec Kit does not have a formal archive/spec-promotion step — the spec file
(`.specify/specs/`) is updated in place. Kiro does not have an explicit spec-promotion concept.

### 3.8 Agent onboarding to the spec system

Standard practice:
- **GitHub Spec Kit**: `/speckit.constitution` as the **first command** — creates the project
  charter (project-wide EARS ubiquitous rules) before any spec work. This "constitution" is
  the immutable context for every subsequent agent action.
- **BMAD**: `bmad-help` skill for context-aware next-step guidance; onboarding by prompting
  an agent to invoke `bmad-help`.
- **Upstream OpenSpec**: `/opsx:onboard` for a guided walkthrough; `AGENTS.md` is the agent's
  entry point.
- **Common pattern**: The agent reads one authoritative instruction file (AGENTS.md/README) at
  session start, then loads change-specific artifacts. "Read before doing anything" is
  universal.

---

## 4. Scaffold Baseline

### 4.1 Change lifecycle

The scaffold's lifecycle: **explore → propose → apply → verify → archive**
(`AGENTS.md:70-79`). Each phase is gated with an explicit user permission request before
proceeding (`SKILL.md` "PHASE GATE" rules in every skill file).

### 4.2 Proposal creation: sequential artifact review

`openspec-propose/SKILL.md:15-19` defines the anti-batch rule: *"Do NOT batch-create all
artifacts. Create proposal, review it, fix it, freeze it. Only then create design..."* Artifacts
are created one at a time, each reviewed and frozen before the next begins.

### 4.3 The @openspec-reviewer

`openspec-propose/SKILL.md:96-198` defines a mandatory @openspec-reviewer audit of each artifact
before freeze. The reviewer is `deepseek-v4-pro`, invoked via `opencode run --agent
openspec-reviewer --model deepseek/deepseek-v4-pro`, a separate model and separate process from
the primary agent. The reviewer checks for severity markers (🔴 blocking, 🟡 warning, 💡
suggestion). Up to 3 reviewer passes; escalate to user if unresolved. The primary MAY overrule
the reviewer with documented rationale (`SKILL.md:196-199`).

### 4.4 Specs as source of truth

`openspec/config.yaml:1`: `schema: spec-driven`.
`AGENTS.md:90`: *"OpenSpec artifacts live in openspec/changes/<name>/"*.
Delta specs under `changes/<name>/specs/` merge into `openspec/specs/<capability>/spec.md` at
archive via the `openspec-sync-specs` skill (`openspec-sync-specs/SKILL.md:56-81`).
`openspec-archive-change/SKILL.md:75-88`: the archive-executor performs optional delta-spec
sync during archive.

### 4.5 Change tiering

The tiering system lives in `ai-docs/fast-track-workflow.md` (a separate file, not inline in
AGENTS.md or config.yaml). Three tiers:
- **SMALL**: skip OpenSpec lifecycle; write `plans/<slug>-plan.md`, delegate to apply-executor,
  verify via diff + behavioral test.
- **MEDIUM**: full lifecycle but only `tasks.md` required; still reviewer-frozen.
- **COMPLEX/UNCERTAIN**: full lifecycle — explore → propose → apply → verify → archive.
Default: fast-track tiering is **opt-in only** (`fast-track-workflow.md:3-9`), gated behind
explicit operator grant. This is a deliberate scaffold constraint (Constraint #4).

### 4.6 Task decomposition

`openspec/config.yaml:12-18` (rules.tasks): tasks.md contains ONLY apply-phase implementation
work. `openspec-propose/SKILL.md:235-238` guardrail: verify and archive steps must NOT appear as
tasks.md checkboxes. `openspec-apply-change/SKILL.md:80-200`: tasks are executed sequentially
by the apply-executor (deepseek-v4-flash); each is checked off on completion.

### 4.7 Verify phase

`openspec-verify-change/SKILL.md:14-31`: the orchestrator's own behavioral review (non-delegated),
requiring: (1) reading actual diffs, (2) re-running full test suite, (3) eyeballing real output,
(4) running live smoke for external API changes. Five mandatory notes.md fields required at
`SKILL.md:173-217`: verdict, live-output eyeball, defects+fixes, as-built deltas,
forward-looking items. Verbally acknowledge all five at turn end (`SKILL.md:218-241`).

### 4.8 Archive and spec promotion

`openspec-archive-change/SKILL.md`: archive-executor performs directory move + optional
delta-spec sync + reconciliation of STATUS.md/decisions.md/open-questions.md. Spec sync is
assessed and presented before executor runs (`SKILL.md:75-88`). The primary reviews the
reconciliation before committing (`SKILL.md:225-257`). Archive is write-deferred: project-tracked
docs are NOT updated during busy work; reconciled only at archive (`AGENTS.md:101-110`).

### 4.9 Agent onboarding

`openspec-onboard/SKILL.md`: EXPLAIN → DO → SHOW → PAUSE pattern; guided walkthrough of a
full change cycle using real codebase tasks. Pre-flight check for CLI (`openspec --version`).
`AGENTS.md:1-23`: "MANDATORY — read before doing anything else" preamble; lists AGENTS.md,
STATUS.md, ai-docs/decisions.md, ai-docs/open-questions.md as starting source of truth. Primary
is framed as orchestrator/reviewer, not implementer.

---

## 5. Gap Table

| Practice | Status | Evidence | Assessment |
|----------|--------|----------|------------|
| 4-phase lifecycle (propose → design → tasks → implement) | **Present** | `AGENTS.md:70-79`, all skill PHASE GATEs | Fully matches industry standard; phase gates are stronger than most tools |
| Spec as durable source of truth (versioned `specs/` dir) | **Present** | `openspec-sync-specs/SKILL.md`, `AGENTS.md:90` | Full implementation; delta-spec + main-spec model matches upstream |
| Sequential artifact creation with per-artifact review | **Ahead** | `openspec-propose/SKILL.md:15-19` | Batch-create is industry default (Kiro, upstream OpenSpec OPSX); scaffold's sequential freeze is a deliberate forward-guard |
| Mandatory independent-model reviewer (separate LLM) | **Ahead** | `openspec-propose/SKILL.md:96-198` | No peer in industry; GitHub Spec Kit /analyze is optional & self-model; this is scaffold's own innovation |
| Behavioral verify (eyeball live output, smoke tests) | **Ahead** | `openspec-verify-change/SKILL.md:14-31` | Industry verify is mostly checklist. Scaffold's live-output eyeball + external-API live smoke is more rigorous than any tool surveyed |
| Five-field notes.md structured handoff at verify | **Ahead** | `openspec-verify-change/SKILL.md:173-217` | No analog in any industry tool. Unique scaffold design |
| Write-deferred project-doc reconciliation (archive) | **Ahead** | `AGENTS.md:101-110`, `openspec-archive-change/SKILL.md` | Unique token-economy design; no industry analog |
| Spec promotion on archive (delta → main specs) | **Present** | `openspec-archive-change/SKILL.md:75-88`, `openspec-sync-specs` | Matches upstream OpenSpec; no formal analog in GitHub Spec Kit or Kiro |
| Change tiering (SMALL/MEDIUM/COMPLEX) | **Partial** | `ai-docs/fast-track-workflow.md:36-57` | Tiering exists but is fast-track-only (opt-in). Industry tiering is also informal/advisory (no tool has a built-in default tiering standard), so this is an alignment gap in *access*, not design quality |
| EARS notation for AI-readable requirements | **Partial** | Scenarios use WHEN/THEN/AND format, but EARS not explicitly named | Industry (GitHub Spec Kit, Kiro, BCMS guide) explicitly adopts EARS. Scaffold is functionally similar but lacks EARS vocabulary and 5-pattern guidance |
| Agent-onboarding guided walkthrough | **Present** | `openspec-onboard/SKILL.md` | Comparable to GitHub Spec Kit's /constitution + walkthrough pattern; well-designed |
| "Constitution" / project-wide guardrails as first-class artifact | **Partial** | `AGENTS.md` + `openspec/config.yaml` cover this role | Functionally present (AGENTS.md Hard Constraints block, config.yaml context), but not surfaced as a named, first-class "constitution" artifact an agent is directed to maintain separately from AGENTS.md |
| /clarify step (resolve ambiguity before design) | **Absent** | Not present in any scaffold skill | GitHub Spec Kit has optional `/speckit.clarify` before `/speckit.plan`; Kiro does in-process. Scaffold has explore skill but no proposal-phase disambiguation step |
| Concurrent/wave task execution (dependency graph) | **Absent** | Tasks are sequential in scaffold | Kiro builds dependency-graph, runs independent tasks concurrently. Scaffold deliberately sequential (Constraint #1: agent-neutral; wave execution requires tool-native parallelism) |
| Spec→code mechanical traceability (requirement IDs in code/tests) | **Absent** | Not in any skill | Absent in most open-source tools too; low urgency unless compliance required. Noted as industry gap not scaffold gap |
| Reviewer-rejection rationale logging | **Present** | `openspec-propose/SKILL.md:196-199` (overrule documented in review-log.md) | Present and explicit; stronger than industry norms |
| Live API probe before design review | **Ahead** | `openspec-propose/SKILL.md:76-88` | No analog in any industry tool; scaffold-originated |

---

## 6. Candidate Recommendations

### R1 — Explicitly adopt EARS notation in the spec template / design.md Verification section

**The change:** In `openspec/config.yaml` (the `rules.specs` section, added), name EARS as the
required format for scenarios. In the spec delta template and the design.md Verification section
template (injected via `openspec instructions`), provide the five EARS pattern stubs and a note
that EARS-format scenarios are required. This requires editing the schema/template, not the
scaffold files directly (scaffold files remain unedited per the hard constraint); it is a
recommendation for a schema change.

**Source:** EARS is explicitly adopted by GitHub Spec Kit (BCMS, thebcms.com/blog/spec-driven-development),
Kiro's requirements.md, and the Augment Code guide; it traces to Mavin et al. (Rolls-Royce 2009);
GitHub blog 2026: *"An agent can read an EARS requirement, generate the code, and write a test
that verifies it — all without guessing."*

**Confidence:** High — EARS is a field-wide convergence in mid-2026, and the scaffold's existing
WHEN/THEN/AND format is already EARS-compatible; this is a naming + pattern formalization, not
a design change.

**Constraint-compat:** Clean. EARS is a text notation, fully agent-neutral (Constraint #1).
State lives in tracked markdown files (Constraint #2). Works in a generic template (Constraint
#3). No autonomy implications (Constraint #4). Sources are cited above (Constraint #5).

**Effort/Risk:** Low effort (config.yaml `rules.specs` addition + template update); zero risk.

---

### R2 — Add a `/clarify` step (proposal-phase disambiguation) before design generation

**The change:** Add a new optional phase between proposal freeze and design creation: the primary
agent explicitly checks proposal.md for ambiguities, underspecified scope, missing edge cases,
and open assumptions — and prompts the user for answers before starting design.md. This can be
implemented as a new skill (`openspec-clarify`) or as an explicit checklist step added to the
propose skill after proposal review. The propose skill's current step 4b (self-review) could be
extended to produce a list of open questions for the user to answer before proceeding to design.

**Source:** GitHub Spec Kit `/speckit.clarify` (github/spec-kit README, "Clarify underspecified
areas — recommended before /speckit.plan"); Microsoft Developer blog 2026: *"good specs capture
intent, constraints, and acceptance criteria, not just structure."*

**Confidence:** Medium — the scaffold's @openspec-reviewer already catches many of the issues
that /clarify targets. The marginal value depends on how often proposal reviews surface questions
that require user input before the reviewer can act. This is most valuable for brownfield changes
where domain assumptions are project-specific.

**Constraint-compat:** Clean. Text-based, agent-neutral. The clarification state can live in
proposal.md itself (answered questions section) or in notes.md. Requires user interaction, so
this is the normal (non-fast-track) path — aligns with Constraint #4. Phase gate would be
required before design starts.

**Effort/Risk:** Medium (new skill or propose skill extension). Risk: adds a step that currently
works implicitly through reviewer loops; may be unnecessary if the reviewer routinely surfaces
the same gaps.

---

### R3 — Make change tiering visible in the default workflow (not only in fast-track)

**The change:** Add a lightweight "change sizing assessment" step to the normal propose phase
(or as a pre-propose step in explore). The primary agent explicitly states the tier
(SMALL/MEDIUM/COMPLEX) before creating any artifacts, and the tier is recorded in the change's
notes.md. This does NOT relax any gates — it simply makes the sizing decision explicit and
durable for the archive-executor and future readers.

The current fast-track tiering logic (`ai-docs/fast-track-workflow.md`) is excellent but
invisible to the default flow. A user reading AGENTS.md has no visibility into the sizing model
unless they know to look in fast-track-workflow.md.

**Source:** Microsoft Developer blog 2026: *"Not every change needs the full lifecycle, so
adoption should be right-sized."* Augment Code guide's "When to use a spec / skip the spec"
table. BMAD's "Scale-Domain-Adaptive" planning depth adjustment.

**Confidence:** Medium — the sizing decision is already made implicitly (all non-fast-track
changes run the full lifecycle). Making it explicit adds a discoverability and auditability
benefit but changes no behavior.

**Constraint-compat:** Clean. Agent-neutral. State in notes.md (tracked file). Autonomy
unchanged — user still controls which tier applies; fast-track is still required to deviate
from the full lifecycle.

**Effort/Risk:** Low effort (AGENTS.md note + propose skill addition of a size-classification
step). Zero risk; no behavioral change.

---

### R4 — Reference the adversarial agent pattern explicitly in the verify skill as a named practice

**The change:** In `openspec-verify-change/SKILL.md`, name and describe the "adversarial agent
pattern" as the design principle behind the orchestrator-not-delegated verify rule. Add a brief
rationale paragraph: the separate-model @openspec-reviewer in propose, and the orchestrator's
own (non-delegated) behavioral review in verify, together implement the Coordinator + Implementor
+ Verifier pattern — with the primary agent playing Verifier. This is not a behavior change; it
is vocabulary alignment with industry.

**Source:** Augment Code guide (augmentcode.com): *"The most underused pattern in spec-driven
development is assigning a separate agent to check the work rather than trusting the implementing
agent to self-verify... A separate Verifier has a cleaner signal."* arXiv "Spec-Driven
Development: From Code to Contract" (Feb 2026) formalizes Spec-Anchored patterns with
multi-agent governance.

**Confidence:** High — the scaffold already implements this pattern; the recommendation is only
to name it. Naming it helps future operators understand WHY verify must not be delegated (a rule
whose rationale is currently implicit).

**Constraint-compat:** Clean — documentation change only. No constraint implications.

**Effort/Risk:** Trivial effort (one paragraph in one skill file). Zero risk.

---

### R5 — Add a named "constitution" block to the onboard skill's output / AGENTS.md template

**The change:** In the onboard skill and in the AGENTS.md template, add an explicit "Project
constitution" section — a machine-readable list of project-wide ubiquitous rules (tech stack,
style, testing standards, API constraints, cost limits). This is functionally already present in
the "Hard constraints" block of AGENTS.md and in `openspec/config.yaml`'s `context:` field, but
it is not named as a "constitution" nor pointed to explicitly as the first thing an agent must
read before proposing. The onboard skill should explicitly walk the user through filling in the
constitution block of AGENTS.md as Phase 1 before demonstrating any change cycle work.

**Source:** GitHub Spec Kit `/speckit.constitution` command (github/spec-kit README): creates
the project charter as the immutable backdrop for all agent actions. Microsoft Developer blog
2026: *"A constitution file... is essentially a list of ubiquitous EARS statements about the
project itself."*

**Confidence:** Medium — the scaffold's existing AGENTS.md structure and config.yaml context
serve the same function. The gap is discoverability and framing, not missing functionality. The
"constitution" naming and first-class onboarding focus would improve agent cold-start behavior.

**Constraint-compat:** Clean. AGENTS.md is already agent-neutral. The addition is text-only in
a template file. No harness-native state.

**Effort/Risk:** Low effort (onboard skill addition + AGENTS.md template note). Low risk.

---

## 7. Already-Ahead / Doesn't-Fit

### Where the scaffold already meets or beats industry standard

**a) Sequential artifact creation with per-artifact freeze before downstream.** Upstream
OpenSpec's OPSX (`/opsx:propose`) and Kiro Quick Plan batch-create all artifacts in one pass.
The scaffold's "Do NOT batch-create" rule (openspec-propose/SKILL.md:15-19) is a deliberate
quality improvement over upstream. Industry evidence (GitHub Spec Kit blog: *"cheap iterations
on the plan beat expensive iterations on the code"*) confirms the principle, but the scaffold
goes further by enforcing it mechanically.

**b) Mandatory separate-model reviewer (deepseek-v4-pro).** No industry tool has an automated,
independent-model reviewer before artifact freeze. The scaffold's @openspec-reviewer is a
scaffold-originated innovation that the adversarial agent pattern literature validates
retrospectively. It should not be weakened to match tools that lack it.

**c) Live API probe before design review.** `openspec-propose/SKILL.md:76-88`. No analog in any
surveyed tool. Prevents a documented failure class (mocked-test-passing, real-API-crashing).

**d) Behavioral verify: live-output eyeball + live smoke for external APIs.** `openspec-verify-change/SKILL.md:14-31`. Industry verify tools are checklist-based (did tasks complete?). The scaffold's behavioral review is qualitatively stronger.

**e) Five-field structured notes.md handoff.** `openspec-verify-change/SKILL.md:173-217`. The
field-5 "forward-looking items" capture is uniquely robust — no industry tool has a structured
mechanism for this; the common failure mode (open questions lost at session boundary) is a
known industry problem with no standard solution.

**f) Write-deferred project-doc reconciliation at archive.** `AGENTS.md:101-110`. No industry
tool addresses the token-economy cost of in-session STATUS.md updates. This is a scaffold-native
optimization.

**g) Hard phase gates with explicit user approval.** Upstream OpenSpec is "fluid, no phase
gates." The scaffold's hard gates align with GitHub Spec Kit's human-checkpoint model and are
consistent with Constraint #4 (autonomy stays opt-in). This is not a gap versus industry; it is
a deliberate divergence from the upstream's philosophy, and a sound one for multi-session
production use.

### Practices deliberately not recommended

**Concurrent/wave task execution (Kiro dependency-graph waves).** Kiro's parallel task execution
is a compelling performance improvement for large task lists, but it requires tool-native
parallelism primitives that are not agent-neutral. Implementing it would require different
mechanics for Claude Code vs. OpenCode, violating Constraint #1. The benefit is real but the
constraint-compat is poor for a generic neutral template.

**Spec-as-source (code generated from spec, spec is sole truth).** The industry debate between
"spec is truth" vs "code is truth" is unresolved (Thoughtworks remains in the "code is truth"
camp). The scaffold correctly treats specs as governance artifacts and code as the primary
deliverable — this is the "Spec-First" pattern described in the Augment Code guide, appropriate
for teams beginning SDD adoption. The "Spec-as-Source" pattern is explicitly flagged in the
ThoughtWorks Technology Radar (Volume 33, 2025) as risking *"a bias toward heavy up-front
specification and big-bang releases"*. No recommendation to move toward spec-as-source.

**Commercial audit-trail tools (Tessl, Intent/Augment Code).** EU AI Act compliance demand for
audit trails is real. The scaffold addresses this through archived change directories with
complete artifact history. Recommending a specific commercial tool would violate Constraint #3
(generic template). The scaffold's archive pattern is a reasonable open alternative.

**Inline change tiering in default workflow (forced user decision per-change).** BMAD's
scale-adaptive auto-classification is appealing but requires autonomous tier assignment, which
conflicts with Constraint #4. The current explicit opt-in fast-track model is the right balance.

---

## 8. Open Questions for the Operator

1. **EARS adoption scope.** R1 recommends naming EARS in the spec template. The scaffold's
   current WHEN/THEN/AND scenario format is already EARS Event-driven pattern. Should the other
   four EARS patterns (Ubiquitous, State-driven, Unwanted Behavior, Optional Features) be
   explicitly introduced to the template? This would make specs richer but requires schema
   changes.

2. **/clarify as separate skill vs. propose skill extension.** R2 could be a new
   `openspec-clarify` skill or an extended step in `openspec-propose`. Should it be mandatory
   or optional? Given that the @openspec-reviewer often surfaces the same gaps, is a dedicated
   clarify step adding value or redundancy for the typical change?

3. **Constitution naming vs. AGENTS.md stability.** R5 proposes naming the "Hard constraints"
   block in AGENTS.md as a "constitution." AGENTS.md is currently framed as a stable file
   edited sparingly. Would adding a constitution sub-section conflict with the stability rule,
   or would it improve discoverability enough to justify the edit?

4. **Sequential artifact creation vs. upstream's "fluid" philosophy.** Upstream OpenSpec v1.4.1
   default OPSX creates all artifacts in one pass. The scaffold's sequential freeze is
   deliberately stronger. Is there appetite to consider a "proposal-only quick path" for MEDIUM
   changes (fast-track) where proposal + tasks are created sequentially but design.md is
   optional? This is already the fast-track MEDIUM tier — but is it worth surfacing in the
   normal workflow at all?

5. **Spec→code traceability for compliance.** If any instantiated project has EU AI Act or
   similar compliance requirements, the current archive structure (artifacts preserved in
   `openspec/changes/archive/`) may not provide sufficient audit-trail granularity (no
   requirement-ID-to-line-of-code mapping). Is this a gap that any current instantiated project
   faces, or is it future-scope?

6. **Reviewer model selection.** The @openspec-reviewer is hardcoded as `deepseek-v4-pro`. As
   the model landscape changes (new DeepSeek releases, OpenSpec v1.5+), is the model selection
   in the scaffold skill files expected to be updated per-project, or should there be a config
   field in `openspec/config.yaml` for `reviewer_model:`?
