# psc-monitor's hand-rolled correctness audit — method extraction

Source repo: `/home/pang/Projects/psc-monitor`. Distills the *method* (not findings) of the
correctness/data-integrity audit (`correctness-audit-2026-07`, the wave/charter/census shape) and
its sibling the test-quality audit (different oracle/catalog shape, worth stealing pieces from).

**Provenance:** psc-monitor's method was itself ported: "ported from the extrends audit playbook
(`extrends:knowledge/reference/audit-methodology-playbook.md`, PD1–PD13) with content fully
re-derived for this repo" (`plans/audit-correctness-quality/brief.md:8-11`). This is a second
hand-rolled implementation of a pattern that already recurred across repos — good evidence for
scaffolding it.

## 1. Artifacts and their roles

- **CHARTER.md** (39 lines, `knowledge/research/correctness-audit-2026-07/CHARTER.md`) — a
  post-hoc prose summary/pointer per wave, not the scope-setting document. Points to the real
  governing doc and each wave's OpenSpec archive dir.
- **The governing brief** (`plans/audit-correctness-quality/brief.md`, 322 lines) — the *actual*
  charter: 10 Ground Rules GR1–GR10 (evidence standard, audit-then-fix, snapshot discipline,
  discovery-mandate exit criterion, independence mechanics, prior-knowledge deference, recording
  rules, finding-ID scheme, reviewer fallibility, artifact preservation — `brief.md:16-66`); a
  **product-derived severity taxonomy S1–S7** (`brief.md:68-86`, see §3); a Fix-Now admission
  criterion (`brief.md:115-138`); the wave plan with per-wave lead lists + discovery-census scope
  (`brief.md:140-262`); exclusions explicitly not inherited from the ported playbook
  (`brief.md:264-272`); a security-sibling boundary (`brief.md:274-283`); executor/model routing
  policy (`brief.md:297-307`).
- **known-findings-ledger.md** (`plans/audit-correctness-quality/`, 209 lines) — do-not-rediscover
  register: FIXED / ACCEPTED-BY-DESIGN / ADMITTED-OPEN, plus a `PRIOR-AUDIT-COVERAGE-MAP` naming
  which subsystems have/haven't had a dedicated pass (`known-findings-ledger.md:1-208`, coverage
  map at `:184-208`).
- **CENSUS.md** (252 lines) — one line per module/surface, exactly one of four dispositions
  (`AUDITED-clean`/`AUDITED-finding`/`LEAD-deferred`/`N/A-<reason>`), each citing evidence,
  **enumeration only, never tallied** (`CENSUS.md:82-83`, brief GR4 at `brief.md:43-47`, GR7
  no-counts rule at `brief.md:56-59`). This is the audit's completeness proof.
- **FINDINGS.md** (4009 lines) — one `## CA-W<wave>-<seq>` section per finding: `Statement`,
  `Evidence` (method-named label), `Repro`, `Scratch DB`, `Severity`, `Recommended fix`, `Effort`
  tag (canonical shape at `FINDINGS.md:116-171`). A **graduation log** at the top
  (`FINDINGS.md:1-100`) records every later refutation session as append-only history, separate
  from the per-finding sections it updates in place. IDs: `CA-W<wave>-<seq>` (GR8,
  `brief.md:60-62`), chosen to avoid two pre-existing colliding "F1–F7" schemes.
- **Per-wave `inventory-w<N>.md`** (change-dir only, not promoted) — the lead-blind independent
  inventory (see §2/§4); its diff against the known lead list appends novel `CA-W<N>-<seq>+`
  findings (`.../tasks.md:52`).
- **review-log.md / notes.md** (change-dir only) — orchestrator commentary, reviewer verdicts,
  operator rulings; not promoted to `knowledge/`.

## 2. Wave protocol

