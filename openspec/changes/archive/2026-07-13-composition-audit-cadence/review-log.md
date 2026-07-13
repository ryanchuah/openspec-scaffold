# Review log — composition-audit-cadence

## proposal.md — Round 1 · 2026-07-11 · deepseek-v4-pro · PASS, PREMISE: AGREE, 0×🔴 3×🟡 3×💡 (all 🟡 fixed pre-freeze; 💡2 adopted, 💡1 declined — proposal kept lean, boundaries live in explore-brief; 💡3 folded into design mandate)

## Review Round 1 — proposal.md

### Summary

The proposal is a well-researched, tightly-scoped COMPLEX-tier proposal that fills a genuine structural gap in the scaffold: whole-repo instruments exist but no mechanism triggers their use, so composition review depends on operator heroics. It is faithful to the explore-brief's direction — no drift detected (consistent problem framing, identical approach, no scope expansion). The dependency on unapplied sibling changes (OW-2, OW-5) is explicitly documented and the sequencing risk is honestly acknowledged.

The most substantive concern is a **signal visibility tension** that the explore-brief identified but the proposal doesn't surface: putting the due-signal in a pull-only `outstanding` fact means it depends on operator attention — exactly the failure mode the change aims to fix. This is carried to design via the explore-brief's open question 5, but the proposal's silence on it risks design overlooking the trade-off.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **Signal visibility tension not surfaced in the proposal itself.** The explore-brief's open question 5 asks whether the staleness signal should also get a non-gating notice on a recurring surface (e.g. a `knowledge_lint` warning line), precisely because a pull-only signal depends on operator attention — the very failure mode this change addresses. The proposal describes the signal as "exposed in the pull-only `outstanding` fact snapshot" and never mentions this tension or the open question. If the proposal freezes without referencing it, design.md might proceed assuming `outstanding`-only is the settled decision and overlook the trade-off. **Fix:** Add a brief note in "What Changes" or "Impact" acknowledging that signal visibility is a design decision carried forward from the explore-brief, and that the pull-only placement has an accepted residual dependence on operator attention unless augmented by a recurring-surface notice.

2. **Dependency on unapplied contracts understates rework risk.** The Impact section says apply is "gated on OW-2's apply and ordered after OW-5's" — which is correct and honest. But it doesn't note the *what-if*: if OW-2's apply phase reveals issues that force a contract change (ledger format, triage questions, disposition taxonomy), OW-6's frozen design would need unfreezing and rework. The same pattern OW-5 used against OW-2 works *because* both sides agreed the contracts were stable — but OW-2 hasn't been exercised in apply yet. **Fix:** Add a brief risk note: "If OW-2's apply surfaces a contract change, OW-6's close-out design will need rework — the freeze boundary is the contract, not the artifact."

3. **`outstanding` fact structural delta is ambiguous.** The proposal says the fact "gains a composition-audit due-signal section (deterministic, provenance-carrying, advisory-only)." The existing `outstanding-work-view` spec R1 defines the fact as enumerating "every configured source" with `source:line` provenance. A computed trigger signal doesn't fit the "configured source" model — it's a synthetic signal, not a source. The wording "section" suggests a new top-level output block; "provenance-carrying" suggests it behaves like a source. **Fix:** Clarify in design.md whether the due-signal is: (a) a standalone section in the fact output (e.g., `composition_audit_due: {due: bool, reason: str, threshold: int, ...}`), or (b) a virtual source in the enumeration. The proposal doesn't need to resolve this — but it should flag the ambiguity so design addresses it explicitly.

---

### 💡 Suggestions

1. **Consider adding an explicit `## Scope` section.** The template says it's optional, but the scope is currently distributed across "What Changes" (bullets describe what's built) and "Impact" (files touched). A short In/Out section — even 3-4 bullet points each, cross-referencing the explore-brief's boundaries — would make the freeze boundary clearer for design.md to consume.

2. **Success criteria would strengthen the proposal.** The "Why" is clear, but explicit testable outcomes (even at headline level) would make design.md's acceptance criteria easier to derive. For example: "SC1: The `outstanding` fact exposes a boolean due-signal computed from archive counts since the last composition anchor. SC2: A plain `run-audit` tag does not reset the composition cadence clock; only a composition-anchor tag does. SC3: The composition-audit ceremony produces exactly one of three machine-discriminable verdicts." Not required — but helpful.

