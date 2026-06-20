## Context

The proposal establishes a pre-implementation **premise-review gate** — the direction-level
counterpart to the post-implementation `verify-multimodel-gate`. The mechanics already exist and are
reused: a single `openspec-reviewer` agent (`.opencode/agents/openspec-reviewer.md`), invoked via
`opencode run` with the delegation harness (`.claude/skills/_shared/delegation-harness.md`), emitting
findings to stdout that the primary appends to disk. This design says exactly how the premise lens
attaches to that machinery without disturbing the existing coherence review.

Current state of the touched surfaces:
- The reviewer's mandate (`## What to Check`) is keyed to structured `proposal.md` / `design.md` /
  `tasks.md`; its only verdict is severity-based (`PASS` / `NEEDS REVISION` from 🔴/🟡/💡).
- The propose skill freezes an artifact on **zero 🔴**.
- SMALL has no skill and no pre-apply phase. Its flow is the AGENTS.md SMALL bullet: write a plan to a
  standard dir (change dir or `plans/`) → delegate apply to flash → self-verify (+ one flash verifier).
- `reviewer-budget` asserts propose is "the only workflow that invokes the `openspec-reviewer`."

## Goals / Non-Goals

**Goals:**
- Add a premise verdict (`AGREE` / `DISSENT`) to the reviewer, **orthogonal** to the severity verdict.
- Make the premise verdict load-bearing exactly where direction is decided, at two altitudes: the
  **explore-brief review** (direction, all tiers), the `proposal.md` review (MEDIUM/COMPLEX), and the
  SMALL plan review — and nowhere else.
- Wire `DISSENT` so it always reaches the operator and never silently auto-resolves; carry an explore-stage
  override forward so the later drift check does not re-raise a settled dissent.
- Define the explore direction gate (owner, trigger, file location, sink) and the SMALL pre-apply pass.
- Keep one reviewer agent and one invocation harness; no new agent, no new model tier.

**Non-Goals:**
- No change to `verify-multimodel-gate` (post-implementation, behavioral) or to the verifier agent.
- No change to the severity system, the propose sequence, or the apply/archive delegation ladders.
- No application/runtime code. No new external dependency.
- Not building tooling to *enforce* SMALL-plan structure programmatically — it's a documented contract.

## Decisions

### D1 — Two orthogonal verdicts; premise verdict emitted only for direction artifacts
The reviewer emits its existing severity verdict (`PASS`/`NEEDS REVISION`) **and**, when the artifact
under review is a **direction artifact** — an `explore-brief.md`, a `proposal.md`, or a SMALL plan — a
premise verdict. For `design.md` / `tasks.md` reviews it emits no premise verdict (the premise was settled
upstream). The invocation prompt signals "this is a premise review" so the reviewer knows to include the
block. *Alternative considered:* always emit a premise verdict — rejected because it invites premise
re-litigation on every downstream artifact, re-opening frozen direction during implementation.

**Output format (deterministic, so the proposer can parse it).** After the existing `### Verdict` block,
the reviewer emits a `### Premise Verdict` section containing exactly one line — `PREMISE: AGREE` or
`PREMISE: DISSENT` — followed by a bullet list of cited concerns (or `- None`). This format is added to
the reviewer agent's `## Output Format` section.

### D2 — Freeze rule: `proposal.md` requires zero 🔴 **AND** `PREMISE: AGREE`
The propose skill's freeze step gains one clause **for `proposal.md` only**: freeze iff zero 🔴 **and**
`PREMISE: AGREE`. A `PREMISE: DISSENT` blocks the freeze **regardless of severity count** (the clean-but-
wrong-premise case). `design.md` / `tasks.md` keep the existing zero-🔴 rule unchanged. This resolves the
Round-1 🔴: a DISSENT can no longer be bypassed by an auto-freeze.

### D2a — Assert the PREMISE line is present (load-bearing defense against omission)
When reviewing `proposal.md`, the propose skill SHALL assert the reviewer output contains a
`PREMISE: AGREE` or `PREMISE: DISSENT` line, as an extension of the existing "assert the real reviewer
ran" check (propose skill Step 3c, which today confirms a `## Review Round` heading + a severity marker).
A **missing** `PREMISE:` line is treated as a failed pass — do **not** freeze, re-run — because a clean
zero-🔴 review that silently omitted the premise verdict (stale agent, model misread the prompt) would
otherwise auto-freeze and defeat the gate.

