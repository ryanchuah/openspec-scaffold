# extrends coverage-gap review (2026-07-12) — second validation of OW-15 + widenings

**Provenance.** extrends ran a departing-principal coverage-gap review of its correctness-audit
program (`extrends/knowledge/research/correctness-audit-2026-07/gap-map-2026-07-11.md`, Fable
session, with `recon-2026-07-11/{taxonomy,coverage-map,post-audit-decay,targeted-probes}.md` as
the recon record). Method: a 30-dimension blind taxonomy written before reading any dossier, then
three read-only subagent surveys (coverage map vs taxonomy; post-audit-decay inventory; targeted
probes of suspect areas), then orchestrator adjudication. **This was an independent execution of
exactly OW-15's Delta 2 — designed without knowledge of the psc review, run the same weekend.**
This doc extracts the scaffold-generalizable results; extrends-specific remediation stays routed
in that repo's own queues.

**Checked against `psc-coverage-gap-review-2026-07-11.md` before writing: everything below is
either explicitly-marked convergent evidence or additive (a widening the psc doc does not
contain).**

---

## 1. Convergent validation of Delta 2 (blind close-out review) — now n=2

- Second repo, second success: against a FOUR-wave, heavily-audited codebase (the audit program
  the psc playbook was originally ported *from*), the blind review still yielded a ranked
  residual list, one process gap with a shipped mechanism (§3), and one live tracker correction
  (a recorded "safe to run manually" play was probe-refuted — it would have double-run a labeled
  eval week). Cost matched psc's: one session, 3–4 read-only subagents.
