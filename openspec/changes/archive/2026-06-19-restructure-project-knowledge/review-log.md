
## Review Round 1 — proposal.md (deepseek openspec-reviewer)

Let me read the existing `scaffold-sync-mechanism` spec and check for any existing `knowledge-organization` spec, and also look at the AGENTS.md and STATUS.md for context.
Let me check the scaffold manifest to understand STATUS.md's current relationship with the sync mechanism.
Now I have the full picture. Let me formulate the review.

---

## Review Round 1 — proposal.md

### Summary

The proposal identifies a real, well-articulated problem (knowledge rotten by directory sprawl with no organizing principle) and lays out an ambitious but coherent vision for fixing it. The Deletion flags section is exemplary — clear, quantitative, and sign-off-ready. The capability identification (`knowledge-organization` new, `scaffold-sync-mechanism` modified) is correct and maps to existing specs. However, the proposal has a **direct scope contradiction with the explore-brief** (migration in scope vs. out), is silent on a directory shown in the proposed structure, and leaves the `STATUS.md` move's interaction with scaffold-managed-file semantics underspecified. These are the kind of ambiguities that would cause the implementer to guess — and guessing wrong on a multi-repo restructure means rework across three repos.

---

### 🔴 Blocking Issues

1. **Scope contradiction: migration in proposal vs. out in explore-brief.** The explore-brief's Out of Scope says explicitly: "Propagating the restructure to extrends or psc-monitor (separate follow-on change)." But the proposal includes change #7 ("Apply it to the live repos. extrends is migrated first… psc-monitor…"), the Impact section says "Three repos," and the Deletion flags section analyzes extrends and psc-monitor content at depth. The proposal is a later artifact and CAN refine explore-brief scope — but it must **acknowledge the scope expansion** and explain why it changed, or the implementer will be confused about whether migration is part of this change or a separate follow-on. As written, an implementer reading both documents gets contradictory instructions.

2. **`STATUS.md` move is underspecified wrt scaffold sync.** `STATUS.md` is currently at the repo root and is **excluded** from the scaffold manifest (per `manifest-excludes-volatile-state`). The proposal says it moves into `memory/` with a note: "BREAKING (path rename; every reference and the sync machinery must follow)." But there are two distinct questions the proposal doesn't answer: (a) Does `memory/STATUS.md` **remain excluded** from scaffold management (i.e., stays per-repo volatile state, only its path changes), or does the move change its sync status? (b) The "sync machinery" that "must follow" — is this `status_lint.py` (which validates `STATUS.md` at root), or the sync `--check` exclusion logic, or both? The implementer needs to know which tools need updating and whether the manifest exclusion rule changes. A wrong assumption here breaks either the lint or causes `STATUS.md` to be overwritten by sync in downstream repos.

3. **`lessons/` directory: proposed structure shows it, proposal is silent.** The explore-brief's Proposed Structure diagram includes `memory/lessons/INDEX.md` and `memory/lessons/<lesson>.md`. The explore-brief also lists "Does `lessons/` earn its directory?" as an unresolved Open Question (#1). The proposal's "What Changes" #2 enumerates the new structure (`memory/decisions/`, `memory/questions/`, `memory/roadmap.md`) but says **nothing** about `memory/lessons/` — not whether it's created, deferred, or folded into another directory. The design step will have to guess whether this directory exists. If it should exist, the proposal should say so; if the open question is resolved as "no," the proposal should say that and explain where lessons content goes instead.

4. **`plans/` dissolution described as scaffold action but `plans/` doesn't exist in scaffold.** The proposal says "`plans/` dissolved into the right homes by type" under What Changes #2. But `plans/` does not exist in the scaffold repo (confirmed by glob). The `plans/` directory and its 13 files exist in **extrends**, not scaffold. If this is a downstream migration step, it should be located under change #7 (migration), not under the scaffold restructuring (#2). Mixing scaffold actions with downstream migration steps in the same bullet creates confusion about what happens where and in what order.

---

### 🟡 Should Fix

5. **Transformation disposition is implicit; only deletions are flagged.** The Deletion flags section is thorough for files being removed, but the proposal doesn't explicitly state the disposition of files being **transformed** (not deleted): `ai-docs/decisions.md`, `ai-docs/open-questions.md`, `ai-docs/parked-follow-ons.md`, `ai-docs/improvement-roadmap.md`. Are all entries in `decisions.md` guaranteed to be captured in the new INDEX.md? Is any content lost in the open-questions split? An explicit "Transformations" or "Migration" subsection stating "no decision/question/lesson content is lost; every entry maps to the new structure" would close a review gap.

6. **`fast-track-workflow.md` removal doesn't state where the replacement lives.** The proposal says the file is removed because "the autonomy override is a one-sentence spoken instruction, not a tracked file." But the file's purpose is coordination — any agent seeing it knows fast-track is active. If this is now purely an operator oral instruction, the proposal should state that explicitly, so future agents don't wonder whether they missed a config. Alternatively, if it's captured in `openspec/config.yaml` somewhere, say so.

7. **`plans/` dissolution homes are vague.** "product strategy/vision → project identity" — what file? `AGENTS.md`? A new `memory/identity.md`? Also "hard-won research preserved in a dedicated research home" — what directory? The explore-brief's Proposed Structure shows no research directory. If the answer is `openspec/changes/archive/` (per the explore-brief's "What Dies" table which says `ai-docs/archive/` content is "archived into openspec archive (research files)"), the proposal should name it.

---

### 💡 Suggestions

8. The "What Changes" section describes `ai-docs/` → `memory/` with a BREAKING note. It would help the implementer to enumerate the exact files whose internal path references need updating: `scripts/status_lint.py`, both `archive-executor.md` bodies, `sync_scaffold.py`, `openspec/config.yaml`'s rules.archive block, `AGENTS.md`, and all skill files that reference `ai-docs/`. Explicit is better than "every reference."

9. Consider adding a "What's Created" table alongside the Deletion flags, listing every new file/directory as a checklist for the implementer. The explore-brief has a Proposed Structure tree but the proposal doesn't.

10. The `knowledge-organization` capability description includes implementation detail ("the registry/growth-trigger rule (when an append-only file must become an indexed directory)"). This is a design-level mechanism, not a proposal-level requirement. Consider stating the requirement ("scalable, bounded-boot-load knowledge storage") and leaving the registry mechanism to design.md.

---

### Verdict

**NEEDS REVISION** — address 🔴 issues 1–4 before proceeding to design.md. Issues 1 (scope contradiction) and 2 (STATUS.md sync semantics) are the most likely to cause implementation rework if left unresolved.

## Review Round 2 — proposal.md (deepseek openspec-reviewer) — PASS

Let me read the relevant specs for context and check for any files referenced in the proposal.
Now let me check the `status_lint.py` to confirm it references `ai-docs/` paths that the proposal says need updating:
Now I have the complete picture. Let me issue the Round 2 review.

---

## Review Round 2 — proposal.md

### Summary

The rewrite genuinely resolves all four Round 1 blockers. The scope contradiction is addressed head-on with an explicit "supersedes the explore-brief" preamble (line 7); `STATUS.md` sync semantics are now clear ("remains per-repo volatile state… never propagated" — line 32); the `lessons/` silence is filled by a dedicated taxonomy-table row (`memory/lessons.md`, line 21); and `plans/` dissolution is correctly relocated to the migration half with an explicit "exists only downstream" qualifier (line 51). The three Should-Fix items are also addressed: transformation data-loss is explicitly denied (line 34), `fast-track-workflow.md`'s replacement is stated (line 37), and `plans/` homes are now concrete file paths.

The proposal is structurally sound and ready to freeze. I found no new 🔴 blocking issues. There are two 🟡 observations and three 💡 suggestions, none of which block progression to design.md.

---

### 🔴 Blocking Issues

None. All four Round 1 blockers are resolved.

---

### 🟡 Should Fix

1. **Taxonomy table commits `research/` to its own directory (`memory/research/`) but line 30 hedges it.**  
   Line 24 of the taxonomy table says Research lives at `memory/research/` (with an index) — a distinct physical home. But line 30 says the exact directory layout — "e.g. whether `research/` is its own directory or a section of `reference/`" — is finalized in design.md. These statements conflict: the table commits to a separate directory; the hedge implies it's still open. The designer will not know which wins. **Recommendation:** either strike the hedge (the table already decided) or downgrade the table cell to match (e.g., "`memory/research/` or `memory/reference/` § Research"). The table is declared "fixed here" (line 30), so a hedge that contradicts it is confusing.

2. **`ai-docs/archive/` directory deletion is underspecified — only `status-log.md` is named.**  
   Line 58 lists `ai-docs/archive/status-log.md` for deletion, and A6 says the parallel archive band-aid "is retired." But `ai-docs/archive/` also contains `retired-notes.md` and `workflow-harmonization-plan-2026-06.md` (confirmed by glob). The explore-brief's "What Dies" table says `retired-notes.md` is discarded, but the proposal's deletion flags don't call it out. The implementer will wonder whether the whole directory is deleted (as A6 implies) or only the explicitly-named file. **Recommendation:** extend the deletion bullet to say "`ai-docs/archive/` (directory)" with a note that `retired-notes.md` is discarded and `workflow-harmonization-plan-2026-06.md` is preserved in `memory/research/` or the openspec archive. This prevents rework when the implementer encounters the three-file directory and stops to ask.

