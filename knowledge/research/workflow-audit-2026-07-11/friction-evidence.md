# Friction evidence — cross-repo mining (subC)

## Status: openspec-scaffold DONE (self); extrends + psc-monitor delegated to background agents (pending)

---

# REPO 1: openspec-scaffold (self-analysis)

## Review-round / revision-cycle stats (26 archived changes with review-log.md)

Methodology: counted `NEEDS REVISION` occurrences per review-log.md as a proxy for revision
cycles (more robust than raw "Round N" labels, because round-numbering convention is
inconsistent across the repo's history — some files reset "Round 1" per artifact
[proposal/design/specs/tasks each start at 1], others number continuously across all
artifacts in one file. Flagging this inconsistency itself as a minor process-debt item.)

Distribution across 26 changes (NEEDS-REVISION count per change, i.e. revision cycles
before every artifact froze):
- 0 revisions: 11/26 changes (42%) — froze clean on first pass for every artifact
- 1 revision: 7/26
- 2 revisions: 3/26
- 3,4,6,9,11: 1 each (outliers)
- Median = 1, Mean ≈ 1.77, Max = 11

Top outliers (most review overhead):
1. `2026-06-21-premise-review-gate`: 11 NEEDS REVISION / 17 PASS markers. Rounds spanned
   proposal (2 rounds), design (3 rounds, including a 🔴 "autonomy path breaks the gate"
   defect found only in round 2), specs (1 round), tasks (1 round). This is the single
   most expensive review cycle in the repo — building a gate about premise review was
   itself the hardest thing to get review-approved.
2. `2026-06-19-restructure-project-knowledge`: 9 NEEDS REVISION / 12 PASS. Design took 2
   revision rounds (5 total design rounds counting re-reviews) driven by real cross-file
   contradictions (e.g. `memory/README.md` ownership conflicting with the spec's
   blanket-exclusion rule; a git-mv ambiguity that would have produced wrong `git rm`
   commands across 3 repos). tasks.md round 1 found 3 concrete 🔴 blockers including one
   that would have deleted load-bearing test infrastructure (`docs/test/canary-non-convergence/`)
   with no design authorization — a real near-miss.
3. `2026-06-16-harden-delegation`: 6 NEEDS REVISION / 14 PASS.
4. `2026-06-17-fix-sync-mechanism`: 4/8.
5. `2026-06-16-harden-delegation-robustness`: 3/4.

What drove multi-round reviews (qualitative, from reading full logs of #1 and #2 above):
cross-artifact contradictions (proposal says X, spec/design says Y), scope creep vs.
explore-brief, and "the implementer would have to guess" ambiguities — NOT typos or
formatting. The reviewer's blocking issues were consistently substantive engineering
defects, not rubber-stamp busywork — this is evidence the review gate does real work,
at the cost of the correspondingly high round count for exactly the changes that were
build-the-review-gate-itself (recursive/self-referential changes are the hardest to review).

## Verify-pass yield (self-review vs. pro-verifier vs. flash-verifier)

Strong, repeated pattern (seen in ≥5 changes): **real defects at verify time are caught by
orchestrator self-review (eyeballing the diff), not by the deepseek pro/flash verifier
passes, which return clean far more often than not.**

Evidence:
- `2026-06-16-verify-multimodel-gate/notes.md`: self-review caught 1 whitespace nit; pro
  pass = no defects; flash pass = no defects.
- `2026-06-16-harden-delegation/notes.md`: primary (orchestrator) self-review caught a
  malformed hook-nesting bug in `.claude/settings.json` and a decisions.md
  self-contradiction; verifier passes not credited with catching anything in this log.
- `2026-06-18-lean-boot-context/notes.md`: "Both surfaced by the primary self-review (the
  pro/flash passes came back clean *after* the fixes)."
