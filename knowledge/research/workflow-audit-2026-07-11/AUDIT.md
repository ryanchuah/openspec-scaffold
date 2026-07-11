# Workflow-efficiency audit — 2026-07-11 (Fable session, wave 2)

**Author:** Fable (departing-principal pass). **Predecessor:** `knowledge/research/scaffold-gap-analysis-2026-07/`
(wave 1: defect-prevention → OW-1..6). **This wave:** workflow *efficiency* — token economy, caching,
wall-clock, operator attention, determinism — traced step-by-step through the lifecycle as run in a
downstream repo, plus operational evidence mined from all 3 repos (81 archived changes).

**Method:** 4 parallel subagents — (A) Opus lifecycle walkthrough against the POST-OW-3 verify shape;
(B) coverage map of everything already frozen/parked/roadmapped (dedup filter); (C) friction-evidence
mining across extrends/psc-monitor/scaffold archives; (D) boot-surface + prompt-caching analysis
including decompiling the opencode binary to confirm what delegated deepseek calls actually receive.
Supporting evidence in this dir: `lifecycle-critique.md`, `friction-evidence.md` (+ per-repo files),
`caching-analysis.md`. Load-bearing claims below were spot-verified by the orchestrator (model-ID
spread, absence of telemetry, HANDOFF write-side docs, parked-item coverage).

---

## Direct answers to the operator's questions

### "How many verify reviewers do we really need?"
The evidence is now quantified (~38 recorded verify sequences, 3 repos): **the orchestrator's own
self-review/behavioral probes caught essentially all real verify-time defects; the pro and flash
passes' modal outcome is "Defects: None."** Scaffold: self caught ~5/5, pro added 1 cosmetic nit,
flash 0. extrends: self caught 4/4 CRITICAL, pro 0 (plus one *negative* — the "read-only" pro
verifier ran a 12,005-row backfill against production `trendscope.db`), flash 1 doc nit.
psc-monitor: 2 real defects, one caught by a flash pass, one by a Sonnet pass, none by pro.
- OW-3's frozen shape (MEDIUM self→pro; COMPLEX self→pro→lens) is the right conservative step. Land it.
- **Next ratchet, evidence-gated (decision made now, execution later):** once OW-7 telemetry covers
  ~20 more MEDIUM verifies, if the pro pass's unique-catch rate is still ≈0, downgrade MEDIUM to
  self + ONE flash-priced lens pass. **Never go below one independent model pass** — the live-smoke
  independence is what caught the pytrends regression that 722 green mock tests missed
  (extrends `lessons.md`), and an independent pass guards the self-review's conflict of interest.