---

### 💡 Suggestions

3. **`plans/` dissolution: "strategy/vision → project identity" is a deferred destination.**  
   Line 51 ends with "strategy/vision → project identity" and line 30 defers "whether product strategy/vision lives in a `memory/` identity doc or in AGENTS' project-context" to design.md. This is acceptable — the proposal acknowledges it's unresolved. If you want to close the loop, add a one-word hint: "strategy/vision → project identity (AGENTS.md `## Project context` or `memory/identity.md` — design.md decides)." Not required; just reduces the number of open threads design.md must resolve from scratch.

4. **`manifest-excludes-volatile-state` spec also needs path updates, not just the checker code.**  
   B2 (line 49) says the reference-checker will follow `ai-docs/`→`memory/`. The scaffold-sync-mechanism spec's `manifest-excludes-volatile-state` requirement (spec.md lines 26–27) hardcodes `STATUS.md`, `ai-docs/decisions.md`, `ai-docs/open-questions.md`, `ai-docs/improvement-roadmap.md`, and `ai-docs/archive/` — all of which change. The Impact section (line 74) says `openspec/config.yaml` references update, but doesn't explicitly say the sync-mechanism spec text itself needs updating. The implementer will catch this (updating the spec is implicit when paths change), but an explicit call-out would prevent the possibility of updating only the code and leaving the spec stale. Consider adding a note: "`scaffold-sync-mechanism` spec's exclusion list and any hardcoded `ai-docs/` paths in it."  

5. **`openspec/config.yaml` line 9 still references `ai-docs/research-fetch-convention.md`.**  
   The config.yaml `context:` block says "(full convention: ai-docs/research-fetch-convention.md)." After the restructure, this reference must point to the new location (presumably `openspec/config.yaml` § `rules.research`, since the file itself is being retired per line 39). The Impact section covers this generally ("any other `ai-docs/` references update"), but the specific target for this one reference isn't `memory/` — it's `openspec/config.yaml` itself. A design.md note to verify this one reference doesn't get blindly rewritten to `memory/` would save a bug.

---

### Verdict

**PASS** — the proposal is clean of blocking issues and ready to freeze. Move to design.md.

**Disposition:** PASS with zero blockers. The 2 Should-Fix + 3 Suggestions (research-home table/hedge consistency, ai-docs/archive whole-dir disposition, strategy/vision hint, sync-mechanism spec text path updates, config.yaml context-block pointer) were all folded into the frozen proposal as path-precision polish — no re-review required (non-blocking).

## Review Round 3 — specs (deepseek openspec-reviewer) — NEEDS REVISION

Let me also check for any existing specs and the design.md for full context.
Now let me also quickly verify whether there's a `design.md` for this change (the freeze order is proposal → design → tasks, and I need to know what phase we're in).
---

## Review Round 3 — specs (knowledge-organization NEW, scaffold-sync-mechanism DELTA)

### Summary

The two specs are substantively solid — they faithfully encode the proposal's taxonomy, classification rule, scalability contract, single-archive mandate, and config-rules propagation. Every requirement is normative and testable, and every requirement has at least one `#### Scenario`. The delta accurately preserves the original `manifest-declares-shared-files` requirement text word-for-word while correctly rewriting the `manifest-excludes-volatile-state` scenario to `memory/` paths. The new `config-rules-block-propagates` requirement is well-specified with four scenarios covering replace, preserve, idempotency, and drift.

There are **two 🔴 blocking issues**: the first is a conflict between the new `config-rules-block-propagates` requirement and the existing `sync-script-copies-files` byte-identical-copy rule for `openspec/config.yaml`; the second is that the `knowledge-organization` spec omits a "home" for `memory/reference/`'s content coverage that the proposal explicitly calls out. There are also 🟡 items around unstated precedent for special-file sync handling and a removed example in the delta's non-target scenario.

---

### 🔴 Blocking Issues

1. **`config-rules-block-propagates` contradicts the existing `sync-script-copies-files` byte-identical-copy rule — no carve-out.**  
   - **Location:** delta spec lines 40–47 (`config-rules-block-propagates`) vs. original spec lines 47–55 (`sync-script-copies-files`, which is NOT modified in the delta).  
   - **Why it blocks:** The original `sync-script-copies-files` requirement states that every manifest-listed file is copied **byte-identical** to the scaffold source, with AGENTS.md as the **sole** carved-out exception (span-replace). `openspec/config.yaml` is manifest-listed (it is not in the exclusion list in either the original or the MODIFIED `manifest-excludes-volatile-state` scenario). The new `config-rules-block-propagates` requirement says the sync SHALL do a *partial* replacement (replace `rules:` block, preserve `context:` block) — which is **not** byte-identical copy. An implementer reading the frozen spec will face a direct contradiction: is `openspec/config.yaml` byte-identical copied (per the unmodified `sync-script-copies-files`) or partially synced (per `config-rules-block-propagates`)?  
   - **What needs to happen:** The delta must either (a) also MODIFY `sync-script-copies-files` to add `openspec/config.yaml` as a second special case alongside AGENTS.md, or (b) add a precedence clause in `config-rules-block-propagates` stating it takes precedence over byte-identical copy for this file. The AGENTS.md precedent already establishes the pattern of carving out special files — this just needs to be stated explicitly.

2. **`knowledge-organization` spec is silent on `memory/reference/` content — the proposal explicitly names it.**  
   - **Location:** proposal taxonomy table row 5 (Reference: "Durable facts not in the code (runbook, external-API semantics, empirical findings)") vs. spec requirement `each-knowledge-type-has-one-home` (lines 15–17).  
   - **Why it blocks:** The proposal defines Reference as covering "durable facts not in the code" with explicit examples: "runbook, external-API semantics, empirical findings." The spec says "reference (durable facts not in code) → `memory/reference/`" with no elaboration. This matters because the Deletion flags section of the proposal calls out psc-monitor content that must be rescued into `memory/reference/`: "empirical company-data findings, market/regulatory facts, two unbuilt feature specs, Stripe integration semantics incl. an apparently-unfixed billing bug." An implementer relying only on the spec won't know that `memory/reference/` is the intended destination for empirical findings and external-API semantics — they might file these elsewhere (e.g., `memory/research/`, `memory/lessons.md`). The spec should enumerate the content types that belong under Reference, as the proposal does for every other home. Without this, the implementer will need to cross-reference the proposal during the migration — defeating the purpose of a self-contained spec.

---

### 🟡 Should Fix

3. **Delta silently removes the `ai-docs/opencode-delegation-notes.md` example from `manifest-lists-only-existing-scaffold-files` scenario.**  
   - **Location:** delta spec line 35–36 vs. original spec lines 42–43.  
   - **Why it matters:** The review brief explicitly states "only the manifest-excludes-volatile-state scenario should change." The `manifest-lists-only-existing-scaffold-files` scenario in the delta drops the parenthetical example `(e.g. ai-docs/opencode-delegation-notes.md)`. While the example is non-normative and now stale (the file no longer lives at that path post-restructure), the change is a deviation from the stated delta scope. The implementer or future reviewer comparing the original to the delta will notice a diff in a scenario that wasn't supposed to change — causing a "did I miss something?" moment. **Recommendation:** either restore the example updated to its new path (if the file still exists at a `memory/` path), or add a brief note explaining the removal.

4. **`knowledge-organization` spec doesn't encode the "on-demand" load discipline for non-boot types.**  
   - **Location:** proposal capability description says the spec covers "the boot-vs-on-demand loading discipline"; spec requirement 3 covers boot but the rest is implicit.  
   - **Why it matters:** The proposal's taxonomy table has a "Load" column assigning every type: boot (State), split (Questions), on-demand (Decisions, Lessons, Reference, Research, Roadmap, Contracts), search-only (History), phase-entry (Rules). The spec's requirement 3 only covers the three boot files. The fact that Decisions, Lessons, Reference, Research, Roadmap, and Contracts are **on-demand only** (never loaded at boot) is implicit from "boot set is minimal" — but the proposal explicitly lists this as a capability deliverable. An implementer building a new tool that scans knowledge files (or an agent bootstrapping) won't find the load contract for non-boot types in the spec. **Recommendation:** add a short requirement or scenario stating that all knowledge types not listed as boot SHALL be loaded on-demand, with History as search-only and Rules as phase-entry.

5. **`archive-step-reconciles-into-new-structure` (knowledge-organization requirement 7) has only one thin scenario — doesn't cover the full reconciliation flow.**  
   - **Location:** spec lines 72–77.  
   - **Why it matters:** The scenario says the archive step SHALL update `memory/STATUS.md`, append to `memory/decisions/INDEX.md`, and reconcile `memory/questions/`. But the proposal's B2 says the archive step must also handle the horizon-split (active vs. parked questions), the STATUS.md cap rule (at most 3 recent changes), the open-questions.md horizon-split rule (BLOCKING items stay; non-BLOCKING park), and the decisions entry format (Date + Status header, ≤300 words). The single scenario doesn't cover: what happens to questions that are neither Active nor Parked (resolved → `retired-notes.md`?), what the STATUS.md prune rule is, or that the decisions entry format must be preserved. The proposal has extensive rules for these (from AGENTS.md standing rules), but the spec doesn't encode them. **Recommendation:** add one or two scenarios covering the decisions entry format and the questions horizon-split.

---

### 💡 Suggestions