### D2b — Surfacing a DISSENT to the operator (exact propose-skill protocol)
A `DISSENT` is a direction fault, not an artifact defect, so it cannot be auto-fixed by the existing
"fix 🔴 → re-review" loop. When the `proposal.md` review returns `PREMISE: DISSENT`, the propose skill
SHALL stop the freeze loop and present the cited concern(s) to the operator via **`AskUserQuestion`** with
three options — **(1) re-frame the proposal**, **(2) re-scope**, **(3) override-to-proceed** — and record
the operator's choice + rationale in `review-log.md`. Only option (3) permits freezing on a DISSENT;
options (1)/(2) loop back to revise the proposal and re-review. **After override-to-proceed the freeze
condition reverts to zero 🔴 only** — the DISSENT is the operator's call and is not re-litigated on
re-review. This is a **new branch** in the propose skill's review-processing step (it has no such branch
today).

### D3 — The premise lens (exact reviewer-mandate additions)
A new `### Premise review (proposal.md and SMALL plans only)` subsection in the reviewer's `## What to
Check`, placed **after the per-artifact subsections** (`For proposal.md` / `design.md` / `tasks.md`),
with four checks: (1) **root, not symptom** — is the stated problem the real cause, or a surface
symptom? (2) **solution targets root** — does the proposed approach actually resolve that cause? (3)
**scope right-sized** — is scope materially over/under-set, and is what's-out stated? (4) **blind spot** —
name the consideration the author missed. Framing is **default-to-dissent**: the reviewer must state
where the framing is *wrong* and why; if it cannot fault the framing it says so explicitly (it does not
manufacture agreement). **Read-only honesty caveat** (added to Anti-Patterns): the reviewer is
`bash: deny` — it *reasons* about root cause from reading the code; it does not and cannot reproduce it,
and must not claim empirical confirmation (consistent with the existing "affirming unverifiable empirics"
anti-pattern).

### D4 — Dissent calibration (prevents dissent-on-everything)
`DISSENT` is reserved for **genuine direction faults**: wrong/symptomatic problem, solution that misses
the root, materially wrong scope, or a critical missed consideration. Style, taste, wording, and
non-direction improvements stay in 🟡/🟢 severity and do **not** trigger `DISSENT`. The mandate states
this explicitly so "default-to-dissent" means "don't manufacture agreement," not "object to everything" —
a gate that always dissents is as useless as one that rubber-stamps.

### D5 — SMALL pre-apply premise pass: one invoker, one gate
Resolves the invoke-vs-gate ambiguity by assigning each role to exactly one actor:
- **Invoker = the orchestrator (not the apply skill).** In the SMALL flow the orchestrator runs the
  premise pass **after the plan is written and before apply delegation** — a trigger **independent of
  operator confirmation**, so it fires identically with or without an autonomy grant. It extracts the
  verdict from the reviewer's jsonl stdout (the reviewer is `edit: deny` and cannot write files), names
  the plan file in the invocation prompt and signals "premise review" per D1, and writes the verdict to
  `premise-review.md`. **No autonomy grant:** the orchestrator presents the verdict *inside* the tier+plan
  confirmation prompt, so a `DISSENT` reaches the operator by construction (handled like D2b). **Under an
  autonomy grant** (no confirmation prompt exists): the autonomy grant covers tier self-classification,
  **not** overriding a premise dissent — a `DISSENT` with no recorded operator override is left in
  `premise-review.md`, the apply gate STOPs on it, and the orchestrator escalates to the operator. This
  rule lives in the **AGENTS.md SMALL bullet**.
- **Gate = the apply skill (does not invoke).** The apply skill gains a gate that runs **after change
  selection (Step 1) and before implementation delegation (Step 6)**: for a SMALL change, it asserts
  `premise-review.md` exists and its verdict is resolved (`AGREE`, or a recorded operator
  override-to-proceed) before delegating apply; otherwise it STOPs. The apply skill never runs the
  `opencode run` invocation itself — that avoids a double-invocation and avoids a DISSENT arriving after
  apply has begun. MEDIUM/COMPLEX skip this gate (they got their premise review at propose).
- **Invocation + budget.** Same hardened `opencode run --agent openspec-reviewer` shape as the propose
  reviewer but `--model deepseek/deepseek-v4-flash`, with `timeout -k 15 780` — the **same envelope as the
  verifier flash pass** (a flash review of a short plan finishes well inside; the budget is a backstop, not
  a target). `tasks.md` adds a `SMALL | premise reviewer (flash) | -k 15 780` row to the delegation-harness
  budget table so the invocation is traceable (the table's first column is normally an OpenSpec phase; this
  row is keyed by the SMALL tier since the pass runs outside the named phases — `tasks.md` notes this). **On timeout/crash** the orchestrator applies the same
  salvage rules as the propose reviewer (extract partial; re-run once if >120s elapsed or any finding
  present; else escalate), writing the partial to `premise-review.md` marked `PARTIAL`.
- **Plan input-shape (contract).** For the reviewer to do its job, a SMALL plan SHALL contain at minimum:
  a **problem statement**, a **proposed approach/fix**, and an explicit **out-of-scope** note. This minimal
  anchor is documented as a `Plan minimum:` sub-point in the AGENTS.md SMALL bullet; it is a contract, not
  enforced tooling — a structurally inadequate plan is flagged by the reviewer as a finding rather than
  guessed at.
- **Verdict sink.** SMALL has no `review-log.md`; the orchestrator writes the extracted verdict to
  `premise-review.md` in the change/plan dir. For MEDIUM/COMPLEX the premise block is part of the proposal
  review already appended to `review-log.md`.

### D6 — `reviewer-budget` delta (the added invocation paths)
Update the `reviewer-budget` requirement so the "only workflow that invokes the `openspec-reviewer`"
claim becomes "the workflows that invoke the reviewer: the `openspec-propose` proposal review, the
**explore direction gate**, and the **SMALL pre-apply premise pass**." All run under the same envelope
(≥780s runaway backstop, `-k 15` soft-kill, incremental emission, partial salvage). No separate budget
number per path — the envelope is a ceiling, not a target. The delta also **adds a scenario** covering the
non-propose invocation paths (or generalizes the existing "WHEN the reviewer is invoked from the propose
workflow" scenario to cover all paths).

### D7 — The explore direction gate (Altitude 1): owner, trigger, invocation
- **Owner = the explore skill.** The skill invokes the reviewer itself via `opencode run` using the
  existing delegation harness — the same pattern the propose skill uses. **Concretely, the explore skill's
  existing `PHASE GATE` block is augmented**: on an advancement signal it now (1) writes
  `explore-brief.md`, (2) runs the premise review, (3) presents the verdict and resolves any `DISSENT`
  (D9), and only then (4) surfaces the advancement hint **naming the captured slug** (e.g. "Direction
  captured as `add-user-auth` — say 'propose add-user-auth' when ready") so the propose skill can locate
  and relocate the brief (D8). This replaces the passive "tell the user they can propose" message with an
  active gate. No new lifecycle *step* is added to `AGENTS.md` (the explore phase gates advancement
  internally); AGENTS.md prose still changes per D5 and the Verification section.
- **Trigger = an explicit advancement choice, not keyword-sniffing.** Rather than parse free text for
  "propose"/"let's go" (fragile — false positives and misses), when exploration crystallizes the skill
  **offers** the operator an explicit option ("Ready to act on this? I'll capture the direction and run
  the premise gate"). The gate fires on that choice. The operator can also invoke it directly ("gate the
  brief"). Idle thinking-aloud produces nothing — the founding "no mandatory output" principle holds; the
  brief is a *response to an explicit advancement*, not an automatic artifact.
- **Model = `deepseek/deepseek-v4-pro`** for all tiers (direction is where a wrong call costs most), under
  the same 780s / `-k 15` envelope (D6).
- **Invocation shape.** Same hardened call the propose skill uses (`< /dev/null`, `--dir <repoRoot>`,
  capture stdout/stderr to separate files, the assert-ran check), but the prompt names
  `plans/<slug>/explore-brief.md` and signals "premise review — direction"; the reviewer emits the
  `### Premise Verdict` block (D1) assessing the four checks (D3) against the brief. The orchestrator
  applies the standard salvage rules on timeout/crash, writing any partial to `premise-review.md`.

