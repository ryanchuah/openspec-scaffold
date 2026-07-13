# Review log — lesson-check-ratchet

## Round 1 — direction gate (explore-brief premise review) · deepseek-v4-pro · 2026-07-10

## Review Round 1 — `plans/lesson-check-ratchet/explore-brief.md` (premise review)

### Summary

This is an exceptionally well-grounded explore brief. The problem — discovered defect classes do not durably close because prose lessons are write-only memory — is proven twice over, in two independent repos, with named recurrence cycles (psc-monitor: B5→CA-W2-05, F16→CA-W2-02; extrends: wave3→wave4 label destruction, fail-soft 3×, wrong-boundary mocking 2×). The root-cause analysis identifies two genuine structural gaps — no closure contract, no cheap place to put an enforcing artifact — that the codebase confirms: `[checks.custom.*]` exists but is an unparsed, convention-less escape hatch with zero process invocations. The three-leg solution (closure rule, invariant framework, close-out routing) is coherent and respects every prior-art constraint (D3 check-only, D7 scaffold/home split, knowledge/ taxonomy, scaffold_lint.py precedent, YAGNI deferrals). No existing spec conflicts — the 12 capability specs are all additive-compatible.

### 🔴 Blocking Issues

None.

### 🟡 Should Fix

1. **Waiver staleness is unaddressed.** The brief correctly identifies waivers as the "honest non-gap" disposition for domain-judgment-only classes, and the ergonomics constraint says "waiver always available but explicit and lintable." But waivers are a one-way valve — a class waived today because "no good mechanical check exists" may become checkable six months later when new tooling or patterns emerge. Without a re-review cadence or expiration, waivers silently degrade into the same write-only memory as today's prose lessons. This is a design.md concern, not a direction fault — but it should be called out explicitly as a design risk now so it doesn't fall through the cracks.

2. **"Frozen regression test" linkage verification is unspecified.** The brief says "frozen regression test (pytest, exists today; the ratchet just records the linkage)." The key question is whether the ratchet *verifies* the linkage (i.e., the test still exists and still exercises the class) or is purely declarative. A declarative-only linkage means a test can be deleted or refactored away and the ratchet entry still says "covered" — the same false-sense-of-security problem the ratchet is meant to solve. The budget-agreement precedent in `scaffold_lint.py` (cross-checking two artifacts for drift) is exactly the shape that should be applied here: the ratchet should verify that a recorded "frozen test" entry actually points at a live, passing test that covers the class. Again, design.md territory — but worth surfacing now.

3. **Code-shape detector performance vs. SQL.** The brief generalizes data-lint's flat-directory pattern to code/repo-shape detectors. Data-lint's SQL checks run against a database (bounded by schema size, read-only, timeout-bounded). Code-shape detectors (semgrep rules, ast-grep patterns, or bespoke Python per-file) run across the entire repo tree at a different cost profile. The brief notes "implementation choice — bespoke per-file Python vs. semgrep/ast-grep rules — is a design.md decision" but doesn't flag that the timeout model (data-lint's per-check 120s default) may need to be different for whole-tree scans. A repo with 15 code-shape invariants each running semgrep across the full tree could be minutes of wall-clock — not a showstopper, but a design constraint that should be surfaced now.

### 💡 Suggestions

1. **Establish a disposition preference ordering.** The three dispositions (check, frozen test, waiver) are presented as equal alternatives, but the ergonomics constraint means the waiver (cheapest to record) will be chosen by default unless the ratchet has a stated preference: *check is preferred over frozen test is preferred over waiver*. Without this, "waiver always available" becomes "waiver always chosen." This is a small rule-text addition, not a design change.

