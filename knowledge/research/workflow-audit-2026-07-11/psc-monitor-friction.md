# psc-monitor workflow friction audit — running notes

## 1. Review rounds per artifact
Parsed via /tmp/.../psc_parse_rounds.py (word-boundary regex to avoid "openspec-reviewer" false
positives on "spec"). 15 review-log.md files (13 archived + 2 active e1/e2).

Distribution of rounds-to-freeze:
- proposal: n=10, values [1,1,1,1,1,1,2,2,2,2], mode=1(x6), median=1, max=2
- specs: n=7, values [1,1,1,2,2,2,2] (after correcting e1 false-positive "spec requirement" phrase
  in a design-review header, true e1 specs=1 not 3), mode split 1/2, median=~1-2, max=2
- design: n=10, values [1,1,2,2,2,2,2,2,2,3], mode=2(x7), median=2, max=3
  (max: 2026-06-21-tier-grade-company-watch-alerts, design.md Round1,2,3-FINAL)
- tasks: n=15, values mostly 1 or 2, mode=1(x8), median=1, max=2

Top 5 by total review cycles (sum of per-artifact rounds-to-freeze):
1. audit-remediation-wave-e2 (ACTIVE/paused) — 8 (proposal2,specs2,design2,tasks2). Commit
   a41a224 self-reports "7 pro rounds".
2. 2026-06-16-historical-reports — 7 (2,2,2,1)
2. 2026-06-18-add-psc-suppression — 7 (2,2,2,1)  [flagged outlier]
4. 2026-06-20-audit-test-suite-quality — 6 (2,-,2,2)
4. 2026-06-21-tier-grade-company-watch-alerts — 6 (1,1,3,1)
4. 2026-07-06-audit-wave0-wave1 — 6 (1,1,2,2)
4. audit-remediation-wave-e1 (ACTIVE/paused) — 6 (1,1,1,1 after correction... commit says "4 pro rounds")

add-psc-suppression outlier check: raw case-insensitive "Round" hits = 31 (grep -o -i 'Round' | wc -l);
with \bRound\b word-boundary = 28. Caller cited "26" from an earlier/different grep pattern — same
ballpark, confirms genuine outlier. Structurally: EVERY artifact needed exactly 2 rounds except tasks
(1) — proposal 1->2, specs 3->4, design 5->6, tasks 7 (global sequential numbering in this file, unlike
most files which reset per-artifact). Notably tasks.md passed clean in 1 round while everything upstream
needed a re-round — unusual (most other changes show design/proposal as the rounds that redo).
Narrative: notes.md documents an opencode apply-executor timeout (exit 124, 600s ceiling) after
completing implementation but before checking off tasks.md; orchestrator reconciled from disk, no
Sonnet fallback needed.

## Friction markers (grep -l across review-log.md + notes.md, archive + e1/e2)
- PARTIAL: 10 files
- timeout: 9 files
- crash: 7 files (mostly DOMAIN crashes — e.g. B-D-36 "hung restic crashes the health sentinel" —
  not agent/tooling crashes; only exception is process-level opencode timeouts described as
  near-crash, see below)
