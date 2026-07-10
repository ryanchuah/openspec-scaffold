# extrends — distilled defect classes (for scaffold gap analysis)

Source: `extrends/knowledge/research/correctness-audit-2026-07/{CHARTER,FINDINGS-wave1..4}.md`,
`extrends/knowledge/research/test-audit/{CHARTER,FINDINGS}.md` + `oracle/*.md`,
`extrends/knowledge/lessons.md`, `extrends/knowledge/audit-log.md`, plus the four archived
`audit-correctness-*` change dirs (proposal/design skim only — these are the **dossier-producing
audit changes themselves**, one per wave, NOT remediation: per CHARTER.md's audit-then-fix
discipline and `decisions/INDEX.md § audit-first-remediation-deferred`, zero remediation has shipped
for any wave as of this writing). No findings invented; IDs quoted verbatim from the corpus. Product
name in-repo: TrendScope.

## Meta

**Why this audit existed / did in-loop gates fail?** The CHARTER frames the whole program in the
posture of "a departing principal engineer" doing a one-time sweep because **no runtime-correctness
audit had ever executed on this repo** (wave-1 proposal: "No runtime-correctness audit has ever
executed on this repo (known-findings ledger)"). That is itself the headline gap-signal: ordinary
per-change verify (self-review + delegated apply) had run on every one of the ~45 archived feature
changes, yet nothing had ever re-swept an accreted subsystem end-to-end. Concrete named misses by
the normal in-loop gates, quoted verbatim: "no existing repo test exercises this path" (ING-1, a
truncation-cap bug); "the entire shell wrapper... has zero automated test coverage of any kind —
every behavioral claim... rests on reading the script, not on any asserting test" (W3-DISC-11, the
cron/ops wrapper); "Green does not guarantee the actual HTTP retry/backoff contract... the function
is always replaced at the mock boundary, never exercised through it" (TQ-2); "a bare
`--cov-fail-under=N` gate would treat kleinberg.py's figure as clean, healthy coverage, exactly
backwards from reality" (TOOL-1). The one place a normal gate *did* work is instructive by contrast:
`lessons.md`'s `harden-pytrends-validation` incident — 722 mock-patched tests passed green on a
`TypeError`-inducing bad assumption, and the reviewer wrongly "confirmed" the assumption as "available
in pytrends 4.9.2" (a hallucinated affirmation of unverifiable-by-the-reviewer external-API behavior)
— but the mandatory **live-smoke step of verify** caught it before ship. That is the scaffold
mechanism this repo already has that *did* prevent a class of defect the audit would otherwise have
had to find; it is the exception, not the rule, in this corpus.

**Remediation status:** per `knowledge/decisions/INDEX.md § audit-first-remediation-deferred`, **ALL
remediation for every wave is deferred until after the auditor's departure** — as of this writing
(2026-07-10, the date Wave 4 itself was archived) zero findings from any of the four waves have been
fixed. This differs from the sibling psc-monitor program, where some remediation waves had already
shipped. Every defect class below is therefore still live in the codebase.

**Scale:** the dossier's own **never-record-counts rule** (CHARTER.md, "no test tallies, no row
counts, no pass/fail counts of any kind appear anywhere in this file") means the source documents
deliberately do not self-report tallies — the approximate counts below are this analysis's own
reconstruction from listed finding IDs, not sourced numbers. Rough shape: Wave 1 ~7 classes/~29
findings (data-in, max severity `silent-data-drift`); Wave 2 ~5 classes/~19 findings (scoring math +
DB integrity, several `silent-data-drift`/`ranking-error`); Wave 3 ~8 classes/~22 findings
(measurement/determinism/ops/reliability, the wave that surfaced the ground-truth-label-destruction
and spend-control classes); Wave 4 ~8 classes/~35+ findings (tests/tooling/LLM-integration — the
richest source of explicit gate-failure language, since it audits the verification floor itself).
Test-audit: ~7 classes/~110+ individual findings across taxonomy A-G, including 3 cases where a weak
test concealed a real, still-shipping product bug (TA-2).

**Oracle timing:** see the dedicated paragraph after the TA-8 test-audit classes below — short
answer: hybrid. Where an OpenSpec spec predates the code, the oracle is a faithful re-read of
pre-existing acceptance criteria; where a capability's spec is THIN/NONE (all three social-media
collectors: HackerNews, Arctic Shift, Bluesky), no acceptance criteria independent of the
implementer's own code comments ever existed before this one-time reconstruction.

## Defect classes

### ING-1: Truncation caps report `complete=True` while dropping in-window data
- **What breaks:** Per-collector safety caps (page limits, item caps, floor-based early stops, recency-stop heuristics) fire and silently stop short of full coverage, but return `complete=True`, so the watermark advances as if the window were fully covered — the gap is never revisited.
- **Prevalence/severity:** 7 findings, max **silent-data-drift**, wave 1.
- **Representative examples:** W1-I1a (`arctic_shift.py:368-411` — `_MAX_PAGES` for-else fires, `complete=True`), W1-I1c (`bluesky.py:379-485` — `max_pages` cap, zero existing tests exercise this path), W1-I3a (`bluesky.py:459-467` — non-chronological stop rule quits on first stale page).
- **Root-cause category:** data-correctness-logic
- **Scaffold-preventability hypothesis:** A test-quality rule requiring a behavioral "cap-fires → `complete=False`" oracle test for every collector's stop/cap path. Hackernews already has exactly this test (`test_collect_recent_unsplittable_overflow_returns_complete_false`), cited in the file as "the pattern every collector above should follow" — its absence elsewhere (confirmed zero-hit grep for bluesky) is what let this ship. Formalizing the `(inserted, complete)` contract as a mandatory acceptance criterion before any collector cap merges would have caught this class directly.

