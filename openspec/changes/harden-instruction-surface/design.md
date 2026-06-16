## Context

A 2026-06-16 audit of the first-load instruction surface (AGENTS.md + `ai-docs/` + the workflow
skills) found it is **lean but drifted**: three changes shipped on 2026-06-16 (the commit-test-gate
hook, the apply-convergence-guard failure ladder, and the `scripts/test-cmd` single-source) updated
the skills and `decisions.md` but were never propagated to older surfaces, and the `## Change tiers`
guidance actively licenses unsafe autonomy ("classify every change yourself and state the tier") — an
agent recently self-classified and began applying edits with no plan shown. This change reconciles the
stale text and adds a tier-confirmation guardrail. It is **scaffold-only**; propagation to
`extrends`/`psc-monitor` rides on the separate single-source change ("change 2").

This is a documentation/instruction change with **no external-API surface** (no code paths, clients,
or network calls change).

## Goals / Non-Goals

**Goals:**
- Instructions never contradict shipped behavior (the hook, the convergence ladder, the test-command source).
- A non-fast-track agent confirms the proposed tier + plan with the operator before executing.
- The orchestrator's verify test re-run is single-sourced from `scripts/test-cmd` (with documented fallback).
- The web-research convention is complete in both copies (rule d present); the onboard tutorial stops teaching a forbidden `tasks.md` shape; the hand-fix threshold is stated once.

**Non-Goals:**
- Cross-repo propagation / the single-source sync mechanism (change 2).
- Creating `.claude/settings.json` (already present + tracked) or `scripts/test-cmd` (scaffold gate stays inert).
- Collapsing the war-story / model-matrix duplication, or de-duplicating the AGENTS.md §9 ↔ research-fetch-convention.md overlap (change 2). This change only makes the two web-research copies *agree*.
- Changing any model assignment, timeout, or the lifecycle phase gates themselves.

## Decisions