- fallback: 22 files (mostly "(FALLBACK — used when...)" agent-definition boilerplate or "No
  Sonnet fallback needed" — see below for actual invocations)
- Sonnet: 18 files
- DISSENT: 0 files (repo-wide)
- non-convergence: 0 files
- escalate: 3 files (audit-wave0-wave1 review-log; wave-e1/e2 notes — all are the "Escalate back
  to Fable ONLY if verify surfaces a design-level defect" propose->apply handoff clause, not actual
  escalation events)

### Actual Sonnet-fallback invocations (real deepseek/opencode failures forcing Sonnet), vs.
non-events ("no Sonnet fallback needed" appears in ~10 changes — the common case):
1. 2026-06-16-harden-stripe-webhook (notes.md:162-165): deepseek-v4-flash FIX run timed out
   (exit 124, no changes) -> Sonnet fallback subagent completed it. Also: 2 independent
   deepseek-v4-pro VERIFY runs timed out (SIGKILL, buffered output lost) before a 3rd tighter
   run succeeded — "an opencode-wall pattern this session, not a code issue".
2. 2026-06-16-historical-reports (notes.md:15-18): deepseek-v4-flash TIMED OUT TWICE (opencode
   run exit 124, empty output, zero file changes both times, "likely stalled exploring") ->
   fell back to Sonnet subagent apply-executor (general-purpose type, model:sonnet, since
   apply-executor agent def is deepseek-only).
That's 2 confirmed real Sonnet-fallback events out of 21 archived + 2 active changes (~9%).

### Process timeouts that did NOT need fallback (executor finished the real work, just missed
the exit/checkbox housekeeping before the wrapper killed it):
- 2026-06-18-add-psc-suppression: flash apply hit 600s ceiling after finishing impl + green
  suite, before checking off tasks.md.
- 2026-06-19-convert-appointment-dates-to-date: flash timed out on task 6.1 (14.7M-row ALTER
  TYPE migration exceeds executor time budget); orchestrator ran the migration manually
  (operational, not code).
- 2026-07-09-audit-remediation-wave-a: flash hit 600s ceiling TWICE, both on productive/complete
  runs.
- 2026-07-06-audit-wave2-signal-path: hit 1200s wrapper during post-completion cosmetic checks;
  all material output already on disk.
=> Pattern: opencode's wall-clock ceiling (600s/1200s) is tripped often (5+ distinct events across
4 changes) but almost never actually loses work — the orchestrator recovers from disk. Real
fallback-triggering failures (empty output / stalled exploration) happened only 2x.

### Non-Sonnet-fallback but deliberate operator ROUTING to Sonnet (not a failure):
2026-07-06-audit-wave2-signal-path notes.md: "2026-07-06 — executor switch mid-apply (operator
ruling). After slice 2b-5 (task 3.3), the operator ruled: use Sonnet subagents for the remainder
of the apply phase... Not a Sonnet fallback (no deepseek failure occurred — all deepseek slices
ran clean); it is a direct operator routing instruction." Also 2026-06-21-tier-grade-company-
watch-alerts used Sonnet as apply/fix/verify executor throughout by operator directive (not
default), with disclosed tradeoff (less cross-family reviewer diversity).

## Verify-pass yield reconstruction (pro vs flash, which catches real bugs)
Across ~13 archived changes with "verifier pass" language in notes.md:
- Most common outcome: BOTH pro and flash return READY / zero defects (add-psc-suppression,
  audit-test-suite-quality, harden-stripe-webhook 06-20, audit-wave0-wave1 post-fix,
  name-normaliser-audit, email-deliverability). I.e. verify passes finding literally nothing is
  the modal outcome.
- 2026-06-30-deploy-security-posture (notes.md:42-44): pro pass judged READY ("the only
  browser-compliant option"); FLASH pass returned NEEDS REVISION on the same item (Secure-cookie
  attribute test-vs-prod mismatch) — artifacts were corrected, then cleared to READY. This is the
  one clean instance of flash catching something pro missed/accepted.
- 2026-06-21-tier-grade-company-watch-alerts (notes.md:4,29-31): used TWO SONNET verifier passes
  (operator directive, not deepseek default). Pass A found a real coverage gap — email-label test
  only exercised watch_entry_type='person', so the company branch of core/email_sender.py had zero
  test coverage; fixed. Pass B (re-run) READY. Real bug caught at verify, but by Sonnet not
  pro/flash.
- 2026-07-06-audit-wave2-signal-path: pro pass READY zero defects; flash pass AND simplicity gate
  were SKIPPED entirely by operator ruling mid-verify (recorded as deliberate, not omission).
- name-normaliser-audit: needed a flash RE-CONFIRMATION pass after a fix (implying first pass
  surfaced something not itself narrated as a defect count, but the re-confirmation is evidence a
  fix cycle happened between passes).
