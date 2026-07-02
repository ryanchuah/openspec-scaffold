# Next-session kickoff prompt — succession-hardening portfolio

> Paste the block below into a fresh session to continue the portfolio. It is written to be
> self-orienting; the detailed state lives in the files it points at.
>
> **Order note:** the operator resequenced the remaining two changes — `delegated-agent-safety`
> (MEDIUM, change 4) runs NEXT (ahead of `prune-knowledge`), on risk priority: it fixes a real,
> already-materialized safety hole, and running `prune-knowledge` last lets it double as a final
> knowledge-tree consolidation pass. There is no dependency between the two, so the swap is safe.

---

Continue the succession-hardening portfolio in /home/pang/Projects/openspec-scaffold.

**Read in order:**
1. AGENTS.md — then follow its mandatory reads (knowledge/STATUS.md + the Active section of
   knowledge/questions/INDEX.md), with the git-log freshness check.
2. plans/succession-hardening/HANDOFF-next-session.md — the portfolio handoff: State (changes 1 & 2
   shipped), the remaining changes with scopes and per-change process requirements, standing
   constraints, and environment gotchas. **Change 4 (`delegated-agent-safety`) is section "### 3."
   there** (numbered by original sequence, not run-order).
3. plans/succession-hardening/explore-brief.md + premise-review.md — the portfolio direction
   (already premise-gated PREMISE: AGREE; do NOT re-gate the direction). Note the reviewer's 🟡 on
   change 4: its data-safety fix must not be prose masquerading as mechanism — see below.

**Where the portfolio stands:** 2 of 4 changes shipped —
- Change 1 `mechanize-invariants` (MEDIUM) — shipped + archived (2026-07-02).
- Change 2 `repair-instruction-surface` (SMALL) — shipped 2026-07-03 (commits `e4eaa2f`,
  `f3ef126`, local `main`, not pushed).
- `prune-knowledge` (SMALL) is DEFERRED to after change 4 by operator decision — do NOT start it
  this session.

**Your task:** propose the next change — **`delegated-agent-safety` (MEDIUM)** — with its tier and
plan, and WAIT for my confirmation before executing anything (producing artifacts and running the
premise review are not gated; delegating apply / mutating project state is).

`delegated-agent-safety` scope (full detail in HANDOFF section "### 3."):
- (a) **Structural fix for the `openspec-verifier` data-safety hazard.** The verifier
  (`.opencode/agents/openspec-verifier.md`, `bash: allow`, `edit: deny`) mutated extrends'
  production SQLite during a real 2026-06-28 verify; current mitigation is only a per-prompt warning
  string. **The direction gate's explicit instruction (and the premise reviewer's 🟡):** explore
  PERMISSION-LEVEL tightening in the OpenCode permission model (external_directory scoping, bash
  allowlists, a read-only variant) BEFORE settling for a mandatory data-safety preamble. If prose is
  genuinely the best available, record the residual risk honestly rather than presenting it as
  resolved. This is the judgment core of the change — do not let a prose fix masquerade as mechanism.
- (b) Sanctioned single-file mid-session handoff convention (extrends improvised three root HANDOFF
  files; bless one — e.g. `knowledge/HANDOFF.md`, boot-read if present, deleted on absorption).
  Touches the AGENTS.md shared span + `knowledge/README.md` taxonomy (both scaffold-managed → joins
  the frozen sync queue).
- (c) Drift beacon: sync stamps the scaffold commit SHA into the target so staleness is visible from
  the downstream repo without running `--check` from the scaffold.
- (d) New-repo bootstrap checklist as a small `knowledge/reference/` file (dissolved-handbook
  remnant; change 1's sync-time hook-wiring warning already covers the mechanical half).

**Process — MEDIUM per AGENTS.md:** run the OpenSpec lifecycle. Propose emits `tasks.md`,
pro-reviewed to freeze (the proposal review carries the premise verdict — freeze needs zero 🔴 AND
PREMISE: AGREE); change-specific acceptance criteria go in the change's `notes.md`. Runs the FULL
verify skill (multi-model passes + simplicity gate + phase-gate STOP). **Because (a) touches a
data-safety surface, the conditional security pass at verify applies** — run it. Do not waive the
multi-model passes unless I explicitly say so.

**Model-tier note:** an Opus orchestrator is sufficient (the gates backstop it), but this is the
judgment-heaviest remaining change — the handoff calls it "the one to watch." Consider Fable for the
security-relevant design step (permission-model research + honest residual-risk framing) if you want
extra assurance.

**Standing constraints (do not violate):**
- **Downstream sync is FROZEN.** Do not run `sync_scaffold.py` against ../extrends or ../psc-monitor.
  The frozen queue already includes `repair-instruction-surface`; (b)/(c) here will join it.
- **Pushes to remotes are NOT authorized.** Commits to local `main` in small reviewed checkpoints
  are fine.
- **No standing autonomy grant** — propose tier + plan and get my confirmation before executing.
- **Flag every deletion to me before committing.**

**Environment:** test invocation is `pytest -q` (NOT `python3 -m pytest`). The commit-test gate is
armed — a red suite blocks the commit. The `openspec` CLI has hung once on `openspec status`; if so,
retry with `timeout 30 ... < /dev/null`.

---

## What comes after `delegated-agent-safety`

- **`prune-knowledge` (SMALL)** — the portfolio closer; operator pre-approved AGGRESSIVE pruning,
  **flag every deletion before committing.** Full scope in HANDOFF section "### 2." Sub-scopes:
  (a) fix the drift `python3 scripts/knowledge_lint.py` flags in this repo's knowledge tree (stale
  `ai-docs/` refs, archive-prefix gap); (b) close fully-resolved parked question files; (c) decide
  the `openspec-onboard` skill's fate (slim hard or delete — manifest-listed, no deletion/tombstone
  mechanism, so record the downstream-delete follow-on); (d) generalize `knowledge_lint.py`
  `DEFAULT_RETIRED_PATHS` (bakes a personal `/home/me/` path into golden-source defaults);
  (e) clean stray `plans/` files and decide `plans/succession-hardening/` residency now the
  portfolio is closing. Running it last means its `knowledge_lint` sweep also validates change 4's
  new knowledge files.
- **Operational queue** (HANDOFF section "### 4.", operator-gated) — when you lift the freeze: sync
  all shipped changes to ../extrends and ../psc-monitor, review + commit per repo, then per-repo
  wiring follow-ons; push to remotes when authorized.
