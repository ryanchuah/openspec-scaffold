# Review Log — premise-review-gate

## proposal.md — Round 1 (deepseek-v4-pro, 2026-06-20) — VERDICT: NEEDS REVISION

## Review Round 1 — proposal.md

### Summary

The proposal identifies a real and non-trivial gap: the current workflow has no systematic, institutionalized pre-implementation review of a change's *direction* (problem / root cause / solution). For SMALL changes, a plan reaches `apply` with zero independent pre-implementation scrutiny. For MEDIUM/COMPLEX, the existing `@openspec-reviewer` is structured around coherence (well-formedness, scope, ambiguity) and is not explicitly mandated to contest whether the *premise* is right at all. The proposed direction — a premise-review gate that is the symmetric pre-implementation twin of the existing post-implementation `verify-multimodel-gate`, with the same per-tier model tiering — is architecturally sound and well-integrated into the existing gates (`tier-confirmation-gate`, the verify gate). However, there are two substantive defects that would cause the implementer to either silently ship a broken interaction or produce a design that misses a critical process gate.

---

### 🔴 Blocking Issues

1. **DISSENT verdict interaction with the propose freeze logic is entirely unspecified.**  
   - **Location:** `## What Changes` lines 25–33, `## Capabilities` lines 40–43, and the proposal's silence on the freeze rule.  
   - **Why it blocks:** For MEDIUM/COMPLEX, the proposal says the premise lens is "folded into the existing `deepseek/deepseek-v4-pro` proposal review." The current propose skill freezes an artifact when the reviewer returns zero 🔴 issues. The proposal introduces an AGREE/DISSENT verdict that is *independent* of the 🔴/🟡/💡 severity system. A reviewer could return **zero 🔴 issues** (artifact is coherent and well-formed) but **DISSENT** (the premise — the problem or root cause — is wrong). Under the current freeze rule, the artifact would auto-freeze. The DISSENT would land in `review-log.md` and be silently bypassed.  
   - **Why it matters:** The proposal's own framing says DISSENT is "surfaced to the operator, not silently auto-resolved" (line 32–33). This intent contradicts the existing freeze logic. If this interaction is not resolved *before* implementation begins, the design.md will inherit an ambiguous mandate and the implementation will likely auto-freeze on the existing PASS/NEEDS REVISION check, producing exactly the rubber-stamp-by-accident that the proposal is trying to prevent.  
   - **What the proposal needs:** An explicit statement that for MEDIUM/COMPLEX, a DISSENT verdict blocks artifact freeze and must be surfaced to the operator — or, alternatively, a clear declaration that DISSENT is informational only (and why that doesn't undermine the gate). The exact mechanism can be deferred to design.md, but the *decision about the interaction* must be present in the proposal.

2. **reviewer-budget spec's "only workflow" claim becomes false, but the proposal declares reviewer-budget "not modified."**  
   - **Location:** `## Capabilities` → `### Modified Capabilities` comment (lines 46–49), and the `openspec/specs/reviewer-budget/spec.md` requirement at line 9: "the `openspec-propose` workflow, which is the **only workflow that invokes the `openspec-reviewer`.**"  
   - **Why it blocks:** The proposal adds a second invocation path for the `openspec-reviewer` agent: the SMALL premise pass, which runs *before* apply — i.e., outside the `openspec-propose` workflow. The reviewer-budget spec's foundational claim becomes factually incorrect. The proposal's comment says reviewer-budget is not modified, but the SMALL premise pass needs a budget (or at minimum an explicit declaration that it operates without one). Without resolution, the implementer faces an ambiguity: apply the 780s reviewer-budget to every SMALL flash pass (expensive — 780s for a flash-tier pass), or skip the budget entirely (risk timeout with no salvage path, since the incremental-emission/salvage rules live in reviewer-budget).  
   - **What the proposal needs:** Either (a) flag reviewer-budget as needing a minor update to acknowledge the SMALL premise pass path and optionally scope its budget, or (b) explicitly state in the new capability requirements that the SMALL premise pass has its own budget specification (which design.md will define), making it clear that reviewer-budget's "only workflow" claim is intentionally superceded. The current "not modified" assertion is misleading.

---

### 🟡 Should Fix

3. **SMALL premise pass placement in the SMALL flow is vague.**  
   - **Location:** `## What Changes` lines 21–24, `## Impact` line 59.  
   - **Why it matters:** The proposal says the premise pass runs "before `apply`" and feeds the `tier-confirmation-gate`. But it doesn't say *when* in the sequence (before tier confirmation? after? as part of it?) or *where* in the affected files (a new step in the apply skill? a separate pre-apply gate?). The `.claude/skills/openspec-apply-change/SKILL.md` is listed as impacted, but that skill currently has no "pre-apply" phase — it starts with "Select the change" and proceeds directly to status/invoke. The design.md author will need to invent the flow from scratch rather than refine a stated intent.  
   - **Suggestion:** Add a sentence clarifying that the premise pass runs *after* the plan is written and *before* the operator confirms the tier+plan — so the operator sees the premise verdict as part of the confirmation checkpoint.

4. **The reviewer mandate expansion references a non-existent design.md.**  
   - **Location:** `## What Changes` lines 28–29: "see the reviewer-mandate summary in design.md."  
   - **Why it matters:** This is a forward reference that can't be verified at proposal time. The proposal should either include enough mandate direction to be self-contained (e.g., a one-paragraph summary of what the premise lens adds to the reviewer's checklist), or explicitly state what design.md must resolve: the new input shape (SMALL plans vs. structured artifacts), the AGREE/DISSENT output format, and the anti-rubber-stamp framing. The reference to a non-existent file is harmless but the missing content leaves the reviewer mandate expansion underspecified.

5. **SMALL "plan" input shape for the premise reviewer is undefined.**  
   - **Location:** `## What Changes` line 22: "the change's plan gets one `deepseek/deepseek-v4-flash` premise review (a flash invocation of the same `openspec-reviewer` agent against the plan)."  
   - **Why it matters:** The `openspec-reviewer` agent's current mandate is structured around reviewing `proposal.md`, `design.md`, and `tasks.md` — artifacts with a known template-driven structure (see the reviewer prompt's "What to Check" section, which enumerates checks for each artifact type). A SMALL plan has no mandated structure (AGENTS.md says "write a plan checkpointed to a standard dir"). The reviewer would not know *what* to check in an unstructured plan document. The proposal should acknowledge this as a scope item that design.md must resolve (either by giving SMALL plans a minimal structure, or by expanding the reviewer mandate to handle unstructured plans).

---

### 💡 Suggestions

6. **"Symmetric twin" framing is elegant but slightly imprecise.** The verify gate is a multi-pass behavioral review of implemented code; the premise gate is a single-pass logical review of direction. They're *complementary*, not truly symmetric. Precision here would help the design.md author reason correctly about differences (e.g., the premise reviewer doesn't re-run a test suite because there's no code yet).

7. **"Default-to-dissent" calibration risk.** The proposal says the reviewer mandate is written "default-to-dissent" to prevent rubber-stamping. Consider whether an overly aggressive dissent stance produces too many false positives that erode the gate's credibility over time. The design.md should address calibration — a reviewer that dissents on every change is as useless as one that rubber-stamps. This is a warning for the design phase, not a proposal defect.

8. **Cost note (line 65) could be more precise.** "One flash call per SMALL change" is correct for the premise pass, but a SMALL change already pays one flash verifier pass (post-implementation). The total SMALL cost increases from 1 flash call to 2 flash calls. Stating the incremental cost explicitly avoids a future reader thinking SMALL remains at 1 flash call total.

---

### Verdict

**NEEDS REVISION** — address the two 🔴 blocking issues before proceeding to design.md. Both are resolvable with small additions to the proposal (a sentence on DISSENT-and-freeze interaction, and an acknowledgment of the reviewer-budget overlap). The 🟡 items are important for a clean design phase but are not hard blockers.

---

## proposal.md — Round 2 (deepseek-v4-pro, 2026-06-20) — VERDICT: PASS (froze; 2 non-blocking 🟡 folded in)

## Review Round 2 — proposal.md

### Summary

Both 🔴 issues from Round 1 are concretely and completely addressed. The DISSENT-vs-freeze interaction is now explicit (line 40–43: freeze requires both zero 🔴 AND `AGREE`), and reviewer-budget is correctly listed under Modified Capabilities (lines 55–61) with the second invocation path acknowledged and the delta scoped. All five 🟡/💡 items from Round 1 have also been addressed or appropriately deferred. The proposal is internally coherent, well-scoped against the existing specs (verify-multimodel-gate, tier-confirmation-gate, reviewer-budget), and identifies its own open design items honestly. I find no remaining blocking defects.

### 🔴 Blocking Issues

None.

### 🟡 Should Fix

1. **SMALL premise pass survival path is underspecified.** The proposal states the SMALL premise verdict is "surfaced *as part of* that operator confirmation checkpoint" (line 35). But SMALL changes have no `review-log.md`, and the reviewer's output currently flows through stdout → primary appends to `review-log.md` (per reviewer-budget spec §"The reviewer remains read-only"). Where does the SMALL premise verdict land — a temp file? stdout inline in the operator prompt? — is left to design.md. This isn't blocking because design.md can resolve it, but the Impact section lists only AGENTS.md and the apply skill as SMALL-flow targets (line 74); it should also note that *the verdict sink* (where the SMALL premise output is recorded) is a design-phase item, to prevent the implementer from defaulting to a `review-log.md` that doesn't exist in the SMALL flow.

2. **"A proposal SHALL freeze" ambiguity — proposal.md vs. all artifacts.** Line 40–41 says "for MEDIUM/COMPLEX a proposal SHALL freeze only when the review returns **zero 🔴 AND `AGREE`**." Since the premise lens is folded into the *proposal* review (line 37–38), this rule naturally applies to proposal.md — but the phrasing "a proposal SHALL freeze" could be read as applying to every artifact reviewed during the propose phase (proposal.md, design.md, tasks.md). The intent is almost certainly proposal.md only (the premise is stated there; design.md and tasks.md are about implementation), but the ambiguity leaves the design.md author to guess whether the DISSENT gate applies to all three artifact reviews or only the first. A one-word clarification ("proposal.md SHALL freeze" or "the proposal artifact SHALL freeze") would resolve it.

### 💡 Suggestions

3. **SMALL plan structure could use a minimal anchor.** The proposal correctly identifies the SMALL plan's free-form nature vs. the reviewer's structured-artifact checklist as an open design item (line 78). Consider noting one concrete minimum in the proposal: design.md should define the minimal structure a SMALL plan must have for the premise reviewer to do its job (e.g., a problem statement, proposed fix, and explicit out-of-scope). This gives design.md a starting point rather than a blank slate.

4. **Round 1 review-log duplication.** The `review-log.md` file (lines 3–5) retains the original spurious line "Now let me read the key reference files to understand the current SMALL flow..." — a leftover from the Round 1 reviewer's reactive preamble that wasn't cleaned up before appending the review. Harmless noise but worth scrubbing at some point.

### Premise Assessment (required by the proposal's own framing)

- **Is the problem real and root?** Yes. The gap is genuine: the current workflow vets implementation correctness post-hoc (verify-multimodel-gate) but has no systematic institution-level check on direction pre-implementation. The operator has been filling this gap manually — the change institutionalizes that into the scaffold.
- **Does the solution address the root?** Yes. The premise-review gate is architecturally clean: a single-pass logical counterpart to the multi-pass behavioral verify gate, tier-proportioned (flash for SMALL, folded into existing pro review for MEDIUM/COMPLEX at zero marginal cost), with a machine-discriminable verdict orthogonal to the severity system.
- **Is the scope right-sized?** Yes. Scope boundaries are explicit (new spec + delta for reviewer-budget; verify-multimodel-gate and tier-confirmation-gate interacted-with but not requirement-modified). Out-of-scope items are declared.
- **Blind spots:**
  - The SMALL plan's free-form shape vs. the reviewer's structured-artifact checklist is acknowledged as an open design item. ✓
  - The SMALL verdict sink (where the output lands) is not specified — flagged as 🟡 above.
  - The "default-to-dissent" calibration risk is identified and deferred to design.md. ✓

### Verdict

**PASS** — ready to freeze and move to `design.md`. The two Round 1 🔴 issues are fully resolved, no new blocking defects found, and the 🟡 items above are clarifications that design.md can resolve without re-opening the proposal.

---

## design.md — Round 1 (deepseek-v4-pro, 2026-06-20) — VERDICT: NEEDS REVISION (4 🔴 addressed)


---

## Review Round 3 — design.md

### Summary

The design is architecturally well-rooted: it reuses the existing `openspec-reviewer` agent and `opencode run` harness, adds an orthogonal premise verdict without disturbing the severity system, and correctly scopes the premise lens to direction artifacts only. D1-D6 make sound decisions individually. However, four decisions have **execution gaps** that would force the implementer to invent protocol in real-time: D5's SMALL pass placement is self-contradictory, D2's operator-surfacing mechanism is underspecified, the PREMISE-line assert-ran check is tucked in Risks rather than Decisions, and the SMALL reviewer's budget row is missing from the shared harness table. Two additional 🟡 issues compound the rework risk. None of these are conceptual — all are wiring-level specification gaps a `tasks.md` author can't resolve.

---

### 🔴 Blocking Issues

#### 1. D5 — SMALL premise pass placement is self-contradictory; implementer cannot determine who invokes it

- **Location:** D5 `Placement` sentence vs. the procedural sentence that follows (design.md lines 72–73).
- **The contradiction:** The first sentence says *"the orchestrator runs the premise pass after the plan is written and before it asks the operator to confirm tier+plan."* The next sentence says *"Procedurally this is documented … as a SMALL-gated pre-apply step in the apply skill (the invocation)."* These are two different execution sites:
  - **Orchestrator-side:** The orchestrator runs the `opencode run --agent openspec-reviewer --model …flash` invocation, captures the verdict, and presents it in the tier-confirmation prompt. The apply skill is never involved in the invocation.
  - **Apply-skill-side:** The apply skill gains a new Step 0 that runs the premise pass before "Select the change" (Step 1). But the apply skill is invoked *after* tier confirmation — the operator has already confirmed — so the `DISSENT` verdict wouldn't reach the operator unless the apply skill itself pauses and re-prompts.