6. **`knowledge-organization` requirement 1's first scenario (`code-derivable-doc-not-stored`) could be stronger with an example.**  
   The scenario says "a document only describes code structure, schema, call flow, or behavior" — but the proposal gives a concrete example: extrends `docs/` (~2,191 lines) which is safe to delete because every file is auto-generated code description. Adding a brief parenthetical example would make the scenario immediately grokkable for an implementer who hasn't memorized the proposal.

7. **`knowledge-organization` requirement 4's `growth-trigger-splits-file` scenario references a "defined size bound" that doesn't exist anywhere in the spec.**  
   The scenario says "WHEN a tracked knowledge file crosses its defined size bound" — but no bound is defined in the spec, the proposal, or the explore-brief. The proposal says the mechanism is design.md's job, which is fine for deferring the *value*, but the spec should either define the bound or explicitly state it's defined elsewhere (e.g., in the archive skill). An implementer reading this in isolation will ask "what bound?"

8. **`config-rules-block-propagates` doesn't specify whether `openspec/config.yaml` must be listed in `scaffold_manifest.txt`.**  
   The sync script operates on manifest-listed files. AGENTS.md is manifest-listed and gets special handling. The new requirement implies `openspec/config.yaml` also gets special handling — but the spec is silent on whether it must appear in the manifest to trigger that handling, or whether the sync script discovers it by convention. Adding a brief scenario like "WHEN `openspec/config.yaml` is listed in the manifest" would close this ambiguity.

---

### Verdict

**NEEDS REVISION** — address 🔴 issues 1 and 2 before proceeding. Issue 1 (config-rules vs. byte-identical-copy conflict) is the most likely to cause implementation rework — the implementer will have to guess which rule wins for `openspec/config.yaml`, and guessing wrong produces silent drift in downstream repos. Issue 2 (Reference content missing from spec) means the migration agent won't know where to put psc-monitor's empirical findings without cross-referencing the proposal. The 🟡 and 💡 items are quality polish that can be addressed in the same pass.

**Disposition:** Both 🔴 accepted and fixed — (1) MODIFIED sync-script-copies-files + check-mode-reports-drift to carve out openspec/config.yaml as a second partial-sync file alongside AGENTS.md (resolves the byte-identical conflict on both copy and check paths); (2) added reference-holds-not-in-code-facts scenario enumerating reference content. 🟡/💡 folded in: restored generalized example, added non-boot-types-load-on-demand scenario, two archive-reconciliation scenarios, size-bound-defined-by-tooling clarification, code-derivable example. Re-review mandatory.

## Review Round 4 — specs (deepseek openspec-reviewer) — PASS

Now let me read the two spec files under review, plus the existing baseline specs:
Now let me verify the scenario format by spot-checking both files for correct 4-hashtag usage:
---

## Review Round 4 — specs (knowledge-organization NEW, scaffold-sync-mechanism DELTA)

### Summary

Both Round 3 🔴 blocking issues are fully resolved. The `sync-script-copies-files` and `check-mode-reports-drift` MODIFIED requirements now explicitly carve out `openspec/config.yaml` as a second partial-sync file alongside `AGENTS.md`, and the `config-rules-block-propagates` requirement includes a precedence clause resolving the former contradiction — there is no remaining ambiguity. The `knowledge-organization` spec now enumerates reference content types via the new `reference-holds-not-in-code-facts` scenario, covering runbook facts, external-API semantics, empirical findings, and unbuilt-work specs — matching the proposal's psc-monitor rescue instructions. The MODIFIED requirement text is faithfully preserved from the original (augmented, not rewritten), and the new scenarios are correct and consistent.

The Round 3 🟡/💡 items are also addressed: the stale `ai-docs/opencode-delegation-notes.md` example is generalized, the `non-boot-types-load-on-demand` scenario is added, the `questions-horizon-split-on-archive` and `decisions-index-entry-points-to-archive` archive-reconciliation scenarios are present, the size bound is explicitly deferred to tooling, the manifest-listing statement for `openspec/config.yaml` is explicit, and the code-derivable scenario includes an example. All scenarios use `####` (4-hashtag) format.

I found no new 🔴 blocking issues. There is one 🟡 observation and one 💡 suggestion, neither of which blocks progression.

---

### 🔴 Blocking Issues

None. Both Round 3 blockers are resolved.

---

### 🟡 Should Fix

1. **The MODIFIED `sync-script-copies-files` scenario `sync-copies-regular-file-byte-identical` uses "neither `AGENTS.md` nor `openspec/config.yaml`" — but the original scenario text has been silently rewritten rather than augmented.**  
   - **Location:** delta spec line 52 vs. original spec line 58.  
   - **Original:** `WHEN sync_scaffold.py <target> is run for a manifest-listed non-AGENTS.md file`  
   - **Delta:** `WHEN sync_scaffold.py <target> is run for a manifest-listed file that is neither AGENTS.md nor openspec/config.yaml`  
   - **Why it's 🟡 (not 🔴):** The rewrite is correct and needed — adding a second excludee to the condition is the minimal faithful change. The phrasing shift from "non-`AGENTS.md`" to "neither `AGENTS.md` nor `openspec/config.yaml`" is the natural way to express the augmented rule. A casual diff reviewer might flag the "non-`AGENTS.md`" → "neither..." change as a wording drift rather than a necessary augmentation, but the substance is identical in intent and the changed condition is exactly what the MODIFIED requirement demands. No implementer would be confused. This is a documentation-nicety observation, not a defect.

---

### 💡 Suggestions

2. **`sync-handles-config-yaml-via-rules-block-replace` (under `sync-script-copies-files`) and `rules-block-replaced` + `context-block-preserved` (under `config-rules-block-propagates`) partially duplicate each other.**  
   - **Location:** delta lines 69–73 vs. lines 134–142.  
   - Both scenario sets describe: replace `rules:` block; preserve `context:` block. The first does it as a `sync-script-copies-files` scenario, the second as standalone `config-rules-block-propagates` scenarios. The cross-reference in the requirement text ("see the `config-rules-block-propagates` requirement") ties them together, so they don't contradict — but an implementer reading both might wonder which one is authoritative. The duplication is harmless (consistent wording, no divergence), but trimming the `sync-script-copies-files` scenario to a one-liner pointing to `config-rules-block-propagates` would reduce the "wait, did I already read this?" friction. Purely a quality-of-life suggestion.

---

### Verdict

**PASS** — the two 🔴 blockers from Round 3 are resolved, no new blockers exist, and the specs are ready to freeze. Proceed to `design.md`.

**Disposition:** PASS — both Round 3 blockers resolved, no new blockers. The 1 🟡 (wording-drift observation) and 1 💡 (harmless config-scenario overlap, tied by cross-reference) are cosmetic and left as-is to preserve the faithful MODIFIED copy. Specs FROZEN.

## Review Round 5 — design.md (deepseek openspec-reviewer) — NEEDS REVISION

## Review Round 5 — design.md

### Summary

The design is **ambitious and largely coherent** — it makes defensible choices on the critical structural questions (D-B directory layout, D-C rules-last-block span, D-F hybrid decisions registry, D-G sequential migration, D-H rescue checklist). It faithfully maps to every frozen proposal commitment: taxonomy homes, config rules-block sync, single archive, migration-preserves-not-in-code, and zero content loss. The Verification section has testable acceptance criteria.

However, the design has **three 🔴 blocking issues** and **four 🟡 should-fix items** that would cause implementation confusion, rework, or silent breakage if not resolved. The 🔴 issues center on: (1) an ambiguous git-mv-vs-selective-move that makes D-G's orphan-removal paths potentially wrong; (2) `memory/README.md`'s ownership being unspecified, which conflicts with the spec's `manifest-excludes` requirement; (3) the `ai-docs/archive/` directory retirement being stated in the proposal but missing from the design's migration steps.

---

### 🔴 Blocking Issues

1. **D-G step 1 says `ai-docs/`→`memory/` as a directory rename, but step 3's orphan paths assume the old `ai-docs/` paths still exist — the implementer will do the wrong `git rm` unless step 1's selectivity is explicit.**

   - **Location:** D-G lines 78–79 ("`git mv`/transform the per-repo content (`ai-docs/`→`memory/`…)") vs. line 82 ("old `ai-docs/delegation-harness.md`, `ai-docs/fast-track-workflow.md`, `ai-docs/research-fetch-convention.md`").
   - **Why it blocks:** If step 1 does a wholesale `git mv ai-docs/ memory/`, then `delegation-harness.md`, `fast-track-workflow.md`, and `research-fetch-convention.md` move to `memory/delegation-harness.md` etc. Git no longer tracks them at `ai-docs/` paths — so `git rm ai-docs/delegation-harness.md` in step 3 fails with "pathspec did not match any files." If step 1 is meant to move ONLY knowledge files (leaving the three non-knowledge files at `ai-docs/`), the design must say so explicitly — `"ai-docs/→memory/"` reads as a wholesale directory rename. The implementer will guess and guess wrong.
   - **Fix:** Either (a) split step 1 into "selectively move knowledge files from `ai-docs/` to `memory/`" with the three orphan-bound files explicitly excluded from the move, or (b) if wholesale rename is intended, update step 3's orphan paths to `memory/delegation-harness.md` etc.