### ING-2: No per-item/per-window fault isolation — one bad record aborts the rest of a run
- **What breaks:** A single malformed record or a single day's transient API failure raises uncaught, aborting all remaining items/days in that collector's run for the window, often paired with a misleading "0 inserted" metric even though partial work was already flushed.
- **Prevalence/severity:** 3 findings, max **silent-data-drift**, wave 1.
- **Representative examples:** W1-I2b (`arctic_shift.py:379-382,403,499-503` — trailing-null `created_utc` crashes posts-phase, `_ingest_comments` never attempted), W1-I4 (`hackernews.py:328,363-418` — one unguarded `objectID` subscript, zero per-item isolation), W1-DISC-3 (`wikipedia.py:236-242,263-269` — no per-day try/except, one day's HTTP 500 aborts all remaining days).
- **Root-cause category:** data-correctness-logic
- **Scaffold-preventability hypothesis:** A test-quality rule requiring a fault-injection oracle (one malformed/failing record or day planted mid-stream) for every collector's iteration boundary. The actual suite never did this: `test_wikipedia.py::test_500_response_raises_http_status_error` covers only the single-day case, not the multi-day partial-success case this sweep found.

### ING-3: Missing critical fields (identity, timestamp) silently defaulted instead of rejected
- **What breaks:** A missing/unparseable `id`, `uri`, or `createdAt` field is defaulted to an empty-string sentinel or `datetime.now()` rather than rejected, causing two distinct records to silently collide under one shared identity key, or a document to be time-shifted into the wrong aggregation period.
- **Prevalence/severity:** 4 findings, max **silent-data-drift**, wave 1.
- **Representative examples:** W1-I3b (`bluesky.py:440` — missing `uri`→`""`, second distinct post silently dropped as duplicate), W1-DISC-2 (`polymarket.py:223` — missing `id`→`""`, same collision mechanism), W1-DISC-1 (`polymarket.py:229-237` — missing/unparseable `createdAt`→collection-instant `now()`, time-anchor misattribution).
- **Root-cause category:** data-correctness-logic
- **Scaffold-preventability hypothesis:** A new deterministic checks.py detector — a static scan across collectors for `.get(<field>, "")`-style sentinel-default patterns feeding an identity key or a `created_utc` construction, flagging any without an explicit reject-and-skip guard. This is exactly the pattern the audit's own Appendix A drafts as a required contract after the fact — i.e. it was mechanically discoverable, just never encoded as a permanent check.

### ING-4: Idempotency/retry/contract hygiene gaps (mostly latent, non-data-loss)
- **What breaks:** Upsert semantics, retry-sleep bounds, and the watermark invariant are enforced only by ad hoc code paths or convention rather than a documented, tested contract — mostly latent/ops-fragility, but one item (no UPDATE path) is a live silent-data-drift.
- **Prevalence/severity:** 5 findings, max **silent-data-drift** (mostly ops-fragility/dev-quality), wave 1.
- **Representative examples:** W1-I5a (`base.py:46-66` — `upsert_document` is insert-only, an edited upstream post never reflected), W1-I5c (`arctic_shift.py:256-275` et al. — unclamped `Retry-After` sleep can stall the whole sequential run), W1-W1 (`watermark.py:87-95` — monotonicity invariant enforced by one function's code only, never written as a testable spec).
- **Root-cause category:** concurrency-idempotency
- **Scaffold-preventability hypothesis:** A new deterministic checks.py detector for two mechanical patterns (unclamped `time.sleep()` on an externally-controlled duration; a loop variable referenced after a possibly-zero-iteration `range()`) would catch the retry/NameError items mechanically. The insert-vs-update semantics question is a genuine product decision no scaffold mechanism can force — closest lever is an acceptance-criteria requirement that upsert update-semantics be explicitly decided before merge.

### AGG-1: Dual-path (legacy vs fact-store) desync + destructive re-derive silently drops history
- **What breaks:** The legacy `aggregate()` path and the flag-gated fact-store path disagree on what "sealed" means and on window/scope boundaries; a routine full re-derive, a prune, or a delayed-recovery collect can silently zero out or orphan history that already looked correctly sealed.
- **Prevalence/severity:** 5 findings, max **silent-data-drift**, wave 1.
- **Representative examples:** W1-A1 (`factstore.py:273-293,128-155` — sealed-day check inspects only `period_meta`, never `document_terms`; a future full re-derive would zero ALL legacy-sealed history, confirmed live on the real snapshot), W1-A2 (`pipeline.py:255-258,284-289` — `agg_start` always computed from "today," never widened for a recovered collector's reach), W1-A3 (`factstore.py:128-155`, `models.py:67,72-74` — non-atomic DELETE-then-INSERT plus FK CASCADE permanently drops a pruned document's counts).
- **Root-cause category:** data-correctness-logic
- **Scaffold-preventability hypothesis:** A stronger verify-gate requiring a mandatory eval-delta/parity check before any config flag that changes a derivation path is flipped on — e.g. before enabling `aggregation_factstore_enabled`, run a full derive against a snapshot copy and diff row counts against the legacy path. This entire class is a flag-gated feature that was never exercised at real scale before shipping the flag.

### TIME-1: Time computation defects — host-local anchors and convention-only UTC enforcement
- **What breaks:** Scoring-window dates are computed from host-local wall-clock calls instead of UTC, and datetime comparisons rely on every writer normalizing to UTC by convention rather than by schema — either can silently shift which ISO week gets scored/published or corrupt comparisons the moment a future writer doesn't follow the convention.
- **Prevalence/severity:** 3 findings, max **silent-data-drift** (manifests as ranking-error), wave 1.
- **Representative examples:** W1-T1 (`pipeline.py:129,284` — bare `date.today()` on a UTC+8 host lands a full calendar day ahead across the Sun→Mon boundary, live-demonstrated to shift `recent_period` to the wrong ISO week), W1-T2 (`aggregate.py:85,89-90`, `factstore.py:252,270-271` — naive `datetime.combine` compared against `created_utc`; SQLite strips tzinfo on write so `DateTime(timezone=True)` is enforced only by convention).
- **Root-cause category:** data-correctness-logic
- **Scaffold-preventability hypothesis:** A new deterministic checks.py detector — the audit's own AST-level scan for bare `date.today()`/naive `datetime.now()` calls (literally how W1-T1 was found) could run permanently as a lint rule banning non-UTC-explicit time anchors in the scoring path; the schema-vs-convention gap needs an acceptance-criteria requirement that a `timezone=True` column be backed by a runtime assertion, not just a docstring.

### EXT-1: Term-extraction fragmentation drops/splits terms feeding all downstream scoring
- **What breaks:** Real trending terms (short acronyms, digit-letter compounds, hyphenated brand names, hashtag-adjacent nouns) get silently dropped entirely or fragmented into multiple non-matching canonical buckets before scoring ever sees them — a systematic, silent, total loss for the affected term.
- **Prevalence/severity:** 2 findings, max **silent-data-drift**, wave 1.
- **Representative examples:** W1-X1 (`extract.py:157-159,145,99-133` — `<3`-char drop kills "AI"/"Go" entirely, "5G" splits into "5 g", "GPT-4" vs "GPT4" become two different canonical terms), W1-DISC-7 (`extract.py` — VR/AR/EV/ML/OS/EU/UN all normalize to `None` standalone, survival purely an accident of spaCy chunk boundaries).
- **Root-cause category:** entity-resolution-domain
- **Scaffold-preventability hypothesis:** Domain-specific — no general scaffold mechanism would realistically catch this; it requires NLP-domain judgment (an acronym allowlist, a tokenizer merge rule, an alias table) that only surfaces via an eval-gate requirement diffing extracted terms against a hand-curated set of known real-world entities/acronyms before ship. No deterministic code-shape detector would flag "AI" silently vanishing.

**Wave 1 process-gap quotes (verbatim):**
- W1-I1c: "No existing repo test exercises this path (grepped `tests/test_bluesky.py` for `max_pages`/`bluesky_max_pages_per_feed` — zero hits); this is a previously-untested truncation path."
- W1-DISC-3: existing test "already demonstrates the single-day case ... but does not test the multi-day partial-success case this sweep confirmed."
- W1-DISC-6: the repo's own idempotency test "only exercises the same-content/same-logic re-run case, never an extraction-logic-changed one."
- W1-DISC-6: the migration-classification helpers that would drive a safe fix have "ZERO production callers anywhere in `src/trendscope/`... no wired script currently drives a safe migration."
- W1-A1: "the default-off gate is the only thing currently preventing this precondition from being exercised."

### MATH-1: Canonical-math divergence (Kleinberg + population-std)
- **What breaks:** Shipped scoring math silently diverges from the canonical/textbook formula it's modeled on — Kleinberg burst detection swaps parameter roles, drops term-dependent cost scaling, and gives free bursts at t=0 (all feeding the S3 notability signal); separately, baseline z-scores use population variance (÷n) instead of sample variance (÷n−1) across every z-score-consuming module.
- **Prevalence/severity:** 2 findings, max **silent-data-drift**, wave 2.
- **Representative examples:** W2-C1 (`kleinberg.py` `compute_burst_weight`, wired via `notability.py:608`→`scoring.py:994,1021` — s/gamma role swap + missing `gamma*ln(n)` scaling + free t=0 init, diverging from Kleinberg 2003), W2-C4 (`scoring.py:647`, `scorers/lane_lrc.py:126-129` — `compute_stats`/`LRCScorer.score` use ÷n population variance where ÷(n−1) sample variance is the textbook baseline-window convention).
- **Root-cause category:** scoring-eval-logic
- **Scaffold-preventability hypothesis:** A stronger verify-gate requiring a golden-battery/reference-equation cross-check whenever code claims to implement a cited published algorithm — this is literally how W2-C1 was found (the audit had to hand-derive Kleinberg's actual equations because no existing test compared against them, only internal self-consistency checks). C4's ÷n-vs-÷(n−1) choice is a genuine statistical-convention judgment call — closer to domain-specific; a spec requirement to document the intended convention per formula would at least surface the ambiguity.

### SCORE-EDGE-1: Zero/empty-input edge cases silently inject a false extreme signal
- **What breaks:** At a zero/empty boundary (zero-document week, empty embedding generator, zero total blend weight), the code doesn't fail or correctly return null — it silently produces a plausible-looking WRONG value (phantom document count, max-similarity score, full-strength reintroduced signal) that flows into the notability blend with no error signal.
- **Prevalence/severity:** 3 findings, max **silent-data-drift**, wave 2.
- **Representative examples:** W2-C2 (`scoring.py`/`notability.py` corpus-totals round-trip — genuine zero-doc week floored to integer count 1 via `max(1, round(...))`, biasing every term's S3 rate that week), W2-C3 (`scoring.py:949-956` — empty fastembed generator yields a zero vector that scores S2=1.0 and gets persisted instead of hitting the exception path), W2-DISC-1 (notability blend — zeroing both weights with S2/S3 undefined makes `total_defined_weight==0` fall through to S1 at full raw strength instead of 0).
- **Root-cause category:** data-correctness-logic
- **Scaffold-preventability hypothesis:** A test-quality rule requiring an explicit boundary-value test (zero count, empty generator, zero weight-total) for every scoring component — none of these three existed as a dedicated test; all three were only found because this audit's probes deliberately constructed the zero/empty case. A mandatory "boundary-input eval-delta" gate on any new scoring formula would catch this class.

### DRIFT-1: Parallel/duplicated implementations silently diverge from what their comment or twin claims
- **What breaks:** Two code paths meant to behave the same (a documented duplicate, a stated parity claim, or a shared config flag) quietly stop matching — one enforces validation/behavior, its twin silently doesn't, and in two cases persisted metadata or a comment then asserts a falsehood about what happened.
- **Prevalence/severity:** 4 findings, max **ranking-error**, wave 2.
- **Representative examples:** W2-DISC-2 (`_rollup_rows_by_lane` vs pooled `_rollup_rows` — lane path silently drops `breadth_unit="thread"` with no NULL guard while the pooled path raises `ValueError` on the same row, yet `Run.params_json` is stamped as if thread-mode applied), W2-DISC-3 (`market_scorer._resolve_run_granularity` vs `digest._run_granularity` — docstring claims duplication but the market path silently substitutes defaults where digest.py raises), W2-D2 (`enrich.py:660-663` comment claims FKs are "unenforced in prod" — false since `db.py:43-46` turned the pragma ON).
- **Root-cause category:** spec-or-acceptance-drift
- **Scaffold-preventability hypothesis:** A deterministic checks.py detector for near-duplicate functions (AST-similarity scan, already precedented by W2-D2's own programmatic FK-pair walk over `Base.metadata`) that flags pairs like these and forces either unification or a tested, explicit divergence contract. For cases with a literal parity claim in prose (docstring/comment), a lint rule that greps "duplicates X"/"same as Y" claims and requires a linked behavioral-parity test would catch the drift directly.

### ENTITY-1: Entity-resolution integrity — inconsistent normalization + non-atomic persistence
- **What breaks:** The entity-identity pipeline uses two mutually-inconsistent normalization functions so accent variants never merge; resolves canonical entities via SELECT-then-INSERT with no concurrency guard; carries a streak silently through enrichment outages; and destructively deletes-then-reinserts all entity rows for a run with the delete OUTSIDE the savepoint its own docstring claims protects it — so a mid-persist failure permanently loses entity data with no rollback.
- **Prevalence/severity:** 2 findings, max **ranking-error**, wave 2.
- **Representative examples:** W2-D4 (`enrich.py:374` `str.lower()` vs `notability.py:60-67` `_ascii_lower()` — 'Café'/'Cafe' never merge under either; `enrich.py:618-634` SELECT-then-INSERT race against `models.py:324`'s UNIQUE(canonical); `enrich.py:668-669` unconditional delete-before-reinsert, no idempotency key), W2-DISC-6 (`enrich.py:664-719` delete+insert sits outside the savepoint at line 728 despite the docstring at lines 647-649 claiming protection — forced-failure repro confirmed Entity rows lost, `params_json` partially written).
- **Root-cause category:** entity-resolution-domain
- **Scaffold-preventability hypothesis:** A stronger verify-gate mandating fault-injection tests (force a failure mid-transaction) for any function whose docstring claims transactional/savepoint protection — exactly the technique that surfaced W2-DISC-6. The normalization split and outage-streak behavior are more domain-specific — closer to an acceptance-criteria gap than something a generic scaffold check would catch.

### DB-1: Missing/asymmetric schema constraints and accident-of-deployment config defaults
- **What breaks:** Several tables lack a constraint (UNIQUE, consistent ON DELETE) that would prevent an inconsistent/duplicate state — one case is proven live-reachable (unconditional duplicate INSERT); separately, a Boolean column's string-literal server default only works because SQLite coerces it by type affinity, and a gate-detection check computed run-wide instead of per-term would silently drop un-gated terms the moment a run mixes gated/un-gated terms.
- **Prevalence/severity:** 6 findings, max **silent-data-drift** (W2-D1; the rest are dev-quality), wave 2.
- **Representative examples:** W2-D1 (`models.py:~390-393` — no UNIQUE(term, week_start) on `embedding_vectors`, no SELECT-before-INSERT in `notability.py:~421-428` — repro proved a second `compute_s2()` call unconditionally inserts a duplicate row), W2-DISC-5 (`models.py:329-337` — `CanonicalEntity.first_flagged_run_id` blocks Run deletion while `last_seen_run_id` silently NULLs, same table, inconsistent ondelete), W2-DISC-8 (`models.py:121` — `Run.rolling` Boolean with `server_default="0"` as a string literal, SQLite-only-safe), W2-DISC-9 (`enrich.py:328-337` — `gate_enabled = any(...)` computed once per run instead of per term).
- **Root-cause category:** data-correctness-logic
- **Scaffold-preventability hypothesis:** A deterministic checks.py detector extending the same programmatic `Base.metadata` walk W2-D2 already used for the FK-pair orphan scan — flag tables whose natural key lacks a UNIQUE constraint when the ORM does read-then-write instead of upsert, tables with inconsistent sibling ondelete clauses, and SQLAlchemy column-default type mismatches (string literal on a Boolean column). The per-term-vs-run-wide gate detection is closer to an acceptance-criteria gap — a spec requirement plus a test that mixes gated/un-gated terms in one run would catch the silent collapse; nothing currently exercises that mix.

**Wave 2 process-gap quotes (verbatim):**
- W2-D1: "no UNIQUE constraint on `(term, week_start)` in `embedding_vectors`... no SELECT-before-INSERT or upsert in `notability.py`... retention pruning prunes by age only and never deduplicates."
- W2-D2: "default test `mem_engine` (`conftest.py:106-107`) runs with `PRAGMA foreign_keys=OFF` (SQLite default), while prod `db.py:43-46` sets `PRAGMA foreign_keys=ON`" — the test harness never exercises the FK-enforced path prod actually runs.
- W2-DISC-2: "No config validation prevents the combination" (scorer="lane-lrc" with an incompatible breadth_unit).
- W2-DISC-6: "The docstring (lines 647-649) claims the savepoint protects Entity/EntityTerm survival — but they're already deleted BEFORE it" — the code's own claimed protection was never actually verified until this audit's forced-failure repro.

### MEAS-1: Ground-truth label pipeline — silent overwrite, loss, and clobbering (recurs wave 3 → wave 4)
- **What breaks:** Writes to the eval label store or eval report output can silently destroy prior human-labeled ground truth or a prior run's evaluation output, with no error or warning surfaced anywhere. The identical catch-log-continue-with-empty-collection shape recurred in a sibling module a whole wave later.
- **Prevalence/severity:** 4 findings across 2 waves, max **silent-data-drift**, waves 3+4.
- **Representative examples:** W3-E3 (`labels_io.py:139-145` — corrupt-YAML load failure falls through to empty `existing_labels`, then overwrites with a single-entry file, destroying every prior entry; unlocked read-modify-write also lets a concurrent writer's entry vanish silently), W3-DISC-1 (`cli.py:241-268` — `eval --all` writes every run's evaluation for a week to the same `output/eval-{iso_week}.md`, only the highest run_id's markdown survives), W4-M2a (`console/labels_io.py:143,228` — same catch-log-continue-with-empty-collection shape, a different module, destroys prior entries in `eval/labels/*.yaml`/`eval/known-events/*.yaml`; "nothing in the UI distinguishes a normal save from a 'just destroyed N existing labels' save").
- **Root-cause category:** data-correctness-logic
- **Scaffold-preventability hypothesis:** A stronger verify-gate behavior — mandatory adversarial exercise of any read-modify-write path (corrupt input + concurrent writer, exactly W3-E3's own repro) — would catch both `labels_io.py` mechanisms directly; a test-quality rule requiring a behavioral oracle for any load-modify-atomic-replace store function ("save must never lose prior entries even if the pre-existing file is malformed") generalizes across both sites instead of being rediscovered per-module.

### MEAS-2: Eval-metric definition ambiguity and harness-internal nondeterminism
- **What breaks:** The `precision_at_k` denominator disagrees across spec/docstring/code, and a dead-but-present `date.today()` fallback would make lead-time computation silently non-reproducible across calendar days if the `recent_period` field were ever missing.
- **Prevalence/severity:** 2 findings, max **measurement-error**, wave 3.
- **Representative examples:** W3-E1 (`evaluate.py:250` vs `:230-231` — code uses a labeled-row-count denominator per spec, docstring describes an unimplemented `min(k,track_size)` denominator; compounded by a sparse-labeling inflation hazard), W3-DISC-2 (`evaluate.py:671-674` — `lead_time_metrics` falls back to `datetime.date.today()` when `run.recent_period is None`; dead path on current data).
- **Root-cause category:** scoring-eval-logic
- **Scaffold-preventability hypothesis:** An acceptance-criteria/spec requirement that a metric's docstring, implementation, and governing spec be checked for agreement (a fixture test asserting the docstring's own stated formula against actual code output) would have caught W3-E1's three-way conflict; W3-DISC-2 is a generic "falls back to wall-clock when unanchored" pattern a checks.py detector could flag.

### MEAS-3: Digest/report surface unsafely diverges from persisted board truth
- **What breaks:** The operator-facing digest can show a Rank number that doesn't match the persisted `TrendScore.rank`, and can publish an ungated run's terms with no marker distinguishing them from a normal gated publish, exactly when the pipeline's own documented recovery instruction is followed.
- **Prevalence/severity:** 3 findings, max **ranking-error**, wave 3.
- **Representative examples:** W3-G1 (`digest.py:~992/~1028` — rendered `Rank` column is a per-section enumerate position, not the persisted `TrendScore.rank` the CSV/console use for the same term), W3-R3 (`pipeline.py:359,379-382,565-573`; `relevance.py:462-481` — a half-completed run with no `gate_keep` verdict survives rollback, and `regenerate_latest_digest`'s `ORDER BY run_at DESC LIMIT 1` with no gate-status filter publishes its ungated terms as if gated), W3-DISC-10 (the documented gate-failure recovery path is itself the mechanism that produces this ungated publish, with no alternate "re-run gate alone" subcommand).
- **Root-cause category:** data-correctness-logic
- **Scaffold-preventability hypothesis:** A mandatory real-output-eyeballing verify-gate step (rendering the actual digest for a forced-failure/half-completed run and reading it, not just checking exit codes) would surface both the Rank-column mismatch and the ungated-publish-with-no-marker defect — both are only visible by comparing the produced artifact to its source-of-truth board.

### DET-1: Nondeterministic persisted rank from unordered iteration and un-tiebroken sorts
- **What breaks:** Two runs over bit-identical data can persist different rank orders because a Python set/dict iteration order (hash-seed-dependent) or unordered SQL row-delivery feeds a sort key with no deterministic tertiary tiebreaker, across at least four sort sites.
- **Prevalence/severity:** 4 findings, max **ranking-error**, wave 3.
- **Representative examples:** W3-N1 (`lane_lrc.py:190-192,277-278` — set-iteration order flips lane-path rank between `PYTHONHASHSEED=0`/`=1` on a constructed genuine tie; pooled-path rank changes with physical DB row-delivery order alone), W3-DISC-5 (`scoring.py:1048,1054-1061` — rerank-mode sort has no tertiary tiebreaker beyond `(-notability,-score)`), W3-N2 (`notability.py:164-174,193-201` — S2 title-context queries sort by `Document.created_utc DESC` with no secondary key, tied timestamps feed embeddings in SQLite-undefined order).
- **Root-cause category:** data-correctness-logic
- **Scaffold-preventability hypothesis:** A deterministic checks.py detector scanning for `sorted(..., key=...)` over a set/dict, or any SQL `ORDER BY` whose key tuple doesn't end in a stable unique column, would catch every site mechanically — the audit itself notes "the fix pattern is identical and mechanical at each site," exactly what a static detector automates.

### DET-2: Unpinned model/library resolution silently drifts persisted signals with no version stamp
- **What breaks:** `fastembed` is unpinned and its own registry can silently repoint a model name to a different actual embedding source with no code change here; persisted `EmbeddingVector` rows carry no model/version stamp, and a CLI producing them is documented read-only but in fact writes new off-grid vectors and prunes on an anchor-arbitrary schedule.
- **Prevalence/severity:** 2 findings, max **silent-data-drift**, wave 3.
- **Representative examples:** W3-N2 (`notability.py:227-230` — model name resolves via fastembed's registry to `qdrant/all-MiniLM-L6-v2-onnx`, confirmed live, zero persisted stamp of which repo/version produced a vector; compatibility check is dimension-only, can't detect a same-dimension embedding-space shift), W3-N3 (`cli.py:111-117,151,190` — `trendscope score` documented "re-scores only" but commits new Run/TrendScore rows and writes off-grid EmbeddingVector rows).
- **Root-cause category:** dependency-external-api
- **Scaffold-preventability hypothesis:** A data-scale/dependency audit rule requiring pinned exact versions (or a committed lockfile) for any package whose resolved artifact feeds a persisted score would catch the registry-drift risk; a stronger verify-gate requirement diffing a function's actual DB write surface against its docstring's claimed behavior would catch W3-N3's undocumented writes mechanically.

### OPS-1: No mutual-exclusion or tuned concurrency control around shared SQLite/cron write paths
- **What breaks:** Nothing prevents two concurrent pipeline invocations from racing; commits can fail outright under concurrent reads because `busy_timeout=5000ms` is CPython's accidental stdlib default (never deliberately set) with no WAL; the one named recovery point for a failed migration is a raw `cp -f` while the correct online-backup pattern already exists a few lines below in the same script.
- **Prevalence/severity:** 3 findings, max **ops-fragility**, wave 3.
- **Representative examples:** W3-O1 (repo-wide grep — zero hits for `flock`/`pidfile`/`lockfile`), W3-O5 (`db.py:36-47` — no explicit timeout/WAL/busy_timeout set; reproduced a genuine `database is locked` error between a live reader and a committing writer), W3-O2 (`run_trendscope.sh:52-78,144-167` — pre-migration copy is a plain `cp -f` with no quick_check/online-backup API, unlike the correct `.backup()` pattern used a few lines later, which itself also lacks a post-backup quick_check; restore never drilled).
- **Root-cause category:** concurrency-idempotency
- **Scaffold-preventability hypothesis:** A stronger verify-gate behavior — mandatory concurrent-execution exercise of any shared-state write path (two simulated concurrent invocations, exactly W3-O5's own repro) — would surface the lock/timeout gap directly; the migration-vs-weekly-backup asymmetry is a review-layer checklist catch since the correct pattern already exists in the same file.

### OPS-2: Degradation/failure signals silently invisible to the operator despite real spend or risk (recurs 3x across waves 3-4)
- **What breaks:** A fail-soft/fail-open branch (WSV, enrich, `write_digest`, `published_count`) logs and continues, but `assess_run_health`'s fixed signal list never reads that branch's status field, so no degraded flag/sidecar signal/ntfy alert ever fires — the same "run_health has no signal for X" shape found three separate times.
- **Prevalence/severity:** 6 findings across 2 waves, max **ops-fragility**, waves 3+4.
- **Representative examples:** W3-O4 (`run_health.py` — degraded-signal list never references `summary['wsv_status']`/`summary['enrich_status']`, confirmed does NOT fire for a mid-pipeline partial failure), W3-DISC-14 (market-moves' own degraded fields DO feed `assess_run_health`, unlike WSV/enrich — an inconsistency across stages), W4-M2b (`pipeline.py:530,543` — `write_digest` and `published_count` failures are each logged but never wired into the same signal list; "the entire weekly deliverable is silently not published... yet `run_pipeline` returns normally... and exits 0").
- **Root-cause category:** observability-gap
- **Scaffold-preventability hypothesis:** A stronger verify-gate behavior — mandatory eval-delta check of the alerting path itself (construct a summary with each fail-soft field set and confirm a signal fires) — would catch this directly; a deterministic checks.py detector cross-referencing every `except Exception`/fail-soft site against whether its status key is actually read by `run_health.py` would have caught all three instances with one mechanism instead of three separate manual traces.

### REL-1: No enforced LLM spend ceiling; retry-ladder multiplication is a latent unbounded-cost hazard
- **What breaks:** A single config-only change (adding a model to any `*_MODELS` env var, or raising `*_max_retries`) would silently multiply real LLM spend with no code path anywhere that would notice, alert, or refuse; cost visibility itself only exists post-hoc for one of three LLM-dependent stages.
- **Prevalence/severity:** 1 finding, max **spend-control**, wave 3.
- **Representative examples:** W3-R1 (`relevance.py:141` — single hardcoded `max_tokens` governs every LLM call; `config.py:138-145,155-161,253-274` — retry ladders are length-1 today but `*_models_raw` is an uncapped string, making retry×model multiplication latent not realized; zero "cost" references in `relevance.py`/`web_search_validate.py`, no pre-flight budget check or run-level ceiling anywhere).
- **Root-cause category:** data-scale-unbounded
- **Scaffold-preventability hypothesis:** A data-scale audit rule requiring any config value that can multiply an external-API call count (model-list length × retry count) to have an enforced maximum at config-validation time — exactly W3-R1's own fix sketch — would catch this as a static config-shape check, without waiting for an actual cost spike.

**Wave 3 process-gap quotes (verbatim):**
- W3-O4: "This scenario-(c) gap is itself untested: zero test files reference `run_trendscope.sh` or `ntfy` anywhere in `tests/`, and no `test_run_health.py` test constructs a summary with `wsv_status`/`enrich_status` set."
- W3-DISC-11: "the entire shell wrapper (preflight, migration safety-copy, exit-code/ntfy branching, weekly backup+rotation) has zero automated test coverage of any kind — every behavioral claim in W3-O1/O2/O4/O5 above rests on reading the script, not on any asserting test."
- W3-O2: "no restore runbook, script, or drill exists anywhere" and the backup step "has no `quick_check` step after the backup completes, unlike this wave's own snapshot-mint path."
- W3-N2: "`AGG_VERSION=3`/`DERIVATION_VERSION=2` are confirmed hand-maintained integers with no automated bump guard against a silent model/library upgrade."
- W3-R1: "Grep-confirmed: zero 'cost' references in `relevance.py` or `web_search_validate.py` — the gate and WSV stages have no cost visibility at all, not even post-hoc."

### TQ-1: Untested defensive/fallback branches in churn×CC hotspots (coverage-reach ≠ depth)
- **What breaks:** High-complexity, high-churn functions have specific except/fallback branches (DB query failures, malformed config, malformed input) that no test touches; if the branch ever fires in production it silently degrades output with no caller-visible signal, while the module's overall coverage % looks healthy.
- **Prevalence/severity:** ~10 findings, max **ranking-error**, wave 4.
- **Representative examples:** W4-T1#1 (`scoring.py:501-511` — per-source maturity `GROUP BY` query's `except Exception` silently degrades to "treat all sources as mature"), W4-T1#5 (`config.py:483` `load_wsv_own_source_domains` has zero tests anywhere, feeds WSV domain classification), W4-T1#4 (`console/data.py:812-1029` — 4 of 5 `OperationalError` degrade blocks never hit by the one fixture), W4-T2 named-gap-1 (`config.py` four validators, incl. `_wsv_search_depth` gating a paid Tavily payload, zero-tested).
- **Root-cause category:** other (a pure coverage-reach gap — no test touches the branch at all, distinct from "assertion too weak" or "forced green").
- **Scaffold-preventability hypothesis:** A new deterministic checks.py detector cross-referencing radon CC × git churn against branch-level (not line-level) coverage misses would flag exactly these functions mechanically — this is literally the manual method W4-T1 used by hand; making it a standing check would surface the class pre-audit instead of via a dedicated wave.

### TQ-2: Mock boundary is the function/module-under-test itself, not the real dependency contract (recurs in both correctness-audit and test-audit)
- **What breaks:** Tests patch the module's own integration point (`get_session`, `_call_chat_completions`) or subclass/override the module under test, instead of the true I/O boundary (`requests.post`, a real SQLAlchemy session, the HTTP edge) — so "green" never exercises the actual commit/rollback, retry/backoff, or failure-isolation contract; a broken implementation would only surface against the real provider/DB/host in production.
- **Prevalence/severity:** 11 findings across both audits, max **silent-data-drift**, wave 4 + test-audit.
- **Representative examples:** W4-T2 named-gap-2 (`db.py` `get_session` — every test mocks or hand-reimplements the commit/rollback contract; `except Exception: session.rollback(); raise` never exercised), W4-T2 named-gap-4 (`relevance.py:104-228` `_call_chat_completions` always replaced at the mock boundary — 429/retry/error-classification never tested through it), `test_wikipedia.py::TestPipelineIntegration::test_failure_isolation` (subclasses `WikipediaCollector`, patches above the HTTP layer), `test_cli_score.py::_inject_get_session` (bypasses commit/rollback/close across all 15 integration tests).
- **Root-cause category:** dependency-external-api
- **Scaffold-preventability hypothesis:** A test-quality rule banning `patch()`/subclass targets that equal the function/module-under-test rather than an injected external boundary, enforceable as a checks.py AST detector (grep-equivalent of the manual audits that found this in two separate corpora) — require mocking one layer down (`requests.post`, a real session), the way `TestTavilyBackend` already does. That the identical anti-pattern was independently rediscovered in the correctness audit AND the test-audit is itself evidence this is a systemic, not incidental, gap.

### TQ-3: CLI dispatch wiring untested — function body tested directly, entry point never exercised
- **What breaks:** Tests call `_cmd_eval`/`_cmd_run` etc. directly or via a throwaway parser, never via `main([...])`; the argparse dispatch table itself — the code path production actually invokes (cron, operator CLI) — is unverified, so a wiring regression would ship undetected.
- **Prevalence/severity:** 2 findings, max **measurement-error**, wave 4.
- **Representative examples:** W4-T1#7 (`cli.py::_cmd_eval` — the `--all` loop, per-run error accumulation, `--replay` branch never invoked end-to-end via `main()` with real data anywhere in the suite), W4-T2 named-gap-3 (`_cmd_backfill`/`_cmd_digest`/`_cmd_console` never called from any test in any form; `_cmd_run` body is tested but `main()`'s dispatch-to-it is not, despite being the exact subcommand the weekly cron drives).
- **Root-cause category:** config-wiring
- **Scaffold-preventability hypothesis:** A checks.py detector diffing the argparse subcommand registry against grep'd `main([...])` call shapes in `tests/` would catch untested wiring mechanically — exactly the manual grep W4-T2 performed; could be a mandatory verify-gate check before any CLI change ships.

### LLM-1: LLM response validation and diagnostic-labeling gaps
- **What breaks:** JSON parse + enum checks pass, but a field's *type* (bool vs. string, list-of-string vs. mixed types) is never validated — a wrong-typed value silently coerces to the opposite meaning or throws an uncaught exception that defeats the multi-model fallback ladder mid-loop; separately, a structural guard correctly protects persisted data but its diagnostic label misdescribes why it fired, misleading a future incident responder.
- **Prevalence/severity:** 4 findings, max **silent-data-drift**, wave 4.
- **Representative examples:** W4-DISC-5 (`relevance.py:352` — `bool(obj.get("keep", False))` coerces `"keep": "false"` (a string) to `True`, silently inverting the model's intent, term kept on the board with no signal), W4-DISC-6 (`web_search_validate.py:648-658` — non-numeric `"confidence"` raises uncaught `ValueError`, bypassing the ladder's `continue`-on-failure pattern), W4-T3(enrich) canonical-guard (`enrich.py:467-473` — design/docstring says a hallucinated canonical is "rejected"; code actually silently resets it to `members[0]` and keeps the entity).
- **Root-cause category:** llm-nondeterminism
- **Scaffold-preventability hypothesis:** A test-quality rule requiring off-schema-type fixtures (string-not-bool, mixed-type list elements) for every LLM JSON field extraction — this wave's own mocked-fixture harness (`w4_llm_gate.json`/`w4_llm_wsv.json`) is exactly the right shape; the gap is that it ran once as an audit pass instead of being a mandatory standing eval-gate over LLM ingestion points. The diagnostic-mislabeling half is more domain-specific — no deterministic detector compares prose design-intent to code semantics; closest general fix is a review-layer requirement to re-check design-doc wording against shipped behavior at diagnostic-producing call sites.

### TOOL-1: Deterministic gate has four structural floor holes (type-check, coverage, warnings, CI scope)
- **What breaks:** No type checker, no coverage config/gate (figures exist only in gitignored `tmp/`), no `filterwarnings=error` (an `SAWarning` and a socket `UserWarning` sail through a green run), and CI runs `pytest -q` only — no lint/format/dependency/secret/duplication check runs unconditionally anywhere.
- **Prevalence/severity:** 4 findings, max **dev-quality** (provisional — no traced data hazard), wave 4.
- **Representative examples:** W4-T5 Hole 1 (no mypy/pyright anywhere), W4-T5 Hole 2 (`kleinberg.py` sits at ~100% coverage with zero direct test reference — "a bare `--cov-fail-under=N` gate would treat kleinberg.py's figure as clean, healthy coverage, exactly backwards from reality"), W4-T5 Hole 3 (`tests/test_provenance.py:176` SAWarning sails through a green run), W4-T5 Hole 4 (`ci.yml` — five steps, only `pytest -q`, no ruff/deptry/gitleaks/osv-scanner/checks.py).
- **Root-cause category:** config-wiring
- **Scaffold-preventability hypothesis:** Directly — new deterministic checks.py detectors (type-check, branch coverage + explicit reach-vs-depth policy, `filterwarnings` allowlist) plus a stronger CI-wiring requirement; this is the textbook case where the missing scaffold mechanism *is* the finding.

### TOOL-2: Audit-tool provisioning drift and the audit's own instruments have unverified blind spots
- **What breaks:** Most audit tools reach the checkout by undocumented ad-hoc paths rather than the tracked provisioning script, and an entire check tier (`radon`/`jscpd`/`vulture`/`index-coverage`) is silently disabled by default with no rationale — a clean `just audit-report` run looks identical to those checks having run and passed; separately, the scripts producing the audit's OWN evidence (mock-usage counter, duplication scanner, assertion-shape classifier) have dead comparisons and traversal blind spots — earlier waves' conclusions rested on instrument output that was itself wrong for multiple waves before anyone checked.
- **Prevalence/severity:** 6 findings, max **dev-quality**, wave 4.
- **Representative examples:** W4-M1 (`install-tools.sh` provisions only gitleaks+osv-scanner of 11 actually-used tools), W4-DISC-8 (`checks.py`'s heavy tier auto-detects `False` with no `checks.toml` override and no comment), W4-T4(a) (`_audit_mocks_oneoff.py` — dead string comparison could never match; roughly half of the historical "over-mocked" flags were counter bugs, not real over-mocking), W4-T4(b) (jscpd's token-exact matching missed a three-way duplicated LLM-response-handling loop across three files — "materially undersold by the jscpd report alone").
- **Root-cause category:** config-wiring (provisioning half) / other (instrument-trust half)
- **Scaffold-preventability hypothesis:** A deterministic checks.py detector that fails loudly on any registered tool's absence/version-mismatch (already exists for gitleaks) extended to every tool in the registry — the scaffold's own verify-gate machinery, just not applied to itself. For the instrument-trust half: a stronger verify-gate behavior mandating adversarial re-verification of any deterministic audit instrument's classifier logic before a later wave trusts its output — precisely what W4-T4 performed as a one-off sweep; making that standing (not a per-wave special case) would catch this class routinely instead of after years of unverified reliance on a buggy counter.

**Wave 4 process-gap quotes (verbatim, this wave is the richest source):**
- (W4-T2, named-gap-4) "Green does not guarantee the actual HTTP retry/backoff contract inside `_call_chat_completions` ... against a real provider response ... the function is always replaced at the mock boundary, never exercised through it."
- (W4-T2, named-gap-4) "a green suite here is consistent with a broken retry/backoff/error-classification implementation that would only surface in production against a real, rate-limiting provider."
- (W4-T2, kleinberg caveat) "A high line-coverage figure here certifies that the lines *ran*, not that any assertion checked the burst weight's numeric correctness — this is the standing illustration for why every coverage figure in this section must be read as reach, not depth."
- (W4-T2, named-gap-2) "the specific design guarantee the function exists to enforce is verified today only against a hand-rolled stand-in whose own name overclaims what it verifies."
- (W4-T2, named-gap-3) "`_cmd_backfill` and `_cmd_digest` are referenced only inside `cli.py`'s own dispatch wiring, never called from any test in any form."
- (W4-T1 #7) "the actual DB-touching body of `_cmd_eval` ... is never invoked end-to-end via `main()` with real data anywhere in the suite."
- (W4-T5, Hole 3) "nothing in today's pytest config would turn either [warning] into a failure."
- (W4-T5, Hole 2) "A bare `--cov-fail-under=N` gate cannot distinguish this from real depth — it would treat kleinberg.py's figure as clean, healthy coverage, exactly backwards from reality."
- (W4-T5, Hole 4) "CI itself, the one mechanism running unconditionally on every push/PR, enforces none of it."
- (W4-DISC-8) "an operator who runs `just audit-report` and sees it complete... has no signal that duplication/complexity/dead-code checking never ran at all — it looks identical to those checks having run clean."
- (W4-M2a) "Nothing in the UI or the response distinguishes a normal 'merge into N existing labels' save from a 'just destroyed N existing labels' save."
- (W4-M2b) "there is no seventh signal for 'did `write_digest` actually succeed.'"
- (W4-M2b) "the entire weekly deliverable ... is silently not published for that run, yet `run_pipeline` returns normally (no exception escapes) ... and exits 0."
- (W4-DISC-2) "the `zero_assert_tests` list is a poor proxy for 'tests lacking verification' against this repo's actual test-writing style."
- (W4-T4(b)) "yes, confirmed, and jscpd's automated report only caught part of it ... materially undersold by the jscpd report alone."

### TA-1: Vacuous / tautological force-green assertions
- **What breaks:** Assertions that are unconditionally true (`or True`, self-comparison, dead-code guards, empty bodies) so a spec-violating regression stays green.
- **Prevalence/severity:** 13+ findings, max **CRITICAL**, test-audit.
- **Representative examples:** `test_lane_scoring.py::TestPerennialDemotion::test_perennial_disabled_no_order_change` (`assert ... or True` — always true), `test_web_search_validate.py::TestPipelineWiring::test_default_off` (empty body, zero asserts), `test_upsert.py::test_created_utc_is_timezone_aware` (`if` guard always False under SQLite — dead assertion).
- **Root-cause category:** test-quality-forced-green
- **Scaffold-preventability hypothesis:** A new checks.py detector — AST lint flagging `assert X or <truthy-literal>`, `assert count_var >= 0`, empty test bodies, and `x == x.method()` self-comparisons — run as a pre-merge gate, not a one-off audit.

### TA-2: Weak tests hid real product bugs (the corpus's single clearest preventability story)
- **What breaks:** Three cases where the weak test wasn't just low-value — it concealed a shipped defect: `market_scorer.is_resolved` excludes ALL co-outcomes of a market instead of only the settled one; `persist_enrichment` doubles Entity rows on re-invocation; `set_watermark` has no monotonicity guard so a clock-step regresses the collection watermark.
- **Prevalence/severity:** 3 findings, max **HIGH**, test-audit.
- **Representative examples:** `market_scorer.py:281-284` masked by `test_market_moves.py::TestScoring::test_resolution_exclusion_closed_flag` (single-outcome fixture hides the multi-outcome bug), `enrich.py:665-677` masked by `test_entity_identity.py::TestIdempotency::test_idempotent_persist` (never queries Entity row count), `watermark.py:92` masked by `test_watermark.py` (only forward-movement tested).
- **Root-cause category:** spec-or-acceptance-drift
- **Scaffold-preventability hypothesis:** A weak test hid a live bug for an unknown period until this one-time audit. Fix is an acceptance-criteria requirement, not a lint: every spec WHEN/THEN clause must map to a named test asserting the THEN on actual persisted state (row counts, not "no crash"), checked at review time. Generic detectors cannot find these — they are domain-logic-boundary bugs.

### TA-3: Collector `complete=False` signal discarded in tests
- **What breaks:** `collect_recent` returns `(count, complete)`; `complete=False` must withhold the watermark advance. Tests unpack as `count, _ = ...`, discarding it even in tests built specifically to exercise the failure path that sets it False — a regression hardcoding `complete=True` would pass the whole suite.
- **Prevalence/severity:** 25+ sites (22 in `test_arctic_shift.py` alone, plus Bluesky/Polymarket/pipeline), max **HIGH**, test-audit.
- **Representative examples:** `test_arctic_shift.py::test_one_failing_subreddit_does_not_abort_others` (line 533, `count, _ =`), `test_bluesky.py::test_per_feed_error_isolation` (line 410, complete discarded).
- **Root-cause category:** test-quality-weak-assertion
- **Scaffold-preventability hypothesis:** checks.py grep-detector banning `_, _ = collector.collect_recent(...)`-style tuple-discard patterns in any collector test file, forcing an explicit assert on the `complete` value. (Note: this is the same `complete=True`-when-it-shouldn't-be shape as wave-1 ING-1 — the test suite's own discard pattern is *why* ING-1's bug shipped invisibly.)

### TA-4: Incremental-aggregation / fact-store spec structurally unguarded
- **What breaks:** The 6-requirement incremental-aggregation spec (fact-store population, direct-write preservation, sealed-day skip, no-reparse re-derivation, dual provenance versions, backfill/gate) is implemented in `factstore.py`/`provenance.py` but almost entirely untested; `test_aggregate.py` only exercises the legacy direct-from-documents path.
- **Prevalence/severity:** 12 findings across `test_aggregate.py`, `test_factstore.py`, `test_provenance.py`, max **HIGH**, test-audit.
- **Representative examples:** `test_aggregate.py` — MISSING entire fact-store `DocumentTerm` tier, MISSING sealed-day skip (Req 3); `test_factstore.py` — MISSING end-to-end "rederive without reparse" path; `test_provenance.py` — `set_period_versions`/`DERIVATION_VERSION` never imported or tested.
- **Root-cause category:** test-quality-fixture-scale-only
- **Scaffold-preventability hypothesis:** A verify-gate requirement — an OpenSpec apply/verify check that fails if a shipped requirement's WHEN/THEN has zero matching test names at merge; line coverage alone would miss this since the *lines* run via import, only the *behavior* is untested. (Same underlying fact-store risk as wave-1 AGG-1.)

### TA-5: Missing fail-closed & boundary-condition scenarios
- **What breaks:** Dozens of individual spec scenarios — error paths, exact-equality boundaries, disabled-by-default gates — have zero coverage, so a fail-closed contract or an off-by-one boundary flip ships silently.
- **Prevalence/severity:** 40+ findings, the largest bucket in the corpus, max **HIGH**, test-audit.
- **Representative examples:** `test_scoring.py` — MISSING `score_run` empty-DB `ValueError` coverage, `test_market_moves.py` — MISSING magnitude/liquidity exact-boundary tests (strict `<`), `test_health.py` — MISSING exact drop-threshold tie boundary.
- **Root-cause category:** other (systemic negative-path/boundary omission, not one weak-assertion pattern)
- **Scaffold-preventability hypothesis:** Stronger verify-gate — require every enumerated scenario ID in a capability's spec/oracle to have ≥1 asserting test at verify time; only works where specs are scenario-enumerated (many collector capabilities are NONE/THIN, so this remains partly domain-specific).

### TA-7: Shape-not-value / partial-contract weak assertions
- **What breaks:** Assertions check that *something* is present (`is None`, `len()`, substring-in-page-text, one field of a multi-field contract) rather than the value the spec mandates, so a wrong-but-present value passes.
- **Prevalence/severity:** 20+ findings, max **MED**, test-audit.
- **Representative examples:** `test_console.py::test_term_detail_prefills_trend_for_kept` (`'trend' in resp.text` satisfied by the heading "Trending," never checks the pre-filled form value), `test_scoring.py::test_multi_source_counts_summed` (AUM S3 `recent_doc_count` never asserted).
- **Root-cause category:** test-quality-weak-assertion
- **Scaffold-preventability hypothesis:** A test-quality rule banning bare `assert "<literal>" in resp.text` for form-field/value checks in view tests — checks.py flags the pattern as requiring either DOM/value-level assertion or an inline justification comment.

### TA-8: Fragility (private-surface / output-pinning) and economy/duplication
- **What breaks:** Tests reach into private attributes/functions or pin incidental output (exact CSS class names, exact ordered CSV fieldnames) unrelated to the spec contract, breaking on harmless refactors; paired with copy-pasted arrange blocks that should be parametrized.
- **Prevalence/severity:** 15 findings, max **LOW**, test-audit.
- **Representative examples:** `test_scorers.py::test_alpha_bonf_unchanged` (reads private `_alpha_bonf` directly, bypasses `prepare()`), `test_preview.py` (pins CSS class `sort-active`/`lane-sparkline` and "coming soon" stub copy).
- **Root-cause category:** test-quality-weak-assertion
- **Scaffold-preventability hypothesis:** Private-surface fragility is domain-specific, no general mechanism; the duplication half is mechanically detectable (a checks.py token-similarity detector across same-file test bodies) but at LOW severity this is a nice-to-have, not a gate.

**Oracle timing (did acceptance criteria exist before code shipped?):** Hybrid, not uniformly
reconstructed. Where a genuine OpenSpec artifact predates the code — `lane-scoring/spec.md`,
`incremental-aggregation/spec.md`, `entity-identity/spec.md`, `polymarket-market-collection/spec.md`,
`digest-flag-provenance/spec.md`, `wikipedia-pageview-collection/spec.md` — the oracle is a faithful
re-read of pre-existing acceptance criteria under the normal OpenSpec lifecycle. But a large share of
capabilities are marked THIN or NONE: `collectors.md` states plainly that HackerNews, Arctic Shift,
and Bluesky have "spec: NONE," intent derived "exclusively from module docstrings and inline
comments"; `plumbing-health.md` marks watermark-advance-and-hold, upsert-idempotency, and
text-cleaning THIN. For those, no acceptance criteria independent of the implementer's own code
comments ever existed before this audit. The sharpest timing evidence: `plumbing-health.md` cites the
archived proposal `2026-06-12-fix-watermark-integrity/notes.md` (nine days before this audit), which
had already named the monotonicity invariant as "explicitly called out... as UNWRITTEN" — the gap was
known and documented and simply never closed. No evidence anywhere of a standing, continuously-run
mechanism checking tests against specs before this audit; the CHARTER frames the whole exercise as a
one-time Session A (build oracle)/Session B (judge tests) pass, and FINDINGS.md calls itself "the
durable audit record" of a completed one-time cycle, not a recurring gate. The only pre-existing
continuous check in this material is `test_schema_parity.py` — a structural DB-schema check, not a
spec-vs-test-behavior check. So test-writing and spec-writing drifted apart silently wherever a spec
existed, and docstring-vs-test drift was invisible by construction wherever it didn't, until this
single reconstruction caught both classes at once.

## Cross-cutting observations

1. **The identical failure shape recurs across waves/corpora before anyone names it as a class.**
   Ground-truth silently destroyed on load failure: `labels_io.py` (wave 3, W3-E3) and
   `console/labels_io.py` (wave 4, W4-M2a) — same catch-log-continue-empty-collection bug, different
   module, one wave apart (merged into MEAS-1 above). Fail-soft branch with no operator-visible
   signal: WSV/enrich (wave 3, W3-O4/R2), then `write_digest`/`published_count` (wave 4, W4-M2b) —
   the exact same "`assess_run_health` doesn't read this status field" shape found three times
   (merged into OPS-2). Wrong-boundary mocking (mock the module-under-test, not the real edge): found
   independently by the *correctness* audit (wave 4, TQ-2) AND the separate *test* audit (TA-6,
   folded in) — two different audit programs rediscovering the same anti-pattern. None of these
   recurrences were caught by a standing rule after the first instance; each was only visible because
   a human/agent happened to re-read that subsystem in a later wave.

2. **Coverage-reach is repeatedly mistaken for coverage-depth, and the corpus names this explicitly.**
   TQ-1's ~10 untested defensive branches sit in modules with healthy overall coverage percentages;
   TOOL-1's kleinberg.py sits at ~100% coverage while zero test asserts the burst weight's numeric
   correctness ("this is the standing illustration for why every coverage figure in this section must
   be read as reach, not depth"). No mechanism in this repo (or a bare `--cov-fail-under=N`, if one
   were added) distinguishes the two.

3. **Flag-gated features shipped without ever being exercised at real scale.** AGG-1's fact-store
   dual-path desync is a `default-off` config flag whose precondition ("the default-off gate is the
   only thing currently preventing this precondition from being exercised" — W1-A1) has literally
   never fired in production. This is the same shape as the "eval whose warm-up is shorter than the
   warmed signal's required history is NOT decision-grade" lesson (`lessons.md`, notability rerank
   eval) — a feature/lever can look validated (tests green, eval ran) while never having been tested
   under the actual condition that will occur once it's turned on.

4. **The test-audit's oracle reconstruction is the direct analogue of psc-monitor's TQ-MISSING
   finding**: coverage gaps were only gradable once someone built a ratified behavior catalog
   (7 `oracle/*.md` files here) from specs that mostly predate the code but were never continuously
   checked against the test suite. No standing mechanism compares tests to specs in this repo either
   — `test_schema_parity.py` is the only continuous check, and it guards schema shape, not behavior.

5. **`lessons.md` explicitly changes future process on:** (a) probe real external behavior before
   self-review, and never let a reviewer "confirm" an unverifiable external-API claim — direct result
   of the pytrends incident; (b) `monkeypatch.undo()` reverts autouse-fixture env vars, a test-isolation
   trap now written down after one latent failure; (c) an eval's `low_confidence`/warm-up flag is a
   hard gate on interpreting its verdict, not a footnote (notability rerank); (d) briefing a
   dossier-assembly delegation must name the domain's specific numeric traps, not just the generic
   never-record-counts rule — the Wave-4 dossier itself briefly violated its own rule (~29 coverage
   percentages slipped in) before the orchestrator's self-review caught it, a small but telling
   instance of the audit program almost reproducing the very "process gap lets a known rule lapse"
   pattern it exists to find elsewhere.

6. **Agreement/difference with the psc-monitor signal:** **Agrees, strongly.** The psc-monitor
   analysis's core finding — "lessons written as prose were never enforced as deterministic checks, so
   identical bugs recurred in sibling code and were re-found by hand months later; per-change verify
   never reviews the accreted composition of many past changes" — holds here in an even starker form,
   because in this repo the recurrence happens **inside the same audit program**, not months later:
   MEAS-1's two sites and OPS-2's three sites recurred *within the same multi-week audit sweep*, one
   wave apart, before anyone generalized the pattern into a standing rule. The corpus's own
   `known-findings-ledger` prior-knowledge register (CHARTER.md PD9) is a written-down list of exactly
   this kind of admitted-open item, and it works only as long as a human keeps re-reading it — it is
   not a check. This is the single strongest, most concretely-evidenced argument in the whole corpus
   for turning named recurring shapes into permanent `checks.py` detectors instead of dossier prose.