- `2026-06-21-premise-review-gate/notes.md`: a real rendering bug (new reviewer-mandate
  section landed inside a fenced code block, silently neutering the instruction) was
  "Surfaced by: orchestrator self-review (eyeballing the diff; `openspec validate` was
  green and blind to it)." Separately, the pro verifier pass DID catch one real 🟡 (a
  stale count needing update from "five" to "six").
- Zero-defect verify passes are the majority state: `2026-06-17-cap-status-log`,
  `2026-06-17-dedup-scaffold`, `2026-06-17-split-open-questions` (pro pass zero),
  `2026-07-03-checks-facts-split`, `2026-06-19-rename-memory-to-knowledge`,
  `2026-07-03-clarify-audit-tooling-surface` all explicitly log "no defects" at verify.

Interpretation: the propose-phase reviewer (pro model, MEDIUM/COMPLEX tier) is where real
issues get caught (see round-count section above — genuine 🔴 blockers). The POST-apply
multi-model verify gate mostly returns clean; its main confirmed catch in this sample is
1 cosmetic 🟡. This suggests the verify gate's marginal yield over self-review is currently
thin in this repo's own history — though it's a "gate that rarely fires" which is a
defensible design if it's meant as a backstop, not a primary catch mechanism.

## DISSENT / OVERRIDE (premise-review-gate)

Checked all 11 production `premise-review.md` files repo-wide (11 real post-freeze
invocations of the premise-review-gate feature, across `plans/*/premise-review.md` and
`openspec/changes/{active,archive}/*/premise-review.md`):
- **10/11 = PREMISE: AGREE.**
- **1/11 = OVERRIDE** (`plans/sync-deletion-manifest/premise-review.md`): operator
  explicitly waived the per-change flash pass ("skip the deepseek direction review pass"),
  citing that a shared portfolio-level direction gate already returned AGREE for the whole
  batch. Not a disagreement — an efficiency shortcut.
- **0/11 real DISSENT events.** The only DISSENT ever recorded was a deliberate smoke-test
  during premise-review-gate's own verify phase (`notes.md`: fed the reviewer a
  deliberately-bad plan to confirm the gate *can* refuse; it did). In 11 live production
  uses since, it has never actually blocked a real proposal.
- This matches an explicit forward-looking risk the authors flagged themselves
  (`2026-06-21-premise-review-gate/notes.md` §5): "Explore-altitude dissent calibration is
  unvalidated against real briefs... Monitor the first real explore-gate runs; if it
  over-fires on under-specified-but-sound briefs, tighten." The flip side not yet
  monitored: it may just never fire at all, at which point it's a cost with unclear
  detection value in practice so far — evidence is thin either way given only 11 samples.

## Operator bypass of the deepseek-delegation path (repeating pattern, ≥4 occurrences)

A distinct friction pattern from crashes: the operator repeatedly chose to run
apply/fix/verify steps on a Claude Sonnet subagent directly instead of the designed
deepseek/opencode delegation path — not because deepseek crashed, but by deliberate
operator override, "disclosed" each time per the workflow's honesty convention:
1. `2026-06-19-rename-memory-to-knowledge/notes.md`: "delegate the scaffold apply... to a
   Claude apply-executor subagent on Sonnet... NOT deepseek-v4-flash... the sanctioned
   fallback path, invoked deliberately." This run then had a genuine defect: the Sonnet
   apply-executor over-swept and hand-edited two main spec files in violation of OpenSpec
   convention (specs should only be touched by the archive step) — caught by the
   orchestrator, reverted.
2. `2026-07-02-mechanize-invariants/notes.md`: "implementation was executed by the Sonnet
   apply-executor subagent by explicit operator directive (deepseek-flash path deliberately
   not attempted); the deepseek pro+flash verifier passes were waived by explicit operator
   directive."
3. `2026-07-02-deterministic-tooling-layer/notes.md`: "all fixes by fresh Sonnet
   fix-executors per the operator override."
