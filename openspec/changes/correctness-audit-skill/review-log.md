# Review log — correctness-audit-skill

## proposal.md — Round 1 (2026-07-11, deepseek-v4-pro)

## Review Round 1 — proposal.md

### Summary

The proposal is thorough, well-grounded in the exhaustive research, and closely tracks the verified explore-brief — no drift detected. The problem statement (audit protocol has no scaffold home → both repos independently re-derived it with the same repeating failure modes) is precisely scoped and well-supported. The solution (a scaffold-managed, operator-invoked skill standardizing the charter/census/FINDINGS contract, with evidence discipline, dedup, class-naming, and close-out routing into OW-2's ratchet) directly targets the identified root cause. Scope boundaries are clear and consistent with the explore-brief. No 🔴 blocking issues were found.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **Wave execution model unstated — has delegation-harness implications.** The proposal describes "wave mechanics and gates" and "model routing (judgment → pro-tier, mechanical → flash)" but does not specify whether audit waves execute as in-process subagent calls or out-of-process `opencode run` delegations. This matters because the research (`scaffold-conventions.md` §4) documents that any `timeout -k <G> <B>` command in the skill must match a sanctioned pair from `.claude/skills/_shared/delegation-harness.md`'s §e table, or the `budget-agreement` lint fails. The "Impact — Modified files" list (proposal line 78-81) includes `scaffold_lint.py` (`_NON_OPENSPEC_SKILL_TOKENS`) but does NOT mention the delegation harness file. If the design chooses `opencode run` with a novel timeout budget, the skill author will hit a scaffold-lint SEAL failure that the proposal's file-modification list doesn't anticipate. **Recommendation:** either state in this proposal that the skill uses only in-process subagent calls (no `opencode run`), or acknowledge that the delegation harness table may need a row if a novel budget pair is chosen — this can be resolved at design time, but flagging the decision point now saves rework.

2. **`Class:` field mandatory even for non-generalizable findings?** The proposal line 35 requires "A mandatory `Class:` kebab-slug shared with the ratchet ledger's class slugs." The research shows psc-monitor had findings closed `intentional-by-design` or `doc-only` — genuinely one-off, non-generalizable items. OW-2's Q1/Q2 triage explicitly says Q2=no (not generalizable) yields no ledger entry. Mandating a `Class:` on every finding when many cannot be generalized creates a contract tension: what value goes in `Class:` for a one-off? If the answer is `none` or `N/A`, the proposal should say so explicitly rather than leaving the designer to guess whether the field means "generalizable class (blank/null ok)" or "every finding MUST be classifiable" — the latter would force a false taxonomy. **Recommendation:** clarify that `Class:` is mandatory-to-fill but accepts a sentinel value (e.g. `N/A` or `none`) for non-generalizable findings, or narrow the requirement to "mandatory on graduating-to-generalizable findings."

3. **OW-2 has a known unresolved SHALL-detection defect in its frozen spec.** The research (`ratchet-and-verify-contracts.md` §2, lines 142-150) documents that OW-2's requirement `generalizable-findings-close-only-with-a-recorded-disposition` fails `openspec validate --strict` because the validator mis-detects `SHALL NOT` — a live defect in OW-2's frozen artifact. While this is OW-2's problem (not OW-5's) and shouldn't change the contract OW-5 depends on, it means OW-2's freeze may need a one-word fix during apply. If that happens, OW-5's design references to OW-2's contract text could need a re-check. **Recommendation:** add a brief risk note acknowledging this — it doesn't change the proposal's substance but makes the dependency chain transparent to the designer.

---

### 💡 Suggestions

1. **`_NON_OPENSPEC_SKILL_TOKENS` change could use a brief justification.** The research (`scaffold-conventions.md` §2, lines 134-146) shows this token set addition is belt-and-suspenders — the `_skill_dir_names()` fallback already resolves `correctness-audit` from directory names. The proposal says it will be modified but doesn't explain why. A one-line note ("ensures explicit recognition even before dir scan") would help the implementer understand intent.

2. **AGENTS.md disambiguation placement is under-specified.** The proposal says "a one-sentence disambiguation in AGENTS.md's audit-tooling section and a cross-pointer in run-audit/SKILL.md" (lines 54-55). The current AGENTS.md "Deterministic audit tooling" section (lines 340-369) is exclusively about the `checks.py`/`facts.py`/`run-audit` ceremony — deterministic tooling that never touches LLM judgment. Dropping an LLM-audit-skill cross-reference into that section could conflate the two audit families unless the disambiguation is precise. This is a design-level wording concern, but noting the tension now keeps the design from having to guess at what "disambiguation" was intended.

---

### Verdict