3. **Cross-change spec-collision handling is noted but underspecified.** The Impact section notes that both `correctness-audit-skill` and this change carry `knowledge-lint` deltas touching the same capability spec. The mitigation is "archive them in apply order and manually check for collision." Consider whether design.md should specify the exact `knowledge-lint` requirements (e.g., "audit-log line check must accept both `audit/<date>` and `audit/<date>-composition` formats") so the collision surface is visible and resolvable before either change archives — reducing the manual-check burden at archive time.

---

### Premise Verdict

```
PREMISE: AGREE
```

- **Root, not symptom** — ✅ The problem is structural: whole-repo detectors exist, a staleness signal is computed, but no mechanism connects them into an occasion. Cadence as a mechanism is genuinely missing.
- **Solution targets the root** — ✅ The three-piece solution (deterministic trigger + operator-invoked ceremony + close-out that resets the clock) directly creates the missing occasion. It reuses existing instruments rather than inventing parallel ones.
- **Scope right-sized** — ✅ In-scope: trigger, ceremony, engine plumbing. Out-of-scope: correctness audit (OW-5), auto-invocation, gates, CI wiring, enabling detectors by default. This is the minimal mechanism that closes the gap.
- **Blind spot** — The signal visibility tension: a pull-only `outstanding` fact depends on operator attention to be seen, which is the same failure mode the change addresses. The explore-brief identified this (open question 5 — non-gating recurring-surface notice) and carried it to design, but the proposal is silent on it. Not a directional fault — design can resolve it — but a material trade-off the proposal should acknowledge rather than leave implicit.

---

### Verdict

**PASS** — ready to move to design.md after addressing the 🟡 issues above. No 🔴 blockers.


## design.md — Round 1 · 2026-07-11 · deepseek-v4-pro · PASS (zero 🔴), 3×🟡 3×💡 — all 🟡 fixed pre-freeze (--include no-op clarification; orchestrator-performs-triage per OW-2 SHALL; sibling-anchor-fields relationship stated); 💡1 computed_from marker adopted; 💡2 unreachable-anchor degradation adopted; 💡3 carried to tasks.md (knowledge_lint.py:147 literal). All 9 source cites verified accurate by reviewer.

Now let me read the research digests and specs in parallel, plus start verifying the source-code claims.
Now let me verify the load-bearing source-code claims. Let me read the exact line ranges the design cites.
Now let me read the relevant existing capability specs to check for consistency.
All source-code claims verified. Now I have all the information needed for a complete review. Let me compile the findings.

---

## Review Round 1 — design.md

### Summary

The design is thorough, well-researched, and consistent with both the frozen `proposal.md` and the explore-brief direction. All nine file:line source-code claims in the Context section verified against the actual source — every one is accurate. The ten decisions (D1–D10) resolve all open questions from the explore brief and all three proposal design mandates. Integration with existing capability specs (`outstanding-work-view`, `knowledge-lint`) is backward-compatible. No unverified external-API exposures exist (stdlib + git CLI only, already a dependency). Three 🟡 clarifications would improve implementability; zero 🔴 blockers.

### 🔴 Blocking Issues

None.

### 🟡 Should Fix

1. **D5 — `--include` behavior for already-enabled checks is unspecified.** The design says `--include` treats a disabled check as enabled. What if the named check is *already* enabled in config? The most likely answer ("runs once, harmless") is trivial, but an implementer reading the design shouldn't have to guess. Add one sentence clarifying: "If the named check is already enabled, `--include` is a no-op — the check runs exactly once."

2. **D7 step 7 — ratchet triage performer not stated.** The close-out step routes findings through OW-2's frozen 3-question triage. The OW-2 ratchet contract carries a SHALL: "The triage is performed by the orchestrating agent (judgment work), never delegated to the mechanical archive-executor, and never blocks on building a detector" (`specs/finding-closure-ratchet/spec.md:113-115`). The design says the ceremony is "operator-invoked" and the close-out step is "the skill's own," but it doesn't explicitly state that the orchestrator (not a delegated model) performs the triage. Add a sentence: "Per OW-2's SHALL, the triage is performed by the orchestrating agent — judgment work, never delegated to a mechanical executor."