### D8 — Explore-brief file location, slug, and verdict sink
The explore stage usually runs before any change directory exists (the propose skill creates it). To give
the brief and its review output a stable home **without forcing an early `openspec new change`**, the
explore skill writes both to a **`plans/<slug>/` directory** (created with `mkdir -p` on first write):
`plans/<slug>/explore-brief.md` and the review output to `plans/<slug>/premise-review.md` (the orchestrator
extracts the verdict block from the reviewer's stdout, since the reviewer is `edit: deny`).
- **Slug.** The explore skill derives `<slug>` as a kebab-case identifier from the exploration topic — the
  same convention the propose skill already uses to derive a change name from a description (e.g. "add user
  auth" → `add-user-auth`). No operator prompt needed; if it collides with an existing `plans/` entry, the
  skill appends a short disambiguator.
- **Relocation (fork resolved — relocate, do not reference).** When the operator advances to `propose`, the
  propose skill creates the change dir and **moves** `plans/<slug>/explore-brief.md` and `premise-review.md`
  into `openspec/changes/<name>/`, so all of a change's artifacts live together in the canonical
  mandatory-read location. For a SMALL change (no propose), the brief and verdict stay in `plans/<slug>/`,
  which is also where the SMALL plan lives. *Alternative considered:* leave the brief in `plans/` and
  reference it — rejected because split artifact homes make the change dir an incomplete record.
- *Alternative considered:* create the change dir eagerly at explore — rejected because exploration may not
  become a change, leaving orphan change dirs.

### D9 — DISSENT at explore, and override propagation to Altitude 2
A `PREMISE: DISSENT` at explore is surfaced to the operator (the explore skill is already interactive) via
the same three-way decision as the proposal path (D2b): re-think direction / re-scope / override-to-proceed.
**Recording format (machine-parseable).** `plans/<slug>/premise-review.md` holds the extracted
`### Premise Verdict` block (`PREMISE: AGREE` or `PREMISE: DISSENT`); when the operator overrides a
`DISSENT`, the skill appends a `### Resolution` section below it containing a single marker line
`OVERRIDE: proceed — <rationale>`. **Override propagation:** the Altitude-2 drift check (D10) and the SMALL
apply gate treat direction as *settled* when the sink contains either `PREMISE: AGREE` **or**
`OVERRIDE: proceed` — so an overridden `DISSENT` is not re-raised as fresh. (`re-think`/`re-scope` instead
loop back to revise the brief and re-review; no `OVERRIDE` line is written.)

### D10 — "Drift" has a concrete definition
When a verified `explore-brief.md` is handed to a later review (SMALL plan pass or MEDIUM/COMPLEX proposal
review) as context, **drift** means the later artifact: (a) reframes the problem differently from the
brief's verified problem; (b) changes to an approach the brief explicitly ruled out; or (c) expands scope
beyond what was vetted at explore. **Narrower scope, restatements, and added implementation detail are NOT
drift.** Drift is reported through the normal `PREMISE: DISSENT` (it is a direction change that was never
verified). This keeps the "also flag drift" instruction concrete rather than leaving the reviewer to guess.

### D11 — Altitude 1 calibration (dissent from an abstract brief)
The explore brief is abstract — problem/solution framing, no concrete scope or implementation constraints.
Applied naively, default-to-dissent on sparse input would over-fire. The mandate states: at the explore
altitude the reviewer dissents when the direction is **demonstrably wrong given the information available**
(symptom mistaken for root, solution that cannot address the stated problem, a ruled-out-by-evidence
approach) — **not** merely because the brief is under-specified (under-specification is expected at explore
and is a 🟡/💡 note, not a `DISSENT`). At the explore altitude the scope check (D3 check 3) is typically
not yet concrete; the reviewer notes "scope not yet concrete — deferred to proposal" rather than treating
it as a fault.

**Placement.** D10 (drift) and D11 (explore-altitude calibration) are added as paragraphs **within** the
`### Premise review` subsection of the reviewer's `## What to Check` (the same subsection D3 introduces) —
not as new top-level sections or under Anti-Patterns.

## Risks / Trade-offs

- **Two verdicts confuse the reviewer model (it emits one, omits the other)** → Mitigated by D2a: the
  invocation prompt explicitly requests the premise block for direction artifacts, and the propose skill
  asserts the `PREMISE:` line is present, treating its absence as a failed pass (re-run, don't freeze).
- **Dissent-on-everything erodes the gate** → Mitigated by D4 calibration; if false-positive dissent
  recurs in practice, the operator override path (D2) keeps it from blocking work while the mandate is
  tuned.
- **SMALL cost doubles (1 → 2 flash calls)** → Accepted in the proposal; flash is the cheap tier and the
  pass guards the highest-leverage decision (direction) on the only path with no other pre-impl review.
- **SMALL plans without the D5 structure get a weak review** → The reviewer flags a structurally
  inadequate plan as a finding rather than guessing; the contract is documented in AGENTS.md so authors
  know the minimum.
- **Scaffold drift across downstream repos** → The reviewer-mandate, skill, and AGENTS.md edits are
  scaffold-managed; propagation uses the standard `sync_scaffold.py` + `scaffold_check.py` path. Per-repo
  knowledge is untouched, so no manual knowledge sweep is needed.

## Migration Plan

Pure documentation/workflow change; no runtime migration, no data. Rollback = `git revert` the change
commit(s). Downstream repos receive it on their next scaffold sync.

## Open Questions

None blocking. (The SMALL-plan structure is a documented contract per D5; tightening it into tooling, if
ever wanted, is a separate future change.)

## Verification

Acceptance criteria for this change (checked at verify):
- **Reviewer mandate.** `.opencode/agents/openspec-reviewer.md` contains the `### Premise review`
  subsection (the four checks of D3), the default-to-dissent + read-only-honesty framing (D3/D4), the
  explore-altitude calibration (D11: dissent when demonstrably wrong, not merely under-specified), the
  "also flag drift" instruction with the D10 definition, and the `### Premise Verdict` /
  `PREMISE: AGREE|DISSENT` output format scoped to direction artifacts — `explore-brief.md` / proposal.md /
  SMALL plans (D1).
- **Explore direction gate (D7–D9).** `.claude/skills/openspec-explore/SKILL.md` produces
  `plans/<slug>/explore-brief.md` and runs the pro premise review only on an operator advancement signal
  (D7), preserving "no mandatory output" for idle exploration; it invokes the reviewer via `opencode run`
  (same harness), writes the extracted verdict to `plans/<slug>/premise-review.md` (D8), surfaces a
  `DISSENT` to the operator with the three-way decision, and records an override alongside the verdict so
  Altitude 2 does not re-raise it (D9). It STOPs before advancing until the verdict is resolved.
- **Brief relocation.** `.claude/skills/openspec-propose/SKILL.md` relocates `plans/<slug>/explore-brief.md`
  and `premise-review.md` into the change dir when a verified brief exists (D8), and best-effort skips when
  no matching `plans/` dir is found.
- **Freeze rule.** `.claude/skills/openspec-propose/SKILL.md` requires, for `proposal.md`, zero 🔴 **and**
  `PREMISE: AGREE` to freeze (D2); asserts the `PREMISE:` line is present, treating absence as a failed
  pass (D2a); and has the `DISSENT` → `AskUserQuestion` (re-frame / re-scope / override-to-proceed) branch
  recording the choice in `review-log.md` (D2b). The reviewer invocation prompt requests the premise
  assessment.
- **SMALL pass — invoker vs. gate (D5).** The AGENTS.md SMALL tier bullet documents the orchestrator
  invoking the flash premise pass **before apply delegation** (which, with no autonomy grant, is before the
  operator tier+plan confirmation), the `timeout -k 15 780` flash
  invocation, the orchestrator writing the extracted verdict to `premise-review.md`, and the plan
  input-shape contract (problem / approach / out-of-scope). The apply skill has the pre-Step-1 **gate**
  (assert `premise-review.md` resolved for SMALL; STOP otherwise) and does **not** invoke the reviewer.
- **Budget table.** `.claude/skills/_shared/delegation-harness.md` has rows for both new invocation paths
  — `explore | direction gate (pro)` and `SMALL | premise reviewer (flash)` — at `-k 15 780`.
- **Drift handling.** Both the SMALL plan pass and the MEDIUM/COMPLEX proposal review, when a verified
  `explore-brief.md` exists, receive it as context with the D10 "flag drift" instruction; drift surfaces as
  a normal `PREMISE: DISSENT`.
- **Specs.** `openspec/specs/premise-review-gate/spec.md` exists and encodes the requirements above;
  `openspec/specs/reviewer-budget/spec.md` is delta'd per D6 (requirement text says **three** invocation
  paths **and** scenarios for both the SMALL premise pass and the explore direction gate). `openspec
  validate` passes (command confirmed available in this repo's `openspec` CLI).
- **AGENTS.md.** Lifecycle/roles, the SMALL tier bullet (including the plan-structure minimum: problem /
  approach / out-of-scope), and the "After reading this file" acknowledgements name the **two-altitude**
  pre-implementation premise gate (direction at explore; change-itself at propose/apply).
- **Scaffold.** `python3 scripts/scaffold_check.py` passes and `sync_scaffold.py --check` reports no
  unexpected drift for the edited scaffold-managed files.
- **Behavioral smoke (BLOCKING — live, not mocked):** the gate's entire purpose is to be able to say no, so
  verify runs a **live** flash premise pass against a deliberately symptom-level plan and confirms it emits
  `PREMISE: DISSENT` with a cited root-cause concern. A gate that cannot dissent is a failed change.
