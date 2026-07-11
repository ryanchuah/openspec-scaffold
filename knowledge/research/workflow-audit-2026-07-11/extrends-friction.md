# Extrends Workflow Friction Audit - Running Notes

## SECTION 1: Review rounds per artifact

42 archived changes, review-log.md present in all 42; notes.md in 43 (one extra, likely an active/unarchived one or duplicate).

### Distribution of max-rounds-to-freeze per artifact (computed via /tmp .../parse_rounds.py + stats.py, header formats vary: "## Round N — <artifact>", "## <artifact> — Round N", "## <artifact>.md — self-review — PASS")
- proposal: n=28 measured, mode=1, median=1, max=3
- design: n=25 measured, mode=1, median=2, max=4
- tasks: n=41 measured, mode=1, median=1, max=7
- spec: n=22 measured, mode=1, median=1, max=6

Most changes freeze every artifact in a single round (self-review PASS, no findings). tasks.md is the artifact most likely to blow past 1 round (median still 1 but long tail to 7).

### Top 5 changes by TOTAL rounds across all artifacts:
1. 2026-06-28-notable-emergence-detector: 20 rounds (proposal 3, design 4, spec 6, tasks 7)
2. 2026-07-04-audit-correctness-quality: 11 rounds (proposal 1, design 2, spec 3, tasks 4)
3. 2026-07-06-audit-correctness-wave2: 10 rounds (proposal 1, design 2, spec 3, tasks 4)
3(tie). 2026-06-09-harden-pytrends-validation: 10 rounds (proposal 2, design 3, spec 4, tasks 1)
5. 2026-06-26-add-thread-count-breadth-unit: 8 rounds (proposal 1, design 1, spec 2, tasks 1, orchestrator 2, premise 1) -- tie with 2026-06-19-add-aggregation-fact-table: 8 rounds (proposal 2, design 4, spec 1, tasks 1)

By far the biggest outlier is notable-emergence-detector (2026-06-28): proposal Round 2 explicitly labeled "re-review after scope narrowing" (extrends repo, archive dir 2026-06-28-notable-emergence-detector/review-log.md:25) -- i.e. scope was narrowed mid-review before it could pass. tasks.md alone took 7 rounds.

### Friction markers (grep -rEic sum of matching LINES across all archive/*/review-log.md + notes.md, 42+43 files):
- PARTIAL (case-insens, \bpartial\b): 65 hits -- but this is almost entirely a DOMAIN term ("partial collection", "partial backfill", "partial-Entity-write") not a workflow-friction marker. Essentially a false-positive category for friction purposes.
- timeout: 20 hits
- crash: 67 hits total mentions; ~34 lines are actual crash events (excluding "no crash" negations)
- fallback: 168 hits (mostly boilerplate invocation-note lines, see Sonnet below)
- Sonnet: 93 hits, but 17 are literally "No Sonnet fallback" (i.e., explicit NEGATIONS logged as standard footer boilerplate). Counting only genuine escalation language (`escalated to a/Sonnet`, `Sonnet apply-executor`, `Sonnet-subagent substitution`, `replaces the deepseek apply-executor with Sonnet`): **10 of 42 changes (~24%) had a real deepseek/opencode -> Claude-Sonnet fallback**, due to crash/timeout/silent-failure of the primary deepseek-v4 executor. List: close-gate-coverage-gap, add-polymarket-probability-scorer, fix-watermark-integrity, add-run-health-alerting, add-cross-lane-breadth-fusion, add-per-lane-scoring, extend-run-health-alerting, speed-up-notability-title-probe (routing choice, NOT a failure), audit-correctness-quality, story-grouped-digest (routing choice, NOT a failure). So of the ~10, at least 2 were deliberate operator routing decisions rather than crash-driven fallback; ~8/42 (~19%) were genuine crash/timeout-driven escalations.
- DISSENT: 0 hits
- non-convergence: 0 hits
- escalate: 27 hits, mix of "Decision pending (escalated to user)" (real scope/design decisions kicked to human, e.g. extrends repo, archive dir 2026-06-06-add-polymarket-collector/notes.md) and "Sonnet apply-executor" escalations already counted above.