Decomposed **by pipeline stage/subsystem lens**, sequenced upstream-before-downstream
(`brief.md:142-144`): **Wave 0** floor+instruments only, no findings (scratch-DB tooling FN-1,
deterministic baseline FN-2, verify the audit's own SQL-invariant "ruler" before citing it,
`brief.md:146-159`); **Wave 1** data-in (downloader→parser→loader/SCD→diff+schema,
`brief.md:161-188`); **Wave 2** signal-path-out (matcher→dispatch→digest+reports+suppression,
`brief.md:190-218`); **Wave 3** time/billing/ops (drafted, not evidenced as executed,
`brief.md:220-246`); **Wave 4** tests/tooling, S7 only, run last (`brief.md:248-262`). Each wave
carries a pre-identified **lead list** (dated, explicitly non-authoritative — "file:line citations
...are as-of the 2026-07-05 sweep... executors re-locate sites semantically," `brief.md:27-29`)
plus an independent **discovery census** covering every in-scope module.

**Who ran it:** explicit executor policy (`brief.md:297-307`) routes by judgment content:
judgment-heavy work (investigation, findings) → `deepseek-v4-pro`; judgment-free mechanical work →
`deepseek-v4-flash`; Sonnet fallback requires operator acknowledgment. **Severities/evidence
labels are never set by the executor tier, regardless of model** — orchestrator-only (same
citation, reinforced GR1 `brief.md:18-19`). Drafts are `PROPOSED:`, finalized only by the
orchestrator (`CENSUS.md:5-6,28-29`).

**Sequencing mechanics:** each wave = one OpenSpec COMPLEX change, sliced into multiple `opencode
run` invocations gated by an explicit unattended-stop marker: "⛔ WAVE GATE — operator
confirmation required. Executors MUST NOT proceed past this line." (`.../tasks.md:41`). The
independent-inventory step runs as its own **lead-blind** invocation — its executor never sees
tasks/design/proposal/brief, only a module list + taxonomy + output path (GR5,
`.../tasks.md:44-46,51`).

**Checkpointing:** every wave ends with a report at an operator gate; the next wave starts only on
confirmation (`brief.md:292-293`). An emergency-escalation clause lets an actively-occurring
S1/S4 finding cut a remediation change immediately, bypassing the gate (`brief.md:293-296`).

## 3. Oracles

Top-level oracle for *how bad*: the **severity taxonomy** is product-derived, not inherited — built
around one customer-harm model ("acts on the absence of an alert"; worst failure = invisible false
negative): S1 silent-false-negative, S2 wrong-entity/wrong-data, S3 silent-sentinel-failure, S4
permanent-data-loss, S5 entitlement/money-divergence, S6 ops-fragility, S7 dev-quality
(`brief.md:74-82`), with stated divergences from the ported source.

For *is-this-actually-a-bug*, mechanisms observed (most-used first):
- **Repro on a disposable scratch DB** (`VERIFIED-BY-repro`) — inject a synthetic pathological
  state, run the real code path, observe. Example: CA-W1-01 staged a fake truncated zip and ran
  the real `download()`/`_already_processed()` (`FINDINGS.md:138-149`).
- **Trace/absence claim** (`VERIFIED-BY-trace`) — every candidate site enumerated and named
  (CA-W1-02, `FINDINGS.md:183-200`).
- **Live read-only query** against the real ~15M-row dev DB for data-shape questions (CA-W2-07's
  CAP=500 bucket-size check, `knowledge/questions/audit-wave1-remediation-decision.md:48-51`); the
  live DB is always read-only to the audit (GR3, `brief.md:36-42`).
- **Spec/reference cross-check** — implementation vs. a written model doc
  (`knowledge/reference/entity-resolution.md` §11), e.g. CA-W2-10 (`brief.md:213-216`).
- **Documentary verification** — e.g. confirming Companies House's ~24h retention claim against
  CH's own docs rather than trusting the operator (`brief.md:166-168`).
- **Forensic history reconstruction** — replaying archived snapshots on scratch; when root cause
  isn't reachable, recorded honestly as blocked, not force-closed (`.../tasks.md:65`,
  `knowledge/questions/audit-ca-w1-10-closure-blocked.md`).
- **Operator attestation, explicitly flagged** pending confirmation, e.g. `LEAD
  (operator-attested)` (`brief.md:172`).

**Sibling test-quality audit's oracle mechanism** (structurally different, worth stealing): a
**derive-but-flag** policy — build a per-domain "behavior catalog" from spec/reference docs
**before** looking at the tests being graded, with a strict anti-circularity rule ("read spec
sources + implementation only — NOT the test files,"
`knowledge/research/test-quality-audit/METHODOLOGY.md:26-28`), provenance statically checkable via
a `<domain>-sources-read.md` declaring zero `tests/` reads (`test-quality-audit/
A-sources-read.md:1-33`). Undocumented behavior is tagged `DERIVED — unverified` and needs an
**operator ratification gate** before grading uses it (`METHODOLOGY.md:16-24,99-105`). "Build the
oracle before you look at what you're grading" is the sharpest transferable idea here.

## 4. Verification/triage of findings

Every finding starts `LEAD` and only ships with a severity after an **adversarial refutation
pass**: "an independent pass (fresh context; different session/model)... whose explicit brief is
to *refute* the finding... actively seek an innocent explanation. A finding graduates from LEAD
only when the refutation attempt fails" (GR1, `brief.md:18-27`).

**Dedup/independence (GR5):** the independent inventory runs *before* exposure to the lead list;
the two are diffed after (`brief.md:48-51`, mechanics `.../tasks.md:44-52`) — catches missed leads
(→ new IDs) and reconciles overlapping coverage (`CENSUS.md:37` notes when inventory
"independently covered the same module" as a pre-listed lead).