**PASS** — no 🔴 blocking issues. Ready to move to `design.md` after the three 🟡 items are addressed (or explicitly deferred to design resolution).

---

### Premise Verdict

```
PREMISE: AGREE
```

- **Root, not symptom:** The proposal correctly identifies that the **protocol** — not the downstream repos' execution of it — is the missing piece. The six failure modes are downstream symptoms of one root cause (no scaffold-owned protocol home). The research files (extrends §6, psc §6) independently corroborate every failure mode.
- **Solution targets the root:** The proposed scaffold-managed skill directly owns the protocol (charter/census/FINDINGS contract, evidence discipline, wave mechanics, close-out routing). Each of the six failure modes maps to a named mechanism — not a warning paragraph — satisfying the explore-brief's own success criterion.
- **Scope right-sized:** In scope = the skill + dossier lint + propagation wiring. Out of scope = OW-6 cadenced audit, OW-1/OW-4 detectors, retroactive remediation, back-porting, auto-provisioning — all consistent with the explore-brief.
- **Blind spot:** The proposal presumes the wave execution model (in-process subagent vs. `opencode run` delegation) doesn't affect the file-modification surface — but it materially determines whether the delegation harness needs a new budget row (🟡 issue 1 above). This is a design-level detail to resolve, not a direction-level fault.

### Pre-freeze fixes applied (orchestrator, 2026-07-11)
Round 1 returned zero 🔴 + PREMISE: AGREE → freeze condition met. All three 🟡 fixed
pre-freeze with concrete decisions, both 💡 absorbed:
- 🟡1 wave execution model → decided in proposal: existing delegation mechanics, wave work
  sliced into bounded checkpointed invocations reusing sanctioned budget pairs (-k 15 780 /
  -k 30 600); delegation-harness.md NOT modified.
- 🟡2 Class: field → mandatory-to-fill with literal sentinel `Class: none (one-off)` for
  non-generalizable findings; kebab-slug otherwise.
- 🟡3 OW-2 validator defect → known-risk note added to Impact/Sequencing.
- 💡1 token-set justification added; 💡2 AGENTS.md disambiguation placement pinned
  (appended at end of section, naming the two audit families).
**proposal.md FROZEN.**
## design.md — Round 1 (2026-07-11, deepseek-v4-pro)

---

## Review Round — design.md

### Summary

The design is thorough, well-researched, and internally consistent with both the frozen `proposal.md` and the `explore-brief.md`. All six failure modes from the hand-rolled audits map cleanly to named mechanisms (census → stopping rule, `Prior:` → dedup, `Class:` → class naming, refuter-overrule → unreliable refuters, ratchet close-out → closure enforcement, ID pattern → outstanding visibility). The marker-gated lint (D8) correctly handles the legacy-dossier problem. Budget pairs are exclusively sanctioned ones, so the SEAL passes. Integration with OW-2's ratchet is faithful to the frozen contract text.

Two 🔴 blocking issues exist: one is a gap in the close-out procedure that would cause REFUTED findings to trigger CI-visible untriaged-age lint failures after 14 days; the other is a missing design acknowledgment of the `_NON_OPENSPEC_SKILL_TOKENS` scaffold_lint.py edit that the proposal explicitly requires. Both are fixable with targeted clarifications.

### 🔴 Blocking Issues

1. **REFUTED (and Q1=no) findings have no escape from the 14-day untriaged-age lint.** The `outstanding.py`/`knowledge_lint.py` untriaged mechanism (see `scripts/outstanding.py:409-472`) flags any finding-ID in a `FINDINGS*` file not referenced under `knowledge/questions/` as "untriaged," and after 14 days `knowledge_lint.py` exits non-zero. The design's close-out routing (D11) only creates ledger entries (and associated `knowledge/questions/` references) for *qualifying classes* — Q2=yes, generalizable findings. REFUTED findings (Q1=no, false premise) and Q2=no one-offs get **no** `knowledge/questions/` reference, so their IDs remain in the FINDINGS files but invisible to the triage mechanism. After 14 days, every refuted finding will trigger a CI-visible `knowledge_lint.py` failure on the downstream repo — a guaranteed operational surprise. **Why this is blocking:** the skill's close-out procedure is incomplete — a downstream operator who finishes a correctness audit would find their CI broken 14 days later through no fault of their own. **Fix direction:** either (a) the close-out step creates a single `knowledge/questions/correctness-audit-YYYY-MM-close-out.md` listing *all* findings by ID with final dispositions (so all IDs get a triage reference, moving them out of the untriaged bucket), or (b) the skill's procedure explicitly instructs the operator to create a triage reference for every finding ID at close-out, including refuted/one-off ones.

