# SMALL plan — delegated-context-caching (OW-8, caching hygiene)

Tier: **SMALL**. Change is entirely doc/prompt/convention edits — no implementation code.
Derives from `knowledge/research/workflow-audit-2026-07-11/caching-analysis.md` §3/§6 and AUDIT
finding 2. OW-13 already shipped this analysis's items #2 (status_lint word budgets) and #3-boot
(`boot_surface_lint`); OW-8 is the delegated-prompt / AGENTS.md-injection remainder.

## Problem statement
Every delegated `opencode run` call (apply / archive / reviewer / verifier — the DeepSeek executors)
pays avoidable token cost per invocation, in two ways the analysis identified:
1. **Prompt shape kills prefix-cache credit.** 3 of the 4 delegated prompt templates inline a
   per-change variable path at word 4–6, ahead of ~40–110 words of byte-identical instruction text.
   DeepSeek prefix-caching rewards only a shared *prefix*; a variable placed early means the entire
   trailing boilerplate — identical across every apply/archive/review call ever made — never gets
   cache credit. The verifier prompt is the exception (no inlined path) and is already optimally
   shaped; it is the reference pattern to copy.
2. **AGENTS.md is auto-injected into every executor and is the highest-churn boot file.** opencode
   (confirmed v1.17.18) injects the project AGENTS.md verbatim into every `opencode run` system
   prompt; AGENTS.md is edited ~every 2 active days, so each edit invalidates the DeepSeek prefix
   cache for all 5 delegated agents at once. This churn cost is invisible and unmanaged today.

## Root cause
- (1) is a mechanical authoring habit — prompts were written "instruction about <thing at path>"
  (path first) rather than "instruction … the thing is at <path>" (path last). Nothing records the
  variable-last convention, so new/edited prompts keep reintroducing the early-variable shape
  (prose-is-write-only-memory).
- (2) is structural: AGENTS.md injection is a project-level baseline applied to all agents, and its
  churn is not treated as the cache-invalidation event it is.

## Proposed approach (what ships)
**A — Variable-paths-LAST reshape (4 prompt strings, behavior-preserving).** Move every per-change
variable substitution to the tail of the prompt, fixed instructions first, matching the verifier's
already-ideal shape. Preserve every wrapper-asserted marker. Exact target strings in §"Reshaped
strings" below. Edit sites (canonical homes, each string lives in exactly one place):
- apply-executor — `.claude/skills/openspec-apply-change/SKILL.md:112-117` (no wrapper marker)
- archive-executor — `.claude/skills/openspec-archive-change/SKILL.md:142-154` (no wrapper marker)
- openspec-reviewer (propose base) — `.claude/skills/openspec-propose/SKILL.md:192-194`
  (markers `### Premise Verdict` / `PREMISE: AGREE|DISSENT` live in the proposal.md-only *append*,
  which is preserved; `## Review Round`/severity come from the agent body, not this string)
- openspec-reviewer (SMALL premise) — `AGENTS.md:211-213` (markers `### Premise Verdict` /
  `PREMISE: AGREE|DISSENT` preserved)

**D — Convention + durable finding.**
- d1: add a "prompt-template shape — variable content last" subsection to
  `.claude/skills/_shared/delegation-harness.md` (the operative contract the 4 delegating skills
  cite), so the convention is review-enforced going forward. Names the verifier prompt as the
  reference and lists the markers that must survive any reshape.
- d2: extend AGENTS.md's existing stability preamble with a tight note: this file is injected into
  every delegated opencode executor and cannot be surgically excluded (see finding), so each edit
  resets the DeepSeek prefix cache for all delegated agents — **batch related edits**.
- d3: record the B-blocked finding durably (full evidence in this change's `notes.md`; a decisions
  registry entry + a Parked follow-on question at archive).

## Out of scope (deliberately NOT done — with rationale)
- **B — disable AGENTS.md injection for executors (the analysis's largest single lever, ~7.2k
  tokens/call): BLOCKED, deferred.** The hypothesized `OPENCODE_DISABLE_PROJECT_CONFIG=1` is proven
  (binary + empirical, this session) to ALSO disable `.opencode/agents/` discovery: with it set,
  `opencode agent list` returns 0 of our project agents (only built-ins). So it would silently swap
  `--agent apply-executor` for a built-in default agent (right model, WRONG role) — the exact
  silent-fallback footgun the delegation harness warns about. No per-agent instruction opt-out exists
  in the opencode v1.17.18 schema. Including B would sacrifice correctness. Full evidence → `notes.md`;
  revisit trigger → Parked follow-on. **This deferral is a correctness requirement, not a punt.**
- **C — single-source the "triplicated" premise prompt: DROPPED (over-engineering avoided).** Recon
  shows the premise prompt is NOT fatly triplicated: the only byte-identical shared substring across
  the 3 call sites is the ~7-word `### Premise Verdict block (PREMISE: AGREE|DISSENT)`; the rest is
  genuinely context-specific (artifact path, framing, model). The verdict FORMAT is already
  single-sourced in the reviewer agent body + the `premise-review-gate` spec, and the invocation
  skeleton is already single-sourced in `delegation-harness.md`. A `_shared/` citation to save ~7
  words would add indirection heavier than what it removes — against the repo's "cite-don't-restate is
  for fat rule-families" ethos. Drift-prevention for the markers, if ever wanted, is better as a
  deterministic lint (cf. `model-id-agreement`), noted as a possible follow-on, not folded in.
