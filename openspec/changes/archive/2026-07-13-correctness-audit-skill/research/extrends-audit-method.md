# extrends correctness-audit method — prior art extraction

Source: `/home/pang/Projects/extrends`. Reverse-engineers the METHOD of the hand-rolled
4-wave correctness audit (`knowledge/research/correctness-audit-2026-07/`, 2026-07-04 →
2026-07-10) plus the earlier, structurally-precedent test audit
(`knowledge/research/test-audit/`, 2026-06-21 → 2026-06-25). Findings content is out of
scope. psc-monitor is being mined separately and is not read here.

## 1. Artifacts and roles

**Three layers per wave, not one.** (1) *Plan layer* — `plans/audit-correctness-quality/
{brief.md, brief-review.md, brief-v1-superseded.md}` (outside `knowledge/`): the actual lead
list and per-wave discovery-shape spec; v1 was adversarially reviewed and superseded by v2,
with v1 kept on disk (PD12, `audit-methodology-playbook.md:101-104`). Prior-knowledge
registers live in a sibling `known-findings-ledger.md`. (2) *Execution-contract layer* — one
OpenSpec change per wave (`openspec/changes/archive/2026-07-04-audit-correctness-quality`
for Wave0+1, `...-wave2/3/4`), normal `proposal.md`/`design.md`/`tasks.md`; checkpointing
lives in `tasks.md` (§2). (3) *Dossier layer* — `knowledge/research/
correctness-audit-2026-07/{CHARTER.md, FINDINGS-wave{1..4}.md}`, the only tracked
deliverable; `tmp/` probe JSON is "regenerable evidence, not a record" (`CHARTER.md:208-214`).

**No CENSUS artifact in the scaffold sense.** The dossier dir holds only CHARTER + 4
FINDINGS files — no separate inventory doc. "Census" is used verbatim exactly once, narrowly:
Wave 4's "full bare-`except Exception` census," a literal grep-and-triage of one exception
pattern (`FINDINGS-wave4.md` W4-M2). The closest thing to a comprehensive pre-audit inventory
is the **earlier** test-audit's `oracle/` directory (7 files, one per capability cluster:
intended behavior / scenarios / edge cases / failure modes / oracle strength / tests-present,
built in a separate pre-execution session — `test-audit/CHARTER.md:1-6,142-156`). The
correctness-audit-2026-07 has no equivalent; it substitutes the brief's "known leads" list
("a floor, not a ceiling," `CHARTER.md:40-43`) plus the ledger. **Gap for the scaffold:**
extrends only built a census-like artifact for the smaller, earlier audit.