3. **D1/D8 — `composition_anchor`/`audit_anchor` relationship in `inventory` fact is implied but not stated.** The design says a composition anchor "automatically also counts as a general audit anchor (deliberate superset — a composition ceremony subsumes a checks report)." This is correct. But the `inventory` fact's two fields (`audit_anchor` and the new `composition_anchor`) will point at *different* tags after a composition ceremony — `audit_anchor` = `audit/2026-07-11-composition` (latest `audit/*` tag), `composition_anchor` = `audit/2026-07-11-composition` (latest `audit/*-composition` tag). After a *plain* run-audit tag, `audit_anchor` = `audit/2026-07-12` but `composition_anchor` = the older composition tag. This is correct behavior, but the relationship between the two fields is only implied by the "superset" claim. State it explicitly so the implementer doesn't mistakenly look for a `composition` field under `audit_anchor` instead of as a sibling.

### 💡 Suggestions

1. **D3 — provenance marker for the due-signal.** The existing `outstanding` fact payload carries `source:line` provenance for enumerated sources (questions INDEX, tasks.md, roadmap, TODO code). The `composition_audit` due-signal is computed from git state, not a configured source — the proposal acknowledged this tension: "a computed trigger does not fit the existing 'configured source with `source:line` provenance' model as-is." Consider adding a `computed_from: "git"` field to the `composition_audit` payload block so the signal's origin is explicit identical to how other outstanding-work items carry provenance.

2. **D3 — unreachable anchor commit degradation.** If a composition anchor tag exists but the tagged commit is no longer reachable (force-push, rebase), `git diff` and `git rev-list` against it will fail. The current design says git failure → `status: "no-git"`, `due: false`. That would mislabel this as a git absence when git is present but the anchor commit is gone. A one-line note in the design ("unreachable-anchor-commit degrades to no-anchor: count all archive dirs, same as first-run behavior") would make the degradation path explicit rather than relying on the generic git-failure catch.

3. **D2 — `knowledge_lint` regex rendering.** The design shows the regex with `\d` (line 58: `audit/\d{4}-\d{2}-\d{2}(-composition)?`). This matches the source. However, the quote of the existing regex in the Context section (line 18) uses the same `\d` notation, while the actual source uses raw string literal `\d`. This is just a rendering difference and technically correct in Python `re.compile` — no functional issue. A minor consistency note for the tasks.md implementer: the literal string to edit is on `knowledge_lint.py:147`.

### Verdict

**NEEDS REVISION** — three 🟡 items above should be resolved before freeze; none are blocking, but all three would cause the implementer to pause and interpret intent rather than execute directly.

---

**Source-code claim verification appendix (all nine pass):**

| Claim | File:line cited | Actual line | Verdict |
|---|---|---|---|
| `_mode_check` consults availability only | checks.py:1168–1198 | `_availability_for_check` at :1177; unavailable → exit 0 at :1180-1183 | ✅ Accurate |
| `--baseline` is `--report`-only | checks.py:1439 | `if args.baseline and not args.report: ... return 3` at :1439 | ✅ Accurate |
| Baseline diff is fingerprint-based | checks.py:1090 | `_baseline_diff` at :1090, uses `_fingerprint` (sha1 over check/rule/path/message) at :1081-1087 | ✅ Accurate |
| `cmd_tag` lays annotated `audit/<date>` | audit_scope.py:309–310 | `tag_name = f"audit/{args.date}"` at :310; `git tag -a` at :326 | ✅ Accurate |
| `log-line` prints registry line | audit_scope.py:363 | `print(f"- **{args.date}** · audit/{args.date} · {short_sha} · {args.essence}")` at :363 | ✅ Accurate |
| Anchor discovery = `git tag --list 'audit/*' --sort=-creatordate` | audit_scope.py:131–132 | `_latest_audit_tag` at :131-134, exact command | ✅ Accurate |
| `knowledge_lint.py` pins regex | knowledge_lint.py:147 | `_AUDIT_LOG_FULL_RE` at :147, exact pattern | ✅ Accurate |
| `outstanding` reads `[facts.outstanding]` | outstanding.py:40–51 | `_load_config` reads `config.get("facts", {}).get("outstanding", {})` at :46 | ✅ Accurate |
| `outstanding` emits JSON + MD | outstanding.py:569–607 | `run()` at :569, JSON write at :607, MD at :611 | ✅ Accurate |