Example quote (crash->Sonnet failure ladder), extrends repo, archive dir 2026-06-12-fix-watermark-integrity/notes.md:
"the deepseek-v4-flash opencode run was attempted twice for slice B and both times truncated mid-exploration (process killed, no work landed, no `Falling back` warning)... per the failure-ladder (crash -> retry -> crash -> Sonnet) the work was escalated to Sonnet."

Example: extrends repo, archive dir 2026-06-15-add-run-health-alerting/notes.md -- deepseek apply-executor TIMED OUT (exit 124, no edit landed) on a mechanical de-indent fix, escalated per failure ladder to Sonnet.

### Verify-pass yield (multi-model gate: orchestrator self-review -> deepseek-v4-pro verifier -> deepseek-v4-flash verifier -> simplicity gate -> security gate)
11 changes have an explicit "## Verify results" section in notes.md. Pattern found: **the orchestrator's own behavioral self-review / probes catch the real (CRITICAL) bugs; the pro/flash multi-model verifier passes downstream of that overwhelmingly return "Defects: None".**
- 2026-06-15-add-run-health-alerting: CRITICAL bug (D1, wrapper heredoc indentation -> degraded-alert path silently dead) found at verify by ORCHESTRATOR eyeballing live output, not by the pro/flash pass. "The mock suite was structurally blind to it... Caught by reading the diff + an empirical reproduction." (notes.md:74-80)
- 2026-06-13-add-entity-identity-registry: CRITICAL bug (D1, pre-migration-0012 crash that would break the next production cron run) found by "an orchestrator repro probe on a production copy" -- again not the automated verifier gate.
- 2026-06-19-add-aggregation-fact-table: CRITICAL cast/type bug found by ORCHESTRATOR SELF-REVIEW before the pro/flash passes ran; once fixed, "pro pass: VERDICT READY / Defects None; flash pass: VERDICT READY / Defects None" -- i.e. the paid multi-model gate found ZERO issues on this change. Also logged: "the deepseek-v4-flash verifier emitted garbled/empty output on two attempts and only produced a clean verdict under an ultra-minimal verdict-only prompt" (notes.md:158-160) -- a real reliability/tooling-gap cost.
- 2026-06-12-fix-scoring-totals-and-streaming: 1 defect (D1) found "at falsifiability" (an orchestrator-run falsifiability probe), fixed by a re-delegated scoped deepseek-v4-flash executor.
- 2026-07-02-speed-up-notability-title-probe: pro+flash both READY; flash pass DID surface one real (if minor) finding -- a documentation-accuracy nit about which pyahocorasick call raises on an empty automaton (notes.md:57). This is the one clean instance in the sample of "flash pass catches something pro/self-review missed."
- 2026-06-28-notable-emergence-detector: **PROCESS INCIDENT** -- the deepseek-v4-pro verifier pass, despite being intended as read-only, had `bash:allow` and actually RAN a live scoring job + 12,005-row embedding backfill against the real production `trendscope.db`, mutating run history. Required an operator-authorized full revert + safety snapshot (`trendscope.db.bak-pre-verify-revert-20260628`). Root cause per the notes: "the pro-pass prompt forbade re-scoring but did not explicitly forbid DB writes." (extrends repo, archive dir 2026-06-28-notable-emergence-detector/notes.md:139-146)
- Several other changes (add-thread-community-capture, add-eval-harness, backfill-thread-community, market-stage-hardening, add-correctness-signals) verify clean with no defects at all (no bugs at any stage).