- **Why it blocks:** The implementer modifying the apply skill (which is one of the scaffold-managed files listed in `Impact`) doesn't know whether to write the `opencode run` invocation there, or to write a passive gate (check that `premise-review.md` exists and its verdict was handled). If they guess wrong, either the invocation happens after operator confirmation (meaning DISSENT doesn't reach the operator) or the invocation is duplicated (once by the orchestrator, once by the skill). The AGENTS.md SMALL bullet update and the apply-skill update must agree on *who invokes* and *who gates*.
- **What's needed:** D5 must unambiguously assign the invocation to ONE actor. The natural fit: the **orchestrator** runs the premise pass (it already handles tier confirmation), writes the verdict to `premise-review.md`, and presents it in the confirmation prompt. The **apply skill** then gates on it — a new pre-Step-1 check that, for SMALL changes only, `premise-review.md` exists and either says `AGREE` or the operator's override-to-proceed is recorded. This split avoids the contradiction.

#### 2. D2 — "Surfaced to operator" mechanism has no UX specification

- **Location:** D2 (design.md lines 45–50), and the proposal's framing (proposal.md lines 42–45).
- **The gap:** D2 says `PREMISE: DISSENT` *"blocks the freeze regardless of severity count … and is surfaced to the operator for a direction decision — re-frame, re-scope, or an explicit operator override-to-proceed (recorded in review-log.md)."* But the design never says **how** the proposer surfaces it. Does the propose skill:
  - (a) Use `AskUserQuestion` to present the DISSENT and ask the operator what to do?
  - (b) Halt with a message and wait for the operator to respond in the chat?
  - (c) Auto-escalate and stop proposing until the operator intervenes?
- **Why it blocks:** The propose skill currently handles 🔴 issues by fixing the artifact and re-invoking the reviewer (up to 3 passes). A `DISSENT` cannot be auto-fixed — it's a direction issue, not an artifact defect. The propose skill's Step 3c currently has no "surface to operator and wait for direction decision" branch. The implementer needs to know the exact protocol: whether to invoke `AskUserQuestion`, what the options presented are, and where the operator's override is recorded. Without this, the implementer will either auto-escalate (breaking the flow) or silently skip the DISSENT (breaking the gate).
- **What's needed:** D2 (or a new D2a) should specify: *"When the proposal review returns `PREMISE: DISSENT`, the propose skill stops the freeze loop, presents the DISSENT concern(s) to the operator via `AskUserQuestion` with three options — (1) re-frame the proposal, (2) re-scope, (3) override-to-proceed — and records the operator's choice + rationale in `review-log.md` before proceeding. Only option (3) allows freeze on a DISSENT."*

#### 3. D1/D2 — PREMISE line assert-ran check is ghettoized in Risks, not promoted to a Decision

- **Location:** `## Risks / Trade-offs` first bullet (design.md lines 95–97) vs. D1/D2.
- **The gap:** The Risks section says: *"The propose skill asserts the PREMISE: line is present for proposal.md and treats its absence like a failed pass (re-run, don't freeze)."* This is a **load-bearing implementation requirement** — it's the defense against the reviewer model omitting the premise verdict. Yet it's only stated in Risks. Neither D1 (which defines the two-verdict output) nor D2 (which defines the freeze rule) states that the proposer MUST verify the `PREMISE:` line's presence before trusting the review. The current assert-ran check (propose skill Step 3c, sub-step 2, lines 134–136) confirms a `## Review Round` heading and a severity marker — it has no `PREMISE:` check.
- **Why it blocks:** If the implementer reads D1 and D2 but skips the Risks section (a reasonable reading order — Decisions define "what to build," Risks describe "what could go wrong"), they won't add the assert-ran check for `PREMISE:`. A reviewer invocation that returns zero 🔴 but omits the `PREMISE:` line (model didn't understand the new prompt, or ran a cached old version of the agent) would pass the existing assert-ran check and trigger auto-freeze — exactly the silent bypass D2 was designed to prevent.
- **What's needed:** Promote this requirement to D2 as an explicit sub-decision: *"The propose skill, when reviewing proposal.md, SHALL assert the reviewer output contains a `PREMISE: AGREE` or `PREMISE: DISSENT` line; its absence is treated as a failed pass — do not freeze, re-run."* The Risks item can remain as a risk note, but the requirement must live in Decisions.

#### 4. D5 — SMALL reviewer invocation has no budget row in the delegation harness

- **Location:** D5 (design.md line 78: *"under the same delegation harness and budget envelope"*), delegation harness `## (e) Timeout budget table` (delegation-harness.md lines 85–96).
- **The gap:** The delegation harness budget table has rows for: apply-executor, archive-executor, fix-executor, verifier (pro pass), verifier (flash pass), and propose reviewer. There is **no row** for a SMALL premise-review invocation. The existing "propose | reviewer" row (780s, `-k 15`) is keyed to the propose phase. D5 says the SMALL pass runs *"under the same budget envelope"* — but the harness table is **phase-specific** (the first column is "Phase"), and the SMALL pass runs outside the propose phase (it runs during the SMALL flow, which is not a named phase in the table).
- **Why it blocks:** The implementer writing the SMALL `opencode run` invocation needs a concrete `timeout -k <grace> <budget>` command line. They have two defensible but conflicting choices: (a) reuse the propose reviewer's 780s/`-k 15` (the design says "same envelope"), or (b) use a shorter budget appropriate to a flash-tier model reviewing a short plan (e.g., 300s). Choice (a) wastes resources; choice (b) requires a new harness row the design didn't authorize. Either way, the implementer is guessing.
- **What's needed:** D5 should state the concrete budget (e.g., `timeout -k 15 300 opencode run …` for flash, or explicitly reuse 780s), and the delegation harness table should gain a row for it. Even if the budget is identical to the propose reviewer, the row must exist so the invocation is traceable.

---

### 🟡 Should Fix

#### 5. Verification section is silent on the SMALL plan structure contract's location

- **Location:** Verification bullet "SMALL pass" (design.md lines 131–133) and "AGENTS.md" (lines 136–137).
- **The gap:** D5 says the SMALL plan structure contract (problem statement, proposed approach, explicit out-of-scope) is *"documented in AGENTS.md so authors know the minimum."* But the Verification section's `AGENTS.md` bullet only checks that *"Lifecycle/roles and the 'After reading this file' acknowledgements name the pre-implementation premise gate"* — it never mentions the SMALL plan contract. The `SMALL pass` Verification bullet lists "the D5 plan input-shape contract" but doesn't say WHERE it's documented. The implementer won't know to inject it into the AGENTS.md SMALL bullet unless the Verification section explicitly requires it.
- **Recommendation:** Add to the Verification AGENTS.md bullet: *"The SMALL tier bullet states the minimum plan structure (problem, approach, out-of-scope) per D5."*

#### 6. D5 — Who writes `premise-review.md` is unstated

- **Location:** D5 `Verdict sink` (design.md lines 83–84).
- **The gap:** The design says the flash premise output *"is written to `premise-review.md` in the change/plan dir."* But the `openspec-reviewer` agent is **`edit: deny`** (openspec-reviewer.md line 8) — it cannot write files. In the propose path, the primary extracts the reviewer's stdout and appends to `review-log.md`. The SMALL path needs the same extraction-and-write step, but D5 doesn't state who performs it (the orchestrator, obviously, but it must be said or the implementer will look for a way to make the reviewer write the file).
- **Recommendation:** D5's Verdict sink should say: *"The orchestrator extracts the verdict from the reviewer's jsonl stdout and writes it to `premise-review.md`."*

#### 7. D5 — "SMALL-gated pre-apply step" terminology is imprecise

- **Location:** D5 (design.md line 73: *"as a SMALL-gated pre-apply step in the apply skill"*).
- **The gap:** The term "pre-apply step" suggests the apply skill runs the premise pass. But as discussed in 🔴1, the orchestrator runs it before operator confirmation. The apply skill's role should be a **gate** (asserting the pass was completed), not the **invocation**. The ambiguous terminology is what created the 🔴1 contradiction.
- **Recommendation:** Rename to *"SMALL-gated pre-implementation gate in the apply skill"* — the skill checks that `premise-review.md` exists and the verdict is resolved, but does not invoke the reviewer itself.

#### 8. Behavioral smoke — "recommended, not blocking" is too weak for a gate change

- **Location:** Verification last bullet (design.md line 141–142: *"Behavioral smoke **(recommended, not blocking)**"*).
- **The gap:** This change's entire purpose is to add a gate that can say "no." If the gate can't actually emit `PREMISE: DISSENT` when given a symptom-level plan, the change is worthless. Making this optional at verify time risks shipping a gate that silently agrees with everything.
- **Recommendation:** Either make it a blocking criterion, or state clearly that the acceptance test at verify is run against a **live** invocation (not a mock) and must produce `DISSENT` on a deliberately bad plan. The current framing as "recommended" doesn't match the change's stakes.

---

### 💡 Suggestions

#### 9. D1 — PREMISE output format could use an explicit section template

- **Location:** D1 (design.md lines 37–42).
- **Suggestion:** The reviewer's current output format (openspec-reviewer.md lines 100–130) specifies a `## Review Round N` header and a `### Verdict` block. D1 adds a `PREMISE: AGREE|DISSENT` line but doesn't say whether it goes inside the Verdict block, as a new `### Premise Verdict` section, or as a standalone line. Providing an explicit format (e.g., *"After the severity Verdict, the reviewer emits `### Premise Verdict` with `PREMISE: AGREE|DISSENT` and a bullet list of cited concerns or `- None`"*) would prevent format drift across reviewer invocations and make the proposer's parsing deterministic.

#### 10. Verification mentions `openspec validate` — confirm it exists

- **Location:** Verification "Specs" bullet (design.md line 135: *"`openspec validate` (or the repo's spec check) passes"*).
- **Suggestion:** The `openspec validate` command may not exist for spec validation. If the actual command is something else (e.g., a spec-lint script), state it explicitly. If there's no validation command, remove the line rather than referencing a phantom tool.

#### 11. D6 — `reviewer-budget` scenario "WHEN the reviewer is invoked from the propose workflow" should be noted as needing update

- **Location:** D6 (design.md lines 87–91), reviewer-budget spec scenario line 17.
- **Suggestion:** D6 correctly says the requirement text changes, but the scenarios within the requirement use "propose workflow" as the invocation context. The implementer should also update (or add) a scenario for the SMALL premise pass path. D6 is silent on scenarios — worth noting so `tasks.md` can include it.

---

### Verdict

**NEEDS REVISION** — the four 🔴 blocking issues must be resolved before `tasks.md` can be written:

1. **🔴1:** Resolve D5's orchestrator vs. apply-skill invocation contradiction — assign the invocation to the orchestrator and the gate to the apply skill.
2. **🔴2:** Specify the UX mechanism for surfacing `DISSENT` to the operator in the propose skill (AskUserQuestion with 3 options).
3. **🔴3:** Promote the PREMISE-line assert-ran check from Risks to a D2 sub-decision.
4. **🔴4:** Add a SMALL reviewer budget row to the delegation harness table (in D5 or a note).

The 🟡 items are important for a clean `tasks.md` but don't block design freeze. The 💡 items are formatting/consistency improvements.

---

## design.md — Round 2 (deepseek-v4-pro, 2026-06-20) — VERDICT: NEEDS REVISION (1 new 🔴 [autonomy path] + 🟡 addressed)


---

## Review Round 2 — design.md

### Summary

All four Round 1 🔴 issues are concretely and completely fixed: D5 now cleanly separates the orchestrator-as-invoker from the apply-skill-as-gate (no more contradictory "invocation lives in the apply skill" language); D2a/D2b specify the exact `AskUserQuestion` protocol for surfacing DISSENT; D2a promotes the PREMISE-line assert-ran check from Risks to a named sub-decision with an explicit reference to the existing Step 3c mechanism; and D5 now includes a concrete budget-row specification for the delegation harness table. All five Round 1 🟡/💡 items are also resolved. The design is internally consistent and well-scoped against the existing specs.

However, I found **one new 🔴** — a silent breakage in the SMALL autonomy path that the current D5 phrasing would cause — and **five 🟡** refinements.

---

### 🔴 Blocking Issues

#### 1. D5 — SMALL premise pass is gated on operator confirmation, which does not exist under autonomy

- **Location:** D5 `Invoker` (design.md lines 93–99).
- **The defect:** D5 says the orchestrator runs the premise pass *"after the plan is written and before it asks the operator to confirm tier+plan (`tier-confirmation-gate`)"* and *"presents the verdict inside the tier+plan confirmation prompt."* This ties the pass's trigger and its presentation mechanism to the operator confirmation step. But AGENTS.md and the `tier-confirmation-gate` spec both say that an agent **with an explicit autonomy grant** self-classifies and proceeds **without** operator confirmation — there is no confirmation prompt and no "ask the operator" step.
- **Why it blocks:** If the AGENTS.md SMALL bullet is updated per D5's current wording ("run the premise pass before asking the operator"), an autonomy-granted orchestrator would either:
  - Skip the premise pass entirely (no "ask the operator" step to trigger it) → the apply skill's gate would find `premise-review.md` missing and STOP, breaking the SMALL flow under autonomy.
  - Or run it and not know where to present the verdict (no confirmation prompt exists).
  Either way, the SMALL premise pass is broken for any agent operating under an autonomy grant — the very mode where the operator needs the gate most (they are not watching per-change).
- **What's needed:** Rephrase D5's trigger to be independent of operator confirmation: the premise pass runs *"after the plan is written and before apply delegation."* Note that in the no-autonomy case this is also before operator confirmation, and the verdict is presented in the confirmation prompt; in the autonomy case, the verdict is written to `premise-review.md` and the apply skill's gate enforces it. This is a one-sentence fix.

---

### 🟡 Should Fix

#### 2. D5 — No recovery/salvage specification for the SMALL premise `opencode run` invocation