**Who verifies:** orchestrator-only for severity/evidence labels (`brief.md:307`). A later
**graduation playbook** (`knowledge/lessons.md:78-125`) formalizes bulk LEAD→VERIFIED work: one
subagent per LEAD, isolated scratch DB + write dir each (never shared, `lessons.md:93-96`);
concurrency capped at ≤4 (cluster `max_connections=20`, `lessons.md:97`); orchestrator builds its
**own** independent source read of each finding's crux before reading the subagent's verdict, then
reconciles and can overrule (GR9, `lessons.md:99-101,112-125`).

**Correction rate, from the actual graduation log** (`FINDINGS.md:1-100`), 32 LEAD adjudications
across 4 sessions: 2026-07-08 Chain-1 (10): 9 VERIFIED, 1 REFUTED (`:9-11`); 2026-07-09 batch 1
(5): 3 VERIFIED, 1 REFUTED, 1 CLOSED-intentional (`:29-31`); batch 2 (8): 6 VERIFIED, 1 REFUTED, 1
CLOSED-doc-only (`:42-44`); batch 3 (9, final): 7 VERIFIED, 1 REFUTED, 1 CLOSED-intentional, and
**"4 of the 7 VERIFIED were overruled from the refuters' `REFUTED` label"** — the automated
refuter's own verdict was wrong ~4/9 times in that batch, caught only by orchestrator re-check
(`:66-73`). Net: ~4/32 (12.5%) outright refuted-as-filed, plus frequent severity/framing
corrections even on confirmed mechanisms (rule: false *premise* → REFUTED; real-but-milder
mechanism → VERIFIED with severity overrule, `lessons.md:112-120`). One already-shipped finding
(CA-W1-20) was refuted post-archive and, during that refutation, a materially similar *real*
defect (CA-W2-30) was found via a different code path (`FINDINGS.md:3070-3089`) — refutation has
original discovery value, not just gatekeeping.

## 5. Close-out routing

Findings do not auto-convert into fixes: GR2 bans mid-audit fixes except a narrow
audit-comprehensiveness "Fix-Now" test (`brief.md:30-35,115-138`); Waves 0–2 shipped **zero
production-code changes** (`CHARTER.md:13`).

1. **Ranking pass** (`knowledge/questions/audit-wave1-remediation-decision.md`, 19.7KB) — once the
   LEAD pool is fully graduated, a dedicated doc sequences the *verified* pool into remediation
   waves A→B→C→D→E→F→G, grouped by shared code surface/fix mechanism (e.g. Wave A batches
   CA-W1-01/02/03/12/14 as one download-integrity cluster; Wave C batches CA-W2-11+12 because
   decoupling them would widen severity, `:105-137`). Even this scheduling step gets an
   independent check: "an Opus subagent digested the full dossier into a draft... the orchestrator
   spot-checked every load-bearing severity" (`:88-91`).
2. **Operator sign-off** gates the ranked plan plus any entangled product/compliance calls (e.g.
   a GDPR Art-17 redaction posture decision gating Wave C, in `knowledge/decisions/INDEX.md`).
3. **Each remediation wave ships as its own OpenSpec change**, `tasks.md` citing exact `CA-W*` IDs
   and `FINDINGS.md` line ranges as the spec of record
   (`openspec/changes/archive/2026-07-09-audit-remediation-wave-a/tasks.md:1-4`, `notes.md:7-9`),
   acceptance criteria mapped 1:1 to findings (`notes.md:14-24`), and **new regression tests
   shipped with the fix** (`tests/test_downloader.py` created fresh, `.../tasks.md:34-46`).
4. **Follow-on residue is tracked**, not dropped — each remediation wave spins off a
   `knowledge/questions/wave-<x>-follow-ons.md` for deferred items with explicit dispositions
   (`knowledge/questions/wave-a-follow-ons.md:1-30`).
5. **What closes without any enforcing check:** findings labeled `CLOSED, intentional-by-design`
   or `CLOSED, doc-only` close with **no test or check**, only a corrected doc/comment and a
   permanent `FINDINGS.md` record (e.g. CA-W2-26, `FINDINGS.md:40-41`; CA-W1-26,
   `FINDINGS.md:64-65`). Nothing mechanically prevents regression — durability rests on a human
   (or future audit) re-reading `FINDINGS.md`/the ledger (GR6 instructs future briefs to,
   `brief.md:52-55`, but it is a read discipline, not an enforced gate).
6. **Most S7 dev-quality findings and some LEADs never get a scheduled wave** — the ranking plan
   explicitly deprioritizes them ("CA-W1-16 sits in its own latent tier, unranked by rule," `:103`).

## 6. Observed weaknesses of the hand-rolled method

