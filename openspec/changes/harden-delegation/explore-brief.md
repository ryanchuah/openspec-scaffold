# Explore Brief — harden-delegation

Captures the exploration context behind this change (incidents, decisions, rejected
approaches, constraints) so design.md and the reviewer have the requirements context that
isn't otherwise in the artifacts.

## The problem

Delegated work — the deepseek `apply-executor` (Flash) and the deepseek `openspec-reviewer`
(Pro) — is governed by *trust* plus a fixed wall-clock `timeout`. That fails in two
directions: agents can spin productively-looking but unproductively until the cap kills
them, and "tests pass before commit" rests on the executor's word.

## Incidents (evidence — leftover /tmp logs, all EXIT=124)

1. **`p2-apply-c` (apply, 600s cap):** 12 edits to one test file, 7 to another; same tests
   failing; continuous tool activity, no convergence. → motivates the non-convergence stop rule.
2. **`p2-review-des-r1` (reviewer, 300s cap):** 44 tool calls, only 2 text entries, all
   read-only grep/read, a ~182s no-tool gap, and **produced no review** before the kill. →
   motivates raising the reviewer budget + incremental review-log output (NOT throttling).
3. **`apply-f1f2` (apply):** repeated partial pytest runs with tweaked flags; killed at
   "run the full suite one final time." Ambiguous (spin vs one long run) — the lone case
   where a modestly larger cap, not heartbeat, might help. Treated as the exception.

Separately: green mock suites have shipped broken integrations (the `order=volume` / pytrends
war-stories) — nothing deterministically enforces tests-green-before-commit.

## Decisions

- **Commit-test-gate** is the primary enforcement: a Claude `PreToolUse` hook on `git commit`
  runs a shared `scripts/test-gate.sh` and blocks on red. The executor never commits, so the
  orchestrator's commit is the single chokepoint.
- **Apply-executor non-convergence** is defined (see proposal "What Changes"): same error
  signature after 2 attempts · OR 3rd edit to same file for same failure · OR artifact/knowledge
  gap. → stop + report; orchestrator triages.
- **Reviewer**: raise the runtime cap and append findings to `review-log.md` incrementally;
  no read/grep throttle (re-examination on new info is legitimate; the reviewer must be
  thorough, never rushed).

## Rejected approaches (do not re-litigate)

- **Progress-heartbeat / stall-on-idle kill.** The real loops kept tool activity continuous,
  so activity-based stall detection would have caught ≤1 of 3 incidents while adding false-kill
  risk to legitimate long single operations (the test suite). Also re-opens the "kill the right
  PID" problem the `timeout` wrapper deliberately solved, and depends on the unproven OpenCode
  event API. Net: high complexity, low yield → dropped.
- **Raising the apply cap as the primary fix.** For looping runs a bigger cap just wastes more
  time before failing; cap stays a backstop only.
- **Throttling the reviewer** ("read each file once / don't re-grep / you have 5 min"). Fights
  the goal — the reviewer is a quality gate and must be thorough; the failure was starvation,
  not excess. Cure is more time + incremental output.

## Constraints / design open-questions (deferred from Review Round 1)

- **Reviewer write mechanism (🟡#1).** `openspec-reviewer.md` currently has `edit: deny` and
  `bash: deny` — it *cannot* write `review-log.md` today. Design must pick: grant `edit`
  scoped to `review-log.md`, OR have the reviewer stream findings to stdout and the primary
  appends. (Streaming keeps the reviewer read-only — likely preferable; design to decide.)
- **Reviewer timeout value (🟡#3).** Concrete new cap; principle = at least match apply's 600s.
  Note the operator has set THIS change's review cap to 780s (13 min) — a candidate anchor.
- **Error-signature normalization (💡#2).** "Same error signature" needs a concrete rule:
  normalize out variable parts (line numbers, timestamps, memory addresses, tmp paths) before
  comparing, so cosmetic changes don't read as progress.
- **Per-repo test command.** The gate needs each repo's test command (extrends: pyproject/pytest;
  psc-monitor: Makefile+pyproject; scaffold: none → gate is a no-op there). Where this value
  lives is a design detail (and will later be a single-source manifest fill).