## specs (3 deltas) — Round 1 · 2026-07-11 · deepseek-v4-pro · PASS (zero 🔴), 5×🟡 2×💡 — all 🟡 fixed pre-freeze (composition_anchor fields stated explicitly; already-enabled --include scenario; not-due placement scenario; K=5 spec-normative — matching one-line consistency fix disclosed in frozen design.md D7; counting wording de-ambiguated). 💡6 null-anchor scenario adopted; 💡7 declined (specs describe behavior, not code — file:line lives in design/tasks). Collision check vs lesson-check-ratchet + correctness-audit-skill deltas: clean.

## Review Round 1 — spec deltas (composition-audit, knowledge-lint, outstanding-work-view)

### Summary

The three spec deltas are well-constructed, faithful to the frozen design's D1–D10 decisions, and consistent with both the frozen `proposal.md` and `design.md`. Delta-format discipline is correct throughout (all `ADDED` requirements — no `MODIFIED` needed since none of the deltas change existing SHALL boundaries; they only add new behavior). SHALL normativity is consistently applied. All scenarios are clear WHEN/THEN. The single-normative-home discipline is strong: the `outstanding-work-view` delta explicitly cites the `composition-audit` spec and says "SHALL NOT restate them"; the ceremony contract cites the ratchet's "frozen format" without restating it; the knowledge-lint delta owns the lint-acceptance side while the composition-audit spec owns the producer side. No collision with the `correctness-audit-skill` knowledge-lint delta (different requirements, different code regions).

Five 🟡 issues — three are missing-scenario gaps, one is a spec self-containment issue, and one is a wording ambiguity. All are fixable without rethinking the design. Zero 🔴 blockers.

---

### 🔴 Blocking Issues

None.

---

### 🟡 Should Fix

1. **`composition_anchor` field shape defined only by reference to an unspec'd surface** — `composition-audit/spec.md` line 158, `composition-signal-is-surfaced-in-inventory` requirement. The spec says `composition_anchor` has "the same field shape" as `audit_anchor`. But `audit_anchor` has no formal spec — the `inventory` fact is not a spec'd capability, and its `{tag, commits_since}` shape exists only in code (`checks.py:675`). The spec should state the required fields explicitly (at minimum `tag` and `commits_since`) so the capability spec is self-contained. Not blocking — the code reference is concrete — but the spec should be the single normative home.

2. **Missing scenario for `--include` with already-enabled check** — `composition-audit/spec.md` lines 80–81, `one-shot-include-for-report-runs` requirement. The requirement text says "An already-enabled name SHALL be a no-op (the check runs exactly once)" — a correct and important edge case — but there is no scenario testing it. Three scenarios cover disabled/uninstalled/no-include, but the already-enabled branch has no coverage. An implementer reading only the scenarios could miss this boundary.

3. **Missing scenario for `not due` markdown placement** — `outstanding-work-view/spec.md` lines 12–13, `composition-audit-due-signal-block` requirement. The requirement says the `## Composition audit` section is "placed directly under the header when `due` and at the bottom otherwise." The `due-state-is-prominent` scenario tests the `due: true` case, but there is no scenario testing the `due: false` placement-at-bottom case. The MARKDOWN rendering path has two branches — both should be covered.

4. **K=5 default is ambiguously owned between spec and skill** — `composition-audit/spec.md` lines 116–117, `composition-ceremony-contract` requirement. The requirement says "default K=5, stated in the skill." This both asserts the default in the spec AND delegates the authoritative statement to the skill. If the skill later states a different default (e.g. K=3), it is ambiguous which is normative — the spec's "default K=5" or the skill's value. The spec should either (a) own the default authoritatively (remove "stated in the skill"), or (b) explicitly delegate (remove "default K=5" and say "K is configurable in the skill").

5. **Counting rule wording: "whose files were added" could be misread** — `composition-audit/spec.md` lines 11–12, `composition-cadence-trigger-semantics` requirement. The phrase "the count of distinct top-level directories under `openspec/changes/archive/` whose files were **added**" could be read as "directories where ALL their files were added" (from the singular/plural ambiguity in "whose files"). The design's computed intent (D3 — `git diff --name-only --diff-filter=A`, first path component, deduplicated) counts directories containing *at least one* added file. Clarify: "…that contain at least one file **added** in…"

---

### 💡 Suggestions