Overall: in this sample, clean-across-the-board is the norm; real defects were caught in 2 of
~13 verify sequences (deploy-security-posture via flash; tier-grade-company-watch-alerts via
Sonnet pass A) — roughly 15% hit rate for "verify pass finds a real issue", and no case where
PRO caught something flash/Sonnet missed; if anything flash/Sonnet were the ones that caught
things in the 2 exceptions found.

## 2. Tasks.md re-scoping
- grep for descoped/deferred/abandoned/removed-from-scope across all 21 tasks.md (archive + e1/e2):
  ZERO hits for "descoped", "abandoned", "removed from scope". "deferred" hits are just: (a) a
  stale header note in 2026-06-16-harden-stripe-webhook/tasks.md ("apply deferred — operator
  chose scope plan only, build later") that turned out NOT to reflect final state — that change
  was fully applied later (17/17 tasks checked in the end, just delayed for a second review); and
  (b) "LEAD-deferred" as an audit-finding disposition label (dossier vocabulary), not a task
  re-scoping event.
- No non-standard checkbox states ([~] etc.) found anywhere — repo convention is strictly [x]/[ ].
- Broader grep for softer re-scoping language ("scope was narrowed/reduced/cut/dropped ... during
  apply") across all notes.md/tasks.md: ZERO hits.
- CONCLUSION: genuine mid-apply re-scoping is essentially ABSENT as a documented phenomenon in
  psc-monitor's 19 archived changes. Evidence is thin/absent here — being explicit per instructions.
- What IS real: audit-remediation-wave-e1 (29/29 tasks unchecked) and -e2 (19/19 tasks unchecked)
  are both fully un-applied — proposal/specs/design/tasks all frozen via review, zero apply
  progress. This is a "paused before apply begins" state, not re-scoping mid-apply. Confirmed via
  git log: "3befc19 E1 propose complete: proposal + specs + design + tasks frozen (4 pro rounds,
  PREMISE: AGREE)" and "a41a224 E2 propose complete: ... frozen (7 pro rounds, PREMISE: AGREE)" —
  both followed by later commits (Wave G memos etc.) with no apply/verify/archive commits for
  E1/E2 yet as of HEAD (dcb2ffb).
- Also notable: 2026-06-16-harden-stripe-webhook (the deferred one) vs 2026-06-20-harden-stripe-
  webhook are two DISTINCT change proposals for the same subsystem, sourced from two different
  adversarial reviews 4 days apart — not the same change re-scoped, but sequential follow-on
  hardening waves on the same file.

## 3. Plans dir (SMALL-tier)
/home/pang/Projects/psc-monitor/plans/ EXISTS. 25 non-premise-review .md files (or dirs) +
12 premise-review siblings (naming inconsistent: "<name>-premise-review.md",
"<name>.premise-review.md", or "<name>/premise-review.md" in a subdir). Plus a
plans/session-handoffs/ dir (currently EMPTY — handoffs get absorbed+deleted by the next
session; only 1 commit ever added files there: b788651).
grep "OVERRIDE"/"DISSENT" across plans/:
- 2 boilerplate "No DISSENT/override needed" clean-pass attestations (billing-ui,
  deploy-path-parameterization, frontend-test-harness).
- plans/audit-remediation-wave-e3/premise-review.md is the one REAL finding: "Reviewer: none —
  the deepseek/deepseek-v4-pro direction-gate run was started 2026-07-10 and killed by the
  operator mid-run before any review text was emitted (77KB of harness events, zero text parts,
  no verdict block; nothing salvageable under the partial-output rule)." Operator ruling:
  "assume the premise is correct" -> `PREMISE: AGREE (operator override — no machine verdict
  exists)`. This is a genuine reviewer-gate breakdown requiring a manual bypass.
- Cross-check: of the 8 premise-review.md files inspected (b, c, e3, e4, e5, g,
  audit-correctness-quality, + billing-ui/deploy-path/frontend-test-harness proto-ones), 7 show
  "Fallback check: clean — no 'Falling back to default agent' in stderr; real reviewer ran." and
  only e3 shows the reviewer-gate failure above. ~1-in-8 (12.5%) real breakdown rate for this
  specific gate, directly evidenced.

## 4. knowledge/lessons.md (134 lines, read in full)
PROCESS-related lessons (about the workflow/agent behavior, not domain bugs):
- "OpenCode delegation — operational notes" (lines 5-33): (1) slice big tier-3 applies
  sequentially by task-group, gated by targeted tests — the 600s/300s timeout wrappers are hard
  ceilings, size slices to fit; (2) fold a scoped fix into the NEXT slice's brief instead of a
  separate fix run — "sequential, no concurrent writers, one fewer invocation"; (3) retry a
  timed-out reviewer ONCE with a tight brief (exact files named, facts front-loaded, exploration
  forbidden) — "deepseek burns most of its budget re-deriving context the orchestrator already
  has"; (4) detect completion via EXIT=$? sentinel file, never pgrep (self-matches); (5) judge
  success from disk (git diff/tests), not exit code — "scoped opencode run fixes have repeatedly
  completed their work yet exited 1 at teardown."
- "Audit LEAD graduation — adversarial refutation playbook" (lines 78-125): pays for itself
  quantitatively — "of 10 LEADs graduated in one session, 4 were materially corrected (1 fully
  refuted, 1 had its severity-driving harm refuted, 1 was broadened, 1 had a factual error)."
  Also: cap concurrency <=4 subagents when scratch DBs involved (Postgres max_connections=20);
  standard opencode hardening (--dir, </dev/null, timeout -k, EXIT sentinel, grep stderr for
  "Falling back to default agent"); a lesson on refuters mislabeling "REFUTED" when they actually
  confirm-the-mechanism-but-dispute-severity (happened twice in one batch, requires orchestrator
  overrule).
