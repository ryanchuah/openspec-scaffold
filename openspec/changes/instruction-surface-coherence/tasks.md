# tasks — instruction-surface-coherence (OW-9 + OW-14)

Apply-phase edits only. All line anchors are as-of session start (2026-07-13); if a file has
shifted, locate by the quoted verbatim text, not the raw number. Acceptance criteria: `notes.md`.
Every edit preserves existing behavior except where an acceptance criterion changes it; this is a
coherence sweep (extraction + reconciliation), not a redesign.

## Group 1 — AGENTS.md canonical rules (shared spans; propagate downstream later)

- [x] **T1 — Canonical `autonomy-phase-advance` rule.** In `AGENTS.md` `## Change tiers` section,
  after the **full grant paragraph** (the paragraph beginning "An agent WITHOUT an explicit autonomy
  grant..." and ending "Scale process weight to risk:", ~L165-170) — NOT mid-paragraph — add a
  canonical block marked `<!-- CANONICAL: autonomy-phase-advance — cite, do not restate -->`
  stating: under an autonomy grant the orchestrator MAY auto-advance lifecycle phases
  (propose→apply→verify→archive) without a fresh per-phase request, EXCEPT it halts and surfaces to
  the operator across (a) a premise **DISSENT**, (b) an unresolved verify **NEEDS-REVISION**, or
  (c) any **operator-named gate** (downstream propagation, push-to-remote). Cross-reference the
  `tier-confirmation-gate` spec as the governing capability. Without a grant, each phase boundary is
  a hard STOP. Keep it to ≤6 lines.

- [x] **T2 — Model-assignment matrix: add haiku tier.** In `AGENTS.md` `## Roles` block (L90-139),
  add a matrix entry for the **haiku tier** as the cheapest mechanical-delegation model:
  haiku = mechanical run-and-extract (grep/build/probe/JSONL-parse); Sonnet = extraction/judgment-
  adjacent passes; deepseek/Sonnet = apply/archive executors (unchanged). Do not re-tier any
  existing agent — this only names the previously-absent haiku rung.

- [x] **T3 — Model-assignment matrix: Sonnet-first pre-route line.** In the same `## Roles` block,
  add one line: the operator MAY pre-route a specific change's apply to **Sonnet-first** (recorded
  in that change's `notes.md`); the deepseek-flash-first default is unchanged. Frame as legitimizing
  existing practice, default unmoved.

- [x] **T4 — Canonical `delegation-by-default` rule.** In `AGENTS.md` Working-process "Use subagents
  for independent work" bullet (L288-295), place the `<!-- CANONICAL: delegation-by-default — cite, do not restate -->`
  marker on the line directly ABOVE the bullet header, and add the crisp canonical one-liner as the
  FIRST sentence of the bullet (before the existing "Parallelize independent research/extraction..."
  content): **run-and-extract → subagent** (haiku mechanical / Sonnet extraction); **read-and-judge
  → orchestrator**; plan the slices before delegating. Preserve all existing bullet content after it.

- [x] **T5 — Assumption-batching rule.** In `AGENTS.md`, add a **new bullet immediately adjacent to**
  (directly after) the "Plan non-trivial work before executing; ask the user when genuinely unsure
  rather than guessing" bullet (L330-331) — do NOT cram it inside that short planning bullet. New
  bullet: a **non-blocking** ambiguity gets a recorded default in the change's `notes.md`
  `Assumptions` block and is batch-surfaced at the next operator gate; only a **blocking** ambiguity
  interrupts immediately.

- [x] **T6 — Boot-read displacement rule.** In `AGENTS.md` top mandatory-read blockquote (L3-37),
  in the "Treat this file as stable" paragraph area (~L31-35), add one line: adding a new mandatory
  boot read SHALL displace or shrink an existing one — the boot set is a fixed budget, not a growing
  list.

## Group 2 — Phase-gate citations (4 skills; each cites T1's canonical rule)

- [x] **T7 — propose skill phase gates.** In `.claude/skills/openspec-propose/SKILL.md` L21 and L307
  PHASE-GATE text, replace the bare "Never invoke implementation without an explicit user request.
  Crossing phases without permission is a hard rule." with a version that cites the
  `autonomy-phase-advance` canonical rule: absent an autonomy grant this is a hard STOP; under a
  grant, auto-advance is permitted per that rule EXCEPT across DISSENT / NEEDS-REVISION /
  operator-named gate. Preserve the user-facing "Say 'apply <name>'" prompt for the no-grant path.

- [x] **T8 — apply skill phase gates.** Same citation edit at
  `.claude/skills/openspec-apply-change/SKILL.md` L21 and L311 (next phase = verification).

- [x] **T9 — verify skill phase gates.** Same citation edit at
  `.claude/skills/openspec-verify-change/SKILL.md` L166 and L439 (next phase = archive). Note the
  NEEDS-REVISION carve-out is especially relevant here.

- [x] **T10 — archive skill phase gate.** Same citation edit at
  `.claude/skills/openspec-archive-change/SKILL.md` L14 and L327 (archive is final; the rule's
  "do not start NEW work without an explicit request" still holds — a grant does not authorize
  inventing a next change).

## Group 3 — Self-review wording reconciliation

- [x] **T11 — Fix delegation-harness self-review carve-out.** In
  `.claude/skills/_shared/delegation-harness.md` §"Carve-out: verify's in-process self-review"
  (L102-107), correct the wording: the self-review is **the orchestrator's own in-process review
  pass performed inline by the primary** (NOT an `opencode run` delegation and NOT a Task-tool
  spawn — there is no separate process), which is exactly why it is exempt from the §a/§c hardening.
  This matches the verify skill (Steps 4-8, "run git diff yourself", "re-run the FULL suite
  yourself"). Remove the misleading "a Task-tool spawn" phrasing. Do not change the exemption
  itself or the delegated-verifier-pass sentence.

## Group 4 — Propose freeze-branch de-duplication (prose surgery — apply carefully)

- [x] **T12 — Collapse propose Claude/OpenCode freeze branches.** In
  `.claude/skills/openspec-propose/SKILL.md`, the two platform branches (Claude L115-208, OpenCode
  L211-234) each restate the same freeze ladder (zero-🔴 gate → per-artifact freeze → premise
  AGREE/DISSENT routing, Claude L178-192 / OpenCode L222-231). Extract the shared freeze ladder into
  ONE statement that both branches reference; keep only the genuinely platform-specific delta (Claude
  = `opencode run` reviewer invocation + jsonl assert; OpenCode = Task-tool `subagent_type` +
  halt-on-failure). Behavior preserved byte-for-behavior — extraction, not redesign. Verify the
  post-branch shared tail (L236-247) still reads coherently after the collapse.
  **MUST-PRESERVE (do not lose in the collapse):** two Claude-branch invariants that sit in the
  invocation section, NOT the freeze ladder — (a) the **model-override clause** ("If the user
  specified a different reviewer model, substitute it for `deepseek/deepseek-v4-pro`", ~L150-152);
  (b) the **prompt-variation-by-artifact** logic (different prompt appendices for proposal vs
  design/tasks, ~L127-137). These are platform/artifact-specific and must survive verbatim in intent.

## Group 5 — Archive EXIT-sentinel

- [x] **T13 — Add archive EXIT-sentinel.** In `.claude/skills/openspec-archive-change/SKILL.md`
  archive-executor invocation (L137-157), append the sentinel to the wrapped command, matching
  apply's shape (apply L118-119): `; echo "EXIT=$?" > /tmp/archive-out.exit`. Update the self-note
  at L134-135 (currently "omits the EXIT-sentinel — pre-existing drift, left as-is") to state the
  sentinel is now present. Update completion detection to key off the exit file if the skill relies
  on the background-completion notification only.

- [x] **T14 — Update delegation-harness §d archive note.** In `.claude/skills/_shared/delegation-harness.md`
  §d (L77-79), update the "Archive's executor ... omits the `echo "EXIT=$?"` sentinel — pre-existing
  drift, left as-is" note to reflect that the sentinel is now added (T13); archive now matches the
  §d contract.

## Group 6 — OW-14 point-of-action delegation cues

- [x] **T15 — verify skill cue (Step 5 ONLY).** In `.claude/skills/openspec-verify-change/SKILL.md`,
  add the point-of-action delegation cue at **Step 5 (re-run the FULL suite, ~L207) ONLY** — the most
  unambiguously mechanical of the inline run+extract steps. The cue MUST cite `delegation-by-default`
  AND restate the constraint inline verbatim in intent: "the *run+extract* of the suite (produce the
  green/fail signal) is delegable to a haiku/Sonnet subagent; the behavioral **judgment** — does the
  output match the oracle — is Steps 4–8's mandatory, **NON-delegable** core and stays with the
  orchestrator." Do NOT add cues at Step 6 (eyeball output) or Step 7 (live-smoke): those steps'
  observation is judgment, and a cue there would read as a loophole against the L203 "do not delegate"
  gate. Leave L203 untouched and unweakened.

- [x] **T16 — apply + archive skill cues.** Add the same one-line point-of-action cue at the inline
  JSONL-parse / targeted-test sites: apply L155/L175 (jsonl parse) and L138-139 (targeted tests
  between slices); archive L166-168 (assert-ran jsonl parse). Cite `delegation-by-default`. Note OW-7
  will later mechanize the jsonl-parse entirely — these cues are the interim rule.

## Group 7 — Gate

- [x] **T17 — Green gate.** Run `bash scripts/check.sh` (ruff + format + pytest incl. scaffold_lint /
  knowledge_lint / status_lint). Must exit 0. Fix any lint failures (e.g., a canonical-marker or cite
  check). Do NOT commit (orchestrator commits after verify).
  **KNOWN MEDIUM validator blind spot (do NOT treat as a gate):** `openspec validate
  instruction-surface-coherence --strict` does NOT validate this change — it prints "Unknown item"
  and exits 0 because `openspec validate` discovers changes via `proposal.md` and MEDIUM changes have
  none (OUTSTANDING-WORK.md finding 2, empirically confirmed this session). The spec delta at
  `specs/tier-confirmation-gate/spec.md` therefore gets NO CLI validation; instead **manually verify
  its delta format** — `## ADDED Requirements`, each `### Requirement:` with its normative SHALL/MUST
  on the requirement's FIRST physical line, and `#### Scenario:` blocks with WHEN/THEN. The pro review
  already inspected it; confirm structure holds after any edits.