6. **Missing null-anchor scenario for `inventory.composition_anchor`** — `composition-audit/spec.md`, `composition-signal-is-surfaced-in-inventory` requirement. The solo scenario covers the case where both anchors exist and diverge after a plain tag. There is no scenario specifying the expected output when no composition anchor exists at all (presumably `{"tag": null, "commits_since": <full history count>}`). Making this explicit would remove the implementer's need to infer the null-case behavior from the "latest `audit/*-composition` tag only" prose.

7. **Knowledge-lint delta could reference the exact code location** — `knowledge-lint/spec.md`, `audit-log-registry-line-accepts-composition-anchor-variant` requirement. The design review-log notes the exact literal (`knowledge_lint.py:147`, regex `audit/\d{4}-\d{2}-\d{2}(-composition)?`). Adding a brief anchor to the spec line would make the specification more precise for the implementer without weakening the behavioral contract. Not required — the spec correctly describes behavior, not code — but the existing design artifact already has this precision.

---

### Collision check with sibling changes

- **`correctness-audit-skill` knowledge-lint delta**: adds dossier-format validation (marked `CHARTER.md`, duplicate IDs, census dispositions, missing Prior:/Class:). The composition-audit knowledge-lint delta extends the audit-log registry-line format. These touch **different requirements and different code regions** — no collision. Both deltas use `## ADDED Requirements` and will merge cleanly at archive (in apply order). The explicit format statement in this delta (lines 10–13) satisfies the proposal's mandate to "make the collision surface visible before either change archives." ✓
- **`lesson-check-ratchet` finding-closure-ratchet**: the composition-audit ceremony contract cites the "frozen format" and "3-question triage" by reference, never restating the format or disposition keywords. ✓

### D1–D10 contract consistency

All ten design decisions are faithfully represented in the spec deltas with no gaps, no scope creep, and no contradictions:
- D1 (composition anchor tag) → `composition-anchor-tag-and-log-line` ✓
- D2 (audit-log formats) → `knowledge-lint` delta ✓
- D3 (due-signal computation) → `composition-cadence-trigger-semantics` ✓
- D4 (thresholds) → same requirement, defaults stated ✓
- D5 (one-shot `--include`) → `one-shot-include-for-report-runs` ✓
- D6 (baseline pointer) → `composition-ceremony-contract` steps 3 + 7 ✓
- D7 (ceremony shape) → `composition-ceremony-contract` 7 steps ✓
- D8 (signal visibility) → `composition-signal-is-surfaced-in-inventory` + `outstanding-work-view` delta; declined recurring notice correctly absent ✓
- D9 (knowledge-drift-review outside core) → ceremony contract excludes it ✓
- D10 (skill file / manifest) → no spec requirement (correctly — file layout is implementation) ✓

---

### Verdict

**PASS** — ready to freeze after addressing the five 🟡 items above. No 🔴 blockers, no structural defects, and no collision with sibling-change contracts.


## tasks.md — Round 1 · 2026-07-11 · deepseek-v4-pro · PASS (zero 🔴), 2×🟡 3×💡 — all fixed/adopted pre-freeze (3.5 rephrased: [facts.outstanding] docstring section must be CREATED, all four keys; 4.3 gained _render_md :497/~:508 anchors; 5.1 frontmatter template cite; 5.2 exact manifest insertion point). All 12 anchors verified accurate by reviewer; full spec/AC coverage confirmed; AC7 correctly excluded as verify-phase.

Now let me read the spec deltas and the referenced source files to verify anchor accuracy.
Now let me verify the anchor accuracy against the actual source files. I'll read the key line ranges referenced in tasks.md.
Let me also check the scaffold manifest and explore brief for context.
Let me check the `_mode_multi` path and the scaffold_lint reference to verify the tasks' internal consistency.
Let me check the house skill frontmatter convention for accuracy of task 5.1 references.
Now I have enough to write the full review. Let me read a couple more things to be thorough — the `_render_md` function signature and the `findings_globs`/`finding_id_pattern` defaults in outstanding.py.
## Review Round 1 — tasks.md

### Summary

The tasks file is well-constructed, internally consistent, and faithfully maps design decisions (D1–D10) and acceptance criteria (AC1–AC6) to concrete, sequential implementation steps. All source-file line anchors are accurate against the live codebase. Every spec requirement across three capability deltas has coverage. The cite-don't-restate discipline holds throughout. Two 🟡 issues create potential implementation friction — one around an absent doc section, one around a missing function anchor — but neither blocks starting work.

### 🔴 Blocking Issues