- B5 reload livelock postmortem (lines 35-77) is mostly a DOMAIN incident (unbounded query OOM'd
  prod), but items 7/9 are process-adjacent: isolate long-running PR work in its own git worktree
  from an unattended batch importing the main tree; the permission gate correctly blocked a mass
  recovery UPDATE, costing "minutes" for a one-word authorization + audit trail.
- F16 transaction-visibility lesson (lines 127-134) is a pure domain/code-correctness lesson, not
  process.

## 5. knowledge/audit-log.md
Does NOT exist anywhere in the repo (`find . -iname "audit-log*"` returns nothing). Being
explicit per instructions: this file is ABSENT despite multiple audit waves having occurred
(wave0-wave1, wave2-signal-path, remediation-wave-a through g). No single running audit-cadence
log was found; audit history instead lives distributed across openspec/changes/archive/*
notes.md/review-log.md and knowledge/research/*.

knowledge/research/correctness-audit-2026-07/FINDINGS.md: 4009 lines, 56 unique CA-W finding IDs.
Verdict-label mention counts (labels recur through discussion, NOT unique-finding counts):
VERIFIED-BY-trace x82, VERIFIED-BY-repro x58, REFUTED x44, LEAD x31.

knowledge/research/test-quality-audit/FINDINGS.md (2026-06-20, 358 lines): graded ~167 cataloged
behaviors across 4 domains. Yield: 0 forced-green, 0 mirrors-implementation, 5 confirmed FLAKY,
18 confirmed WEAK assertions, 12 confirmed BLOATED arrange, 1 FRAGILE, 6 PARAM, 27 behaviors with
zero test coverage (hard MISSING), 13 partial-coverage gaps. Executive summary states "two
confirmed production bugs" surfaced (one is B-D-36, a hung-restic-crashes-health-sentinel bug,
"the only production-safety bug found" per notes.md). This maps to a heavy audit-authoring/grading
effort (4 domain behavior catalogs + per-domain sources-read files + grading + ratification dirs)
yielding a small number of real production bugs — consistent with "high review overhead, modest
direct-bug yield" for this wave; most of the yield is test-suite-quality metadata (weak/bloated/
missing coverage), not shipped-code defects.

## 6. Handoff / context-exhaustion evidence
- `find -iname "*handoff*"`: only `plans/session-handoffs` (currently empty).
- `find -path "*/tmp/*"`: `tmp/outstanding-work.md` (613 lines, 46KB) and
  `tmp/remediation-wave-draft.md` (301 lines, 29KB) — gitignored per commit 544324f "Gitignore
  tmp/ (operator-local planning scratch dir)".
- knowledge/README.md:28 documents the mechanism explicitly: "a session writes
  `knowledge/HANDOFF.md` when it must hand off before archive (e.g. context exhausted
  mid-change)... The next session absorbs the handoff and deletes it. There is exactly one such
  file — this supersedes ad-hoc multiple root-level HANDOFF files."
- knowledge/HANDOFF.md does NOT currently exist (absorbed/deleted, consistent with mechanism).
  Git history: 5 commits added it, 5 deleted it (13 total touching commits) — 5 discrete
  create/delete handoff cycles over the project's life.
  Broader "*HANDOFF*"/"*handoff*" filename-add commits: 9 total (includes the pre-consolidation
  ad-hoc root-level ones, e.g. a stale `tmp-stripe-review-handover.md` referenced in
  2026-06-16-harden-stripe-webhook/notes.md).
- Searched knowledge/, openspec/changes/, plans/, tmp/ for "context exhausted / ran out of
  context / session limit / picking up where" (beyond the one README.md definition): ZERO
  narrative hits. i.e., the mechanism is documented and evidently used (5 cycles), but no
  session ever narrates *why* — no notes.md/review-log.md says "I ran out of context, handing
  off." Also searched "context window/budget/ran low/limit" repo-wide: zero hits.
- The `plans/session-handoffs/` + `plans/wave-e-handoffs/` files referenced in
  tmp/outstanding-work.md (e.g. "session-propose-e1.md", "session-propose-e2.md") look like
  DELIBERATE, planned session-boundary chunking of large multi-wave work (Wave E's 5 briefs
  split across sessions) rather than reactive context-exhaustion recovery — the tmp file says
  "Session handoff prompts prepared 2026-07-10" ahead of time, not after a crash.
- CONCLUSION: context exhaustion has a defined, evidently-used escape hatch (5 cycles) but zero
  direct narrative evidence in this repo of it being *forced* by running out of context (as
  opposed to planned multi-session sequencing) — evidence for the "crisis" framing is thin.

## 7. Git log bookkeeping ratio
Total commits: `git log --oneline | wc -l` = 218

Per-keyword counts (`git log --oneline | grep -ciE "<kw>"`):
- reconcile: 26
- review-log: 0
- fix-hook: 0
- re-sync: 0
- archive: 24
- sync scaffold: 7
- lint fix: 0
- propagat: 3
UNION (any of the above, `grep -ciE "reconcile|review-log|fix-hook|re-sync|archive|sync scaffold|lint fix|propagat"`): 42/218 = 19.3%

Supplementary (not in the original ask, added for context) keywords checkpoint/handoff/"record
operator"/status: checkpoint=6, handoff=18, "record operator"=3, status=7.
UNION incl. supplementary: 66/218 = 30.3%.

Caveat: these are subject-line keyword matches on `git log --oneline`, a crude proxy — commit
message conventions in this repo are narrative/descriptive (e.g. "Wave G memos complete: 9 picks
+ 2 Wave-D riders recorded, pro gate PREMISE: AGREE...") rather than terse, so keyword hits likely
UNDER-count true bookkeeping share (many propose/reconcile/archive commits use synonyms not in the
list, e.g. "Archive audit-remediation-wave-a and reconcile project docs" hits both "archive" and
"reconcile" — counted once in union). ~19-30% of all commits are process/bookkeeping rather than
direct feature/fix work, by this proxy.