Net read: across the 11 changes with recorded verify sections, roughly 4 surfaced a real CRITICAL/blocking defect at verify time, and in every one of those 4, the catch was attributed to the ORCHESTRATOR's own behavioral probe/self-review, not the downstream pro/flash multi-model verifier gate. The multi-model gate's main recorded values-add in this sample: one doc-accuracy nit (speed-up-notability-title-probe) and confirmation/no-new-issues on the rest -- plus one serious NEGATIVE (the production DB mutation incident above). This suggests the automated multi-model verify gate, as currently practiced, is largely a rubber stamp/confirmation step layered AFTER the real bug-finding work (orchestrator self-review), while adding its own real risk (unintended live writes).

## SECTION 2: tasks.md re-scoping mid-apply

Checkbox states across all 42 archived tasks.md: 813 `- [x]` vs only 2 `- [ ]` (both in extrends repo, archive dir 2026-06-08-tune-enrich-merge-prompt/tasks.md, tasks 5.1/5.2). No non-standard checkbox markers (`[~]`, `[!]`, etc.) exist anywhere -- the workflow enforces a strict binary checkbox convention.

Those 2 unchecked tasks are NOT abandoned work -- notes.md explicitly hands them to the archive phase ("### Still owned by archive (fresh session -- do NOT do here)", extrends repo, archive dir 2026-06-08-tune-enrich-merge-prompt/notes.md:62). Pattern: the final tasks.md group (spec-sync + STATUS.md/decisions reconciliation) is routinely left unchecked at apply-time and completed by the archive-executor instead -- a structural handoff, not scope loss.

"descoped"/"deferred" hits: grep -rli "descoped" tasks.md+notes.md → 1 file (2026-06-14-add-board-console/notes.md): a design item (persisting `partial_sources` for a health panel) explicitly "descoped here" and pushed to a follow-on change. grep -rli "deferred" tasks.md → 7 files, but nearly all are scope EXCLUSIONS decided at proposal/design time and stated upfront in tasks.md (e.g. 2026-06-06-add-polymarket-collector/tasks.md: "backfill() is deferred -> it must raise NotImplementedError"; 2026-06-15-add-run-health-alerting/tasks.md: source-health/validation-deadness alerting "DEFERRED... do NOT implement them"; 2026-06-16-disable-pytrends-validation/tasks.md: full module removal "is a separate, deferred decision"). These are planned non-goals, not re-scoping DURING apply.

Genuine mid-apply re-scoping (plan changed after implementation started, due to something discovered while executing) is rare -- the clearest instance found: 2026-07-06-audit-correctness-wave2/notes.md:592-594, "### Rescoped invariant" -- inv-05 (Monday-aligned period_start check) was rescoped mid-apply because the naive formulation fired against the entire daily-grain corpus (over-broad false-positive), narrowed to weekly-grain-only rows per an orchestrator decision recorded inline.

Also 2026-06-28-notable-emergence-detector's proposal Round 2 was explicitly "re-review after scope narrowing" (review-log.md:25) -- but this happened during the PROPOSAL review loop, before apply started, not mid-apply.

Bottom line: of 42 archived changes, only ~1 shows a clean mid-apply re-scope event (audit-correctness-wave2), plus 1 clear post-hoc descope-to-follow-on (add-board-console). Re-scoping is not a frequent failure mode in this sample; the workflow's discipline (freeze proposal/design/tasks before apply) appears to mostly succeed at preventing scope churn during execution.

## SECTION 3: plans/ directory (SMALL-tier) -- STILL EXISTS, did NOT get pruned away

Contrary to the assumption that plans/ might be a pre-OpenSpec relic: /home/pang/Projects/extrends/plans/ is alive, git-tracked, and actively growing (newest file timestamp 2026-07-11, same day as this audit). `git ls-files plans/` = 68 tracked files (62 at top level + 6 in subdirs: audit-correctness-quality/, audit-security/, comprehensive-repo-audit/, session-e-daily-cadence/).