- **No spec delta.** A reorders words within a prompt (not spec-governed); D is convention + finding
  docs. `premise-review-gate` owns the premise *behavior* (verdict format, altitudes), which is
  unchanged. Forcing a spec delta would duplicate a canonical rule (handoff lesson #1).
- **No new deterministic check for "variable-last".** Considered and rejected: distinguishing
  per-change variables from fixed illustrative `<placeholder>`s (e.g. `knowledge/questions/<item>.md`
  in the archive prompt) is too fuzzy to detect reliably → high false-positive risk. The convention is
  review-enforced instead. (Marker-preservation IS checkable but is already enforced at runtime by the
  wrapper's `--require-marker`; a static duplicate is deferred as optional.)
- **OW-12 (archive mechanization), OW-16 (product-audit skill): NOT folded.** Different surfaces,
  higher blast radius; stapling them raises verification risk without coherence gain (handoff #2).
- The `.claude/worktrees/analyze/` locked worktree holds stale copies of these skill files — NOT
  canonical; ignore for the reshape.

## Reshaped strings (exact targets — apply is mechanical find-and-replace)

### A1 · apply-executor — `.claude/skills/openspec-apply-change/SKILL.md`, prompt body (112-117)
Target:
```
         "Implement an OpenSpec change by working through its tasks.md sequentially, \
          top to bottom, following its design.md and proposal.md. Check off each task \
          ([ ] -> [x]) in tasks.md as it lands. Do not modify proposal.md or design.md. \
          Do not commit. End with a brief completion report (what was implemented, \
          deviations, what the primary should check at verify, and any external-API \
          behavior you ASSUMED rather than verified). The change's tasks.md, design.md, \
          and proposal.md are all in the change directory: <changeRoot>." \
```

### A2 · archive-executor — `.claude/skills/openspec-archive-change/SKILL.md`, prompt body (142-154)
Target:
```
          "Archive an OpenSpec change: move its change dir to the archive path, sync \
           delta specs if requested, and reconcile the three project docs \
           (knowledge/STATUS.md, knowledge/decisions/INDEX.md, knowledge/questions/INDEX.md) \
           from the archived notes.md / proposal.md / design.md. Also run \
           scripts/knowledge_lint.py and re-check knowledge/reference/, \
           knowledge/roadmap.md, and the individual knowledge/questions/<item>.md Parked \
           bodies for now-stale claims about this just-shipped change; surface any findings \
           flag-only — do not edit those wider bodies. Do not commit. End with a brief \
           completion report (what was moved, which specs synced, which docs reconciled, \
           any wider-sweep findings, anything the primary should double-check). \
           changeRoot: <changeRoot>; \
           archivePath: <planningHome.changesDir>/archive/YYYY-MM-DD-<name>; \
           Delta spec sync requested: <yes/no>." \
```

### A3 · openspec-reviewer propose base — `.claude/skills/openspec-propose/SKILL.md` (192-194)
Target (base string; the per-artifact appends at 175-176 / 179-181 are UNCHANGED and still append
after this):
```
                "Review an OpenSpec change artifact. Also read the explore-brief if it \
                 exists and openspec/specs/ for context. The artifact to review is at \
                 <changeRoot>/<artifact>.md." \
```

### A4 · openspec-reviewer SMALL premise — `AGENTS.md` (211-213)
Target (the optional drift-append at 216-218 is UNCHANGED):
```
    "Review a SMALL change plan — NOT a structured proposal.md. Emit a ### Premise \
     Verdict block (PREMISE: AGREE|DISSENT) assessing problem/root-cause/solution. The \
     plan to review is at <planPath>." \
```

## Verification plan (SMALL)
1. Orchestrator deep review of every edit (semantics preserved, no marker dropped).
2. Deterministic grep: each reshaped prompt still contains its required markers
   (`### Premise Verdict`, `PREMISE: AGREE|DISSENT` for A3-append/A4) AND its first `<…>` per-change
   variable now sits in the final ~20% of the string.
3. One `deepseek/deepseek-v4-flash` verifier pass (SMALL bullet: same shape as the verify behavioral
   pass, flash tier).
4. `bash scripts/check.sh` green (ruff, scaffold_lint incl. model-id-agreement + executor-body
   agreement, status_lint C3, boot_surface_lint under budget). `openspec validate` "Unknown item"
   error on a proposal-less SMALL is expected — ignore.

## Apply-executor deviation (disclosed)
SMALL's default is delegate-to-deepseek-flash. This change is entirely doc/prompt/convention edits
(the primary's domain per AGENTS.md "quick doc edits and commits are done by the primary directly —
do not over-delegate trivia"), with exact target strings pre-authored, so the primary applies them
directly. Rationale: higher reliability on load-bearing prose, and it avoids the stale-worktree
misapplication footgun. The mandated SMALL premise pass and the verification above still run.