None.

### 🟡 Should Fix

1. **Task 3.5 — `[facts.outstanding]` schema section does not currently exist in `checks.py`'s docstring.** The task says to add `composition_change_threshold` / `composition_commit_threshold` "under the `[facts.outstanding]` schema section (:23–70)." But `[facts.outstanding]` is NOT documented at :23–70 — only `[tools]` and `[checks.<name>]` appear there. The existing `[facts.outstanding]` keys (`findings_globs`, `finding_id_pattern` from `outstanding.py:28–32`) are undocumented anywhere in `checks.py`'s docstring. The implementer will discover there is no section to add "under" and must create it from scratch — including documenting the two existing keys and their defaults — before adding the two new threshold keys. This is a D4-design accuracy issue (it claims the existing keys are documented), but surfaced here as a task gap: the task undersells what the implementer actually needs to do. **Fix:** rephrase to acknowledge the section must be created, not extended, and list all four keys that need documenting.

2. **Task 4.3 — markdown rendering work references `run()` but NOT `_render_md`.** The task says "Wire the block into `run()`'s payload (:569–607) as top-level `"composition_audit"` and into the rendered markdown." The payload wiring is indeed in `run()` at :569–607, but the markdown rendering happens in `_render_md` at line 497 — a separate function with a different signature. The task provides only ONE anchor (`:569–607`) for work that spans TWO functions. The implementer grep's `_render_md` naturally, so this won't break the build, but a second anchor would make the task file a more reliable implementation contract. **Fix:** add a second anchor `(:497)` for the `_render_md` insertion.

### 💡 Suggestions

1. **Task 4.3** — Provide explicit `_render_md` anchor: the `_render_md` function starts at line 497; the `## Composition audit` section insertion-point logic (header-adjacent when `due`, bottom otherwise) needs to slot into the markdown line-building loop starting around line 508.

2. **Task 5.2** — Specify exact alphabetical insertion point: `.claude/skills/composition-audit/SKILL.md` goes between `knowledge-drift-review/SKILL.md` (line 9) and `openspec-apply-change/SKILL.md` (line 10) in the Skills section of `scripts/scaffold_manifest.txt`, not just "alphabetical placement." Saves the implementer a file scan.

3. **Task 5.1** — Could name a concrete frontmatter template: citing `.claude/skills/outstanding-work-review/SKILL.md` lines 1–9 as the canonical house-convention frontmatter eliminates any ambiguity about what "per house skill conventions" means.

### Coverage Check

| Spec Requirement | Tasks |
|---|---|
| `composition-cadence-trigger-semantics` | 4.1, 4.2, 4.3, 4.4 |
| `composition-anchor-tag-and-log-line` | 1.1, 1.2, 1.3, 1.4 |
| `one-shot-include-for-report-runs` | 3.1, 3.2, 3.4 |
| `composition-ceremony-contract` | 5.1 |
| `composition-signal-is-surfaced-in-inventory` | 3.3, 3.4 |
| `audit-log-registry-line-accepts-composition-anchor-variant` | 2.1, 2.2 |
| `composition-audit-due-signal-block` | 4.1, 4.2, 4.3, 4.4 |
| AC1–AC6 | 1.4, 2.2, 3.4, 4.4, 5.1, 5.2, 6.1 |

AC7 (behavioral end-to-end dry-run) is correctly excluded — it's a verify-phase behavioral check, not an apply-phase task.

### Anchor Accuracy

All twelve `file:line` cites verified against the live source tree. The inventory's `audit_anchor` build at `checks.py:647–676` is the correct target for the `composition_anchor` sibling. The `--include` flag should insert near `checks.py:1433` (the `--baseline` arg, with the guard mirroring `:1439`). All `audit_scope.py` anchors (:309–310, :363, :393–397, :399–401) exactly match the current source. `knowledge_lint.py:147` and `:51–54` are correct.

### Verdict

**PASS** — ready to freeze and move to apply. The two 🟡 issues are real but neither would cause rework exceeding ~5 minutes; address them for a cleaner implementation contract, but do not block on them.

---

## Verify phase (2026-07-13, Opus orchestrator)

**Tier:** COMPLEX → self-review → pro behavioral pass → flash lens pass.

**Lens selection:** test-quality / adversarial-oracle lens. Rationale: OW-6 ships four test
batteries (audit_scope, knowledge_lint, checks `--include`+inventory, outstanding due-signal)
and has NO data-path-dominant surface, so the data-scale lens does not apply.

