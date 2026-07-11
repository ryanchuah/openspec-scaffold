# Lifecycle critique — MEDIUM & COMPLEX walkthrough (post-OW-3 shape)

Scope: defects in the WORKFLOW DEFINITION. Excludes OW-1..6 and the 5 "New findings"
(validate-at-freeze, MEDIUM validator blind spot, chain-shape prose restatement, OW-2 delta
validate fail, RENAMED unexercised). Evidence is file:line.

## Confirmed-already-efficient (credit, do not "fix")
- `_convergence.py` + apply-executor STOP:a/b/c ladder — apply's per-failure convergence is
  already fully scriptized and well-designed (apply-executor.md 33-58).
- `scaffold_lint` budget-agreement check byte-compares embedded timeouts against the harness
  §e table — budgets are single-sourced + enforced (delegation-harness.md 95-98).
- `check.sh` is a clean single-definition-of-green with graceful tool degradation.
- Explore's operational direction-gate machinery (steps 1-5) is correct and minimal; only its
  surrounding prose is bloated.
- Error paths mostly terminate cleanly at operator escalation (propose 3-pass, apply triage,
  verify 3-cycle) — no true dead-ends.

## FINDINGS (ranked)

### F1 — Every delegation hand-rolls the same grep/jq/assert post-processing; no wrapper script
- Evidence: harness §a/§b/§d; verify SKILL 95-101 + 57-73; propose SKILL 159-208; apply SKILL
  151-178; explore SKILL 36-38; AGENTS.md 186-203 (SMALL); archive SKILL 166-168.
- 6 skills each re-describe: hardened `opencode run` + timeout, grep stderr for "Falling back to
  default agent", `jq -r .part.text`, format-marker assert, EXIT-sentinel poll. All deterministic,
  all fragile (§d documents the pgrep-self-match footgun). No `scripts/` wrapper exists (confirmed).
- Fix: `scripts/opencode_delegate.py` (or oc_run.sh) runs cmd+timeout, checks fallback, extracts
  text, validates expected marker, writes {status, text, exit} to disk. Collapses dozens of prose
  lines across 6 skills into one tested script + one-line skill calls. Highest-yield scriptable.
- Confidence: HIGH.