- The premise gates are the same story earlier in the lifecycle: **0 DISSENT in ~25 live premise
  reviews across all repos** (the only DISSENT ever recorded is the gate's own smoke test). Verdict:
  do NOT delete (n too small, payoff asymmetric), but the direction-gate and propose-premise are
  near-duplicate pro reviews (wave-1 SYNTHESIS said the same). **Scheduled decision:** at ~50
  cumulative premise reviews with 0 production DISSENT, downgrade the direction gate to flash and
  keep the premise verdict folded into the proposal review only.

### "Are the prompts too tight or too loose?"
Neither, where it counts: the **agent definitions** (`openspec-reviewer`, `openspec-verifier`) are
tight-but-justified — the calibration rules and anti-patterns each trace to a real incident. The
problems are in **skill prose**, in both directions:
- Too loose: verify steps 13–15 tell the orchestrator to "search codebase for keywords… assess if
  implementation *likely* exists" — fuzzy inference the repo bans everywhere else, duplicating what
  `openspec status --json` returns deterministically.
- Too ritualistic: verify step 18's mandated emoji-checklist echo and ~40 lines belaboring the
  notes.md field-5 discipline — a lint should enforce this, not prose; explore's SKILL is ~85%
  stance/ASCII-gallery prose re-injected on every invocation.
Fix direction is OW-11 (trim ritual, mechanize the checks, tighten the fuzzy rubric); leave the
model-facing prompts alone.

### "What could be a deterministic script but isn't?"
Fully scriptable: delegation post-processing (the same grep/jq/assert/EXIT-sentinel sequence is
hand-rolled in 6 skills — OW-7); archive dir-move and ADDED/REMOVED/RENAMED delta-sync (OW-12);
task-checkoff coverage (the CLI already computes it); freeze-eligibility parsing (zero-🔴 +
`PREMISE: AGREE` are machine-readable — OW-11); notes.md five-field presence (OW-11).
Correctly LLM — do not script: reconciliation narrative, behavioral eyeballing/live smoke,
premise/lens judgment, explore.

### "How do we improve caching for Claude and deepseek?"
The one discovery that matters most: **opencode injects `AGENTS.md` verbatim into every delegated
deepseek call** (system array = [agent.md body, baseline-including-AGENTS.md], confirmed by
decompiling the binary), and **AGENTS.md is the highest-churn boot file** (32 edits since 2026-05-01
— more than STATUS.md at 24, despite AGENTS.md's own "treat this file as stable" contract). Every
AGENTS.md edit therefore invalidates the deepseek prefix cache for all 5 delegated agents at once,
and the apply-executor receives ~7.2k tokens written in the *orchestrator's* voice ("you do not
implement") that contradict its role. Second-order: 3 of 5 delegated prompt templates put the
variable `<changeRoot>` path at word 4–5, ahead of ~40–60 words of byte-identical boilerplate,
zeroing prefix-cache credit for the tail (the verifier prompt is the exception — already a fixed
string, optimally shaped). Boot surface for Claude: scaffold ~16k tokens, psc ~23k, extrends ~30k —
the spread is `knowledge/decisions/INDEX.md` (extrends 52KB). All → OW-8 and OW-13.

---

## New findings not covered by OW-1..6 or any parked item (dedup-checked)

Ranked by leverage. Every item routes to **Opus** — no remaining item needs Fable-tier design; the
design calls each item needed are made inline below.

1. **No delegation wrapper, no run telemetry** — 6 skills each hand-roll the identical hardened
   `opencode run` post-processing (timeout, fallback-grep, `jq` text extraction, format-marker
   assert, EXIT-sentinel poll, the pgrep self-match footgun), and nothing records what delegated
   runs actually do. The "exit codes lie" lesson is recorded ≥4 times across the repos because every
   session re-interprets exit codes by hand. Wave-1's yield analysis — and this wave's — had to be
   reconstructed from narrative review-logs. One tested `scripts/opencode_delegate.py` + a one-line
   JSONL ledger per run (`output/delegation-log.jsonl`: agent, model, phase, change, duration, exit,
   fallback?, verdict-marker, retry#) collapses the 6 restatements and makes every future
   optimization question (premise-gate yield, pro-pass yield, deepseek crash rate) a query instead
   of an archaeology project. → **OW-7**
2. **Delegated-context caching hygiene** — variable-paths-last prompt reshaping; stabilize or scope
   down the AGENTS.md injection into executors (test `OPENCODE_DISABLE_PROJECT_CONFIG=1` after
   verifying no agent.md silently depends on AGENTS.md content); treat AGENTS.md edits as
   cache-invalidation events (batch them); single-source the premise prompt that is currently
   triplicated (explore/propose/AGENTS.md SMALL bullet). → **OW-8**
3. **Autonomy-grant vs phase-gate contradiction** — AGENTS.md says an autonomy grant means
   "self-classify and proceed"; all four phase skills say "never invoke the next phase without an
   explicit user request — hard rule," with no carve-out. An autonomy-granted orchestrator gets
   contradictory instructions at every boundary. **Design call (made now):** the grant permits
   phase auto-advance EXCEPT across a premise DISSENT, a verify NEEDS-REVISION escalation, or any
   operator-named gate (propagation, push); state it once, cite everywhere. Same sweep fixes the
   harness-vs-skill contradiction on whether verify's self-review is a Task-tool spawn or the
   orchestrator's own inline pass (**resolve to: inline, orchestrator's own** — that is the pass
   whose independence the multi-model gate is defined against), the propose skill's duplicated
   Claude/OpenCode freeze-logic branches, the archive skill's missing EXIT-sentinel line, and adds
   the assumption-batching rule (below). → **OW-9**
4. **Apply-executor throughput** — the executor re-runs the FULL suite after every task (targeted
   runs are only permitted on the red path), which is what makes the 600s ceiling bind and forces
   slice ceremony; ~15–19% of downstream changes hit a crash/timeout→Sonnet escalation, each burning
   a 600–780s budget plus a re-brief, and the retry brief never states the resume contract
   (skip `[x]`, resume at first `[ ]`, *reconcile the half-edited in-flight task*) even though this
   is the only resume path that exists ("no subagent resume"). Green path → targeted tests per task,
   full suite once per slice; retry brief → explicit resume contract + distilled-state carry-forward
   (the extrends lesson: "deepseek burns most of its budget re-deriving context the orchestrator
   already has"). → **OW-10**
5. **Skill de-bloat + mechanized gates** (post-OW-3 only — touches the same files): replace verify
   steps 12–16 with deterministic CLI coverage + a short coherence note; cut explore's gallery prose;
   `freeze-check` script (parse review verdict block → FREEZE-OK/BLOCKED); `notes_lint.py` for the
   five-field discipline replacing the step-18 ritual; explore→propose slug-match warning (today a
   mismatched change name silently orphans the brief AND its premise review); run the two COMPLEX
   verifier passes concurrently (read-only on a frozen tree; saves ~13 min wall-clock; serialize only
   the NEEDS-REVISION re-run); add a model-ID agreement lint (`deepseek-v4` is hardcoded 44× across
   13 files with no guard — budgets already have one). → **OW-11**
6. **Archive mechanization** — dir-move + deterministic delta-applier for ADDED/REMOVED/RENAMED
   (LLM judgment only for MODIFIED merges + the reconciliation narrative). Keep the executor on pro:
   what remains after scripting IS the judgment-heavy part. → **OW-12**
7. **Knowledge-surface bounding, round 2** — `status_lint` word-budgets for the currently-exempt
   sections (extrends' "Immediate next action" hit 1,645 words — an accretion log; the cap rule
   itself works everywhere it applies); bound `knowledge/decisions/INDEX.md` (extrends 52KB ≈ 13k
   tokens; year-split, current year in INDEX); consider a plans/-count lint (extrends' `plans/`
   regrew into a 68-file shadow workflow contradicting its own migration plan — the lint makes the
   drift visible, the cure is operator triage). → **OW-13**

### Operator-attention economics (the "skill to ask the operator questions" idea)
The evidence does not support a new interviewing skill: propose reviews already catch
"implementer-would-guess-wrong" ambiguity (multi-round reviews were doing real work — including a
near-miss where round 1 would have deleted the load-bearing canary fixture), and premise reviews
run 100% AGREE. The cheaper, real gap is **interrupt batching**: AGENTS.md's "ask when genuinely
unsure" produces scattered synchronous asks, while operator waivers/overrides already happen ad hoc.
**Rule to add (folded into OW-9):** a non-blocking ambiguity gets a recorded default in the change's
`notes.md` (`Assumptions` block) and the batch is surfaced at the next operator gate; only blocking
ambiguities interrupt immediately. One rule line + one notes.md block — not a skill.

### Sonnet-first legitimization (small but telling)
The scaffold repo shows ≥4 deliberate operator overrides routing apply/fix work to Sonnet instead
of deepseek-first (vs 1 genuine auto-fallback). The operator is voting with their feet on
judgment-heavy changes. **Design call (fold into OW-9):** add one line to the model-assignment
matrix: the operator may pre-route a change's apply to Sonnet-first, recorded in `notes.md` — this
legitimizes existing practice without weakening the deepseek-first default; OW-7 telemetry then
decides whether the default itself should move.

---

## Explicit non-findings (diminishing returns — do NOT build these)

- **Verifier sandbox hardening** — the prod-DB backfill incident predates and motivated the
  2026-07-03 denylist speedbump; the accepted-residual disposition (real backstop = repo-level data
  isolation) stands. Cheap upgrade if it recurs: run verifier passes in a disposable git worktree.
  Recorded; do not build now.
- **Session-handoff write skill** — the write-side convention already exists in scaffold-managed
  `knowledge/README.md`; most downstream handoff usage is planned chunking, not crisis. At most a
  content checklist line (optional, OW-9).
- **Scaffold CI** — local commit-test-gate + operator-gated push already enforce green; CI adds a
  remote copy of the same signal. Skip.
- **New-downstream-repo bootstrap script** — 2 downstream repos, additions rare. Write it when
  repo #4 appears (matches the roadmap's own copier-spike conclusion).
- **`lessons.md` bounding** — 142 lines; OW-2's ratchet will drain it structurally. Skip.
- **Multi-repo sync batching** — O(N) manual ceremonies is fine at N=2; revisit at N=4.
- **Relitigating OW-3's frozen shape** — the new evidence (pro-pass yield ≈0) *strengthens* OW-3;
  the further MEDIUM downgrade is the scheduled decision above, gated on telemetry, not a redesign.

**Departing-principal verdict:** after the frozen batch (OW-2/3/5/6) plus OW-1/4 and the efficiency
wave above, scaffold *process* optimization is at diminishing returns. The next marginal token is
worth more spent downstream — extrends still carries ~33 unremediated correctness-audit classes with
zero remediation shipped, and both downstream repos show adoption drift (shadow `plans/` workflow,
audit cadence dead at n=1) that no new scaffold mechanism fixes. Stop optimizing the factory;
ship with it.

---

## Sequencing & orchestrator routing (recorded verdict)

**Everything below is Opus. No remaining backlog item needs Fable.** The judgment calls each item
needed are made in this document; the standard escalation caveat applies (DESIGN-level defect
discovered at propose/apply/verify → stop, escalate to operator/Fable).

Recommended Opus session order:
1. **Apply the frozen batch OW-2 → OW-3 → OW-5 → OW-6** (hard order; OW-2 first makes the one-word
   normative fix from wave-1 finding 1). Nothing in this wave blocks on it, but OW-7/9/11 edit the
   same skill files OW-3 rewrites — landing them before the batch would force rebasing frozen
   artifacts. **Batch first.**
2. **OW-9** (contradiction sweep — cheap, fixes live contradictory instructions, carries the two
   one-line matrix/rule additions).
3. **OW-1, OW-4** (wave-1 detectors; defect-prevention outranks efficiency).
4. **OW-7** (wrapper + telemetry — the sooner it lands, the sooner the scheduled decisions get data).
5. **OW-10**, then **OW-11**, then **OW-8**, then **OW-13**, then **OW-12**.

**Park verdict for this session: PARK EVERYTHING.** No item above must be applied now to unblock
other work; the four frozen changes remain deliberately paused; the only cost of parking is the
known waste OW-3/OW-7 will remove (zero-yield flash passes, hand-rolled delegation) plus deferred
telemetry. Maximize Fable time on judgment, not ceremony.