Per knowledge/reference/*.md (e.g. frontend-and-operator-ui.md:316-327, register-diverse-source-planting.md:9,71), `plans/` is the deliberate home of **SMALL/tier-1 "plan only"** changes -- i.e. a lightweight track that explicitly bypasses the full openspec propose->design->tasks->apply->verify->archive lifecycle for small/mechanical work. So the repo runs TWO parallel change-tracking systems: the heavyweight reviewed openspec/changes/ (42 archived) and the lighter plans/ (68 files, its own premise-review + apply-gate convention, no multi-round adversarial review log).

This directly contradicts the ORIGINAL migration intent: knowledge/research/OPENSPEC_MIGRATION_PLAN.md Phase 5 (lines 131-182) was titled "Prune plans/ to roadmap-only" and explicitly planned to reduce plans/ down to just 2 forward-looking roadmap docs (`data-source-expansion.md`, `prediction-market-integration.md`), moving everything else out (e.g. `git mv plans/mvp-implementation.md ai-docs/archive/...`). **That pruning did not stick** -- plans/ has instead regrown into a 68-file shadow-workflow directory full of premise-reviews, handoffs, and session artifacts. This is itself a friction finding: a lighter-weight workflow tier keeps reappearing/persisting alongside the "official" openspec workflow, suggesting the full 6-stage lifecycle is too heavy for a meaningful fraction of work and operators route around it via plans/.

- premise-review.md siblings: 13 found (e.g. plans/b1-known-events-recall-leadtime-premise-review.md, plans/b4-premise-review.md, plans/wire-audit-layer-premise-review.md, plans/session-e-daily-cadence/premise-review.md). Verdict convention: "PREMISE: AGREE -- no operator override needed" (plans/premise-review-source-key-health-labels-rekey.md) / "No dissent -> SMALL apply gate is open" (plans/wire-audit-layer-premise-review.md).
- "OVERRIDE" mentioned in 12 files (mostly the phrase "no operator override needed", i.e. the AGREE path -- not actual override events).
- "DISSENT" mentioned in 3 files (plans/premise-review-fix-notability-s2-vectorize.md, plans/wire-audit-layer-premise-review.md, plans/wave4-propose-handoff.md) -- again mostly "no dissent" (gate-open) not real disagreement.
- Also notable: 10+ "*-handoff.md" files in plans/ (fork1-handoff.md, wave1/2/3/4-remediation-handoff.md, wave4-apply-handoff.md, wave4-propose-handoff.md, session-c/d/e/g-handoff.md, llm-gold-anchor-*-handoff.md, notability-loop-perf-handoff.md) -- cross-referenced in Section 6 below as context-exhaustion evidence.

## SECTION 4: knowledge/lessons.md -- PROCESS-related lessons only

Full file is 132 lines / 7 dated entries. Framed explicitly as "Project-specific cautionary tales" (line 3). Classification:

PROCESS-related (4 of 7, workflow/delegation/agent-behavior):
1. **harden-pytrends-validation incident (2026-06-09)**, lessons.md:9-40 -- TWO lessons in one incident: (a) propose-phase: "probe real external behavior before self-review" -- a mock-based test suite gave false confidence; the real bug (urllib3 2.x API rename) only surfaced at verify-phase live smoke, not in 722 green mock tests. (b) reviewer: "never affirm unverifiable empirics" -- the reviewer runs with `bash: deny` (cannot execute code) yet "confirmed" an external library kwarg was "available," which was false and shipped a regression. This is the single most-cited/most-referenced incident in the whole knowledge tree.
2. **Delegation override** (lessons.md:42-48) -- documents the mandatory rule that the primary agent never implements tasks inline; Claude Code drives an OpenCode deepseek-v4-flash apply-executor, Sonnet only as a failure-ladder fallback.
3. **OpenCode delegation -- orchestration patterns** (lessons.md:54-83) -- concrete operational lessons from "session-8": slice big applies into task-group ranges sized to the 300s/600s hard timeout ceilings; fold a scoped fix into the NEXT slice's brief rather than a separate run; retry a timed-out reviewer once with a tight, context-preloaded brief. Explicit rationale: "deepseek burns most of its budget re-deriving context the orchestrator already has." Also documents that completion/success must be judged from disk (git diff / test run), NOT from the executor's exit code, because "scoped opencode run fixes have repeatedly completed their work yet exited 1 at teardown."
4. **Dossier-assembly delegations must state the never-record-counts trap explicitly** (audit-correctness-wave4, 2026-07-10; lessons.md:99-115) -- 6 parallel section-writer subagents transcribing findings; one subagent's section carried ~29 banned coverage-percentage figures because the generic "no counts" briefing didn't name the specific trap. Caught by orchestrator self-review before the verifier pass, required a re-delegated rewrite + a dedicated `_denumeralize_oneoff.py` sweep script.

Borderline/domain (not counted above): the `monkeypatch.undo()` test-isolation fix (explicitly labeled "not a product defect" but is a pytest-hermeticity gotcha, lessons.md:50-52); "score in-place on a prepared DB" (an eval-harness efficiency lesson, lessons.md:85-97); the notability rerank eval warm-up lesson (lessons.md:117-132, a product/eval-methodology lesson, not about the workflow itself).

## SECTION 5: knowledge/audit-log.md cadence + correctness-audit-2026-07 wave overhead

knowledge/audit-log.md is only 16 lines total: **exactly ONE dated cycle entry** -- `2026-07-03 · audit/2026-07-03 · b9a96c2 · ruff hygiene only`. The file's own header frames it as a registry of routine `scripts/checks.py --report` cycles, but only one such cycle is logged. An explicit "Gap note (2026-07-10, not a cycle)" states: "the ceremony lapsed 2026-07-04 -> 2026-07-10 while correctness-audit Waves 1-4 ran as OpenSpec changes... Deliberately NOT backfilled." So the routine deterministic-audit cadence effectively ran once, then paused for 6 days, superseded by a much heavier ad hoc audit program. Cannot compute a real "N audits/week" cadence from n=1; the honest read is "the lightweight audit mechanism was abandoned in favor of the heavyweight one within days of the log being created."

The heavyweight substitute, knowledge/research/correctness-audit-2026-07/, produced 4 wave dossiers as full OpenSpec changes (archived as 2026-07-04-audit-correctness-quality, 2026-07-06-audit-correctness-wave2, 2026-07-06-audit-correctness-wave3, 2026-07-10-audit-correctness-wave4) -- 4 waves in 6 calendar days:
- FINDINGS-wave1.md: 1194 lines / 84.6 KB, 14 distinct lead IDs (W1-*)
- FINDINGS-wave2.md: 876 lines / 59.0 KB, 11 distinct lead IDs (W2-*)
- FINDINGS-wave3.md: 1075 lines / 71.4 KB, 17 distinct lead IDs (W3-*)
- FINDINGS-wave4.md: 2414 lines / 191.6 KB, 12 distinct lead IDs (W4-*)
Dossier size roughly DOUBLED from wave1 to wave4 (84.6KB -> 191.6KB) while the lead count (things actually investigated) went DOWN slightly (14 -> 12) -- a real overhead-growth signal: each wave's writeup is getting heavier per finding investigated, not lighter, despite three prior waves of process experience.

knowledge/reference/audit-methodology-playbook.md documents concrete overhead/failure evidence from running this audit program:
- "CI had been structurally red for weeks" (workflow installed `.[dev]` while the suite imports the `[console]` extra) -- "discovered only when FN6's push made someone look" (audit-methodology-playbook.md:220-223). A real, silent, multi-week CI-broken incident.
- "A pro-tier reviewer invented a nonexistent tasks-template requirement mid-review; the finding was overruled with recorded rationale (review-log.md round 4)" (:224-227) -- a hallucinated review finding that had to be manually overruled (matches the audit-correctness-wave2 review-log round-4 "REJECTED (reviewer wrong on the template)" instance found in Section 1).
- The audit brief itself wrongly assumed `plans/` was untracked/gitignored when it is in fact git-tracked (:216-219) -- baselines had to be moved to `output/checks/` mid-flight, confirming Section 3's finding that `plans/` is a real, tracked, still-used directory that trips up even the audit program's own assumptions.

## SECTION 6: HANDOFF / context-exhaustion evidence

`knowledge/README.md:26-28` formally documents a designed mechanism: a session writes `knowledge/HANDOFF.md` (singular, root of knowledge/) "when it must hand off before archive (e.g. **context exhausted mid-change**)"; the next session absorbs it and deletes it. The doc explicitly states this "supersedes ad-hoc multiple root-level HANDOFF files" -- i.e., ad hoc handoffs were a recognized-enough pain point that a formal single-file mechanism was built to replace them.

Confirmed real usage in git history (`git log --oneline -- knowledge/HANDOFF.md`):
- `1c7a0c4 Wave-2 apply: 4.2 upstream backend landed (scaffold e604990); session handoff`
- `4fb0c22 Absorb wave-2 session handoff: delete knowledge/HANDOFF.md`
This is a concrete, dated instance of a mid-apply context-exhaustion handoff during the audit-correctness-wave2 change.

Broader handoff-file census (`find -iname "*handoff*"`, excluding .git): **21 files**, overwhelmingly in `plans/` (15: wave1-4-remediation/apply/propose/resume-handoff.md, session-c/e/g-handoff.md, llm-gold-anchor-*-handoff.md, notability-loop-perf-handoff.md, fork1-handoff.md), plus `tmp/handoff-accuracy-program.md`, `tmp/test-audit-handoff.md`, `knowledge/research/community-lane-breadth-handoff-2026-07-01.md`, `plans/audit-correctness-quality/wave2-handoff.md`, and exactly one inside `extrends repo, archive dir ` (`2026-06-28-notable-emergence-detector/handoff.md` -- a "paste into a fresh session" boot script for starting the COMPLEX propose phase with pre-loaded context, i.e. a planned session-boundary handoff rather than an emergency one).

Direct-phrase search ("context exhaust", "ran out of context", "session limit", "picking up where") across knowledge/, openspec/changes/, plans/: only the knowledge/README.md mechanism description itself uses "context exhausted" literally; no other file admits to it in those exact words -- but the sheer volume of *-handoff.md files (21) and the existence of a dedicated single-file mechanism for it is itself the evidence that this happens routinely enough to need tooling, even though individual incidents aren't always narrated as "we ran out of context."

## SECTION 7: git log bookkeeping ratio

Total commits: `git log --oneline | wc -l` = **520**.

Bookkeeping-keyword match (`git log --oneline | grep -ciE "reconcile|review-log|fix-hook|re-?sync|archive|sync scaffold|lint fix|propagat"`) = **99 commits (19.0%)**.

Per-keyword breakdown (case-insensitive, on the oneline log):
- reconcile: 56
- archive: 67
- sync scaffold: 11
- propagat: 3
- review-log, fix-hook, re-sync/resync, lint fix: 0 each (these particular literal strings don't appear in subject lines; the concepts exist but under different wording, e.g. "Reconcile trackers", "Archive X and reconcile project docs")

Sample bookkeeping commits: `52f7650 audit-correctness-wave4 archive: move to archive/, reconcile knowledge/`; `a993d27 Reconcile trackers: B2 labeling ergonomics shipped`; `0d602a3 Sync scaffold to ea28a8e + absorb the shared lint layer`; `ad738e4 Archive story-grouped-digest and reconcile project docs`.

Caveat: this keyword set is imprecise -- "archive" commits are LEGITIMATE required process steps (every change must be archived), not necessarily wasted effort, and some reconcile commits bundle real doc updates with real feature landings in the same commit. ~19% is a reasonable upper-bound estimate of "pure bookkeeping" commit share, not a precise figure. It does NOT include the (much larger, unmeasured) token/time cost of maintaining review-log.md/notes.md prose inside feature commits, which Section 1 shows is substantial.