2. **`_NON_OPENSPEC_SKILL_TOKENS` edit not reflected in design decisions.** The frozen `proposal.md` explicitly says `correctness-audit` must be added to `scaffold_lint.py`'s `_NON_OPENSPEC_SKILL_TOKENS` (line 63-64 of proposal.md: *"`correctness-audit` added to `scaffold_lint.py`'s `_NON_OPENSPEC_SKILL_TOKENS`"*). The design's 12 decisions (D1-D12) do not mention this edit at all. While the research (`scaffold-conventions.md` §2, lines 131-146) documents the rationale, and the verification criteria implicitly cover SEAL pass (which would catch a missing token edit), an implementer reading only the design decisions could omit this edit and hit a SEAL failure late. **Why this is blocking:** the `dangling-skill-refs` check in `scaffold_lint.py` scans for non-`openspec-` skill tokens; if `correctness-audit` appears in `run-audit/SKILL.md` or `AGENTS.md` (as both the proposal and design say it will — the cross-pointer in `run-audit/SKILL.md` and the disambiguation sentence in `AGENTS.md`), and it's not in `_NON_OPENSPEC_SKILL_TOKENS`, the SEAL `test_live_repo_lints_clean` will fail. The fix is simple: add a brief sentence to D1 or a new sub-bullet noting the `scaffold_lint.py` token-set edit.

### 🟡 Should Fix

1. **D6 wave delegation mechanism is ambiguous about in-process vs. `opencode run` timeout coverage.** The design says waves use "`opencode run` under the shared delegation harness §a–e, or in-process subagents where the platform provides them — harness carve-out applies." The timeout budget pairs (`-k 15 780`, `-k 30 600`) are only meaningful for `opencode run`; in-process subagents are exempt per the harness carve-out and have no bounded-wait guard. If an investigation runs as an in-process subagent with no timeout, a stuck model could hang indefinitely. **Recommended fix:** clarify that the primary path is `opencode run` with the sanctioned budgets, and in-process subagents are a fallback only (not the default), or specify an equivalent timeout mechanism for the in-process path.

2. **D8: missing edge case — dossier dir exists but `CHARTER.md` is absent.** The marker-gate design says "dossier without marker → skipped entirely" and "absent dossier → clean," but doesn't explicitly cover the case where `knowledge/research/correctness-audit-*/` exists but `CHARTER.md` doesn't. A `FileNotFoundError` on `CHARTER.md` read would crash the check rather than skip gracefully. **Recommended fix:** the design should note that missing `CHARTER.md` is treated the same as absent marker → skipped (same "absent CH → clean" fallback).

3. **`UNVERIFIABLE-HERE` evidence label is absent from D4's fixed label set.** psc's research (`psc-audit-method.md` §7 vocabulary table) documents this as an explicit label for claims needing unavailable resources. The design's D4 only lists `VERIFIED-BY-{repro|trace|test}` / `LEAD` / `REFUTED`. If an audit encounters a claim that can't be verified with available tools, there's no label for it — it stays `LEAD` forever (and never graduates), which could block census completion. **Recommended fix:** either add `UNVERIFIABLE-HERE` as a valid evidence label (a non-`LEAD` disposition that triggers the `Prior:`/`Class:` lint requirement), or explicitly state that such findings remain `LEAD-deferred` in the census and are handled at the operator's discretion at close-out.

4. **D2 prior-knowledge register format and location are unspecified.** The charter template includes a "prior-knowledge register pointer" but the design gives no guidance on what the register looks like or where it lives. Both repos converged on `known-findings-ledger.md` with FIXED/ACCEPTED-BY-DESIGN/ADMITTED-OPEN sections and a PRIOR-AUDIT-COVERAGE-MAP. If every downstream operator invents their own format, the dedup grep (D7) that searches the register won't work reliably. **Recommended fix:** the design should specify that the prior-knowledge register is a per-repo markdown file (location and format are guided by the skill's wiring walk-through, not scaffold-standardized), but the skill's inlined templates should include a suggested register format that the D7 grep can search.

### 💡 Suggestions

1. **D4: cross-reference `Class: none (one-off)` to OW-2's Q2=no explicitly.** The design says `Class:` is mandatory-to-fill and uses `none (one-off)` as sentinel. The close-out D11 says Q2=no → no ledger entry. Explicitly noting that `Class: none (one-off)` = "Q2=no, point fix suffices" tightens the spec integration and prevents future implementers from incorrectly creating ledger entries for one-off findings.

2. **D5 refutation protocol: elevate "refuters may file new leads" from observation to instruction.** The research shows psc found a real sibling defect during refutation. The design says "refuters may file new leads" as observation. Making it an explicit instruction in the skill text (e.g., "If you discover a materially similar real defect during refutation, file it as a new lead immediately") would mechanize this discovery value rather than leaving it to chance.

