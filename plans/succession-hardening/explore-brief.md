# Explore brief — succession-hardening

**Date:** 2026-07-02
**Status:** direction crystallized; awaiting premise review
**Method:** five parallel read-only exploration sweeps over this repo and both downstream
repos (sync mechanism, instruction surface, knowledge base/history, downstream state,
tooling quality), synthesized by the orchestrator. Operator has confirmed the direction
and tier framing below; this gate validates the premise before any change is proposed.

## Problem

This scaffold governs agent workflows for two downstream repos (psc-monitor, extrends), so
mistakes here propagate and are costly. The system as built works — downstream commit
discipline is real, the sync core is spec'd and tested (45 tests, idempotent, span-aware),
and the upstream/downstream feedback loop demonstrably closes (psc-monitor's knowledge-drift
diagnosis became `knowledge_lint.py` the same day). But the project must now be carried by
junior/mid-level engineers and Sonnet-class models rather than a frontier-class operator,
and **the system's remaining safety rests on prose conventions that only a frontier-class
operator reliably sustains.**

Evidence, by failure mode:

1. **Silent non-propagation.** A new skill/agent/script added to the scaffold but not to
   `scripts/scaffold_manifest.txt` never syncs downstream and nothing detects it —
   `sync_scaffold.py --check` walks only manifest entries.
2. **Unmarked load-bearing anchors.** The AGENTS.md span-merge hinges on three literal
   heading strings (`> **MANDATORY`, `## Roles`, `## After reading this file`) and a
   rules-block-must-be-last invariant in `openspec/config.yaml`. Nothing in either file
   marks these as special; an innocent heading rename breaks every downstream sync (loud
   but mystifying), and the failure surfaces at sync time, far from the edit that caused it.
3. **"Single-sourced" numbers that aren't.** Timeout budgets live in the delegation-harness
   §e table, but ~8 embedded bash blocks across AGENTS.md and four skills carry the literal
   numbers; a budget change requires synchronized hand-edits with no drift check. The
   existing `test_executor_body_agreement.py` proves the mechanized-agreement pattern works;
   it just covers only executor bodies.
4. **Instruction-surface hazards for smaller models.** `openspec-verify-change/SKILL.md`
   contains two competing procedures — the mandatory behavioral review formatted as a
   blockquote preamble, then a separately numbered "Steps 1–10" checklist; every other skill
   uses "Steps 1–N" as *the* procedure, so a model pattern-matching on that convention skips
   the part the file itself calls the core of verify. `openspec-apply-change/SKILL.md:67`
   references a skill (`openspec-continue-change`) that does not exist in this repo.
5. **Known safety holes, undecided.** (a) The `openspec-verifier` agent (`bash: allow`)
   mutated extrends' production SQLite DB during a real 2026-06-28 verify run; the standing
   fix is a per-prompt warning string, with the structural scaffold-level fix an open TODO.
   (b) There is no drift alarm: both downstream repos sat a week+ stale until someone
   manually ran `--check`. (c) A fresh repo bootstrapped by `cp -r` inherits
   `scripts/scaffold_check.py` but not the `.claude/settings.json` PreToolUse wiring that
   invokes it — the edit-guard is silently absent.
6. **Un-sanctioned workaround pattern downstream.** extrends improvised three root-level
   HANDOFF/HANDOVER files (superseding one another) for mid-session, not-yet-archived
   handoffs — a real need the knowledge taxonomy has no home for, currently met outside
   every discipline the system enforces.
7. **The scaffold's own knowledge tree has flagged-but-unfixed drift.** `knowledge_lint.py`
   surfaced stale `ai-docs/` references in `knowledge/roadmap.md` and
   `knowledge/decisions/INDEX.md` and an archive-prefix citation gap; these were enumerated
   in `knowledge/questions/` as out-of-scope for the knowledge-lint change and remain live.
   Several parked question files are fully resolved but still open as pointers.

## Root cause

