# Plan — repair-instruction-surface (SMALL)

**Portfolio:** succession-hardening, change 2 of 4 (direction premise-gated `AGREE`, 2026-07-02).
**Tier:** SMALL. **Date:** 2026-07-02.

## Tier rationale

Content-preserving instruction-surface edits + one small agent-readable reference file. No
behavior change to any script, no lifecycle change, no new abstraction. The riskiest part (the
verify-skill restructure) is mechanically backstopped by the `scaffold_lint.py` SEAL
(`budget-agreement` + `dangling-skill-refs`, run against this live repo by
`test_scaffold_lint.py::test_live_repo_lints_clean`) and the `sync_agents_md` unit tests. Matches
the explore-brief tier assignment and the session handoff. SMALL process applies: plan + flash
premise pass before apply; single flash verifier pass after; no verify-skill invocation.

## Problem statement

Three residual instruction-surface hazards from the succession-hardening explore brief (its
failure modes #4 and #7-adjacent), all forms of "the golden source relies on prose only a
frontier operator sustains":

**(a) The verify skill has two competing procedures.**
`.claude/skills/openspec-verify-change/SKILL.md` presents the mandatory behavioral review as a
blockquote *preamble* (lines 14–41), then a separately numbered **"Steps 1–10"** artifact/spec
checklist (lines 146–354). Every other openspec skill uses "Steps 1–N" as *the* procedure, so a
Sonnet-class / smaller model pattern-matches onto the numbered checklist and skips the behavioral
half — which the file itself calls "the core of verify, not optional." This makes the single most
important gate in the whole lifecycle the easiest one to skip. Highest-leverage item in this change.

**(b) The golden source still presents as an unfilled template.**
`AGENTS.md` line 1 is `# <FILL: project name>` and its `## Project context` section (lines 66–79)
carries two `<FILL:>` placeholder blocks. The `openspec/config.yaml` `context:` block — which
AGENTS.md names as "the single short source" for project context — is *partially* `<FILL:>`:
its first four fields (Project / Purpose / Tech stack / Testing) are placeholders, while the
Style and Web-research lines already carry real content. A junior engineer or model opening the repo
that governs both downstream repos sees a half-built template instead of a plain statement that
this repo **is** the golden-source scaffold.

**(c) [optional] Exit-code conventions are prose-scattered.**
The deterministic tooling family uses a small set of exit-code conventions (audit 0/2/3;
knowledge_lint & sync `--check` 0/1; status_lint 0/2; test-gate 0/2; scaffold_lint; the
convergence check's verdict-on-stdout). No single agent-readable surface states them. A small
`knowledge/reference/` table single-sources them (mechanism-over-docs: deterministic checks first,
agent-readable on-demand reference second — this is the second tier, not a human handbook).

**Already resolved — explicitly OUT of scope:** the dangling `openspec-continue-change` reference
(fixed and shipped with change 1, mechanize-invariants).

## Proposed approach

### (a) Restructure the verify skill — content-preserving reorganization

Collapse the two procedures into ONE numbered procedure whose opening steps ARE the behavioral
review. Concretely:

- The blockquote's 5 behavioral steps (read diffs / re-run full suite / eyeball real output /
  live smoke / on-defect re-delegate) become the **first numbered steps** of the single "Steps"
  procedure, under a heading that marks them mandatory and non-delegable.
- The current "Steps 1–10" artifact/spec checklist renumbers to follow, keeping the document's
  existing ordering semantics intact: **behavioral review → multi-model passes (MEDIUM/COMPLEX) →
  simplicity + security gates → artifact/spec-mapping checks → report → notes.md checkpoint →
  verbal acknowledgement → PHASE-GATE STOP.**
- **Every** rule, caveat, timeout budget, severity label (🔴/CRITICAL/WARNING/SUGGESTION), the
  SMALL-tier-exclusion note, the multi-model pass sequence, the fix-redelegation mechanics, and
  the phase gate are preserved **verbatim**. Only their *framing* changes from
  "preamble + separate checklist" to "one continuous numbered procedure." This is reorganization,
  not redesign — no semantic edits.

**Why it's safe to do as content-preserving reorg:** `scaffold_lint.py`'s `budget-agreement` check
requires every embedded `timeout -k G B` pair in this file to match the §e harness table, and
`dangling-skill-refs` requires every skill reference to resolve; both run against this file via the
SEAL test in the pytest suite, which the commit gate enforces. Any accidental budget-number drift
or broken reference during the restructure fails at commit time.

**Fidelity risk / executor choice — operator decision.** A content-preserving restructure of a
nuanced instruction file rewards judgment over mechanical edits. The default apply-executor is
deepseek-v4-flash; for change 1's comparable delicate work the operator directed Sonnet instead.
**Recommendation: Sonnet apply-executor for sub-scope (a)** (with the SEAL + my verify review as
backstops), flash acceptable for (b)/(c). Flagged for your call.

### (b) Fill the golden-source identity — provably non-propagating

- `AGENTS.md` line 1: `# <FILL: project name>` → `# openspec-scaffold`.
- `AGENTS.md` `## Project context`: replace the two `<FILL:>` blocks with 2–4 sentences stating
  plainly that this repo IS the golden-source scaffold governing the downstream repos
  (extrends, psc-monitor) via `scripts/sync_scaffold.py`, keeping the existing pointer to
  `config.yaml` `context:` as the single short source. Fill or drop the "Hard constraints"
  `<FILL:>` line (recommend: state the real standing constraints — edit scaffold-managed files
  only upstream; downstream propagation is operator-gated).
- **Recommended addition (flagged):** fill the `openspec/config.yaml` `context:` block too
  (Project / Purpose / Tech stack / Testing / Style already partly real). AGENTS.md points to it
  as the single source, so leaving it `<FILL:>` leaves the pointer dangling. It is per-repo (see
  zero-drift proof below), same safety profile. The handoff scoped (b) to AGENTS.md only, so this
  is a proposed expansion — include it or not, your call.

**Zero-drift guarantee (why none of (b) propagates downstream):**
`sync_agents_md` composes the downstream file as `t_title + span1 + proj_ctx + span2 + tail`,
where `t_title` (everything before `> **MANDATORY`, including the title) and `proj_ctx` (the
`## Project context` section) are taken from the **target**, not the scaffold
(`scripts/sync_scaffold.py:94–96`). `sync_config_yaml` likewise "preserves the target's
`context:` block" (`sync_scaffold.py:137`). Both are already unit-tested
(`test_sync_scaffold.py::test_project_context_preserved_byte_identical`). Filling these regions in
the scaffold therefore **cannot** change any downstream file.

**Empirical confirmation without touching the frozen downstream repos:** I will run
`sync_agents_md(edited_scaffold_text, synthetic_target_text)` and `sync_config_yaml(...)` against a
synthetic target in the scratchpad and assert the output's title/project-context/context equal the
*synthetic target's*, not the scaffold's. **I will NOT run `sync_scaffold.py --check` against
`../extrends` or `../psc-monitor`** — the standing sync freeze forbids running the tool against a
downstream repo. (Note: the handoff's sub-scope (b) literally says "confirm with
`sync_scaffold.py --check` against a downstream." That collides with the freeze. The synthetic-target
dry-run gives the identical guarantee without touching a real downstream. If you'd rather I run a
read-only `--check` against a real downstream anyway, tell me and I will.)

### (c) [optional] Exit-code conventions reference file

Add `knowledge/reference/exit-codes.md` — a compact table of the deterministic-tooling exit-code
conventions, **verified against script source** (sweep complete; table + file:line evidence saved
to scratchpad `exit-codes-verified.md`). The sweep found the handoff's own shorthand is partly
wrong, which is exactly why the source-verified table earns its place: the **"audit family 0/2/3"
is only true for `audit_bundle.py` + `data_lint.py`** — `audit_scope.py` and `index_coverage.py`
are **0/3 only** (report-only, never gate); `_convergence.py` surfaces its verdict on stdout (its
docstring's advertised exit 1 is never returned); `sync_scaffold.py` has `--check-refs` and a
preflight `sys.exit(1)` beyond `--check` 0/1. Agent-neutral, on-demand. Optional: drop it if
you'd rather keep `knowledge/reference/` minimal. `knowledge/reference/` is not auto-propagated
(per-repo per AGENTS.md), so it is scaffold-local regardless.

## Out of scope

- **Any downstream repo edit or sync** — frozen (operator hold). See propagation note below.
- The dangling `openspec-continue-change` fix — already shipped in change 1.
- **Any behavioral/semantic change to the verify procedure** — every rule/budget/gate/severity
  preserved verbatim; this is reorganization, not redesign.
- Any change to scripts, `scaffold_lint` checks, or the sync mechanism.
- Pushes to remotes — not authorized.

## Propagation note (joins the frozen pending-sync queue)

- **(a)** `openspec-verify-change/SKILL.md` IS manifest-managed (byte-copy, manifest line 16), so
  its restructure **will** propagate downstream on the next sync → joins the frozen queue with the
  four already-queued changes. No downstream action now.
- **(b)** AGENTS.md title/project-context and config.yaml `context:` are target-preserved →
  **do not propagate** (proven above). Scaffold-local, permanent.
- **(c)** `knowledge/reference/` is not auto-propagated → scaffold-local.

## Deletions

**None expected.** (a) reorganizes one file in place; (b) edits two files in place; (c) adds one
file. If execution surfaces any required deletion I will flag it before committing (standing
preference).

## Decisions confirmed (operator, 2026-07-03)

- **Executor for (a):** Sonnet apply-executor (per change-1 precedent for delicate restructure).
- **Scope (b):** AGENTS.md + config.yaml `context:` (first four fields) — the config expansion is
  approved; per-field fill drafted in `impl-spec.md`.
- **Scope (c):** include `knowledge/reference/exit-codes.md`.
- **Frozen-`--check` substitution:** synthetic-target dry-run in scratch (no real downstream
  touched) — accepted as the zero-drift confirmation.
- Premise verdict `PREMISE: AGREE` (flash, 2026-07-03) recorded in `premise-review.md`; its one 🟡
  ("entirely `<FILL:>`" inaccuracy) fixed in this plan.

The exact executor instructions (target structure for (a), verbatim fill text for (b)/(c)) live in
`impl-spec.md` in this dir.

## Process (SMALL, per AGENTS.md)

1. **[now]** Plan written (this file).
2. **[now, before apply — not gated on your confirmation]** Orchestrator runs the SMALL flash
   premise pass over this plan (`opencode run --agent openspec-reviewer --model
   deepseek/deepseek-v4-flash`, referencing the verified explore-brief for D10 drift). Verdict
   written to `premise-review.md` in this dir and presented to you inside the confirmation prompt.
3. **[after your confirmation]** Delegate execution to the apply-executor (Sonnet recommended for
   (a) per above; flash otherwise — your call). Sequential, checks off nothing (no tasks.md for
   SMALL; execution follows this plan's sub-scopes).
4. **[after apply]** My own verification: eyeball that the restructured skill reads as one
   procedure with the behavioral steps first; run the full suite (scaffold_lint SEAL green); run
   the synthetic-target sync dry-run for (b). Then a **single deepseek-v4-flash verifier pass**
   (SMALL does not invoke the verify skill or its multi-model passes).
5. **[commit]** Local `main`, small reviewed checkpoints. **No push.** Flag any deletion first.