- **D1 — H1 (AGENTS.md:42-43, "hook-free").** Replace `(A tracked, hook-free `.claude/settings.json`
  permissions file is also fine.)` with text acknowledging the shipped commit-test-gate `PreToolUse`
  hook as a sanctioned, Claude-only carve-out running a tracked, agent-neutral script, cross-referencing
  the `ai-docs/decisions.md` commit-test-gate hook carve-out decision. `settings.json` was verified
  present + git-tracked, so **no**
  conditional "may ship" hedging and **no** file creation (rejecting the reviewer's false-premise finding).
- **D2 — tier-confirmation gate (AGENTS.md `## Change tiers`, lines 114-115).** Rewrite "classify every
  change yourself and **state the tier** (the operator initiates tier-2/tier-3 lifecycles)" so that an
  agent **without** a fast-track grant proposes its tier + plan and obtains operator confirmation
  **before executing** (delegating apply / editing code / mutating state); producing the plan is not
  gated. With a grant, self-classify per fast-track. If the operator is unavailable, the agent does NOT
  execute — it reports the proposed tier/plan and waits. Cross-reference `ai-docs/fast-track-workflow.md`.
- **D3 — H2 (fast-track-workflow.md:38).** Replace the **entire** "Failure ladder: …" sentence (it
  currently covers both the operational-crash clause AND the "non-crash failure → Sonnet immediately"
  clause) with a single pointer that **references, does not restate**, the apply skill's canonical
  ladder (avoids future re-drift): e.g. "Failure ladder: follow the apply skill's ladder — operational
  crash → retry once → Sonnet; non-crash → declared-blocker (`### NON-CONVERGENCE BLOCKER`) routes to
  orchestrator triage, NOT reflexive Sonnet, vs opaque give-up → Sonnet. Always disclose any fallback."
  This keeps line 34's "delegation mechanics identical to the normal workflow" true.
- **D4 — M3 (verify SKILL:18 + config.yaml verify rule).** Change the hard-coded
  `.venv/bin/python -m pytest -q` full-suite re-run to source from `scripts/test-cmd`, **with the
  canonical fallback** already used by the apply-executor / apply-convergence-guard spec: "prefer
  `scripts/test-cmd`, falling back to the project's documented test command when absent — never an
  improvised command; e.g. `.venv/bin/python -m pytest -q`." The line-24 opt-in live-smoke example stays
  illustrative (it is inherently project-specific and already prefixed "e.g.").
- **D5 — L1 (hand-fix threshold).** Reconcile to a **single** standing value: **a single disclosed
  one-line change** (matches AGENTS.md:124 and fast-track's "single trivial one-liner"). Update verify
  SKILL:25 and config.yaml's "more than ~2 lines" phrasings to the one-line wording so no "~2 lines"
  remains.
- **D6 — M1/M2 (onboard SKILL).** (a) Remove the `## 2. Verify` checkbox from the tasks.md template
  (366-376) — verify is not a `tasks.md` item; mention it as a separate phase in prose. (b) onboard is a
  simplified teaching path, so do not rewrite the tutorial — append a one-line note (after the existing
  "DO:" narration block at each site) at the implement step (395-403) and the archive step (431-434)
  that **real changes delegate apply to the apply-executor and
  archive via the archive skill** (the inline implement + bare `openspec archive` shown here are
  teaching simplifications). This carries the genuine safety dimension the reviewer flagged without
  expanding scope.
- **D7 — M4 + L2 (research-fetch-convention.md).** Add **rule (d)** (the WebSearch-from-main-thread ban
  + route research through subagents) so the canonical block matches AGENTS.md:214-217. Reword the
  measurement line (5-6) to drop the dead `output/fetch-measure.md` path and present the reduction as
  illustrative, not a cited artifact. Leave the AGENTS.md §9 ↔ file overlap itself for change 2 — this
  change only makes the two agree.

## Risks / Trade-offs

- **Half-applied multi-site edits (L1/M3 touch several files).** → Mitigation: tasks.md enumerates each
  `file:site` explicitly, and Verification uses grep assertions that fail if any site is missed.
- **Scaffold-only edits leave extrends/psc-monitor stale.** → Accepted and documented; propagation is
  change 2. No regression — those repos already hold the stale text.
- **Referencing the apply skill from fast-track (D3) could rot if the skill is renamed/moved.** → Low;
  both are tracked shared files referenced by skill name, and a rename would update references in the
  same change. Preferred over restating (which is what caused the drift).
- **Onboard left as a simplified path (D6b) rather than fully delegated.** → Accepted: it is a one-time
  user tutorial; a pointer to the real delegated path removes the contradictory mental model without
  bloating the lesson.

## Verification

Change-specific acceptance criteria (verify phase confirms each; greps are concrete checks):
- **H1:** `grep -n "hook-free" AGENTS.md` → no matches; the cross-agent-compatibility section names the
  commit-test-gate hook and points to `ai-docs/decisions.md`.
- **Tier gate:** AGENTS.md `## Change tiers` states the without-grant "propose tier+plan, confirm before
  executing" rule and the operator-unavailable behavior, and references `ai-docs/fast-track-workflow.md`.
- **H2:** `grep -n "Sonnet immediately" ai-docs/fast-track-workflow.md` → no matches; line references the
  apply skill's declared-blocker ladder.
- **M3:** `grep -n "scripts/test-cmd" .claude/skills/openspec-verify-change/SKILL.md openspec/config.yaml`
  → at least one match in each, at the full-suite re-run instruction; AND
  `grep -n ".venv/bin/python -m pytest" .claude/skills/openspec-verify-change/SKILL.md openspec/config.yaml`
  → the hard-coded command is absent from the full-suite re-run text (it may remain only behind an "e.g."
  in the line-24 live-smoke example, which is out of M3 scope).
- **L1:** `grep -rn "~2 lines" AGENTS.md .claude/skills/openspec-verify-change/SKILL.md openspec/config.yaml`
  → no matches; the three sites (AGENTS.md — already the canonical source — verify SKILL, config.yaml) all
  read "one-line".
- **M1/M2:** the onboard tasks.md template has no `## 2. Verify` checkbox; onboard notes that real
  changes delegate apply/archive.
- **M4/L2:** `grep -n "WebSearch" ai-docs/research-fetch-convention.md` → present (rule d);
  `grep -n "fetch-measure" ai-docs/research-fetch-convention.md` → no matches.
- **Spec sync:** `openspec validate harden-instruction-surface --strict` passes; the three deltas
  (new `tier-confirmation-gate`; modified `apply-convergence-guard`, `commit-test-gate`) archive into
  `openspec/specs/` cleanly.
- **Scope guard:** no new files (`.claude/settings.json`, `scripts/test-cmd`, `scripts/test-gate.sh`
  unchanged); `git diff --stat` touches only the six files in Impact + the change dir.

## Open Questions

None blocking. Exact replacement wording for the onboard delegation note (D6b) is left to the
apply-executor within the stated constraint (one line, points to the delegated apply/archive path).