2. **`memory/README.md` ownership is a spec contradiction — it carries the universal taxonomy but the spec excludes the entire `memory/` tree from scaffold management.**

   - **Location:** D-B (tree shows `memory/README.md` as a scaffold-skeleton file), D-I (taxonomy in three places, with `memory/README.md` as the "agent-facing map"), vs. the frozen `scaffold-sync-mechanism` delta spec `manifest-excludes-volatile-state` scenario (which excludes the *entire* `memory/` tree — "`memory/STATUS.md`, the `memory/decisions/` tree, the `memory/questions/` tree, `memory/lessons.md`, `memory/roadmap.md`, the `memory/reference/` tree, and the `memory/research/` tree").
   - **Why it blocks:** The taxonomy is declared **universal** in the proposal (line 11: "a universal contract that applies to every repo") and the design enshrines it as the document "future agents can read" linked from the boot map. If `memory/README.md` is excluded from scaffold sync, every downstream repo must hand-author it — and taxonomy drift across repos is inevitable. If it IS scaffold-managed, the spec's blanket exclusion of the `memory/` tree must be amended (at minimum carving out `memory/README.md`). An implementer who follows the spec won't list it in the manifest; an implementer who follows the design will. One of them is wrong, and the implementer will have to reconcile the contradiction.
   - **Fix:** Explicitly decide: (a) add `memory/README.md` to the manifest and amend the spec's `manifest-excludes-volatile-state` to carve it out, or (b) state that `memory/README.md` is a one-time template copied during migration (not synced), with the normative taxonomy in the spec as the authoritative source and AGENTS.md as the synced pointer.

