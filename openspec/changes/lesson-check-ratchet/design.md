# Design — lesson-check-ratchet

## Context

Both downstream repos re-shipped bug classes that had already been found, fixed once, and
written down as prose (evidence: `knowledge/research/scaffold-gap-analysis-2026-07/`,
frozen `proposal.md`, verified `explore-brief.md`). The scaffold has exactly one
domain-invariant mechanism today — `data_lint.py`'s flat `checks/*.sql` convention — and a
prose-only lesson store. The industry precedent for what this change builds is strong and
citable: Google's Error Prone exists to "eliminate classes of serious bugs from entering
our code," and the Tricorder program (ICSE 2015) formalized admission criteria for turning
recurring findings into permanently-run checks (near-zero false positives, obvious and
actionable fixes) — see `research/tooling-research.md`.

Hard constraints inherited from prior decisions (see `research/prior-art-digest.md`):
scaffold scripts are Python 3.13 **stdlib-only**; everything is **check-only** (D3, never
writes/fixes); the invariant framework ships upstream but per-repo wiring is a downstream
SMALL change (D7); upstream parser surface stays limited; `scaffold_lint.py` is
golden-source-only so propagating enforcement must live in `knowledge_lint.py`; target
scale is D4 ("~5 deliberate checks per repo, grown from incidents").

## Goals / Non-Goals

**Goals:**
- A lintable closure contract: every generalizable finding gets exactly one recorded
  disposition in a machine-checkable ledger, and the lint catches missing, malformed,
  dangling, or stale dispositions.
- A one-dropped-file path from "we got burned by X" to "X is checked on every audit run."
- Close-out routing at the two existing triage points (archive, run-audit) bounded to a
  ≤3-question classification.

**Non-Goals:** (frozen in proposal — Out of Scope) OW-1/OW-4 generic detectors; OW-5/OW-6
audit skills; retroactive downstream remediation; back-filling all legacy lessons;
auto-wiring downstream repos; semantic verification that a linked test "truly exercises"
its class (deterministically unknowable — the honest limit, mitigated below).

## Decisions

### D1 — Ledger: `knowledge/ratchet-log.md`, registry-line format, five dispositions

One line per finding-class, `·`-separated like `audit-log.md`/`decisions/INDEX.md`:

```
- **YYYY-MM-DD** · <class-slug> · <disposition> — <essence / source refs>
```

where `<disposition>` is exactly one of:

| Disposition | Form | Lint verification |
|---|---|---|
| check | `check:<pointer>` | pointer resolves (see D3) |
| frozen test | `test:<path>[::<name>]` | file exists; `::<name>` appears in file text |
| waiver | `waiver:review-by YYYY-MM-DD` | reason present; valid ISO calendar date; not past |
| open | `open:since YYYY-MM-DD` | valid ISO calendar date; flagged when older than the age threshold |
| grandfathered | `grandfathered` | format only |

All dates are validated as real ISO 8601 calendar dates (`2026-13-01` and `not-a-date` are
lint findings, not silently skipped). The `open` age threshold is configurable via the
existing `[knowledge_lint]` table in `checks.toml` (key `ratchet_open_max_age_days`,
default 30) — the same configuration surface as `_check_untriaged_age`'s
`untriaged_max_age_days`. `test:` pointers SHOULD include a `::<name>` node (conventions
text recommends it) — a bare file path verifies only file existence, which is weak for a
suite file.

`check:` pointers take two forms: `check:checks/<file>` (a per-repo invariant file, D3) or
`check:<script>.py::<name>` (a named check function/registry entry in a scaffold script,
verified by grepping the name in that file — the `budget-agreement` artifact-vs-artifact
shape). Preference ordering is normative: **check > test > waiver**; `open` is a temporary
state for "fix shipped, enforcement deferred" so archive is never blocked on writing a
detector, and its 30-day age flag (the `_check_untriaged_age` precedent) stops it from
becoming a parking lot. `grandfathered` is legal only for pre-ratchet legacy lessons.

*Why a separate file, not fields in `lessons.md`:* lessons stay narrative (taxonomy
decision, prior-art digest); a registry needs registry-line discipline to be lintable for
free (the `audit-log.md` D9 precedent). *Why not TOML:* the knowledge tree is
markdown-first and every sibling registry is a `.md` one-liner list; a second config
dialect buys nothing at ≤tens of lines.