### F2 — Phase-gate hard-STOP conflicts with AGENTS.md autonomy grant
- Evidence: AGENTS.md 156 ("autonomy is operator-told"), 163-166 ("With an explicit autonomy
  grant, self-classify and proceed") vs propose 21/290, apply 21/307, verify 134/407, archive
  14/312 ("Never invoke [next phase] without an explicit user request. This is a hard rule.").
- Under an autonomy grant an orchestrator faces contradictory instructions at every phase
  boundary. The SMALL bullet carefully scopes autonomy (185-212) but the skill phase gates make
  zero autonomy carve-out. Ambiguous + conflicting.
- Fix: one sentence in each phase gate stating the autonomy interaction (grant may auto-advance
  phases EXCEPT across a premise DISSENT / verify NEEDS-REVISION escalation), OR explicitly state
  gates are unconditional and autonomy only covers tier self-classification. Pick one, cite it.
- Confidence: HIGH.

### F3 — apply-executor re-runs the FULL suite after every task — doesn't scale in budget
- Evidence: apply-executor.md step 2 ("Run the project's tests"), step 3 ("Green → mark [x] and
  proceed"). Targeted re-run is allowed ONLY on the red/CONTINUE path (step 4).
- A COMPLEX change with 15 sub-tasks runs the full suite ~15x inside the 600s ceiling; green-path
  cadence is full-suite-per-task. Blows budget on redundant green runs; interacts badly with the
  "split across task ranges" guidance (apply SKILL 128-142).
- Fix: green path runs targeted/impacted tests per task; one full-suite run at end of the
  slice/run. Keep full-suite on red only if it aids triage.
- Confidence: HIGH.

### F4 — Verify steps 12-16 are generic-rubric bloat that duplicates stronger gates + invites
        low-precision keyword-guessing
- Evidence: verify SKILL 205-274. Step 13 re-parses `[ ]`/`[x]` (CLI already returns
  progress total/complete/remaining — apply SKILL 62). Step 13/14 "search codebase for keywords
  related to the requirement… assess if implementation likely exists" is exactly the fuzzy
  guessing the repo distrusts elsewhere. Correctness is already carried by behavioral review
  (4-8) + pro pass + simplicity/security gates.
- Fix: replace 12-16 with (a) deterministic task/spec coverage from `openspec status --json`, and
  (b) a short coherence note; lean on the behavioral+multimodel gates for correctness.
- Confidence: HIGH.

### F5 — "Self-review is a Task-tool spawn" (harness) contradicts "your own, do not delegate" (skill)
- Evidence: harness 102-107 ("Verify's in-process self-review pass (the primary agent's own
  review) is a Task-tool spawn, not opencode run") vs verify SKILL 14-16 + 171 + AGENTS.md
  ("your OWN substantive behavioral review… never delegated"). A Task-tool spawn IS a subagent =
  delegation. The two docs disagree on who performs the self-review.
- Fix: reconcile — either the self-review is the orchestrator inline (correct the harness), or it
  is a permitted same-family subagent spawn (correct the skill's "non-delegable" wording).
- Confidence: MEDIUM-HIGH.

### F6 — Apply retry/resume doesn't instruct resume-at-first-unchecked or reconcile the in-flight task
- Evidence: apply SKILL failure ladder 180-202; retry brief guidance 183-187 ("tight brief… forbid
  re-exploration") never says "skip [x] tasks, resume at first [ ], and reconcile the half-edited
  in-flight task." Resume state is on disk (tasks.md marks + uncommitted edits) but the killed
  task may be half-implemented yet still `[ ]`.
- "No subagent resume" (AGENTS.md 280) makes this the actual resume path; it relies on the fresh
  executor's own inference.
- Fix: retry/fresh-executor brief must state: resume at first unchecked; treat already-`[x]` as
  done; inspect+reconcile the first unchecked task's partial edits before continuing.
- Confidence: MEDIUM-HIGH.

### F7 — Explore skill is ~85% stance/ASCII-gallery prose injected on every invocation
- Evidence: explore SKILL — operational contract 16-49; then 55-324 is stance + entry-point
  ASCII galleries (89-280) + restated guardrail (320). ~270 lines the model doesn't need spelled
  out, loaded every explore.
- Fix: keep the direction-gate contract + a short stance; cut the galleries to 1-2 tiny examples.
- Confidence: HIGH (cost), LOW risk.

### F8 — Explore→propose brief relocation depends on silent slug==name match
- Evidence: explore writes `plans/<slug>/` (SKILL 20, slug from topic); propose relocates
  `plans/<name>/` → change dir with best-effort skip (SKILL 46-56, "silence is intentional" 55).
  If explore's slug ≠ propose's change name, the mv no-ops silently, brief+premise-review orphan
  in plans/, and the proposal reviewer's explore-brief path (propose 130-136) misses.
- Fix: propose should look up the brief by content/most-recent plans dir or warn when a
  plans/<slug>/explore-brief.md exists but none matched the change name; or have explore print the
  exact `propose <slug>` command (it half-does at 47) and have propose default name to that slug.
- Confidence: MEDIUM.

### F9 — Verifier pro + lens passes run strictly sequentially on a frozen, read-only tree
- Evidence: verify SKILL 59-71 (two sequential invocation blocks), gate semantics 108-113. Both
  passes are read-only verifiers on an unchanging tree — safe to run concurrently (unlike apply's
  writers). Only failure/re-run needs serialization.
- Fix: first-pass pro+lens concurrently (both background), serialize only on a NEEDS-REVISION
  re-run. Roughly halves COMPLEX verify blocking (~26→~13 min). Add explicit "what to do while a
  background run blocks" guidance (none exists today).
- Confidence: MEDIUM.

### F10 — Premise-review invocation prompt is triplicated across explore/propose/SMALL
- Evidence: explore SKILL 28-32; propose SKILL 129-136; AGENTS.md 186-195. Three hand-written
  prompt strings for the same premise review, slightly different wording — drift risk (same
  cite-don't-restate family the repo applies elsewhere) and a minor deepseek prefix-cache miss.
- Fix: single canonical premise-prompt block (in the reviewer agent or harness) cited by all
  three. Note: the big stable prefix is already the --agent system prompt, so the cache win is
  small; the drift-prevention win is the real one.
- Confidence: MEDIUM.

### F11 — Archive: dir-move + 3-of-4 delta-sync ops are mechanical yet run by the pro LLM
- Evidence: archive-executor.md §1 (mkdir+mv+conflict, 24-32) and §2 (delta sync); sync-specs
  SKILL 49-83. ADDED (append), REMOVED (delete block), RENAMED (rename header) are deterministic;
  only MODIFIED partial-scenario merge needs judgment. The mv/conflict-guard is 100% scriptable.
  status_lint (3d) is already a script — good. Reconciliation narrative (3a/3c) correctly stays
  LLM.
- Fix: `scripts/archive_move.py` for the move; a structured delta-applier for ADDED/REMOVED/
  RENAMED with LLM fallback only for MODIFIED. Shrinks the pro call to genuine judgment.
- Confidence: MEDIUM.

### F12 — Freeze-eligibility is a prose judgment, not a deterministic check
- Evidence: propose SKILL 184-192 — freeze = zero 🔴 AND (proposal) PREMISE: AGREE, judged by the
  orchestrator reading the appended review text. The reviewer verdict is machine-readable
  (reviewer.md 137-169: 🔴/🟡/💡 + `PREMISE:` + `VERDICT:`).
- Fix: `freeze-check` parses the latest review block for residual 🔴 + the premise line + (already
  covered) `openspec validate`, emits FREEZE-OK/BLOCKED. Removes a fumble-prone manual gate.
- Confidence: MEDIUM.

### F13 (minor) — notes.md five-field discipline is a belabored prose contract + verbal ritual
- Evidence: verify SKILL 315-382 (~40 lines on field 5 + a mandated emoji-checklist echo in 18).
  Guards a real failure (open-questions dying at session boundary) but is enforced by ritual, not
  mechanism.
- Fix: `scripts/notes_lint.py` asserting the 5 fields + "Still owned by archive" present; gate the
  phase-STOP on it. Converts ritual → deterministic check (mechanism-over-docs).
- Confidence: MEDIUM.

### Low-priority
- Propose Claude/OpenCode branches restate the freeze+premise+overrule logic twice (propose
  114-208 vs 211-234) — maintenance/token bloat; single-source the shared logic, fork only the
  invocation. (Recurs in apply/verify/archive.)
- Archive omits the EXIT-sentinel (harness 76-79; archive 133-136) — known drift, one-line fix
  (append the sentinel) for completion-detection robustness.

## Missing skills
- session-handoff (WRITE side): AGENTS.md 10-13 reads/deletes HANDOFF.md but no skill WRITES one
  when context runs low — exactly when the session is most degraded and "no subagent resume"
  (280) bites hardest. High value. A resume skill is largely covered by the AGENTS.md resume
  preamble, but the write side is unowned.
- (No operator-disambiguation skill needed — AskUserQuestion inline suffices.)

## VERDICT: reviewer/verifier prompts too tight or too loose?
- Agent DEFINITIONS (openspec-reviewer, openspec-verifier) are TIGHT-but-JUSTIFIED: four premise
  checks, default-to-dissent, D4/D10/D11 calibration, anti-patterns citing real incidents. Each
  section earns its place; not over-constrained.
- Skill INVOCATION prompts are appropriately THIN (weight lives in the agent def).
- The problems are in SKILL PROSE, both directions:
  - TOO TIGHT / ritualistic: verify step 18 "use exactly this shape" verbal ack (360-382);
    notes.md field-5 belaboring (315-358) — a lint should enforce presence.
  - TOO LOOSE: verify steps 13-15 "search keywords… assess if implementation likely exists"
    (228-256) — invites low-precision guessing.
- Net: the models' own prompts are fine; trim ritual and tighten the fuzzy rubric in the verify
  SKILL.

## VERDICT: which steps can be script-replaced (full/partial)?
- FULL: delegation post-processing (F1); archive dir-move (F11); task-checkoff counting (use
  `openspec status --json`, already exists — F4); freeze severity-parse (F12); notes.md field
  presence (F13).
- PARTIAL: delta-spec sync ADDED/REMOVED/RENAMED (F11); review-log round/date stamping.
- CORRECTLY LLM (do not script): reconciliation narrative (STATUS why + questions routing),
  behavioral eyeball/live smoke, premise + lens judgment, explore.