**Self-review (orchestrator) — 3 defects found and fixed:**
- 🔴 `checks.py` `_run_inventory` composition_anchor: `commits_since` was `None` when no
  `audit/*-composition` tag exists, but spec `composition-signal-is-surfaced-in-inventory`
  scenario `no-composition-anchor-yields-null-tag` requires the **full-history count**. The
  AC4 test `test_no_composition_tag_yields_null_anchor` was also too weak (allowed
  `type(None)`). Re-delegated to a fresh deepseek apply-executor: the no-tag branch now
  computes `git rev-list --count HEAD`; the test asserts `int` == full-history count.
  `audit_anchor` left unchanged (out of scope; its own null-when-no-tag behavior — asymmetry
  recorded as a follow-on).
- 💡 `.claude/skills/composition-audit/SKILL.md` step 4: delegated a file-WRITE to the
  read-only `openspec-reviewer` (`edit: deny`). Fixed inline — the reviewer now emits the
  shortlist as text and the orchestrator writes the `pre-digest.md` checkpoint from the
  captured output (idiomatic reviewer/verifier pattern).
- 💡 `knowledge_lint.py` docstring: item-5 list indent drifted 3→4 spaces (apply-executor
  markdown-indent mangle). Fixed inline.

**Eyeball-real-output (verify step 6):** built a real tmp git repo and exercised the
due-signal at the threshold boundary, the plain-tag-does-NOT-reset regression, OR co-fire,
no-git degradation, the inventory composition_anchor (with/without tag), and the
audit_scope tag/log-line + knowledge_lint round-trip (plain/composition accepted, foreign
suffix flagged) — all conform to the spec deltas.

**Pro behavioral pass (deepseek-v4-pro):** `VERDICT: READY`, Defects: None. Independently
built a tmp git repo and confirmed every spec scenario, incl. the fixed composition_anchor
full-history count.

**Flash test-quality lens pass (deepseek-v4-flash):** `VERDICT: READY`, Defects: None. Read
all test files in full, ran the new/modified tests, and scrutinized the divergence test's
`time.sleep(1.1)` (sound — forces distinct creator dates) and the regex test coverage.

**Both multi-model gates READY, no defects. No Sonnet fallback used anywhere this session.**

**Simplicity/quality gate (read-only `/code-review`-style, 3 parallel finder subagents +
orchestrator verify-from-disk):** all findings are quality-only (no correctness defect
survived disk-verification). Dispositions:
- Fixed inline: a never-record-counts slip I introduced in this log (removed a passing test
  tally — AGENTS.md canonical rule).
- Parked to `ratchet-lint-cleanup` (behavior-preserving, propagate-later): `outstanding.py`
  duplicate `rev-list` blocks + duplicate no-git degraded-dict; `checks.py` `composition_anchor`
  ↔ `audit_anchor` shared-helper extraction (touches pre-existing out-of-scope `audit_anchor`);
  centralizing the `audit/<date>-composition` literal across the 4 modules that hardcode it;
  `audit_scope.py` `getattr(args,"kind")` defensive fallback.
- Recorded as forward-looking advisory-signal edge cases (see notes.md field 5): (a)
  `archived_changes_since` counts a pre-anchor archive dir if a NEW file is added to it after
  the anchor (impl matches the spec's literal "dir with ≥1 file added in range"; benign on an
  advisory never-gating signal; trigger violates the immutable-archive rule) — and design.md's
  counting-rule note conflates "edit" (correctly excluded) with "add"; (b) the no-anchor branch
  counts on-disk dirs via `iterdir()` (incl. untracked) while the anchored branch uses git —
  inconsistent basis, benign-advisory, transient trigger.
- Noted (no change): SKILL step 6 inlines the spec's ESCALATE indicator triple — acceptable
  runbook detail since the skill already cites the normative sequence + default K.

No fix re-delegation from the simplicity gate: the change was READY from self-review + both
independent gates, every cleanup item is behavior-preserving on certified-green code, and
parking to the designated cleanup lane matches the OW-5 precedent (fold one-liners, park
restructures). Security gate: NOT triggered (no auth/credentials/persisted-user-data/external-
network surface; git subprocess uses list-args, no shell). 

### Verify verdict: READY FOR ARCHIVE.

