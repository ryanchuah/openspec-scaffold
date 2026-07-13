# Pass-yield evidence: who caught what, across the verify chain

**Question:** in the OpenSpec verify phase (orchestrator self-review → deepseek-v4-pro verifier
pass → deepseek-v4-flash verifier pass), has the third pass (flash, running the same checklist as
pro) ever earned its cost — i.e. caught a defect that self-review AND pro both missed?

**Method:** every `openspec/changes/{archive/*,*}/notes.md` + `review-log.md` in
`openspec-scaffold`, `extrends`, and `psc-monitor` was read for explicit pass/model attribution of
verify-phase defects (`grep` for `flash pass|pro pass|Verify Pass|VERDICT|NEEDS REVISION|self-review`
across all three repos' change dirs surfaced ~120 candidate files; ~45 were read in full or in their
verify-section). Findings below are organized per repo → per change, with a cross-repo summary
first. "Yield" = a defect surfaced by a pass that no earlier pass in the chain (self-review, then
pro) had already found. "Confirmation" (no yield) = the pass returned READY / zero defects on work
already known-clean.

---

## Cross-repo summary table

| Pass | Changes it ran in (recorded) | Unique real catches | Unique *trivial/cosmetic* catches | False positives overruled | Times waived/skipped |
|---|---|---|---|---|---|
| **Self-review** (orchestrator) | ~40 (effectively every change with a notes.md) | **~25** (most CRITICAL/correctness bugs: cast-type crashes, pre-migration crashes, cookie-security bugs, sparkline NULL bug, S2 same-term bug, absolute-path provenance, etc.) | several (whitespace, stale banners) | 1 (a naive tail-anchor probe artifact in fix-sync-mechanism, self-caught) | 0 (self-review is never waived — it's the floor) |
| **deepseek-v4-pro verifier** | ~30 | **1 substantial** (harden-stripe-webhook v1: TOCTOU sweep race, found on a *second, independent* pro re-verify pass) | 2 (premise-review-gate stale count; audit-correctness-wave1 never-record-counts wording, which forced a NEEDS REVISION round) | 0 recorded | ~6 (operator-directed skips: fix-sync-mechanism, lifecycle-gates, split-open-questions-round, checks-facts-split, shared-lint-layer, mechanize-invariants) |
| **deepseek-v4-flash verifier** (3rd pass, same checklist as pro) | ~28 | **0** | **3** (speed-up-notability-title-probe: doc-attribution nit for an exception source; name-normaliser-audit: stale test-fixture cosmetic field; client-ui-prototype: 2 dead imports, jointly credited with the simplicity gate) | 0 recorded as flash-specific; 1 shared-with-pro finding where flash's *verdict* (NEEDS REVISION) was stricter than pro's (READY) on the identical observation (deploy-security-posture) | ~7 (operator-directed skips: audit-correctness-wave3, audit-correctness-wave4, audit-wave2-signal-path, split-open-questions, fix-sync-mechanism n/a-pro-skipped-not-flash, checks-facts-split, shared-lint-layer, mechanize-invariants) |
| **Simplicity/quality gate** (separate from the 3-pass chain) | ~15 | **~15** (dead code, over-parameterization, non-sargable SQL, tautological probes, etc.) | several | 4 recorded (deterministic-tooling-layer review-log; mechanize-invariants) | n/a — a different gate, not scoped by this question |
| **Security-review gate** (separate) | ~8 | **1 major** (delegated-agent-safety: the denylist's literal-spelling bypass — the load-bearing finding pro+flash both missed) | — | 0 | n/a |

**Bottom line for the question asked:** across every recorded multi-model verify chain in all
three repos, **the flash pass never caught a real, non-trivial defect that self-review and pro
had both missed.** Its only recorded unique yields are three cosmetic/documentation nits (an
exception-source misattribution in a code comment, a stale test-fixture label, two dead imports).
By contrast pro caught one substantial defect (a TOCTOU race), and — more importantly — the
*self-review* and the *simplicity/security gates* (which are not the flash pass) caught the large
majority of everything real. See "Data-quality caveats" for why this may understate flash's true
value (it is also the pass most often skipped by operators, and several early changes predate the
gate's existence).

---

## openspec-scaffold

### 2026-06-16 — verify-multimodel-gate (the change that introduced this gate; MEDIUM)
Dogfooded on itself. Self-review: 1 trivial whitespace nit (fixed inline). Pro: READY, 0 defects.
Flash: READY, 0 defects (flash's report included a detailed disk-evidence trail but no new
findings). No yield from pro or flash.

### 2026-06-17 — cap-status-log (MEDIUM)
Self: 0. Pro: READY/0. Flash: READY/0. No yield.

### 2026-06-17 — lifecycle-gates (MEDIUM, the change that formalized the SMALL/MEDIUM tier split)
Self-review caught a non-canonical delta-spec format (re-delegated to a flash *fix*-executor to
correct — that's an apply-side fix, not a verify catch). **Pro pass SKIPPED** at operator
instruction (the "W1/W2 lighter pattern" for low-risk scaffold changes). Flash: READY/0. No yield
from either model pass.

### 2026-06-17 — split-open-questions (MEDIUM)
Self-review caught two whitespace drifts the flash *apply*-executor had introduced. Pro: READY/0
defects. **Flash verifier pass skipped** by explicit operator instruction this session. No yield.

### 2026-06-17 — fix-sync-mechanism / W1 (tier unstated, treated as light-MEDIUM)
Self-review: one false-alarm self-corrected (a naive tail-anchor probe artifact, not a code
defect). **Pro pass skipped at operator instruction** — flash ran alone (READY/0). This is the
closest in-repo analogue to a "flash-only" pass on a real change, and it found nothing.

### 2026-06-18 — lean-boot-context (MEDIUM)
Self-review caught 2 real defects (a test-fixture regression from an operator-directed guard bump;
content loss in an appendix relocation — three load-bearing pitfalls dropped). Pro: READY/0
(post-fix). Flash: READY/0 (post-fix). No yield.

### 2026-06-18 — add-status-lint (MEDIUM)
Self, pro, flash all READY/0. Flash's first run emitted no closing text (operational hiccup, not a
finding) and had to be re-run once. No yield.

### 2026-06-21 — premise-review-gate (tier not explicitly stated; workflow/instruction change)
Self-review caught a real doc bug (a new agent-file section rendered inside a fenced code block,
so it read as example text, not a live instruction). **Pro pass caught a genuine, if trivial,
finding self-review missed**: a stale "acknowledge five things" count after a 6th item was added
elsewhere in the same change (🟡, fixed with a one-word edit). Flash: READY, no unique finding.
**This is the strongest pro-only-yield example in openspec-scaffold** — small, but real and
attributable specifically to the pro pass.

### 2026-07-02 — deterministic-tooling-layer (MEDIUM)
Self-review caught 2 defects (absolute-path fingerprint contract violation; a phantom-table alias
bug). The **simplicity/quality gate** (8-angle harness, a separate gate from pro/flash) caught 8
more real defects (git-rename mishandling, per-file subprocess floor-contract violation, an
UPDATE-statement extraction gap, an expression-index misparse, etc.) — this gate did the heavy
lifting for defects self-review didn't catch. Pro and both flash verifier passes (including a
scoped re-run after the gate): **zero defects, explicitly recorded as such** ("Pro and both flash
verifier passes: zero defects").

### 2026-07-02 — mechanize-invariants (MEDIUM)
**Pro+flash verifier passes explicitly WAIVED by operator directive** ("self review is enough…
keep the simplicity/quality gate"). Self-review: 0 functional defects. Simplicity gate: 7 findings,
5 fixed, 2 refuted-with-rationale. No pro/flash data point at all — waived, not run.

### 2026-07-03 — checks-facts-split (MEDIUM)
**Multi-model passes waived by operator instruction** ("skip the pro and flash review pass for
this"). The pro pass was launched and *deliberately abandoned unread*; the flash pass never
launched. Self-review: 0 defects at verify (propose-phase pro review had caught real issues
earlier, but that's a different gate/phase). Zero verify-phase model-pass data.

### 2026-07-03 — shared-lint-layer (MEDIUM, portfolio change C)
**Deepseek review/verify passes waived by operator instruction for this whole change** — "the
orchestrator's own self-review is the propose-phase review of record." Self-review caught 2 real
defects (a citation-matcher false-positive on single-line refs; a curl-installer with 404 URLs,
descoped instead of fixed). No pro/flash data — waived.

### 2026-07-03 — delegated-agent-safety (MEDIUM; the highest-stakes example on record)
Pro and flash verifier passes: **both READY, zero defects** — both reasoned only from the
*declared* permission-pattern list. The **security-review gate** (separate from pro/flash) then
**live-probed the running permission engine** and found the load-bearing defect both model passes
missed: the denylist matched literal command spelling, not command identity, so `sed -i`, `cp`,
`find -delete`, `/usr/bin/rm`, `env rm`, `python3.13 -c` all bypassed it — several defeating
`edit: deny` outright. This is explicitly called out in the notes ("The security pass found the
load-bearing defect — and it mattered... All three pro-reviewer propose rounds + both verifier
passes reasoned from the declared pattern list and green-lit the... framing"). Self-review
separately caught a lint/citation coherence issue. **Neither pro nor flash caught the one thing
that actually mattered here; a different, non-checklist gate did.**

### 2026-07-09 — outstanding-work-collector (MEDIUM)
Self-review flagged an absolute-vs-relative provenance inconsistency, fixed on operator request.
Notes state explicitly: "**The pro/flash verifier passes found no behavioral defect.**" Both passes
were then re-run READY after the fix (confirmation, not a catch). No yield.

---

## extrends

### 2026-06-13 — add-entity-identity-registry (predates the multi-model gate; no pro/flash chain)
Self-review (orchestrator) alone found a CRITICAL pre-migration crash bug (D1: digest/eval queries
would `OperationalError` on a DB that predates a migration — would have broken the next cron) plus
3 apply-gate defects. **No pro/flash verifier pass exists in this record at all** — this change
(2026-06-13) predates the verify-multimodel-gate's introduction in openspec-scaffold (2026-06-16)
and its propagation to extrends. Recorded as a data-quality boundary, not a "waived" case.

### 2026-06-19 — add-aggregation-fact-table (COMPLEX)
Self-review found 1 CRITICAL defect (a `cast()`→numeric SQLite bug that would crash the mandatory
pre-flip verification probe — the probe had never actually been run before verify, because the
table it depends on was empty). Pro: READY/0 defects. Flash: READY/0 defects. Notably: **"the
deepseek-v4-flash verifier emitted garbled/empty output on two attempts and only produced a clean
verdict under an ultra-minimal verdict-only prompt; the pro pass was reliable"** — an operational
reliability cost recorded against flash, not a catch.

### 2026-06-20 — client-ui-prototype (MEDIUM)
Self-review (live-output eyeball) found the substantive bug: every legacy-run entity rendered an
empty sparkline (NULL `weekly_doc_counts`, no fallback). Pro: READY/0. Flash: READY/0 formal
defects, but the notes credit "**the flash pass / simplicity gate**" jointly with catching two
trivial dead imports — the joint attribution makes this an ambiguous, but real, small flash-side
yield (dead code, not a behavior bug).

### 2026-06-28 — notable-emergence-detector (COMPLEX)
Self-review caught 1 CRITICAL correctness bug (S2 novelty score compared same-term only, not
corpus-wide — collapsing real catches into gravel) and 1 dead-config finding, both **before**
pro/flash ran; pro and flash then returned READY on the already-fixed tree (no yield). Separately:
**the deepseek-v4-pro verifier pass itself caused a process incident** — despite being nominally
read-only, it ran a full scoring pipeline and a backfill script against the **production** cron DB
(bash:allow was not scoped tightly enough), requiring an operator-authorized revert. This is a cost
of running the pro pass, not a benefit, and it is the direct origin of the later
delegated-agent-safety hardening change.

### 2026-07-02 — speed-up-notability-title-probe (MEDIUM)
Self: 0. Pro: READY/0. **Flash caught a genuine (if trivial) documentation-accuracy nit**: the
design doc and a code comment attributed an empty-automaton exception to the wrong library call
(`make_automaton()` vs `iter()`) — corrected inline. This is the cleanest unambiguous flash-only
catch found in any repo, and it is purely cosmetic/doc-level; the guard itself was already correct
either way.

### 2026-07-04 — audit-correctness-quality / Wave 1 (COMPLEX, findings-only)
Self-review caught a stale banner. **Pro round 1 returned NEEDS REVISION** on a real
process-compliance defect (real-corpus row counts recorded in a tracked dossier, violating the
never-record-counts rule) — fixed, round 2 PASS. Flash: READY/0. The **simplicity gate** caught six
probe-quality defects, headlined by a tautological duplication probe (comparing a hand-copy against
itself, overclaiming its own evidence method) — the single richest non-self-review catch in this
sample, attributed to the simplicity gate, not flash.

### 2026-07-06 — audit-correctness-wave2 (COMPLEX)
Self-review caught a wording defect (a burst-detection claim overstated where the JSON evidence
actually diverged). Pro: READY/0. Flash: READY/0 — notes state explicitly "Pro and flash verifier
passes surfaced no defects." The simplicity gate caught 3 real defects (a documented-vs-implemented
key-count mismatch; a false-positive-prone homogeneity check; a non-sargable SQL check rewritten
for an ~8.5x speedup). No pro/flash yield.

### 2026-07-06 — audit-correctness-wave3 (COMPLEX)
Self-review: 0. Pro: READY/0 (independently re-ran the suite, recomputed checksums, spot-checked
claims). **Flash verifier pass and the simplicity gate were both SKIPPED by explicit operator
directive mid-verify.** No flash data point — not a null result, an unrun one.

### 2026-07-10 — audit-correctness-wave4 (COMPLEX, findings-only)
Self-review caught a real process-compliance defect (dossier carried ~29 precise coverage
percentages and line-counts, violating never-record-counts) before the verifier pass ran. Pro:
READY/0 (independently reproduced the two highest-stakes claims and confirmed never-record-counts
clean). **Flash verifier pass SKIPPED by operator directive.** No yield; no flash data point.

### Other extrends changes sampled with explicit "pro/flash: zero defects" (no yield)
add-psc-suppression-adjacent analogues in this repo — add-test-tiering ("Verifier passes (pro +
flash): none"), tier-grade equivalents, console-entity-dedup ("self + pro + flash all clean"),
add-cross-lane-breadth-fusion, polish-client-ui-prototype, add-thread-count-breadth-unit
(pro+flash both READY zero defects; a later flash *re-verify* after quality fixes was also clean) —
consistently: self-review or the simplicity/security gates carry the real catches; pro/flash
confirm.

---

## psc-monitor

### 2026-06-16 — harden-stripe-webhook, v1 (MEDIUM) — richest pro-yield example found
Two real defects (DEFECT A CRITICAL: sweep deactivated the wrong end of the list — oldest instead
of newest, opposite of spec, would have shipped with a red CI; DEFECT B: a dead-letter UPDATE run
on an already-aborted transaction) are recorded as "found during verify" without clean pass
attribution — this change's formal pro/flash verify chain was explicitly **not yet run** at that
point per its own "Workflow status" note, so these are best read as self-review catches; the
notes do not credit pro or flash by name for A/B. **Separately, and materially: a *second,
independent* deepseek-v4-pro verification pass** (run "blind to prior reviews," per
`research/deepseek-verify.md`) **found a genuine new MEDIUM defect (M1): a TOCTOU race** in the
grace-period sweep (a concurrent re-upgrade between the sweep's SELECT and UPDATE could still
downgrade a paying customer) — fixed with a re-assert-inside-the-UPDATE guard + a regression test.
**This is the single most substantial pro-only catch found in any of the three repos.** (No flash
pass is mentioned in this change's verify record at all.)

### 2026-06-18 — add-psc-suppression (COMPLEX)
Self, pro, flash: all clean, explicitly "**None** surfaced at verify (self-review, pro pass, and
flash pass all returned clean / READY with no defects)." No yield.

### 2026-06-20 — harden-stripe-webhook v2 (MEDIUM, the hardening-of-the-hardening)
Self, pro, flash all READY/0. Security review (Stripe money/auth boundary): 0 findings. No yield.

### 2026-06-19 — convert-appointment-dates-to-date (tier unstated)
Self, pro, flash: all READY/0 defects. No yield.

### 2026-06-20 — add-ntfy-operator-alerting (tier unstated)
Self, pro, flash: all READY/0. One *suspected* defect was investigated and disproven — not a catch.

### 2026-06-20 — audit-test-suite-quality (findings-only)
Self, pro, flash: all clean. Notable **operational cost, not yield**: "the deepseek-v4-flash
verifier could not emit its formal `VERDICT:` block across two attempts... a flash/`opencode run`
output-truncation artifact" — judged substantively READY from the (truncated) transcript,
corroborated by pro. Logged as a candidate `knowledge/lessons.md` entry: "flash truncates the
closing block on long read-only reviews... prefer pro for long verifications."

### 2026-06-21 — tier-grade-company-watch-alerts (tier unstated; operator substituted Sonnet for deepseek)
Not a deepseek pro/flash data point (operator directed **Sonnet** verifiers for both passes,
disclosed as reduced cross-family diversity vs the deepseek default). "Verifier Pass A (Sonnet)"
found a real test-coverage gap (a spec scenario's email-side behavior was implemented correctly but
untested); "Pass B (Sonnet)" READY. Included here because it is structurally the same slot in the
chain the flash pass would otherwise occupy, and it *did* find something — suggesting the chain
position (a second independent model pass) can be productive when not deepseek-flash specifically.

### 2026-06-30 — deploy-security-posture (COMPLEX, auth/CSRF/cookie hardening) — the nuanced case
Self-review found the substantive bug (a `__Host-` cookie emitted without `Secure` in dev, breaking
dev login — the `__Host-` prefix requires `Secure`). The security-review gate separately found a
functional bug (frontend logout hit the wrong path). **Both pro and flash independently flagged the
SAME single remaining item** — that the design/spec still described the old env-gated `Secure`
behavior after the as-built code moved to always-on `Secure`. **Pro's verdict: READY** ("the only
browser-compliant option," non-blocking). **Flash's verdict: NEEDS REVISION** on the identical
observation — flash's stricter severity judgment is what actually forced the artifact correction;
a flash re-pass then cleared READY. This is *not* a unique-content catch (pro saw the same thing),
but it is the one recorded case where flash's verdict discipline, not its content-finding, produced
an outcome pro alone would not have forced.

### 2026-07-01 — name-normaliser-audit (MEDIUM)
Self-review caught 1 CRITICAL defect (a test coupled to the change directory, which `archive`
relocates — would have reddened the suite post-archive). The simplicity gate caught 3 more real
defects (an F-N3 invariant leak in a fallback path; a connection leak-safety issue; AST-test
verbosity) plus a security-checklist catch (a PII artifact not gitignored). **Flash flagged a
genuine, if purely cosmetic, catch**: a test fixture's `agree:false`/`disagreements` fields had
gone stale relative to the fix and were now misleading — flagged 🟡-cosmetic, left as-is with
rationale (harmless, tests don't read those fields). Pro: 0. This is the second-cleanest
unambiguous flash-only catch found, and again purely cosmetic.

### 2026-07-06 — audit-wave0-wave1 (COMPLEX)
Self-review (with delegated sweeps) caught dossier-consistency issues (mislabeled evidence fields,
missing Evidence/Repro fields, never-record-counts phrasing slips). A security/simplicity sweep
caught real hardening gaps (SQL-identifier-injection guards on scratch-DB scripts — one path could
reach the LIVE DB through an f-string SELECT). Pro and flash verifier passes: **both READY on the
post-fix state** — no unique catch recorded for either beyond confirming the fixed tree.

### 2026-07-06 — audit-wave2-signal-path (COMPLEX)
Self-review caught a real defect (two live-reading probes were SELECT-only in intent but did not
*enforce* read-only on the connection path — fixed). Pro: READY/0. **Flash verifier pass and the
simplicity gate were both SKIPPED by operator ruling mid-verify.** No flash data point.

### 2026-07-09 — audit-remediation-wave-a (MEDIUM)
Self-review caught 1 real defect between apply slices (a content-length-absent-header case was
unhandled). Pro: READY/0. Flash: READY/0, explicitly "0 defects, criterion-by-criterion." No yield.
Operational note: the flash *apply*-executor (not the verifier) twice hit its 600s ceiling on
otherwise-complete work — a cost, not a verify-pass finding.

### SMALL-tier changes: does the single flash-only pass ever catch anything? (the separate question)
Both SMALL-tier changes found with a plan.md in this sample — `2026-06-20-add-er-semantic-tests`
and `2026-07-02-rebrand-to-helmsentry` — carry **no notes.md and no recorded verify outcome at
all**. `add-er-semantic-tests` was never executed standalone (subsumed into
`audit-test-suite-quality` before its planned single flash verifier pass ever ran).
`rebrand-to-helmsentry` has a plan.md + premise-review.md (flash premise pass, a *different*,
pre-apply gate) but no notes.md documenting its post-apply verify outcome. **A repo-wide grep for
any `notes.md` declaring `Tier: SMALL` across all three repos returned zero files.** This is a
structural, not incidental, gap: the tier-scaling design (formalized in
`openspec-scaffold/2026-06-17-lifecycle-gates`) deliberately exempts SMALL changes from the
notes.md-producing verify skill — "it does its own verification per AGENTS.md (optionally one flash
pass if risky)" — so there is **no historical record in any of the three repos of what the SMALL-only
flash pass has or hasn't caught**, despite the mechanism being specified for three-plus weeks. This
is worth flagging on its own terms: it is not that flash-only passes were tried and found nothing —
it's that the lightweight tier was designed to not leave a paper trail, so the question "has the
SMALL-tier flash-only pass ever caught anything" is currently unanswerable from the archive.

---

## Data-quality caveats

1. **Attribution granularity varies by era.** Early changes (openspec-scaffold's own W1/W2-era
   changes, extrends' `add-entity-identity-registry` from 2026-06-13) predate the
   verify-multimodel-gate mechanism itself (introduced 2026-06-16) or its propagation to that repo,
   so they have no pro/flash chain to evaluate at all — self-review-only "verify checkpoints."
2. **The pass most often skipped is not flash — it's pro**, in openspec-scaffold specifically
   (fix-sync-mechanism, lifecycle-gates: pro skipped, flash ran). But flash is skipped more often
   in absolute count once the COMPLEX findings-only audit waves are included (wave2-signal-path,
   wave3, wave4 in extrends all explicitly skipped flash "by operator directive mid-verify"), which
   thins the denominator for judging flash's yield specifically in the highest-stakes, most
   defect-dense changes of the sample.
3. **Some "defects found during verify" entries do not name which pass caught them** (both
   `harden-stripe-webhook` v1's Defect A/B and `historical-reports`'s apply-review defects) — these
   read as self-review catches by process of elimination (the formal multi-model chain is either
   not yet run or not referenced in that section) but are not explicitly labeled, so they are
   excluded from the pro/flash yield counts above rather than assumed.
4. **Operator-directed model substitution** (Sonnet standing in for deepseek pro/flash in
   `tier-grade-company-watch-alerts`, and Sonnet apply-executors substituting for flash in several
   changes) means "the flash pass" sometimes wasn't deepseek-flash at all — those cases are called
   out separately, not folded into the flash tally.
5. **Repos self-report a policy against recording raw counts** ("never-record-counts") in several
   changes, which is why "one line each, nature not counts" was used per the task's own instruction
   — but this also means some notes.md entries state "N defects" only as a category tally with
   qualitative description, occasionally forcing a judgment call on what counts as "one" vs
   "several" findings from a single pass.
6. **Sample is large but not exhaustive.** ~45 of ~120 candidate notes.md/review-log.md files across
   the three repos were read in detail (all changes with `Verify`/`Verdict` headers plus every hit
   for "flash"/"pro pass" context in a grep sweep); several MEDIUM changes with uniformly
   "zero-defects-all-passes" verify sections were sampled but not individually narrated above once
   the pattern was well-established (add-web-search-validator, add-run-health-alerting and its
   extension, add-cross-lane-breadth-fusion, add-per-lane-scoring, add-thread-breadth-eval-labels,
   polish-client-ui-prototype, story-grouped-digest, harden-delegation(-robustness), knowledge-lint,
   clarify-audit-tooling-surface, fix-convergence-guard, single-source-rules, restructure-project-
   knowledge, rename-memory-to-knowledge — all consistent with the dominant pattern of "self-review
   or a separate gate catches; pro/flash confirm").