3. **Verification criteria: separate `knowledge_lint.py` live-tree check into its own bullet.** Currently "Live tree passes `knowledge_lint.py` (this repo has no dossier → check inert) and the full pytest suite including the scaffold SEAL" is one bullet covering two distinct verifications. Splitting them makes each independently testable and harder to overlook during verify.

4. **D6: note that the skill will cite `_shared/delegation-harness.md` explicitly.** The four existing delegating skills all cite the harness. Adding a sentence to D6 stating "the skill's SKILL.md cites `_shared/delegation-harness.md` for invocation mechanics (matching the propose/apply/verify/archive precedent)" would make the implementation contract clearer.

### Verdict

**NEEDS REVISION** — address the two 🔴 issues before proceeding to `tasks.md`. The 🟡 items are important quality improvements but not hard blockers for freeze.

## design.md — Round 2 (2026-07-11, deepseek-v4-pro; reviewer numbered it Round 3)


### Summary

The design is thorough, well-researched, and directly addresses both Round 1 🔴 blocking issues. The D11 per-wave-gate triage file correctly closes the REFUTED/one-off escape from the 14-day untriaged-age lint, and the D1 text now explicitly covers the `_NON_OPENSPEC_SKILL_TOKENS` edit. All four 🟡 items from Round 1 have been addressed with substantive additions (D6 clarifies the delegation path, D8 covers the missing-CHARTER.md case, D4 adds `UNVERIFIABLE-HERE` as a graduated label, and D7 specifies the prior-knowledge register format). The four 💡 suggestions are also absorbed. No 🔴 blocking issues remain. Two 🟡 items identify boundary cases where operator action is implied but not explicit, and a few 💡 suggestions offer wording clarifications.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **`LEAD-deferred` findings at audit close — path to the triage file is implied but not explicit.** D11's per-wave-gate triage file appends only "each newly graduated finding's ID and current disposition." Findings that remain `LEAD` (census disposition `LEAD-deferred`) at audit close — such as `UNVERIFIABLE-HERE` findings — never pass through the refutation-to-graduation pipeline and therefore may never get a triage reference appended. D4 says these are "dispositioned by the operator at close-out," which implies the operator adds a triage reference, but D11 doesn't state it. Without an explicit triage-file entry, the finding ID would still be in the FINDINGS file with no `knowledge/questions/` reference, and the 14-day untriaged-age lint would fire after audit close. **Fix direction:** add one sentence to D11's close-out paragraph stating that `LEAD-deferred` findings (including `UNVERIFIABLE-HERE`) get their IDs appended to the triage file at close-out as part of operator dispositioning.

2. **`UNVERIFIABLE-HERE` → mandatory `Class:` field creates a semantic tension.** D4 makes `Class:` mandatory-to-fill for all graduated findings (non-`LEAD` evidence). D4 also makes `UNVERIFIABLE-HERE` a graduated label. But for a genuinely unverifiable finding — where the operator literally cannot determine the nature of the defect — forcing a `Class:` slug (either a real class name or the literal sentinel `none (one-off)`) is awkward: the operator is declaring something about a finding they can't verify. The sentinel `none (one-off)` is the pragmatic fallback, but using it for an unverifiable finding that *might* be a class-level defect silently closes off the class-naming path. **Fix direction:** either (a) allow `UNVERIFIABLE-HERE` findings to carry `Class: TBD` without triggering the D8 lint (add `TBD` as a deferred-explicitly sentinel alongside `none (one-off)`), or (b) add a brief rationale sentence to D4 explaining that `none (one-off)` is the safe default for unverifiable findings and the operator can re-open with a class slug if later evidence surfaces.

---

### 💡 Suggestions

1. **D11 triage file format could use a minimal entry template.** The untriaged mechanism is a simple grep for the ID string — any format works mechanically. But for operator readability and consistency across audits, consider specifying a minimal format in D11, e.g. `- CA-W1-03: REFUTED — false premise` or `- CA-W2-07: none (one-off) — point fix`. This is purely a guidance improvement, not a mechanical requirement.

2. **D4 evidence label set — `UNVERIFIABLE-HERE` census disposition change is not mechanized.** D4 says `UNVERIFIABLE-HERE` findings have "its census row becomes `LEAD-deferred`." This census-side update happens at graduation time, but neither D3 (census mechanics) nor D5 (graduation) explicitly describes the census-update step. The implementer of the SKILL.md text will need to spell this out. Not a design defect — just noting that the census write-back for `UNVERIFIABLE-HERE` is a procedure detail the design expects the skill text to carry.