4. `2026-07-03-delegated-agent-safety/notes.md`: "apply/archive on Sonnet per this session's
   operator directive... Apply was a Sonnet subagent; a second Sonnet fix-executor handled
   the ephemeral-citation coherence fix."

Genuine crash/config-driven fallback (distinct from operator choice), found once:
- `2026-06-18-lean-boot-context/notes.md`: apply invoked with `--dir` pointed at the parent
  directory (for cross-repo reach) broke `.opencode/agents/` discovery →
  `agent "apply-executor" not found. Falling back to default agent`. Ran anyway on the
  default deepseek-v4-flash agent; operator accepted the result as-is (all deterministic
  gates passed). This is the only literal automatic-fallback-on-error instance found in
  this repo's history — everything else labeled "fallback"/"Sonnet" in review-logs turned
  out to be spec/mechanism text (describing the fallback design) or explicit operator
  overrides, not crash-triggered activations.

## Tasks re-scoping mid-apply

Weak/thin evidence in this repo: only `2026-06-21-premise-review-gate/tasks.md` matched
rescoping-style grep markers, and on inspection this was pre-freeze review commentary
("🟡3 no Effort field... Overruled") rather than a real mid-apply descope. No clear
instance found of a task being abandoned/descoped *during* apply in this repo. (Contrast:
`2026-07-02-deterministic-tooling-layer/notes.md` mentions "install-tools descope" via
commit history — `53d6590 Descope install-tools to go-install helper + security-scanners
reference` — a real descope, but recorded in commit messages, not tasks.md rescoping
markers.)

## plans/ dir (SMALL-tier)

3 SMALL-tier plans exist at `/home/pang/Projects/openspec-scaffold/plans/`:
`succession-hardening/`, `sync-deletion-manifest/`, `day-to-day-tooling/` — each has a
`premise-review.md` sibling (100% coverage). Verdicts: 2x AGREE, 1x OVERRIDE (see above).
No DISSENT among these 3.

## knowledge/lessons.md — process-related lessons (openspec-scaffold, 142 lines total)

Real, concrete process lessons (not domain bugs):
- **Executor overreach into neighbor changes** (§4): a deepseek-flash apply run briefed on
  one change also implemented an unrelated in-flight change, burying it mid-transcript.
  Required post-hoc diff-classification and surgical revert. Explicit conclusion: "the
  executor overran even with [an explicit 'don't touch other changes'] instruction —
  verification is the real defense."
- **Concurrent edits to shared working tree** (§4): a parallel session's apply "wiped W5's
  first apply entirely" by resetting the shared tree mid-work. Conclusion: independent
  parallel applies must use separate git worktrees, not the shared main tree — a real
  lost-work incident.
- **MEDIUM tier over-processed as COMPLEX** (§5): "W1 was confirmed MEDIUM by the operator
  but was given the full COMPLEX path (proposal + design + specs + tasks, 5 review passes)
  — over-processing and wasted review rounds." Explicit self-acknowledged waste.
- **openspec-reviewer bash-crash misdiagnosed as timeout** (§5): when the reviewer agent
  tries to call bash (denied by permissions), opencode hard-errors the whole run (~120s,
  exit 1, zero findings) — this looks like a timeout but isn't, and the fix (a read-only
  preamble in the prompt) is different from timeout handling. Documented specifically so
  it isn't escalated to Sonnet fallback unnecessarily.
- **`opencode debug skill` capture race** (§6): piping the ~120KB debug stream directly to
  grep races the output and silently returns a false-negative subset; must capture to file
  first.

## knowledge/audit-log.md

Does not exist in openspec-scaffold (confirmed absent from `knowledge/` listing). The
audit-cadence mechanism (`run-audit` skill, `composition-audit-cadence` /
`correctness-audit-skill` changes) is built here but audit-log.md itself is a
downstream-repo artifact per the design — no audit cadence to measure in the scaffold's
own repo.

## HANDOFF / context-exhaustion evidence