### D2 — Enforcement lint lives in `knowledge_lint.py` (propagates), guarded on existence

New check `_check_ratchet_log`, guarded exactly like `_check_audit_log`: absent file =
silently clean (un-adopted repos unaffected; no flag-day). It validates line format,
disposition keyword, slug shape, dates, dangling `check:`/`test:` pointers, stale waivers,
aged `open` entries. `knowledge/ratchet-log.md` joins the canonical single-home map so the
orphan/duplicate check covers it, AND joins `EPHEMERAL_PATHS` (the `audit-log.md`
precedent) so prose citations of the ledger in a repo that has not adopted it yet are not
flagged as broken citations. `scaffold_lint.py` is NOT touched (golden-source-only;
this contract must propagate). The existing live-tree pytest gate makes the scaffold's own
ledger continuously verified — no new test wiring needed beyond the check itself.

*Verification depth (premise-review 🟡 resolved):* v1 verifies pointer **liveness**
(file exists, named symbol textually present), not semantic coverage. Semantic drift
("test exists but no longer exercises the class") is delegated to the existing
`knowledge-drift-review` LLM pass, whose scope note gains one line telling it to
spot-check ratchet pointers. Declarative-only linkage — the reviewer's stated worry — is
thereby excluded by construction at the deterministic layer, with the semantic residue
explicitly owned by the judgment layer.

### D3 — Invariant runner: new stdlib `scripts/repo_lint.py`, `checks/*.py`, one file = one invariant

Mirrors `data_lint.py` sideways, same flat `checks/` directory, disjoint extension:

- **Check contract:** check files are discovered via a `checks/*.py` glob (flat, no
  recursion, sorted filename order — the same convention as `data_lint.py`'s
  `checks/*.sql` glob; the two conventions share one directory with disjoint extensions).
  Each `checks/*.py` is a standalone script; the runner invokes it as
  `<python> <file> <repo-root>` in a subprocess. The script prints a JSON array of
  findings `[{"path", "line", "message"}]` (empty array = pass) to stdout and exits 0;
  any nonzero exit, timeout, or unparseable stdout = infra failure. A minimal real check
  (e.g. psc-monitor's unbounded-`fetchall()` class) is ~10 lines of stdlib Python.
- **Runner semantics:** sorted filename order; stop on FIRST infra failure (exit 3);
  per-check subprocess timeout (default 120s, `--timeout`); findings capped in the JSON
  `sample` (`--max-sample`, default 5) with full count; JSON artifact
  `repo_lint.json` (`generated_by`, per-check `{name, status, findings, sample}`); exit
  0 clean / 2 findings / 3 infra — byte-consistent with `data_lint.py`'s contract.
- **`checks.py` registration:** one registry entry `repo-lint` (tier floor, kind
  delegate, family check), auto-detect trigger `checks/*.py present`, config
  `[checks.repo-lint]` with `paths` = checks dir (first entry only, extra entries
  INFRA-FAIL — the data-lint rule). Invocation follows the `data-lint` integration
  pattern exactly: `checks.py` imports `repo_lint.main()` and calls it in-process with
  `--json <out-path>` and `--checks-dir <configured-dir>`, then reads the resulting
  `repo_lint.json` to extract aggregate count and status. Delegating check: its JSON is
  NOT merged into the aggregate `findings.json` (parser-surface constraint).

*Why subprocess-per-check over in-process import:* hard timeout enforcement via
`subprocess.run(timeout=N)` is universal across all check shapes, unlike `data_lint.py`'s
in-process timeouts which need backend-specific interrupt mechanisms (`threading.Timer` →
`conn.interrupt()` for SQLite, subprocess timeout for psql) and have no equivalent for
arbitrary Python; plus crash isolation (one broken check can't take down the runner) and
zero import-path coupling. Startup cost (~tens of ms × ≤15 checks) is irrelevant at D4
scale. *Why bespoke stdlib over semgrep/ast-grep/opengrep:* stdlib-only is a hard project
constraint; ruff cannot host custom rules (verified open issue, 2026-05); external
engines remain available per-repo via the existing `[checks.custom.*]` escape hatch and
the conventions doc names ast-grep (single pinned binary, YAML rules) as the recommended
graduation path if a repo outgrows ~15 bespoke checks — options table with adoption
evidence in `research/tooling-research.md`. *Why arbitrary code over declarative
patterns:* the highest-value real invariants from the evidence corpus (fail-soft status
key must be read by `run_health.py`; test fixtures must not set `autocommit=TRUE`;
paired artifacts must agree) are cross-file logic no regex/pattern dialect expresses;
TOML-declared regexes were considered and rejected as covering only the weakest third of
the corpus. **Trust model:** check files are repo-trusted code, same class as
`[checks.custom.*]` commands — the D3 caveat ("check-only is the configuring repo's
responsibility") is restated verbatim in the runner docstring.

### D4 — Triage decision rule: three questions, asked at two existing gates

```
Q1  Real defect (not noise/env)?                 no → stop (no entry)
Q2  Generalizable class (sibling could recur)?   no → stop (point fix suffices)
Q3  Mechanically detectable or test-freezable?
      yes → disposition check: / test: (artifact ships with the fix; open: if deferred)
      no  → waiver:review-by <date> — <why domain-judgment-only>
```

Routing hooks (text additions only, no new mechanism):
- **`openspec-archive-change` skill, Step 6 (primary's review):** before committing, scan
  the change's `notes.md`/`review-log.md` for found-and-fixed defects; apply the three
  questions; append ledger line(s). The **primary** does this, not the archive-executor —
  it is exactly the generalizability judgment the mechanical executor cannot make, it
  costs one read of files already in the primary's context, and the enforcing artifact
  (check/test) was already built during apply/verify when the disposition is `check:`/
  `test:`.
- **`run-audit` skill, Step 3 (triage):** findings judged real get the same three
  questions; entry appended alongside the existing audit-log line ceremony.
- **AGENTS.md:** one bullet in Working process stating the closure rule and preference
  ordering, citing the `finding-closure-ratchet` capability spec as canonical.

### D5 — Scaffold bootstrap: the ledger's first entries are its own guards

`knowledge/ratchet-log.md` ships in this repo with real entries, so the mechanism is
exercised where it is built and the live-tree lint gate proves the format end-to-end.
Literal initial content (these ARE the ledger lines, in the D1 format):

```
- **2026-07-10** · ratchet-ledger-format · check:scripts/knowledge_lint.py::_check_ratchet_log — self-referential bootstrap; the ledger's own format check.
- **2026-07-10** · delegation-timeout-budget-drift · check:scripts/scaffold_lint.py::budget-agreement — pre-existing exemplar of lesson→check conversion (mechanize-invariants, 2026-07-02).
- **2026-07-10** · repo-invariant-runner-contract · test:scripts/test_repo_lint.py::test_stops_on_first_infra_failure — the runner's load-bearing fail-loud behavior, pinned by name.
```

### D6 — Propagation surface

Manifest additions mirror `data_lint.py`'s treatment: `scripts/repo_lint.py` and
`scripts/test_repo_lint.py` (verified: `scaffold_manifest.txt` lists both `data_lint.py`
and `test_data_lint.py` today). Synced by existing
mechanisms: `knowledge_lint.py`, the two skill files, the AGENTS.md span,
`knowledge/README.md` — whose **Reference taxonomy row gains `knowledge/ratchet-log.md`
alongside `audit-log.md`** as a second bounded one-line-per-entry registry ledger (no new
taxonomy row). Explicitly NOT synced (per-repo content):
`knowledge/ratchet-log.md`, `checks/` contents, `checks.toml`. Downstream first
invariants are named in advance as adoption seeds (documentation, not wiring): psc-monitor
SCALE-1 (unbounded fetch), TXN-1 (autocommit fixture); extrends OPS-2 (fail-soft status
key unread by run_health), MEAS-1 (load-failure→empty-collection overwrite shape).

## Risks / Trade-offs

- **[Waiver/open abuse — cheapest disposition wins]** → normative preference ordering in
  rule text; waiver requires a reason and a review-by date, lint-flagged when past; `open`
  age-flagged at 30 days. The failure mode degrades to today's status quo (prose), never
  below it.
- **[Ledger vs lessons.md drift — two homes for one story]** → they hold different
  categories by construction (narrative vs closure registry, the decisions-INDEX/archive
  split precedent); lint owns format, `knowledge-drift-review` owns semantics.
- **[Whole-tree scans slower than SQL checks]** (premise-review 🟡) → per-check subprocess
  timeout, default 120s; D4 scale bounds the total; conventions doc tells check authors to
  glob narrowly; a chronically slow invariant belongs behind `[checks.custom.*]` at heavy
  tier instead.
- **[False-positive fatigue kills adoption]** → Tricorder admission criteria adopted into
  the conventions text: a check must be near-zero-FP and actionable; a noisy check gets
  tuned or demoted to waiver — noise discipline is why D4-scale intentional checks work.
- **[Downstream repos never adopt]** → accepted in proposal; mitigations: framework
  arrives on next sync, named seed invariants above, and OW-5/OW-6 route findings into the
  ledger by construction once built.
- **[Arbitrary-code checks can write]** → repo-trusted by documented design (D3 caveat,
  verbatim from the custom-checks precedent); subprocess isolation bounds crashes, not
  writes. Not enforceable without a sandbox; explicitly out of proportion at this scale.

## Migration Plan

Additive, no flag day: land runner + lint + docs + skills in scaffold; bootstrap ledger;
full suite green (live-tree gate now covers the ledger). Downstream: next
operator-authorized `sync_scaffold.py` run delivers the framework inert (no `checks/*.py`,
no ledger → auto-disabled, lint-guarded); adoption is a per-repo SMALL change. Rollback:
revert the scaffold commits; downstream unaffected until synced.

## Verification (acceptance criteria for verify phase)

1. **`repo_lint.py` behavioral (fixture-based):** clean dir → exit 0 + empty checks JSON;
   check emitting findings → exit 2, findings counted, sample capped at `--max-sample`;
   check exiting nonzero / printing non-JSON → exit 3, run stops at FIRST infra failure
   (later sorted files not executed); hung check → killed at `--timeout`, exit 3; no
   `checks/*.py` → exit 0 "no checks configured"; JSON artifact schema matches
   `data_lint.json`'s shape (`generated_by` + per-check entries).
2. **`checks.py` integration:** `--list` shows `repo-lint`; auto-enabled iff `checks/*.py`
   exists; `[checks.repo-lint] enabled=false` respected; second `paths` entry INFRA-FAILs.
3. **`knowledge_lint.py` ratchet checks (fixture-based):** absent ledger → clean; each
   malformed-line/unknown-disposition case flagged; dangling `check:`/`test:` pointer
   flagged; live pointer passes; `::name` absent from pointed file flagged; waiver past
   review-by flagged; `open` older than 30 days flagged; `grandfathered` passes format-only.
4. **Live tree:** scaffold's own suite green including the live-tree lint gate over the
   new bootstrapped `knowledge/ratchet-log.md`, and `scaffold_lint` SEAL green with the
   manifest additions.
5. **Routing text:** archive + run-audit skills contain the three-question triage step and
   ledger line format; AGENTS.md bullet present inside the synced span (verify via
   `sync_scaffold.py --check` self-consistency remaining green).
6. **Real-output eyeball (self-contained in this repo):** run `repo_lint.py` against a
   scratch checkout with one synthetic toy invariant (e.g. a ~10-line check flagging
   `os.system(` call sites) planted over a synthetic offending file; observe the finding
   land in `repo_lint.json` and `checks.py --floor` exit 2. (The real downstream seeds —
   fetchall shape etc. — are per-repo adoption work, not exercisable here.)

### Live Probe

Skipped — no external-API surface: the change is stdlib-only scripts, markdown, and skill
text; no new library kwarg/client/request shape exists to probe.

## Open Questions

None blocking. Two deliberate deferrals, to be parked at archive: (a) whether
`outstanding.py` should also surface `open:` ratchet entries in the outstanding-work
snapshot (wait for real usage; the 30-day lint flag covers rot meanwhile); (b) whether
OW-1's test-quality detector ships as `checks/*.py` tenants or a built-in — decided in
OW-1, not here.
