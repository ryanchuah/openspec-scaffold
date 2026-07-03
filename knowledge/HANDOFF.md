# HANDOFF — prune-knowledge shipped; close out this repo before propagation

**Type:** ephemeral mid-work session handoff (2026-07-03). Boot-read right after `knowledge/STATUS.md`
per AGENTS.md; **delete this file once absorbed** (its normal state is absent).
**From:** the session that implemented + committed `prune-knowledge` (portfolio closer).
**To:** the next orchestrator session.
**Operator intent for next session:** finish closing out ALL remaining in-repo items (including the
YAML nit below) **before** starting downstream propagation.

## Boot order

1. `AGENTS.md` + its mandatory reads (`knowledge/STATUS.md`, Active section of
   `knowledge/questions/INDEX.md`) with the `git log --oneline -5` freshness check.
2. **This file.**
3. The `prune-knowledge` artifacts if you need detail: `plans/succession-hardening/prune-knowledge/`
   (plan.md, tasks.md, premise-review.md).

## Standing constraints (unchanged — do not violate)

- **Downstream sync is FROZEN** by operator hold. Do NOT run `sync_scaffold.py` against a downstream
  repo until the operator lifts it.
- **Pushes to remotes are NOT authorized.** All commits are local `main` only.
- **No standing autonomy grant:** propose tier + plan and get operator confirmation before executing.
- **Flag every deletion to the operator before committing** (standing preference).
- **Mechanism over docs** (operator philosophy): deterministic checks first, agent-readable on-demand
  reference second, no human handbook.

## State — where things stand

- `prune-knowledge` (SMALL, succession-hardening change 4 of 4 — the closer) is **IMPLEMENTED and
  COMMITTED** to local `main` as **`28ba2bd`**. Gates green at commit (knowledge_lint exit 0, suite
  green via the armed commit-test gate). Verify was READY twice (orchestrator + one deepseek-v4-flash
  verifier pass); premise pass was operator-WAIVED (per-run).
- With this, **all four succession-hardening changes are shipped.** The proactive-build queue is empty.
- ⚠️ **`knowledge/STATUS.md` is now STALE** — it still lists `prune-knowledge` as the remaining approved
  change / immediate next action. Reconciling it is task 1 below (it was deliberately NOT reconciled in
  the shipping session; that is the write-deferred rule).

## Close-out tasks remaining IN THIS REPO (do these next, in order)

### 1. Reconcile project docs for prune-knowledge (the deferred archive/reconcile step)

`prune-knowledge` is a **plan-based SMALL change — there is NO `openspec/changes/` dir to move** and no
spec deltas. So "archive" here is doc reconciliation only. Your context will be fresh, so you may
reconcile **directly** (it is light) or delegate to the archive-executor per the write-deferred rule —
either is fine.
- **`knowledge/STATUS.md`:** add a `prune-knowledge` shipped section (≤150 words); drop the oldest
  narrated section per the ≤3 cap; rewrite `## Immediate next action` to say the portfolio is closed and
  the next horizon is repo close-out (tasks 2–4) then propagation.
- **`knowledge/decisions/INDEX.md`:** add a registry line for prune-knowledge (archiveless → `[inline]`
  essence: drove knowledge_lint to green via EPHEMERAL_PATHS + de-citing + drift fixes; closed 3 resolved
  trackers; **deleted openspec-onboard**). **Record that this SUPERSEDES the harden-instruction-surface
  `D6b` "keep onboard as a simplified teaching path" decision.**
- **`knowledge/questions/INDEX.md`:** no new Active items; prune-knowledge already removed the 3 closed
  trackers' pointers.

### 2. Portfolio residency + delete the old transient handoff

- **Delete `plans/succession-hardening/HANDOFF-next-session.md`** — the portfolio it guided is closed
  (that file itself says to delete it once the portfolio closes).
- Decide `plans/succession-hardening/` residency. It holds: `explore-brief.md` + `premise-review.md`
  (the premise-gated portfolio direction), `NEXT-SESSION-PROMPT.md` (stale), and the per-change dirs
  `repair-instruction-surface/` + `prune-knowledge/`. Options: keep the two premise-gated direction files
  as the durable portfolio record and drop the rest, or fold anything durable into `knowledge/` and
  delete the dir. Flag the deletions.

### 3. Broader parked-follow-on close-out sweep

Open each remaining pointer in `knowledge/questions/INDEX.md` (Parked) and close the genuinely-resolved
ones; leave the rest. **Caveat the operator already accepted:** a large share of parked items are gated
**on propagation itself** (per-repo lint-knowledge burn-down, downstream audit wiring, the onboard
tombstone) — those **cannot** close before propagating; they close during/after it. So the achievable
pre-propagation end-state is "everything resolvable-in-this-repo closed; the propagation-gated tail
stays open by design." Do not force-close a propagation-gated item.

### 4. The YAML nit (operator explicitly wants this closed)

`knowledge/questions/claude-agent-frontmatter-yaml.md` — the `.claude` fallback-agent `description:`
lines aren't strict YAML (latent, low-pri). Investigate; either fix the frontmatter or consciously close
the item with rationale. Note the `.claude/agents/*.md` are scaffold-managed, so a fix propagates on next
sync.

### 5. Carry-forward for propagation (record, don't act — sync is frozen)

- **onboard TOMBSTONE:** the scaffold manifest has no deletion mechanism, so the `extrends` +
  `psc-monitor` copies of `openspec-onboard` must be **deleted manually per-repo** when the freeze lifts.
  Make sure this survives into whatever pending-sync note you keep.

## Then: downstream propagation (operator-gated — do NOT start unprompted)

The frozen queue is a **large batch — 8 changes** (`premise-review-gate`, `pro-agent-flash-delegation`,
`deterministic-tooling-layer`, `knowledge-lint`, `mechanize-invariants`, `repair-instruction-surface`
[verify-skill only], `delegated-agent-safety`, `prune-knowledge`). When the operator lifts the freeze:
`sync_scaffold.py` per repo → manual per-repo knowledge/terminology sweep (the non-auto-propagated docs)
→ per-repo wiring (audit.toml, checks, task-runner targets, dev-extras pins; a first lint-knowledge pass)
→ onboard manual deletion (tombstone above) → pushes when authorized.

- **Orchestrator model for propagation: Opus, not Fable.** It is mechanical-but-careful (run sync, read
  diffs, commit, follow per-repo wiring docs) and backstopped by deterministic gates (scaffold_check
  guard, sync `--check` drift convergence, downstream commit-test gates + suites). Fable's premium is for
  gate-less open-ended synthesis (a future strategic re-audit), which this is not.
- **Watch the cross-repo `--dir` gotcha:** any delegated `opencode run` must set `--dir` to a repo that
  contains `.opencode/agents/<agent>.md`, or opencode silently falls back to the default agent (right
  model, wrong role). Run one slice per repo.

## Session facts a fresh agent won't find in the docs

- Test invocation on this machine is `pytest -q` from the repo root; `python3 -m pytest` FAILS (pytest is
  user-installed for python3.13 only). `scripts/test-cmd` encodes this.
- The commit-test gate is live: every `git commit` via Claude Code's Bash tool runs the suite (~2s); a red
  suite blocks the commit. `knowledge_lint.py` is NOT part of that gate — run it manually.
- deepseek delegation via `opencode run` works on this box (opencode 1.17.11; deepseek-v4-flash/pro
  configured). This session ran apply + the verifier pass on deepseek-v4-flash successfully.
- Premise/verifier waivers this session were PER-RUN operator directives, not standing.