- **Location:** D5 `Invocation + budget` (lines 106–110).
- **The gap:** The proposal path has explicit salvage semantics (reviewer-budget spec: extract partial output, mark `PARTIAL`, re-run once if findings exist or >120s elapsed, else escalate). D5 says the SMALL pass uses the *"same hardened `opencode run` shape"* and *"same envelope as the verifier flash pass"* but never says what the orchestrator does on timeout or crash. The SMALL path has no `review-log.md` to append to, and its only output is a single `premise-review.md` file.
- **Why it matters:** A timeout on the flash premise pass (unlikely but possible with a complex plan) leaves the orchestrator with no verdict and no recorded guidance. The apply skill's gate would find `premise-review.md` missing/incomplete and STOP, which is safe but leaves the operator with no salvage path.
- **Recommendation:** Add a sentence: *"On timeout or crash, the orchestrator applies the same salvage rules as the propose reviewer (extract partial, re-run once if >120s or any finding present; else escalate), writing the partial to `premise-review.md` marked `PARTIAL`."*

#### 3. D6 — Scenario update for reviewer-budget is only mentioned in Verification, not in D6

- **Location:** D6 (lines 119–124) vs. Verification `Specs` bullet (lines 172–173).
- **The gap:** D6 says to update the reviewer-budget *requirement text* (the "only workflow" claim). The verification section says the delta includes *"requirement text **and** a scenario for the SMALL premise-pass invocation path."* But D6 itself never mentions the scenario — the implementer reading D6 would update only the requirement body and might leave the existing scenario ("WHEN the reviewer is invoked from the propose workflow") unchanged or incomplete.
- **Recommendation:** Add to D6: *"A new scenario is added for the SMALL premise-pass path (or the existing scenario is generalized to cover both paths)."*

#### 4. Verification — `openspec validate` may be a phantom command

- **Location:** Verification `Specs` bullet (line 173): *"`openspec validate` passes."*
- **The gap:** It's unclear whether `openspec validate` exists in this repo. The `openspec` CLI is used for `instructions`, `status`, `new`, `list` — `validate` is not attested. If it doesn't exist, a task referencing it would produce a spurious pass (no-op) or a failure that the implementer can't fix.
- **Recommendation:** Verify the command exists, or replace with a concrete check (e.g., *"no spec file references a non-existent delta source"* or *"`grep` confirms the reviewer-budget requirement text no longer says 'only workflow'"*).

#### 5. D5 — "pre-Step-1" positioning in the apply skill creates a chicken-and-egg ambiguity

- **Location:** D5 `Gate` (line 100): *"the apply skill gains a pre-Step-1 check."*
- **The gap:** The apply skill's Step 1 is "Select the change" — which resolves the change name to its directory. The gate needs the change directory to locate `premise-review.md`, but "pre-Step-1" runs before the change is selected. A literal reading puts the gate before the step that gives it the path it needs.
- **Why it matters:** The task-writer must decide whether to run the gate after Step 1 (select) but before Step 6 (delegate), or to construct the path from the name before Step 1. The design should disambiguate.
- **Recommendation:** Rephrase to *"the apply skill gains a gate that runs before the implementation delegation (Step 6): for a SMALL change..."* This avoids the positional ambiguity without changing the semantics.

#### 6. D2 + D2b — Override-to-proceed + 🔴 interaction is implicit

- **Location:** D2 (line 51) and D2b (line 69).
- **The gap:** D2 says freeze requires *"zero 🔴 AND `PREMISE: AGREE`"*. D2b says override-to-proceed *"permits freezing on a DISSENT"*. It is implicit that after override, freeze still requires zero 🔴 (the override substitutes for the PREMISE condition but does not waive the severity check). The design never states this explicitly, and a task-writer building the propose skill's new DISSENT branch might wonder: after override, does freeze require only zero 🔴, or should the DISSENT be re-checked on re-review?
- **Recommendation:** Add to D2b: *"After override-to-proceed, the freeze condition becomes zero 🔴 only — the DISSENT is not re-litigated on re-review, and the operator's override is the final word on direction."*

---

### 💡 Suggestions

#### 7. D3 — Premise review subsection placement in the reviewer agent file

The design says a new `### Premise review (proposal.md and SMALL plans only)` subsection is added to the reviewer's `## What to Check`. The current "What to Check" has subsections keyed to artifact types (`For proposal.md`, `For design.md`, `For tasks.md`). The task-writer needs to know where the new subsection goes — after `For tasks.md`? Before `Output Format`? This is a task-level detail but a one-line placement note in D3 would prevent guesswork.

#### 8. D5 — The reviewer invocation prompt for SMALL differs from the propose prompt

The reviewer agent's instructions say "Read the explore-brief.md if it exists, and openspec/specs/ for context" and its checklist references `proposal.md` / `design.md` / `tasks.md`. For a SMALL change, none of these exist — the reviewer needs to be told to read the plan file instead. D5 says *"same hardened `opencode run` shape"* but the prompt argument differs. This is implicit; a brief note (*"the orchestrator's invocation prompt names the plan file and signals 'premise review' per D1"*) would close the gap.

#### 9. D5 — Plan input-shape contract location in AGENTS.md

D5 says the plan structure contract is *"documented in the AGENTS.md SMALL bullet"* and the verification section confirms this. The task-writer may benefit from knowing whether this is a sentence addition to the existing SMALL bullet or a new standalone bullet (e.g., a `Plan minimum:` sub-bullet). Not blocking — the task-writer can decide — but a hint would save an ambiguity.

---

### Verdict

**NEEDS REVISION** — one 🔴 blocking issue (D5 autonomy path), five 🟡 refinements, and three 💡 suggestions. The 🔴 is a one-sentence fix: decouple the premise pass trigger from operator confirmation. The 🟡 items are important for a clean `tasks.md` but do not individually block design freeze.

---

## design.md — Round 3 (deepseek-v4-pro, 2026-06-20) — VERDICT: PASS (FROZEN)

Now let me read the supporting files — the reviewer agent, the propose/apply skills, delegation harness, and relevant specs — to verify the fixes in full context.
Now let me read the specs and AGENTS.md SMALL tier bullet to complete the context:
Now let me verify the SMALL tier bullet context and the `After reading this file` section of AGENTS.md for completeness:
## Review Round 3 — design.md

### Summary

All Round 2 issues are concretely and completely fixed. The 🔴 autonomy-path defect is resolved by decoupling the SMALL premise-pass trigger from operator confirmation (D5 lines 97–98: *"after the plan is written and before apply delegation — a trigger independent of operator confirmation"*) and adding an explicit autonomy-DISSENT path (lines 102–106: the orchestrator writes the verdict to `premise-review.md`, the apply gate STOPs, and the orchestrator escalates). All four named 🟡 fixes — salvage rules (lines 117–119), D6 scenario generalization (lines 135–136), gate positioning changed from "pre-Step-1" to "after Step 1 / before Step 6" (lines 108–109), and override→zero-🔴 clarification (lines 69–71) — are present, precise, and resolve the ambiguities they targeted. The design is internally consistent, well-scoped against the frozen `proposal.md`, and integrates cleanly with the existing `reviewer-budget`, `tier-confirmation-gate`, and `verify-multimodel-gate` specs.

I find **zero remaining 🔴 blocking defects.** One Round 2 🟡 remains unaddressed; one new 💡 observation follows.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **`openspec validate` may be a phantom command (re-raised from Round 2 🟡4, not addressed).**
   - **Location:** Verification `Specs` bullet (line 183): *"`openspec validate` passes."*
   - **Why it matters:** The `openspec` CLI is attested for `instructions`, `status`, `new`, `list` — `validate` is not referenced anywhere else in the repo. If it doesn't exist, the verify-phase orchestrator would encounter a command-not-found error, making this criterion either a spurious no-op or a confusing blocker. Of the five Round 2 🟡 items, this is the only one the round-3 fixes didn't touch — the other four (salvage, D6 scenario, gate positioning, override→zero-🔴) are all resolved.
   - **Recommendation:** Either (a) confirm `openspec validate` exists and works, or (b) replace with a concrete check (e.g., *"grep confirms the reviewer-budget requirement text no longer says 'only workflow'"*).

---

### 💡 Suggestions

2. **Review-log formatting drift (cosmetic).** Lines 105–106 of `review-log.md` contain a raw preamble from the Round 1 reviewer (*"Now let me read the key reference files..."*) that was never cleaned up before the Round 1 verdict was appended. This is harmless noise but may confuse future readers scanning the log. Scrubbing it is optional.

3. **D5 — Delegation-harness budget row keyed to "SMALL" Phase.** D5 (line 116) says the delegation-harness table gains a row `SMALL | premise reviewer (flash) | -k 15 780`. The existing table's Phase column uses OpenSpec phase names (`apply`, `archive`, `verify`, `propose`); "SMALL" is a tier, not a phase. The tasks.md author will need to decide whether to add a non-phase row or key it differently. This is a task-level detail, not a design defect, but worth noting as a minor disambiguation for the implementer.

---

### Verdict

**PASS** — ready to freeze and move to `tasks.md`. The design is concrete, complete, and consistent with the frozen `proposal.md`. All Round 2 🔴 and named 🟡 fixes are verified present and correct. The single remaining 🟡 (`openspec validate`) is a verification-criterion detail that does not block design freeze.

---

## specs — Round 1 (deepseek-v4-pro, 2026-06-20) — VERDICT: PASS (FROZEN; 2 🟡 + 1 💡 folded in)

Now let me read the existing specs for `tier-confirmation-gate` and `verify-multimodel-gate` to check for contradictions, and the `explore-brief.md` for context.
Now I have all the context I need — the frozen `proposal.md` and `design.md`, both delta specs, and the existing `reviewer-budget`, `tier-confirmation-gate`, and `verify-multimodel-gate` specs. Let me also quickly scan for any other spec files that might interact.
Good — the only specs that could interact are the three I've already read (`reviewer-budget`, `tier-confirmation-gate`, `verify-multimodel-gate`). Let me now compile the review.

---

## Review Round 4 — delta specs (`premise-review-gate/spec.md` + `reviewer-budget/spec.md`)

### Summary

The delta specs are **well-crafted and faithful to the frozen design**. Every D1-D6 design decision is encoded as a requirement with at least one scenario — in most cases, multiple scenarios that cover the normal path, the error case, and the autonomy variant. The MODIFIED `reviewer-budget` requirement header matches the existing spec **verbatim**, and all original SHALL statements are preserved while the "only workflow" claim is correctly broadened to "two workflows." SHALL language is used consistently and exclusively (no MUST drift). I find **zero contradictions** with `tier-confirmation-gate` or `verify-multimodel-gate` — the premise gate enriches the tier-confirmation prompt without replacing it, and it uses a different agent (`openspec-reviewer`) at a different phase than the verify gate (`openspec-verifier`). The SMALL cost increase (1→2 flash calls) doesn't conflict with verify-multimodel-gate's SMALL scenario, which governs only the post-apply verifier pass.

There are **two 🟡 issues** that would cause minor rework or ambiguity during implementation, and one 💡 suggestion — but nothing blocking.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **SMALL premise-pass timeout salvage is not scenario-covered in the premise-review-gate spec.**
   - **Location:** `premise-review-gate/spec.md` requirement "The SMALL premise pass runs before apply…" (lines 92–104).
   - **The gap:** D5 (design.md lines 117–119) explicitly defines timeout/crash salvage for the SMALL premise pass: *"On timeout/crash the orchestrator applies the same salvage rules as the propose reviewer (extract partial; re-run once if >120s elapsed or any finding present; else escalate), writing the partial to `premise-review.md` marked `PARTIAL`."* The `reviewer-budget` spec's salvage scenarios (lines 35–41 of the original) are generic and reference `review-log.md` — the propose-path output file. The SMALL path writes to `premise-review.md`, not `review-log.md`. The premise-review-gate spec has no scenario covering what happens when the SMALL premise pass times out or crashes. The implementer writing the SMALL orchestrator path must handle this case, but they'd have to infer the correct destination file from the general salvage rules combined with the SMALL output-path requirement — or, worse, default to writing a partial to `review-log.md` (which D5's `Verdict sink` says doesn't exist in the SMALL flow).
   - **What's needed:** One additional scenario in the premise-review-gate spec, e.g.:
     > **Scenario: SMALL premise pass timeout is salvaged to premise-review.md**
     > - WHEN the SMALL flash premise pass times out or crashes
     > - THEN the orchestrator salvages partial output per the reviewer-budget salvage rules and writes it to `premise-review.md` marked `PARTIAL`
   - **Severity rationale:** Not 🔴 because the salvage rules from `reviewer-budget` apply by reference and the destination file (`premise-review.md`) is already the established output path for SMALL. But the implicit cross-reference will cause the implementer to pause and decide — exactly the kind of ambiguity `tasks.md` should not contain.