Where the project converted a discipline into a mechanism (status_lint, executor
body-agreement test, commit-test gate, knowledge_lint), the rule has held. Where it relies
on prose and operator memory, its own linters are already finding drift in its own files.
The root cause is **an enforcement gap, not a documentation gap**: the operator's explicit
philosophy is that scaffolding should be deterministic and agent-driven — so the fix is
deterministic checks that fail loudly at commit time, plus agent-neutral on-demand
reference for the small irreducible remainder, not a human handbook.

## Direction

Four sequenced changes, each through the normal lifecycle at its own tier. Downstream
propagation of everything below **stays frozen** (operator hold, 2026-07-02) and joins the
existing pending-sync queue.

1. **`mechanize-invariants` (MEDIUM).** New `scripts/scaffold_lint.py` + tests, running in
   the scaffold's own pytest suite (green-before-commit already mandatory), covering:
   manifest completeness (managed-dir globs vs manifest, with an explicit exclusion list);
   AGENTS.md anchor + no-tail invariants and the config.yaml rules-block-is-last invariant
   at commit time (reusing `sync_scaffold.py` functions, not duplicating them); dangling
   skill-reference detection across instruction files; timeout-budget agreement between the
   harness §e table and every embedded `timeout -k X Y opencode run` block. Also: arm the
   scaffold repo's own dormant commit-test gate (`scripts/test-cmd` running pytest), and add
   a sync-time warning when a target repo's `.claude/settings.json` lacks the
   `scaffold_check.py` wiring.
2. **`repair-instruction-surface` (SMALL).** Restructure the verify skill so the behavioral
   review is the single numbered procedure (content-preserving reorganization); remove the
   dangling `openspec-continue-change` reference; fill the scaffold's own AGENTS.md
   title/project-context spans (per-repo spans — will not propagate) so the golden source
   stops presenting as an unfilled template.
3. **`prune-knowledge` (SMALL).** Fix the linter-flagged drift in the scaffold's own
   knowledge tree; close fully-resolved parked question files; decide and execute the
   onboard-skill slimming (operator approved aggressive pruning; every deletion flagged
   before commit). Note for the proposal: the manifest has no deletion/tombstone mechanism —
   removing a scaffold-managed file upstream orphans it downstream silently; scope this
   change to scaffold-side pruning and record the gap (or fold a tombstone check into
   change 1 if cheap).
4. **`delegated-agent-safety` (MEDIUM).** Structural fix for the verifier data-safety
   hazard (mandatory data-safety preamble in `openspec-verifier.md`: snapshot-before-touch,
   never write to production data stores; plus any expressible opencode permission
   tightening); a sanctioned single-file mid-session handoff convention (boot-read if
   present, deleted on absorption) added to the AGENTS.md shared span + knowledge taxonomy;
   a drift beacon (sync stamps the scaffold commit SHA into the target so staleness is
   visible without running `--check` from the scaffold).

Dissolved into the above (per operator direction, mechanism-over-docs): no maintainer
handbook; the exit-code-conventions table and the new-repo bootstrap checklist become small
`knowledge/reference/` files carried by changes 2–4; no init tooling (repo #3 is "maybe
eventually" — the sync-time wiring warning covers the bootstrap gap).

## Out of scope

- Any downstream repo edits or syncs (frozen; operator will authorize separately).
- Lifecycle redesign — the five-phase process is earning its keep downstream.
- Repo-registry / CI infrastructure for hypothetical scale.
- Accepted low-priority debt: triplicated `_write_json_atomic`, `audit_bundle._mode_multi`
  complexity-E refactor, `/tmp` convergence-state scoping, `fetch_clean.py` tests — all
  recorded in `knowledge/questions/`, none load-bearing for succession.

## Risks / open questions for the reviewer

- Is the four-change split right, or should 2 and 3 merge (both small doc-surface passes)?
- Change 1's budget-agreement check parses bash blocks out of markdown — is that check too
  brittle to be worth mechanizing, versus reducing the embedded blocks to citations?
- Change 4 touches synced agent files while sync is frozen — any sequencing hazard beyond
  queue growth?