3. **D8 verification bullet for live-tree knowledge_lint is ambiguous about the untriaged-age check.** The verification says "Live tree passes `knowledge_lint.py` (this repo has no dossier → check inert)." This covers the new D8 `_check_audit_dossier` being inert, but the existing `_check_untriaged_age` also runs. Since no dossier exists, both are inert — which is correct. But a reader might wonder: what about when a dossier DOES exist? The D8 fixture tests cover the dossier-format checks, but no verification criterion covers the interaction between the D8 lint and the existing untriaged-age lint (i.e., that graduated findings with triage-file references don't lint stale). This is inherently untestable in a unit test (it depends on real git dates), but consider adding a verification note that the operator should verify this manually during the first real audit.

4. **D11 wording — "appended at every wave gate" could be more precise about timing within the gate.** The wave gate is an explicit operator checkpoint. "Appended at every wave gate" means the operator (or skill text) does the append as part of the gate ceremony. Making this a concrete step in the wave-gate checklist — "Append each newly graduated finding's ID to the triage file, then present the gate" — would reduce ambiguity for the skill author. This is a wording suggestion for the SKILL.md, not a design defect.

---

### Verdict

**PASS** — zero 🔴 blocking issues. Ready to freeze and move to `tasks.md`. The two 🟡 items are boundary-case clarifications that don't affect the design's core correctness, and the 💡 suggestions are optional quality improvements.

### Pre-freeze fixes applied after Round 2 (orchestrator, 2026-07-11)
Round 2 returned zero 🔴 (PASS) → freeze condition met. Both 🟡 fixed pre-freeze:
- 🟡1 → D11 now states LEAD-deferred/UNVERIFIABLE-HERE findings get triage-file IDs
  appended at close-out ("no ID leaves the audit without a triage reference").
- 🟡2 → D4: UNVERIFIABLE-HERE takes Class: none (one-off) as safe default with re-open
  rationale (option b).
💡s absorbed: triage entry line format in D11; census write-back added to D5; first-real-
audit manual verification bullet added; wave-gate checklist timing pinned in D11.
**design.md FROZEN.**
## specs (both deltas) — Round 1 (2026-07-11, deepseek-v4-pro; first invocation timed out at budget, salvaged per harness rule and re-run once)


### Summary

The two delta specs faithfully encode the 12 frozen design decisions from `design.md` with **one structural gap**: the **graduation log** (D4) is mentioned in a scenario but never defined as a required artifact — an implementer reading only the spec would not know to create or maintain it. The OW-2 interface vocabulary is reused correctly by normative reference, with verbatim keywords (`waiver:review-by`, `Q2=no`) appearing where they do surface. No contradictions with existing capabilities (`knowledge-lint`, `outstanding-work-view`, `verify-multimodel-gate`, `noninteractive-delegation-safety`) were found. Format discipline (requirement/scenario structure, SHALL normativity) is consistent with existing specs.

---

### 🔴 Blocking Issues

1. **Graduation log is referenced but never defined as a required artifact** — `specs/correctness-audit/spec.md`, requirement "findings-graduate-only-through-adversarial-refutation-with-orchestrator-re-check". Design D4 explicitly states: *"A graduation log is appended at the top of each FINDINGS file (append-only history of refutation sessions), separate from in-place field updates."* The spec mentions "graduation log" exactly once — in the "refuter verdict is wrong" scenario (`"with the overrule recorded in the graduation log"`) — but never defines what a graduation log is, where it goes (top of FINDINGS files), what format it follows, or that it MUST exist. Since the graduation log is the durable evidence trail for the refutation-and-re-check pipeline (D5), and the spec's "Requirements" section is what drives implementation, this is a structural gap: the implementer would know findings have fields but wouldn't know to maintain the append-only refutation history artifact that ties those fields to their evidence provenance. **Fix:** add a requirement (or extend an existing one) stating that each FINDINGS file SHALL carry an append-only graduation log at its top recording refutation sessions, separate from in-place field updates.

---

### 🟡 Should Fix

1. **OW-2 ledger line format and disposition keywords delegated by reference, not reproduced** — `specs/correctness-audit/spec.md`, requirement "every-finding-id-is-triage-referenced-and-close-out-routes-into-the-ratchet". The spec says *"using the ratchet's exact line format and disposition keywords"* without stating what those are. The research digest explicitly requires OW-5 to reuse the verbatim line format (`- **YYYY-MM-DD** · <kebab-class-slug> · <disposition> — <essence>`) and the five disposition keywords (`check:<pointer>`, `test:<path>[::<name>]`, `waiver:review-by YYYY-MM-DD`, `open:since YYYY-MM-DD`, `grandfathered`). Since this spec has an apply-order dependency on OW-2 (OW-2 must be applied first), the cross-reference is technically valid — but the implementer cannot fully understand the close-out contract from this spec alone. **Why it matters:** if OW-2's apply session changes the line format or keywords (unlikely but possible), this spec's "exact" reference silently drifts. **Fix:** add a brief normative statement reproducing the exact line format and the five disposition keywords, so this spec is self-contained for the OW-2 interface surface it consumes.

2. **Prior-knowledge register referenced but never defined as a contract element** — `specs/correctness-audit/spec.md`, requirements "the-dossier-is-the-durable-record-and-checkpoint-state" and "findings-follow-the-standard-entry-contract". The spec mentions "prior-knowledge register pointer" in the charter and uses "prior-knowledge register" as a grep target for the `Prior:` field, but never defines: (a) what format the register follows, (b) its typical location convention, or (c) that the charter's pointer field makes it a deterministic target. Design D7 defines it with a suggested default path (`knowledge/reference/known-findings-ledger.md`) and an inlined template in the skill. **Why it matters:** the `Prior:` field's dedup mechanism (D7) depends on a deterministic grep target — if the charter's pointer is missing or the register format is not understood, the dedup is silently unreliable. **Fix:** add a brief requirement or scenario stating that the charter SHALL record the path to a prior-knowledge register whose format follows the template inlined in the skill, making the D7 grep deterministic.

3. **"Typically `waiver:`" in requirement body weaker than scenario's `waiver:review-by`** — `specs/correctness-audit/spec.md`, requirement "every-finding-id-is-triage-referenced-and-close-out-routes-into-the-ratchet". The requirement says *"typically `waiver:` with the rationale"* while the matching scenario uses the full OW-2 form *"a `waiver:review-by` disposition recording the rationale."* The OW-2 contract's allowance is specifically `waiver:review-by YYYY-MM-DD`, not bare `waiver:`. **Why it matters:** if an implementer reads only the requirement body and creates a `waiver:some reason` line, it would fail OW-2's `_check_ratchet_log` lint which expects `waiver:review-by YYYY-MM-DD`. **Fix:** harmonize the requirement body to use the full form `waiver:review-by` to match the scenario and OW-2's contract.

---

### 💡 Suggestions

1. **Add explicit Q1/Q2/Q3 mapping for readability** — `specs/correctness-audit/spec.md`, requirement "every-finding-id-is-triage-referenced-and-close-out-routes-into-the-ratchet". The spec uses "Q2=no" but never spells out what Q1/Q2/Q3 are. Adding a parenthetical `(Q1: real defect? → Q2: generalizable class? → Q3: mechanically detectable or test-freezable?)` would make the spec self-documenting without requiring OW-2 lookup.

2. **Include the default finding-ID pattern for self-containment** — `specs/correctness-audit/spec.md`, requirement "findings-follow-the-standard-entry-contract". The spec says the ID *"matches the shipped outstanding-fact default ID pattern"* without stating the pattern. A brief parenthetical `(\b[A-Z]{2,}(?:-[A-Z0-9]+)?-\d+\b)` costs nothing and eliminates a cross-document dependency.

3. **Consistency of `<YYYY-MM>` placeholders** — `specs/correctness-audit/spec.md`. The dossier directory uses `correctness-audit-<YYYY-MM>/` and the triage file uses `correctness-audit-<YYYY-MM>-triage.md`. Both are internally consistent and match the design (D2, D11). No action needed — noting for completeness.

---

### Verdict

**NEEDS REVISION — address 🔴 issue (graduation log definition) before proceeding.**

The single 🔴 is a spec-contract gap: the graduation log is a load-bearing evidence-trail artifact (D4/D5) that the spec references but does not define. Fixing it is a one-requirement addition. The 🟡 items are self-containment improvements that prevent silent drift and cross-document ambiguity — fix them now rather than rediscovering them at implementation or archive time.

**PREMISE: AGREE**
- None. The spec deltas faithfully encode the problem (unowned audit protocol causing repeated hand-rolled failure modes), the root cause (protocol has no scaffold home), and the solution direction (scaffold-owned skill standardizing the protocol while leaving product judgment per-repo). The 12 design decisions are all accounted for in the requirements, and the close-out routing into OW-2's ratchet interface uses the correct vocabulary and triage decision rule.

## specs (both deltas) — Round 2 (2026-07-11, deepseek-v4-pro)


### Summary

Both delta specs now pass all Round 1 findings cleanly. The 🔴 graduation-log gap is closed (now defined with placement, content, and purpose). The three 🟡 concerns are resolved: OW-2 vocabulary is reproduced verbatim (cross-checked against the research digest — line format and five disposition keywords match character-for-character), the prior-knowledge register is defined with default path and format reference, and `waiver:review-by` now appears in full form everywhere. The two 💡 quality-of-life additions (Q1/Q2/Q3 spelled out, ID regex inlined) are present. The two specs are internally consistent with each other and with the frozen `design.md`. No regressions detected — no existing requirement was weakened or made contradictory by the fixes.

One 🟡 observation about a boundary interaction that the implementer will need to handle, and two minor 💡 style notes. No 🔴 issues.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **`UNVERIFIABLE-HERE` census-row write-back is described in requirement prose but never exercised by a scenario.** The correctness-audit spec states (line 74–75) that `UNVERIFIABLE-HERE` findings "SHALL default to `Class: none (one-off)`" and (via reference to D4/D5 in the design) that their census row becomes `LEAD-deferred`. The knowledge-lint spec checks census dispositions against the fixed set that includes `LEAD-deferred`, so the lint interaction is covered. But the correctness-audit spec has no scenario confirming the census write-back for this label — e.g., "**WHEN** a finding graduates with `UNVERIFIABLE-HERE` evidence / **THEN** its census row disposition is set to `LEAD-deferred`." The implementer building the SKILL.md text will discover this census-update step from the design (D4/D5), not the spec. Not a hard blocker — the requirement prose is clear — but adding a one-paragraph scenario would close the completeness gap and match the pattern of every other evidence label having scenario coverage.

---

### 💡 Suggestions

1. **Graduation log has no deterministic lint enforcement.** The correctness-audit spec requires an append-only graduation log at the top of each FINDINGS file (lines 96–98), but the knowledge-lint's D8 check validates only duplicate IDs, census dispositions, and `Prior:`/`Class:` presence on graduated findings — it never checks that the graduation log exists or is well-formed. The design explicitly scopes D8 to "core" format checks, so this is not a spec defect, but it means the graduation log — the *load-bearing evidence trail for the entire refutation-graduation pipeline* — has weaker mechanical enforcement than the entry fields do. The implementation should note this: the lint catches malformed entries but cannot catch a missing or incoherent graduation trail.

2. **The final requirement in correctness-audit ("every-finding-id-is-triage-referenced-and-close-out-routes-into-the-ratchet", lines 138–173) spans 36 lines across five distinct behaviors** (triage file lifecycle, per-wave-gate append, close-out append for ungraduated, ratchet routing with Q1/Q2/Q3, ledger line format, waiver-vs-prose rule, REFUTED handling, remediation queue). A single scenario for each sub-behavior would make the spec more testable and reduce the implementer's risk of missing one of the five. This matches the design's single D11 decision, so it is structurally sound — but consider whether splitting into two requirements (triage-file mechanics vs. ratchet close-out routing) would improve implementability for a later reader.

---

### Verdict

**PASS** — zero 🔴 blocking issues. Ready to freeze and move to `tasks.md`. The 🟡 item is a scenario-completeness gap that the design already covers; the 💡 items are optional quality improvements.

### Premise Verdict

```
PREMISE: AGREE
```

- **No drift from the verified explore-brief.** The two delta specs faithfully encode the explored problem (unowned audit protocol causing repeated hand-rolled failure modes), root cause (protocol has no scaffold home), and solution direction (scaffold-owned skill standardizing the protocol while leaving product judgment per-repo). All six named failure modes map to spec requirements.
- **No drift from the frozen design.md.** All 12 design decisions are accounted for in the requirements. The close-out routing into OW-2's ratchet interface uses the correct vocabulary and triage decision rule, verbatim.
- **Scope remains right-sized.** In scope: the skill's protocol contract + dossier lint. Out of scope: cadenced audit (OW-6), detectors (OW-1/OW-4), auto-provisioning, remediation execution — identical to the frozen design.

### Pre-freeze fixes applied after specs Round 2 (orchestrator, 2026-07-11)
Round 2 returned zero 🔴 (PASS) → freeze condition met. The 🟡 fixed pre-freeze:
- UNVERIFIABLE-HERE census write-back now has its own scenario.
💡 dispositions: graduation-log-not-lint-enforced caveat carried to notes.md (design
scopes D8 to core format checks deliberately); requirement-split suggestion DECLINED —
reviewer's own assessment is "structurally sound, matches the design's single D11
decision"; splitting would decouple the triage-file and ratchet halves of one invariant
(no ID leaves untriaged, nothing closes silently), which land or fail together.
**Both spec deltas FROZEN.** `openspec validate --strict` clean.

## tasks.md — Round 1 (2026-07-11, deepseek-v4-pro; first invocation was an operational instant-kill with zero output — empty stderr, one step_start event — re-run once per crash ladder)


### Summary

The `tasks.md` is thoroughly constructed. Every design decision (D1–D12) maps to at least one concrete task, each task is apply-phase executor work (no verify/archive checkboxes), tasks are correctly sequenced, and path/line references to the live tree are accurate. The executor can proceed sequentially without inventing decisions. The only substantive concern is a moderate-yield 🟡 issue: one load-bearing D7 detail (per-wave `Class:` re-read) is not explicitly called out in the task sub-sections the executor would use as a checklist, relying solely on the catch-all "sourcing from design decisions" instruction. The remaining findings are diagnostic/wording notes.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **D7's per-wave mechanical `Class:` re-read step is not explicitly listed in task 1.2's Waves or Wave gate sub-sections.** Design D7 requires: *"Each wave opens with a mechanical re-read of all prior waves' `Class:` lines (a grep, flash-tier)."* This is a concrete procedural step — distinct from the `Prior:` field requirement and the wave-gate checklist — that prevents cross-wave duplicates (one of the six explore-brief failure modes). The task 1.2 sub-section "**Waves**" describes slice boundaries and delegation mechanics but does not name this step, and "**Wave gate**" covers the post-wave checklist (census→graduation→triage→gate) but not the pre-wave opening step. The catch-all instruction *"sourcing every behavior from the frozen spec delta and design decisions"* serves as backstop coverage, but an executor working from the enumerated sub-sections as a checklist could miss it. **Recommend:** add an explicit bullet under the Waves sub-section, e.g. *"Each wave opens with a mechanical `Class:` re-read of prior waves (flash-tier grep, D7)"* — or fold it into the Wave gate checklist as a pre-condition.

2. **Task 2.1's "check registry" phrasing is slightly misleading for `knowledge_lint.py`.** The task says *"wire it into the check registry/run sequence the same way as the other checks"* — but `knowledge_lint.py` has no registry data structure; the `collect_findings` function (line 932) is a flat sequence of `findings.extend(_check_*(...))` calls. The instruction is still actionable (the executor reading the adjacent code will see the pattern), but the word "registry" adds a moment of confusion for a flash-tier executor. **No code change needed** — just note this as a wording concession.

---

### 💡 Suggestions

1. **Task 3.3's placement instruction has mild ambiguity.** *"Append one sentence at the END of AGENTS.md's `## Deterministic audit tooling` section (inside the synced span, after the task-runner paragraph)"* — the section ends with a "Discover checks" paragraph (line 366–368); "after the task-runner paragraph" could mean after line 364 (between the task-runner and discover-checks paragraphs) or after line 368 (as a new final paragraph). Either is within the synced span and won't break the gate, but an explicit "as a new final paragraph after the 'Discover checks' paragraph" would remove all doubt.

2. **Task 1.1's "Interpreter convention" block may be partially unnecessary.** Unlike `run-audit` which directly runs Python CLI tools, the correctness-audit skill primarily delegates to `opencode run`. The task says to copy the convention block "in form" from `run-audit/SKILL.md:23-28` — which is harmless but may introduce a paragraph about resolving `<py>` that an executor finds confusing when the skill's own procedures use `opencode run` rather than `<py>`. Consider whether to adapt it or include it only if the skill actually invokes Python directly (e.g. for census-skeleton seeding via `facts.py`).

3. **The `openspec validate --strict` acceptance criterion.** The design.md Verification section requires `openspec validate correctness-audit-skill --strict` to pass before freeze. This is verify-phase work (correctly not a task checkbox), but the orchestrator should note it as a verify checkpoint. A one-line note in the sequencing preamble would help: *"After apply, verify includes `openspec validate correctness-audit-skill --strict` per design Verification §."*

---

### Verdict

**PASS** — ready to freeze and move to next artifact. The 🟡 items are diagnostic refinements, not rework-risking defects; the task set covers every frozen requirement and design decision.

### Pre-freeze fixes applied after tasks Round 1 (orchestrator, 2026-07-11)
Round 1 returned zero 🔴 (PASS) → freeze condition met. Fixed pre-freeze:
- 🟡1 per-wave Class: re-read now an explicit bullet in task 1.2 Waves.
- 🟡2 "check registry" reworded to the actual flat collect_findings() extend-call.
- 💡1 task 3.3 placement pinned (new final paragraph after "Discover checks").
- 💡2 interpreter-convention block justified (skill invokes facts.py/knowledge_lint
  directly).
- 💡3 sequencing preamble notes the validate-at-verify checkpoint.
**tasks.md FROZEN. Propose phase complete: 4/4 artifacts frozen (proposal, design,
2 spec deltas, tasks) — proposal 1 round, design 2 rounds, specs 2 rounds, tasks 1
round, zero 🔴 outstanding anywhere, PREMISE: AGREE at direction gate, proposal, and
specs.**