2. **Acknowledge the self-referential bootstrap.** "Scaffold's own tree passing the new lint" means the ratchet rule itself needs a ratchet entry (a check verifying the ratchet's own ledger format, analogous to `_check_audit_log` in `knowledge_lint.py`). This is philosophically clean and precedented, but noting it now would save a design.md "wait, what guards the guard?" digression.

3. **Consider a one-time "grandfathered" disposition.** The brief says existing lessons are grandfathered with "an explicit one-time triage parked as follow-up." Adding a fourth disposition — `grandfathered` — for legacy entries would let the lint distinguish "this entry was explicitly reviewed and deferred" from "this entry was never triaged" (which should be a lint finding). Without it, the lint can't distinguish a legacy untriaged entry from a new untriaged entry, creating noise.

4. **Downstream adoption risk is real but unstated.** Per D7, the framework ships centrally, invariants are per-repo follow-on SMALL changes. The brief correctly respects this, but doesn't acknowledge the risk that downstream repos simply leave the framework empty and never adopt. The ratchet's value depends on per-repo execution. This is not a design defect — it's the correct separation — but stating the risk explicitly would strengthen the brief's credibility with the operator.

### Premise Verdict

```
PREMISE: AGREE
```

**Cited concerns:**
- **Root, not symptom** — PASS. The brief goes beyond "bugs recur" to identify the two structural gaps (no closure contract, no cheap artifact slot) that cause recurrence. The evidence from two independent repos with named recurrence cycles within the same audit program is the strongest signal available short of a controlled trial.
- **Solution targets the root** — PASS. The three legs are tightly coupled and directly address both structural gaps. The ergonomics constraint (≤minutes per finding, ≤3 classification questions) is correctly identified as load-bearing.
- **Scope right-sized** — PASS. In-scope boundaries are concrete; out-of-scope items are explicitly named (OW-1/OW-4 detectors, OW-5/OW-6 audit skills, retroactive remediation, back-filling). The relationship to future work (OW-5/OW-6 consume this interface) is clear.
- **Blind spot** — three design.md-level concerns (waiver staleness/re-review, frozen test linkage verification, code-shape detector performance model) plus three optional suggestions (disposition preference ordering, self-referential bootstrap acknowledgment, grandfathered disposition for legacy entries, downstream adoption risk acknowledgment). None are direction-fatal — all are resolvable in design.md.

**No drift detected** from the verified SYNTHESIS.md or OUTSTANDING-WORK.md. The brief faithfully translates GAP 1/OW-2 into a concrete change scope. Prior-art constraints (D3, D7, knowledge/ taxonomy, scaffold_lint.py budget-agreement precedent, YAGNI deferrals) are explicitly honored. No existing spec conflicts.

### Verdict

**PASS — direction is sound; ready to advance to design.md.** The 🟡 items are design.md-resolution concerns, not blocking issues at the explore altitude.

## Round 2 — proposal.md review (premise + D10 drift) · deepseek-v4-pro · 2026-07-10

## Review Round 1 — proposal.md

### Summary

The proposal is well-formed, directionally sound, and faithfully carries forward the explore-brief's problem statement, root cause analysis, and three-leg solution. No drift from the verified brief is detected. The change's scope is appropriate and the out-of-scope boundaries are communicated (though less explicitly than in the explore-brief). The existing spec constraints — knowledge-lint detect-only posture, scaffold-sync manifest discipline, knowledge-organization taxonomy, and archive-step reconciliation — are all respected in the proposal's design decisions. Two minor ambiguities at the 🟡 level should be tightened before freezing.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **"Frozen regression test" disposition is under-specified relative to the explore-brief.** The proposal (line 20) says "a **frozen regression test** linkage" without clarifying what "frozen" means. The explore-brief (line 60) clarifies: "frozen regression tests (pytest, exists today; the ratchet just records the linkage)." A naive reader could interpret "frozen" as "the test becomes immutable" — when the actual intent is "the ledger records a permanent pointer to an existing test, and the lint verifies the test file still exists." The proposal should be at least as explicit as the explore-brief on this point, otherwise the design.md author may spend cycles wrestling with a phantom "freeze" mechanism that was never intended. **Fix:** add a sentence clarifying that "frozen" means the linkage is recorded and verified, not that the test is immutable.

2. **The ratchet ledger's canonical filename is not stated.** The proposal says "New tracked ratchet ledger in `knowledge/`" (line 26) but never names the file. The prior-art-digest (line 270) notes the precedent of `knowledge/audit-log.md` and suggests `knowledge/lesson-ratchet.md` as a plausible name. Since both `knowledge_lint.py`'s CANONICAL_MAP and the `scaffold_manifest.txt` need to know the exact filename, leaving it unspecified creates an ambiguity that design.md will need to resolve. If the filename is meant to be a scaffold-design decision (like `audit-log.md` was), the proposal should state the filename. If it's meant to be per-repo configurable, the proposal should say so. **Fix:** state the canonical filename or explicitly defer the naming decision to design.md with a rationale.

---

### 💡 Suggestions

1. **Add an explicit "Out of Scope" section.** The explore-brief carries a detailed out-of-scope list (OW-1/OW-4 detectors, OW-5/OW-6 audit skills, retroactive remediation, back-filling all lessons). The proposal communicates these through scattered "not built here" and "follow-on work" clauses, but a dedicated section would make the scope boundaries unambiguous to the design.md author. The template allows it — the reviewer system prompt confirms proposals "may add" Scope and Success Criteria sections. This is optional; the information is present, just distributed.

2. **Carry forward the ergonomics constraint explicitly.** The explore-brief's line 87-91 establishes a load-bearing ergonomics constraint: classification ≤3 questions, detector = 1 dropped file, waiver always available but explicit and lintable. The proposal mentions the waiver always-available property and the preference ordering, but doesn't restate the ≤3-questions and 1-dropped-file constraints. Adding them as explicit design constraints in the proposal would ensure design.md treats them as non-negotiable rather than aspirational.

3. **The "no breaking changes" claim could cite the guarding mechanism.** Line 55 says the new lint checks are "guarded on ledger existence, so repos that have not adopted the ledger yet lint clean." This is correct but could cite the existing `_check_audit_log` pattern as precedent — the same guard (skip silently when target file absent) would apply. A brief citation strengthens the claim for the reviewer and design author.

---

### Premise Verdict

```
PREMISE: AGREE
```

- **Root, not symptom:** The proposal correctly identifies the structural gap — no closure contract + no cheap enforcement slot — rather than surface symptoms like "agents don't remember lessons." ✅
- **Solution targets the root:** Three legs (closure rule + invariant framework + close-out routing) directly address both root causes. ✅
- **Scope right-sized:** The in-scope items are concrete and implementable; out-of-scope is communicated (though distributed rather than centralized). The ergonomics constraint from the explore-brief is a quality guard, not a scope item. ✅
- **Blind spot:** The "frozen regression test" verification depth — whether the lint only checks file existence or verifies the test actually exercises the class — is flagged above as 🟡 and belongs to design.md. No proposal-level blind spot that would cause rework. ✅
- **Drift (D10):** None detected. The proposal faithfully carries forward the explore-brief's problem, root cause, three-leg solution, and scope boundaries. The proposal adds implementation detail (specific knowledge_lint checks, disposition ordering, grandfathered disposition) but does not reframe the problem, switch approach, or expand scope. ✅

---

### Verdict

**PASS** — ready to freeze and move to design.md after the two 🟡 clarifications are addressed (or explicitly deferred to design.md with rationale).

**Primary disposition:** zero 🔴 + PREMISE: AGREE → frozen. Both 🟡 fixed pre-freeze (frozen-linkage semantics clarified; ledger canonically named `knowledge/ratchet-log.md`). 💡 1–3 applied (Out of Scope section, ergonomics constraints elevated to non-negotiable inputs, \_check_audit_log guard precedent cited).

## Round 3 — design.md review · deepseek-v4-pro · 2026-07-10

## Review Round 1 — design.md

### Summary

The design is well-structured, deeply grounded in the existing system (every major decision cites a precedent from `knowledge_lint.py`, `data_lint.py`, `checks.py`, or `scaffold_lint.py`), and is consistent with the frozen `proposal.md` and `explore-brief.md`. The core architecture — a registry-line ledger enforced by a guarded lint check, a subprocess-per-invariant runner mirroring `data_lint.py`'s conventions sideways, and triage routing at the two existing close-out gates — is coherent and implementable. The main issues are formatting ambiguity in the bootstrap ledger examples, a missing explicit specification of how the runner discovers files in the shared `checks/` directory, and several edge cases that could cause rework if not clarified now.

---

### 🔴 Blocking Issues

**None.** No issue I found would cause implementation to go in a wrong direction or be fundamentally unimplementable. The ones below are important clarifications that should be resolved before implementation starts but do not block basic correctness.

---

### 🟡 Should Fix

1. **D5 bootstrap entry 2 — ambiguous `·` vs ` — ` separator.** The design presents entry 2 as:
   ```
   `delegation-timeout-budget-drift` · `check:scripts/scaffold_lint.py::budget-agreement`
       · grandfathered-in as the pre-existing exemplar of lesson→check conversion.
   ```
   The defined ledger format is `<class-slug> · <disposition> — <essence>`, using ` — ` (em-dash) for the essence separator. The second `·` here looks like a ledger-format separator but is actually the design's own list-continuation formatting. The implementer will need to translate this into a correct ledger line. **Fix:** Either present the bootstrap entries in their literal ledger-line format, or add a clarifying note that the entries in D5 are *descriptions* of the entries, not the literal format. The literal format for entry 2 should be:
   ```
   - **2026-07-10** · delegation-timeout-budget-drift · check:scripts/scaffold_lint.py::budget-agreement — grandfathered-in as the pre-existing exemplar of lesson→check conversion.
   ```

2. **Runner file-discovery mechanism not fully specified.** D3 says "Mirrors `data_lint.py` sideways, same flat `checks/` directory, disjoint extension" but never states that the runner globs `checks/*.py` (the way `data_lint.py` globs `checks/*.sql` at line 247). The verification section item 1 mentions "no `checks/*.py` → exit 0" which implies a glob, but the runner's contract (§D3) should explicitly say the runner discovers check files via a `checks/*.py` glob (sorted). This matters because `data_lint.py`'s docstring explicitly documents the `*.sql` glob convention — `repo_lint.py` should do the same. **Fix:** Add a sentence to D3: "Check files are discovered via a `checks/*.py` glob (flat, no recursion, sorted filename order), the same convention as `data_lint.py`'s `checks/*.sql` glob."

3. **`knowledge/ratchet-log.md` should join `EPHEMERAL_PATHS` in `knowledge_lint.py`.** The design D2 says the ledger joins `CANONICAL_MAP`. But `knowledge/audit-log.md` is also in `EPHEMERAL_PATHS` (line 126 of `knowledge_lint.py`) because it's legitimately absent in repos that haven't adopted audit tooling. Downstream repos that haven't adopted the ratchet won't have `knowledge/ratchet-log.md` — if any prose file cites it, the `_check_broken_citations` check would flag the citation as broken. Adding `knowledge/ratchet-log.md` to `EPHEMERAL_PATHS` prevents this. **Fix:** Add a note to D2 (or D6) that `knowledge/ratchet-log.md` should also be added to `EPHEMERAL_PATHS` in `knowledge_lint.py`.

4. **`checks.py` integration path for `repo-lint` not described.** D3 describes the `checks.py` registration (trigger, config section, delegate semantics) but does not specify HOW `checks.py` invokes `repo_lint`. The existing pattern for `data-lint` (lines 905-941 in `checks.py`) is: import `data_lint.main()`, call it in-process with `--json <out_path>`, then read the JSON artifact to extract count/status. The analogous integration for `repo-lint` should be specified: import `repo_lint.main()`, call it in-process with `--json <out_path>` (and `--checks-dir` from config), read `repo_lint.json` for per-check summaries. **Fix:** Add a sentence to D3: "`checks.py` imports `repo_lint.main()` and calls it in-process with `--json` and `--checks-dir`, then reads the resulting `repo_lint.json` to extract the aggregate count and status — the same pattern used for `data-lint`."

5. **Waiver `review-by` date validation depth is unspecified.** D1 says waivers have `review-by YYYY-MM-DD` and the lint checks "date not past." But what about malformed dates (`2026-13-01`, `not-a-date`)? Should the lint also validate date format, or just compare? The `_check_audit_log` precedent uses a regex for full line validation. The `_check_ratchet_log` check should similarly validate the date format (ISO 8601 YYYY-MM-DD, valid calendar date). **Fix:** Clarify in D1 or D2: "The waiver review-by date must be a valid ISO 8601 date (YYYY-MM-DD) and not in the past; malformed dates are lint-flagged."

6. **`open` age threshold of 30 days is hardcoded vs the `_check_untriaged_age` configurable precedent.** D1 says `open` entries older than 30 days are flagged. D2 names the precedent as `_check_untriaged_age`, which uses a *configurable* `untriaged_max_age_days` (default 14, from `checks.toml`). The design is free to hardcode 30 days, but citing the configurable precedent while making the threshold non-configurable creates a mild inconsistency. **Fix:** Either (a) accept the hardcoded 30 days and remove the `_check_untriaged_age` precedent citation (use a different supporting argument), or (b) make the threshold configurable via `[knowledge_lint]` in `checks.toml` with a default of 30.

7. **Verification item 6 "Real-output eyeball" — the seeded invariant is psc-monitor's fetchall shape, which doesn't exist in the scaffold repo.** The verification scenario describes planting "one seeded real invariant (the fetchall shape)" over a synthetic offending file. But the fetchall detector is a psc-monitor check — it won't be in the scaffold's own `checks/` directory. For the verify phase, the orchestrator would need to either (a) write a minimal synthetic invariant, or (b) accept that this verification is downstream-only. **Fix:** Replace "the fetchall shape" with "a synthetic invariant (e.g., a script that detects `os.system()` calls as a toy invariant)" to make the verify step self-contained in the scaffold repo.

---

### 💡 Suggestions

1. **D5 entry 3 — `test:` pointer resolution depth.** Entry 3 uses `test:scripts/test_repo_lint.py` (no `::<name>`). D1 says without `::<name>`, only file existence is verified. For a test suite file, this is a weak check — the file could exist but contain no test functions. Consider recommending that `test:` pointers always include at least one `::<name>` (a specific test function) to ensure the test is actually present and named, not just the file. This is optional but would strengthen the pointer verification.

2. **D3 "why subprocess-per-check" rationale mentions "`data_lint`'s `conn.interrupt()` trick has no generic equivalent."** This references the SQLite backend's `threading.Timer` → `conn.interrupt()` mechanism. Since the subprocess model uses OS-level timeout (via `subprocess.run(timeout=N)`), the connection-interrupt comparison is slightly confusing — the timeout mechanism is different. Consider rephrasing: "hard timeout enforcement via `subprocess.run(timeout=N)` is universal across all check shapes, unlike `data_lint.py`'s in-process timeout which requires backend-specific interrupt mechanisms (`threading.Timer` → `conn.interrupt()` for SQLite, PGOPTIONS for Postgres)."

3. **D4's AGENTS.md bullet placement — verify the span-merge anchor still works.** D4 says to add a bullet "in Working process" citing the `finding-closure-ratchet` capability spec. The `AGENTS.md` has a span-replace contract (between `## Roles` and `## After reading this file`). The `## Working process` section is within this span. Adding a bullet there is correct and will propagate. But the implementer should verify the new bullet doesn't cause the AGENTS.md tail separator to fail (the span-replace uses `## After reading this file` as the end anchor). **Suggestion:** add a verification item or a note that `sync_scaffold.py --check` must remain green after the AGENTS.md edit.

4. **`knowledge/README.md` taxonomy row — consider adding `ratchet-log.md` to the Reference row alongside `audit-log.md`.** The Reference row currently mentions `knowledge/reference/; knowledge/audit-log.md`. Adding `knowledge/ratchet-log.md` to the same row (rather than creating a new row) follows the precedent of "bounded one-line-per-entry registry ledgers." The design could be more explicit: "The Reference taxonomy row gains `knowledge/ratchet-log.md` alongside `audit-log.md` as a second bounded one-line-per-entry registry ledger."

---

### Premise Verdict

PREMISE: AGREE

- None — the design faithfully implements the proposal's stated direction: it defines a closure contract with five dispositions, a lint-enforced registry-line ledger, a stdlib subprocess-per-check invariant runner mirroring `data_lint.py`, and triage routing at the two existing close-out points. No scope creep, no reframing of the problem, no approach ruled out by the explore brief. D3/D7 constraints are honored throughout. The solution targets the root cause (no closure contract + no cheap invariant slot) directly.

---

### Verdict

**PASS** with 🟡 findings — ready to freeze after addressing the seven Should Fix items above. None are 🔴 blocking; the design's architecture, integration points, and precedent alignment are sound and implementable as specified.

**Primary disposition:** zero 🔴 → frozen after fixing all seven 🟡 pre-freeze (literal bootstrap ledger lines; explicit checks/*.py glob; EPHEMERAL_PATHS addition; data-lint-pattern in-process invocation via repo_lint.main(--json/--checks-dir); ISO-date validation; open-age threshold made configurable (ratchet_open_max_age_days, default 30, [knowledge_lint] table); synthetic toy invariant for the self-contained eyeball step). 💡 1/2/4 also applied; 💡 3 already covered by Verification item 5.

## Round 4 — specs review (both capability deltas) · deepseek-v4-pro · 2026-07-10

## Review Round 1 — Specs Artifacts (finding-closure-ratchet & repo-invariant-checks)

### Summary

Overall quality is high: both specs faithfully translate the design's decisions into testable requirements with well-formed WHEN/THEN scenarios. The delta-spec format is correct (`## ADDED Requirements`, `### Requirement:` / `#### Scenario:` structure, bullet-list bodies with bold `WHEN`/`THEN` keywords). Requirement-design consistency is strong — the 4+4 requirements cleanly partition the two capabilities, and I found no outright contradictions. The issues below are all addressable refinements; none is a hard blocker that would cause implementation to head in the wrong direction.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

#### 1. Ambiguous `::<name>` requirement in `establishment-pointers` spec (design D1 vs spec wording)

**Location:** `finding-closure-ratchet/spec.md`, requirement `enforcement-pointers-are-verified-live-not-declarative`, line 59:

> "a `::<name>` suffix must appear textually in the pointed-at file"

**Why it matters:** Design D1 says `test:` pointers "SHOULD" include `::<name>` — bare file paths are explicitly contemplated ("a bare file path verifies only file existence, which is weak"). But the spec's unconditional "must appear textually" could be read as requiring the suffix on every `test:` entry, which would reject bare `test:scripts/test_x.py` lines — directly contradicting D1's SHOULD (= recommended, not required). An implementer reading only the spec would build a lint check that flags bare file paths, causing false-positive noise when repos use the simpler form.

**Relevant design:** `design.md` D1 table, "frozen test" row: "file exists; `::<name>` appears in file text" (verified-live when present) and the following paragraph: "`test:` pointers SHOULD include a `::<name>` node … a bare file path verifies only file existence."

**Fix:** Clarify that verification of `::<name>` is conditional — e.g., "when a `::<name>` suffix is present, it must appear textually in the pointed-at file."

#### 2. No scenario for `grandfathered` disposition behavior

**Location:** `finding-closure-ratchet/spec.md`, requirement `ratchet-ledger-has-a-lintable-registry-format` and requirement `enforcement-pointers-are-verified-live-not-declarative`.

**Why it matters:** Design D1 says `grandfathered` gets "format only" lint verification — meaning a grandfathered entry with a dangling pointer or stale date does NOT get flagged. The spec requirement 3 correctly scopes pointer verification to `check:` and `test:` entries, but there is no scenario that demonstrates the negative case (a grandfathered line with a bogus pointer silently passes). This matters because `grandfathered` is the only disposition that interacts differently with the linter, and the spec should make the boundaries explicit.

**Fix:** Add a scenario under requirement 3 like:
> #### Scenario: grandfathered entry not checked for liveness
> - **WHEN** a ledger entry has disposition `grandfathered` and cites a path that does not exist
> - **THEN** the linter does not report a dangling-pointer finding (only format is checked)

#### 3. Close-out routing Q1/Q2 stop conditions are implicit

**Location:** `finding-closure-ratchet/spec.md`, requirement `close-out-gates-route-findings-into-the-ledger`, line 88:

> "whose output for a qualifying finding is one ledger line"

**Why it matters:** The spec says "qualifying finding" which implies Q1=yes AND Q2=yes, but the design D4 explicitly spells out the stop conditions: `Q1 no → stop (no entry)` and `Q2 no → stop (point fix suffices)`. The spec scenarios show the success path (finding → entry) but not the stop path (finding judged not-real or not-generalizable → no entry). An implementer for the archive/audit skill could miss the stop conditions and create ledger entries for noise or one-offs, diluting the ratchet.

**Fix:** Either add scenarios for the stop conditions, or explicitly state in the requirement body: "Findings judged not-real (Q1) or not-generalizable (Q2) produce no ledger entry."

#### 4. Delta specs lack `## Purpose` sections (house-style delta)

**Location:** Both spec files. The house style in `openspec/specs/` universally starts with `## Purpose`. These delta specs for new capabilities start directly with `## ADDED Requirements`.

**Why it matters:** At archive time, the archive-executor promotes these deltas into `openspec/specs/<capability>/spec.md`. If there is no Purpose section, the executor either needs to synthesize one (from the proposal/design, which adds judgment work and risk of misalignment) or the resulting main spec will lack the Purpose section that every other spec has. The proposal's `## Why` and `## What Changes` sections are the natural source material for a Purpose.

**Fix:** Add a brief `## Purpose` section to each delta spec, summarizing what the capability does and why it exists, drawing from the proposal. This ensures the archive step produces a complete spec with no synthetic gap-filling.

---

### 💡 Suggestions

#### 1. Add a positive scenario for "valid ledger entry passes lint"

Neither spec has a scenario demonstrating that a correctly-formed, live-pointer entry produces zero findings. The existing scenarios cover only the *failure* modes. A positive scenario would round out the spec and give the implementer a clear target for "what clean looks like." Example:
> #### Scenario: valid ledger entry passes without findings
> - **WHEN** a ledger entry has a valid `check:scripts/knowledge_lint.py::_check_ratchet_log` disposition and the named symbol exists in the file
> - **THEN** the linter reports no finding for that line

#### 2. `check:` pointer target enumeration in scenario vs design scope

The `finding-closure-ratchet` scenario `class closed by an enforcing check` lists "a `checks/*.py` or `checks/*.sql` invariant, or a named check in a scaffold lint script" as valid targets. The `checks/*.sql` target is outside both new capability specs — it lives in the existing `data-lint` capability (not captured as an OpenSpec spec in this repo). This isn't wrong (the lint's "file exists" check works for any extension), but it means the scenario cross-references a mechanism defined outside this change. Consider adding a brief parenthetical citing the existing `data_lint.py` convention so the dependency is explicit.

#### 3. Single-blank-line separation sometimes missing between requirements

`repo-invariant-checks/spec.md` requirement `runner-registers-as-a-delegating-check` (line 47 heading) is separated from the preceding requirement's last scenario by only one blank line (same as the scenario-to-scenario gap). The house style consistently uses one blank line between all blocks regardless of heading level, so this is technically conformant — but the visual distinction between a scenario boundary and a requirement boundary is lost when both are separated by the same single blank line. In larger specs (e.g., `scaffold-sync-mechanism`), horizontal rules (`---`) mark requirement clusters. Not needed here at only 4 requirements, but worth noting for consistency.

---

### Verdict

**PASS** — ready to freeze and move to next artifact (tasks.md), provided the 🟡 issues are addressed. None of the 🟡 items would cause implementation to go in the wrong direction — they are boundary clarifications, not structural defects. The 🔴 column is clean.

**House-style check:** Both specs conform to the delta-spec conventions (`## ADDED Requirements`, `### Requirement: <kebab-slug>`, `#### Scenario: <prose-sentence>`, bullet-list `WHEN`/`THEN` bodies). The `# capability-name` level-1 heading is correct for delta specs (differing from main specs' `## Purpose`-first style, which is expected for promotion-at-archive deltas). Prose-style scenario titles match the newer-spec house style (shared-lint-gate, premise-review-gate, etc.). ✅

**Primary disposition:** zero 🔴 → frozen after fixing all four 🟡 (conditional ::name verification wording; grandfathered no-liveness scenario; explicit Q1/Q2 stop conditions; ## Purpose sections added to both deltas) plus 💡1 (positive valid-entry scenario) and 💡2 (data_lint.py convention cited).

## Round 5 — tasks.md review · deepseek-v4-pro · 2026-07-10

## Review Round 5 — tasks.md

### Summary

The `tasks.md` is **well-structured and comprehensive**: all six design decisions (D1–D6) and all eight spec requirements (4 per capability spec) have corresponding tasks. The dependency ordering (T1→T2→T3→T4→T5→T6) is correct — the runner must exist before registration, and the green gate is last. Each task is apply-phase deterministic executor work with no verify/archive leakage. The issues below are integration-clarity gaps and one missing task detail, not structural defects; none would cause a wrong implementation direction. The most impactful finding is that **task 2.1 does not explicitly tell the implementer to update `_autodetect_defaults()`**, which is the actual mechanism that makes the auto-detect trigger work — an implementer reading only the task text could miss it.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **T2.1 — Auto-detect trigger update to `_autodetect_defaults()` not explicit.** The task says "auto-detect trigger = any `checks/*.py` present (mirror the `checks/*.sql` trigger," but never names the function that actually implements this: `_autodetect_defaults()` at line 279 of `checks.py`. The `data-lint` mirror pattern works because `has_checks` (line 284) gates on `*.sql` — the implementer must extend that logic (e.g. a second `has_py_checks` boolean or an `any(checks_dir.glob("*.py"))` check) so the `"repo-lint": ...` entry returns `True` when `.py` files exist. An implementer reading only the task text could add the registry entry with a trigger string but miss the `_autodetect_defaults` update, leaving the check permanently disabled even with `checks/*.py` present.

   **Fix:** Add to T2.1: "update `_autodetect_defaults()` to return True for `repo-lint` when `checks/*.py` exists (same function, same shape as the `*.sql` check at line 284)."

2. **T1.1 — "D3 caveat" reference is ambiguous between design.md D3 and checks.py D3.** The task says "the check-only obligation (D3 caveat verbatim from `checks.py`'s custom-check caveat)" — but `design.md` also has a decision labeled D3 (the invariant runner architecture). The distinction matters: the implementer needs the *checks.py docstring lines 67–70* caveat text, not design.md D3's architecture rationale. 

   **Fix:** Reword to: "the check-only caveat from `checks.py`'s D3 custom-checks section (lines 67–70: 'the engine cannot prevent a custom command from writing to the repo...'), adapted for check files."

3. **T4.4 — Manifest is not fully alphabetical, making "alphabetical placement" ambiguous.** The task says "alphabetical placement consistent with existing entries" but the existing `scripts/scaffold_manifest.txt` is NOT fully alphabetical (e.g., `outstanding.py` at line 43 appears before `knowledge_lint.py` at line 44, and test files have similar out-of-order entries like `test_audit_scope.py` after `test_facts.py`). An implementer who reads "alphabetical" literally would reorder existing entries, creating unnecessary diff churn, or be unsure where to insert.

   **Fix:** Either (a) state the exact insertion lines: "insert `scripts/repo_lint.py` after `scripts/outstanding.py` and `scripts/test_repo_lint.py` after `scripts/test_outstanding.py`," or (b) change to "place adjacent to the `data-lint` entries — `repo_lint.py` next to `data_lint.py`, `test_repo_lint.py` next to `test_data_lint.py`," which follows the grouping convention the manifest actually uses.

4. **T5.1 — Archive skill Step 6 insertion point not specified within the multi-paragraph step.** Step 6 ("Primary reviews, fixes, and commits") is a complex block with five sub-steps: Read back from disk, Quality check, Fix trivial issues, Lint before committing, Commit once satisfied. The task says to insert the ratchet-triage step "before the archive commit" but doesn't specify WHERE in Step 6's flow it goes — e.g., before/after the Quality check? Before/after the Lint step? The triage needs to happen before the commit, but its position relative to other review steps affects whether the lint step would catch ledger format errors the triage just introduced.

   **Fix:** Specify: "Insert as a new sub-step between 'Quality check' and 'Lint before committing' — scan notes.md/review-log.md, apply three questions, append ledger line(s), then the lint step catches any format errors."

5. **T5.3 — "Add one scope line" is too vague for an implementer.** The task says to add "one scope line" to the knowledge-drift-review skill — "the semantic pass spot-checks `ratchet-log.md` `check:`/`test:` pointers for entries whose enforcing artifact no longer exercises the recorded class." But the skill has five numbered steps and an output template. The implementer needs to know: which step? What form? The design.md D2 says this is "delegated to the existing `knowledge-drift-review` LLM pass, whose scope note gains one line telling it to spot-check ratchet pointers" — so it's an addition to Step 2 (Class B — stale claims), as a new bullet under what to scan. But the task doesn't say this.

   **Fix:** Specify: "In Step 2 (Class B — stale 'not yet built' claims), add one bullet: spot-check `knowledge/ratchet-log.md` `check:` and `test:` entries whose enforcing artifact (file/symbol) exists but no longer exercises the recorded defect class (the semantic-drift residue the deterministic liveness check cannot see)."

---

### 💡 Suggestions

1. **T3.1 — Run sequence insertion point would benefit from an explicit position.** "Register the check in the run sequence" — the implementer will insert into `collect_findings()`. Naming the position ("after `_check_audit_log` at line 944, before `_check_root_handoff_files`") costs nothing and removes a micro-decision.

2. **T3.2 — Missing test case for `ratchet_open_max_age_days` config override.** The task lists "aged `open` (and config override honored)" — but only mentions the override in the T3.1 description line. T3.2 could be more explicit: "config override `ratchet_open_max_age_days = 7` respected" as a distinct fixture case, or at minimum note that the implementer should read `_load_knowledge_lint_config` for the pattern.

3. **T2.2 — test_checks.py uses `unittest` (not pytest) and shell stubs.** The existing `test_checks.py` uses `unittest` + fake shell stubs (lines 1–8). The `repo-lint` task says "auto-enabled iff `checks/*.py` exists" — this can be tested by creating a scratch `checks/` directory with a `.py` file and running `--list`. The implementer should note the `unittest` convention, not `pytest`, when extending this file. This is obvious from reading the file but could be mentioned.

4. **T4.1 — "3-line header comment" is a brittle spec.** The task says "3-line header comment stating the format + the three literal bootstrap entries." The number of lines depends on formatting. Better: "a header comment (HTML comment or plain text) stating the registry-line format, followed by the three literal bootstrap entries."

5. **No explicit task for updating `_load_knowledge_lint_config()` return dict.** T3.1 says to read `ratchet_open_max_age_days` from `checks.toml [knowledge_lint]`. The existing `_load_knowledge_lint_config` (line 328) returns `{"untriaged_max_age_days": ..., "duplicate_scan_dirs": ...}`. The implementer will need to add `"ratchet_open_max_age_days": kl.get("ratchet_open_max_age_days", 30)` to this return dict. This is implied by T3.1 but not explicitly listed as a file change. Minor — the implementer will discover it.

---

### Premise Verdict

```
PREMISE: AGREE
```

- **Root, not symptom:** The tasks faithfully implement the closure contract + invariant framework + close-out routing from the proposal's root-cause diagnosis. ✅
- **Solution targets the root:** Every design decision (D1–D6) and all eight spec requirements are covered by concrete, ordered tasks. ✅
- **Scope right-sized:** Tasks cover only the in-scope items from the frozen proposal and design — no OW-1/OW-4 detectors, no OW-5/OW-6 skills, no downstream wiring. ✅
- **Blind spot:** The `_autodetect_defaults()` gap in T2.1 (flagged above as 🟡1) is the closest thing to a blind spot — an implementer could wire the registry entry correctly but miss the auto-detect logic update, leaving the check permanently disabled. Addressed above. ✅

---

### Verdict

**PASS** — ready to freeze and move to apply after addressing the five 🟡 issues. None are 🔴 blocking; all are integration-clarity gaps that an experienced implementer would resolve by reading the referenced source files, but the tasks should be explicit enough that an executor reading only `tasks.md` cannot miss them.

**Primary disposition:** zero 🔴 + PREMISE: AGREE → frozen after applying all five 🟡 (explicit _autodetect_defaults() update; checks.py-docstring D3-caveat disambiguation; manifest placement adjacent to data-lint siblings, no reorder; archive-skill insertion point pinned between Quality-check and Lint; drift-review Step 2 bullet spelled out) and all five 💡 (run-sequence position, config-override fixture case, unittest convention note, header-comment wording, _load_knowledge_lint_config return-dict addition).

## Pre-apply mechanical fix (validation-shape, no re-review) · primary (Opus) · 2026-07-13

`openspec validate --strict` failed on the ADDED requirement
`generalizable-findings-close-only-with-a-recorded-disposition`:
`must contain SHALL or MUST`. Root cause is **not** a missing normative verb — openspec's
parser captures a requirement's `text` as only its **first physical line**, and the SHALL sat
on line 2 ("instance) SHALL NOT be treated as closed"). Fix: reordered the opening sentence so
the normative clause ("A generalizable finding SHALL NOT be treated as closed until …") is on
line 1, with the definition of "generalizable finding" and the preference ordering moved to a
trailing sentence. **No normative content changed** — all five dispositions, the `grandfathered`
legality note, and the check > test > waiver ordering are preserved verbatim; this is a
line-wrap/validation-shape fix only, so no review round is triggered. `openspec validate
lesson-check-ratchet --strict` now exits 0.