No `HANDOFF.md` or `handoffs-archive/` found. No stray `tmp/` debris (repo is clean per git
status). One relevant repo-internal signal: `2026-06-19-rename-memory-to-knowledge/notes.md`
flags a gitignored scratch file `tmp_rename-knowledge_handoff.md` used for a cross-repo
session handoff, to be discarded post-archive — i.e., ad hoc handoff files are used but
treated as disposable scratch, not tracked. Also noted: 4 currently-frozen-but-unapplied
changes (`lesson-check-ratchet`, `verify-stack-redirect`, `composition-audit-cadence`,
`correctness-audit-skill` — see recent git log) are NOT evidence of context exhaustion —
`knowledge/STATUS.md` / notes.md explicitly record this as a deliberate operator batching
decision ("Park verdict: parked apply blocks nothing... OW-5 itself waits on OW-2's
apply"), i.e. propose-many-then-sequence-applies-by-dependency, a deliberate practice, not
a stall.

## Git log bookkeeping ratio (openspec-scaffold)

- Total commits: 134
- "Archive X and reconcile project docs" commits: 25 (essentially 1 per archived change —
  27 archived change dirs exist, so archive+reconcile ceremony is ~93% consistently a
  dedicated commit)
- Standalone "Reconcile ..." commits (drift fixups outside the archive step): 5
- "Propose ..." commits: 10
- "Apply/Implement/Fix ..." commits: 22
- Broad bookkeeping-keyword match (reconcile|review-log|fix-hook|re-sync|sync scaffold|lint
  fix|propagat|archive|status log|convergence guard fix): 59/134 = 44%
- Narrow/precise (archive+reconcile only): 30/134 = 22%
- Reproducible via: `git log --oneline | grep -ciE "<pattern>"` in
  `/home/pang/Projects/openspec-scaffold`.
- Interpretation: roughly 1 in 5 commits in this repo is pure archive/reconcile ceremony,
  climbing to ~2 in 5 if sync/lint/propagation fixups are folded in. This is the meta-repo
  that builds the tooling, so this ratio is likely an upper bound vs. downstream product
  repos (to be compared against extrends/psc-monitor once their agents report back).

---

# CROSS-REPO: pre-existing internal synthesis (found, not authored by me)

`/home/pang/Projects/openspec-scaffold/knowledge/research/scaffold-gap-analysis-2026-07/`
(dated 2026-07-10, the commit immediately preceding this session) is a prior "Fable
principal-engineer pass" that independently mined the exact same friction question from
both downstream repos' audit trails. Treating this as strong corroborating secondary
evidence (it read primary sources I'm independently sampling too) — cite it, don't just
restate it as my own finding.

## Key quantified claims from SYNTHESIS.md / scaffold-procedures.md (their gate-ledger reconstruction, re-derived from SKILL.md text, not measured runtime — flagged as such in the source)

**Per-tier model-pass cost (reconstructed from `openspec-verify-change/SKILL.md` +
AGENTS.md tier rules, baseline / worst-case):**
- SMALL: ~4 model passes baseline (3 delegated + 1 self-review) / ~5 worst-case
- MEDIUM: ~9 baseline (6 delegated + 3 self-review) / ~12+ worst-case (propose reviewer
  re-review loop up to 3x + conditional security gate)
- COMPLEX: ~14 baseline (9 delegated + 5 self-review) / ~20+ worst-case (each of 3 propose
  artifacts up to 3x re-review)

**Central redundancy finding (their GAP 5, matches what I independently found in
openspec-scaffold's own notes.md above):** the verify stack's self→pro→flash sequence
executes the **identical procedure** (full diff read, full suite re-run, eyeball real
output, live smoke) three times, differentiated ONLY by model weight — SKILL.md's own text
concedes "a second pro pass adds little" model diversity for OpenCode orchestrators. Each
of the 3 passes independently re-runs the full test suite — the single most expensive
redundancy in the whole gate ledger for MEDIUM/COMPLEX changes.

**Evidence the in-loop gates are missing real bugs (their central thesis, sourced from
downstream audit dossiers, corroborating my own scaffold-repo finding that self-review
catches more than the pro/flash verifier passes do):**
- Both extrends and psc-monitor independently reinvented a bespoke, heavier multi-wave
  correctness-audit program (CHARTER → CENSUS → wave FINDINGS → remediation) *on top of*
  the standard verify gate — "the strongest evidence the standard gate was judged
  structurally insufficient for this class of defect" (psc-issues.md).
- extrends: "no runtime-correctness audit had ever executed on this repo" across ~45
  archived feature changes before Wave 1 was hand-built. 4 waves total, approx.
  7/5/8/8 defect classes and ~29/19/22/35+ findings per wave (counts are the analyst's own
  reconstruction — the audit corpus deliberately never self-reports tallies), plus a
  separate test-audit (~7 classes / ~110+ findings, including 3 confirmed cases where a
  weak test concealed a real, still-shipping product bug).
- psc-monitor: Wave 1 = 12 verified + 14 leads; Wave 2 = 11 verified + 19 leads (~55 items
  total across 2 waves); a separate test-quality audit found 5 FLAKY / 18 WEAK / 12
  BLOATED / 1 FRAGILE / 6 PARAM tests + 27 hard-missing/13 partial-missing test scenarios +
  1 confirmed production bug hiding behind zero exception-path coverage.
- Concrete named recurrences of the *same bug shape* surviving multiple audit passes
  (i.e., "found," "lessoned," and then found again in a sibling code path): psc-monitor's
  B5 unbounded-`fetchall()` livelock (2026-06-12) recurred and was re-found by hand in
  Wave 2 (CA-W2-05); psc-monitor's F16 fixture/production transaction-semantics mismatch
  recurred as an `autocommit=TRUE` pattern; extrends' ground-truth-label-destruction bug
  recurred one wave apart (wave 3 `labels_io.py` → wave 4 `console/labels_io.py`).
- One explicit case where the standard gate DID work as a counter-example/control: extrends
  `lessons.md`'s `harden-pytrends-validation` incident — 722 mock-patched tests passed
  green on a bad assumption the reviewer had wrongly "confirmed," but the mandatory
  **live-smoke step** of verify caught it before ship. Cited as "the exception, not the
  rule."
- Remediation status differs sharply between repos: extrends has deferred remediation for
  ALL 4 waves (zero fixes shipped as of 2026-07-10, deliberately, per an explicit
  "audit-first-remediation-deferred" decision) vs. psc-monitor which had already shipped
  some remediation waves by the time of this analysis.

**What they found NOT to be a gap** (worth including for balance/honesty): tiered
process + delegation harness + archive-as-handoff token economy is "sound... leave it";
premise/direction gates are "cheap relative to building the wrong thing... keep"; the
simplicity/security gates are "genuinely lens-diverse, diff-only, no suite rerun."

## My assessment of this source
This is a self-produced internal document (by a prior "Fable" session of this same
workflow, i.e., not independent outside evidence) so it shares any systematic bias in how
this project narrates its own friction — but its method (re-deriving numbers from source
artifacts rather than asserting) and its explicit "these are my own reconstructed counts,
not sourced tallies" caveats make it a credible, well-labeled synthesis. I'm treating its
claims as corroborating, not load-bearing on their own — cross-checked against my own and
the two background agents' independent primary-source sampling below.

---

# REPO 2: extrends — DONE (background agent; full detail in extrends-friction.md, same dir)

Headline numbers (42 archived changes):
- Review rounds: mode=1, median=1 for proposal/tasks/spec; design median=2. Long tail:
  tasks max=7, spec max=6. Worst change: 2026-06-28-notable-emergence-detector = 20 total
  rounds (proposal 3, design 4, spec 6, tasks 7), incl. a mid-review scope narrowing.
- Delegation failures: ~8/42 changes (~19%) had a genuine crash/timeout-driven
  deepseek→Sonnet escalation (plus 2 more that were deliberate operator routing choices).
  Example: fix-watermark-integrity — deepseek flash truncated mid-exploration TWICE
  (process killed, no work landed) → Sonnet per failure ladder. add-run-health-alerting:
  deepseek timed out (exit 124, no edit) on a mechanical de-indent fix.
- DISSENT: 0. non-convergence: 0. "PARTIAL" 65 hits but almost all domain vocabulary
  (partial collection/backfill), not workflow salvage events — false-positive category.
- VERIFY YIELD (matches scaffold finding, now confirmed in 2nd repo): of 11 changes with
  explicit verify sections, 4 caught real CRITICAL bugs at verify — ALL 4 attributed to
  the ORCHESTRATOR's own self-review/behavioral probe, none to the pro/flash multi-model
  gate (which overwhelmingly returned "Defects: None"). The gate's one positive catch in
  sample: a doc-accuracy nit (speed-up-notability-title-probe flash pass). Its one big
  NEGATIVE: 2026-06-28-notable-emergence-detector — the "read-only" pro verifier pass had
  bash:allow and RAN a live scoring job + 12,005-row backfill against production
  trendscope.db, mutating run history; required operator-authorized revert + DB snapshot
  (notes.md:139-146; root cause: prompt forbade re-scoring but not DB writes). Also:
  flash verifier "emitted garbled/empty output on two attempts" on add-aggregation-fact-table.
- Tasks re-scoping: essentially disciplined — 813 [x] vs 2 [ ] checkboxes; only ~1 genuine
  mid-apply rescope (audit-correctness-wave2 inv-05 over-firing) + 1 descope-to-follow-on.
- plans/ shadow workflow: 68 git-tracked files, actively growing (newest 2026-07-11) —
  directly contradicts OPENSPEC_MIGRATION_PLAN.md Phase 5 "prune plans/ to roadmap-only,"
  which never stuck. 13 premise-review.md siblings; no real OVERRIDE/DISSENT events
  (mentions are "no override needed" gate boilerplate). Interpretation: operators route a
  meaningful fraction of work around the heavyweight lifecycle via plans/.
- lessons.md: 4/7 entries process-related. Star incident: harden-pytrends-validation —
  722 green mock tests + a reviewer that "confirmed" a nonexistent library kwarg (reviewer
  runs bash:deny, cannot verify empirics) shipped toward a real regression; caught only by
  verify live-smoke. Also: "deepseek burns most of its budget re-deriving context the
  orchestrator already has" (slice-briefs lesson); executor exit codes unreliable ("fixes
  have repeatedly completed their work yet exited 1 at teardown" — judge from disk).
- audit-log.md: n=1 entry ever (2026-07-03), then an explicit gap note — the lightweight
  deterministic audit cadence lapsed 6 days later, superseded by the heavyweight 4-wave
  correctness audit. Wave dossiers GREW 84.6KB→191.6KB (wave1→wave4) while lead counts
  fell 14→12 — per-finding overhead rising, not falling, despite process experience.
  Playbook also records: CI silently red "for weeks"; a pro reviewer hallucinated a
  nonexistent tasks-template requirement mid-review (manually overruled, round 4).
- Context exhaustion: formal knowledge/HANDOFF.md mechanism exists explicitly for
  "context exhausted mid-change" (knowledge/README.md:26-28), built to supersede
  "ad-hoc multiple root-level HANDOFF files" — the mechanism's existence is itself
  evidence of recurring pain. Confirmed real usage: commits 1c7a0c4/4fb0c22 (wave-2 apply
  handoff, written + absorbed). 21 *handoff* files repo-wide (15 in plans/), plus
  tmp/ session debris (tmp/handoff-accuracy-program.md, tmp/test-audit-handoff.md).
- Git ratio: 520 commits; 99 (19.0%) match bookkeeping keywords (reconcile 56, archive 67,
  sync scaffold 11, propagat 3 — overlapping). Upper-bound estimate; archive commits are
  required process, and prose-maintenance cost inside feature commits is unmeasured.

# REPO 3: psc-monitor — DONE (background agent; full detail in psc-monitor-friction.md, same dir)

Headline numbers (13 archived + 2 active changes):
- Review rounds: proposal mode=1/max=2; design mode=2/max=3
  (tier-grade-company-watch-alerts); tasks mode=1/max=2. Worst total cycles:
  audit-remediation-wave-e2 (active) = 8 cycles ("7 pro rounds" per commit a41a224);
  historical-reports = 7; add-psc-suppression = 7 (every artifact needed exactly 2 rounds
  except tasks; its notes.md also records an opencode apply TIMEOUT — exit 124 at the 600s
  ceiling AFTER finishing implementation but before checking off tasks.md, reconciled from
  disk, no Sonnet needed).
- Delegation failures: 2/13 archived changes had real crash-driven Sonnet fallbacks —
  harden-stripe-webhook/notes.md:162 (flash timed out, Sonnet finished) and
  historical-reports/notes.md:15-18 (flash timed out TWICE with empty output → Sonnet).
  One more Sonnet use was explicit operator routing, "Not a Sonnet fallback."
  DISSENT=0, non-convergence=0.
- Verify yield: modal outcome = pro+flash both clean. Real defects in only 2 of ~13 verify
  sequences: deploy-security-posture/notes.md:42-44 (FLASH caught a Secure-cookie test
  mismatch that pro missed) and tier-grade-company-watch-alerts/notes.md:29-31 (Sonnet
  verifier pass A found a real test-coverage gap). NO case where pro caught something
  flash/Sonnet missed.
- Tasks re-scoping: zero rescope markers across all 21 tasks.md. e1 (29/29 unchecked) and
  e2 (19/19 unchecked) are frozen-but-unapplied = paused before apply (deliberate), not
  mid-apply abandonment.
- plans/: 25 plan files + 12 premise-review siblings (naming inconsistent). One REAL gate
  breakdown: plans/audit-remediation-wave-e3/premise-review.md — deepseek review killed by
  operator mid-run before ANY review text emitted ("77KB of harness events, zero text
  parts") → forced "PREMISE: AGREE (operator override — no machine verdict exists)".
  1 of 8 inspected premise-reviews (12.5%) is this failure mode.
- lessons.md (134 lines): process lessons ~= extrends' (shared scaffold lineage): slice
  applies to fit the 600s wrapper; fold fixes into next slice; retry timed-out reviewer
  once with tight brief; judge completion from disk, not exit code ("scoped opencode run
  fixes have repeatedly completed their work yet exited 1 at teardown").
- audit-log.md: DOES NOT EXIST anywhere in the repo. correctness-audit-2026-07/FINDINGS.md
  = 56 unique finding IDs / 4009 lines; test-quality-audit graded ~167 behaviors → 27
  zero-coverage gaps but only TWO confirmed production bugs — heavy audit effort, modest
  confirmed-bug yield.
- Handoffs: knowledge/HANDOFF.md had 5 create/delete cycles in git history (currently
  absent). No narrative literally says "ran out of context"; usage looks like planned
  session-boundary chunking.
- Git ratio: 218 commits; 42/218 (19.3%) narrow bookkeeping keywords; 66/218 (30.3%)
  broader set incl. checkpoint/handoff/status.

---

# CROSS-REPO SYNTHESIS (final)

## Verify-pass yield table (reconstructed, all three repos)

| Repo | Verify sequences w/ recorded outcomes | Real defects caught at verify | By self-review | By pro pass | By flash pass | By Sonnet pass |
|---|---|---|---|---|---|---|
| openspec-scaffold | ~14 notes.md w/ defect sections | ~5 changes had verify-time defects | ~5 (all) | 1 cosmetic 🟡 (stale count) | 0 | n/a |
| extrends | 11 | 4 CRITICAL | 4 (all) | 0 (+1 NEGATIVE: mutated prod DB) | 1 doc nit | n/a |
| psc-monitor | ~13 | 2 | 0 | 0 | 1 (Secure-cookie test) | 1 (coverage gap) |

Net: across ~38 recorded verify sequences in 3 repos, the pro-tier verifier pass has ~1
cosmetic catch and 1 production-DB-mutation incident to its name; flash has 2 modest
catches; orchestrator self-review caught essentially all the real bugs (~9-10). The
internal SYNTHESIS.md (GAP 5) independently reached the same verdict from the audit-dossier
angle: triple same-lens verify passes let the audit-found defect classes through anyway.

## Repeating friction patterns (each seen ≥2 times, cross-repo)

P1. Multi-model verify redundancy (all 3 repos + internal synthesis) — see table.
P2. deepseek crash/timeout → Sonnet escalation: extrends ~8/42 (~19%), psc-monitor 2/13
    (~15%), scaffold 1 auto-fallback (agent-discovery break) + ≥4 operator-choice
    overrides. Failure ladder works but costs a wasted 600-780s budget + re-brief each time.
P3. Premise/direction gate never dissents in production: 0 DISSENT across all 3 repos
    (scaffold 10/11 AGREE + 1 waiver-override; extrends 13 premise files all AGREE-ish;
    psc-monitor incl. 1 no-verdict override). Only DISSENT ever = deliberate smoke test.
P4. Exit-code unreliability / judge-from-disk: identical lesson in scaffold lessons.md
    ("Exit 0 ≠ success"), extrends lessons.md ("completed their work yet exited 1 at
    teardown"), psc-monitor lessons.md (same wording, shared lineage). Plus psc-suppression
    exit-124-after-work-done. ≥4 independent recordings.
P5. Apply timeout ceiling (600s) forces slicing: extrends session-8 lesson + psc-monitor
    slicing lesson + psc-suppression exit 124 + extrends run-health-alerting exit 124.
P6. Handoff-file ecosystem for session boundaries: extrends 21 handoff files + formal
    HANDOFF.md mechanism w/ confirmed use; psc-monitor 5 HANDOFF.md lifecycles; scaffold
    tmp_*_handoff.md scratch. Mostly planned chunking, occasionally context exhaustion.
P7. Reviewer hallucination/overreach requiring manual overrule: extrends pytrends kwarg
    "confirmation" (bash:deny reviewer affirming unverifiable empirics) + hallucinated
    tasks-template requirement (wave2 round 4 REJECTED); scaffold premise-review-gate
    tasks round ("openspec validate may be phantom" — false, overruled) + reviewer
    bash-crash lesson. ≥4 events.
P8. Delegated-executor overreach: scaffold neighbor-change implementation (W3/W5 incident)
    + Sonnet main-spec hand-edit (rename-memory-to-knowledge); extrends read-only verifier
    mutating production DB (12,005 rows). 3 events.
P9. Heavyweight lifecycle routed around: extrends plans/ = 68-file shadow workflow
    contradicting the migration plan's prune intent; extrends audit-log cadence abandoned
    after n=1; scaffold MEDIUM-as-COMPLEX over-processing lesson. Plus propose-then-pause
    batching (4 scaffold + 2 psc-monitor changes frozen at apply).

## Bookkeeping-to-feature commit ratios
- extrends: 99/520 = 19.0% (narrow keywords)
- psc-monitor: 42/218 = 19.3% narrow, 66/218 = 30.3% broad
- openspec-scaffold: 30/134 = 22% narrow (archive+reconcile), 59/134 = 44% broad
Downstream repos converge on ~19-20% narrow / ~30% broad; the meta-repo is higher (44%
broad) as expected. All are upper-bound keyword estimates; archive commits are mandatory
process by design.