**FINDINGS format — two dialects, by design** (`CHARTER.md:6-9`: "adapted, not copied... that
charter organizes findings by taxonomy code across one scan pass; this one organizes by
subsystem wave"). test-audit: `[taxonomy-code] file::test (line) — mechanism. Fix: ...`,
grouped by severity (CRITICAL/HIGH/MED/LOW) then risk tier (T1–T4); taxonomy codes A1–G4
(`test-audit/CHARTER.md:39-79`). correctness-audit-2026-07: `**W{n}-{Subsystem}{n}[letter] —
title.** **{PD3 label}**. file.py:line. Repro: tmp/audit/scan/….json. Severity:
{PD4 class}. Fix sketch: .... Effort: S|M|L.` — no CRITICAL/HIGH/MED/LOW scale at all;
severity is purely the product-specific taxonomy (§4). Example: `FINDINGS-wave1.md:44-56`.
Every wave file closes with a **lead-disposition table** — every charter lead + every
discovery ID (`W{n}-DISC-n`) gets one disposition row, the wave's completeness proof
(`FINDINGS-wave1.md:1102-1193`). Wave 4 alone appends a **program close-out appendix**.

## 2. Wave protocol

**Scoped by subsystem, sequenced by trust-dependency (PD10).** Wave 0 (precondition, not a
wave): fix-now floor hardening (FN1–FN7 — test collection, DB pin, snapshot tooling,
time-freeze, schema check, baseline capture); the only sanctioned in-audit code edits
(`CHARTER.md:20-28`). Wave 1 — data-in (ingestion, aggregation/backfill/factstore, time,
extraction): "a math audit run on top of silently-missing data is measuring noise"
(`CHARTER.md:38`). Wave 2 — scoring math + DB integrity. Wave 3 — measurement/eval-ruler,
determinism, ops, reliability: "audit the ruler before judging with it"
(`CHARTER.md:82-83`). Wave 4 (final) — tests/coverage, LLM-integration, audit-instrument
repair, tooling floor, exception re-triage, docs/clutter: runs last because its subject is
the floor every later remediation stands on.

**Executor routing not uniform.** Mechanical Wave-0 tasks → cheap/fast executor; discovery +
evidence-labeling → a stronger model, with an explicit rule: "never let a cheap model assign
evidence labels: mislabeled evidence is how the superseded v1 brief shipped wrong CONFIRMEDs"
(`playbook:234-237`). Routing is fixed per-wave in `design.md`.

**Checkpointing is a two-stage buffer.** Each investigation task appends a one-line
disposition (lead ID → PD3 label + basis + artifact path) to the change dir's `notes.md`;
separate later "section-assembly" tasks compile those lines + `tmp/audit/scan/*.json` into
the tracked `FINDINGS-waveN.md` prose (`.../tasks.md:13-16`). Wave 4 additionally fanned the
*writing* step to six parallel section-writer subagents — the step that leaked ~29 coverage
percentages past the never-record-counts rule before self-review caught it
(`lessons.md:99-115`, §6).

**Snapshot discipline (PD7): one canonical snapshot per wave**, reused across every probe in
that wave rather than minted per finding — "cheaper, and keeps every finding's repro
comparable against the same fixed state" (`CHARTER.md:115-117,216-225`). Live DB is
read-only throughout; "beware nominally read-only commands that write" (`CHARTER.md:110-114`).
Prior wave's snapshot deleted only once the new one's `PRAGMA quick_check` is confirmed.

**Deterministic-scan-then-judgment inside every wave**, not just test-audit: each wave has a
dedicated oneoff probe script dumping JSON to `tmp/audit/scan/`; prose cites the JSON by path
and never inlines counts (never-record-counts, restated verbatim in every wave preamble).

**Relation to the separate test-audit.** Chronologically prior and the explicit structural
precedent (`CHARTER.md:6-9`), but more fine-grained: judgment fans out **per capability**
(one subagent per capability, checkpointed to `tmp/audit/findings/<capability>.md`,
`test-audit/CHARTER.md:111-116`) via a formal two-layer model (Layer 1 = 6 deterministic
AST/git-log scan scripts; Layer 2 = subagents seeded with `{oracle entry, spec, impl, test,
scan-JSON slice}`). correctness-audit-2026-07 does not replicate this per-capability fan-out
for investigation itself — each wave's ~4 sections read as one continuous pass per wave,
single executor, orchestrator-reviewed; parallel fan-out is reserved for Wave 4's
dossier-*assembly* step only. Granularity difference worth naming: test-audit parallelizes
at capability level, correctness-audit-2026-07 (if at all) at wave/section level.

## 3. Oracles

**D8 verification-method map — pre-registered, not decided at finding-time.** Each lead's
evidence method (execution probe / code-trace+fixture-replay / code-trace-only) is fixed in
advance in `design.md`: "the executor follows this, no rubric-guessing" (`CHARTER.md:119-133`).
Live network APIs are never used to verify a lead; where "live" evidence matters, the audit
cross-references an *existing* gated-live test's prior evidence instead of a fresh call
(W1-I1d, `FINDINGS-wave1.md:84-87`).

**Independent golden-reference re-derivation** — the strongest oracle used. W2-C1 (Kleinberg
burst detection): auditor hand-implements the published paper's equations from scratch
("Reference A"), independently cross-checks against `pybursts`' crash-frame internals
("Reference B"), then diffs shipped `kleinberg.py` against both — "faithfulness-gated" (a
line-for-line transcription of the shipped function is asserted bit-identical to the real
function before any divergence number is trusted) (`FINDINGS-wave2.md:44-114`).

**Self-consistency before real data.** Probes validate against hand-derivable synthetic
fixtures first (W3-E1: "each of the four metric variants asserted against a hand-derived
expected value before any real data was touched," `FINDINGS-wave3.md:59-61`).

**Contract/invariant reasoning** — "the code already knows it happened": does an internal
boolean the code already computes (`complete=True/False`) match ground truth? Fix sketches
repeatedly note the fix exposes an existing internal signal rather than inventing detection
(W1-I1a, `FINDINGS-wave1.md:54-56`).

**Spec-independence as oracle** (test-audit's core method, `test-audit/CHARTER.md:14-32`):
triangulate SPEC (read without reference to `src/`) vs. IMPL vs. TESTS — "if you derive
intended behavior by reading `src/`, you launder the impl's bugs into your oracle."
correctness-audit-2026-07 cites specs opportunistically for real-bug findings but keeps no
comparably rigorous src-blind oracle document.

**Adversarial re-verification (PD1/PD2) is applied to *inherited* dossiers, not each wave's
own output.** The four-pass discipline (docs cross-check, independent sweep, claim spot-check,
floor trust check, `playbook:39-49`) ran once, on the v1→v2 brief transition before Wave 1.
Every wave preamble marks its own findings "PROVISIONAL... not yet adversarially re-verified
by a second pass," and no evidence shows that second pass happening for Waves 1–4 (§6).

## 4. Verification/triage

**Evidence labels (PD3), no bare "CONFIRMED."** `VERIFIED-BY-{repro|test|trace}` / `LEAD` /
`REFUTED` (`CHARTER.md:50-68`) — adopted because "this repo has shipped wrong CONFIRMEDs
before." A repro without a named snapshot path is disqualified from `VERIFIED-BY-repro`
(`CHARTER.md:108-109`).

**Severity (PD4): product-specific 7-class taxonomy**, ranked by the product's own worst
failure mode — `silent-data-drift > ranking-error > board-manipulation > measurement-error >
spend-control > ops-fragility > dev-quality` (`CHARTER.md:70-92`) — explicitly not generic
HIGH/MED/LOW. Every severity is PROVISIONAL, and classification visibly wobbles: W1-I5a/b was
reclassified from `silent-data-drift` to `ops-fragility` mid-write-up because "non-atomicity
manifests as a crash not a silent duplicate" (wave1 lead-disposition, ~1122-1125) — defensible,
but nothing re-audits severity assignments dossier-wide afterward.

**REFUTED is a first-class outcome, not silent deletion** (`CHARTER.md:62-64`): W1-I1e's
"recurring PERMANENT gap" framing partially REFUTED by a 3-run replay showing self-heal within
one cron cycle; W1-T2's "+00:00 lexicographic accident" mechanism REFUTED outright while a
narrower real risk survives. Motivated by a prior retracted false positive ("LIVE DEFECT:
empty digest," `decisions/INDEX.md:90`), cited directly in `CHARTER.md:178-182`.

**Cross-wave dedup: not mechanized, and it visibly failed once.** No documented step checks a
new lead against prior waves' dossiers (PD9 only covers the PRE-audit ledger, not intra-audit
dedup). Concrete miss: **`W3-E3`** (`FINDINGS-wave3.md:185-223`) fully investigates
`labels_io.py`'s corrupt-YAML-destroys-prior-labels mechanism at `labels_io.py:139-145,158-
159,168-182`, severity `silent-data-drift`, full fix sketch. One wave later **`W4-M2a`**
(`FINDINGS-wave4.md:1774-1841`) independently re-derives the **same** destructive-overwrite
mechanism at `labels_io.py:143`/`:228` — same function, same load-failure→silent-
continue→atomic-replace flow — inside Wave 4's from-scratch exception census. `W4-M2a` PD9-
cites `W3-E3` only for an unrelated micro-detail (the `labeled_at` dead statement,
`FINDINGS-wave4.md:2162-2169`), never for the shared main mechanism. This is exactly the kind
of cross-wave duplicate the downstream scaffold gap-analysis flagged as needing manual merge.

**Dossier verification happens at the OpenSpec change's verify phase, spot-check depth.**
Wave 4's close-out: "orchestrator self-review + independent pro verifier pass, zero defects,
both reproduced the two highest-stakes silent-data-drift traces... against source"
(`decisions/INDEX.md:111`) — i.e. 2 of ~19 Wave-4 findings got independent re-derivation; the
rest rely on the single investigative pass.

## 5. Close-out routing

**Decision `audit-first-remediation-deferred`** (`decisions/INDEX.md:103`, 2026-07-06):
operator re-sequenced so the auditor spends remaining time on Waves 3–4, and **all
remediation — including Wave 2's, already pre-digested — is deferred to post-departure**,
executed by a successor. Rationale: no later wave's *trust* depends on a fix landing (PD10
gates on trust, not applied fixes); remediating first would rewrite the files/lines later
waves must cite, forcing snapshot re-mints; zero Wave-2 findings had manifested in prod yet.
Wave 2's five open design decisions were pre-settled as "recommended dispositions" in
`plans/wave2-remediation-handoff.md` so the successor "inherits judgment, not just facts."

**Current state** (`FINDINGS-wave4.md` close-out): Wave 1's `W1-A4pt1`+`W1-T1` were
fast-tracked and shipped 2026-07-05 (`fix-pipeline-time-anchors`) as an explicit,
operator-approved exception interleaved with Wave 2 — not standard flow. Otherwise: "no
`src/` fix has shipped from any wave; each wave produced findings only." Wave 2's queue is
pre-digested/QUEUED; Wave 3's handoff treatment is itself an open operator decision tracked
in `knowledge/questions/INDEX.md`; Wave 4's queue is just its own disposition table. Summed
across all four waves' disposition tables, roughly 30-odd distinct finding IDs sit
unremediated — consistent with the scaffold gap-analysis's "~33 classes, zero remediation"
characterization (not re-derived to an exact count here, per the repo's own
never-record-counts convention).

**Load-bearing contrast: extrends ran two audits with opposite close-out postures on the same
repo.** The earlier test-audit fully remediated within days: "All 8 remediation batches
shipped to `main`... four real production bugs fixed as separate corrective commits"
(`test-audit/FINDINGS.md:358-366`). The later correctness-audit-2026-07 deliberately defers
everything, rationalized by the departing-principal-engineer framing ("the deliverable is
this dossier, not a fixed repo," `CHARTER.md:17-18`). Both postures came from the same
wave/charter/dossier protocol — what differed was an operator sequencing call, not the audit
method. Relevant directly to the scaffold's finding-closure ratchet design.

## 6. Observed weaknesses

- **Cross-wave duplicate finding, undetected by the audit itself** — `W3-E3`/`W4-M2a` on
  `labels_io.py` (§4). No mechanized or documented step checks a new lead against prior
  waves before write-up.
- **The same higher-order defect class recurs across waves, never named as one class.**
  W1-I1 (Wave 1: several collectors return `complete=True` after silently truncating —
  signal computed but never propagates, `FINDINGS-wave1.md:36-43`), W4-M2b (Wave 4:
  `pipeline.py`'s digest-write failure has no `assess_run_health` signal, `FINDINGS-
  wave4.md`~1884-1888), and W4-DISC-5 (Wave 4: LLM gate's `"keep"` field silently
  type-coerces a string to truthy, inverting model intent, `FINDINGS-wave4.md:604-625`) are
  three independent instances, three subsystems, of one pattern: an authoritative
  success/failure signal exists internally but never reaches the layer that would act on it.
  Wave 4 notices the M2a/M2b kinship locally ("sharing the same root pattern: a logged catch
  whose log line does not actually prevent or surface the consequence that matters,"
  `FINDINGS-wave4.md:1886-1888`) but never connects it back to Wave 1's foundational instance
  three waves earlier, and the playbook's transferable defect-class catalog
  (`playbook:161-201`) doesn't fold in this "logged-but-not-gating" sub-pattern either.
- **No symmetric stopping rule for the discovery mandate.** PD6 requires going beyond known
  leads every wave (a thoroughness strength) but nothing bounds how much is enough; each wave
  self-declares "COMPLETE," and the only external check (the disposition table's coverage
  check) verifies charter-named leads are covered — it cannot verify open-ended discovery
  didn't miss something, since no independent census exists to measure against (§1).
- **Adversarial re-verification is front-loaded onto the inherited dossier, not applied
  wave-by-wave to fresh output.** ~30 findings across Waves 1–4 carry only a single
  investigative pass, explicitly marked not-yet-re-verified, with only 2 spot-checked at
  final verify. The methodology's own stated lesson — "mislabeled evidence is how the
  superseded v1 brief shipped wrong CONFIRMEDs" (`playbook:236-237`) — is a risk the
  wave-by-wave process structurally still carries for its own findings, not just inherited
  ones.
- **never-record-counts is easy to violate and needed a deterministic backstop.** The Wave-4
  six-subagent dossier assembly shipped ~29 coverage percentages before self-review caught
  it; fixed via re-delegation plus a purpose-built `_denumeralize_oneoff.py` sweep
  (`lessons.md:99-115`). The rule needs an explicit, domain-specific trap warning per
  delegation brief — "coverage" reads as a legitimate metric, not a banned tally.
- **Method is appended-to, not versioned per wave.** `CHARTER.md` grew from ~226 to 317 lines
  via 3 stacked "scope extension" sections (`CHARTER.md:227-316`); reconstructing the active
  ruleset for wave N means reading cumulatively from the top rather than each wave restating
  its own rules standalone.

## 7. Reusable vocabulary

- **wave** — sequential, subsystem-scoped audit round (Wave 0 precursor + Waves 1–4),
  trust-ordered (PD10), not parallel.
- **charter** — cumulative governing scope+rules doc for the whole program.
- **dossier** — durable output set (CHARTER + FINDINGS-wave* collectively).
- **lead** — named, ID'd defect hypothesis (e.g. `W1-I1`); known leads are "a floor, not a
  ceiling."
- **discovery (mandate)** / **DISC-n** — PD6's requirement to surface leads beyond the known
  list; numbered `W{n}-DISC-{n}` in a wave-global namespace.
- **disposition** / **lead-disposition table** — closing per-lead ledger (PD3 label + PD4
  severity + one-line essence) proving wave completeness.
- **evidence label** — `VERIFIED-BY-{repro|test|trace}` / `LEAD` / `REFUTED` (PD3).
- **repro** / **trace** / **fixture-replay** — the three named evidence-production methods.
- **snapshot discipline** — PD7's read-only `.backup()`-copy isolation; "canonical wave
  snapshot" names the one reused artifact per wave.
- **fix-now** — the sole sanctioned in-audit code edit, admitted only when it hardens the
  audit's own trustworthiness, never the product.
- **fix sketch** — a finding's prescribed remediation, written but never executed in-audit.
- **effort tag** — S/M/L sizing on every finding.
- **severity taxonomy** — product-specific ranked classes (PD4); here: `silent-data-drift`,
  `ranking-error`, `board-manipulation`, `measurement-error`, `spend-control`,
  `ops-fragility`, `dev-quality`.
- **never-record-counts** — no test tallies/row counts/coverage percentages in tracked docs;
  quantities characterized by direction/magnitude class only.
- **audit-then-fix** — PD5's hard sequencing rule (vs. fix-as-found).
- **departing principal engineer** — the audit's operating role framing.
- **prior-knowledge registers** — `accepted-by-design` (don't re-litigate) vs.
  `admitted-open` (absorb with attribution, don't re-find) (PD9).
- **census** — used narrowly, only for one literal inventory (Wave 4's bare-`except
  Exception` census), not a formal artifact type parallel to charter/dossier. No
  comprehensive pre-audit census exists for the correctness audit; the closest analog is the
  earlier, differently-shaped test-audit's `oracle/` catalog.
- **sweep** — a read-only discovery/inventory pass over a bounded surface.
- **class** — defect-class categories in the transferable catalog (e.g. "truncation-vs-
  completeness contract," "silent wrong-direction fallbacks").
- **verification-method map** — D8's pre-registered, per-lead oracle-method assignment,
  fixed before execution.
- **PD-n** — numbered, citable process decisions (PD1–PD13,
  `knowledge/reference/audit-methodology-playbook.md`), the durable how/why record separate
  from any single audit's content.
