# GAP 2 evidence base — composition-audit-cadence (OW-6)

Assembled for the OW-6 proposal designer. Sources: `knowledge/research/scaffold-gap-analysis-2026-07/{SYNTHESIS,psc-issues,extrends-issues,scaffold-procedures}.md`.
All quotes verbatim from those files; all IDs quoted as they appear in source.

**Scope note (important disambiguation):** GAP 2 and GAP 6 are two different scaffold gaps that
both got worked in this backlog. GAP 6 (→ `correctness-audit-skill`, OW-5, already proposed) is
about standardizing the **heavyweight, hand-rolled, LLM-driven wave audit** (CHARTER/CENSUS/
FINDINGS) that both downstream repos built from scratch. GAP 2 (→ this change, OW-6) is
specifically about the **cheap, already-built, whole-repo deterministic detectors** (`jscpd`,
`vulture`, `audit_scope.py scan`, `knowledge-drift-review`) that exist in the scaffold today but
are off-by-default and run on no schedule. Most of the composition-shaped bugs catalogued below
were actually caught by the *heavyweight* audits (OW-5's territory), not by the cheap detectors —
that asymmetry is the central design question this evidence base surfaces for OW-6: what does a
cheap cadenced pass add on top of OW-5, rather than duplicate it.

---

## 1. GAP 2 — verbatim from SYNTHESIS.md (lines 55-62)

> ### GAP 2 — Verify is single-diff-scoped; nothing audits accreted composition
> The verify SKILL is explicitly one-diff-scoped. Whole-repo/multi-commit views (`jscpd`,
> `vulture`, `audit_scope.py scan`, `knowledge-drift-review`) exist but are **off-by-default
> in the operator-pulled audit layer, wired to no cadence.** So a subsystem assembled from 15
> individually-approved changes is never reviewed *as a whole* — which is exactly the seam the
> downstream audits mined.
> **Fix direction:** promote a **first-class, cadenced composition-audit** (the thing both
> repos hand-built) into a scaffold skill, seeded by the whole-repo detectors, feeding GAP 1.

Note: the fix direction's parenthetical ("the thing both repos hand-built") is aspirational/
imprecise in the source — what both repos actually hand-built was the *heavyweight* wave-audit
apparatus (GAP 6/OW-5 territory), not a cheap cadenced detector sweep. Read literally, GAP 2's
own diagnosis (jscpd/vulture/audit_scope/knowledge-drift-review "off-by-default... wired to no
cadence") is about the cheap layer; the fix direction should be read as "give the cheap layer a
cadence and a home," with GAP 6 separately covering the heavyweight audit's standardization.

## 2. Other SYNTHESIS.md lines touching composition, cadence, jscpd, vulture, knowledge-drift-review, audit_scope

- **Evidence section (lines 27-29):** "Both repos independently **reinvented a multi-wave
  correctness-audit program** (CHARTER → CENSUS → wave FINDINGS → remediation change) —
  machinery the scaffold does not provide. Teams don't build that when the standard verify
  gate is catching things."
- **Cross-cutting recurrence (lines 30-37):** psc-monitor's B5/F16 sibling recurrences and
  extrends' MEAS-1/OPS-2/TQ-2 recurrences are cited as the direct evidence that "a
  human/agent re-reading the whole corpus **still doesn't durably generalize a pattern into a
  guard**" (line 38) — i.e. even when composition IS reviewed (by a hand-built audit), the
  finding doesn't automatically feed forward; this is GAP 1's territory but it bounds what
  GAP 2 alone can promise (a cadenced sweep without GAP 1's ratchet will re-find, not
  prevent).
- **GAP 6 (lines 103-108):** "`run-audit` is deterministic-detector-only. The **LLM
  correctness audit**... is not a scaffold skill... **Fix direction:** a `correctness-audit`
  scaffold skill that standardizes the wave/charter/census shape and **routes every
  generalizable finding into GAP 1's ratchet** on close." — confirms GAP 6 = heavyweight
  audit (OW-5), separate from GAP 2's cheap-detector-cadence scope.
- **Preserve-list (lines 130-137):** does **not** mention jscpd/vulture/composition at all —
  the "what is working" list is scoped to tiered process, premise/direction gates, and
  simplicity/security gates. Silence here is itself informative: nobody argues the existing
  cheap-detector layer is *already* working well; it's simply absent from both the "broken"
  and "keep" lists because it has never been exercised on a cadence to know.
- **Sequencing (lines 155-162):** "5. **GAP 6 + GAP 2 (correctness-audit + composition-audit
  skills)** — larger; land after the ratchet exists so their findings have somewhere to go."
  Explicit design constraint: OW-6 should assume GAP 1 (lesson-check-ratchet, OW-2) is either
  landed or landing alongside it, since a composition-audit finding with no ratchet just
  becomes another prose lesson that recurs (per the cross-cutting recurrence evidence above).

## 3. scaffold-procedures.md — composition detectors off-by-default + verify diff-scoped

Direct answer to "(b) Does any mechanism review the accreted composition of many past
changes, rather than a single diff?" (lines 205-217), quoted at length because it is the
single most load-bearing paragraph for OW-6's design:

> "**PARTIALLY, and not wired into the per-change gate.** Three candidates, none 'run
> automatically every change': `jscpd`/`vulture` (checks.py, whole-repo scan for cross-change
> duplication/dead-code, but **disabled by default**, audit-time only); `knowledge-drift-review`
> skill (explicit whole-tree sweep for stale 'not yet built' claims, intra-doc contradictions,
> buried gates — its own text: '**Not** wired into every `openspec-archive-change` run...
> invoke it on operator request or on a recurring cadence,' pull-only); `audit_scope.py scan`
> (churn+complexity hotspots since the last `audit/<date>` tag — genuinely multi-commit, but an
> informational fact snapshot inside the operator-invoked `run-audit` cycle, never a gate). The
> verify skill's simplicity/quality gate is explicitly scoped OFF from this: 'review of **the
> change's `git diff`**' — single-diff only, by its own words. Net: the capability exists but
> lives entirely in the operator-pulled, off-by-default audit layer, never the mandatory
> verify/archive path."

Live `checks.py --list` output in this repo (lines 9-22) confirms the disabled state
concretely: `jscpd` = `heavy / check / disabled / unavailable`; `vulture` = `heavy / check /
disabled / available` (i.e. installed but switched off); `radon` and `index-coverage` also
`disabled`. Registry annotation on jscpd specifically (line 167): "**the one built-in
mechanism that scans whole-repo accreted duplication, not a single diff**, but off."

Also relevant — cost ledger context for why a *cheap* cadenced pass is the right shape (not
another heavyweight model-pass tier): the existing verify stack already runs self→pro→flash
identically 3× per MEDIUM/COMPLEX change (~9-14 model passes per change, lines 219-229) — GAP
2/OW-6 should not add a fourth expensive per-change pass; the detectors it promotes
(jscpd/vulture/audit_scope/knowledge-drift-review) are deterministic/cheap by construction,
which is what makes a *cadence* (not a per-diff gate) the appropriate trigger shape.

---

## 4. Composition-shaped defect classes — psc-issues.md

For each: ID, one-line shape, why single-diff verify structurally could not see it.

| ID | Shape | Why single-diff verify missed it |
|---|---|---|
| **CFG-1** (`_DROPPABLE_INDEXES` vs `SCHEMA_STATEMENTS`, `init_db.py` vs migrations, `DiffRow` NamedTuple vs SQL SELECT lists, `SIGNAL_LABELS` duplicated) | Two hand-synced parallel artifacts drift with nothing enforcing agreement; confirmed live drift in one instance (migration 005's index never added to the droppable list) | Each of the two artifacts was correct *at the time its own diff was reviewed*; drift only exists in the relationship between two changes made at different times — a diff-scoped review of either change alone has no visibility into the other's current state |
| **SCALE-1** (CA-W2-05, `matcher.py:521-523`) | Unbounded `SELECT ... FROM alerts` a few lines from a comment describing the prior F17 incident; F17's fix paginated the *diff* fetch but left the *alerts* fetch unbounded | The B5 lesson ("green tests are scale-blind") was written down after the F17/B5 incident but never became a check; the sibling unbounded query shipped in a *later, separate* change whose diff-scoped verify had no reason to re-read the earlier incident's context |
| **TXN-1** (F16 historical incident + CA-W2-02) | Test fixture uses `autocommit=TRUE`, production doesn't — hides an uncommitted-visibility bug; CA-W2-02 sits in the same file/function family and later found the failure-handling path F16's fix shifted risk onto | F16's fix addressed its own diff; the sibling failure mode existed in adjacent code untouched by F16's diff and was never re-examined until a later whole-corpus audit |
| **RETRY-1** (CA-W2-02, CA-W2-03, CA-W2-04) | Side-effecting write (entry INSERT) commits before a dependent step (`backfill_for_entry()`); if the dependent step throws, no retry path exists | The commit-then-dependent-step pattern is only a bug in relation to *how a later caller uses* the function — a diff review of the write path alone, or of the caller alone, doesn't see the composed failure mode |
| **DOC-1** (test-quality "Conflict C#1"; CA-W1-20; CA-W2-18) | Tracked reference doc's field names drift from the live implementation, nothing (test/lint/CI) fails when they diverge | Classic composition drift: the doc was accurate when written, the code changed in a later, separate diff, and no mechanism cross-checks doc against code on an ongoing basis — named as exactly `knowledge-drift-review`'s target shape, but that skill is pull-only/cadence-less per scaffold-procedures.md |
| **Cross-cutting #2** (explicit, lines 281-284 of psc-issues.md) | "**Verify gates review diffs, not accreted subsystems.** The audit exists because parser/loader, entity-resolution, and email content 'never had a dedicated pass' — an admission that nothing periodically re-examines a capability's whole surface as it accretes across many individually-passing changes." | This is the corpus's own explicit statement of GAP 2 |
| **Cross-cutting #1** (lines 274-279) | "Lessons get written as prose, not turned into checks, and the same bug recurs" — B5→CA-W2-05, F16→CA-W2-02, each a sibling instance surviving past the incident until the audit re-found it by hand | Ties GAP 2 to GAP 1: a composition sweep without a ratchet just re-discovers the same shape later |

## 5. Composition-shaped defect classes — extrends-issues.md

This corpus is the richer source for composition evidence because it explicitly tracks
findings that **recurred within the same audit program**, giving tighter cadence data than
psc-monitor's cross-incident recurrences.

| ID | Shape | Why single-diff verify missed it |
|---|---|---|
| **MEAS-1** (W3-E3 `labels_io.py` → W4-M2a `console/labels_io.py`) | "The identical catch-log-continue-with-empty-collection shape recurred in a sibling module a whole wave later" — corrupt-input load failure silently destroys prior ground-truth labels; recurred in a *different module* one wave (not months) after the first instance was found | Each module's own diff-scoped verify saw only its own file; the shared anti-pattern across two independently-authored modules is only visible by reading both together, which no per-diff gate does |
| **OPS-2** (W3-O4/W3-DISC-14 → W4-M2b, "recurs 3x across waves 3-4") | `assess_run_health`'s fixed signal list never reads a given fail-soft branch's status field — found in WSV/enrich (wave 3), confirmed inconsistent vs. market-moves (wave 3), then found again in `write_digest`/`published_count` (wave 4) | Same shape: each new fail-soft branch is added in its own diff, correctly reviewed on its own terms, but nothing cross-references the fixed enumerated signal list in `run_health.py` against the *current, accreted* set of fail-soft sites across the whole codebase |
| **TQ-2** (correctness-audit wave 4 AND separate test-audit TA-6, independently) | Mock boundary is the module-under-test itself, not the real I/O edge (`requests.post`, real DB session) — "the identical anti-pattern was independently rediscovered in the correctness audit AND the test-audit... itself evidence this is a systemic, not incidental, gap" | Each individual test's diff looked reasonable in isolation (mocking is normal); only a whole-suite sweep surfaced that the pattern was systemic across many files |
| **DRIFT-1** (W2-DISC-2, W2-DISC-3, W2-D2) | Two code paths meant to behave the same (documented duplicate/parity claim) quietly stop matching — one enforces validation, its twin silently doesn't | Each twin was correct when last touched; divergence accretes as one twin gets a fix/feature the other doesn't, invisible to a diff review of either twin alone. **Directly relevant to jscpd**: proposed fix is "a deterministic checks.py detector for near-duplicate functions (AST-similarity scan)" |
| **DET-1** (W3-N1, W3-DISC-5, W3-N2, 4 sort sites) | Nondeterministic persisted rank from unordered set/dict iteration or un-tiebroken sort, across at least 4 independent sites in the codebase | "The fix pattern is identical and mechanical at each site" but each site was authored/reviewed separately; only a whole-repo grep found all 4 |
| **TOOL-2** (W4-M1, W4-DISC-8, W4-T4a, W4-T4b) | Audit-tool provisioning drift **and** — most directly relevant to OW-6 — "an entire check tier (`radon`/`jscpd`/`vulture`/`index-coverage`) is silently disabled by default with no rationale — a clean `just audit-report` run looks identical to those checks having run and passed" | This is extrends' own version of GAP 2's diagnosis, independently arrived at: whole-repo detectors exist, are off, and their absence is invisible |
| **Cross-cutting #1** (extrends, lines 351-361) | "**The identical failure shape recurs across waves/corpora before anyone names it as a class.**" Explicitly lists MEAS-1, OPS-2, and the TQ-2 wrong-boundary-mocking cross-audit rediscovery as the evidence, concluding "None of these recurrences were caught by a standing rule after the first instance; each was only visible because a human/agent happened to re-read that subsystem in a later wave." | This is the corpus's own explicit statement of what a cadenced composition pass would catch |
| **Cross-cutting #6** (extrends, lines 395-406) | Cross-repo agreement statement: "the recurrence happens **inside the same audit program**, not months later: MEAS-1's two sites and OPS-2's three sites recurred *within the same multi-week audit sweep*, one wave apart, before anyone generalized the pattern into a standing rule... This is the single strongest, most concretely-evidenced argument in the whole corpus for turning named recurring shapes into permanent `checks.py` detectors instead of dossier prose." | Strongest single passage in either corpus tying composition-recurrence directly to a cadence argument |

---

## 6. Evidence FOR a cadenced composition pass

Bugs that accreted across approved changes and were only caught by a later whole-repo audit
(or never, in extrends' case — remediation is fully deferred):

1. **CA-W2-05 / SCALE-1 (psc-monitor)** — an unbounded `fetchall()` in `matcher.py`, a
   sibling of the incident (F17/B5) that had already produced a written lesson
   ("audit each pipeline step's input domain, not just the step you're measuring... the step
   nobody is looking at is the one that kills you" — psc-issues.md line 302-303). The lesson
   existed; no per-diff gate enforced it on the sibling function; only the wave-2 correctness
   audit found it, months after the incident that should have prevented it.
2. **MEAS-1 (extrends)** — ground-truth-destroying load bug recurred in a *different module*
   one wave after the first instance, inside a single audit program, before anyone had
   generalized the pattern. This is the tightest recurrence-interval evidence in either
   corpus: not "months later" but "one wave apart" — i.e., the composition-review cadence
   that *did* exist (the audit's own wave structure) was itself barely fast enough to catch
   the second instance before a third could ship.
3. **OPS-2 (extrends)** — the identical "fail-soft branch invisible to `assess_run_health`"
   shape found three separate times (W3-O4, W3-DISC-14 as an inconsistency check, W4-M2b) —
   each new instance shipped through a clean per-diff verify because each new fail-soft
   branch, on its own diff, looks like ordinary defensive code; only a sweep that reads the
   fixed signal list against the *current full set* of fail-soft sites reveals the gap.
4. **Extrends' base-rate case** — "no runtime-correctness audit had ever executed on this
   repo" across ~45 archived feature changes before Wave 1 ran. Every defect class in that
   corpus (29+ findings just in wave 1) accreted silently for the entire life of the repo
   under a working per-diff verify gate, because nothing was cadenced to look at the whole
   at any interval, not even a long one.
5. **CFG-1 / DET-1 (both corpora)** — mechanically-shaped drift (parallel-artifact
   desync, nondeterministic-sort sites) that a cheap deterministic detector (a paired-artifact
   diff check, an AST grep for unstable sort keys) would catch immediately and cheaply,
   *if it ran on any cadence at all* — these are the strongest candidates for the actual
   detector layer (jscpd/vulture-adjacent custom checks) GAP 2 wants promoted, as opposed to
   needing a heavyweight LLM audit.

## 7. Counter-evidence / limits

**(a) Composition-shaped findings a jscpd/vulture-class detector could NOT have caught** —
these needed LLM/human judgment even though they are compositional in nature:

- **MATH-1 (extrends)** — Kleinberg burst-detection parameter-role swap and ÷n-vs-÷(n−1)
  variance convention. Found by hand-deriving the published algorithm's actual equations and
  diffing against the code; "no existing test compared against them, only internal
  self-consistency checks." No duplication/dead-code/complexity detector would surface a
  subtle deviation from an external published formula.
- **TA-2 (extrends)**, the corpus's own "clearest preventability story" for weak tests hiding
  real bugs — explicitly stated: "**Generic detectors cannot find these — they are
  domain-logic-boundary bugs**" (extrends-issues.md line 291).
- **ER-1/SUP-1 (psc)** — entity-resolution and suppression-correctness semantics are named
  as "domain-defined" in SYNTHESIS.md's own non-gaps list (lines 112-122): "the most a
  scaffold can add is an eval-gate diffing against curated ground truth, which is a per-repo
  asset, not a generic check."
- **EXT-1 (extrends)** — NLP term-fragmentation; SYNTHESIS.md's non-gaps list again: "no
  general scaffold mechanism would realistically catch this."
- **W4-T4(b) / TOOL-2 (extrends), the most direct counter-evidence for THIS specific
  detector family:** "jscpd's token-exact matching missed a three-way duplicated
  LLM-response-handling loop across three files — 'materially undersold by the jscpd report
  alone.'" This is load-bearing: even where jscpd *did* run (as an audit-time one-off), its
  token-exact matching algorithm undersold the true duplication footprint. A cadenced jscpd
  pass is not a complete composition-audit substitute; it needs either a semantic-similarity
  layer or an LLM read-through to catch what token-exact matching misses.

**(b) Findings the hand-rolled heavyweight correctness audits (OW-5's territory) DID catch,
that a cheap detector would not have** — the great majority of the catalogue above. Of ~30+
composition-shaped classes across both corpora, only a handful (CFG-1, DET-1, TA-3's
tuple-discard pattern, W2-D1's missing-UNIQUE-constraint pattern, DRIFT-1's near-duplicate-
function pairing) are explicitly named as candidates for a **deterministic checks.py
detector**. Everything else (MEAS-1, OPS-2, TQ-2, ENTITY-1, MATH-1, SCORE-EDGE-1, AGG-1,
TIME-1, TA-2, TA-5, and more) required a human/LLM reading whole modules against each other
or against a reconstructed behavioral oracle — i.e., required the heavyweight wave-audit
machinery, not a cheap scan.

**Implication for OW-6's design:** the evidence base does not support positioning a cadenced
jscpd/vulture/audit_scope/knowledge-drift-review sweep as a replacement for, or even a
reliable early-warning system for, most of what OW-5's heavyweight audit catches. What it
*does* support is a cheap, high-frequency tripwire for the narrow, genuinely mechanical slice
(parallel-artifact drift, dead code, exact-duplication, doc/code field-name drift, unstable
sort keys) that today ships invisibly purely because the existing cheap detectors are
switched off — a real, if narrower, gap than "catch what OW-5 catches, faster."

## 8. Cadence calibration signal

Data on how long composition bugs sat live before being found, to calibrate a trigger
threshold:

- **Extrends, unbounded case:** ~45 archived feature changes shipped with a working per-diff
  verify gate before *any* whole-repo audit ran — i.e., zero cadence produced an unbounded
  latency (the entire pre-audit life of the repo). This is the strongest argument that *any*
  cadence, even an infrequent one, beats none.
- **Extrends, tightest recurrence interval:** MEAS-1 and OPS-2 each recurred **"one wave
  apart, inside the same audit program"** (SYNTHESIS.md line 37; extrends-issues.md lines
  399-401) — i.e., days-to-low-single-digit-weeks, not months. The audit's own wave cadence
  was fast enough to catch the second instance but not fast enough to prevent it from
  shipping in the first place; a per-change-count or short-calendar cadence is what this
  data point argues for, not a quarterly-or-longer one.
- **psc-monitor, cross-incident interval:** the B5 lesson was dated **2026-06-12**; the
  correctness audit that re-found the sibling bug (CA-W2-05) lives in a directory dated
  `correctness-audit-2026-07` — i.e., roughly **3-6 weeks** elapsed between the incident that
  should have prevented the class and the ad hoc audit that caught the sibling. SYNTHESIS.md
  characterizes this loosely as "months later" (line 33), but the primary-source dates in
  psc-issues.md support a shorter interval — worth the designer re-confirming the exact CA-W2
  wave date if precise calibration matters, but even the conservative reading is weeks, not
  quarters.
- **Trigger-shape implication:** because extrends' worst case is "never had a cadence at
  all" and the corpora's tightest recurrence data is on the order of weeks (not months), a
  designer should treat "N approved changes since last composition pass" (count-based,
  matching how the audits themselves were provoked — by change accretion, not calendar time)
  as at least as strong a candidate trigger as a fixed calendar interval. Neither corpus
  supplies a clean natural threshold (no data point isolates "exactly when a cheap detector
  alone would have fired first"), so the designer will need to pick a threshold defensibly
  (e.g., anchored to the existing `run-audit`/`audit_scope.py scan` cadence already used
  operator-side) rather than derive one purely from this evidence.