- **High latency, high overhead per finding closed.** Wave 0+1 shipped 2026-07-06; the LEAD pool
  wasn't fully graduated until 2026-07-09 across 4 sessions; remediation Wave A shipped 2026-07-09;
  Waves B–G still gated weeks later per `knowledge/STATUS.md`. Every stage is its own OpenSpec
  change with its own multi-model verify pass.
- **The refuter model is unreliable and needs a second pass every time** — batch 3's 4-of-7
  overrule rate (§4) is a named, repeat risk (`lessons.md:112-126`, "a refuter's REFUTED verdict is
  itself a claim to verify").
- **Cross-wave duplicate discovery happened at least once**: CA-W1-20/CA-W2-30
  (`FINDINGS.md:3070-3089`) — no dedup mechanism beyond the wave-internal GR5 diff and
  orchestrator memory was evidenced.
- **Line-number citations are self-admittedly unreliable** mid-audit — the brief tells executors
  not to trust them (`brief.md:27-29`), an implicit admission of citation rot over a multi-week
  audit.
- **Coverage gaps despite explicit awareness**: frontend, email-content depth, and endpoint-by-
  endpoint authz were flagged as highest-discovery-value gaps in the ledger
  (`known-findings-ledger.md:196-206`) yet deliberately deferred by the wave plan itself
  (`brief.md:258-260`) — naming a gap didn't guarantee closing it.
- **Remediation planning became its own sprawling artifact**: 7 named waves (A–G) plus 5 "Wave E"
  sub-briefs (E1–E5) each needing an explore-brief/premise-review before a tier could be set
  (`knowledge/decisions/INDEX.md:71-74`) — discovery throughput outstripped remediation
  throughput.
- **Closure-without-enforcement is a named, accepted category**, not solved (§5 point 5) — the
  clearest opening for a scaffold-managed finding-closure ratchet to add value over what
  psc-monitor built by hand.
- **Heavy synchronous operator cost**: nearly every stage transition (wave gate, tier
  classification, product/compliance calls, model-fallback acknowledgment) requires a separately
  recorded operator ruling in `knowledge/decisions/INDEX.md`.

## 7. Reusable vocabulary

| Term | Meaning here |
|---|---|
| **Charter** / **brief** | Split in this repo: `CHARTER.md` is a post-hoc summary; `brief.md` is the real scope+rules+taxonomy+plan. A scaffold artifact should probably fold these into one, or name them distinctly on purpose. |
| **Wave** | A bounded, sequenced audit phase scoped to a subsystem/lens, ending at an operator gate. |
| **Census** | Completeness ledger: one disposition per in-scope module (`AUDITED-clean`/`AUDITED-finding`/`LEAD-deferred`/`N/A-<reason>`), enumerated, never tallied. |
| **Finding** | A `CA-W<wave>-<seq>`-ID'd `FINDINGS.md` entry: statement, evidence+method, repro, severity, fix, effort. |
| **Lead** | An unverified candidate finding, pre-identified or inventory-surfaced; no severity until adversarially verified. |
| **Ground rules (GR1–GR10)** | The audit's numbered operating constitution, referenced by number throughout. |
| **Severity taxonomy (S1–S7)** | Product-derived, ranked by customer-harm-invisibility; re-derived per repo, never inherited blind. |
| **Oracle** | Test-quality-audit term: the independent, spec-derived source of truth graded against; "derive-but-flag" when none exists. |
| **Adversarial verification / refutation** | An independent pass whose brief is to try to disprove a finding; graduation happens only when refutation fails. |
| **Graduation** | A `LEAD` becoming a final `VERIFIED-BY-*`/`REFUTED`/`CLOSED-*` label. |
| **VERIFIED-BY-{repro\|trace\|test}** | Method-named evidence labels — never a bare "confirmed." |
| **UNVERIFIABLE-HERE** | Explicit label for claims needing a resource the audit lacks (e.g. live Stripe creds). |
| **Discovery census** | The scope list a wave's independent-inventory pass must cover. |
| **Lead-blind** | An executor deliberately denied the existing lead list, to keep an inventory pass independent (GR5). |
| **Fix-Now criterion** | Narrow admission test for any mid-audit code change; distinct from remediation. |
| **Known-findings ledger** | Do-not-rediscover register (FIXED/ACCEPTED-BY-DESIGN/ADMITTED-OPEN/coverage-map). |
| **Wave gate** | Explicit operator checkpoint between waves; executors must not cross it unattended. |
| **Remediation wave** | A distinct, later, ranked OpenSpec change that fixes already-verified findings — never the same change as the audit wave that found them. |
| **Sweep** | Overloaded: a read-only reconnaissance pass, and separately a data re-migration operation ("re-canonicalisation sweep") — pick one sense for the scaffold. |