- **Union evidence for Delta 2's "reviewer writes blind FIRST, then unions with the seed":** the
  two blind taxonomies (psc 45-dim, extrends 30-dim) each contain dimensions the other lacks.
  Concretely: extrends' blind list missed psc's class #1 (backups of non-reconstructible state)
  — and when the psc seed was diffed back against extrends, **that class fired** (never
  chartered in any extrends wave; the weekly "backup created" health line is a class-#6
  partial-✅ shape; routed in extrends' gap-map §5). Cross-repo teeth, in both directions, on
  the checklist's first real use.

## 2. Seed widenings (new dimensions / class extensions for OW-15's Delta 3)

1. **Measurement-pipeline parity.** For any repo with an eval/scorecard/metrics harness: does
   eval grade the *identical artifact path* production publishes, or a re-derivation? No
   extrends wave ever asked it (nearest findings — digest fidelity, CLI write surface — do not
   close it); not in the psc 45-dim seed. Suggested home: group C (output-surface semantics) or
   its own row; conditional dimension (skip if no eval harness).
2. **Run-indexed vs period-indexed derived state under sequential re-runs.** Seed group D covers
   storage idempotency on re-run. The subtler failure survives idempotent storage: derived
   metrics keyed by *run* (streaks, was_new/first-seen flags, survival cohorts) distort when
   runs-per-period ≠ 1. extrends: aggregation verified idempotent, yet a same-week second run
   still inflates entity run-streaks and flips was_new — distorting eval reads. Widen group D:
   "…and for each derived metric, is it keyed by run or by period, and what does a duplicate
   run within one period do to it?"
3. **Phantom capability claims** — widens class #5 (phantom dev tooling: declared ≠ invoked)
   from dev tooling to *product claims*: optional extras/backends/features declared in the
   manifest or README with zero exercised path. extrends: the `[postgres]` extra — never
   installed in any test/CI, with two SQLite-dialect-locked upserts that prove the claim false.
   Disposition pattern generalizes: exercised lane OR ratified declare-unsupported.
4. **Cross-stream/cross-program interference + the boot-doc rule.** No seed dimension covers
   *concurrent programs* (audit remediation vs frozen-but-unapplied feature changes vs live
   operations). extrends: the audit program's risk-window flags pointed into other streams, but
   no feature-stream handoff pointed back — grep-verified one-directional. The load-bearing
   rule: **a sequencing constraint lives in the boot doc of the session that must obey it**, not
   only in the doc that discovered it (extrends had to append its labels_io-before-gold-write
   window into the consuming session's steer before it became real). Suggested home: close-out
   routing text in the `correctness-audit` skill (a routed finding that constrains another
   stream is not "routed" until it is in that stream's boot/handoff doc).
5. **Verified-safety-claim tagging** — widens class #6 (partial-✅ dispositions): any tracker
   claim that *authorizes a state-mutating operator action* ("safe to re-run X; worst case is
   Y") must carry a VERIFIED-BY tag or an explicit UNVERIFIED marker. extrends: a recorded
   "manual run today is safe, dates to next week" play was wrong in both directions (it anchored
   to the already-scored week AND the distortion path was live) — caught only because the blind
   review happened to probe it.
6. **Named smell for the group-I config census:** pydantic-settings v2 with `extra="ignore"`
   and no `env_prefix` — typo'd or prefixed env vars become silent no-ops. Second live instance
   (psc's dropped Wave 3 chartered the same census; extrends confirms the class with a greppable
   signature worth naming in the checklist).
7. **(Probe instruction, small) Hazard liveness against deployed config, not code defaults.**
   extrends' re-run distortion was first mis-graded "dormant" because the code default for the
   relevant stage is off — production has it on. Audit probes SHOULD grade liveness against the
   deployed configuration (.env / activation records), with the default noted separately.

## 3. Delta 4 candidate — coverage liveness AFTER close-out (post-close unaudited-code ledger)

Delta 1 defends dossier liveness *before* close-out (an unfinished audit must stay visible).
Nothing defends coverage *after* a clean close-out: every wave audits a snapshot, so runtime code
shipped later is unaudited by construction, and wave-level scrutiny never re-fires. This
mechanizes blind-spot class #7 (point-in-time audits need a convention) *as applied to the audit
program itself*, with a shipped reference implementation:

- extrends found ~8 runtime items shipped after the wave that owned their subsystem — the top
  one on the live publish path with **no spec** and two live-only failure modes; the largest
  (~multi-script gold-labeling tooling that writes the eval ground truth) postdated the FINAL
  wave entirely and had zero pytest coverage.
- Mechanism (reference impl: `extrends/knowledge/research/correctness-audit-2026-07/
  POST-WAVE4-LEDGER.md`): a ledger seeded at close-out; **any change whose diff touches
  persistence or publish paths (or writes eval ground truth) appends one line at verify/archive
  time** (commit, subsystem, wave-owner, spec?, review tier); when the open set accumulates
  several persistence-touching entries, cut a mini-wave from the ledger instead of trusting
  per-change verifier passes alone.
- OW-15 shape: one more skill-text/close-out requirement + optionally a knowledge-lint check
  (ledger exists after close-out; entries well-formed). Cheap, deterministic.

## 4. Small adjacent process candidate (placement TBD — not audit-taxonomy)

**Committed-handoffs check.** extrends' departure review found seven load-bearing boot/handoff
docs (session boot contexts, premise-review records) sitting *untracked* in the working tree —
a handoff that isn't committed isn't a handoff. Candidate: a session-end/departure checklist
line, or an untracked-`plans/`-files knowledge-lint check; pairs naturally with OW-13's optional
plans-count lint. Operator discretion.

## 5. Routing

**Folded into OW-15 — no new OW number.** Same capability, same apply-after-OW-5 gate, one
owner; the OW-15 entry in `OUTSTANDING-WORK.md` (this dir) now carries an extrends-convergence
paragraph: Delta 4 (§3), the Delta-3 widenings (§2), and the §4 process candidate. Roadmap
mirror updated; awareness pointer appended to the OW-5 change dir's `notes.md` (freeze NOT
reopened). Reverse-merge already done downstream: psc class #1 fired against extrends and is
routed in extrends' own queue (`gap-map-2026-07-11.md §5`) — first evidence the checklist pays
across repos in both directions.
