# psc-monitor — distilled defect classes (for scaffold gap analysis)

Source: `psc-monitor/knowledge/research/correctness-audit-2026-07/{FINDINGS,CENSUS,CHARTER}.md`,
`psc-monitor/knowledge/research/test-quality-audit/FINDINGS.md`, `psc-monitor/knowledge/lessons.md`,
`psc-monitor/plans/audit-correctness-quality/brief.md`, plus wave0/wave1/wave2/wave-a/wave-e1/wave-e2
change dirs. No findings invented; IDs are quoted verbatim from the corpus.

## Meta

**Why this audit existed (corpus's own words):** the premise-review verdict names the root problem as
"systematic gaps in correctness coverage across the entire pipeline... not a single defect or outage,"
targeting subsystems that **"never had a dedicated pass"**: parser/loader data-correctness, a
from-scratch entity-resolution pass, email digest content, frontend. This means ordinary per-change
verify (self-review + pro/flash) only ever inspects one change's diff — nothing re-sweeps an entire
accreted subsystem. Many individually-reviewed changes composed into these defects; only a hand-built
audit ever looked at the composition.

**Explicit process/gate gaps named (not code bugs):**
- `brief.md` §3: local commit gates (`test-gate.sh`, `scaffold_check.py`) are Claude-harness-only —
  DeepSeek/human commits bypass them, CI is the backstop, and **"CI runs no ruff"** (no CI backstop for
  the lint leg). No type checker, no coverage config existed before this audit added `pytest-cov` itself.
- `lessons.md` B5 (2026-06-12 livelock): **"Green tests are scale-blind. 209 tests + green CI said
  nothing about a path whose input was 14.6M rows, because no fixture exceeds a few dozen."** Directly
  foreshadows CA-W2-05 below — the same bug pattern recurred in a sibling function after the incident.
- `lessons.md` F16: a backfill "passed in tests because the test fixture uses `autocommit=TRUE`
  (production does not)" — fixture/production semantics mismatch hid a real bug.
- Test-quality audit: suite is honest (0 forced-green, 0 mirrors-implementation) — the defects found are
  *gaps* in what's tested, not deception. Its one confirmed production bug (B-D-36) existed because the
  exception path had zero coverage.

**Scale (approximate — the corpus itself refuses tallies per its own GR7 rule; this is my
reconstruction):** Wave 1: 12 originally-verified + 14 LEADs, all later graduated (~9 net
REFUTED/CLOSED). Wave 2: 11 originally-verified + 19 LEADs, all later graduated (~5 net
REFUTED/CLOSED). Across ~55 total items, a handful are S1 (silent-false-negative)/S2 (wrong-data,
suppression-leak) carrying real remediation weight; most are S6/S7 (ops-fragility, dev-quality).
Test-quality audit: 5 FLAKY, 18 WEAK, 12 BLOATED, 1 FRAGILE, 6 PARAM, 27 hard-MISSING + 13
partial-MISSING behaviors, 1 confirmed production bug (B-D-36), 2 bug-or-policy items still
unratified.

**Bespoke audit machinery:** yes, extensively. The correctness audit ported a whole methodology from a
different project ("extrends"), re-deriving a severity taxonomy (S1–S7), ten ground rules (evidence
standards, audit-then-fix separation, scratch-DB discipline, census exit criteria, lead-blind
independence, a LEAD→VERIFIED adversarial-refutation playbook), a per-module disposition ledger
(`CENSUS.md`), and scratch-DB tooling — none of which exist in the standard OpenSpec lifecycle. That a
heavier, bespoke, wave-based apparatus had to be built on top of the standard verify gate is itself the
strongest evidence the standard gate was judged structurally insufficient for this class of defect.

## Defect classes

### DL-1: Download-path integrity gaps (stale/corrupt snapshot silently accepted)
- **Breaks:** downloader can return a stale/partial/unvalidated file; dedup is permanently dead because
  the field it compares is never written; no retry/backoff.
- **Prevalence:** 4 findings, max **S1**/S4-framing (permanent SCD gap under CH's ~24h retention).
- **Examples:** CA-W1-01 (`downloader.py:98-149` fallthrough returns stale dest, never re-downloads),
  CA-W1-02 (content-length read, never compared to final size), CA-W1-12 (`file_sha256` never written).
- **Root cause:** data-correctness-logic.
- **Preventability:** Plausible — a verify-gate rule requiring adversarial-input eyeballing for any
  function whose output becomes a permanent data source, or an acceptance-criteria checklist item
  ("every external fetch validates its own output"). **Status: shipped** (`audit-remediation-wave-a`,
  2026-07-09).

### DL-2: Loader circuit-breaker gaps + no content witness for the authoritative date
- **Breaks:** all three loader guards skip on an empty DB; blanket `--force` disables all at once;
  `snapshot_date` is filename-regex-parsed with nothing to cross-check it against.
- **Prevalence:** 2 findings, **S1** each.
- **Examples:** CA-W1-04 (`loader.py:354-413`), CA-W1-05 (filename-only date).
- **Root cause:** data-correctness-logic.
- **Preventability:** Partly domain-specific, but "a guard unconditionally skipped under one named
  condition, or one flag silencing N guards at once" is a checklist-flaggable shape. **Status: in
  progress** (`audit-remediation-wave-e2` explore-brief accepted 2026-07-10, not yet applied).

### CFG-1: Hand-synced parallel artifacts drift with no structural link or test
- **Breaks:** two lists/structures required to stay in lockstep are hand-maintained with nothing
  enforcing agreement.
- **Prevalence:** 4 findings; **confirmed live drift** in one.
- **Examples:** CA-W1-08 — `_DROPPABLE_INDEXES` vs `SCHEMA_STATEMENTS`; migration 005's
  `idx_appt_company_number` was never added to the droppable list, "no test asserting agreement." CA-W1-07
  (`init_db.py` vs migrations, convention-only parity). CA-W2-14 (`DiffRow` NamedTuple positionally
  coupled to two SQL `SELECT` lists, no runtime assertion). CA-W2-18 (`SIGNAL_LABELS` duplicated
  byte-identically in two modules).
- **Root cause:** config-wiring.
- **Preventability:** **High** — cleanest candidate for a new `checks.py` detector: declare paired
  artifacts in `checks.toml` and diff them. Would have caught CA-W1-08 before the audit did.

### ER-1: Entity/identity dedup non-determinism and drift
- **Breaks:** identity mechanics (dedup tiebreak, canonical-name computation) aren't fully deterministic
  or versioned — two runs, or two write sites, can disagree about who a person is.
- **Prevalence:** 3 findings, **S1/S2**; one has confirmed live drift (~1% of sampled rows).
- **Examples:** CA-W1-06 (`DISTINCT ON ... ORDER BY raw_name` tiebreak underdetermined on ties, can flip
  CEASED/ACTIVE across runs). CA-W1-16 (natures-of-control parsing silently drops data, suppresses
  CONTROL_CHANGE diffs). CA-W2-01 (`normalise()` output persisted at 4+ sites, no version witness,
  confirmed divergence).
- **Root cause:** entity-resolution-domain.
- **Preventability:** Mostly domain-specific, but "derived value persisted at multiple independent write
  sites with no version stamp" is a design-review-checklist smell. **Status: in progress**
  (`audit-remediation-wave-e1`, active COMPLEX change as of 2026-07-10).

### SUP-1: Suppression (GDPR-adjacent) output-correctness gaps
- **Breaks:** suppression anti-join is opt-in per query, silently inert for name-only/partial-DOB cases,
  over-applies to whole company alerts, and can be bypassed by a loader fallback that skips
  normalisation.
- **Prevalence:** 4 findings, max **S2**, explicit Art 17/21 GDPR exposure language.
- **Examples:** CA-W2-06 ("nothing structural... no SQL view, no RLS, no query-builder, **no
  test-harness contract**... a new report endpoint added tomorrow would have zero test coverage for
  suppression until a test is explicitly written for it"). CA-W2-11 (anti-join over-suppresses whole
  company alerts). CA-W2-12 (`NULL IS NOT DISTINCT FROM` makes name-only/partial-DOB suppressions
  silently inert). CA-W2-30 (`loader.py::_to_row()` fallback bypasses `normalise()`, defeats
  suppression).
- **Root cause:** entity-resolution-domain (borders security/privacy).
- **Preventability:** CA-W2-06 specifically is **highly preventable** — a test-quality rule requiring an
  enumerator test ("discover every query touching the protected table, assert the anti-join fragment is
  present") for any suppression-adjacent capability. CA-W2-11/12/30 need domain-semantic review, not a
  generic mechanism.

### SCALE-1: Unbounded query / unbounded fetch at growth scale
- **Breaks:** a query with no `LIMIT`/pagination/time-window materializes an entire (unboundedly
  growing) table client-side.
- **Prevalence:** 1 finding, framed **S6 today → S1 at scale**, directly adjacent to a prior real
  incident.
- **Examples:** CA-W2-05 — `matcher.py:521-523`, unbounded `SELECT ... FROM alerts`, a few lines from a
  comment describing the **F17 incident** ("an unbounded fetch here once materialized a 14.6M-row
  backlog... froze the host"); F17's fix paginated the *diff* fetch but left the *alerts* fetch
  unbounded. Exactly the pattern `lessons.md`'s B5 post-mortem told future agents to grep for.
- **Root cause:** data-scale-unbounded.
- **Preventability:** **Highest of any class here.** A deterministic `checks.py` detector (grep
  `fetchall()`/unbounded SELECT without LIMIT/keyset predicate in pipeline modules) is exactly what the
  "mind data scale" rule should already do — this finding shows it doesn't cover every query in a module
  it already flagged once. The B5 lesson was written down; not enforced; a sibling bug survived until a
  full audit re-found it by hand.

### RETRY-1: No standalone retry path for a partial/failed side-effecting operation
- **Breaks:** an operation with a real side effect can fail partway with no way to retry just that
  failure — only a full pipeline re-run, which doesn't cover the case.
- **Prevalence:** 3 findings, **S1**.
- **Examples:** CA-W2-02 (`watchlist.py:226-240` — entry INSERT commits *before* `backfill_for_entry()`
  runs; if backfill throws, entry stays permanently active with zero alerts, no retry). CA-W2-04 (no
  standalone re-dispatch path at any CLI flag/route/cron/script). CA-W2-03 (dispatch wraps all users in
  one transaction; a mid-batch error can roll back already-delivered rows, duplicate sends on retry).
- **Root cause:** concurrency-idempotency.
- **Preventability:** Partial — a propose-time acceptance-criteria question ("does this write have an
  independent retry path if it fails partway?") for any side-effecting write; needs whole-surface
  reading, not pattern-matching. Notably CA-W2-02 sits in the same file/function family as the **F16**
  transaction-visibility lesson — F16's fix (commit before the second-connection call) shifted risk onto
  exactly the failure-handling path CA-W2-02 later found unguarded.

### TXN-1: Test fixture doesn't mirror production transaction/connection semantics
- **Breaks:** test DB connection uses `autocommit=TRUE` while production doesn't — a real
  uncommitted-visibility bug is invisible in the suite.
- **Prevalence:** 1 named historical incident (F16) + 1 structurally-related later finding in the same
  code family (CA-W2-02).
- **Examples:** `lessons.md` F16: "passed in tests because the test fixture uses `autocommit=TRUE`
  (production does not)." CA-W2-02's own docstring: "the request connection is not autocommit in
  production — only the test fixture is."
- **Root cause:** test-quality-fixture-scale-only.
- **Preventability:** Plausible as a new check — flag any test fixture whose connection mode differs
  from production's factory. F16's rule ("check uncommitted-state visibility before a second connection
  call") is written as prose in `lessons.md`, not enforced — a direct instance of "mechanism over docs."

### TQ-WEAK: Weak/vague test assertions
- **Breaks:** assertions check a weaker property than what's knowable (`is not None`, `len(x) >= 1`,
  substring match) where the exact value is derivable from the test's own setup.
- **Prevalence:** 18 confirmed (test-quality audit), all 4 domains.
- **Examples:** W-B-1/2 (`idempotency_key is not None` — a wrong key would still pass; exact `uuid5(...)`
  is knowable). W-A-2/W-C-6/W-D-5 (`len(x) >= 1` where exactly 1 row is set up — a duplication
  regression would still pass). W-D-2 (`.get('fuzzy_match_enabled', False) is False` passes vacuously if
  the key is simply absent).
- **Root cause:** test-quality-weak-assertion.
- **Preventability:** **High** — a rule banning specific weak-assertion shapes (`is not None`/`>=` count
  checks when the exact value is derivable in-test) is mechanically lintable.

### TQ-FLAKY: Clock-dependent tests without a frozen clock
- **Breaks:** tests call `date.today()`/`datetime.now()` for both setup and the code path under test,
  unfrozen — a midnight boundary between calls changes the result.
- **Prevalence:** 5 confirmed, matcher/health-check surfaces.
- **Examples:** FL-A-1/2 (`test_matcher.py`, `date.today()` for diff-window setup *and* passed to
  `run_matching()`). FL-D-1 (`test_health_pipeline_endpoint`, `days_since == 1` can become 2 across
  midnight).
- **Root cause:** test-quality-weak-assertion (nondeterministic-test variant).
- **Preventability:** **High** — lint requiring `freezegun`/injected clock for any test calling a
  real-time function; mechanical to enforce.

### TQ-MISSING: Coverage gaps on already-identified risk paths (incl. 1 confirmed prod bug)
- **Breaks:** zero/partial coverage on exactly the exception/edge paths most likely to matter.
- **Prevalence:** 27 hard-MISSING + 13 partial-MISSING behaviors; 1 confirmed production bug; 2
  bug-or-policy items pending an operator ruling.
- **Examples:** **B-D-36** — `check_backup_freshness` catches `FileNotFoundError` but not
  `subprocess.TimeoutExpired`; a hung `restic` crashes the whole health-sentinel process, "monitoring
  goes dark precisely when an infrastructure problem is most likely," zero coverage of that path. B-B-22
  (no-email downgrades never get `free_grace_until` set — effectively infinite grace, untested). B-D-16
  (`/watchlist/nationalities` has no auth dependency unlike sibling routes, entirely untested).
- **Root cause:** test-quality-weak-assertion (coverage-gap variant); observability-gap for B-D-36.
- **Preventability:** **High, but ordering matters** — these gaps were only gradable because the audit
  first built four ratified behavior catalogs; before that, nothing specified what "fully tested" meant.
  A merge-time rule requiring a versioned acceptance/behavior catalog per capability, checked for full
  coverage, would have caught B-D-36/B-B-22 at the change that introduced them.

### OBS-1: Silent sentinel/watchdog failure
- **Breaks:** monitoring code that should fail loud instead fails quiet — an uncaught exception type
  crashes the monitor, or a misconfiguration silently degrades a safeguard to a permanent no-op.
- **Prevalence:** 2 correctness findings (max S5) + B-D-36 above (doubles as this class's clearest
  instance).
- **Examples:** CA-W1-18 (sentinel/watchdog fragility, "no automated backstop"). CA-W2-27 (if
  `sweep_free_grace.py`'s cron ever omits `--force`, the sweep runs in dry-run mode indefinitely with
  only a log line — "no alert, no metric, no operator-visible sentinel").
- **Root cause:** observability-gap.
- **Preventability:** High for the general shape — a rule requiring every monitoring function to test its
  own failure-to-alert path (not just the happy path) would have caught B-D-36 directly. CA-W2-27's
  "silent misconfig degrades a guard" needs a deploy-config linter, not a code check.

### CONC-1: Check-then-act concurrency races (TOCTOU)
- **Breaks:** a limit/uniqueness check runs, then an independent write happens, nothing at the DB level
  enforces the invariant between them.
- **Prevalence:** 3 findings; 1 confirmed (S5), 2 refuted-on-inspection but the *shape* recurs.
- **Examples:** CA-W2-08 (watchlist free-tier limit is TOCTOU, no DB constraint — confirmed). CA-W2-13
  (`suppress_psc.py add` — REFUTED, a partial unique index already exists; residual: uncaught
  `UniqueViolation`). CA-W2-29 (concurrent grace sweeps — verified safe by repro).
- **Root cause:** concurrency-idempotency.
- **Preventability:** Moderate — a grep-based "SELECT-existence-check immediately followed by INSERT
  with no matching unique constraint" detector is plausible but noisy; more realistic as a design-review
  checklist item for entitlement/limit logic.

### QRY-1: Filter/limit ordering bugs
- **Breaks:** a filter applied in the wrong place relative to a `LIMIT`, or a compound value parsed as
  one atomic token — both produce false negatives on the customer-facing search/report surface.
- **Prevalence:** 3 findings, max **S1**.
- **Examples:** CA-W2-19 (`reports.py` — nationality filter applied in Python *after* the SQL `LIMIT`,
  false-negative 404 beyond the CAP). CA-W2-20 (`_nationality_matches` treats `"British,French"` as one
  fragment). CA-W2-07 (CAP=500 mechanism correct, but the threshold value was never validated against
  real bucket sizes — a live query found buckets that exceed it).
- **Root cause:** data-correctness-logic.
- **Preventability:** Domain-specific/code-review-catchable ("filter after LIMIT" is flaggable by a
  reviewer, noisy for a generic static detector). Lower leverage than the classes above.

### DEP-1: Third-party format/markup brittleness (Companies House dependency)
- **Breaks:** parsing assumes a specific external format shape (HTML markup, zip entry order, CSV
  NULL-vs-empty semantics) with no defensive handling if the third party changes it.
- **Prevalence:** 3 findings, all **S6/S7** (forward-looking, not currently triggering).
- **Examples:** CA-W1-13 (HTML-scraping URL discovery, brittle regex). CA-W1-17 (zip inner-entry = first
  `namelist()` entry, no extension filter). CA-W1-23 (`None`→`""` COPY semantics, triple-defended today).
- **Root cause:** dependency-external-api.
- **Preventability:** **No general scaffold mechanism would realistically catch this** — requires
  product-specific knowledge of the third party's format. The corpus's own fix (Wave E2: use CH's
  previously-discarded "totals record" as a content witness) is a domain insight, not a generic check.

### DOC-1: Reference-doc / implementation drift
- **Breaks:** a tracked reference doc's field names/behavior no longer match the live implementation,
  and nothing (test, lint, CI) failed when they diverged.
- **Prevalence:** 3 instances across both corpora.
- **Examples:** test-quality "Conflict C#1" — `historical-reports.md` documents
  `nationality_observed`/`country_of_residence_observed`; the live API emits
  `distinct_nationalities`/`distinct_countries`, zero test asserts either name. CA-W1-20's archived
  dossier cited a non-existent file, `api/routes/psc_suppression.py`. CA-W2-18 corrected an
  `entity-resolution.md` claim about `SIGNAL_LABELS`.
- **Root cause:** spec-or-acceptance-drift.
- **Preventability:** Plausible — exactly the shape this scaffold's own `knowledge-drift-review` skill
  targets, but that mechanism is scoped to the OpenSpec knowledge tree, not arbitrary product reference
  docs. Extending its scope (or a "doc field names must appear in the code they document" grep) is a
  concrete, moderate-effort candidate.

### SEC-BLIND: Security is structurally out of scope of both corpora
- **Breaks:** nothing directly — a scope note, not a finding. Neither corpus can answer "did the
  security-review gate work" because security was explicitly excluded (brief §8: "a separate audit,
  entirely out of scope").
- **Examples:** the one security catch anywhere in this corpus was on the audit's *own* probe script — an
  f-string `SELECT` in `_audit_scratch_db_oneoff.py` "could reach the LIVE DB" via SQL identifier
  injection, caught by that wave's own verify-phase security review (fixed same-wave). It has never run
  against `pipeline/`/`api/`/`core/` product code under this program.
- **Root cause:** security.
- **Preventability:** Not this program's finding to make — flag that a clean correctness bill of health
  says nothing about security posture; a dedicated security-audit wave is an acknowledged, separate gap.

## Cross-cutting observations

1. **Lessons get written as prose, not turned into checks, and the same bug recurs.** Two dated
   incidents each produced a hand-written rule in `lessons.md` (B5 → grep unbounded fetchall; F16 →
   check uncommitted-state visibility) — and a sibling instance of the same bug (CA-W2-05, CA-W2-02)
   survived past each incident until this audit re-found it by hand. The rule existed; enforcement on
   every future diff did not. Strongest candidate: turn named incident root causes into permanent
   `checks.py` detectors, not just journal entries.

2. **Verify gates review diffs, not accreted subsystems.** The audit exists because parser/loader,
   entity-resolution, and email content "never had a dedicated pass" — an admission that nothing
   periodically re-examines a capability's whole surface as it accretes across many individually-passing
   changes.

3. **Local gates have known, named reach gaps CI doesn't fully backstop** (no ruff in CI; local hooks are
   Claude-Code-only, bypassed by DeepSeek/human commits) — a standing, already-documented weak spot.

4. **TQ-WEAK and TQ-FLAKY are the most mechanically preventable classes in the whole corpus** — both are
   pattern-matchable (assertion shape / unfrozen clock calls), yet 23 instances accumulated before a
   dedicated audit caught them. Cheapest, highest-confidence "add this check now" recommendation.

5. **TQ-MISSING could only be graded because the audit first invented ratified behavior catalogs** — no
   artifact previously stated what "fully tested" meant for these modules. Implication: acceptance
   criteria/behavior catalogs need to exist *before* code ships, or coverage-gap bugs like B-D-36 ship
   invisibly and get caught only by a later audit.

6. **`lessons.md` explicitly changes future process on:** (a) LEAD-graduation — use deepseek-v4-pro for
   adversarial refutation, not Sonnet, per an operator ruling after an earlier plan wasn't adversarial
   enough; (b) a standing review rule for uncommitted-state visibility (F16); (c) "audit each pipeline
   step's input domain, not just the step you're measuring... the step nobody is looking at is the one
   that kills you" (B5) — a direct generalization of SCALE-1 and arguably the single most transferable
   principle in the corpus.