3. **The `ai-docs/archive/` directory retirement (whole-directory deletion) is in the proposal's Deletion flags but absent from D-G migration steps — the implementer won't delete it.**

   - **Location:** Proposal Deletion flags line 58 ("`ai-docs/archive/` (whole directory): retired") vs. design D-G step 3 (orphan list only: `ai-docs/delegation-harness.md`, `ai-docs/fast-track-workflow.md`, `ai-docs/research-fetch-convention.md`). Verification line 121 ("no `ai-docs/archive/status-log.md` remains") exists but doesn't specify the deletion mechanism.
   - **Why it blocks:** `ai-docs/archive/` is NOT a sync-managed file (it's excluded from the manifest per the original spec), so it won't appear as a sync orphan. D-D only addresses *stopping future writes* (dropping the prune step), not removing the existing directory. Without an explicit step in D-G's migration sequence to enumerate, preserve, and then `git rm` the `ai-docs/archive/` directory, the implementer will leave it in place — and the Verification check for its absence will fail, requiring rework. The proposal also requires selective content preservation (`workflow-harmonization-plan-2026-06.md`, research files) before deletion — D-H covers psc-monitor's `docs/` rescue but says nothing about `ai-docs/archive/` content rescue.
   - **Fix:** Add an explicit step (or sub-step within D-G step 1) covering: enumerate per-repo `ai-docs/archive/` contents, preserve substantive files (research, plans), then `git rm -r ai-docs/archive/`.

---

### 🟡 Should Fix

4. **D-D archive-executor body rewrite is too high-level — the implementer rewriting two load-bearing operational procedures from four bullet points has dangerous latitude.**

   - **Location:** D-D lines 64–68 (four bullets describing the new reconciliation).
   - **Why it matters:** The current archive-executor bodies have ~30 lines of detailed, mechanical instructions for step 3 (exact output formats, demotion rules, prune-to-status-log, `**Date:**`/`**Status:**` format, horizon-split routing, lint-reconciliation loop). D-D says "change their step-3 targets" with bullet points but doesn't specify:
     - The new `memory/STATUS.md` reconciliation output format (does the "dense-paragraph style of existing `## Latest change` entries" carry over?)
     - Whether the existing `ai-docs/decisions.md` and `ai-docs/open-questions.md` are referenced by the rewritten bodies at all (they shouldn't be — but "only the path changes" for questions is ambiguous about whether `parked-follow-ons.md` as a separate file dies)
     - The exact format of the `memory/decisions/INDEX.md` one-line entry: is it `<date> · <title> · <one-line essence> → openspec/changes/archive/<dated-change>/` as D-D states, or something machine-parseable? Does it carry `**Date:**` and `**Status:**` fields (as current decisions entries do, and as the `status_lint.py` decisions check will validate)?
   - The implementer given only D-D's four bullets will produce two executor bodies that diverge from each other and from the linter's expectations. The design should at minimum include a concrete example of each reconciliation output format.

5. **D-G convergence check (step 4) omits `--check-refs` — citation-integrity drift will go undetected.**

   - **Location:** D-G line 81 ("`sync_scaffold.py --check <repo>` and `status_lint.py <repo>` → both clean"). The Verification section likewise only lists `--check`.
   - **Why it matters:** After migration, AGENTS.md and other managed files will contain rewritten references from `ai-docs/` to `memory/`. If ANY of these references are wrong (e.g., a `memory/decisions.md` that should be `memory/decisions/INDEX.md`), `--check` won't catch it — it only verifies byte-convergence of managed files, not citation integrity. `--check-refs` is the tool that detects dangling citations. Running it post-migration would catch any path-rewrite errors before they become silent boot-context rot. The design should include `--check-refs` in the convergence step (or explain why it's excluded — e.g., the scaffold's `_AIDOC_PATH_RE` and filter functions haven't been updated to `memory/` yet, which itself would be an implementation gap).

6. **The `openspec/config.yaml` `rules.archive` sub-block references `ai-docs/` paths that must be rewritten — but the design is silent on this update.**

   - **Location:** Current `openspec/config.yaml` lines 50–51: "reconciliation of STATUS.md / ai-docs/decisions.md / ai-docs/open-questions.md" inside `rules.archive`. The proposal's Impact section line 74 says "any other `ai-docs/` references update."
   - **Why it matters:** After migration, `rules.archive` is scaffold-managed (propagated via the new config sync in D-C). If Phase 1 doesn't update these references in the scaffold's config.yaml, the next sync will propagate stale `ai-docs/` references to ALL downstream repos — and those directories won't exist. The design's Phase 1 migration plan mentions "add `rules.research` to config.yaml" and "update the `scaffold-sync-mechanism` spec text paths" but doesn't explicitly call out the `rules.archive` text rewrite. The implementer could easily miss this and leave the archive executor referencing dead paths.
   - **Recommendation:** Add a bullet to Phase 1 explicitly updating `rules.archive` and any other `rules:` sub-block text that references `ai-docs/` or root `STATUS.md`.

7. **`status_lint.py`'s new decisions check for `INDEX.md` is underspecified — the implementer doesn't know what mechanical invariants to enforce.**

   - **Location:** D-E lines 71–72: "it validates that each `INDEX.md` entry is a one-line registry entry whose pointer resolves to an existing `openspec/changes/archive/...` path OR is explicitly marked inline (no-archive case)."
   - **Why it matters:** The current decisions check has concrete invariants: parse `**Date:**`, reject missing `**Status:**`, cap words at 300 for change-record entries, skip legacy via `--since`. D-E replaces this with two checks (pointer resolution + inline marker) but says nothing about:
     - Whether `INDEX.md` entries carry `**Date:**` and `**Status:**` headers (the new one-line format doesn't fit the old header structure)
     - Whether there's a backfill-safe `--since` mechanism for old inline entries
     - What constitutes "explicitly marked inline" — a specific token like `[inline]`, or a comment convention?
   - Without these specifications, the test suite (`test_status_lint.py`) will need to be rewritten from untestable prompts. The design should define at least the minimum machine-parseable format for an INDEX.md entry.

---

### 💡 Suggestions

8. **D-G's copy-only-sync explanation could mention that `sync_scaffold.py` must be run from the scaffold repo, not the target.** The current `sync_scaffold.py` determines the scaffold root relative to its own location (`Path(__file__).resolve().parent.parent`), so it must be invoked from the scaffold checkout. A downstream migration executor running from inside the target repo would produce confusing errors. One sentence would prevent that.

9. **The Migration Plan's Phase 1 says "All scaffold tests green" but doesn't call out `test_executor_body_agreement.py` explicitly.** The Verification section does (line 116), but the Migration Plan could reinforce it — the executor-body agreement test is the canary for the risk called out in "Both executor bodies must stay byte-identical."

10. **The Open Questions "growth-trigger" bound reuse implies a growth-trigger mechanism exists — it doesn't.** The knowledge-organization spec's `growth-trigger-splits-file` scenario is forward-looking (this change doesn't implement an auto-splitter). The design's Open Question should note that the bound is *forward-looking* and not enforced by any tool in this change, to avoid the implementer building a mechanism the tasks don't call for.

11. **`_REF_SCAN_EXCLUDE` in `sync_scaffold.py` currently hardcodes `"ai-docs/archive/"` and `"docs/reviews/"` — both directories die in this restructure.** The design mentions updating the reference-checker for the `ai-docs/`→`memory/` rename but doesn't explicitly call out that the stale exclude entries should be cleaned up. A brief note in the Phase 1 update list would help.

12. **The config.yaml `rules:` block's span-replace should also handle the case where `rules:` doesn't exist in the target.** Newly-scaffolded repos (or repos that predate the `rules:` block) might not have the `rules:` key. The sync should insert it at EOF rather than aborting. The design's "aborts if a non-comment top-level key follows `rules:`" guard doesn't cover the "no `rules:` at all" case. (This may be deliberate — first sync always creates it — but worth stating explicitly.)

---

### Verdict

**NEEDS REVISION** — address 🔴 issues 1–3 before proceeding to tasks.md. Issue 1 (git-mv ambiguity → wrong orphan removal) is the most likely to cause a migration re-run across three repos — getting it wrong means downstream repos end up with stale wrong-path files that wouldn't be caught until Phase 4 convergence. Issue 2 (`memory/README.md` ownership) is a spec-design conflict that would produce contradictory implementation instructions. Issue 3 (missing `ai-docs/archive/` deletion step) would leave the dual archive partially in place, violating the single-archive requirement.

The 🟡 items (4–7) are documentation gaps that would force the implementer to guess at operator-critical reconciliation formats and linter invariants — address them in the same revision pass. The 💡 items (8–12) are quality-of-life polish.

**Disposition:** All 3 🔴 + 4 🟡 + suggestions accepted and fixed. (1) D-G step 1 now explicitly selective (knowledge files only; 3 managed files left for step-3 git rm). (2) memory/README.md made the one scaffold-managed file under memory/ — frozen scaffold-sync-mechanism delta amended to carve it out (manifest-includes-taxonomy-map). (3) D-G adds enumerate-preserve-then-rm for ai-docs/archive/. 🟡: D-D now gives concrete STATUS/INDEX/questions formats; D-E specifies machine-parseable INDEX lint format; Phase 1 rewrites rules.archive ai-docs paths + reference-checker + _REF_SCAN_EXCLUDE cleanup; convergence + Verification add --check-refs. 💡: run-from-scaffold note, append-if-absent for config rules, executor-body-agreement called out, growth-trigger marked forward-only. Re-review mandatory (covers design + amended spec).

## Review Round 6 — design.md + amended spec (deepseek openspec-reviewer) — PASS

Now let me read the spec files — both the delta and the originals:
Now let me verify one more thing — check if there are any other files I should examine for context:
## Review Round 6 — design.md (re-review) + scaffold-sync-mechanism delta reconfirmation

### Summary

All three 🔴 Round 5 blockers are **genuinely resolved**. D-G step 1 is now explicitly selective (not a wholesale `git mv`), `memory/README.md` is carved out as the one scaffold-managed file under `memory/` in both the design and the amended spec, and `ai-docs/archive/` deletion is an explicit enumerate-preserve-`git rm -r` step. The spec amendment is internally consistent: the `manifest-excludes-volatile-state` scenario enumerates excluded subtrees under `memory/` with a single named exception (`memory/README.md`), and the new `manifest-includes-taxonomy-map` scenario establishes the positive requirement — no contradiction. The MODIFIED requirement text faithfully preserves the original wording (the `manifest-declares-shared-files` and `sync-script-copies-files` requirement bodies are augmented, not rewritten; `check-mode-reports-drift` has a single new trailing sentence). All four 🟡 items from Round 5 are also addressed: D-D now gives concrete formats, D-E specifies machine-parseable INDEX lint invariants, Phase 1 explicitly rewrites `rules.archive`, and convergence/Verification both include `--check-refs`.

I found **no new 🔴 blocking issues**. There are three 🟡 items — two around migration-step specificity (the questions-file splitting transformation is implicit, and the linter scope for "non-comment list item" is underspecified) and one format-alignment note between D-D and D-E. None would cause the implementer to guess wrong; they are clarifications a careful executor would resolve by reading D-D's end-state descriptions.

---

### 🔴 Blocking Issues

None. All three Round 5 blockers are fully resolved:

1. **D-G git-mv ambiguity** → D-G step 1 now says *"**Selectively** move the per-repo **knowledge** files"*, explicitly warns *"Do NOT wholesale-rename `ai-docs/`"*, and explains *why* (the three scaffold-managed files must stay behind for step 3's `git rm`). No ambiguity remains.

2. **`memory/README.md` ownership** → The spec delta's `manifest-excludes-volatile-state` scenario (lines 15–22) enumerates excluded subtrees (`memory/STATUS.md`, `memory/decisions/` tree, etc.) and carves out *"the sole exception under `memory/` is `memory/README.md` — the universal taxonomy map — which IS scaffold-managed"*. The new `manifest-includes-taxonomy-map` scenario (lines 25–29) establishes the positive requirement. D-B (lines 42–43) and D-I (lines 98–99) both confirm it's the one synced file under `memory/`. The specification is internally consistent: a general exclusion with a single named exception.

3. **`ai-docs/archive/` deletion** → D-G step 1 now includes *"**Enumerate `ai-docs/archive/`**, preserve substantive files (research, plans) into `memory/research/` or `reference/`, then `git rm -r ai-docs/archive/`."* The deletion mechanism is explicit and sequenced (enumerate → preserve → delete).

---

### 🟡 Should Fix

1. **D-G migration step 1 hand-waves the open-questions→questions/ transformation.**
   - **Location:** D-G line 88: `open-questions.md+parked-follow-ons.md→questions/`
   - **Why it matters:** The target structure (`memory/questions/`) uses **per-item `.md` files** referenced from `INDEX.md`'s Active/Parked sections (per D-D line 77). But D-G step 1 just says to "move" these files — it doesn't say they must be **split** into individual `<item>.md` files with an `INDEX.md` pointer registry. A literal reader could `git mv open-questions.md memory/questions/INDEX.md` and `git mv parked-follow-ons.md memory/questions/` without creating the per-item structure. The D-D end-state description provides enough information for a careful executor to infer the split, but the migration is the single step where the implementer must decide how to physically transform these files — and the decision isn't stated.
   - **Recommendation:** Add a sentence like *"Each question/parked item becomes its own `<item>.md` under `memory/questions/`, with `INDEX.md`'s Active section holding blocking-item pointers and its Parked section holding non-blocking pointers."* This mirrors the detail already given for the decisions transformation (`decisions.md→decisions/INDEX.md`).

2. **D-E's "non-comment list item" scope leaves list-item detection to the implementer's imagination.**
   - **Location:** D-E line 81: *"each non-comment list item under `memory/decisions/INDEX.md`"*
   - **Why it matters:** An `INDEX.md` file will contain `## ` section headers, blank lines, preamble prose, and list items. D-E says to check "non-comment list items" — but a `## ` header is not a list item, a `- **bold date**...` bullet is, and Markdown has at least three list-item prefixes (`-`, `*`, `1.`). If the linter matches `* ` lines or numbered items, it may fire false positives on prose bullets or section content that isn't a decision entry. The implementer must guess which list-item syntax the linter should enforce.
   - **Recommendation:** Constrain to the concrete format D-D specifies: *"each line matching `^- \*\*YYYY-MM-DD\*\*` (a dash-list-item with a bolded ISO date) SHALL be a valid registry entry; all other lines are excluded from the check."* This makes the format both the input constraint and the linter's scan anchor.

3. **D-D and D-E disagree on where `[inline]` sits in the entry syntax.**
   - **Location:** D-D lines 68–76 vs. D-E line 81.
   - **D-D inline form:** `- **YYYY-MM-DD** · <slug> · [inline] <short rationale>` — `[inline]` is a **token embedded in the entry text**, replacing the `→ pointer` slot.
   - **D-E invariant description:** *"a bolded ISO date + ` · <slug> · <text>` followed by **either** a `` → `path` `` pointer … **or** an `[inline]` marker."* — `[inline]` is framed as an **alternative suffix** (like the pointer, appearing *after* the `<text>`).
   - **Why it matters:** The implementer building the linter needs a single, unambiguous format to parse. D-D's concrete example shows `[inline]` between the slug and the rationale; D-E's prose suggests it follows the `<text>`. The implementer must reconcile the two — and if they pick the wrong one, the linter will reject valid entries or accept invalid ones.
   - **Recommendation:** Reconcile D-E to match D-D's concrete format: *"a bolded ISO date + ` · <slug> · <text>` where `<text>` is either `[inline] <short rationale>` (for archiveless decisions) or `<one-line essence> → \`<archive-path>\`` (for archived decisions)."* This eliminates the ambiguity.

---

### 💡 Suggestions

4. **D-B directory tree has a formatting glitch.** Line 58 shows `changes/  changes/archive/` with a double space. Harmless but looks like a pasting artifact.

5. **The reference-checker update in Phase 1 mentions `_AIDOC_PATH_RE`→`memory/` but the `_synced_files()` function (line 261) and the section-citation filter (line 306) also hardcode `ai-docs/`.** These are implicitly covered by the general "update the reference-checker" directive, but calling them out in the Phase 1 bullet would prevent the implementer from missing them during a regex-only search-and-replace. Consider expanding the Phase 1 `sync_scaffold.py` bullet to mention the `_synced_files()` return filter and the `cited_file.startswith("ai-docs/")` guard.

6. **The verification section mentions `--check-refs` (line 128) but the earlier D-G convergence text doesn't mention what `--check-refs` tests for in the migrated repos.** After migration, AGENTS.md will cite `memory/decisions/INDEX.md`, `memory/questions/INDEX.md`, etc. `--check-refs` verifies those resolve — but only if the reference checker has been updated (per Phase 1) to scan `memory/` paths instead of `ai-docs/`. The design correctly orders Phase 1 (update the checker) before Phase 4 (run `--check-refs`), so this works — purely a suggestion to add a one-line note in D-G step 4: *"`--check-refs` verifies all `memory/` citations in synced files resolve to existing targets"* so the reader knows what signal they're getting.

---

### Spec Amendment Reconfirmation

The `scaffold-sync-mechanism` delta is **internally consistent**:

- **Exclusion + carve-out are non-contradictory.** Lines 17–22 enumerate every subtree under `memory/` that is excluded from the manifest (`STATUS.md`, `decisions/`, `questions/`, `lessons.md`, `roadmap.md`, `reference/`, `research/`). Line 22 then states the single exception: `memory/README.md`. Lines 25–29 establish the positive requirement. This is a standard pattern of "exclude X except Y" — no contradiction.

- **MODIFIED requirement text is faithfully preserved.** The `manifest-declares-shared-files` requirement body (delta lines 3–9) is **byte-identical** to the original (lines 12–18). The `sync-script-copies-files` requirement body (delta lines 47–57) preserves all original sentences and adds only the `openspec/config.yaml` partial-sync sentence plus the "only two files" clarification — neither replacing nor removing original text. The `check-mode-reports-drift` requirement body (delta lines 96–104) adds exactly one sentence to the end ("`openspec/config.yaml` SHALL likewise be compared…") — all preceding text is word-for-word preserved.

- **Scenario changes are minimal and justified.** The `manifest-excludes-volatile-state` scenario is the one intentionally rewritten (from `ai-docs/` paths to `memory/` paths), which is the purpose of the delta. The `sync-copies-regular-file-byte-identical` scenario's "non-AGENTS.md" → "neither AGENTS.md nor openspec/config.yaml" is the minimal augmentation to express the second partial-sync file. The `sync-injects-no-header` scenario adds "or openspec/config.yaml" to the parenthetical — again, minimal faithful augmentation. The `manifest-lists-only-existing-scaffold-files` scenario's example was generalized (the prior `ai-docs/opencode-delegation-notes.md` was made abstract), which was the intended fix from Round 4. No other scenario text changed.

---

### Verdict

**PASS** — ready to freeze. All Round 5 blockers are resolved, the spec amendment is internally consistent and faithfully preserves the original requirement text, and no new 🔴 issues exist. The three 🟡 items (questions-migration specificity, list-item scope, inline-format reconciliation) are implementation-clarity polish that can be addressed in a quick single-pass fix before proceeding to `tasks.md`.

**Disposition:** PASS — all 3 Round 5 blockers resolved, spec amendment reconfirmed internally consistent and faithful. The 3 🟡 (questions-split detail, INDEX lint anchor, [inline] format reconciliation) + 3 💡 (tree glitch, reference-checker _synced_files/section-guard mention, --check-refs note) folded into design as clarity polish. Design FROZEN.

## Review Round 7 — tasks.md (deepseek openspec-reviewer) — NEEDS REVISION

Now let me read the existing specs, the explore-brief, and the current scaffold code to assess the tasks against the design's requirements.
Let me read the rest of the review-log and check the current state of the scaffold code for context.
Now let me verify the scaffold codebase matches what the tasks reference — checking `sync_scaffold.py`, `status_lint.py`, `scaffold_manifest.txt`, and agent bodies.
## Review Round 7 — tasks.md

### Summary

The task list is broadly coherent with the frozen design — it sections work correctly (scaffold mechanism first, then extrends, then psc-monitor), covers all ten design decisions and four Migration Plan phases, and hits the key Verification prerequisites. However, it has **three 🔴 blocking issues**:

1. **Task 1.8 deletes load-bearing test infrastructure with no design authorization or relocation step.**
2. **Task 8.4 omits the "do NOT touch the three managed `ai-docs/` files" constraint that task 7.1 carries — the downstream `git rm` in 8.8 would fail.**
3. **Task 7.6's `ai-docs/` removal after selective migration may leave undeleted originals (`decisions.md`, `open-questions.md`, etc.) — the task doesn't state what to do with the knowledge-file originals after copying them to `memory/`.**

There are also four 🟡 issues around underspecified migration transformations, a missing `openspec validate` pre-flight, an over-broad `docs/` deletion assumption, and scope-ambiguity in the reference-checker update task.

---

### 🔴 Blocking Issues

1. **Task 1.8 would delete `docs/test/canary-non-convergence/` — load-bearing test infrastructure required by the `apply-convergence-guard` spec — with no relocation and no design authority.**

   - **Location:** Task 1.8 — "Delete scaffold `docs/` and all root `tmp_*.md` scratch files."
   - **Why it blocks:** The scaffold's `docs/` contains `docs/test/canary-non-convergence/` with `test_canary.py`, `canary_impl.py`, and `tasks.md`. This is not documentation — it is an end-to-end canary fixture that the `apply-convergence-guard` spec **requires** the repository to carry (requirement: *"The repository SHALL carry an end-to-end canary fixture..."*, scenario: *"The canary cannot be made green by editing the impl"*). The proposal's Deletion flags analyzed **only** extrends `docs/` (~2,191 lines, all code-derivable) and psc-monitor `docs/` (~6,002 lines, rescue needed). The design D-H addresses only those two repos. **Neither the proposal nor the design authorizes deleting scaffold `docs/`.** Running task 1.8 as written would remove the canary fixture, violating the `apply-convergence-guard` spec and silently breaking non-convergence-detection verification. Task 6.3 (`pytest`) may not even catch this if the canary isn't collected by default discovery.
   - **Fix:** Either (a) exclude `docs/test/` from deletion (leaving test infrastructure in place), or (b) add a pre-deletion relocation step moving `docs/test/` to a proper test location (e.g., `tests/` or `scripts/tests/`), with the `apply-convergence-guard` spec updated to reference the new path. Option (a) is simpler and doesn't touch a frozen spec.

2. **Task 8.4 omits the critical "do NOT touch the three managed `ai-docs/` files" constraint present in task 7.1 — the `git rm` in task 8.8 will fail if the executor moves those files during 8.4.**

   - **Location:** Task 8.4 ("Selectively move psc-monitor `ai-docs/` knowledge into `memory/`...") vs. Task 7.1 ("Do NOT touch the three managed `ai-docs/` files yet.") vs. Task 8.8 (`git rm ai-docs/delegation-harness.md`, etc.)
   - **Why it blocks:** This is the exact same design-level defect that was caught and fixed in Round 5 (🔴 blocker 1: *"D-G step 1 says `ai-docs/`→`memory/` as a directory rename, but step 3's orphan paths assume the old `ai-docs/` paths still exist"*). The design D-G was amended to say "Selectively move the per-repo knowledge files ... Do NOT wholesale-rename `ai-docs/`". Task 7.1 carries this constraint explicitly. Task 8.4 does not. If the apply-executor moves `ai-docs/delegation-harness.md` into `memory/` during 8.4, then 8.8's `git rm ai-docs/delegation-harness.md` will fail with `pathspec did not match any files` — the file no longer exists at that path. The executor stops and rework is required. Since psc-monitor is the last migration step, this failure would come after hours of work.
   - **Fix:** Add the explicit constraint to task 8.4: *"Do NOT touch the three managed `ai-docs/` files (`delegation-harness.md`, `fast-track-workflow.md`, `research-fetch-convention.md`) — they must stay at their `ai-docs/` paths for task 8.8's `git rm`."*

3. **Tasks 7.1/8.4 use `git mv` to migrate knowledge files but task 7.6/8.8's `git rm` of managed files assumes `ai-docs/` is otherwise empty — originals of migrated knowledge files may be left behind, blocking the directory removal.**

   - **Location:** Task 7.1 vs. 7.6, and 8.4 vs. 8.8.
   - **Why it blocks:** Tasks 7.1 and 8.4 say "selectively move `ai-docs/` knowledge into `memory/`" — if "move" means `git mv`, then `ai-docs/decisions.md`, `ai-docs/open-questions.md`, etc. no longer exist at `ai-docs/` paths. After 7.4 (delete `docs/` and `tmp_*.md`), if the only remaining files are the three managed ones, task 7.6's `git rm` of those three leaves `ai-docs/` empty → removal works. **But** if "move" means copy-then-`git rm` later, or if the executor copies content but doesn't delete originals, then `ai-docs/` still contains `decisions.md`, `open-questions.md`, `parked-follow-ons.md`, `workflow-lessons.md`, etc. after 7.1 — and 7.6 only removes the three managed files, leaving `ai-docs/` non-empty. The task says "remove the now-empty `ai-docs/`" — but it won't be empty. The executor will either error or leave stale originals. The design D-G says "selectively move" but the task doesn't specify whether originals are deleted as part of the move.
   - **Fix:** In tasks 7.1 and 8.4, state explicitly: *"After copying each knowledge file to its `memory/` destination, `git rm` the original from `ai-docs/` so that when the three managed files are removed in step 7.6/8.8, `ai-docs/` is truly empty."*

---

### 🟡 Should Fix

4. **No task for `openspec validate restructure-project-knowledge` — a design Verification prerequisite.**

   - **Location:** Design Verification line 125: "`openspec validate restructure-project-knowledge` passes; the `knowledge-organization` spec and `scaffold-sync-mechanism` delta are present."
   - **Why it matters:** Task 6.3 runs `pytest` and `ruff` but doesn't include `openspec validate`. If the delta specs have a format defect (unclosed scenario, missing requirement header), `pytest` won't catch it — the defect would surface only at archive time when the delta can't be synced to main specs. Add this as a pre-flight check before 6.3 (or fold it into 6.3). This matters because the specs went through multiple review rounds and were modified — a format drift is plausible.

5. **Tasks 7.1 and 8.4 do not specify the `open-questions.md` → per-item `.md` transformation.**

   - **Location:** Tasks 7.1, 8.4 vs. design D-G/D-D.
   - **Why it matters:** The design D-D specifies that `memory/questions/` uses **per-item `.md` files** referenced by `INDEX.md`'s Active/Parked pointers. The design D-G (amended in Round 6 🟡1) adds: *"each question/parked item becomes its own `memory/questions/<item>.md`, with `INDEX.md`'s Active section holding blocking-item pointers and its Parked section holding non-blocking pointers."* Task 1.5 for the scaffold mentions "per-item `memory/questions/<item>.md`" — but tasks 7.1 and 8.4 just say `open-questions.md+parked-follow-ons.md → questions/`. An executor reading only the task (not the design) could `git mv` the whole file into the directory without splitting, producing a structure that doesn't match the design's intent. Add the per-item split instruction to 7.1 and 8.4.

6. **Task 1.8 also deletes scaffold `tmp_*.md` files — all 13 of them — with no assessment of whether any contain not-in-code knowledge.**

   - **Location:** Task 1.8.
   - **Why it matters:** The scaffold has 13 `tmp_*.md` files (e.g., `tmp_spike1_bootcost.md`, `tmp_opt_p1_landmine.md`, `tmp_research_agent_sync.md`). The proposal's Deletion flags say `tmp_*.md` files are "deleted — re-statable, or scratch." The design D-H doesn't analyze them. The `knowledge-organization` spec's `migration-preserves-not-in-code-knowledge` requirement says content inside a directory slated for removal SHALL be relocated to its taxonomy home before deletion. Some `tmp_*.md` files may contain spike findings or research that IS not-in-code knowledge (e.g., `tmp_spike1_bootcost.md` likely contains boot-analysis findings). The task should include a review step: enumerate `tmp_*.md` files, salvage any not-in-code knowledge into `memory/research/` or `memory/reference/`, then delete the rest. Alternatively, justify in the task description why all 13 are safe to delete (they aren't — several are "spike" artifacts that by definition contain synthesized investigation).

7. **Task 6.2 (grep main spec for remaining `ai-docs/` references) implies the delta spec is incomplete — the task should verify the delta first, then update the main spec.**

   - **Location:** Task 6.2: "Grep the main `openspec/specs/scaffold-sync-mechanism/spec.md` for any remaining `ai-docs/` or root-`STATUS.md` references in requirement text outside the change delta; update them to `memory/` paths."
   - **Why it matters:** The delta spec is supposed to be the complete set of changes to the main spec. If the main spec has `ai-docs/` references the delta didn't cover, that's a delta defect that should be fixed in the delta (which is the frozen artifact), not patched in the main spec during apply. Applying a partial delta plus ad-hoc main-spec edits creates two sources of truth. The task should be: *"Verify the delta spec covers all `ai-docs/`→`memory/` path updates in scaffold-sync-mechanism; if any are missed, fix the delta spec (not the main spec — the archive step syncs the delta)."*

---

### 💡 Suggestions

8. **Section 7 and 8 tasks assume extrends/psc-monitor are locally checked out but don't state the prerequisite.** Add a preamble: *"extrends and psc-monitor must be checked out at paths provided by the operator; the apply-executor must be told these paths before starting sections 7–8."*

9. **Design Phase 4 convergence step "spot-check boot files answer one question each" has no corresponding task.** Tasks 7.8/8.10 run automated checks only. Add a brief manual-verification note to each: *"After checks pass, spot-check: AGENTS.md (~50 lines, links to `memory/README.md`), `memory/STATUS.md` (~30 lines), and `memory/questions/INDEX.md` Active section (~10 lines)."*

10. **Task 7.5/8.7 say "Run `sync_scaffold.py <extrends>` from the scaffold checkout" — the from-scaffold-checkout constraint should be stated once at the top of sections 7 and 8**, not repeated per-task. (The design notes this constraint at D-G; surfacing it at the section level avoids the executor running from inside the target repo and getting confusing errors.)

11. **Task 5.3 runs `test_executor_body_agreement.py` in isolation, but it's also part of the full suite in 6.3.** This is harmless (double-gating), but the task could note that 5.3 is a pre-check and 6.3 is the final gate.

---

### Verdict

**NEEDS REVISION** — address the three 🔴 blocking issues before the apply phase. Issue 1 (`docs/test/` deletion) can be fixed by scoping task 1.8 to exclude `docs/test/`. Issue 2 (missing constraint in 8.4) is a one-line addition. Issue 3 (knowledge-file originals) requires clarifying that `git rm` of originals happens during the migration tasks, not deferred. The 🟡 items are quality polish that will reduce executor guesswork — address them in the same pass.

**Disposition:** All 3 🔴 + 🟡 accepted/fixed. (1) scaffold docs/ holds the apply-convergence-guard canary + 2 smoke fixtures (NOT docs) — task 1.8 now RELOCATES them to tests/ then 1.9 deletes empty docs/ (spec does not hardcode the path; fixtures not synced). (2) task 8.4 now carries the do-NOT-touch-managed-files constraint. (3) all knowledge migrations now say transform-then-git-rm-original so ai-docs/ ends empty. 🟡: added 1.10 tmp_*.md salvage-before-delete; 6.3 openspec validate; 6.2 reframed to fix the DELTA not the main spec; per-item questions split in 7.1/8.4; section 7/8 prerequisites (operator paths + run-from-scaffold). 💡9 boot-file spot-check declined as a task (verify-phase judgment, lives in design Verification). Re-review mandatory.

## Review Round 8 — tasks.md (deepseek openspec-reviewer) — NEEDS REVISION

Now let me read the rest of `review-log.md` and also the frozen `design.md` and relevant specs:
Let me now check the specs and existing code that the tasks reference:
Let me verify the actual filesystem state for the canary fixtures and other referenced paths:
Let me check if the canary fixture has hardcoded paths that matter for relocation:
Let me check the orphan `ai-docs/` files that may not be covered by any task:
Now I have all the data I need. Let me emit the review.

---

## Review Round 8 — tasks.md (re-review)

### Summary

All three Round 7 🔴 blockers are substantively resolved: the canary + smoke fixtures relocate to `tests/` before `docs/` deletion (1.8→1.9); task 8.4 now carries the "do NOT touch the three managed files" constraint; and the knowledge-migration tasks (1.4–1.7, 7.1) explicitly `git rm` originals. Round 7 🟡 items (1.10 tmp-salvage, 6.3 openspec-validate, 6.2 delta-not-main-spec, per-item questions split in 7.1/8.4, section prerequisites) are all present.

However, the fix for 🔴 #3 (originals not git rm'd) introduced an oversight: by enumerating exactly which `ai-docs/` files get `git rm`'d (decisions, open-questions, parked-follow-ons, workflow-lessons, archive/), the task list makes visible that **four additional `ai-docs/` files are never handled** — but task 1.11 still declares `ai-docs/` "now-empty" and removes it. This is a new 🔴 blocking issue: the directory won't be empty, and the removal will fail.

The 🟡 issue is a specificity asymmetry between 7.1 (explicit `git rm`) and 8.4 (says "removing each original" without the `git rm` mechanism).

---

### 🔴 Blocking Issues

1. **Four scaffold `ai-docs/` root files have no disposition — `ai-docs/` won't be empty at task 1.11, so the `rmdir` will fail.**

   - **Files:** `ai-docs/improvement-roadmap.md` (41 lines, improvement roadmap), `ai-docs/explore-agent-context-infra-2026-06-18.md` (486 lines, major exploration), `ai-docs/workflow-audit-2026-06-16.md` (138 lines, audit), `ai-docs/consolidation-plan-2026-06-16.md` (223 lines, consolidation plan).
   - **Why it blocks:** Tasks 1.3–1.7 and 1.11 explicitly handle all other `ai-docs/` files (`decisions.md`, `open-questions.md`, `parked-follow-ons.md`, `workflow-lessons.md`, `archive/`, `delegation-harness.md`, `fast-track-workflow.md`, `research-fetch-convention.md`). Task 1.11 concludes with "remove the now-empty `ai-docs/`" — but these four files remain, so `ai-docs/` is NOT empty, and `git rm -r ai-docs/` or `rmdir ai-docs/` will fail (directory not empty). The executor will stop, requiring rework.
   - **Fix:** Add a task (e.g., 1.6b or folded into 1.7) that moves `improvement-roadmap.md` → `memory/roadmap.md` (populating the skeleton created in 1.2), moves the three exploration/audit files into `memory/research/` (indexed), then `git rm` each original — so `ai-docs/` genuinely empties before 1.11.

---

### 🟡 Should Fix

2. **Task 8.4 says "removing each original after transform" but doesn't explicitly say `git rm` — asymmetrical with task 7.1.**

   - **Location:** Task 8.4 vs. task 7.1.
   - **Why it matters:** Task 7.1 explicitly says "`git rm` each migrated source." Task 8.4 says "removing each original after transform" for the `decisions.md`/`open-questions.md`/`parked-follow-ons.md` migrations but omits the `git rm` mechanism. A literal executor could use plain `rm` (leaving untracked ghosts in the working tree) or `git rm` — the asymmetry creates an unnecessary decision point. The design D-G is explicit about `git rm`, so this is a phrasing fix, not a conceptual gap.
   - **Recommendation:** Add "`git rm` each migrated source" (or equivalent explicit phrasing) to 8.4, matching 7.1.

3. **Canary fixture's own `tasks.md` and the smoke READMEs contain hardcoded `docs/test/` paths that won't resolve after relocation.**

   - **Location:** Task 1.8 vs. canary `docs/test/canary-non-convergence/tasks.md` (hardcodes `docs/test/canary-non-convergence/test_canary.py`) and `docs/test/commit-gate-smoke/README.md` (hardcodes `docs/test/commit-gate-smoke/`).
   - **Why it matters:** Task 1.8 says "Confirm no live (non-archived) file references the old `docs/test/...` path" — this correctly flags the issue, but the relocation step itself doesn't explicitly say to update these internal references. The canary's `tasks.md` is the instruction file the apply-executor reads; if the pytest invocation path isn't updated during relocation, a future canary run will fail ("file not found: docs/test/canary-non-convergence/test_canary.py"). The smoke READMEs are operator procedures — less critical but would still reference dead paths.
   - **Recommendation:** Add to task 1.8: "After moving the fixtures, update any self-referential `docs/test/` paths within the moved files (the canary's `tasks.md` pytest command, smoke README procedure paths) to the new `tests/` location."

---

### 💡 Suggestions

4. **Task 1.2 creates `memory/roadmap.md` but doesn't populate it — existing `ai-docs/improvement-roadmap.md` content is lost unless covered by the new task for 🔴 #1.** This is already covered by the fix for 🔴 #1; this suggestion merely notes the connection so the fix can directly move `improvement-roadmap.md` → `memory/roadmap.md` (rather than creating an empty one then separately populating it).

5. **Task 1.8 says to drop `__pycache__`/`.pytest_cache` cruft — the `__pycache__` directory under `docs/test/canary-non-convergence/` contains `.pyc` files for multiple Python versions (3.12, 3.13).** A simple `git rm -r` or `rm -rf` of those cache dirs works but is worth explicitly noting they're not tracked (or are gitignored). Not a defect — the task already says "drop" — just a note that `git rm` won't work on untracked files.

---

### Round 7 Blocker Verification

| Round 7 🔴 | Status | Evidence |
|---|---|---|
| #1: 1.8 deletes canary fixture | **FIXED** | 1.8 now relocates 3 fixtures to `tests/`; 1.9 deletes the *empty* `docs/`. `apply-convergence-guard` spec does not hardcode the path. |
| #2: 8.4 missing managed-files constraint | **FIXED** | 8.4 now says "**Do NOT touch the three managed `ai-docs/` files** … — they stay for step 8.8." |
| #3: Migration originals not git rm'd | **FIXED** | 1.4 (`git rm ai-docs/decisions.md`), 1.5 (`git rm` both source files), 1.6 (`git rm` the original), 1.7 (`git rm -r ai-docs/archive/`), 7.1 (`git rm` each migrated source). 🟡 symmetry gap in 8.4 noted above. |

---

### Verdict

**NEEDS REVISION** — address 🔴 issue 1 before proceeding. The four orphan `ai-docs/` files (`improvement-roadmap.md`, `explore-agent-context-infra-2026-06-18.md`, `workflow-audit-2026-06-16.md`, `consolidation-plan-2026-06-16.md`) have no migration or deletion task, which means `ai-docs/` won't be empty at task 1.11 and the executor will hit a hard stop. The 🟡 items (8.4 `git rm` phrasing, fixture self-referential paths) are quality polish that can be addressed in the same pass.

**Disposition:** 🔴 (4 unhandled scaffold ai-docs files → ai-docs/ not empty) fixed: new task 1.7 routes improvement-roadmap→roadmap + 3 analysis docs→research; new 1.13 sweep guard. Robustness: extended the sweep to extrends 7.1 and psc-monitor 8.4 (catches opencode-delegation-notes.md and downstream improvement-roadmap.md — same latent wall the reviewer found in scaffold). 🟡: 8.4 now explicit git rm; 1.9 updates canary self-referential docs/test paths + rm -rf untracked caches. 💡: 1.2 no longer pre-creates roadmap.md (the 1.7 move creates it). Re-review (3rd/final reviewer pass for tasks).

## Review Round 9 — tasks.md (deepseek openspec-reviewer) — PASS

Now let me verify the actual filesystem state to confirm the four previously-unhandled files exist and that the task coverage is complete:
## Review Round 9 — tasks.md (final re-review)

### Summary

All prior rounds' issues are resolved. The Round 8 🔴 blocker (four unhandled scaffold `ai-docs/` files → directory not empty) is **genuinely fixed** — and the fix is hardened with sweep guards in all three repos. Every `ai-docs/` file across every repo has an explicit disposition in the task chain, and the sweep/gate at the end of each repo's section catches any straggler before directory removal. No new coverage gaps or ordering hazards introduced. All tasks remain deterministic, mechanical apply-phase work. This tasks.md is ready to freeze.

---

### 🔴 Blocking Issues

None.

**Round 8 blocker verification — the four previously-unhandled files:**

| File | Disposition | Task |
|---|---|---|
| `ai-docs/improvement-roadmap.md` | → `memory/roadmap.md` (git rm original) | 1.7 |
| `ai-docs/consolidation-plan-2026-06-16.md` | → `memory/research/` (indexed, git rm original) | 1.7 |
| `ai-docs/workflow-audit-2026-06-16.md` | → `memory/research/` (indexed, git rm original) | 1.7 |
| `ai-docs/explore-agent-context-infra-2026-06-18.md` | → `memory/research/` (indexed, git rm original) | 1.7 |

All four files confirmed present on disk (glob output above). Task 1.7 handles all four. ✓

**Cross-repo ai-docs/ emptiness proof — traced end-to-end:**

- **Scaffold:** tasks 1.4 (`decisions.md`), 1.5 (`open-questions.md` + `parked-follow-ons.md`), 1.6 (`workflow-lessons.md`), 1.7 (the four above), 1.8 (`archive/`), 1.12 (`delegation-harness.md` relocated, `fast-track-workflow.md` + `research-fetch-convention.md` git rm'd) → 1.13 sweep gate → remove empty `ai-docs/`. Every root `ai-docs/` file is accounted for. ✓
- **Extrends:** 7.1 (knowledge files git rm'd + sweep catches `opencode-delegation-notes.md` and downstream `improvement-roadmap.md`), 7.3 (`archive/` git rm -r), 7.6 (3 managed files git rm'd) → "now-empty `ai-docs/` should remove cleanly." ✓
- **psc-monitor:** 8.4 (knowledge files git rm'd + sweep catches `opencode-delegation-notes.md`), 8.5 (`archive/` git rm -r), 8.8 (3 managed files git rm'd) → "now-empty `ai-docs/` should remove cleanly." ✓

---

### 🟡 Should Fix

None. Two prior 🟡 items from Round 8 are verified as addressed:

1. **8.4 `git rm` phrasing** → task 8.4 now says *"git rm each original after transform"* — explicit mechanism matches 7.1. ✓
2. **Canary self-referential paths** → task 1.9 says *"Update any self-referential `docs/test/` paths inside the moved files (the canary's `tasks.md` pytest command, the smoke READMEs' procedure paths) to the new `tests/` location"* — covers all 5 `docs/test/` hits confirmed by grep. ✓

---

### 💡 Suggestions

None. The task list is complete and internally consistent.

---

### Round 8 Disposition Verification (by-line match against actual tasks.md)

| Claim in Round 8 disposition | Tasks.md evidence |
|---|---|
| "new task 1.7 routes improvement-roadmap→roadmap + 3 analysis docs→research" | 1.7 line 9: "Move scaffold `ai-docs/improvement-roadmap.md` → `memory/roadmap.md`; move the prior-consolidation analysis docs … → `memory/research/`" ✓ |
| "new 1.13 sweep guard" | 1.13 line 15: "Sweep: confirm `ai-docs/` is now empty; if any file remains, route it to its taxonomy home … and `git rm` it; then remove the empty `ai-docs/` directory" ✓ |
| "extended the sweep to extrends 7.1 and psc-monitor 8.4" | 7.1 line 54: "Then **sweep**: route any remaining `ai-docs/` knowledge file (e.g. `opencode-delegation-notes.md`) to its taxonomy home and `git rm` it"; 8.4 line 70: identical sweep ✓ |
| "8.4 now explicit git rm" | 8.4 line 70: "`git rm` each original after transform" ✓ |
| "1.9 updates canary self-referential docs/test paths" | 1.9 line 11: "Update any self-referential `docs/test/` paths inside the moved files … to the new `tests/` location" ✓ |
| "1.2 no longer pre-creates roadmap.md (the 1.7 move creates it)" | 1.2 line 4: "(`roadmap.md` is created by the move in 1.7.)" ✓ |

---

### Verdict

**PASS** — the Round 8 blocking issue is resolved, no new blockers introduced, and all three repos' `ai-docs/` directories provably empty before removal. Tasks.md is ready to freeze. Proceed to apply phase.

**Disposition:** PASS — clean (no 🔴/🟡/💡). All ai-docs/ dispositions explicit + sweep-guarded in all 3 repos. tasks.md FROZEN. All four artifacts frozen; propose phase complete.