2. **The SMALL premise-pass requirement conflates plan-structure contract with apply-gate mechanics.**
   - **Location:** `premise-review-gate/spec.md` lines 102–104: the last sentence of the SMALL requirement — *"A SMALL plan SHALL contain at minimum a problem statement, a proposed approach, and an explicit out-of-scope note for the premise reviewer to assess; a structurally inadequate plan is reported as a finding rather than guessed at."*
   - **The gap:** This sentence is about a **plan-authoring contract** (a requirement on the plan writer, enforced by the reviewer's finding, not by tooling). The surrounding requirement text and all four scenarios are about the **orchestrator's invocation mechanics** and the **apply skill's gate**. The plan-structure contract has no scenario of its own. During implementation, the task that defines the SMALL flow (AGENTS.md bullet update) and the task that defines the reviewer's premise lens (reviewer agent mandate) both touch this contract, but the spec's placement inside the orchestrator/apply-gate requirement makes it easy to miss when updating the reviewer agent. Either scenario would also close a subtle gap: today, the reviewer's `## What to Check` for SMALL plans (which don't have structured `proposal.md` sections) must know what minimal structure to look for — the contract anchors that, and a scenario makes it testable.
   - **What's needed:** Either add a standalone scenario:
     > **Scenario: Reviewer flags a structurally inadequate SMALL plan**
     > - WHEN a SMALL plan lacks a problem statement, proposed approach, or out-of-scope note
     > - THEN the premise reviewer reports this as a structural finding
     - **Or** move the plan-structure sentence into its own brief requirement (e.g., "Requirement: SMALL plans carry a minimum structure for premise review"). Either approach gives the implementer a testable behavior.
   - **Severity rationale:** Not 🔴 because the contract is stated in the requirement text — the implementer *will* see it and encode it somewhere. But without a scenario, the verification pass can't confirm whether the reviewer agent actually flags a structurally inadequate plan vs. silently guessing.

---

### 💡 Suggestions

3. **`premise-review.md` content format is implicit.** The SMALL requirement (line 95) says the orchestrator *"extract[s] the verdict from the reviewer's stdout … and write[s] it to `premise-review.md`."* The apply-gate requirement (line 101) says the gate *"assert[s] `premise-review.md` exists with a resolved verdict (`AGREE` or a recorded override-to-proceed)."* It's implicit that the file contains the extracted verdict block — not the full reviewer stdout — but "extract" could be read as "capture all output." If the implementer writes the full review output to `premise-review.md` and the gate greps for `PREMISE: AGREE`, it works either way. But if the file is intended to mirror `review-log.md` (append-only, full rounds), the verb "extract" is misleading. A one-word clarification (*"write **only** the verdict block to `premise-review.md`"*) would prevent format drift. This is a 💡 because both reasonable interpretations produce a file the gate can parse.

---

### D1-D6 Coverage Matrix (verified present)

| Decision | Requirement(s) | Scenario(s) | Status |
|---|---|---|---|
| **D1** — Two orthogonal verdicts, direction-artifacts only | "The reviewer emits a premise verdict orthogonal to the severity system" + "SHALL NOT run on design.md or tasks.md" | "Coherent artifact with a wrong premise", "Sound direction", "Non-direction issues do not trigger dissent", "Downstream artifacts are not re-litigated" | ✅ |
| **D2** — Freeze: zero 🔴 + PREMISE: AGREE | "A proposal freezes only on zero blocking issues AND premise agreement" | "Clean but dissented proposal does not freeze", "Missing premise line is a failed pass", "Clean and agreed proposal freezes" | ✅ |
| **D2a** — Assert PREMISE line present | Same requirement (lines 59–60) | "Missing premise line is a failed pass" | ✅ |
| **D2b** — Surface DISSENT via AskUserQuestion | "A premise dissent is surfaced to the operator and never silently auto-resolved" | "Operator chooses to revise", "Operator overrides" | ✅ |
| **D3** — Premise lens (four checks + default-to-dissent) | Woven into "premise verdict" requirement (lines 29–32 of premise-review-gate spec) | "Coherent artifact with a wrong premise", "Sound direction" | ✅ (implicit via scenario coverage) |
| **D3** — Read-only honesty | "The reviewer reasons about root cause read-only and does not claim empirical proof" | "Reviewer does not overclaim" | ✅ |
| **D4** — Dissent calibration | "DISSENT is reserved for genuine direction faults … and not for style, taste, or wording" | "Non-direction issues do not trigger dissent" | ✅ |
| **D5** — SMALL pass: invoker, gate, autonomy, input-shape, verdict-sink | "The SMALL premise pass runs before apply, independent of operator confirmation, and is gated at apply" | "SMALL premise pass fires under autonomy", "Autonomy does not override a dissent", "Apply gate blocks…", "Apply gate passes…" | ✅ (🟡 on missing timeout scenario) |
| **D6** — reviewer-budget delta | MODIFIED "The reviewer is budgeted for thoroughness, never rushed" (two-workflow text) | "Reviewer budget — propose review", "Reviewer budget — SMALL premise pass", "Re-examination is permitted" | ✅ |

### Existing-Spec Contradiction Check

| Spec | Interaction | Verdict |
|---|---|---|
| `tier-confirmation-gate` | SMALL premise verdict enriches the confirmation prompt without replacing the gate | ✅ No contradiction — the premise verdict is additional information inside an existing checkpoint; the gate's requirement ("obtain operator confirmation before executing") is unchanged. |
| `verify-multimodel-gate` | Premise gate uses `openspec-reviewer` (pre-apply); verify gate uses `openspec-verifier` (post-apply). SMALL now has 2 flash calls (1 premise + 1 verifier). | ✅ No contradiction — different agents, different phases. The verify spec's SMALL scenario ("SHALL run a single flash verifier pass") governs only the post-apply pass; the premise pass is an additive pre-apply pass with a different agent. |
| `reviewer-budget` (unmodified requirements) | Salvage + read-only requirements reference `review-log.md`; SMALL path uses `premise-review.md`. | ✅ No contradiction — the premise-review-gate spec explicitly establishes `premise-review.md` as the SMALL output destination, overriding the propose-path default. |

### Normative Language Audit

- **SHALL count in `premise-review-gate/spec.md`:** 26 occurrences. All are correctly scoped — they prescribe required behavior, not aspirations.
- **SHALL count in `reviewer-budget/spec.md` (delta):** 5 occurrences in the requirement text (plus 2 in scenarios). All preserved from the original; the new invocations are correctly scoped.
- **MUST count in both deltas:** 0. Consistent with existing specs, which also use SHALL exclusively.
- **No weakening language** (MAY, SHOULD, RECOMMENDED) is used where D1-D6 mandate SHALL. The one place where the design uses softer language — D5's plan input-shape ("a contract, not enforced tooling") — is correctly encoded as a SHALL on the plan author plus a reviewer-finding behavior, not as a weaker normative level.

---

### Verdict

**PASS** — ready to freeze and move to implementation. The two 🟡 items (missing timeout-salvage scenario for SMALL, and plan-structure contract inlining) are refinements that would make the spec more testable but do not block correct implementation — the behavioral requirements they encode are already stated in the requirement text. The 💡 suggestion is a clarity improvement only. No 🔴 issues, no contradictions with existing specs, and all six design decisions are traceably encoded.

---

## tasks.md — Round 1 (deepseek-v4-pro, 2026-06-20) — VERDICT: PASS (FROZEN)

Folded in 🟡1 (split 3.1 → harness gets budget row only; invocation command moved to 3.2 SMALL bullet),
🟡2 (concrete SMALL invocation prompt string added to 3.2), 💡6 (1.1 notes SMALL plan minimum structure).

**Overruled (per propose-skill "reviewer can be wrong", rationale recorded):**
- 🟡3 "no Effort: ~N hours field" — the authoritative `openspec instructions tasks` template is
  `- [ ] X.Y <desc>` with NO Effort field; tasks are already small-scoped. Adding the field would be
  noise against the template. Granularity guideline still honored.
- 💡4 "`openspec validate` may be phantom" — false; `openspec validate` was run successfully twice this
  session (it reports "Change ... is valid"). Task 5.1 kept.

Now let me read the key files to verify the tasks hit real paths and the design decisions are covered. I'll read all the referenced files and the delta specs in parallel.
Let me also check the scaffold manifest and the AGENTS.md "After reading" section that task 4.2 edits, plus the explore-brief if it exists.
## Review Round 1 — tasks.md

### Summary

`tasks.md` covers every design decision (D1-D6, D2a, D2b) with concrete, verifiable tasks that hit real scaffold-managed files. No orphan tasks and no missing decisions. The task grouping (1–5) follows a sane processing order. Two 🟡 concerns deserve attention: task 3.1 overreaches beyond what design D5 asks for the delegation-harness file, and the SMALL premise-pass invocation prompt (what exact words the orchestrator feeds the reviewer) is left entirely to the implementer with no specification anchor. Neither is a 🔴 blocker — the implementer can produce correct output — but both would cause rework or hesitation.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **Task 3.1 asks for more than design D5 specifies for `delegation-harness.md` — invocation shape and salvage rules in a file that is a shared contract, not a per-invocation cookbook.**  
   - **Location:** Task 3.1 (tasks.md line 16), design D5 (design.md lines 113–119).  
   - **The discrepancy:** Design D5 says: *"†asks.md adds a `SMALL | premise reviewer (flash) | -k 15 780` row to the delegation-harness budget table so the invocation is traceable."* The design asks for a budget-table **row** — nothing more. Task 3.1 additionally wants: *"Add the hardened `opencode run …` invocation shape … including the timeout/crash salvage rule writing the partial to `premise-review.md` marked `PARTIAL`."*  
   - **Why it matters:** The `delegation-harness.md` file is explicitly a *shared operational contract* that skills cite — it does **not** carry per-phase invocation commands (those live in each skill's own SKILL.md). The orchestrator's SMALL premise pass is neither a skill nor a phase — the invocation command logically belongs in **AGENTS.md** (which describes the SMALL flow) or the **apply skill** (which gates on the result). Task 3.2 already says AGENTS.md will *"Reference the harness invocation from 3.1,"* but if 3.1 places the command in the harness and 3.2 references it there, the invocation shape ends up in the wrong file. The implementer will either (a) add it to the harness (technically works but violates the file's contract purpose), (b) realize the dissonance and stop to decide where it goes, or (c) add it to both files.  
   - **Recommendation:** Split task 3.1: add only the budget-table row to `delegation-harness.md` (per D5); move the invocation shape and salvage rules into task 3.2 (AGENTS.md SMALL bullet), specifying the exact `opencode run` command the orchestrator runs. This keeps the harness as a budget-table authority and puts the invocation where it belongs — in the SMALL-flow documentation.

2. **No specification of the SMALL premise-pass invocation prompt — the reviewer needs to be told what file to read and that this is a premise review.**  
   - **Location:** Task 3.2 (tasks.md line 17), design D5 (design.md lines 98–99: *"names the plan file in the invocation prompt and signals 'premise review' per D1"*).  
   - **The gap:** The design says the orchestrator *"names the plan file in the invocation prompt and signals 'premise review.'"* Neither task 3.1 (which adds the `opencode run` command shape to the harness) nor task 3.2 (which updates the AGENTS.md SMALL bullet and *references* that command) specifies the actual prompt string. The reviewer agent's current checklist is keyed to structured `proposal.md`/`design.md`/`tasks.md` artifacts — for a SMALL plan, the reviewer needs to be told: (a) which file is the plan, (b) this is a SMALL plan (not proposal.md), and (c) to emit the `### Premise Verdict` block. The propose skill's equivalent invocation prompt is explicit (propose SKILL.md lines 117–119).  
   - **Why it matters:** The implementer writing the AGENTS.md SMALL bullet will need to *invent* this prompt string. If they get it wrong (e.g., reference a non-existent `proposal.md`), the reviewer may misparse the input and produce a garbage verdict. The delta spec (`premise-review-gate/spec.md`) has a scenario for "Reviewer flags a structurally inadequate SMALL plan" — but the reviewer can only do that if the prompt correctly tells it *what* to read and *what format* to expect.  
   - **Recommendation:** Add a concrete prompt string to task 3.2 (or a separate sub-task), e.g.: *"Review the plan at `<planPath>`. This is a SMALL change plan — it is not a structured proposal.md. Emit a premise verdict (### Premise Verdict) only."* This closes the gap between D5's signal-to-prompts and the implementer's blank slate.

3. **No effort estimates on any task.**  
   - **Location:** Entire tasks.md (lines 1–28).  
   - **The template/AGENTS.md convention calls for `Effort: ~N hours` on each task. All 14 tasks lack this field. This is a formatting defect — the implementer cannot judge whether any task is oversized — but not blocking because the task descriptions are sufficiently scoped. The executor should estimate effort at implementation time and flag any task that would exceed ~2 hours.

---

### 💡 Suggestions

4. **Task 5.1 (`openspec validate premise-review-gate`) may reference a phantom command.** The design's verification section (Round 3 review, 🟡1) already flagged this: `openspec validate` is not attested anywhere else in the repo. If the command doesn't exist, the executor will report a failure that the orchestrator must triage. This is a 💡 (not 🟡) because 5.1 is a self-check, not load-bearing for correctness — the delta specs were already reviewed in Round 4 and are known-correct. Consider replacing with a concrete check like `grep` for the changed requirement text, or dropping the task since the delta specs are frozen.

5. **Tasks lack explicit inter-dependency notes.** The section ordering (1→2→3→4→5) is reasonable, but within sections the executor has no guidance on whether tasks can be done in parallel or must be sequential. For example, 3.1 and 3.2 and 3.3 are independent edits to different files and could be parallelized. Explicit dependency markers (e.g., "Depends on: 1.2") would help the executor avoid unnecessary sequencing. This is 💡 because the current order is safe.

6. **Task 1.1 could explicitly mention the SMALL plan structure contract for the reviewer.** The premise review subsection (D3) adds four generic checks (root/symptom, solution targets root, scope, blind spot). But the reviewer also needs to know what *minimum structure* a SMALL plan provides for those checks to operate on. The AGENTS.md contract (task 3.2) says plans must have problem/approach/out-of-scope, and the delta spec has a scenario for "Reviewer flags a structurally inadequate plan" — but the reviewer agent's own mandate (task 1.1) doesn't explicitly reference this minimum. It's implicit in the four checks, so this is 💡 only.

---

### Verdict

**PASS** — ready to freeze and move to implementation. The three 🟡 items are refinements, not blockers: task 3.1's scope vs. D5 is a placement question the implementer can resolve (put the budget row in the harness, put the invocation shape in AGENTS.md), and the SMALL invocation prompt is inferable from D1/D5 context. No design decision lacks a task, no task lacks a design decision, and every file referenced is confirmed real and scaffold-managed.

---

## proposal.md — Round 3 (REVISED: explore direction gate added) (deepseek-v4-pro, 2026-06-20) — VERDICT: NEEDS REVISION (2 🔴 addressed)

Let me also read the remaining context files — the explore-brief for this change, the reviewer agent definition, and the propose skill:
Now let me also check the `apply-convergence-guard` and `noninteractive-delegation-safety` specs since the proposal touches apply-skill and delegation paths:
Now let me read the remaining review-log to see if tasks.md was already reviewed, and also the delta specs for completeness:
Now I have the complete picture — the revised proposal adds an explore-direction gate, but the downstream design.md, specs, and tasks.md were all written and frozen for the previous proposal scope. Let me produce the review.

---

## Review Round 5 — proposal.md (REVISED — explore-direction gate added)

### Summary

The revised proposal is directionally sound: adding an explore-stage direction gate (Altitude 1) closes a genuine gap — the most consequential decision ("is this the right thing to build?") has been the least systematically reviewed. The two-altitude architecture (direction at explore, change-itself at propose/apply) is clean and well-separated. The proposal correctly identifies reviewer-budget as needing a delta, and preserves the existing DISSENT-vs-freeze resolution from the prior rounds.

However, the scope expansion introduces **two 🔴 execution gaps** that would force the design.md author to invent invocation machinery and review criteria from scratch — exactly the kind of ambiguity that causes rework. There are also **four 🟡 refinements** and **three 💡 suggestions**.

---

### 🔴 Blocking Issues

#### 1. Explore-direction gate has no invocation owner — who runs the reviewer?

- **Location:** Lines 33–34 ("that output MUST be premise-reviewed"), line 91 ("explore skill is updated to... require the pro premise review before the phase advances"), and the Impact section (lines 90–98).
- **The gap:** The proposal mandates that load-bearing explore output "MUST be premise-reviewed" and that the explore skill must "require" this review. But **nowhere does it say who invokes the reviewer**. Three possibilities exist, each with different downstream consequences:
  - **(a) The explore skill invokes it** — but the explore skill has no `opencode run` machinery today; this would require adding the full delegation harness, timeout budget, salvage logic, and `review-log.md` append. The Impact section (line 90–91) mentions only "capture load-bearing conclusions as explore-brief.md" and "require the pro premise review" — not "invoke the reviewer."
  - **(b) The orchestrator (primary agent) invokes it** — but the orchestrator has no defined process step between "explore completed" and "operator says propose"; this would need a new AGENTS.md lifecycle rule.
  - **(c) The propose skill invokes it as a pre-condition** — but the propose skill can't do this before the change directory exists (which it creates in Step 2), and the explore-brief may need review before that.
- **Why it blocks:** Without establishing who owns the invocation, the design.md author cannot write the invocation path, budget specification, error handling, or verdict-sink logic for Altitude 1. The implementer would have to invent the protocol from three conflicting plausible interpretations. This is the single largest gap between the revised proposal and implementability.
- **What's needed:** The proposal (or, minimally, a note in the Impact section) should state which actor invokes the reviewer for the explore-brief — even if the exact mechanism is deferred to design.md. For example: *"The explore skill itself invokes the reviewer via `opencode run` (same harness as the propose skill) before reporting a direction verdict to the operator"* or *"The orchestrator runs the reviewer after the explore skill writes the brief and before the operator advances."*

#### 2. SMALL "consistency check" narrowing path has no defined criteria

- **Location:** Lines 43–44 ("if a pro-reviewed explore brief already covers the same direction, this flash pass narrows to a consistency check").
- **The gap:** The proposal carefully defines the full premise lens as four checks (line 51: root-vs-symptom, solution-targets-root, scope-right-sizing, blind-spot). But the SMALL narrowing to a "consistency check" is mentioned only in a parenthetical with **zero specification of what the consistency check actually consists of**. Questions the design.md author cannot answer from the proposal:
  - Does the flash reviewer still emit `PREMISE: AGREE|DISSENT` for a consistency check, or a different verdict?
  - What does "consistency" mean — does the reviewer check that the plan's problem/solution match the explore-brief's problem/solution? That scope hasn't drifted? Both?
  - When the SMALL plan is consistent but the explore-brief was wrong, does the consistency check catch it, or does it defer to the pro-reviewed explore-brief? (The proposal says SMALL flash pass "narrows to a consistency check" — this implies it does NOT re-assess premise de novo, so a wrong explore-brief would not be caught by the flash pass.)
- **Why it blocks:** The SMALL flow has two distinct paths now — full premise review (no explore-brief) and consistency check (explore-brief exists). The proposal defines only the former. The design.md author needs to design the latter from nothing, with no anchor in the proposal about what "consistent" means. The risk is that the consistency check becomes either a no-op rubber stamp or an overreaching re-premise — both undermine the gate.
- **What's needed:** At minimum, define what the consistency check checks. E.g.: *"The consistency check verifies: (a) the plan's problem statement matches the explore-brief's verified problem; (b) the proposed approach is consistent with the direction validated at explore; (c) scope has not expanded beyond what was vetted. It does not re-argue root cause."* The verdict format (still PREMISE: AGREE|DISSENT or a different signal) should also be stated.

---

### 🟡 Should Fix

#### 3. Existing downstream artifacts (design.md, specs, tasks.md) were frozen under the old scope

- **Location:** Entire change directory — `design.md`, `specs/premise-review-gate/spec.md`, `specs/reviewer-budget/spec.md`, `tasks.md`.
- **Why it matters:** All three were reviewed and frozen before the explore-direction gate was added. The design has no D7 for explore-brief handling; the delta spec has no requirements for explore-brief review; `tasks.md` has no tasks for explore-skill reviewer invocation. These artifacts must be un-frozen and expanded when the proposal freezes. This isn't a proposal defect, but it's a 🟡 process note for the primary agent: the proposal can't truly freeze while downstream artifacts are silently inconsistent with it.

#### 4. Explore-brief.md trigger condition is ambiguous

- **Location:** Lines 36–39 ("the gate fires ONLY when exploration's conclusions are written down to steer a change").
- **Why it matters:** "Load-bearing conclusions that will drive a downstream change" is a judgment call an explore agent must make in real time. The explore agent may discuss 5 ideas with the operator and produce extensive output — does ALL of that require an explore-brief and direction review? What if the operator casually says "interesting, let me think about it" — no change is imminent, but "conclusions" were written? The implementer updating the explore skill needs a bright-line rule ("produce explore-brief.md when the operator says 'propose' or 'implement this'" vs. "produce it whenever you make a recommendation"). The current phrasing leaves the trigger entirely to agent judgment, which invites both false positives (unnecessary pro reviews) and false negatives (skipped reviews on real conclusions).
- **Recommendation:** Tie the trigger to an observable event: e.g., *"The explore skill produces an explore-brief.md when the operator indicates intent to proceed to propose or apply on the basis of the exploration's conclusions — signaled by the operator saying 'propose', 'implement', 'let's go', or similar advancement language."*

#### 5. Explore-brief.md file location when no change directory exists is unspecified

- **Location:** Line 36 ("capture its load-bearing conclusions as an explore-brief.md"), and the reviewer's existing instruction to read "the explore-brief.md if it exists" (openspec-reviewer.md line 48).
- **Why it matters:** The reviewer and the propose skill both expect `explore-brief.md` to live under `openspec/changes/<name>/` (the reviewer is invoked with `--dir <repoRoot>` and artifact paths). But explore often happens BEFORE a change directory is created — the propose skill creates it in Step 2 (`openspec new change`). If the explore agent writes the brief to a location other than the change dir, the reviewer invocation command must pass a different path, and the downstream propose skill must relocate it. This is resolvable in design.md but the proposal should acknowledge it as an explicit design decision to be made.
- **Recommendation:** The Impact section or a brief note should flag: *"Where explore-brief.md lives when no change directory exists yet is a design-phase decision (options: create the change dir early, or write to a `plans/` directory and relocate during propose)."*

#### 6. MEDIUM/COMPLEX with explore-brief: implicit double-premising needs acknowledgment

- **Location:** Lines 45–47 (MEDIUM/COMPLEX change-itself check: "premise lens folded into the existing proposal.md review … When a verified explore brief exists, this review additionally checks the proposal did not drift from it").
- **Why it matters:** For MEDIUM/COMPLEX with an explore-brief, the proposal gets the full premise lens (4 checks) PLUS a drift check. The premise lens already includes "is the problem real and root" — which was the Altitude 1 direction review's core question. This means the MEDIUM/COMPLEX proposal is effectively premise-reviewed TWICE: once as an abstract direction (explore-brief), once as a concrete proposal. The proposal frames this as "no new gate" (zero incremental cost), which is correct — but the redundancy should be acknowledged explicitly so the design.md author doesn't try to "optimize away" the proposal premise lens (which would break the case where no explore-brief exists). The current text ("When a verified explore brief exists, this review additionally checks the proposal did not drift from it") says "additionally" — implying the premise lens still runs. This is fine but implicit.
- **Recommendation:** A one-line clarification: *"The premise lens always runs on the MEDIUM/COMPLEX proposal review; when an explore-brief exists, the lens also cross-references it for drift — this is additive, not a replacement, because the concrete proposal may surface new blind spots."*

---

### 💡 Suggestions

#### 7. Explore-brief review has no verdict-sink specified

- **Location:** The proposal specifies verdict sinks for proposal.md (`review-log.md`, line 62 context) and SMALL plans (`premise-review.md`, implied), but not for explore-brief reviews. Where does the Altitude 1 review output go? Options: the change dir's `review-log.md` (but it may not exist yet), a standalone `explore-review.md`, or the explore-brief.md itself (appended). The design.md will need to decide; noting it in the proposal would prevent the design author from forgetting it.

#### 8. "Load-bearing conclusions" could use a stable term

- **Location:** Lines 36, 38 ("load-bearing conclusions", "exploration's conclusions are written down").
- **Suggestion:** The proposal uses "load-bearing conclusions," "explore-brief.md," and "output/brief" interchangeably to refer to the same thing. Standardizing on "explore-brief.md" (the file name that triggers the gate) would make the design.md clearer. The "load-bearing" qualifier describes WHEN the file must be produced, not WHAT the file is.

#### 9. The Impact section lists 8 bullet points but doesn't mention the delegation harness budget table update

- **Location:** Impact section (lines 90–109).
- **Why it matters:** The OLD scope's design.md (D5, line 116–117) called for adding a SMALL premise reviewer row to the delegation harness budget table. The SMALL path still requires this, whether or not explore was involved. The Impact section lists AGENTS.md, explore skill, reviewer agent, propose skill, apply skill, new spec, reviewer-budget delta, and scaffold propagation — but doesn't explicitly mention `delegation-harness.md`. The SMALL flash invocation needs budget specification, and the explore pro invocation for the direction gate ALSO needs budget specification (the same 780s/-k 15 envelope, presumably). Both invocation paths need harness rows. This is a 💡 because the budget needs are implicit in the "reviewer-budget delta" bullet, but the harness table is a separate file that the implementer must edit.

---

### Premise Assessment

Per the proposal's own framing, let me assess the premise of the revised proposal:

- **Is the problem real and root?** Yes. The explore stage is where direction is decided, and it has been systematically under-reviewed — the operator has been filling this gap manually. Institutionalizing it into the scaffold is a genuine structural improvement.
- **Does the solution address the root?** Yes, but with the two execution gaps flagged above (invocation owner, consistency-check definition). The two-altitude architecture addresses the root cleanly; the gaps are in the wiring.
- **Is scope right-sized?** The scope expansion is bounded and clear: one new altitude (direction at explore), one updated skill (explore), and adjustments to the downstream artifacts. It does not creep into the verify gate or change the severity system.
- **Blind spots:**
  - Who invokes the explore-brief review and with what harness? **🔴 flagged.**
  - What does the SMALL consistency check actually check? **🔴 flagged.**
  - How does a DISSENT at explore interact with an operator who says "proceed anyway" and then the proposal review checks "drift" against a DISSENTed brief? This edge case is unexamined in the proposal.
  - The explore skill currently has a strong "do not auto-advance" guard (line 16–17, line 286 of SKILL.md). Adding "require the premise review before phase advances" complements rather than contradicts this — but the precise interaction (does the guard block both agent-initiated AND operator-initiated advancement?) should be explicit.

---

### Verdict

**NEEDS REVISION** — address the two 🔴 blocking issues before proceeding to design.md:

1. **🔴1:** Establish who invokes the reviewer for the explore-brief (explore skill, orchestrator, or propose skill pre-condition). Even a one-sentence declaration of the owner is sufficient — the exact mechanism can be designed later, but the design.md author needs to know which file gets the invocation machinery.
2. **🔴2:** Define what the SMALL "consistency check" narrowing actually checks — at minimum, what properties it verifies and whether it still emits the AGREE/DISSENT verdict. The SMALL flow has two paths; only the non-narrowed path is currently specified.

The 🟡 items (stale downstream artifacts, trigger condition ambiguity, file location, double-premising acknowledgment) are important for a clean design phase but do not individually block proposal freeze. The 💡 items are optional clarifications.

---

## proposal.md — Round 4 (REVISED) (deepseek-v4-pro, 2026-06-20) — VERDICT: PASS (RE-FROZEN). Carries to design.md: 🟡 override propagation Alt1→Alt2; 🟡 define "drift"; 💡 explore "no mandatory output" reconciliation; 💡 Alt1 calibration (dissent when demonstrably wrong, not merely under-specified); 💡 cost summary.

## Review Round 3 — proposal.md (REVISED: explore-direction gate added, SMALL narrowing removed)

### Summary

The revised proposal is **clean and concrete**. Both prior 🔴 issues are completely and correctly resolved:

- **🔴1 (invocation owner):** Line 36 assigns the explore direction gate unambiguously to **the explore skill** — it invokes the reviewer via `opencode run` (same harness as propose), reports the verdict, before the phase advances. No ambiguity, no competing candidate.
- **🔴2 (SMALL consistency check undefined):** The special-case narrowing was **removed entirely**. The SMALL flash pass always runs the **full premise lens** (line 49); when an explore-brief exists, it's purely additional context with an "also flag drift" instruction, same `AGREE|DISSENT` verdict format. No separate mode. No undefined behavior.

All four folded-in items are also present and precise: trigger tied to operator advancement language (lines 39–41), file-location/sink deferred to design.md (lines 43–45), delegation-harness rows added to Impact (lines 100–101), and MEDIUM/COMPLEX double-premising explicitly noted as additive (lines 54–56).

The two-altitude architecture (direction at explore, change-itself at propose/apply) is internally coherent and well-separated. I find **zero 🔴 blocking defects**. Two 🟡 items address cross-altitude interactions the design.md author would benefit from having flagged; three 💡 items are optional refinements.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **DISSENT-at-explore override → proposal drift-check handoff is unspecified.**  
   - **Location:** Lines 36–38 (Altitude 1 verdict → operator decision), lines 54–56 (Altitude 2 drift check).  
   - **The gap:** When Altitude 1 returns `PREMISE: DISSENT` and the operator says "proceed anyway," the operator's override must be recorded *somewhere* so the Altitude 2 proposal review's drift check doesn't see a DISSENTed brief and re-flag the same issue. The proposal establishes that DISSENT is surfaced and override-to-proceed exists as a concept (line 68), but the recording mechanism is part of the "verdict sink" deferred to design.md (line 43–45). Without explicit flagging, the design.md author could easily overlook this cross-altitude data flow.  
   - **Why 🟡 not 🔴:** The proposal correctly defers verdict-sink mechanics to design.md, and the override-to-proceed concept is already established. But the *propagation* of an override from Altitude 1 to Altitude 2 (e.g., a marker in the explore-brief, or a separate `override.md`) is a handoff detail that the design *must* resolve — flagging it here prevents a silent gap.  
   - **Recommendation:** Defer to design.md with a note that the verdict sink must accommodate both the `AGREE`/`DISSENT` verdict and any operator override, so Altitude 2's drift check can distinguish "verified direction" from "direction the operator chose to proceed on despite DISSENT."

2. **"Drift" from explore-brief is undefined.**  
   - **Location:** Lines 49–51 (SMALL: "flag any drift"), lines 54–56 (MEDIUM/COMPLEX: "cross-references it for drift").  
   - **The gap:** The proposal says the reviewer should flag drift but never defines what constitutes drift. Does a *narrower* scope count (the plan is more conservative than the brief — generally safe)? Does a restated-but-equivalent problem statement count as drift? Is drift limited to *contradictions* (plan does something the brief explicitly ruled out), or does it include *omissions* (plan skips something the brief said was important)? The design.md needs a concrete definition.  
   - **Why 🟡 not 🔴:** The SMALL full lens already covers the four core checks (root/symptom, solution-addresses-root, scope, blind spots). The drift check is additive context, not a separate gate — the worst case is that it produces either false positives or false negatives, but the full lens catches genuine direction problems either way. Still, without a definition, the implementer wiring the "flag drift" instruction into the reviewer prompt won't know what words to use.  
   - **Recommendation:** State in the proposal or defer explicitly to design.md: *"Drift means: the plan contradicts a verified direction conclusion (problem reframed differently, approach changed to one ruled out during explore, scope expanded beyond what was vetted). Narrower scope and restatements are not drift."*

---

### 💡 Suggestions

3. **Explore skill "no mandatory output" principle needs design-phase reconciliation text.**  
   - The explore skill currently states *"There are no fixed steps, no required sequence, no mandatory outputs."* (line 17). The proposal adds a conditional mandatory output (explore-brief.md, when the operator signals advancement). The proposal correctly notes that explore "keeps 'no mandatory output'; the gate fires only at that point" — but the design.md implementer updating the skill file needs to know how to reconcile the new rule with the existing principle. A brief design-phase note (*"the explore skill's founding principle is preserved for idle exploration; the brief is a response to an operator signal, not an automatic output"*) would prevent implementer hesitation.

4. **Altitude 1 DISSENT calibration — reasoning from a brief alone.**  
   - The Altitude 1 review happens *before any proposal exists* — the reviewer has only the explore-brief (abstract problem/solution framing, no concrete scope, no implementation constraints). The same premise lens (root-vs-symptom, solution-targets-root, scope, blind spot) applied to an abstract brief may produce more DISSENTs than the same lens applied to a concrete `proposal.md`. The default-to-dissent stance combined with sparse input could produce excessive false positives. The design.md should address calibration for the explore-brief case specifically — e.g., the reviewer should dissent when the direction is *demonstrably wrong* given the information available, not merely *under-specified* (which is expected at explore stage).

5. **Cost Impact could state the incremental total.**  
   - Line 118 says *"the direction gate adds one pro call only when explore produced a load-bearing brief."* This is accurate but the per-tier cost summary is distributed across the Impact text. A one-line summary — e.g., *"SMALL: +1 flash call (premise pass); MEDIUM/COMPLEX: +0 calls if no explore-brief, +1 pro call if explore-brief exists"* — would help downstream readers quickly understand the operational cost without parsing the full section.

---

### Premise Assessment (required by the proposal's own framing)

Per the four-checks premise lens:

- **Is the problem real and root?** Yes. The explore stage is where direction is decided, and it has been the least systematically reviewed step — the operator has been filling this gap manually. Institutionalizing it as a scaffold gate is a genuine structural improvement.
- **Does the solution address the root?** Yes. The two-altitude architecture (direction at explore, change at propose/apply) addresses the root with zero marginal cost at MEDIUM/COMPLEX and one additional flash call at SMALL. The shared mechanics (AGREE/DISSENT verdict, orthogonal to severity, default-to-dissent, read-only honesty) provide a consistent framework across both altitudes.
- **Is the scope right-sized?** Yes. The scope expansion is bounded: one new altitude (direction at explore), one updated skill (explore), adjustments to reviewer agent and delegation harness, and explicit deferrals to design.md for file-location/verdict-sink mechanics. The existing verify gate and tier-confirmation gate are interacted-with but not requirement-modified.
- **Blind spots:**
  - DISSENT-at-explore override propagation to Altitude 2 drift check is unspecified — flagged as 🟡 above. ✓
  - "Drift" definition is absent — flagged as 🟡 above. ✓
  - Altitude 1 calibration (dissent from an abstract brief vs. a concrete proposal) is a design-phase calibration risk — flagged as 💡 above. ✓

---

### Existing-Spec Contradiction Check

| Spec | Interaction | Verdict |
|---|---|---|
| `reviewer-budget` | "Only workflow" claim becomes false; proposal correctly lists it as Modified with a delta scoped to the added invocation paths. | ✅ No contradiction — the delta is acknowledged and scoped |
| `tier-confirmation-gate` | SMALL premise verdict enriches the confirmation prompt without replacing the gate; neither requirement text nor scenarios need modification. | ✅ No contradiction — additive, not replacement |
| `verify-multimodel-gate` | Premise gate uses `openspec-reviewer` (pre-apply); verify gate uses `openspec-verifier` (post-apply). SMALL now has 2 flash calls (1 premise + 1 verifier). | ✅ No contradiction — different agents, different phases |

---

### Verdict

**PASS** — ready to freeze and move to `design.md`. Both Round 5 🔴 issues are fully resolved, the architecture is clean and internally coherent, the scope boundaries are explicit, and the proposal correctly defers implementation details (file location, verdict sink, exact UX) to design.md. The two 🟡 items are cross-altitude interactions worth flagging for the design phase but do not block proposal freeze.

**Note:** The downstream artifacts (`design.md`, `tasks.md`, both delta specs) were previously frozen under the old scope (before the explore-direction gate was added). They will need to be **un-frozen and expanded** once this proposal freezes — they are silently inconsistent with it until then. This is a process note for the primary agent, not a proposal defect.

---

## design.md — Round 3 (D7-D11 explore-gate expansion) (deepseek-v4-pro, 2026-06-20) — VERDICT: NEEDS REVISION. Design 🔴 addressed: 🔴3 slug (kebab from topic), 🔴4 relocate (not reference), 🔴5 override format (### Resolution / OVERRIDE: proceed). 🟡6/7/8 + 💡10/11/12 folded. 🔴1/🔴2 (stale delta specs) + 🟡9 (tasks harness row) deferred to the specs/tasks revision steps that follow.

Now let me read the remaining context files — the review log, the change specs, and the AGENTS.md shared spans.
Let me read the remaining reference files — the openspec-reviewer agent, the delegation harness, and the relevant AGENTS.md sections.
Let me read the AGENTS.md SMALL bullet and the "After reading this file" section for the current baseline.
Now I have all the context I need to conduct a thorough review of the expanded design.md, focused on D7-D11. Let me emit the review.

---

## Review Round 4 — design.md (D7-D11 expansion)

### Summary

The design for the explore direction gate (D7-D11) is architecturally sound in concept: it reuses the existing `openspec-reviewer` agent and `opencode run` harness, correctly attaches to the explore skill's existing STOP-before-advancing guard, defines drift concretely (D10), and calibrates dissent for abstract briefs (D11). However, the expansion introduced **five 🔴 issues**: a stale delta spec that contradicts D6 ("two workflows" vs. "three"), a missing delta spec for the new D7-D11 requirements, an unspecified slug-determination mechanism (D8), an unresolved relocation-vs-reference fork (D8), and an underspecified override-recording protocol (D9). None of these are conceptual — all are wiring-level gaps that would force the implementer to invent protocol during task execution.

---

### 🔴 Blocking Issues

#### 1. Delta spec `reviewer-budget/spec.md` is stale — says "two workflows" but D6/D7 require three

- **Location:** `openspec/changes/premise-review-gate/specs/reviewer-budget/spec.md` line 4: *"There are **two** workflows that invoke the `openspec-reviewer`: the `openspec-propose` proposal review … and the SMALL pre-apply premise pass."*
- **Why it blocks:** D6 (design.md line 134) explicitly lists **three** invocation paths: *"the `openspec-propose` proposal review, the **explore direction gate**, and the **SMALL pre-apply premise pass**."* The delta spec was frozen in Review Round 4 *before* D7-D11 were added — it correctly reflected the D1-D6 design (propose + SMALL = two new paths beyond the historical single-path claim). But after the expansion, the explore direction gate is a third path, and the delta spec's "two workflows" claim is now factually false. If the implementer trusts only the delta spec (which is the normative source), they will omit the explore-gate budget row and the explore gate will have no documented budget envelope — exactly the "implementer guessing at the invocation" defect the D5 🔴1 review was designed to prevent.
- **What's needed:** Update the delta spec to say "three workflows" (or at minimum add the explore direction gate as a third invocation path). Add a scenario for it. The verification section already expects both harness rows (design.md line 243), so the spec must match.

#### 2. Delta spec `premise-review-gate/spec.md` has no requirements or scenarios for D7-D11

- **Location:** `openspec/changes/premise-review-gate/specs/premise-review-gate/spec.md` — the entire file covers only D1-D6. There are zero requirements for D7 (explore direction gate — owner/trigger/invocation), D8 (file location: `plans/<slug>/`), D9 (DISSENT at explore + override propagation), D10 (drift definition encoded in reviewer mandate), or D11 (explore-altitude calibration).
- **Why it blocks:** The design.md's Verification section (lines 226-235) lists specific acceptance criteria for D7-D9: the explore skill produces `plans/<slug>/explore-brief.md`, runs the pro premise review, writes to `plans/<slug>/premise-review.md`, surfaces DISSENT with three-way decision, records override, and STOPs before advancing. These are spec-worthy behaviors that the `tasks.md` author and the verify-phase agent need to test. Without scenario coverage in the delta spec, these behaviors are untestable — a gate that looks correct on paper but has an unverified behavior path is a latent defect.
- **What's needed:** Add new requirements (or extend existing ones) to the `premise-review-gate` delta spec covering: (a) the explore direction gate — owner/trigger/invocation model/mandatory brief output; (b) the `plans/<slug>/` file location and verdict sink; (c) DISSENT at explore + override propagation to Altitude 2; (d) the drift definition (D10) as part of the reviewer mandate; (e) the explore-altitude calibration (D11) — dissent only when demonstrably wrong, not merely under-specified. Each needs at least one scenario.

#### 3. D8 — Slug selection for `plans/<slug>/` is entirely unspecified

- **Location:** D8 (design.md lines 158-163): *"write both to a **`plans/<slug>/` directory**: `plans/<slug>/explore-brief.md` … `plans/<slug>/premise-review.md`"*
- **Why it blocks:** The implementer needs to create `plans/<slug>/explore-brief.md` but neither D7 nor D8 says **who chooses the slug** or **how it's chosen**. Does the explore skill derive it from the conversation topic? Does it ask the operator? Does the propose skill name it later? Path construction is blocked entirely on this decision. Without a slug, the `mkdir -p` call can't run, the file write has no target directory, and the downstream drift check has no `explore-brief.md` path to hand to the reviewer.
- **What's needed:** D7 or D8 must state how the slug is selected. Options: (a) the explore skill asks the operator for a name, (b) the explore skill derives a kebab-case slug from the topic, (c) the propose skill names it and the explore skill writes to a temp path that gets renamed. Any one of these is implementable; the current silence is not.

#### 4. D8 — Relocation vs. reference is an unresolved fork

- **Location:** D8 (design.md lines 161-162): *"When the operator advances to `propose`, the propose skill relocates the brief into the change dir (or leaves it in `plans/` and references it — the reviewer already reads `explore-brief.md` 'if it exists')."*
- **Why it blocks:** The phrase *"(or leaves it in `plans/` and references it)"* presents two mutually exclusive options as a disjunction. The implementer doesn't know which to build:
  - **Option A (relocate):** The propose skill moves the file to the change dir. The reviewer invocation prompt points to the change dir. The `plans/` directory becomes an empty stub.
  - **Option B (reference):** The file stays in `plans/`. The reviewer invocation prompt points to `plans/<slug>/`. The propose skill does nothing with the file.
  - These have different propose-skill logic, different reviewer invocation prompts, and different downstream behavior (if the file is relocated, it's discoverable in the change dir; if not, it's only in `plans/`).
- **What's needed:** Pick one option and document it. Both are implementable. The fork itself is the defect.

#### 5. D9 — Override recording protocol in `premise-review.md` is underspecified

- **Location:** D9 (design.md lines 168-172): *"The operator's choice and rationale are recorded in `plans/<slug>/premise-review.md`."* and *"that override is recorded *alongside the verdict* in the same sink."*
- **Why it blocks:** D8 says `premise-review.md` holds "the extracted verdict block" (the `### Premise Verdict` section extracted from the reviewer's stdout). D9 says the override is recorded "alongside the verdict" in the same file. But the implementer doesn't know the protocol:
  - Does the override go **above** the verdict block (risk: the gate parsing logic sees the verdict first)?
  - Does it go **below** (risk: the gate parsing only reads the first `PREMISE:` line)?
  - Does the whole file get restructured to include a "Resolution" section?
  - Is there a machine-parseable format (e.g., `OVERRIDE: operator-to-proceed — <rationale>`)?
  - The apply skill's SMALL gate asserts `premise-review.md` exists with "a resolved verdict (`AGREE` or a recorded override-to-proceed)" — but the gate can't "read" an override if there's no defined format to grep for.
- **What's needed:** Specify the exact format for the override in `premise-review.md`. The natural fit: after the `### Premise Verdict` block (which holds `PREMISE: AGREE` or `PREMISE: DISSENT`), append a `### Resolution` or `### Operator Override` section when the operator overrides, containing `OVERRIDE: proceed` and the rationale. The apply gate and Altitude-2 drift check can then grep for either `PREMISE: AGREE` or `OVERRIDE: proceed`.

---

### 🟡 Should Fix

#### 6. D7 — Explore skill's phase-gate language needs explicit modification

- **Location:** D7 (design.md line 144): *"the explore skill's own STOP-before-advancing guard already holds the gate point."*
- **The gap:** The current explore skill's PHASE GATE (line 16-17 of SKILL.md) says: *"If exploration crystallizes into a concrete plan, tell the user they can say 'propose a change for X' — but do NOT invoke the propose skill yourself."* This is a passive message, not an active gate. D7 requires the explore skill to write `explore-brief.md`, invoke the reviewer via `opencode run`, and present the verdict — all *before* telling the user they can propose. The existing text doesn't describe this sequence. The implementer needs to know that the phase-gate section is being **replaced or augmented** with the active gate steps.
- **Recommendation:** State that the explore skill's "PHASE GATE" block gains: on advancement signal → write `explore-brief.md` → run premise review → present verdict → resolve DISSENT if needed → then surface the advancement hint. This makes the modification concrete rather than implicit.

#### 7. D10/D11 — Drift definition and calibration need concrete placement guidance in the reviewer mandate

- **Location:** D10 (lines 174-180) and D11 (lines 182-188) — both describe reviewer mandate content but don't say where in the mandate file they go.
- **The gap:** The reviewer's `## What to Check` currently has a `### Premise review (proposal.md and SMALL plans only)` subsection (from D3). D10's drift definition and D11's explore-altitude calibration are scope expansions of that subsection — they tell the reviewer "when you see a verified explore brief, also flag drift using this definition" and "at the explore altitude, dissent only when demonstrably wrong." But the design doesn't say they go into the same subsection. The task-writer could place them in the wrong section (e.g., under Anti-Patterns, or as a new top-level section).
- **Recommendation:** Add placement guidance — e.g., *"D10's drift definition and D11's explore-altitude calibration are added as paragraphs within the `### Premise review` subsection of the reviewer's `## What to Check`."*

#### 8. D7 — Advancement signal detection is NLP-dependent and fragile

- **Location:** D7 (design.md line 147): *"Trigger = operator advancement signal … 'propose', 'implement', 'let's go', or similar."*
- **The gap:** The explore skill must detect that the user said "propose" or "let's go." This is inherently NLP-dependent — the skill is running in conversation mode and must parse natural language. If the trigger detection is too narrow, real advancement requests miss the gate; if too broad, idle conversation triggers a spurious gate invocation. The design leaves this entirely to the skill author with no guidance on handling false positives/negatives.
- **Recommendation:** Either (a) add a structured trigger (the explore skill offers an explicit choice: *"Ready to advance? I'll capture the direction and run the premise gate"*) so detection is a button-click, not NLP, or (b) note in Risks that false-negative trigger detection is a known failure mode and the operator can always say "run the direction gate" or "gate the explore brief."

#### 9. Tasks.md — Missing explore-direction-gate row in delegation harness task

- **Location:** `tasks.md` line 16 (task 3.1): *"add **only** a budget-table row `SMALL | premise reviewer (flash) | -k 15 780`"*
- **The gap:** The Verification section (design.md line 243) says the harness has rows for **both** new paths: `explore | direction gate (pro)` AND `SMALL | premise reviewer (flash)`. But task 3.1 only adds the SMALL row. The explore row has no task. The implementer following tasks.md would leave the explore gate without a documented budget row.
- **Recommendation:** Split task 3.1 into two sub-tasks (or add a task) covering both rows. This is a tasks.md defect, but flagged here because the design.md Verification section makes a promise tasks.md doesn't fulfill.

---

### 💡 Suggestions

#### 10. D8 — `plans/` directory existence

D8 says files go in `plans/<slug>/` but neither D7 nor D8 says who creates the `plans/` root directory. The explore skill creates `plans/<slug>/explore-brief.md` but `mkdir -p` handles this. The design could mention it's created on first write by `mkdir -p` — minor clarity.

#### 11. D11 — "Demonstrably wrong" vs. D3's four checks

D11 calibrates the explore altitude: dissent when "demonstrably wrong." D3's four checks are: (1) root, not symptom; (2) solution targets root; (3) scope right-sized; (4) blind spot. At the explore altitude, the brief typically has no concrete scope (problem/solution framing only), so check (3) doesn't apply cleanly. D11 handles this implicitly by saying under-specification is not dissent, but the reviewer might still try to apply check (3) and find nothing to assess. Worth noting that at explore, the reviewer can note "scope not yet concrete — deferred to proposal" rather than flagging it as a concern. This is a reviewer-mandate nuance that the task-writer should capture.

#### 12. D7 — Explore skill `opencode run` invocation shape

D7 says the explore skill invokes the reviewer "via `opencode run` using the existing delegation harness — the same pattern the propose skill uses." The propose skill's invocation uses `timeout -k 15 780 opencode run --agent openspec-reviewer --model deepseek/deepseek-v4-pro`. The explore skill would use the same shape. But the propose skill's invocation also captures stdout/stderr to separate files and runs assert-ran. The design could note that the explore skill needs to handle stdout capture and assert-ran (per the delegation harness contract) — the same as propose but writing to `premise-review.md` instead of `review-log.md`. The task-writer will figure this out, but calling out the shared contract explicitly would reduce implementer guesswork.

---

### D7-D11 Consistency Matrix

| Decision | Consistent with proposal.md? | Consistent with D1-D6? | Contradicts explore skill? | Contradicts propose/apply skills? |
|---|---|---|---|---|
| **D7** (owner/trigger/invocation) | ✓ Matches Altitude 1 spec | ✓ D1 lists `explore-brief.md` as direction artifact | ⚠️ Extends phase-gate (not contradiction — new behavior) | ✓ No overlap with propose/apply |
| **D8** (file location + sink) | ✓ Matches "write to `plans/`" choice | ✓ Consistent with D5's verdict sink pattern | ✓ No existing `plans/` contract | 🔴 Relocation ambiguity affects propose skill |
| **D9** (DISSENT + override propagation) | ✓ Matches "surfaced to operator" framing | ✓ Extends D2b's three-way decision to explore | ✓ Interactive by nature — natural fit | ✓ No contradiction |
| **D10** (drift definition) | ✓ Matches "flag drift" requirement | ✓ Consistent with D3 premise lens | N/A — reviewer mandate change | N/A — reviewer mandate change |
| **D11** (explore calibration) | ✓ Matches "default-to-dissent" calibration risk callout | ✓ Extends D4 without contradicting it | N/A — reviewer mandate change | N/A — reviewer mandate change |

---

### Verdict

**NEEDS REVISION** — five 🔴 blocking issues must be resolved before the design can be considered frozen for D7-D11:

1. **🔴1:** Update `reviewer-budget/spec.md` delta from "two workflows" to "three" (adding the explore direction gate path with a scenario).
2. **🔴2:** Add D7-D11 requirements and scenarios to `premise-review-gate/spec.md`.
3. **🔴3:** D8 — Specify how the `<slug>` is chosen (who determines it, when).
4. **🔴4:** D8 — Resolve the relocation-vs-reference fork — pick one option and drop "(or)".
5. **🔴5:** D9 — Specify the override recording format in `premise-review.md` (exact section and machine-parseable marker).

The five 🟡 items are important for a clean `tasks.md` but do not individually block design freeze. The 💡 items are refinements.

---

## design.md — Round 4 (D7-D11 re-review) (deepseek-v4-pro, 2026-06-20) — VERDICT: PASS (RE-FROZEN; 4 🟡 + 💡7 folded). Deferred 🔴 (specs) handled in the specs step next.

Let me start by reading the design.md and the relevant context files.
Now let me read the existing skills, the reviewer agent, the delegation harness, and existing specs to assess consistency.
Now let me read the delegation harness, existing specs, and the review log.
Now let me read the relevant existing specs and the AGENTS.md SMALL tier section.
Let me read the full AGENTS.md SMALL section and the "After reading this file" acknowledgements.
Let me read the rest of the review log and check the existing delta specs.
Now let me re-read the current design.md with focus on D7-D11, and also check the explore and propose skills one more time for consistency.
Now I have all the context needed. Let me emit the review.

---

## Review Round 5 — design.md (D7-D11 re-review)

### Summary

All three prior 🔴 design-level issues are concretely and precisely resolved in the current text:

- **🔴3 (slug unspecified):** D8 lines 168–171 now derive the slug as a kebab-case identifier from the exploration topic, with collision disambiguation — same convention the propose skill already uses. ✅
- **🔴4 (relocate-vs-reference fork):** D8 lines 172–177 now explicitly resolves to **RELOCATE** — the propose skill moves `plans/<slug>/explore-brief.md` and `premise-review.md` into the change dir. The fork is closed; the "or" disjunction is gone. ✅
- **🔴5 (override recording format):** D9 lines 184–189 now specifies a machine-parseable `### Resolution` section with `OVERRIDE: proceed — <rationale>`, and defines the gate's grep contract (`PREMISE: AGREE` **or** `OVERRIDE: proceed`). ✅

D7-D11 are internally coherent and wire cleanly into D1-D6. The explore-skill gate (D7), file-location/slug/relocation (D8), override propagation (D9), drift definition (D10), and altitude calibration (D11) form a complete, implementable specification for the Altitude 1 direction gate. I find **zero 🔴 blocking issues in the design**. The two prior 🔴 that concern delta specs (reviewer-budget "two workflows" → "three"; premise-review-gate spec missing D7-D11 requirements) are correctly deferred to the specs revision step — they don't reflect design gaps.

Four 🟡 integration-point refinements and three 💡 suggestions follow.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **D8 — The propose skill's relocation step is not explicitly covered by any D1-D6 decision.**  
   - **Location:** D8 lines 172–174.  
   - **The gap:** D8 states that the propose skill moves `plans/<slug>/` files into the change dir. This is a new propose-skill behavior. But the propose-skill changes documented in D1-D6 cover only freeze (D2), assert-ran (D2a), DISSENT branch (D2b), and the premise-assessment prompt. The relocation step has no corresponding decision in the D1-D6 set. The tasks.md author (and the verification section) could overlook this new propose-skill responsibility because it's tucked inside an explore-stage decision (D8).  
   - **Why it matters:** If the task-writer misses the relocation step, the propose skill will silently skip moving the explore-brief into the change dir, breaking the "all artifacts in one canonical location" contract and causing downstream drift checks to miss the brief.  
   - **Recommendation:** Either add a brief sentence to D2/D2b noting "when a verified explore-brief exists in `plans/`, the propose skill relocates it per D8," or ensure the Verification section's explore-gate bullet (line 250–255) explicitly includes the relocation step.

2. **D8 — Slug-to-change-name matching between explore and propose has no explicit handoff.**  
   - **Location:** D8 lines 172–177.  
   - **The gap:** The explore skill derives a slug from the topic (e.g., `add-user-auth`). The propose skill derives a change name from the operator's description. D8 says the propose skill "moves `plans/<slug>/`" — but the propose skill needs to *find* the slug. If the operator says "propose add-user-auth" and the explore topic was "add user auth," both derive to the same slug and the relocation succeeds. But if the operator says "propose auth" and the explore topic was "add user authentication," the slugs diverge and the propose skill won't find the brief.  
   - **Why 🟡 not 🔴:** The natural happy path works — the operator typically uses the same topic language. And the explore-brief is optional context (proposals can proceed without it). But the relocation could silently fail without any feedback.  
   - **Recommendation:** D7's "you can say propose/apply" hint should include the capture name (e.g., "Direction captured as `add-user-auth`. Say 'propose add-user-auth' when ready.") so the operator uses the matching name. Or D8 should note that the propose skill attempts a best-effort match and silently skips relocation when no `plans/<change-name>/` directory exists.

3. **Verification — SMALL pass timing wording is imprecise for the autonomy case.**  
   - **Location:** Verification line 261–262: *"AGENTS.md SMALL tier bullet documents the orchestrator invoking the flash premise pass before operator tier+plan confirmation."*  
   - **The gap:** D5 lines 97–98 explicitly decouples the trigger from operator confirmation: the pass runs *"after the plan is written and before apply delegation — a trigger independent of operator confirmation."* The Verification wording reflects only the no-autonomy path. Under autonomy there is no confirmation prompt, but the pass still runs.  
   - **Recommendation:** Rephrase to *"before apply delegation"* (matching D5's canonical phrasing), or add a clause: *"before apply delegation (which, in the no-autonomy case, is before the operator tier+plan confirmation)."*

4. **Verification — Specs bullet omits the explore direction gate scenario for reviewer-budget.**  
   - **Location:** Verification line 272–273: *"reviewer-budget/spec.md is delta'd per D6 (requirement text **and** a scenario for the SMALL premise-pass invocation path)."*  
   - **The gap:** D6 (line 134) lists **three** invocation paths: propose, explore, and SMALL. But the Verification bullet only mentions a SMALL scenario. The explore direction gate scenario is not explicitly required here. This connects to the deferred 🔴1 (reviewer-budget spec says "two workflows" needs "three"), but the Verification section itself should state the full expectation.  
   - **Recommendation:** Add "and the explore direction gate" so the line reads: *"...a scenario for the SMALL premise-pass invocation path and the explore direction gate."* This ensures the verify-phase orchestrator checks for both paths, not just one.

---

### 💡 Suggestions

5. **D7 — `plans/` root directory creation is implicit.** D8 says `mkdir -p` on first write — a one-line note in D7 that the explore skill creates the directory via `mkdir -p` before writing would make the wiring explicit rather than relying on the task-writer to infer it from D8.

6. **D11 — Scope-check deferral at explore altitude.** D11 correctly says the reviewer notes "scope not yet concrete — deferred to proposal" for D3 check 3. The reviewer mandate's `### Premise review` subsection should explicitly state this deferral language so it's part of the reviewer's prompt, not just design commentary. This is a task-level detail but worth flagging as a 💡 so the mandate task-writer doesn't accidentally encode explore-altitude calibration without the scope deferral text.

7. **D7 — "no new lifecycle step" statement could be misinterpreted.** D7 line 147 says *"no new lifecycle step is added to `AGENTS.md`."* While technically true (the gate is inside the explore phase, not a new phase), the AGENTS.md lifecycle section and "After reading this file" acknowledgements DO change. A reader might misinterpret "no new lifecycle step" as "AGENTS.md is unchanged" — which D5 and the Verification section both contradict. A brief qualifier (*"no new lifecycle step is added to AGENTS.md; the explore phase internally gates advancement"*) would prevent this reading.

---

### D7-D11 Internal Consistency Matrix

| Decision | Consistent with D1-D6? | Consistent with proposal.md? | Integrates with explore skill? | Integrates with propose/apply skills? |
|---|---|---|---|---|
| **D7** (owner/trigger/invocation) | ✅ D1 lists explore-brief as direction artifact | ✅ Matches Altitude 1 spec | ✅ Augments PHASE GATE; preserves "no mandatory output" | ✅ No overlap |
| **D8** (location/slug/relocation) | ✅ Consistent with D5 verdict-sink pattern | ✅ Matches "write to plans/" choice | ✅ Creates `plans/<slug>/` | 🟡 Relocation step not in D1-D6 |
| **D9** (DISSENT + override format) | ✅ Extends D2b three-way decision | ✅ Matches "surfaced to operator" | ✅ Interactive by nature | ✅ Override format machine-parseable |
| **D10** (drift definition) | ✅ Consistent with D3 premise lens | ✅ Matches "flag drift" requirement | N/A — reviewer mandate | N/A — reviewer mandate |
| **D11** (explore calibration) | ✅ Extends D4 without contradicting | ✅ Matches calibration risk callout | N/A — reviewer mandate | N/A — reviewer mandate |

---

### Verdict

**PASS** — ready to freeze and move to `tasks.md` for the expanded scope. The three prior 🔴 design-level issues are concretely and correctly resolved (slug derivation, relocate-not-reference, machine-parseable override format). D7-D11 are internally complete and wire consistently into D1-D6 and the explore/propose/apply skills. The four 🟡 items are integration-point refinements that don't block implementation — they can be folded into `tasks.md` or resolved during task authoring. The two deferred 🔴 (delta specs) are correctly scoped to the next revision step and do not reflect design gaps.

---

## specs — Round 2 (explore-gate expansion) (deepseek-v4-pro, 2026-06-20) — VERDICT: PASS (FROZEN; D7-D11 fully encoded; 🟡 SHALL-retain + 💡 PARTIAL/slug clauses folded).

Now let me run the validation the user mentioned:
Now let me check the existing explore skill to verify the "no mandatory output" constraint referenced in the specs:
Now I have all the context I need. Let me compile the comprehensive review.

---

## Review Round N — delta specs (premise-review-gate + reviewer-budget)

### Summary

The delta specs are high quality and systematically encode every design decision from D7–D11 as explicit requirements with scenarios. The two-altitude gate description is faithfully rendered in the first requirement. `explore-brief.md` is correctly elevated as a third direction artifact alongside `proposal.md` and SMALL plans. The reviewer-budget MODIFIED block correctly updates the requirement text to list three invocation paths and adds the two new scenarios (explore direction gate, SMALL premise pass). There are no contradictions with `tier-confirmation-gate` or `verify-multimodel-gate`. `SHALL` language is used consistently throughout requirements. One minor wording gap is worth noting but not blocking.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **Design `## Verification` section states "the reviewer-mandate" as a unified item, but the spec splits it across four separate requirements.** This is not a defect — it's correct spec decomposition — but the Verification checklist in design.md (line 248) says "Reviewer mandate" as a single acceptance criterion spanning D3/D4/D11/D10/D1. The reviewer implementer reading the design only may not realize these five decisions map to **four** distinct spec requirements (orthogonal verdict, read-only honesty, drift definition, explore-altitude calibration). The implementer can find them, but the design's Verification point is too coarse-grained for a review checklist.  
   - **Where:** `design.md` line 248 vs. `specs/premise-review-gate/spec.md` requirements 2, 3, 10, 11.
   - **Why it matters:** During verify, the orchestrator will check each item against the design's Verification list. If the list says "reviewer mandate" as one thing, the orchestrator might miss checking individual requirements.
   - **Recommendation:** Expand the Verification bullet into sub-items matching the spec requirements, or at minimum list the four requirements by name.

2. **Minor: "retain" lacks SHALL in the freeze-rule requirement.** The requirement "A proposal freezes only on zero blocking issues AND premise agreement" ends with: "`design.md` and `tasks.md` retain the existing zero-🔴 freeze rule." This is a clarifying statement about unchanged behavior, but as part of a SHALL-bearing requirement it reads as weaker than the surrounding SHALL language.  
   - **Where:** `specs/premise-review-gate/spec.md` line 70.
   - **Recommendation:** Change to "`design.md` and `tasks.md` SHALL retain the existing zero-🔴 freeze rule" for consistency with the rest of the spec.

---

### 💡 Suggestions

1. **Scenario completeness for explore advancement hint format.** The design D7 says the explore skill, after resolving the gate, "surfaces the advancement hint naming the captured slug (e.g. 'Direction captured as `add-user-auth` — say `propose add-user-auth` when ready') so the propose skill can locate and relocate the brief (D8)." The spec captures the gate trigger, execution, and verdict resolution but doesn't encode the format of the advancement hint (which is load-bearing for the relocate mechanic — the propose skill needs the slug to find the brief). The relocate scenario only says "WHEN the operator advances a verified brief to `propose`" — it doesn't say how the propose skill **learns** the slug.  
   - **Where:** Design D7/D8, spec requirement "The explore brief and its verdict have a defined home, slug, and relocation" scenario "Propose relocates the brief into the change dir."
   - **Why it matters (low):** The implementer may not realize the propose skill needs a way to find the brief. This is a minor integration detail between two skills — not a spec defect, but worth a quick note in the scenario to make the contract explicit.
   - **Recommendation:** Add a sentence to the relocation scenario: "AND the propose skill receives the slug from the advancement hint so it can locate `plans/<slug>/`."

2. **The "two altitudes" framing in the first requirement is dense.** The first requirement (lines 3–15) packs the entire two-altitude architecture into a single paragraph per altitude. This is correct and accurate but would benefit from a structural break — perhaps a bullet for Altitude 1 and a bullet for Altitude 2 — to match the parallel structure of the design's Goals section. Non-blocking; purely readability.

3. **The `PARTIAL` salvage marker for SMALL is mentioned in the requirement but not in its own scenario.** The SMALL premise pass requirement says "writing the partial to `premise-review.md` marked `PARTIAL`" and there is a scenario "SMALL premise pass timeout is salvaged to premise-review.md" — but that scenario doesn't explicitly assert the `PARTIAL` marker is present.  
   - **Where:** `specs/premise-review-gate/spec.md` lines 106–108 and 135–137.
   - **Recommendation:** Add to the timeout scenario: "AND the output is marked `PARTIAL`" to make the marker testable.

4. **Reviewer-budget existing scenario "Reviewer budget" renamed.** The delta renames the existing scenario from "Reviewer budget" to "Reviewer budget — propose review". This is the correct pattern for the MODIFIED block and the archive reconciler should handle it, but the design D6 describes "generalizes the existing scenario" as an alternative — the actual delta chose "add new scenarios + rename existing" rather than generalization. Either approach is fine; just noting the slight divergence from the design's wording for the archive executor's awareness.

---

### Detail: D7–D11 Encoding Check

| Decision | Requirement Title | Scenarios | Verdict |
|---|---|---|---|
| **D7** (owner, trigger, invocation) | "The explore skill owns and runs the direction gate on an advancement signal" | "Idle exploration triggers nothing", "Advancement choice fires the gate" | ✅ Encoded |
| **D8** (location, slug, relocation) | "The explore brief and its verdict have a defined home, slug, and relocation" | "Brief written to plans with a derived slug", "Propose relocates the brief into the change dir" | ✅ Encoded |
| **D9** (explore DISSENT, override propagation) | "A direction dissent at explore is surfaced and its override propagates" | "Override is recorded machine-parseably and propagates", "Re-think loops back without an override marker" | ✅ Encoded |
| **D10** (drift definition) | "Drift from a verified brief is concretely defined and flagged as a dissent" | "Scope expansion beyond the vetted direction is drift", "A narrower plan is not drift" | ✅ Encoded |
| **D11** (explore-altitude calibration) | "The explore-altitude review is calibrated for an abstract brief" | "Under-specification is not a dissent", "A demonstrably wrong direction is a dissent" | ✅ Encoded |

All five decisions are fully encoded as requirements with scenarios. The drift definition's three prongs (reframed problem, ruled-out approach, scope expansion) are explicitly listed in the requirement text; the calibration's key distinction (demonstrably wrong vs. under-specified) is captured in both requirement text and scenarios.

---

### Detail: Contradiction Check with Existing Specs

- **`tier-confirmation-gate`**: No contradiction. The SMALL premise pass runs **before** the operator confirmation (without autonomy), and its verdict feeds **into** the confirmation prompt. Under autonomy, the pass still runs and the apply gate checks the verdict. Tier-confirmation-gate's gate "between planning and execution, not before planning" is preserved — the premise pass runs after the plan is written.
- **`verify-multimodel-gate`**: No contradiction. The premise-review-gate is explicitly pre-implementation; verify-multimodel-gate is post-implementation. They are described as complementary, not overlapping. The premise-review-gate spec explicitly calls itself "distinct from and in addition to... the post-implementation `verify-multimodel-gate`."
- **`reviewer-budget`**: No contradiction. The MODIFIED delta correctly updates the "only workflow" claim to three workflows. The `openspec verify` parenthetical about behavioral review is preserved verbatim: "(`openspec-verify-change`'s behavioral review is the orchestrator's own, not a wrapped reviewer call)."

---

### Detail: `openspec validate`

The user reports `openspec validate` already passes. I cannot independently verify this (read-only agent, no `bash` access), but the structural indicators are consistent with a passing validation:
- Correct header format (`## ADDED Requirements` / `## MODIFIED Requirements`)
- `### Requirement:` + title pattern matches existing specs
- `#### Scenario:` format matches existing specs
- No orphaned or malformed blocks

---

### Verdict

**PASS** — ready to freeze and move to the next artifact. The 🟡 items are minor wording refinements that do not affect implementation quality or spec correctness. All D7–D11 decisions are fully encoded, the reviewer-budget MODIFIED block correctly updates the existing requirement, SHALL language is consistent, and no contradictions exist with sibling specs.

---

## tasks.md — Round 2 (explore-gate expansion) (deepseek-v4-pro, 2026-06-20) — VERDICT: PASS (FROZEN)

Folded: 🟡2 (split dense 4.2 → 4.2 invocation / 4.3 routing+resilience / 4.4 apply gate), 🟡3 (4.4 gate
pinned immediately after Step 1, fail-fast), 💡2 (2.2 marked synchronous, no EXIT-sentinel), 💡3 (1.1 title
supersession note).
**Overruled (recorded):** 🟡1 "missing Effort: ~N hours field" — the authoritative `openspec instructions
tasks` template is `- [ ] X.Y <desc>` with NO Effort field (verified this session); adding it is noise
against the template. (Same overrule as the pre-expansion tasks round.)

Let me also check the existing AGENTS.md and apply skill for SMALL flow alignment:
## Review Round N — tasks.md

### Summary

The tasks.md is solid and well-aligned with the frozen design. Every D1–D11 decision has at least one corresponding task; there are no orphan tasks (all map to design decisions or cross-cutting AGENTS.md requirements stated in the proposal). All files named are scaffold-managed per `scripts/scaffold_manifest.txt`. The tasks are apply-phase implementation edits to scaffold files — no verify-smoke or spec-promotion tasks (the spec deltas were already created in the propose phase). Dependency order is sane: the reviewer mandate (Section 1) comes first, then the explore/propose/SMALL wiring builds on it.

The chief concern is **lack of explicit effort estimates** on every task, which the AGENTS.md template requires. Secondary: task 4.2 is an unusually dense single task, and task 4.3’s insertion point in the apply skill is underspecified.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **Missing effort estimates on all tasks.** The AGENTS.md template specifies each task should include `Effort: ~N hours`. None of the 14 tasks have this field. While the scope is clear enough to infer effort (each is a single-file documentation edit), an executor that misses this may produce uneven pacing or report confusion. Add `Effort: ~2 hours` (or similar) to each task.

2. **Task 4.2 is a single monolithic task with >10 sub-requirements.** It packs into one checkbox: the orchestrator invocation, the flash command with `--model`, the verdict extraction to `premise-review.md`, the autonomy-grant branching, the `Plan minimum:` contract, the drift context instruction, and the timeout/crash salvage rules. A `deepseek-v4-flash` executor reading this sequentially could easily miss one sub-point (e.g., the autonomy-grant escalation path). Consider splitting into 4.2a (invocation + command + verdict extraction), 4.2b (autonomy-grant branching + escalation), and 4.2c (plan-minimum + drift + salvage).

3. **Task 4.3 gate insertion point is ambiguous.** The task says the gate runs "after change selection (Step 1) and before implementation delegation (Step 6)". In the apply skill, Steps 2–5 (status check, apply instructions, read context, show progress) fall in that range. If the gate is inserted immediately after Step 1, it gates before context has been read — which is efficient (fail-fast) but means the gate runs before the skill has determined it's a SMALL change. If inserted after Step 5 (just before Step 6), it has full context but wastes the context reads for blocked changes. Either is workable, but the task should pick one or note that the implementer should place it as a new step immediately after Step 1 with a brief rationale. (D5 says "after change selection (Step 1)" which suggests early placement.)

---

### 💡 Suggestions

1. **Continuous task numbering.** The current numbering restarts per section (1.1–1.4, 2.1–2.3, etc.). A continuous T1–T14 scheme (or at least Section 1 through Section 6 labels) would make cross-references unambiguous.

2. **Task 2.2 should explicitly state the reviewer call is synchronous.** The delegation harness distinguishes synchronous calls (no EXIT-sentinel) from background calls (§d). The explore direction gate follows the propose pattern, which is synchronous. Adding "synchronous — no EXIT-sentinel needed" would prevent the executor from incorrectly trying to append a background-completion sentinel.

3. **Task 1.1 subsection title note.** The design D3 parenthetical says `(proposal.md and SMALL plans only)`, but D1 and D7 require the lens to also cover `explore-brief.md`. Task 1.1 correctly uses `(direction artifacts: explore-brief.md, proposal.md, SMALL plans)`. This is a faithful correction of the design’s narrower title — but a brief note in the task acknowledging the deviation from D3’s literal text would prevent the executor from second-guessing.

---

### Verdict

**PASS — ready to freeze and move to apply.** The 🟡 issues above are genuine but non-blocking: they affect implementer clarity and pacing, not correctness. The task map from D1–D11 is complete, all files are scaffold-managed, and no orphan/leaked tasks exist.
